"""Unit tests for exchange fetchers."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from scripts.ccxt_pipeline.fetchers.binance import BinanceFetcher
from scripts.ccxt_pipeline.fetchers.bybit import BybitFetcher
from scripts.ccxt_pipeline.fetchers.hyperliquid import HyperliquidFetcher
from scripts.ccxt_pipeline.models import OpenInterest, Venue


class TestBinanceFetcher:
    """Tests for BinanceFetcher."""

    @pytest.fixture
    def fetcher(self) -> BinanceFetcher:
        """Create a BinanceFetcher instance."""
        return BinanceFetcher()

    def test_venue_name(self, fetcher: BinanceFetcher) -> None:
        """Test venue name property."""
        assert fetcher.venue_name == "BINANCE"

    def test_ccxt_id(self, fetcher: BinanceFetcher) -> None:
        """Test ccxt_id property."""
        assert fetcher.ccxt_id == "binance"

    def test_normalize_symbol(self, fetcher: BinanceFetcher) -> None:
        """Test symbol normalization."""
        # Standard format
        assert fetcher.normalize_symbol("BTCUSDT-PERP") == "BTC/USDT:USDT"
        assert fetcher.normalize_symbol("ETHUSDT-PERP") == "ETH/USDT:USDT"
        # Hyphen-delimited format
        assert fetcher.normalize_symbol("BTC-USDT-PERP") == "BTC/USDT:USDT"
        assert fetcher.normalize_symbol("ETH-USDT") == "ETH/USDT:USDT"
        # Already normalized (passthrough)
        assert fetcher.normalize_symbol("BTC/USDT:USDT") == "BTC/USDT:USDT"
        assert fetcher.normalize_symbol("SOL/USDT:USDT") == "SOL/USDT:USDT"
        # USD quote
        assert fetcher.normalize_symbol("BTCUSD-PERP") == "BTC/USD:USD"

    @pytest.mark.asyncio
    async def test_fetch_open_interest(self, fetcher: BinanceFetcher) -> None:
        """Test fetching current open interest."""
        mock_response = {
            "symbol": "BTC/USDT:USDT",
            "openInterestAmount": 125432.50,
            "openInterestValue": 12543250000.0,
            "timestamp": 1705320000000,
        }

        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_open_interest = AsyncMock(return_value=mock_response)
            fetcher._connected = True

            result = await fetcher.fetch_open_interest("BTCUSDT-PERP")

            assert isinstance(result, OpenInterest)
            assert result.symbol == "BTCUSDT-PERP"
            assert result.venue == Venue.BINANCE
            assert result.open_interest == 125432.50
            assert result.open_interest_value == 12543250000.0


class TestBybitFetcher:
    """Tests for BybitFetcher."""

    @pytest.fixture
    def fetcher(self) -> BybitFetcher:
        """Create a BybitFetcher instance."""
        return BybitFetcher()

    def test_venue_name(self, fetcher: BybitFetcher) -> None:
        """Test venue name property."""
        assert fetcher.venue_name == "BYBIT"

    def test_ccxt_id(self, fetcher: BybitFetcher) -> None:
        """Test ccxt_id property."""
        assert fetcher.ccxt_id == "bybit"

    def test_normalize_symbol(self, fetcher: BybitFetcher) -> None:
        """Test symbol normalization."""
        assert fetcher.normalize_symbol("BTCUSDT-PERP") == "BTC/USDT:USDT"

    @pytest.mark.asyncio
    async def test_fetch_open_interest(self, fetcher: BybitFetcher) -> None:
        """Test fetching current open interest."""
        mock_response = {
            "symbol": "BTC/USDT:USDT",
            "openInterestAmount": 85123.25,
            "openInterestValue": 8512325000.0,
            "timestamp": 1705320000000,
        }

        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_open_interest = AsyncMock(return_value=mock_response)
            fetcher._connected = True

            result = await fetcher.fetch_open_interest("BTCUSDT-PERP")

            assert isinstance(result, OpenInterest)
            assert result.symbol == "BTCUSDT-PERP"
            assert result.venue == Venue.BYBIT
            assert result.open_interest == 85123.25


class TestHyperliquidFetcher:
    """Tests for HyperliquidFetcher."""

    @pytest.fixture
    def fetcher(self) -> HyperliquidFetcher:
        """Create a HyperliquidFetcher instance."""
        return HyperliquidFetcher()

    def test_venue_name(self, fetcher: HyperliquidFetcher) -> None:
        """Test venue name property."""
        assert fetcher.venue_name == "HYPERLIQUID"

    def test_ccxt_id(self, fetcher: HyperliquidFetcher) -> None:
        """Test ccxt_id property."""
        assert fetcher.ccxt_id == "hyperliquid"

    def test_normalize_symbol(self, fetcher: HyperliquidFetcher) -> None:
        """Test symbol normalization for Hyperliquid."""
        # Hyperliquid uses different symbol format
        assert fetcher.normalize_symbol("BTC-USD-PERP") == "BTC/USD:USD"

    @pytest.mark.asyncio
    async def test_fetch_open_interest(self, fetcher: HyperliquidFetcher) -> None:
        """Test fetching current open interest."""
        mock_response = {
            "symbol": "BTC/USD:USD",
            "openInterestAmount": 42567.10,
            "openInterestValue": 4256710000.0,
            "timestamp": 1705320000000,
        }

        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_open_interest = AsyncMock(return_value=mock_response)
            fetcher._connected = True

            result = await fetcher.fetch_open_interest("BTC-USD-PERP")

            assert isinstance(result, OpenInterest)
            assert result.symbol == "BTC-USD-PERP"
            assert result.venue == Venue.HYPERLIQUID
            assert result.open_interest == 42567.10


class TestBinanceFetcherHistory:
    """Tests for BinanceFetcher history methods (T035-T037)."""

    @pytest.fixture
    def fetcher(self) -> BinanceFetcher:
        """Create a BinanceFetcher instance."""
        return BinanceFetcher()

    @pytest.mark.asyncio
    async def test_fetch_oi_history(self, fetcher: BinanceFetcher) -> None:
        """Test fetching historical open interest (T035)."""
        base_ts = 1705320000000  # Jan 15, 2024

        # Simulate paginated response (2 pages)
        page1 = [
            {
                "symbol": "BTC/USDT:USDT",
                "openInterestAmount": 120000.0 + i * 1000,
                "openInterestValue": 12000000000.0 + i * 100000000,
                "timestamp": base_ts + i * 300000,  # 5-min intervals
            }
            for i in range(5)
        ]
        page2 = [
            {
                "symbol": "BTC/USDT:USDT",
                "openInterestAmount": 125000.0 + i * 1000,
                "openInterestValue": 12500000000.0 + i * 100000000,
                "timestamp": base_ts + 1500000 + i * 300000,
            }
            for i in range(3)
        ]

        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_open_interest_history = AsyncMock(
                side_effect=[page1, page2, []]
            )
            fetcher._connected = True

            start = datetime.fromtimestamp(base_ts / 1000, tz=timezone.utc)
            end = datetime.fromtimestamp((base_ts + 3600000) / 1000, tz=timezone.utc)

            results = await fetcher.fetch_open_interest_history(
                "BTCUSDT-PERP", start, end
            )

            assert len(results) == 8
            assert all(isinstance(r, OpenInterest) for r in results)
            assert all(r.venue == Venue.BINANCE for r in results)
            assert all(r.symbol == "BTCUSDT-PERP" for r in results)

    @pytest.mark.asyncio
    async def test_pagination_handles_empty_response(
        self, fetcher: BinanceFetcher
    ) -> None:
        """Test pagination stops on empty response (T036)."""
        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_open_interest_history = AsyncMock(return_value=[])
            fetcher._connected = True

            start = datetime(2024, 1, 15, tzinfo=timezone.utc)
            end = datetime(2024, 1, 16, tzinfo=timezone.utc)

            results = await fetcher.fetch_open_interest_history(
                "BTCUSDT-PERP", start, end
            )

            assert results == []
            mock_exchange.fetch_open_interest_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_pagination_respects_end_date(self, fetcher: BinanceFetcher) -> None:
        """Test pagination stops when records exceed end date (T036)."""
        base_ts = 1705320000000

        # Return data that goes past end date
        records = [
            {
                "symbol": "BTC/USDT:USDT",
                "openInterestAmount": 120000.0,
                "openInterestValue": 12000000000.0,
                "timestamp": base_ts + i * 3600000,  # 1-hour intervals
            }
            for i in range(10)  # 10 hours of data
        ]

        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_open_interest_history = AsyncMock(return_value=records)
            fetcher._connected = True

            start = datetime.fromtimestamp(base_ts / 1000, tz=timezone.utc)
            # Only want 3 hours of data
            end = datetime.fromtimestamp((base_ts + 10800000) / 1000, tz=timezone.utc)

            results = await fetcher.fetch_open_interest_history(
                "BTCUSDT-PERP", start, end
            )

            # Should only include records within the date range
            assert len(results) == 4  # 0h, 1h, 2h, 3h


class TestBybitFetcherHistory:
    """Tests for BybitFetcher history methods with chunk workaround."""

    @pytest.fixture
    def fetcher(self) -> BybitFetcher:
        """Create a BybitFetcher instance."""
        return BybitFetcher()

    @pytest.mark.asyncio
    async def test_fetch_oi_history_with_lower_limit(
        self, fetcher: BybitFetcher
    ) -> None:
        """Test Bybit uses lower pagination limit (200 vs 500)."""
        # Verify the limit constant
        assert fetcher.OI_HISTORY_LIMIT == 200
        assert fetcher.FUNDING_HISTORY_LIMIT == 200

    @pytest.mark.asyncio
    async def test_fetch_oi_history_handles_api_error(
        self, fetcher: BybitFetcher
    ) -> None:
        """Test Bybit history handles API errors gracefully."""
        with patch.object(fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_open_interest_history = AsyncMock(
                side_effect=Exception("API rate limit")
            )
            fetcher._connected = True

            start = datetime(2024, 1, 15, tzinfo=timezone.utc)
            end = datetime(2024, 1, 16, tzinfo=timezone.utc)

            # Should not raise, returns empty list on error
            results = await fetcher.fetch_open_interest_history(
                "BTCUSDT-PERP", start, end
            )

            assert results == []


class TestFetchFundingRate:
    """Tests for funding rate fetching (T043-T044)."""

    @pytest.fixture
    def binance_fetcher(self) -> BinanceFetcher:
        """Create a BinanceFetcher instance."""
        return BinanceFetcher()

    @pytest.fixture
    def bybit_fetcher(self) -> BybitFetcher:
        """Create a BybitFetcher instance."""
        return BybitFetcher()

    @pytest.fixture
    def hyperliquid_fetcher(self) -> HyperliquidFetcher:
        """Create a HyperliquidFetcher instance."""
        return HyperliquidFetcher()

    @pytest.mark.asyncio
    async def test_fetch_funding_binance(self, binance_fetcher: BinanceFetcher) -> None:
        """Test fetching current funding rate from Binance (T043)."""
        from scripts.ccxt_pipeline.models import FundingRate

        mock_response = {
            "symbol": "BTC/USDT:USDT",
            "fundingRate": 0.0001,
            "fundingTimestamp": 1705348800000,  # 8h later
            "timestamp": 1705320000000,
        }

        with patch.object(binance_fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_funding_rate = AsyncMock(return_value=mock_response)
            binance_fetcher._connected = True

            result = await binance_fetcher.fetch_funding_rate("BTCUSDT-PERP")

            assert isinstance(result, FundingRate)
            assert result.symbol == "BTCUSDT-PERP"
            assert result.venue == Venue.BINANCE
            assert result.funding_rate == 0.0001
            assert result.next_funding_time is not None

    @pytest.mark.asyncio
    async def test_fetch_funding_bybit(self, bybit_fetcher: BybitFetcher) -> None:
        """Test fetching current funding rate from Bybit (T043)."""
        from scripts.ccxt_pipeline.models import FundingRate

        mock_response = {
            "symbol": "BTC/USDT:USDT",
            "fundingRate": -0.00015,  # Negative = shorts pay longs
            "fundingTimestamp": 1705348800000,
            "timestamp": 1705320000000,
        }

        with patch.object(bybit_fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_funding_rate = AsyncMock(return_value=mock_response)
            bybit_fetcher._connected = True

            result = await bybit_fetcher.fetch_funding_rate("BTCUSDT-PERP")

            assert isinstance(result, FundingRate)
            assert result.venue == Venue.BYBIT
            assert result.funding_rate == -0.00015

    @pytest.mark.asyncio
    async def test_fetch_funding_hyperliquid(
        self, hyperliquid_fetcher: HyperliquidFetcher
    ) -> None:
        """Test fetching current funding rate from Hyperliquid (T043)."""
        from scripts.ccxt_pipeline.models import FundingRate

        mock_response = {
            "symbol": "BTC/USD:USD",
            "fundingRate": 0.00008,
            "fundingTimestamp": 1705323600000,  # 1h interval for Hyperliquid
            "timestamp": 1705320000000,
        }

        with patch.object(
            hyperliquid_fetcher, "_exchange", create=True
        ) as mock_exchange:
            mock_exchange.fetch_funding_rate = AsyncMock(return_value=mock_response)
            hyperliquid_fetcher._connected = True

            result = await hyperliquid_fetcher.fetch_funding_rate("BTC-USD-PERP")

            assert isinstance(result, FundingRate)
            assert result.venue == Venue.HYPERLIQUID
            assert result.funding_rate == 0.00008

    @pytest.mark.asyncio
    async def test_fetch_funding_history(self, binance_fetcher: BinanceFetcher) -> None:
        """Test fetching historical funding rates (T044)."""
        from scripts.ccxt_pipeline.models import FundingRate

        base_ts = 1705320000000

        # 8-hour intervals for funding history
        records = [
            {
                "symbol": "BTC/USDT:USDT",
                "fundingRate": 0.0001 + i * 0.00001,
                "fundingTimestamp": base_ts + (i + 1) * 28800000,
                "timestamp": base_ts + i * 28800000,
            }
            for i in range(3)  # 3 funding periods
        ]

        with patch.object(binance_fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.fetch_funding_rate_history = AsyncMock(
                side_effect=[records, []]
            )
            binance_fetcher._connected = True

            start = datetime.fromtimestamp(base_ts / 1000, tz=timezone.utc)
            end = datetime.fromtimestamp((base_ts + 86400000) / 1000, tz=timezone.utc)

            results = await binance_fetcher.fetch_funding_rate_history(
                "BTCUSDT-PERP", start, end
            )

            assert len(results) == 3
            assert all(isinstance(r, FundingRate) for r in results)
            assert all(r.venue == Venue.BINANCE for r in results)


class TestStreamLiquidations:
    """Tests for liquidation streaming (T050, T051)."""

    @pytest.fixture
    def binance_fetcher(self) -> BinanceFetcher:
        """Create a BinanceFetcher instance."""
        return BinanceFetcher()

    @pytest.fixture
    def bybit_fetcher(self) -> BybitFetcher:
        """Create a BybitFetcher instance."""
        return BybitFetcher()

    @pytest.fixture
    def hyperliquid_fetcher(self) -> HyperliquidFetcher:
        """Create a HyperliquidFetcher instance."""
        return HyperliquidFetcher()

    @pytest.mark.asyncio
    async def test_stream_liquidations_binance(
        self, binance_fetcher: BinanceFetcher
    ) -> None:
        """Test streaming liquidations from Binance via WebSocket (T050)."""
        from scripts.ccxt_pipeline.models import Liquidation, Side

        # Mock WebSocket liquidation data (CCXT format)
        mock_liquidation = {
            "symbol": "BTC/USDT:USDT",
            "side": "sell",  # Position that was liquidated (long position)
            "price": 99500.0,
            "amount": 1.25,
            "timestamp": 1705320000000,
        }

        received_liquidations: list[Liquidation] = []

        def callback(liq: Liquidation) -> None:
            received_liquidations.append(liq)

        with patch.object(binance_fetcher, "_exchange", create=True) as mock_exchange:
            # Mock watch_liquidations to return data once then raise to stop loop
            mock_exchange.watch_liquidations = AsyncMock(
                side_effect=[[mock_liquidation], asyncio.CancelledError()]
            )
            binance_fetcher._connected = True

            # Run streaming with timeout
            with pytest.raises(asyncio.CancelledError):
                await binance_fetcher.stream_liquidations("BTCUSDT-PERP", callback)

            # Verify callback was called with correct data
            assert len(received_liquidations) == 1
            liq = received_liquidations[0]
            assert isinstance(liq, Liquidation)
            assert liq.symbol == "BTCUSDT-PERP"
            assert liq.venue == Venue.BINANCE
            assert liq.side == Side.LONG  # sell = long position liquidated
            assert liq.price == 99500.0
            assert liq.quantity == 1.25

    @pytest.mark.asyncio
    async def test_stream_liquidations_bybit(self, bybit_fetcher: BybitFetcher) -> None:
        """Test streaming liquidations from Bybit via WebSocket (T050)."""
        from scripts.ccxt_pipeline.models import Liquidation, Side

        mock_liquidation = {
            "symbol": "BTC/USDT:USDT",
            "side": "buy",  # Position that was liquidated (short position)
            "price": 100500.0,
            "amount": 0.5,
            "timestamp": 1705320000000,
        }

        received_liquidations: list[Liquidation] = []

        def callback(liq: Liquidation) -> None:
            received_liquidations.append(liq)

        with patch.object(bybit_fetcher, "_exchange", create=True) as mock_exchange:
            mock_exchange.watch_liquidations = AsyncMock(
                side_effect=[[mock_liquidation], asyncio.CancelledError()]
            )
            bybit_fetcher._connected = True

            with pytest.raises(asyncio.CancelledError):
                await bybit_fetcher.stream_liquidations("BTCUSDT-PERP", callback)

            assert len(received_liquidations) == 1
            liq = received_liquidations[0]
            assert liq.side == Side.SHORT  # buy = short position liquidated
            assert liq.venue == Venue.BYBIT

    @pytest.mark.asyncio
    async def test_stream_liquidations_hyperliquid_polling(
        self, hyperliquid_fetcher: HyperliquidFetcher
    ) -> None:
        """Test Hyperliquid uses polling fallback for liquidations (T050)."""
        from scripts.ccxt_pipeline.models import Liquidation

        # Hyperliquid returns liquidations via REST API polling
        mock_liquidations = [
            {
                "symbol": "BTC/USD:USD",
                "side": "sell",
                "price": 99000.0,
                "amount": 2.0,
                "timestamp": 1705320000000,
            }
        ]

        received_liquidations: list[Liquidation] = []

        def callback(liq: Liquidation) -> None:
            received_liquidations.append(liq)

        with patch.object(
            hyperliquid_fetcher, "_exchange", create=True
        ) as mock_exchange:
            # Hyperliquid uses fetch_liquidations (polling) instead of watch
            mock_exchange.fetch_liquidations = AsyncMock(
                side_effect=[mock_liquidations, asyncio.CancelledError()]
            )
            hyperliquid_fetcher._connected = True

            with pytest.raises(asyncio.CancelledError):
                await hyperliquid_fetcher.stream_liquidations("BTC-USD-PERP", callback)

            assert len(received_liquidations) == 1
            assert received_liquidations[0].venue == Venue.HYPERLIQUID


class TestWebSocketReconnect:
    """Tests for WebSocket reconnection with exponential backoff (T051)."""

    @pytest.fixture
    def binance_fetcher(self) -> BinanceFetcher:
        """Create a BinanceFetcher instance."""
        return BinanceFetcher()

    @pytest.mark.asyncio
    async def test_websocket_reconnect_on_error(
        self, binance_fetcher: BinanceFetcher
    ) -> None:
        """Test WebSocket reconnects on connection error (T051)."""
        from scripts.ccxt_pipeline.models import Liquidation

        mock_liquidation = {
            "symbol": "BTC/USDT:USDT",
            "side": "sell",
            "price": 99500.0,
            "amount": 1.0,
            "timestamp": 1705320000000,
        }

        received_liquidations: list[Liquidation] = []

        def callback(liq: Liquidation) -> None:
            received_liquidations.append(liq)

        with patch.object(binance_fetcher, "_exchange", create=True) as mock_exchange:
            # First call fails, second succeeds, third raises to stop
            mock_exchange.watch_liquidations = AsyncMock(
                side_effect=[
                    Exception("Connection lost"),  # First attempt fails
                    [mock_liquidation],  # Second attempt succeeds
                    asyncio.CancelledError(),  # Stop loop
                ]
            )
            binance_fetcher._connected = True

            # Mock sleep to speed up test
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(asyncio.CancelledError):
                    await binance_fetcher.stream_liquidations("BTCUSDT-PERP", callback)

            # Should have received data after reconnect
            assert len(received_liquidations) == 1

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(
        self, binance_fetcher: BinanceFetcher
    ) -> None:
        """Test exponential backoff uses correct delays (T051)."""
        from scripts.ccxt_pipeline.utils.reconnect import ExponentialBackoff

        backoff = ExponentialBackoff(
            initial_delay=1.0,
            max_delay=16.0,
            max_retries=5,
            multiplier=2.0,
        )

        # Verify delays follow exponential pattern
        assert backoff.get_delay(0) == 1.0  # 1s
        assert backoff.get_delay(1) == 2.0  # 2s
        assert backoff.get_delay(2) == 4.0  # 4s
        assert backoff.get_delay(3) == 8.0  # 8s
        assert backoff.get_delay(4) == 16.0  # 16s (max)
        assert backoff.get_delay(5) == 16.0  # Stays at max

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, binance_fetcher: BinanceFetcher) -> None:
        """Test that streaming stops after max retries exceeded (T051)."""
        from scripts.ccxt_pipeline.models import Liquidation

        callback_count = 0

        def callback(liq: Liquidation) -> None:
            nonlocal callback_count
            callback_count += 1

        with patch.object(binance_fetcher, "_exchange", create=True) as mock_exchange:
            # All attempts fail
            mock_exchange.watch_liquidations = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            binance_fetcher._connected = True

            # Mock sleep to speed up test
            with patch("asyncio.sleep", new_callable=AsyncMock):
                # Should raise after max retries
                with pytest.raises(ConnectionError, match="Max retries exceeded"):
                    await binance_fetcher.stream_liquidations("BTCUSDT-PERP", callback)

            # Callback should not have been called
            assert callback_count == 0
