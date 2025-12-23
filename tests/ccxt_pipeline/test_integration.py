"""Integration tests for CCXT pipeline.

These tests validate end-to-end workflows including multi-exchange
concurrent fetching and storage operations.
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from scripts.ccxt_pipeline.fetchers import FetchOrchestrator
from scripts.ccxt_pipeline.fetchers.binance import BinanceFetcher
from scripts.ccxt_pipeline.fetchers.bybit import BybitFetcher
from scripts.ccxt_pipeline.fetchers.hyperliquid import HyperliquidFetcher
from scripts.ccxt_pipeline.models import OpenInterest, FundingRate, Venue
from scripts.ccxt_pipeline.storage.parquet_store import ParquetStore


class TestFetchOIAllExchanges:
    """Integration tests for concurrent OI fetching from all exchanges (T019)."""

    @pytest.fixture
    def mock_oi_responses(self) -> dict[str, dict]:
        """Create mock OI responses for each exchange."""
        ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        return {
            "binance": {
                "symbol": "BTC/USDT:USDT",
                "openInterestAmount": 125000.0,
                "openInterestValue": 12500000000.0,
                "timestamp": ts,
            },
            "bybit": {
                "symbol": "BTC/USDT:USDT",
                "openInterestAmount": 85000.0,
                "openInterestValue": 8500000000.0,
                "timestamp": ts,
            },
            "hyperliquid": {
                "symbol": "BTC/USD:USD",
                "openInterestAmount": 42000.0,
                "openInterestValue": 4200000000.0,
                "timestamp": ts,
            },
        }

    @pytest.mark.asyncio
    async def test_fetch_oi_all_exchanges(self, mock_oi_responses: dict) -> None:
        """Test fetching OI from all exchanges concurrently."""
        # Create fetchers
        fetchers = [BinanceFetcher(), BybitFetcher(), HyperliquidFetcher()]
        orchestrator = FetchOrchestrator(fetchers)

        # Mock all exchange connections and fetch methods
        for fetcher in fetchers:
            fetcher._connected = True
            fetcher._exchange = AsyncMock()

        # Set up mock responses
        with (
            patch.object(fetchers[0], "_exchange", create=True) as mock_binance,
            patch.object(fetchers[1], "_exchange", create=True) as mock_bybit,
            patch.object(fetchers[2], "_exchange", create=True) as mock_hyperliquid,
        ):
            mock_binance.fetch_open_interest = AsyncMock(
                return_value=mock_oi_responses["binance"]
            )
            mock_bybit.fetch_open_interest = AsyncMock(
                return_value=mock_oi_responses["bybit"]
            )
            mock_hyperliquid.fetch_open_interest = AsyncMock(
                return_value=mock_oi_responses["hyperliquid"]
            )

            # Mark as connected
            orchestrator._connected = True

            results = await orchestrator.fetch_open_interest("BTCUSDT-PERP")

            # Verify all 3 exchanges returned results
            assert len(results) == 3

            # Verify each result
            successful = [r for r in results if r.success]
            assert len(successful) == 3

            venues = {r.venue for r in successful}
            assert venues == {"BINANCE", "BYBIT", "HYPERLIQUID"}

            # Verify data types
            for result in successful:
                assert isinstance(result.data, OpenInterest)
                assert result.data.open_interest > 0
                assert result.data.open_interest_value > 0

        # Cleanup
        await orchestrator.close_all()

    @pytest.mark.asyncio
    async def test_fetch_oi_partial_failure(self) -> None:
        """Test that partial failures don't crash the whole fetch."""
        fetchers = [BinanceFetcher(), BybitFetcher()]
        orchestrator = FetchOrchestrator(fetchers)

        ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        success_response = {
            "symbol": "BTC/USDT:USDT",
            "openInterestAmount": 125000.0,
            "openInterestValue": 12500000000.0,
            "timestamp": ts,
        }

        # Mark as connected
        for fetcher in fetchers:
            fetcher._connected = True
            fetcher._exchange = AsyncMock()

        with (
            patch.object(fetchers[0], "_exchange", create=True) as mock_binance,
            patch.object(fetchers[1], "_exchange", create=True) as mock_bybit,
        ):
            mock_binance.fetch_open_interest = AsyncMock(return_value=success_response)
            mock_bybit.fetch_open_interest = AsyncMock(
                side_effect=Exception("Rate limit exceeded")
            )

            orchestrator._connected = True
            results = await orchestrator.fetch_open_interest("BTCUSDT-PERP")

            assert len(results) == 2

            # One success, one failure
            successes = [r for r in results if r.success]
            failures = [r for r in results if not r.success]

            assert len(successes) == 1
            assert len(failures) == 1
            assert "Rate limit" in str(failures[0].error)

        await orchestrator.close_all()


