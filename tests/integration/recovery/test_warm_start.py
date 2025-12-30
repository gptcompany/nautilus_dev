"""Integration test for warm start (existing positions) - FR-001.

Tests that TradingNode correctly recovers positions from cache on restart.
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.mark.integration
@pytest.mark.recovery
class TestWarmStart:
    """Integration tests for warm start scenario."""

    def test_warm_start_loads_positions(self, mock_cache):
        """Test that positions are loaded from cache on warm start."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Setup cached position
        mock_position = MagicMock()
        mock_position.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        mock_position.side.value = "LONG"
        mock_position.quantity.as_decimal.return_value = Decimal("1.5")
        mock_position.is_open = True

        mock_cache.positions.return_value = [mock_position]

        provider = PositionRecoveryProvider(cache=mock_cache)
        positions = provider.get_cached_positions(trader_id="TESTER-001")

        assert len(positions) == 1
        assert positions[0].instrument_id.value == "BTCUSDT-PERP.BINANCE"

    def test_warm_start_reconciles_matching(self, mock_cache):
        """Test that matching positions reconcile without discrepancies."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Setup matching positions
        cached_pos = MagicMock()
        cached_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        cached_pos.side.value = "LONG"
        cached_pos.quantity.as_decimal.return_value = Decimal("1.0")

        exchange_pos = MagicMock()
        exchange_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        exchange_pos.side.value = "LONG"
        exchange_pos.quantity.as_decimal.return_value = Decimal("1.0")

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[cached_pos],
            exchange=[exchange_pos],
        )

        assert len(reconciled) == 1
        assert len(discrepancies) == 0

    def test_warm_start_multiple_positions(self, mock_cache):
        """Test warm start with multiple positions."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Setup multiple positions
        positions = []
        for symbol in ["BTCUSDT-PERP.BINANCE", "ETHUSDT-PERP.BINANCE"]:
            pos = MagicMock()
            pos.instrument_id.value = symbol
            pos.side.value = "LONG"
            pos.quantity.as_decimal.return_value = Decimal("1.0")
            pos.is_open = True
            positions.append(pos)

        mock_cache.positions.return_value = positions

        provider = PositionRecoveryProvider(cache=mock_cache)
        loaded = provider.get_cached_positions(trader_id="TESTER-001")

        assert len(loaded) == 2

    def test_warm_start_recovery_state_complete(self, recovery_state_complete):
        """Test recovery state after successful warm start."""
        from strategies.common.recovery.models import RecoveryStatus

        assert recovery_state_complete.status == RecoveryStatus.COMPLETED
        assert recovery_state_complete.positions_recovered == 2
        assert recovery_state_complete.indicators_warmed
        assert recovery_state_complete.orders_reconciled
        assert recovery_state_complete.is_complete

    def test_warm_start_recovery_duration(self, recovery_state_complete):
        """Test recovery duration calculation."""
        duration = recovery_state_complete.recovery_duration_ms

        assert duration is not None
        assert duration == 5000.0  # 5 seconds in milliseconds

    def test_warm_start_handles_position_mismatch(self, mock_cache):
        """Test warm start detects and reports position mismatches."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        # Setup mismatched positions
        cached_pos = MagicMock()
        cached_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        cached_pos.side.value = "LONG"
        cached_pos.quantity.as_decimal.return_value = Decimal("1.0")

        exchange_pos = MagicMock()
        exchange_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        exchange_pos.side.value = "LONG"
        exchange_pos.quantity.as_decimal.return_value = Decimal("2.0")  # Different

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[cached_pos],
            exchange=[exchange_pos],
        )

        assert len(reconciled) == 1
        assert len(discrepancies) == 1
        assert "quantity" in discrepancies[0].lower()
