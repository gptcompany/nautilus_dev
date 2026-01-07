"""Unit tests for data models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from scripts.ccxt_pipeline.models import FundingRate, Liquidation, OpenInterest, Side, Venue


class TestOpenInterest:
    """Tests for OpenInterest model."""

    def test_valid_open_interest(self, sample_open_interest: OpenInterest) -> None:
        """Test creating a valid OpenInterest."""
        assert sample_open_interest.symbol == "BTCUSDT-PERP"
        assert sample_open_interest.venue == Venue.BINANCE
        assert sample_open_interest.open_interest == 125432.50
        assert sample_open_interest.open_interest_value == 12543250000.0

    def test_symbol_normalized_to_uppercase(self) -> None:
        """Test that symbol is normalized to uppercase."""
        oi = OpenInterest(
            timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
            symbol="btcusdt-perp",
            venue=Venue.BINANCE,
            open_interest=100.0,
            open_interest_value=1000.0,
        )
        assert oi.symbol == "BTCUSDT-PERP"

    def test_empty_symbol_rejected(self) -> None:
        """Test that empty symbol is rejected."""
        with pytest.raises(ValidationError):
            OpenInterest(
                timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
                symbol="",
                venue=Venue.BINANCE,
                open_interest=100.0,
                open_interest_value=1000.0,
            )

    def test_negative_open_interest_rejected(self) -> None:
        """Test that negative open interest is rejected."""
        with pytest.raises(ValidationError):
            OpenInterest(
                timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                open_interest=-100.0,
                open_interest_value=1000.0,
            )

    def test_negative_value_rejected(self) -> None:
        """Test that negative value is rejected."""
        with pytest.raises(ValidationError):
            OpenInterest(
                timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                open_interest=100.0,
                open_interest_value=-1000.0,
            )

    def test_model_is_immutable(self, sample_open_interest: OpenInterest) -> None:
        """Test that model is immutable (frozen)."""
        with pytest.raises(ValidationError):
            sample_open_interest.open_interest = 200.0


class TestFundingRate:
    """Tests for FundingRate model."""

    def test_valid_funding_rate(self, sample_funding_rate: FundingRate) -> None:
        """Test creating a valid FundingRate."""
        assert sample_funding_rate.symbol == "BTCUSDT-PERP"
        assert sample_funding_rate.venue == Venue.BINANCE
        assert sample_funding_rate.funding_rate == 0.0001

    def test_negative_funding_rate_allowed(self) -> None:
        """Test that negative funding rate is allowed (shorts pay longs)."""
        fr = FundingRate(
            timestamp=datetime(2025, 1, 15, 8, 0, 0, tzinfo=UTC),
            symbol="BTCUSDT-PERP",
            venue=Venue.BINANCE,
            funding_rate=-0.0005,
        )
        assert fr.funding_rate == -0.0005

    def test_optional_fields(self) -> None:
        """Test that optional fields can be None."""
        fr = FundingRate(
            timestamp=datetime(2025, 1, 15, 8, 0, 0, tzinfo=UTC),
            symbol="BTCUSDT-PERP",
            venue=Venue.BINANCE,
            funding_rate=0.0001,
        )
        assert fr.next_funding_time is None
        assert fr.predicted_rate is None


class TestLiquidation:
    """Tests for Liquidation model."""

    def test_valid_liquidation(self, sample_liquidation: Liquidation) -> None:
        """Test creating a valid Liquidation."""
        assert sample_liquidation.symbol == "BTCUSDT-PERP"
        assert sample_liquidation.venue == Venue.BINANCE
        assert sample_liquidation.side == Side.LONG
        assert sample_liquidation.quantity == 1.25

    def test_short_side(self) -> None:
        """Test creating a SHORT liquidation."""
        liq = Liquidation(
            timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
            symbol="BTCUSDT-PERP",
            venue=Venue.BYBIT,
            side=Side.SHORT,
            quantity=0.5,
            price=100100.0,
            value=50050.0,
        )
        assert liq.side == Side.SHORT

    def test_zero_quantity_rejected(self) -> None:
        """Test that zero quantity is rejected."""
        with pytest.raises(ValidationError):
            Liquidation(
                timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                side=Side.LONG,
                quantity=0,
                price=100.0,
                value=100.0,
            )

    def test_zero_price_rejected(self) -> None:
        """Test that zero price is rejected."""
        with pytest.raises(ValidationError):
            Liquidation(
                timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                side=Side.LONG,
                quantity=1.0,
                price=0,
                value=100.0,
            )


class TestVenue:
    """Tests for Venue enum."""

    def test_all_venues_defined(self) -> None:
        """Test that all expected venues are defined."""
        assert Venue.BINANCE.value == "BINANCE"
        assert Venue.BYBIT.value == "BYBIT"
        assert Venue.HYPERLIQUID.value == "HYPERLIQUID"

    def test_venue_count(self) -> None:
        """Test that we have exactly 3 venues."""
        assert len(Venue) == 3


class TestSide:
    """Tests for Side enum."""

    def test_sides_defined(self) -> None:
        """Test that both sides are defined."""
        assert Side.LONG.value == "LONG"
        assert Side.SHORT.value == "SHORT"