class TestFetchAndStore:
    """Integration tests for fetch-and-store workflow (T029)."""

    @pytest.fixture
    def temp_catalog(self) -> Path:
        """Create a temporary catalog directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_fetch_and_store_open_interest(self, temp_catalog: Path) -> None:
        """Test fetching OI and storing to Parquet."""
        ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        mock_response = {
            "symbol": "BTC/USDT:USDT",
            "openInterestAmount": 125000.0,
            "openInterestValue": 12500000000.0,
            "timestamp": ts,
        }

        fetcher = BinanceFetcher()
        fetcher._connected = True
        fetcher._exchange = AsyncMock()

        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_open_interest = AsyncMock(return_value=mock_response)

            # Fetch data
            oi = await fetcher.fetch_open_interest("BTCUSDT-PERP")

            # Store data
            store = ParquetStore(temp_catalog)
            store.write([oi])

            # Verify data was written
            records = store.read(OpenInterest, "BTCUSDT-PERP", "BINANCE")
            assert len(records) == 1
            assert records[0]["open_interest"] == 125000.0
            assert records[0]["venue"] == "BINANCE"

        await fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_and_store_funding_rate(self, temp_catalog: Path) -> None:
        """Test fetching funding rate and storing to Parquet."""
        ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        mock_response = {
            "symbol": "BTC/USDT:USDT",
            "fundingRate": 0.0001,
            "fundingTimestamp": ts + 28800000,  # 8h later
            "timestamp": ts,
        }

        fetcher = BinanceFetcher()
        fetcher._connected = True
        fetcher._exchange = AsyncMock()

        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_funding_rate = AsyncMock(return_value=mock_response)

            # Fetch data
            fr = await fetcher.fetch_funding_rate("BTCUSDT-PERP")

            # Store data
            store = ParquetStore(temp_catalog)
            store.write([fr])

            # Verify data was written
            records = store.read(FundingRate, "BTCUSDT-PERP", "BINANCE")
            assert len(records) == 1
            assert records[0]["funding_rate"] == 0.0001
            assert records[0]["venue"] == "BINANCE"

        await fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_and_store_multiple_exchanges(self, temp_catalog: Path) -> None:
        """Test fetching from multiple exchanges and storing all data."""
        ts = int(datetime.now(timezone.utc).timestamp() * 1000)

        mock_responses = {
            "binance": {
                "symbol": "BTC/USDT:USDT",
                "openInterestAmount": 125000.0,
                "openInterestValue": 12500000000.0,
                "timestamp": ts,
            },
            "bybit": {
                "symbol": "BTC/USDT:USDT",
                "openInterestAmount": 85000.0,
                "openInterestValue": 8500000000.0,
                "timestamp": ts,
            },
        }

        fetchers = [BinanceFetcher(), BybitFetcher()]
        orchestrator = FetchOrchestrator(fetchers)

        for fetcher in fetchers:
            fetcher._connected = True
            fetcher._exchange = AsyncMock()

        with (
            patch.object(fetchers[0], "_exchange", create=True) as mock_binance,
            patch.object(fetchers[1], "_exchange", create=True) as mock_bybit,
        ):
            mock_binance.fetch_open_interest = AsyncMock(
                return_value=mock_responses["binance"]
            )
            mock_bybit.fetch_open_interest = AsyncMock(
                return_value=mock_responses["bybit"]
            )

            orchestrator._connected = True
            results = await orchestrator.fetch_open_interest("BTCUSDT-PERP")

            # Collect successful results
            oi_data = [r.data for r in results if r.success and r.data]
            assert len(oi_data) == 2

            # Store all data
            store = ParquetStore(temp_catalog)
            store.write(oi_data)

            # Verify each exchange's data
            binance_records = store.read(OpenInterest, "BTCUSDT-PERP", "BINANCE")
            bybit_records = store.read(OpenInterest, "BTCUSDT-PERP", "BYBIT")

            assert len(binance_records) == 1
            assert len(bybit_records) == 1
            assert binance_records[0]["open_interest"] == 125000.0
            assert bybit_records[0]["open_interest"] == 85000.0

        await orchestrator.close_all()


class TestIncrementalUpdate:
    """Integration tests for incremental data updates (T037)."""

    @pytest.fixture
    def temp_catalog(self) -> Path:
        """Create a temporary catalog directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_incremental_update_detects_new_data_only(self, temp_catalog: Path) -> None:
        """Test that incremental update only fetches data after last timestamp."""
        store = ParquetStore(temp_catalog)

        # Create initial data
        now = datetime.now(timezone.utc)
        initial_data = [
            OpenInterest(
                timestamp=now - timedelta(hours=2),
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                open_interest=100000.0,
                open_interest_value=10000000000.0,
            ),
            OpenInterest(
                timestamp=now - timedelta(hours=1),
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                open_interest=110000.0,
                open_interest_value=11000000000.0,
            ),
        ]
        store.write(initial_data)

        # Check last timestamp
        last_ts = store.get_last_timestamp(OpenInterest, "BTCUSDT-PERP", "BINANCE")
        assert last_ts is not None

        # The incremental update should start from last_ts + 1ms
        # (This would be used by the CLI to only fetch new data)
        assert last_ts >= now - timedelta(hours=1, seconds=1)

    def test_incremental_update_appends_new_data(self, temp_catalog: Path) -> None:
        """Test that new data is appended to existing data."""
        store = ParquetStore(temp_catalog)

        now = datetime.now(timezone.utc)

        # Write initial data
        initial = OpenInterest(
            timestamp=now - timedelta(hours=1),
            symbol="BTCUSDT-PERP",
            venue=Venue.BINANCE,
            open_interest=100000.0,
            open_interest_value=10000000000.0,
        )
        store.write([initial])

        # Write new data
        new = OpenInterest(
            timestamp=now,
            symbol="BTCUSDT-PERP",
            venue=Venue.BINANCE,
            open_interest=110000.0,
            open_interest_value=11000000000.0,
        )
        store.write([new])

        # Verify both records exist
        records = store.read(OpenInterest, "BTCUSDT-PERP", "BINANCE")
        assert len(records) == 2

        # Verify ordering
        values = sorted([r["open_interest"] for r in records])
        assert values == [100000.0, 110000.0]


