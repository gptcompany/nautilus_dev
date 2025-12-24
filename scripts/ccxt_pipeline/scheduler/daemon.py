"""DaemonRunner for continuous 24/7 data collection.

Implements scheduled fetching of Open Interest and Funding Rates,
and continuous streaming of Liquidation events.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from scripts.ccxt_pipeline.config import get_config
from scripts.ccxt_pipeline.fetchers import FetchOrchestrator, get_all_fetchers
from scripts.ccxt_pipeline.models import FundingRate, Liquidation, OpenInterest
from scripts.ccxt_pipeline.storage.parquet_store import ParquetStore
from scripts.ccxt_pipeline.utils.logging import get_logger

logger = get_logger("daemon")


@dataclass
class DaemonStats:
    """Statistics for monitoring daemon health."""

    start_time: float = field(default_factory=time.time)
    fetch_count: int = 0
    error_count: int = 0
    liquidation_count: int = 0
    last_fetch_time: datetime | None = None
    last_error: str | None = None


class DaemonRunner:
    """Background service for continuous data collection.

    Manages scheduled fetching of OI and funding rates, and continuous
    streaming of liquidation events from all configured exchanges.

    Attributes:
        stats: Daemon statistics for monitoring.
    """

    def __init__(
        self,
        symbols: list[str] | None = None,
        exchanges: list[str] | None = None,
        oi_interval_minutes: int = 5,
        funding_interval_minutes: int = 60,
        catalog_path: str | None = None,
    ) -> None:
        """Initialize the daemon runner.

        Args:
            symbols: Trading symbols to fetch (default: ["BTCUSDT-PERP", "ETHUSDT-PERP"]).
            exchanges: Exchanges to fetch from (default: all).
            oi_interval_minutes: OI fetch interval in minutes.
            funding_interval_minutes: Funding rate fetch interval in minutes.
            catalog_path: Path to Parquet catalog (default: from config).
        """
        self._symbols = symbols or ["BTCUSDT-PERP", "ETHUSDT-PERP"]
        self._exchanges = exchanges
        self._oi_interval = oi_interval_minutes
        self._funding_interval = funding_interval_minutes

        config = get_config()
        self._catalog_path = catalog_path or config.catalog_path

        self._orchestrator: FetchOrchestrator | None = None
        self._store: ParquetStore | None = None
        self._scheduler: AsyncIOScheduler | None = None

        self._running = False
        self._shutdown_requested = False
        self._liquidation_task: asyncio.Task | None = None
        self._pending_writes: list[OpenInterest | FundingRate | Liquidation] = []

        self.stats = DaemonStats()

    async def start(self) -> None:
        """Start the daemon.

        Initializes connections, starts scheduler, and begins liquidation streaming.
        """
        if self._running:
            logger.warning("Daemon is already running")
            return

        logger.info("Starting daemon...")

        # Initialize components
        fetchers = get_all_fetchers(self._exchanges)
        self._orchestrator = FetchOrchestrator(fetchers)
        self._store = ParquetStore(self._catalog_path)

        # Connect to exchanges
        await self._orchestrator.connect_all()

        # Set up scheduler
        self._scheduler = AsyncIOScheduler()
        self._setup_scheduled_jobs()
        self._scheduler.start()

        # Start liquidation streaming
        self._start_liquidation_stream()

        self._running = True
        self._shutdown_requested = False
        self.stats = DaemonStats()

        logger.info(
            f"Daemon started. OI interval: {self._oi_interval}m, "
            f"Funding interval: {self._funding_interval}m"
        )

    async def stop(self) -> None:
        """Stop the daemon gracefully.

        Stops scheduler, cancels streams, flushes data, and closes connections.
        """
        if not self._running:
            return

        logger.info("Stopping daemon...")

        # Stop scheduler
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

        # Cancel liquidation stream
        await self._cancel_liquidation_stream()

        # Flush pending writes
        await self._flush_pending_writes()

        # Close connections
        await self._cleanup()

        self._running = False
        logger.info("Daemon stopped")

    def request_shutdown(self) -> None:
        """Request graceful shutdown (called from signal handler)."""
        self._shutdown_requested = True
        logger.info("Shutdown requested")

    async def run_forever(self) -> None:
        """Run the daemon until shutdown is requested.

        Main loop that keeps daemon running and handles shutdown.
        """
        await self.start()

        try:
            while not self._shutdown_requested:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Daemon cancelled")
        finally:
            await self.stop()

    def get_status(self) -> dict[str, Any]:
        """Get current daemon status for monitoring.

        Returns:
            Status dictionary with running state and statistics.
        """
        uptime = time.time() - self.stats.start_time if self._running else 0

        return {
            "running": self._running,
            "shutdown_requested": self._shutdown_requested,
            "fetch_count": self.stats.fetch_count,
            "error_count": self.stats.error_count,
            "liquidation_count": self.stats.liquidation_count,
            "uptime_seconds": uptime,
            "last_fetch_time": (
                self.stats.last_fetch_time.isoformat() if self.stats.last_fetch_time else None
            ),
            "last_error": self.stats.last_error,
            "symbols": self._symbols,
            "exchanges": self._exchanges or ["all"],
        }

    def _setup_scheduled_jobs(self) -> None:
        """Set up scheduled fetch jobs."""
        if not self._scheduler:
            return

        # Schedule OI fetching
        self._scheduler.add_job(
            self._scheduled_oi_fetch,
            trigger=IntervalTrigger(minutes=self._oi_interval),
            id="oi_fetch",
            name="Open Interest Fetch",
            replace_existing=True,
        )

        # Schedule funding rate fetching
        self._scheduler.add_job(
            self._scheduled_funding_fetch,
            trigger=IntervalTrigger(minutes=self._funding_interval),
            id="funding_fetch",
            name="Funding Rate Fetch",
            replace_existing=True,
        )

        logger.info(
            f"Scheduled jobs: OI every {self._oi_interval}m, "
            f"Funding every {self._funding_interval}m"
        )

    async def _scheduled_oi_fetch(self) -> None:
        """Scheduled job: Fetch OI for all symbols."""
        for symbol in self._symbols:
            await self._fetch_open_interest(symbol)

    async def _scheduled_funding_fetch(self) -> None:
        """Scheduled job: Fetch funding rates for all symbols."""
        for symbol in self._symbols:
            await self._fetch_funding_rate(symbol)

    async def _fetch_open_interest(self, symbol: str) -> None:
        """Fetch open interest for a symbol from all exchanges.

        Args:
            symbol: Trading pair symbol.
        """
        if not self._orchestrator:
            return

        try:
            results = await self._orchestrator.fetch_open_interest(symbol)

            data_points: list[OpenInterest] = []
            for result in results:
                if result.success and result.data:
                    data_points.append(result.data)
                elif result.error:
                    self.stats.error_count += 1
                    self.stats.last_error = str(result.error)
                    logger.warning(f"OI fetch error from {result.venue}: {result.error}")

            if data_points:
                self._store_data(data_points)

            self.stats.fetch_count += 1
            self.stats.last_fetch_time = datetime.now(timezone.utc)

            logger.debug(f"Fetched OI for {symbol}: {len(data_points)} data points")

        except Exception as e:
            self.stats.error_count += 1
            self.stats.last_error = str(e)
            logger.error(f"Error fetching OI for {symbol}: {e}")

    async def _fetch_funding_rate(self, symbol: str) -> None:
        """Fetch funding rate for a symbol from all exchanges.

        Args:
            symbol: Trading pair symbol.
        """
        if not self._orchestrator:
            return

        try:
            results = await self._orchestrator.fetch_funding_rate(symbol)

            data_points: list[FundingRate] = []
            for result in results:
                if result.success and result.data:
                    data_points.append(result.data)
                elif result.error:
                    self.stats.error_count += 1
                    self.stats.last_error = str(result.error)
                    logger.warning(f"Funding fetch error from {result.venue}: {result.error}")

            if data_points:
                self._store_data(data_points)

            self.stats.fetch_count += 1
            self.stats.last_fetch_time = datetime.now(timezone.utc)

            logger.debug(f"Fetched funding for {symbol}: {len(data_points)} data points")

        except Exception as e:
            self.stats.error_count += 1
            self.stats.last_error = str(e)
            logger.error(f"Error fetching funding for {symbol}: {e}")

    def _start_liquidation_stream(self) -> None:
        """Start liquidation streaming in background task."""
        if not self._orchestrator:
            return

        async def stream_all_symbols():
            """Stream liquidations for all symbols."""
            tasks = []
            for symbol in self._symbols:
                task = asyncio.create_task(
                    self._orchestrator.stream_liquidations(symbol, self._on_liquidation)
                )
                tasks.append(task)

            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                for task in tasks:
                    task.cancel()
                # Await cancelled tasks to allow cleanup
                await asyncio.gather(*tasks, return_exceptions=True)
                raise

        self._liquidation_task = asyncio.create_task(stream_all_symbols())
        logger.info(f"Started liquidation streaming for {self._symbols}")

    async def _cancel_liquidation_stream(self) -> None:
        """Cancel the liquidation streaming task and await cleanup."""
        if self._liquidation_task:
            self._liquidation_task.cancel()
            try:
                await self._liquidation_task
            except asyncio.CancelledError:
                pass  # Expected when cancelling
            self._liquidation_task = None
            logger.info("Liquidation stream cancelled")

    def _on_liquidation(self, liquidation: Liquidation) -> None:
        """Callback for liquidation events.

        Args:
            liquidation: Liquidation event to store.
        """
        self._pending_writes.append(liquidation)
        self.stats.liquidation_count += 1

        # Batch write every 100 liquidations
        if len(self._pending_writes) >= 100:
            self._flush_pending_writes_sync()

        logger.debug(
            f"Liquidation: {liquidation.venue.value} {liquidation.symbol} "
            f"{liquidation.side.value} {liquidation.quantity} @ {liquidation.price}"
        )

    def _store_data(self, data: list[OpenInterest | FundingRate | Liquidation]) -> None:
        """Store data to Parquet.

        Args:
            data: List of data points to store.
        """
        if not self._store or not data:
            return

        try:
            self._store.write(data)
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            self.stats.error_count += 1
            self.stats.last_error = str(e)

    def _flush_pending_writes_sync(self) -> None:
        """Flush pending writes synchronously (for callback use)."""
        if not self._store or not self._pending_writes:
            return

        try:
            self._store.write(self._pending_writes)
            self._pending_writes.clear()
        except Exception as e:
            logger.error(f"Error flushing pending writes: {e}")
            self.stats.error_count += 1
            self.stats.last_error = str(e)

    async def _flush_pending_writes(self) -> None:
        """Flush pending writes before shutdown."""
        self._flush_pending_writes_sync()

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self._orchestrator:
            await self._orchestrator.close_all()
            self._orchestrator = None
