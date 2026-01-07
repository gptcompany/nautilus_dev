# monitoring.collectors.daemon - DaemonCollector for health metrics
#
# T011-T012: Create DaemonCollector class with DaemonRunner.get_status() polling

import asyncio
import logging
import socket
from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from monitoring.collectors import BaseCollector
from monitoring.config import MonitoringConfig
from monitoring.models import DaemonMetrics

logger = logging.getLogger(__name__)


class DaemonCollector(BaseCollector[DaemonMetrics]):
    """Collector for DaemonRunner health metrics.

    Polls DaemonRunner.get_status() and emits DaemonMetrics to QuestDB.
    Integrates with Spec 001 CCXT Pipeline.
    """

    def __init__(
        self,
        config: MonitoringConfig,
        status_provider: Callable[[], dict] | None = None,
    ):
        """Initialize DaemonCollector.

        Args:
            config: Monitoring configuration.
            status_provider: Optional callable that returns daemon status dict.
                           If None, uses default DaemonRunner.get_status().
        """
        self.config = config
        self._status_provider = status_provider
        self._running = False
        self._task: asyncio.Task | None = None
        self._host = config.host or socket.gethostname()
        self._env = config.env
        self._on_metrics: Callable[[DaemonMetrics], None] | None = None

    def set_on_metrics(self, callback: Callable[[DaemonMetrics], None]) -> None:
        """Set callback for when metrics are collected.

        Args:
            callback: Function to call with collected metrics.
        """
        self._on_metrics = callback

    async def collect(self) -> list[DaemonMetrics]:
        """Collect metrics from DaemonRunner.

        Returns:
            List containing single DaemonMetrics instance.
        """
        try:
            status = self._get_status()
            metrics = self._status_to_metrics(status)
            return [metrics]
        except Exception as e:
            logger.error(f"Error collecting daemon metrics: {e}")
            # Return degraded metrics on error
            return [
                DaemonMetrics(
                    timestamp=datetime.now(UTC),
                    host=self._host,
                    env=self._env,
                    fetch_count=0,
                    error_count=0,
                    liquidation_count=0,
                    uptime_seconds=0.0,
                    running=False,
                    last_error=str(e),
                )
            ]

    def _get_status(self) -> dict:
        """Get daemon status from provider or DaemonRunner.

        Returns:
            Status dictionary with daemon metrics.
        """
        if self._status_provider:
            return self._status_provider()

        # Default: Try to import and use DaemonRunner from Spec 001
        try:
            # Import deferred to avoid circular imports
            from scripts.ccxt_pipeline.daemon_runner import DaemonRunner

            return cast(dict, DaemonRunner.get_status())
        except ImportError:
            logger.warning("DaemonRunner not available, using mock status")
            return self._mock_status()

    def _mock_status(self) -> dict:
        """Generate mock status for testing when DaemonRunner unavailable.

        Returns:
            Mock status dictionary.
        """
        return {
            "running": False,
            "uptime_seconds": 0.0,
            "fetch_count": 0,
            "error_count": 0,
            "liquidation_count": 0,
            "last_error": None,
        }

    def _status_to_metrics(self, status: dict) -> DaemonMetrics:
        """Convert status dict to DaemonMetrics.

        Args:
            status: Status dictionary from DaemonRunner.

        Returns:
            DaemonMetrics instance.
        """
        return DaemonMetrics(
            timestamp=datetime.now(UTC),
            host=self._host,
            env=self._env,
            fetch_count=status.get("fetch_count", 0),
            error_count=status.get("error_count", 0),
            liquidation_count=status.get("liquidation_count", 0),
            uptime_seconds=float(status.get("uptime_seconds", 0.0)),
            running=bool(status.get("running", False)),
            last_error=status.get("last_error"),
        )

    async def start(self) -> None:
        """Start periodic collection."""
        if self._running:
            logger.warning("DaemonCollector already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info(f"DaemonCollector started (interval={self.config.daemon_collect_interval}s)")

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
        logger.info("DaemonCollector stopped")

    async def _collection_loop(self) -> None:
        """Internal collection loop."""
        while self._running:
            try:
                metrics_list = await self.collect()
                for metrics in metrics_list:
                    if self._on_metrics:
                        self._on_metrics(metrics)
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")

            await asyncio.sleep(self.config.daemon_collect_interval)


__all__ = ["DaemonCollector"]