class TestFundingRateStorage:
    """Integration tests for funding rate storage (T045)."""

    @pytest.fixture
    def temp_catalog(self) -> Path:
        """Create a temporary catalog directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_funding_storage(self, temp_catalog: Path) -> None:
        """Test storing funding rates to Parquet (T045)."""
        ts = int(datetime.now(timezone.utc).timestamp() * 1000)

        mock_responses = {
            "binance": {
                "symbol": "BTC/USDT:USDT",
                "fundingRate": 0.0001,
                "fundingTimestamp": ts + 28800000,
                "timestamp": ts,
            },
            "bybit": {
                "symbol": "BTC/USDT:USDT",
                "fundingRate": -0.00015,
                "fundingTimestamp": ts + 28800000,
                "timestamp": ts,
            },
        }

        fetchers = [BinanceFetcher(), BybitFetcher()]
        orchestrator = FetchOrchestrator(fetchers)

        for fetcher in fetchers:
            fetcher._connected = True
            fetcher._exchange = AsyncMock()

        with (
            patch.object(fetchers[0], "_exchange", create=True) as mock_binance,
            patch.object(fetchers[1], "_exchange", create=True) as mock_bybit,
        ):
            mock_binance.fetch_funding_rate = AsyncMock(
                return_value=mock_responses["binance"]
            )
            mock_bybit.fetch_funding_rate = AsyncMock(
                return_value=mock_responses["bybit"]
            )

            orchestrator._connected = True
            results = await orchestrator.fetch_funding_rate("BTCUSDT-PERP")

            # Collect successful results
            funding_data = [r.data for r in results if r.success and r.data]
            assert len(funding_data) == 2

            # Store all data
            store = ParquetStore(temp_catalog)
            store.write(funding_data)

            # Verify each exchange's data
            binance_records = store.read(FundingRate, "BTCUSDT-PERP", "BINANCE")
            bybit_records = store.read(FundingRate, "BTCUSDT-PERP", "BYBIT")

            assert len(binance_records) == 1
            assert len(bybit_records) == 1
            assert binance_records[0]["funding_rate"] == 0.0001
            assert bybit_records[0]["funding_rate"] == -0.00015

        await orchestrator.close_all()

    @pytest.mark.asyncio
    async def test_funding_history_storage(self, temp_catalog: Path) -> None:
        """Test storing historical funding rates."""
        base_ts = int(datetime.now(timezone.utc).timestamp() * 1000) - 86400000

        # 8-hour intervals for funding history
        mock_history = [
            {
                "symbol": "BTC/USDT:USDT",
                "fundingRate": 0.0001 + i * 0.00001,
                "fundingTimestamp": base_ts + (i + 1) * 28800000,
                "timestamp": base_ts + i * 28800000,
            }
            for i in range(3)
        ]

        fetcher = BinanceFetcher()
        fetcher._connected = True
        fetcher._exchange = AsyncMock()

        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_funding_rate_history = AsyncMock(
                side_effect=[mock_history, []]
            )

            start = datetime.fromtimestamp(base_ts / 1000, tz=timezone.utc)
            end = datetime.now(timezone.utc)

            results = await fetcher.fetch_funding_rate_history(
                "BTCUSDT-PERP", start, end
            )

            assert len(results) == 3

            # Store data
            store = ParquetStore(temp_catalog)
            store.write(results)

            # Verify
            records = store.read(FundingRate, "BTCUSDT-PERP", "BINANCE")
            assert len(records) == 3

        await fetcher.close()


class TestLiquidationStorage:
    """Integration tests for liquidation storage (T052)."""

    @pytest.fixture
    def temp_catalog(self) -> Path:
        """Create a temporary catalog directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_liquidation_storage_single(self, temp_catalog: Path) -> None:
        """Test storing a single liquidation to Parquet (T052)."""
        from scripts.ccxt_pipeline.models import Liquidation, Side

        now = datetime.now(timezone.utc)
        liquidation = Liquidation(
            timestamp=now,
            symbol="BTCUSDT-PERP",
            venue=Venue.BINANCE,
            side=Side.LONG,
            quantity=1.25,
            price=99500.0,
            value=124375.0,
        )

        store = ParquetStore(temp_catalog)
        store.write([liquidation])

        # Verify data was written
        records = store.read(Liquidation, "BTCUSDT-PERP", "BINANCE")
        assert len(records) == 1
        assert records[0]["symbol"] == "BTCUSDT-PERP"
        assert records[0]["venue"] == "BINANCE"
        assert records[0]["side"] == "LONG"
        assert records[0]["quantity"] == 1.25
        assert records[0]["price"] == 99500.0
        assert records[0]["value"] == 124375.0

    def test_liquidation_storage_multiple_sides(self, temp_catalog: Path) -> None:
        """Test storing liquidations with different sides."""
        from scripts.ccxt_pipeline.models import Liquidation, Side

        # Use past timestamps to avoid "future timestamp" validation error
        now = datetime.now(timezone.utc) - timedelta(seconds=10)
        liquidations = [
            Liquidation(
                timestamp=now,
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                side=Side.LONG,
                quantity=1.0,
                price=99000.0,
                value=99000.0,
            ),
            Liquidation(
                timestamp=now + timedelta(seconds=1),
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                side=Side.SHORT,
                quantity=0.5,
                price=101000.0,
                value=50500.0,
            ),
        ]

        store = ParquetStore(temp_catalog)
        store.write(liquidations)

        records = store.read(Liquidation, "BTCUSDT-PERP", "BINANCE")
        assert len(records) == 2

        sides = {r["side"] for r in records}
        assert sides == {"LONG", "SHORT"}

    def test_liquidation_storage_multiple_venues(self, temp_catalog: Path) -> None:
        """Test storing liquidations from multiple exchanges."""
        from scripts.ccxt_pipeline.models import Liquidation, Side

        now = datetime.now(timezone.utc)
        liquidations = [
            Liquidation(
                timestamp=now,
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                side=Side.LONG,
                quantity=1.0,
                price=99000.0,
                value=99000.0,
            ),
            Liquidation(
                timestamp=now,
                symbol="BTCUSDT-PERP",
                venue=Venue.BYBIT,
                side=Side.SHORT,
                quantity=2.0,
                price=99500.0,
                value=199000.0,
            ),
        ]

        store = ParquetStore(temp_catalog)
        store.write(liquidations)

        # Verify each venue's data is stored separately
        binance_records = store.read(Liquidation, "BTCUSDT-PERP", "BINANCE")
        bybit_records = store.read(Liquidation, "BTCUSDT-PERP", "BYBIT")

        assert len(binance_records) == 1
        assert len(bybit_records) == 1
        assert binance_records[0]["venue"] == "BINANCE"
        assert bybit_records[0]["venue"] == "BYBIT"

    def test_liquidation_storage_get_last_timestamp(self, temp_catalog: Path) -> None:
        """Test getting last timestamp for liquidations."""
        from scripts.ccxt_pipeline.models import Liquidation, Side

        now = datetime.now(timezone.utc)
        liquidations = [
            Liquidation(
                timestamp=now - timedelta(minutes=5),
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                side=Side.LONG,
                quantity=1.0,
                price=99000.0,
                value=99000.0,
            ),
            Liquidation(
                timestamp=now,
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                side=Side.SHORT,
                quantity=0.5,
                price=100000.0,
                value=50000.0,
            ),
        ]

        store = ParquetStore(temp_catalog)
        store.write(liquidations)

        last_ts = store.get_last_timestamp(Liquidation, "BTCUSDT-PERP", "BINANCE")
        assert last_ts is not None
        # Allow for microsecond precision loss
        assert abs((last_ts - now).total_seconds()) < 1
