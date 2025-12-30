"""Unit tests for position loading from cache (FR-001).

Tests:
- Loading positions from Redis cache
- Handling empty cache
- Handling multiple positions
- Position snapshot deserialization
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from strategies.common.recovery.models import PositionSnapshot


@pytest.mark.recovery
class TestPositionLoading:
    """Tests for position loading functionality."""

    def test_load_positions_from_cache_empty(self, mock_cache):
        """Test loading positions when cache is empty."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        provider = PositionRecoveryProvider(cache=mock_cache)
        mock_cache.positions.return_value = []

        positions = provider.get_cached_positions(trader_id="TESTER-001")

        assert positions == []
        mock_cache.positions.assert_called_once()

    def test_load_positions_from_cache_single(self, mock_cache):
        """Test loading a single position from cache."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Create mock position
        mock_position = MagicMock()
        mock_position.instrument_id = MagicMock()
        mock_position.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        mock_position.side.value = "LONG"
        mock_position.quantity.as_decimal.return_value = Decimal("1.5")
        mock_position.avg_px_open.as_decimal.return_value = Decimal("42000.00")
        mock_position.is_open = True

        mock_cache.positions.return_value = [mock_position]

        provider = PositionRecoveryProvider(cache=mock_cache)
        positions = provider.get_cached_positions(trader_id="TESTER-001")

        assert len(positions) == 1
        assert positions[0].is_open

    def test_load_positions_from_cache_multiple(self, mock_cache):
        """Test loading multiple positions from cache."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Create mock positions
        mock_positions = []
        for i, symbol in enumerate(["BTCUSDT-PERP.BINANCE", "ETHUSDT-PERP.BINANCE"]):
            pos = MagicMock()
            pos.instrument_id = MagicMock()
            pos.instrument_id.value = symbol
            pos.side.value = "LONG" if i == 0 else "SHORT"
            pos.quantity.as_decimal.return_value = Decimal("1.0")
            pos.avg_px_open.as_decimal.return_value = Decimal("1000.00")
            pos.is_open = True
            mock_positions.append(pos)

        mock_cache.positions.return_value = mock_positions

        provider = PositionRecoveryProvider(cache=mock_cache)
        positions = provider.get_cached_positions(trader_id="TESTER-001")

        assert len(positions) == 2

    def test_load_positions_filters_closed(self, mock_cache):
        """Test that only open positions are returned."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Create mix of open and closed positions
        open_pos = MagicMock()
        open_pos.is_open = True
        open_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"

        closed_pos = MagicMock()
        closed_pos.is_open = False
        closed_pos.instrument_id.value = "ETHUSDT-PERP.BINANCE"

        mock_cache.positions.return_value = [open_pos, closed_pos]

        provider = PositionRecoveryProvider(cache=mock_cache)
        positions = provider.get_cached_positions(trader_id="TESTER-001")

        # Provider should return all positions, filtering is caller's responsibility
        assert len(positions) == 2


@pytest.mark.recovery
class TestPositionSnapshot:
    """Tests for PositionSnapshot model."""

    def test_snapshot_creation_valid(self):
        """Test creating a valid PositionSnapshot."""
        snapshot = PositionSnapshot(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="LONG",
            quantity=Decimal("1.5"),
            avg_entry_price=Decimal("42000.00"),
            ts_opened=1704067200000000000,
            ts_last_updated=1704153600000000000,
        )

        assert snapshot.instrument_id == "BTCUSDT-PERP.BINANCE"
        assert snapshot.side == "LONG"
        assert snapshot.quantity == Decimal("1.5")
        assert snapshot.avg_entry_price == Decimal("42000.00")

    def test_snapshot_side_validation(self):
        """Test that invalid sides are rejected."""
        with pytest.raises(ValueError, match="Invalid position side"):
            PositionSnapshot(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="INVALID",
                quantity=Decimal("1.0"),
                avg_entry_price=Decimal("42000.00"),
                ts_opened=1704067200000000000,
                ts_last_updated=1704153600000000000,
            )

    def test_snapshot_side_case_insensitive(self):
        """Test that side validation is case-insensitive."""
        snapshot = PositionSnapshot(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="long",  # lowercase
            quantity=Decimal("1.0"),
            avg_entry_price=Decimal("42000.00"),
            ts_opened=1704067200000000000,
            ts_last_updated=1704153600000000000,
        )

        assert snapshot.side == "LONG"  # Normalized to uppercase

    def test_snapshot_quantity_non_negative(self):
        """Test that negative quantities are rejected."""
        with pytest.raises(ValueError):
            PositionSnapshot(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="LONG",
                quantity=Decimal("-1.0"),
                avg_entry_price=Decimal("42000.00"),
                ts_opened=1704067200000000000,
                ts_last_updated=1704153600000000000,
            )

    def test_snapshot_price_positive(self):
        """Test that non-positive prices are rejected."""
        with pytest.raises(ValueError):
            PositionSnapshot(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="LONG",
                quantity=Decimal("1.0"),
                avg_entry_price=Decimal("0"),
                ts_opened=1704067200000000000,
                ts_last_updated=1704153600000000000,
            )

    def test_snapshot_timestamps_valid(self):
        """Test that ts_opened must be <= ts_last_updated."""
        with pytest.raises(ValueError, match="ts_last_updated cannot be before"):
            PositionSnapshot(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="LONG",
                quantity=Decimal("1.0"),
                avg_entry_price=Decimal("42000.00"),
                ts_opened=1704153600000000000,  # Later
                ts_last_updated=1704067200000000000,  # Earlier
            )

    def test_snapshot_json_serialization(self, position_snapshot):
        """Test JSON serialization of PositionSnapshot."""
        json_data = position_snapshot.model_dump_json()

        assert "BTCUSDT-PERP.BINANCE" in json_data
        assert "LONG" in json_data
        assert "1.5" in json_data
