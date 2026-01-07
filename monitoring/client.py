# monitoring.client - QuestDB MetricsClient wrapper
#
# T013: Create QuestDB MetricsClient wrapper

import asyncio
import logging
from typing import Any, Union

import httpx

from monitoring.config import MonitoringConfig
from monitoring.models import (
    DaemonMetrics,
    ExchangeStatus,
    PipelineMetrics,
    TradingMetrics,
)

logger = logging.getLogger(__name__)

MetricType = Union[DaemonMetrics, ExchangeStatus, PipelineMetrics, TradingMetrics]


class MetricsClient:
    """Async client for QuestDB metrics ingestion via HTTP ILP.

    Supports buffering, batching, and automatic flushing.
    """

    def __init__(self, config: MonitoringConfig | None = None):
        """Initialize metrics client.

        Args:
            config: Monitoring configuration. If None, uses defaults.
        """
        self.config = config or MonitoringConfig()
        self._buffer: list[str] = []
        self._buffer_lock = asyncio.Lock()
        self._http_client: httpx.AsyncClient | None = None
        self._flush_task: asyncio.Task | None = None

    @property
    def _base_url(self) -> str:
        return f"http://{self.config.questdb_host}:{self.config.questdb_http_port}"

    async def __aenter__(self) -> "MetricsClient":
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._start_flush_task()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    def _start_flush_task(self) -> None:
        """Start periodic flush task."""
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._periodic_flush())

    async def _periodic_flush(self) -> None:
        """Periodically flush buffer."""
        while True:
            await asyncio.sleep(self.config.flush_interval)
            await self.flush()

    async def close(self) -> None:
        """Close client and flush remaining metrics."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        await self.flush()

        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def write(self, metric: MetricType) -> bool:
        """Write single metric to QuestDB.

        Args:
            metric: Metric object with to_ilp_line() method.

        Returns:
            True if successful, False otherwise.
        """
        try:
            line = metric.to_ilp_line()
            client = self._get_client()
            response = await client.post(
                f"{self._base_url}/write",
                content=line,
                headers={"Content-Type": "text/plain"},
            )
            return response.status_code == 204
        except httpx.ConnectError as e:
            logger.error(f"QuestDB connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error writing metric: {e}")
            return False

    async def write_batch(self, metrics: list[MetricType]) -> bool:
        """Write batch of metrics to QuestDB.

        Args:
            metrics: List of metric objects.

        Returns:
            True if successful, False otherwise.
        """
        if not metrics:
            return True

        try:
            lines = "\n".join(m.to_ilp_line() for m in metrics)
            client = self._get_client()
            response = await client.post(
                f"{self._base_url}/write",
                content=lines,
                headers={"Content-Type": "text/plain"},
            )
            return response.status_code == 204
        except httpx.ConnectError as e:
            logger.error(f"QuestDB connection error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error writing batch: {e}")
            return False

    async def buffer(self, metric: MetricType) -> None:
        """Buffer metric for batch write.

        Automatically flushes when batch_size is reached.

        Args:
            metric: Metric object to buffer.
        """
        async with self._buffer_lock:
            self._buffer.append(metric.to_ilp_line())
            if len(self._buffer) >= self.config.batch_size:
                await self._send_batch(self._buffer.copy())
                self._buffer.clear()

    async def _send_batch(self, lines: list[str]) -> bool:
        """Send batch of ILP lines to QuestDB.

        Args:
            lines: List of ILP format lines.

        Returns:
            True if successful, False otherwise.
        """
        if not lines:
            return True

        try:
            payload = "\n".join(lines)
            client = self._get_client()
            response = await client.post(
                f"{self._base_url}/write",
                content=payload,
                headers={"Content-Type": "text/plain"},
            )
            return response.status_code == 204
        except Exception as e:
            logger.error(f"Error sending batch: {e}")
            return False

    async def flush(self) -> bool:
        """Flush buffered metrics to QuestDB.

        Returns:
            True if successful, False otherwise.
        """
        async with self._buffer_lock:
            if not self._buffer:
                return True
            result = await self._send_batch(self._buffer.copy())
            if result:
                self._buffer.clear()
            return result

    async def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute SQL query against QuestDB.

        Args:
            sql: SQL query string.

        Returns:
            List of result rows as dictionaries.
        """
        try:
            client = self._get_client()
            response = await client.get(
                f"{self._base_url}/exec",
                params={"query": sql},
            )
            if response.status_code != 200:
                logger.error(f"Query failed: {response.text}")
                return []

            data = response.json()
            columns = [col["name"] for col in data.get("columns", [])]
            rows = data.get("dataset", [])

            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []

    async def health_check(self) -> bool:
        """Check QuestDB health.

        Returns:
            True if QuestDB is healthy, False otherwise.
        """
        try:
            client = self._get_client()
            response = await client.get(f"{self._base_url}/exec", params={"query": "SELECT 1"})
            return response.status_code == 200
        except Exception:
            return False

    def submit(self, metric: MetricType) -> None:
        """Submit metric to buffer (sync interface for callbacks).

        This method provides a synchronous interface for callback handlers.
        The metric is buffered and will be flushed asynchronously.

        Args:
            metric: Metric object to submit.
        """
        # Schedule the async buffer operation on the event loop
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.buffer(metric))
        except RuntimeError:
            # No running loop - log warning and skip
            logger.warning("No running event loop, metric not submitted")

    async def start(self) -> None:
        """Start the metrics client.

        Initializes HTTP client and starts periodic flush task.
        """
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        self._start_flush_task()
        logger.info(f"MetricsClient started (QuestDB: {self._base_url})")

    async def stop(self) -> None:
        """Stop the metrics client.

        Alias for close() for consistency with collector interfaces.
        """
        await self.close()
        logger.info("MetricsClient stopped")


__all__ = ["MetricsClient"]
