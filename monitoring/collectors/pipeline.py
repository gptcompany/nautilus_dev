# monitoring.collectors.pipeline - PipelineCollector for data pipeline metrics
#
# T019-T021: Create PipelineCollector with fetch tracking and gap detection

import asyncio
import logging
import socket
from datetime import datetime, timezone
from typing import Callable

from monitoring.collectors import BaseCollector
from monitoring.config import MonitoringConfig
from monitoring.models import PipelineMetrics

logger = logging.getLogger(__name__)


class PipelineCollector(BaseCollector[PipelineMetrics]):
    """Collector for data pipeline throughput metrics.

    Tracks fetch counts, data gaps, and throughput per exchange/symbol.
    Integrates with Spec 001 CCXT Pipeline.
    """

    def __init__(
        self,
        config: MonitoringConfig,
        stats_provider: Callable[[], dict] | None = None,
    ):
        """Initialize PipelineCollector.

        Args:
            config: Monitoring configuration.
            stats_provider: Optional callable that returns pipeline stats dict.
                           Expected format:
                           {
                             "exchanges": {
                               "binance": {
                                 "oi": {"count": 100, "bytes": 50000, "latency_ms": 10.0},
                                 "funding": {"count": 50, "bytes": 25000, "latency_ms": 15.0},
                               },
                               ...
                             },
                             "gaps": [
                               {"exchange": "binance", "symbol": "BTC/USDT:USDT", "data_type": "oi", "duration_seconds": 120},
                             ]
                           }
        """
        self.config = config
        self._stats_provider = stats_provider
        self._running = False
        self._task: asyncio.Task | None = None
        self._host = config.host or socket.gethostname()
        self._env = config.env
        self._on_metrics: Callable[[PipelineMetrics], None] | None = None

        # Internal tracking
        self._last_fetch_counts: dict[
            str, dict[str, int]
        ] = {}  # exchange -> data_type -> count

    def set_on_metrics(self, callback: Callable[[PipelineMetrics], None]) -> None:
        """Set callback for when metrics are collected.

        Args:
            callback: Function to call with collected metrics.
        """
        self._on_metrics = callback

    async def collect(self) -> list[PipelineMetrics]:
        """Collect metrics from data pipeline.

        Returns:
            List of PipelineMetrics instances for each exchange/data_type.
        """
        try:
            stats = self._get_stats()
            metrics_list = self._stats_to_metrics(stats)
            return metrics_list
        except Exception as e:
            logger.error(f"Error collecting pipeline metrics: {e}")
            return []

    def _get_stats(self) -> dict:
        """Get pipeline stats from provider.

        Returns:
            Stats dictionary with exchange/data_type metrics.
        """
        if self._stats_provider:
            return self._stats_provider()

        # Default: Try to import and use pipeline stats from Spec 001
        try:
            from scripts.ccxt_pipeline.daemon_runner import DaemonRunner

            return DaemonRunner.get_pipeline_stats()
        except (ImportError, AttributeError):
            logger.warning("Pipeline stats not available, using mock stats")
            return self._mock_stats()

    def _mock_stats(self) -> dict:
        """Generate mock stats for testing.

        Returns:
            Mock stats dictionary.
        """
        return {
            "exchanges": {
                "binance": {
                    "oi": {
                        "count": 0,
                        "bytes": 0,
                        "latency_ms": 0.0,
                        "symbols": ["BTC/USDT:USDT"],
                    },
                    "funding": {
                        "count": 0,
                        "bytes": 0,
                        "latency_ms": 0.0,
                        "symbols": ["BTC/USDT:USDT"],
                    },
                    "liquidation": {
                        "count": 0,
                        "bytes": 0,
                        "latency_ms": 0.0,
                        "symbols": ["BTC/USDT:USDT"],
                    },
                }
            },
            "gaps": [],
        }

    def _stats_to_metrics(self, stats: dict) -> list[PipelineMetrics]:
        """Convert stats dict to list of PipelineMetrics.

        Args:
            stats: Stats dictionary from pipeline.

        Returns:
            List of PipelineMetrics instances.
        """
        metrics_list = []
        now = datetime.now(timezone.utc)
        exchanges = stats.get("exchanges", {})
        gaps = stats.get("gaps", [])

        # Convert gap list to lookup for faster access
        gap_lookup: dict[tuple[str, str, str], float] = {}
        for gap in gaps:
            key = (gap["exchange"], gap["symbol"], gap["data_type"])
            gap_lookup[key] = gap["duration_seconds"]

        for exchange, data_types in exchanges.items():
            for data_type, data in data_types.items():
                symbols = data.get("symbols", ["unknown"])
                for symbol in symbols:
                    gap_key = (exchange, symbol, data_type)
                    gap_detected = gap_key in gap_lookup
                    gap_duration = gap_lookup.get(gap_key)

                    metrics = PipelineMetrics(
                        timestamp=now,
                        exchange=exchange,
                        symbol=symbol,
                        data_type=data_type,
                        host=self._host,
                        env=self._env,
                        records_count=data.get("count", 0),
                        bytes_written=data.get("bytes", 0),
                        latency_ms=data.get("latency_ms", 0.0),
                        gap_detected=gap_detected,
                        gap_duration_seconds=gap_duration,
                    )
                    metrics_list.append(metrics)

        return metrics_list

    async def start(self) -> None:
        """Start periodic collection."""
        if self._running:
            logger.warning("PipelineCollector already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info(
            f"PipelineCollector started (interval={self.config.pipeline_collect_interval}s)"
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
        logger.info("PipelineCollector stopped")

    async def _collection_loop(self) -> None:
        """Internal collection loop."""
        while self._running:
            try:
                metrics_list = await self.collect()
                for metrics in metrics_list:
                    if self._on_metrics:
                        self._on_metrics(metrics)
            except Exception as e:
                logger.error(f"Error in pipeline collection loop: {e}")

            await asyncio.sleep(self.config.pipeline_collect_interval)


__all__ = ["PipelineCollector"]
