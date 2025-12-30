"""Integration test for cold start (no prior state) - FR-001.

Tests that TradingNode starts correctly with no prior cached state.
"""

import pytest


@pytest.mark.integration
@pytest.mark.recovery
class TestColdStart:
    """Integration tests for cold start scenario."""

    def test_cold_start_no_positions(self, mock_cache):
        """Test starting with empty cache (no prior positions)."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        mock_cache.positions.return_value = []

        provider = PositionRecoveryProvider(cache=mock_cache)
        positions = provider.get_cached_positions(trader_id="TESTER-001")

        assert positions == []
        assert provider.discrepancy_count == 0

    def test_cold_start_reconciliation_empty(self, mock_cache):
        """Test reconciliation with no positions on either side."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[],
            exchange=[],
        )

        assert reconciled == []
        assert discrepancies == []

    def test_cold_start_recovery_state(self, recovery_state_pending):
        """Test recovery state starts as pending."""
        from strategies.common.recovery.models import RecoveryStatus

        assert recovery_state_pending.status == RecoveryStatus.PENDING
        assert recovery_state_pending.positions_recovered == 0
        assert not recovery_state_pending.indicators_warmed
        assert not recovery_state_pending.orders_reconciled

    def test_cold_start_config_validation(self, recovery_config):
        """Test recovery config is valid for cold start."""
        assert recovery_config.recovery_enabled
        assert recovery_config.warmup_lookback_days >= 1
        assert recovery_config.startup_delay_secs >= 5.0
