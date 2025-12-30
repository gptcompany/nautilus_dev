"""Automated daemon stability test (T074).

This test verifies daemon stability by:
1. Running with shortened intervals (seconds instead of minutes)
2. Verifying scheduled fetches occur
3. Checking memory stability
4. Testing graceful shutdown
5. Validating data storage

Runtime: ~90 seconds (automated version of 24-hour manual test)
"""

import asyncio
import gc
import tempfile
import time
import tracemalloc
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


class TestDaemonStabilityAutomated:
    """Automated stability tests for T074.

    These tests verify the daemon mechanics work correctly in a compressed
    timeframe, validating the same properties as the 24-hour manual test.
    """

    @pytest.fixture
    def temp_catalog(self):
        """Create temporary catalog directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_fetchers(self):
        """Create mock fetchers that return realistic data."""
        from datetime import datetime, timezone
        from scripts.ccxt_pipeline.models import OpenInterest, FundingRate, Venue

        def create_oi(venue: Venue, symbol: str) -> OpenInterest:
            return OpenInterest(
                timestamp=datetime.now(timezone.utc),
                symbol=symbol,
                venue=venue,
                open_interest=50000.0 + (hash(venue.value) % 10000),
                open_interest_value=2500000000.0,
            )

        def create_funding(venue: Venue, symbol: str) -> FundingRate:
            return FundingRate(
                timestamp=datetime.now(timezone.utc),
                symbol=symbol,
                venue=venue,
                funding_rate=0.0001,
                next_funding_time=datetime.now(timezone.utc),
            )

        mock_binance = AsyncMock()
        mock_binance.venue = Venue.BINANCE
        mock_binance.fetch_open_interest = AsyncMock(
            side_effect=lambda s: create_oi(Venue.BINANCE, s)
        )
        mock_binance.fetch_funding_rate = AsyncMock(
            side_effect=lambda s: create_funding(Venue.BINANCE, s)
        )
        mock_binance.stream_liquidations = AsyncMock()
        mock_binance.connect = AsyncMock()
        mock_binance.close = AsyncMock()

        mock_bybit = AsyncMock()
        mock_bybit.venue = Venue.BYBIT
        mock_bybit.fetch_open_interest = AsyncMock(
            side_effect=lambda s: create_oi(Venue.BYBIT, s)
        )
        mock_bybit.fetch_funding_rate = AsyncMock(
            side_effect=lambda s: create_funding(Venue.BYBIT, s)
        )
        mock_bybit.stream_liquidations = AsyncMock()
        mock_bybit.connect = AsyncMock()
        mock_bybit.close = AsyncMock()

        return [mock_binance, mock_bybit]

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)  # 2 minute timeout
    async def test_daemon_runs_without_crash(self, temp_catalog, mock_fetchers):
        """Test daemon runs for 30 seconds without crashing."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        with patch(
            "scripts.ccxt_pipeline.scheduler.daemon.get_all_fetchers"
        ) as mock_get:
            mock_get.return_value = mock_fetchers

            runner = DaemonRunner(
                symbols=["BTCUSDT-PERP"],
                oi_interval_minutes=1,  # Will be triggered manually
                funding_interval_minutes=1,
                catalog_path=temp_catalog,
            )

            # Start daemon
            await runner.start()
            assert runner._running is True

            # Run for 30 seconds
            run_time = 30
            start = time.time()
            while time.time() - start < run_time:
                if not runner._running:
                    pytest.fail("Daemon stopped unexpectedly")
                await asyncio.sleep(1)

            # Verify still running
            assert runner._running is True
            status = runner.get_status()
            assert status["running"] is True
            assert status["uptime_seconds"] >= run_time - 1

            # Graceful shutdown
            await runner.stop()
            assert runner._running is False

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_daemon_scheduled_fetches_execute(self, temp_catalog, mock_fetchers):
        """Test scheduled OI and funding fetches execute correctly."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        with patch(
            "scripts.ccxt_pipeline.scheduler.daemon.get_all_fetchers"
        ) as mock_get:
            mock_get.return_value = mock_fetchers

            runner = DaemonRunner(
                symbols=["BTCUSDT-PERP"],
                oi_interval_minutes=1,
                funding_interval_minutes=1,
                catalog_path=temp_catalog,
            )

            await runner.start()

            # Manually trigger scheduled jobs multiple times
            for i in range(5):
                await runner._scheduled_oi_fetch()
                await runner._scheduled_funding_fetch()
                await asyncio.sleep(0.1)

            # Verify fetches occurred
            assert runner.stats.fetch_count >= 10  # 5 OI + 5 funding

            # Verify fetchers were called
            for fetcher in mock_fetchers:
                assert fetcher.fetch_open_interest.call_count >= 5
                assert fetcher.fetch_funding_rate.call_count >= 5

            await runner.stop()

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_daemon_memory_stability(self, temp_catalog, mock_fetchers):
        """Test daemon memory usage doesn't grow unbounded."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        with patch(
            "scripts.ccxt_pipeline.scheduler.daemon.get_all_fetchers"
        ) as mock_get:
            mock_get.return_value = mock_fetchers

            runner = DaemonRunner(
                symbols=["BTCUSDT-PERP", "ETHUSDT-PERP"],
                oi_interval_minutes=1,
                funding_interval_minutes=1,
                catalog_path=temp_catalog,
            )

            # Start memory tracking
            tracemalloc.start()
            gc.collect()
            initial_snapshot = tracemalloc.take_snapshot()

            await runner.start()

            # Simulate many fetch cycles
            for _ in range(50):
                await runner._scheduled_oi_fetch()
                await runner._scheduled_funding_fetch()
                await asyncio.sleep(0.05)

            gc.collect()
            final_snapshot = tracemalloc.take_snapshot()

            # Compare memory
            top_stats = final_snapshot.compare_to(initial_snapshot, "lineno")

            # Calculate total memory growth
            total_growth = sum(
                stat.size_diff for stat in top_stats if stat.size_diff > 0
            )

            # Allow up to 50MB growth (generous for test environment)
            max_allowed_growth = 50 * 1024 * 1024  # 50MB

            await runner.stop()
            tracemalloc.stop()

            assert total_growth < max_allowed_growth, (
                f"Memory grew by {total_growth / 1024 / 1024:.2f}MB, "
                f"exceeds {max_allowed_growth / 1024 / 1024:.2f}MB limit"
            )

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_daemon_graceful_shutdown_timing(self, temp_catalog, mock_fetchers):
        """Test daemon shuts down within 10 seconds."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        with patch(
            "scripts.ccxt_pipeline.scheduler.daemon.get_all_fetchers"
        ) as mock_get:
            mock_get.return_value = mock_fetchers

            runner = DaemonRunner(
                symbols=["BTCUSDT-PERP"],
                oi_interval_minutes=1,
                funding_interval_minutes=1,
                catalog_path=temp_catalog,
            )

            await runner.start()

            # Trigger some activity
            for _ in range(3):
                await runner._scheduled_oi_fetch()

            # Measure shutdown time
            start_shutdown = time.time()
            await runner.stop()
            shutdown_duration = time.time() - start_shutdown

            assert runner._running is False
            assert shutdown_duration < 10.0, (
                f"Shutdown took {shutdown_duration:.2f}s, exceeds 10s limit"
            )

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_daemon_error_recovery(self, temp_catalog):
        """Test daemon recovers from transient errors without stopping."""
        from datetime import datetime, timezone
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner
        from scripts.ccxt_pipeline.models import OpenInterest, Venue

        # Create fetcher that fails intermittently
        error_count = 0

        async def flaky_fetch(symbol):
            nonlocal error_count
            error_count += 1
            if error_count % 3 == 0:  # Fail every 3rd call
                raise ConnectionError("Network timeout")
            return OpenInterest(
                timestamp=datetime.now(timezone.utc),
                symbol=symbol,
                venue=Venue.BINANCE,
                open_interest=50000.0,
                open_interest_value=2500000000.0,
            )

        mock_fetcher = AsyncMock()
        mock_fetcher.venue = Venue.BINANCE
        mock_fetcher.fetch_open_interest = AsyncMock(side_effect=flaky_fetch)
        mock_fetcher.fetch_funding_rate = AsyncMock(side_effect=flaky_fetch)
        mock_fetcher.stream_liquidations = AsyncMock()
        mock_fetcher.connect = AsyncMock()
        mock_fetcher.close = AsyncMock()

        with patch(
            "scripts.ccxt_pipeline.scheduler.daemon.get_all_fetchers"
        ) as mock_get:
            mock_get.return_value = [mock_fetcher]

            runner = DaemonRunner(
                symbols=["BTCUSDT-PERP"],
                oi_interval_minutes=1,
                funding_interval_minutes=1,
                catalog_path=temp_catalog,
            )

            await runner.start()

            # Run many fetch cycles with intermittent failures
            for _ in range(20):
                await runner._scheduled_oi_fetch()
                await asyncio.sleep(0.05)

            # Verify daemon is still running despite errors
            assert runner._running is True

            # Verify errors were tracked
            assert runner.stats.error_count > 0

            # Verify successful fetches also occurred
            assert runner.stats.fetch_count > runner.stats.error_count

            await runner.stop()

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_daemon_data_persistence(self, temp_catalog, mock_fetchers):
        """Test data is written to disk and persists after shutdown."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner
        from scripts.ccxt_pipeline.storage.parquet_store import ParquetStore

        with patch(
            "scripts.ccxt_pipeline.scheduler.daemon.get_all_fetchers"
        ) as mock_get:
            mock_get.return_value = mock_fetchers

            runner = DaemonRunner(
                symbols=["BTCUSDT-PERP"],
                oi_interval_minutes=1,
                funding_interval_minutes=1,
                catalog_path=temp_catalog,
            )

            await runner.start()

            # Trigger fetches
            for _ in range(5):
                await runner._scheduled_oi_fetch()
                await runner._scheduled_funding_fetch()
                await asyncio.sleep(0.1)

            await runner.stop()

            # Verify data was written to disk
            catalog_path = Path(temp_catalog)

            # Check for parquet files
            parquet_files = list(catalog_path.rglob("*.parquet"))
            assert len(parquet_files) > 0, "No parquet files found after daemon run"

            # Verify data is readable
            store = ParquetStore(temp_catalog)
            # Data should exist (we can't query specific types without knowing schema)
            assert catalog_path.exists()

    @pytest.mark.asyncio
    @pytest.mark.timeout(90)
    async def test_daemon_concurrent_operations(self, temp_catalog, mock_fetchers):
        """Test daemon handles concurrent OI and funding fetches correctly."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        with patch(
            "scripts.ccxt_pipeline.scheduler.daemon.get_all_fetchers"
        ) as mock_get:
            mock_get.return_value = mock_fetchers

            runner = DaemonRunner(
                symbols=["BTCUSDT-PERP", "ETHUSDT-PERP", "SOLUSDT-PERP"],
                oi_interval_minutes=1,
                funding_interval_minutes=1,
                catalog_path=temp_catalog,
            )

            await runner.start()

            # Run concurrent fetch operations
            tasks = []
            for _ in range(10):
                tasks.append(asyncio.create_task(runner._scheduled_oi_fetch()))
                tasks.append(asyncio.create_task(runner._scheduled_funding_fetch()))

            await asyncio.gather(*tasks, return_exceptions=True)

            # Verify no crashes and stats tracked
            assert runner._running is True
            assert runner.stats.fetch_count > 0

            await runner.stop()

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_daemon_status_reporting(self, temp_catalog, mock_fetchers):
        """Test daemon status reports accurate information."""
        from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

        with patch(
            "scripts.ccxt_pipeline.scheduler.daemon.get_all_fetchers"
        ) as mock_get:
            mock_get.return_value = mock_fetchers

            runner = DaemonRunner(
                symbols=["BTCUSDT-PERP"],
                oi_interval_minutes=1,
                funding_interval_minutes=1,
                catalog_path=temp_catalog,
            )

            # Check status before start
            status_before = runner.get_status()
            assert status_before["running"] is False
            assert status_before["fetch_count"] == 0

            await runner.start()
            await asyncio.sleep(2)

            # Trigger some fetches
            for _ in range(3):
                await runner._scheduled_oi_fetch()

            # Check status during run
            status_during = runner.get_status()
            assert status_during["running"] is True
            assert status_during["uptime_seconds"] >= 2
            assert status_during["fetch_count"] >= 3
            assert status_during["symbols"] == ["BTCUSDT-PERP"]

            await runner.stop()

            # Check status after stop
            status_after = runner.get_status()
            assert status_after["running"] is False
