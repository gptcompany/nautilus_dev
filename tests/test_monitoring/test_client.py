# TDD RED Phase: Tests for MetricsClient (T010)
# These tests MUST fail initially until client.py is implemented

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Python 3.10 compatibility
import datetime as _dt
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMetricsClient:
    """Tests for MetricsClient QuestDB wrapper (T010)."""

    def test_client_creates_with_config(self):
        """Client should initialize with MonitoringConfig."""
        from monitoring.client import MetricsClient
        from monitoring.config import MonitoringConfig

        config = MonitoringConfig(
            questdb_host="localhost",
            questdb_http_port=9000,
            questdb_ilp_port=9009,
        )
        client = MetricsClient(config)
        assert client.config.questdb_host == "localhost"

    def test_client_creates_with_defaults(self):
        """Client should work with default config."""
        from monitoring.client import MetricsClient

        client = MetricsClient()
        assert client.config is not None

    @pytest.mark.asyncio
    async def test_client_write_single_metric(self):
        """Client should write a single metric to QuestDB."""
        from monitoring.client import MetricsClient
        from monitoring.models import DaemonMetrics

        client = MetricsClient()
        metrics = DaemonMetrics(
            timestamp=datetime.now(UTC),
            host="test-server",
            env="dev",
            fetch_count=10,
            error_count=0,
            liquidation_count=0,
            uptime_seconds=100.0,
            running=True,
        )

        # Mock the HTTP request
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=204)
            result = await client.write(metrics)
            assert result is True

    @pytest.mark.asyncio
    async def test_client_write_batch_metrics(self):
        """Client should write batch of metrics efficiently."""
        from monitoring.client import MetricsClient
        from monitoring.models import DaemonMetrics

        client = MetricsClient()
        now = datetime.now(UTC)
        metrics_batch = [
            DaemonMetrics(
                timestamp=now,
                host=f"server-{i}",
                env="prod",
                fetch_count=i * 10,
                error_count=0,
                liquidation_count=0,
                uptime_seconds=100.0,
                running=True,
            )
            for i in range(100)
        ]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=204)
            result = await client.write_batch(metrics_batch)
            assert result is True
            # Should batch efficiently (not 100 individual requests)
            assert mock_post.call_count <= 2

    @pytest.mark.asyncio
    async def test_client_flush_on_threshold(self):
        """Client should auto-flush when buffer reaches threshold."""
        from monitoring.client import MetricsClient
        from monitoring.config import MonitoringConfig
        from monitoring.models import DaemonMetrics

        config = MonitoringConfig(
            questdb_host="localhost",
            batch_size=10,  # Low threshold for test
        )
        client = MetricsClient(config)

        with patch.object(client, "_send_batch", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            for i in range(15):
                await client.buffer(
                    DaemonMetrics(
                        timestamp=datetime.now(UTC),
                        host="server",
                        env="dev",
                        fetch_count=i,
                        error_count=0,
                        liquidation_count=0,
                        uptime_seconds=0.0,
                        running=True,
                    )
                )
            # Should have flushed at least once (at 10)
            assert mock_send.call_count >= 1

    @pytest.mark.asyncio
    async def test_client_handles_connection_error(self):
        """Client should handle QuestDB connection errors gracefully."""
        import httpx

        from monitoring.client import MetricsClient
        from monitoring.models import DaemonMetrics

        client = MetricsClient()
        metrics = DaemonMetrics(
            timestamp=datetime.now(UTC),
            host="server",
            env="dev",
            fetch_count=0,
            error_count=0,
            liquidation_count=0,
            uptime_seconds=0.0,
            running=True,
        )

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            result = await client.write(metrics)
            assert result is False

    @pytest.mark.asyncio
    async def test_client_query_returns_data(self):
        """Client should query QuestDB and return results."""
        from monitoring.client import MetricsClient

        client = MetricsClient()
        query = "SELECT * FROM daemon_metrics LIMIT 10"

        mock_response = {
            "columns": [
                {"name": "timestamp", "type": "TIMESTAMP"},
                {"name": "host", "type": "SYMBOL"},
            ],
            "dataset": [
                ["2025-12-26T12:00:00.000000Z", "server-01"],
            ],
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value=mock_response),
            )
            result = await client.query(query)
            assert len(result) == 1
            assert result[0]["host"] == "server-01"

    @pytest.mark.asyncio
    async def test_client_health_check(self):
        """Client should provide health check method."""
        from monitoring.client import MetricsClient

        client = MetricsClient()

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            is_healthy = await client.health_check()
            assert is_healthy is True

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Client should work as async context manager."""
        from monitoring.client import MetricsClient

        async with MetricsClient() as client:
            assert client is not None
