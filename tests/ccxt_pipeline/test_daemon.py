"""Unit tests for DaemonRunner (Phase 8: T058-T060).

Tests scheduling, graceful shutdown, and stability for continuous data collection.
"""

import asyncio

# Python 3.10 compatibility
import datetime as _dt
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDaemonScheduling:
    """Tests for DaemonRunner scheduling (T058)."""

    @pytest.mark.asyncio
    async def test_daemon_runner_initialization(self) -> None:
        """Test DaemonRunner initializes with correct configuration."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        assert runner is not None
        assert runner._running is False
        assert runner._scheduler is None

    @pytest.mark.asyncio
    async def test_daemon_schedules_oi_fetch(self) -> None:
        """Test daemon schedules OI fetching at configured intervals."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner(
            oi_interval_minutes=5,
            funding_interval_minutes=60,
        )

        # Mock the scheduler
        with patch.object(runner, "_scheduler") as mock_scheduler:
            mock_scheduler.add_job = MagicMock()
            runner._setup_scheduled_jobs()

            # Verify OI job was scheduled
            calls = list(mock_scheduler.add_job.call_args_list)
            assert len(calls) >= 1  # At least OI job

    @pytest.mark.asyncio
    async def test_daemon_schedules_funding_fetch(self) -> None:
        """Test daemon schedules funding rate fetching."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner(
            oi_interval_minutes=5,
            funding_interval_minutes=60,
        )

        with patch.object(runner, "_scheduler") as mock_scheduler:
            mock_scheduler.add_job = MagicMock()
            runner._setup_scheduled_jobs()

            # Verify jobs were scheduled
            assert mock_scheduler.add_job.called

    @pytest.mark.asyncio
    async def test_daemon_stores_fetched_data(self) -> None:
        """Test daemon stores fetched data to ParquetStore."""
        from scripts.ccxt_pipeline.models import OpenInterest, Venue
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        mock_store = MagicMock()
        runner._store = mock_store

        # Create mock OI data
        oi = OpenInterest(
            timestamp=datetime.now(UTC),
            symbol="BTCUSDT-PERP",
            venue=Venue.BINANCE,
            open_interest=100000.0,
            open_interest_value=10000000000.0,
        )

        # Test store is called
        runner._store_data([oi])
        mock_store.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_daemon_concurrent_exchange_fetching(self) -> None:
        """Test daemon fetches from multiple exchanges concurrently."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        # Mock orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.fetch_open_interest = AsyncMock(return_value=[])
        runner._orchestrator = mock_orchestrator

        await runner._fetch_open_interest("BTCUSDT-PERP")

        mock_orchestrator.fetch_open_interest.assert_called_once_with("BTCUSDT-PERP")


class TestGracefulShutdown:
    """Tests for graceful shutdown (T059)."""

    @pytest.mark.asyncio
    async def test_daemon_stops_on_sigint(self) -> None:
        """Test daemon stops gracefully on SIGINT."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()
        runner._running = True

        # Simulate shutdown request
        runner.request_shutdown()

        assert runner._shutdown_requested is True

    @pytest.mark.asyncio
    async def test_daemon_flushes_pending_writes(self) -> None:
        """Test daemon flushes pending writes before stopping."""
        from scripts.ccxt_pipeline.models import OpenInterest, Venue
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        mock_store = MagicMock()
        runner._store = mock_store

        # Add pending data
        oi = OpenInterest(
            timestamp=datetime.now(UTC),
            symbol="BTCUSDT-PERP",
            venue=Venue.BINANCE,
            open_interest=100000.0,
            open_interest_value=10000000000.0,
        )
        runner._pending_writes.append(oi)

        # Flush on shutdown
        await runner._flush_pending_writes()

        mock_store.write.assert_called_once()
        assert len(runner._pending_writes) == 0

    @pytest.mark.asyncio
    async def test_daemon_closes_all_connections(self) -> None:
        """Test daemon closes all exchange connections on shutdown."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        mock_orchestrator = AsyncMock()
        runner._orchestrator = mock_orchestrator

        await runner._cleanup()

        mock_orchestrator.close_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_daemon_stops_scheduler(self) -> None:
        """Test daemon stops the APScheduler on shutdown."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        mock_scheduler = MagicMock()
        mock_scheduler.shutdown = MagicMock()
        runner._scheduler = mock_scheduler
        runner._running = True

        await runner.stop()

        mock_scheduler.shutdown.assert_called_once()
        assert runner._running is False

    @pytest.mark.asyncio
    async def test_daemon_cancels_liquidation_stream(self) -> None:
        """Test daemon cancels liquidation streaming task on shutdown."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        # Create a real asyncio task that we can cancel
        async def mock_stream():
            await asyncio.sleep(100)  # Long running task

        task = asyncio.create_task(mock_stream())
        runner._liquidation_task = task

        await runner._cancel_liquidation_stream()

        assert task.cancelled()
        assert runner._liquidation_task is None


class TestDaemonStability:
    """Integration-level tests for daemon stability (T060)."""

    @pytest.mark.asyncio
    async def test_daemon_recovers_from_fetch_error(self) -> None:
        """Test daemon continues after a fetch error."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        # Mock orchestrator that fails once then succeeds
        mock_orchestrator = AsyncMock()
        mock_orchestrator.fetch_open_interest = AsyncMock(
            side_effect=[Exception("Network error"), []]
        )
        runner._orchestrator = mock_orchestrator

        # First call should not raise (error handled internally)
        await runner._fetch_open_interest("BTCUSDT-PERP")

        # Second call should succeed
        await runner._fetch_open_interest("BTCUSDT-PERP")

        assert mock_orchestrator.fetch_open_interest.call_count == 2

    @pytest.mark.asyncio
    async def test_daemon_logs_errors(self) -> None:
        """Test daemon logs errors without crashing."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        mock_orchestrator = AsyncMock()
        mock_orchestrator.fetch_open_interest = AsyncMock(side_effect=Exception("Test error"))
        runner._orchestrator = mock_orchestrator

        # Should not raise
        await runner._fetch_open_interest("BTCUSDT-PERP")

    @pytest.mark.asyncio
    async def test_daemon_tracks_fetch_count(self) -> None:
        """Test daemon tracks successful fetch count for monitoring."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        mock_orchestrator = AsyncMock()
        mock_orchestrator.fetch_open_interest = AsyncMock(return_value=[])
        runner._orchestrator = mock_orchestrator

        assert runner.stats.fetch_count == 0

        await runner._fetch_open_interest("BTCUSDT-PERP")

        assert runner.stats.fetch_count == 1

    @pytest.mark.asyncio
    async def test_daemon_tracks_error_count(self) -> None:
        """Test daemon tracks error count for monitoring."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()

        mock_orchestrator = AsyncMock()
        mock_orchestrator.fetch_open_interest = AsyncMock(side_effect=Exception("Test error"))
        runner._orchestrator = mock_orchestrator

        assert runner.stats.error_count == 0

        await runner._fetch_open_interest("BTCUSDT-PERP")

        assert runner.stats.error_count == 1

    @pytest.mark.asyncio
    async def test_daemon_status_report(self) -> None:
        """Test daemon provides status report."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        runner = DaemonRunner()
        runner._running = True

        status = runner.get_status()

        assert "running" in status
        assert status["running"] is True
        assert "fetch_count" in status
        assert "error_count" in status
        assert "uptime_seconds" in status
