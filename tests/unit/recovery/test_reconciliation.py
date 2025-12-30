"""Unit tests for position reconciliation logic (FR-001).

Tests:
- Reconciling cached positions with exchange positions
- Detecting discrepancies (missing, extra, quantity mismatch)
- Resolution strategies for discrepancies
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.mark.recovery
class TestPositionReconciliation:
    """Tests for position reconciliation functionality."""

    def test_reconcile_matching_positions(self, mock_cache):
        """Test reconciliation when cache and exchange match."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Create matching positions
        cached_pos = MagicMock()
        cached_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        cached_pos.quantity.as_decimal.return_value = Decimal("1.0")
        cached_pos.side.value = "LONG"

        exchange_pos = MagicMock()
        exchange_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        exchange_pos.quantity.as_decimal.return_value = Decimal("1.0")
        exchange_pos.side.value = "LONG"

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[cached_pos],
            exchange=[exchange_pos],
        )

        assert len(reconciled) == 1
        assert len(discrepancies) == 0

    def test_reconcile_quantity_mismatch(self, mock_cache):
        """Test reconciliation detects quantity differences."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Create positions with different quantities
        cached_pos = MagicMock()
        cached_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        cached_pos.quantity.as_decimal.return_value = Decimal("1.0")
        cached_pos.side.value = "LONG"

        exchange_pos = MagicMock()
        exchange_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        exchange_pos.quantity.as_decimal.return_value = Decimal("2.0")  # Different
        exchange_pos.side.value = "LONG"

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[cached_pos],
            exchange=[exchange_pos],
        )

        assert len(reconciled) == 1
        assert len(discrepancies) == 1
        assert "quantity" in discrepancies[0].lower()

    def test_reconcile_position_missing_on_exchange(self, mock_cache):
        """Test reconciliation detects position missing on exchange."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Cached position but no exchange position
        cached_pos = MagicMock()
        cached_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        cached_pos.quantity.as_decimal.return_value = Decimal("1.0")
        cached_pos.side.value = "LONG"

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[cached_pos],
            exchange=[],  # No positions on exchange
        )

        assert len(reconciled) == 0
        assert len(discrepancies) == 1
        assert (
            "missing" in discrepancies[0].lower()
            or "closed" in discrepancies[0].lower()
        )

    def test_reconcile_position_missing_in_cache(self, mock_cache):
        """Test reconciliation detects position missing in cache (external position)."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Exchange position but no cached position
        exchange_pos = MagicMock()
        exchange_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        exchange_pos.quantity.as_decimal.return_value = Decimal("1.0")
        exchange_pos.side.value = "LONG"

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[],  # No cached positions
            exchange=[exchange_pos],
        )

        # External position should be included if claiming is enabled
        assert len(reconciled) == 1
        assert len(discrepancies) == 1
        assert "external" in discrepancies[0].lower()

    def test_reconcile_side_mismatch(self, mock_cache):
        """Test reconciliation detects side differences (LONG vs SHORT)."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Create positions with different sides
        cached_pos = MagicMock()
        cached_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        cached_pos.quantity.as_decimal.return_value = Decimal("1.0")
        cached_pos.side.value = "LONG"

        exchange_pos = MagicMock()
        exchange_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        exchange_pos.quantity.as_decimal.return_value = Decimal("1.0")
        exchange_pos.side.value = "SHORT"  # Different side

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[cached_pos],
            exchange=[exchange_pos],
        )

        assert len(discrepancies) >= 1
        assert any("side" in d.lower() for d in discrepancies)

    def test_reconcile_multiple_positions(self, mock_cache):
        """Test reconciliation with multiple positions."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Create multiple matching positions
        cached_positions = []
        exchange_positions = []

        for symbol in ["BTCUSDT-PERP.BINANCE", "ETHUSDT-PERP.BINANCE"]:
            cached = MagicMock()
            cached.instrument_id.value = symbol
            cached.quantity.as_decimal.return_value = Decimal("1.0")
            cached.side.value = "LONG"
            cached_positions.append(cached)

            exchange = MagicMock()
            exchange.instrument_id.value = symbol
            exchange.quantity.as_decimal.return_value = Decimal("1.0")
            exchange.side.value = "LONG"
            exchange_positions.append(exchange)

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=cached_positions,
            exchange=exchange_positions,
        )

        assert len(reconciled) == 2
        assert len(discrepancies) == 0

    def test_reconcile_empty_both(self, mock_cache):
        """Test reconciliation when both cache and exchange are empty."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[],
            exchange=[],
        )

        assert len(reconciled) == 0
        assert len(discrepancies) == 0
