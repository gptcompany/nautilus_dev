# monitoring.collectors.exchange - ExchangeCollector for connectivity metrics
#
# T029-T032: Create ExchangeCollector with WebSocket status, latency, reconnection tracking

import asyncio
import logging
import socket
from datetime import datetime, timezone
from typing import Callable

from monitoring.collectors import BaseCollector
from monitoring.config import MonitoringConfig
from monitoring.models import ExchangeStatus

logger = logging.getLogger(__name__)


class ExchangeCollector(BaseCollector[ExchangeStatus]):
    """Collector for exchange connectivity status.

    Tracks WebSocket connection status, latency, and reconnections per exchange.
    Integrates with Spec 001 CCXT Pipeline.
    """

    def __init__(
        self,
        config: MonitoringConfig,
        status_provider: Callable[[], dict] | None = None,
    ):
        """Initialize ExchangeCollector.

        Args:
            config: Monitoring configuration.
            status_provider: Optional callable that returns exchange status dict.
                           Expected format:
                           {
                             "binance": {
                               "connected": True,
                               "latency_ms": 45.2,
                               "reconnect_count": 3,
                               "last_message_at": datetime(...),
                               "disconnected_at": None
                             },
                             "bybit": {...},
                             ...
                           }
        """
        self.config = config
        self._status_provider = status_provider
        self._running = False
        self._task: asyncio.Task | None = None
        self._host = config.host or socket.gethostname()
        self._env = config.env
        self._on_metrics: Callable[[ExchangeStatus], None] | None = None

    def set_on_metrics(self, callback: Callable[[ExchangeStatus], None]) -> None:
        """Set callback for when metrics are collected.

        Args:
            callback: Function to call with collected metrics.
        """
        self._on_metrics = callback

    async def collect(self) -> list[ExchangeStatus]:
        """Collect metrics from all exchanges.

        Returns:
            List of ExchangeStatus instances for each exchange.
        """
        try:
            status_dict = self._get_status()
            metrics_list = self._status_to_metrics(status_dict)
            return metrics_list
        except Exception as e:
            logger.error(f"Error collecting exchange metrics: {e}")
            return []

    def _get_status(self) -> dict:
        """Get exchange status from provider.

        Returns:
            Status dictionary with per-exchange metrics.
        """
        if self._status_provider:
            return self._status_provider()

        # Default: Try to import and use exchange status from Spec 001
        try:
            from scripts.ccxt_pipeline.daemon_runner import DaemonRunner

            return DaemonRunner.get_exchange_status()
        except (ImportError, AttributeError):
            logger.warning("Exchange status not available, using mock status")
            return self._mock_status()

    def _mock_status(self) -> dict:
        """Generate mock status for testing.

        Returns:
            Mock status dictionary.
        """
        return {
            "binance": {
                "connected": False,
                "latency_ms": 0.0,
                "reconnect_count": 0,
                "last_message_at": None,
                "disconnected_at": None,
            },
            "bybit": {
                "connected": False,
                "latency_ms": 0.0,
                "reconnect_count": 0,
                "last_message_at": None,
                "disconnected_at": None,
            },
            "okx": {
                "connected": False,
                "latency_ms": 0.0,
                "reconnect_count": 0,
                "last_message_at": None,
                "disconnected_at": None,
            },
        }

    # Valid exchange names (must match models.ExchangeStatus Literal)
    VALID_EXCHANGES = frozenset(("binance", "bybit", "okx", "dydx"))

    def _status_to_metrics(self, status_dict: dict) -> list[ExchangeStatus]:
        """Convert status dict to list of ExchangeStatus.

        Args:
            status_dict: Status dictionary from exchange manager.

        Returns:
            List of ExchangeStatus instances.
        """
        metrics_list = []
        now = datetime.now(timezone.utc)

        for exchange, data in status_dict.items():
            # Skip unknown exchanges to avoid Pydantic validation errors
            if exchange not in self.VALID_EXCHANGES:
                logger.warning(f"Skipping unknown exchange: {exchange}")
                continue

            # Clamp latency to valid range
            latency = min(max(data.get("latency_ms", 0.0), 0.0), 10000.0)

            metrics = ExchangeStatus(
                timestamp=now,
                exchange=exchange,
                host=self._host,
                env=self._env,
                connected=bool(data.get("connected", False)),
                latency_ms=latency,
                reconnect_count=data.get("reconnect_count", 0),
                last_message_at=data.get("last_message_at"),
                disconnected_at=data.get("disconnected_at"),
            )
            metrics_list.append(metrics)

        return metrics_list

    async def start(self) -> None:
        """Start periodic collection."""
        if self._running:
            logger.warning("ExchangeCollector already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info(
            f"ExchangeCollector started (interval={self.config.exchange_collect_interval}s)"
        )

    async def stop(self) -> None:
        """Stop collection and cleanup resources."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("ExchangeCollector stopped")

    async def _collection_loop(self) -> None:
        """Internal collection loop."""
        while self._running:
            try:
                metrics_list = await self.collect()
                for metrics in metrics_list:
                    if self._on_metrics:
                        self._on_metrics(metrics)
            except Exception as e:
                logger.error(f"Error in exchange collection loop: {e}")

            await asyncio.sleep(self.config.exchange_collect_interval)


__all__ = ["ExchangeCollector"]
