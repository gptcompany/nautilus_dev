#!/usr/bin/env python3
"""monitoring/metrics_collector.py

T066-T069: Main metrics collector entry point with orchestration and Prometheus endpoint.

Orchestrates all collectors and manages metric submission to QuestDB.
Optionally exposes a Prometheus-compatible /metrics endpoint (FR-011).

Usage:
    python -m monitoring.metrics_collector [--prometheus-port 8080]
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any

from monitoring.client import MetricsClient
from monitoring.collectors.daemon import DaemonCollector
from monitoring.collectors.exchange import ExchangeCollector
from monitoring.collectors.pipeline import PipelineCollector
from monitoring.collectors.trading import TradingCollector
from monitoring.config import MonitoringConfig
from monitoring.models import (
    DaemonMetrics,
    ExchangeStatus,
    PipelineMetrics,
    TradingMetrics,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MetricsOrchestrator:
    """Orchestrates all metric collectors and manages lifecycle.

    T067: Implements collector orchestration (all collectors running together).
    """

    def __init__(
        self,
        config: MonitoringConfig | None = None,
        enable_prometheus: bool = False,
        prometheus_port: int = 8080,
    ):
        """Initialize the metrics orchestrator.

        Args:
            config: Monitoring configuration. If None, loads from environment.
            enable_prometheus: Whether to expose Prometheus /metrics endpoint.
            prometheus_port: Port for Prometheus HTTP server.
        """
        self.config = config or MonitoringConfig()
        self.enable_prometheus = enable_prometheus
        self.prometheus_port = prometheus_port

        # Client for QuestDB
        self._client: MetricsClient | None = None

        # Collectors
        self._daemon_collector: DaemonCollector | None = None
        self._exchange_collector: ExchangeCollector | None = None
        self._pipeline_collector: PipelineCollector | None = None
        self._trading_collector: TradingCollector | None = None

        # Prometheus server
        self._prometheus_server: Any = None

        # State
        self._running = False
        self._shutdown_event = asyncio.Event()

        # Prometheus metrics storage (for /metrics endpoint)
        self._prometheus_metrics: dict[str, Any] = {}

    async def start(self) -> None:
        """Start all collectors and the metrics client."""
        if self._running:
            logger.warning("MetricsOrchestrator already running")
            return

        logger.info("Starting MetricsOrchestrator...")

        # Initialize client
        self._client = MetricsClient(self.config)
        await self._client.start()

        # Initialize collectors
        self._daemon_collector = DaemonCollector(self.config)
        self._exchange_collector = ExchangeCollector(self.config)
        self._pipeline_collector = PipelineCollector(self.config)
        self._trading_collector = TradingCollector(self.config)

        # Set up metric callbacks
        self._daemon_collector.set_on_metrics(self._handle_daemon_metrics)
        self._exchange_collector.set_on_metrics(self._handle_exchange_metrics)
        self._pipeline_collector.set_on_metrics(self._handle_pipeline_metrics)
        self._trading_collector.set_on_metrics(self._handle_trading_metrics)

        # Start collectors
        await self._daemon_collector.start()
        await self._exchange_collector.start()
        await self._pipeline_collector.start()
        await self._trading_collector.start()

        # Start Prometheus endpoint if enabled
        if self.enable_prometheus:
            await self._start_prometheus_server()

        self._running = True
        logger.info("MetricsOrchestrator started successfully")

    async def stop(self) -> None:
        """Stop all collectors and cleanup resources."""
        if not self._running:
            return

        logger.info("Stopping MetricsOrchestrator...")

        # Stop collectors
        if self._daemon_collector:
            await self._daemon_collector.stop()
        if self._exchange_collector:
            await self._exchange_collector.stop()
        if self._pipeline_collector:
            await self._pipeline_collector.stop()
        if self._trading_collector:
            await self._trading_collector.stop()

        # Stop Prometheus server
        if self._prometheus_server:
            await self._stop_prometheus_server()

        # Stop client (flushes remaining metrics)
        if self._client:
            await self._client.stop()

        self._running = False
        logger.info("MetricsOrchestrator stopped")

    def _handle_daemon_metrics(self, metrics: DaemonMetrics) -> None:
        """Handle daemon metrics from collector."""
        if self._client:
            self._client.submit(metrics)
        self._update_prometheus_metrics("daemon", metrics)

    def _handle_exchange_metrics(self, metrics: ExchangeStatus) -> None:
        """Handle exchange metrics from collector."""
        if self._client:
            self._client.submit(metrics)
        self._update_prometheus_metrics("exchange", metrics)

    def _handle_pipeline_metrics(self, metrics: PipelineMetrics) -> None:
        """Handle pipeline metrics from collector."""
        if self._client:
            self._client.submit(metrics)
        self._update_prometheus_metrics("pipeline", metrics)

    def _handle_trading_metrics(self, metrics: TradingMetrics) -> None:
        """Handle trading metrics from collector."""
        if self._client:
            self._client.submit(metrics)
        self._update_prometheus_metrics("trading", metrics)

    def _update_prometheus_metrics(self, category: str, metrics: Any) -> None:
        """Update Prometheus metrics storage for /metrics endpoint."""
        if not self.enable_prometheus:
            return

        # Store latest metrics by category for Prometheus export
        key = f"{category}_{getattr(metrics, 'host', 'unknown')}"
        self._prometheus_metrics[key] = {
            "category": category,
            "timestamp": metrics.timestamp.isoformat(),
            "data": metrics.model_dump(),
        }

    async def _start_prometheus_server(self) -> None:
        """Start Prometheus-compatible HTTP server (T069)."""
        try:
            from aiohttp import web

            app = web.Application()
            app.router.add_get("/metrics", self._prometheus_metrics_handler)
            app.router.add_get("/health", self._health_handler)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", self.prometheus_port)
            await site.start()
            self._prometheus_server = runner

            logger.info(
                f"Prometheus metrics available at http://0.0.0.0:{self.prometheus_port}/metrics"
            )
        except ImportError:
            logger.warning("aiohttp not installed, Prometheus endpoint disabled")
        except Exception as e:
            logger.error(f"Failed to start Prometheus server: {e}")

    async def _stop_prometheus_server(self) -> None:
        """Stop Prometheus HTTP server."""
        if self._prometheus_server:
            await self._prometheus_server.cleanup()
            self._prometheus_server = None

    async def _prometheus_metrics_handler(self, request: Any) -> Any:
        """Handle /metrics endpoint requests (Prometheus format)."""
        from aiohttp import web

        lines = []

        # Generate Prometheus format metrics
        for key, data in self._prometheus_metrics.items():
            category = data["category"]
            metrics_data = data["data"]

            # Flatten metrics to Prometheus format
            for field, value in metrics_data.items():
                if isinstance(value, (int, float)) and field != "timestamp":
                    metric_name = f"nautilus_{category}_{field}"
                    labels = self._get_prometheus_labels(metrics_data)
                    lines.append(f"{metric_name}{{{labels}}} {value}")

        content = "\n".join(lines)
        return web.Response(text=content, content_type="text/plain")

    async def _health_handler(self, request: Any) -> Any:
        """Handle /health endpoint for container health checks."""
        from aiohttp import web

        status = {
            "status": "healthy" if self._running else "unhealthy",
            "collectors": {
                "daemon": self._daemon_collector is not None,
                "exchange": self._exchange_collector is not None,
                "pipeline": self._pipeline_collector is not None,
                "trading": self._trading_collector is not None,
            },
            "client_connected": self._client is not None,
        }

        import json

        return web.Response(
            text=json.dumps(status),
            content_type="application/json",
            status=200 if self._running else 503,
        )

    def _get_prometheus_labels(self, data: dict) -> str:
        """Generate Prometheus label string from metrics data."""
        labels = []
        for key in ["host", "env", "exchange", "strategy", "symbol", "venue"]:
            if key in data and data[key]:
                # Escape special chars in label values (Prometheus format)
                value = (
                    str(data[key]).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                )
                labels.append(f'{key}="{value}"')
        return ",".join(labels)

    async def run_until_shutdown(self) -> None:
        """Run until shutdown signal received."""
        await self._shutdown_event.wait()

    def request_shutdown(self) -> None:
        """Request graceful shutdown."""
        self._shutdown_event.set()


@asynccontextmanager
async def create_orchestrator(
    config: MonitoringConfig | None = None,
    enable_prometheus: bool = False,
    prometheus_port: int = 8080,
):
    """Context manager for MetricsOrchestrator lifecycle.

    Usage:
        async with create_orchestrator() as orchestrator:
            await orchestrator.run_until_shutdown()
    """
    orchestrator = MetricsOrchestrator(
        config=config,
        enable_prometheus=enable_prometheus,
        prometheus_port=prometheus_port,
    )
    await orchestrator.start()
    try:
        yield orchestrator
    finally:
        await orchestrator.stop()


async def main(prometheus_port: int = 8080) -> None:
    """Main entry point for metrics collector."""
    # Set up signal handlers
    loop = asyncio.get_event_loop()
    orchestrator: MetricsOrchestrator | None = None

    def signal_handler():
        logger.info("Received shutdown signal")
        if orchestrator:
            orchestrator.request_shutdown()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Run orchestrator
    async with create_orchestrator(
        enable_prometheus=True,
        prometheus_port=prometheus_port,
    ) as orch:
        orchestrator = orch
        logger.info("Metrics collector running. Press Ctrl+C to stop.")
        await orch.run_until_shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NautilusTrader Metrics Collector")
    parser.add_argument(
        "--prometheus-port",
        type=int,
        default=8080,
        help="Port for Prometheus /metrics endpoint (default: 8080)",
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(prometheus_port=args.prometheus_port))
    except KeyboardInterrupt:
        logger.info("Metrics collector stopped by user")
        sys.exit(0)
