"""TDD Tests for Hawkes OFI Indicator (Spec 025).

Tests for HawkesState, HawkesOFI, and edge cases.
These tests align with the actual implementation API.

Note: The implementation uses relative time in seconds (not nanoseconds)
for internal event timestamps to simplify Hawkes intensity calculations.

Test IDs:
- T023: HawkesState tests
- T024: HawkesOFI indicator tests
- T025: Edge case tests
"""

from __future__ import annotations

import pytest

from strategies.common.orderflow.hawkes_ofi import (
    HawkesOFI,
    HawkesState,
)
from strategies.common.orderflow.config import HawkesConfig
from strategies.common.orderflow.trade_classifier import (
    TradeClassification,
    TradeSide,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def default_config() -> HawkesConfig:
    """Default Hawkes configuration for testing."""
    return HawkesConfig(
        decay_rate=1.0,
        lookback_ticks=1000,
        refit_interval=100,
        use_fixed_params=False,
        fixed_baseline=0.1,
        fixed_excitation=0.5,
    )


@pytest.fixture
def fixed_params_config() -> HawkesConfig:
    """Configuration with fixed parameters (no fitting)."""
    return HawkesConfig(
        decay_rate=1.0,
        lookback_ticks=1000,
        refit_interval=100,
        use_fixed_params=True,
        fixed_baseline=0.1,
        fixed_excitation=0.5,
    )


@pytest.fixture
def small_buffer_config() -> HawkesConfig:
    """Configuration with small buffer for testing limits."""
    return HawkesConfig(
        decay_rate=1.0,
        lookback_ticks=100,
        refit_interval=10,
        use_fixed_params=True,
        fixed_baseline=0.1,
        fixed_excitation=0.5,
    )


@pytest.fixture
def hawkes_indicator(default_config: HawkesConfig) -> HawkesOFI:
    """Default HawkesOFI indicator instance."""
    return HawkesOFI(config=default_config)


@pytest.fixture
def fixed_hawkes_indicator(fixed_params_config: HawkesConfig) -> HawkesOFI:
    """HawkesOFI indicator with fixed parameters."""
    return HawkesOFI(config=fixed_params_config)


def make_classification(
    side: TradeSide,
    volume: float = 1.0,
    price: float = 100.0,
    timestamp_ns: int = 0,
) -> TradeClassification:
    """Helper to create TradeClassification objects."""
    return TradeClassification(
        side=side,
        volume=volume,
        price=price,
        timestamp_ns=timestamp_ns,
        method="tick_rule",
        confidence=1.0,
    )


# ==============================================================================
# T023: HawkesState Tests
# ==============================================================================


class TestHawkesStateOFI:
    """Tests for HawkesState.ofi property (T023).

    OFI = (buy_intensity - sell_intensity) / (buy_intensity + sell_intensity)
    Expected range: [-1.0, 1.0]
    """

    def test_hawkes_state_ofi_balanced(self) -> None:
        """Test that equal buy/sell intensity produces OFI = 0.0."""
        state = HawkesState(
            buy_intensity=1.0,
            sell_intensity=1.0,
            baseline=(0.1, 0.1),
            excitation=(0.5, 0.5),
            decay=1.0,
            branching_ratio=0.5,
            last_fit_time=0,
            ticks_since_fit=0,
        )
        assert state.ofi == pytest.approx(0.0, abs=1e-6)

    def test_hawkes_state_ofi_buy_dominant(self) -> None:
        """Test that buy_intensity > sell_intensity produces OFI > 0."""
        state = HawkesState(
            buy_intensity=2.0,
            sell_intensity=1.0,
            baseline=(0.1, 0.1),
            excitation=(0.5, 0.5),
            decay=1.0,
            branching_ratio=0.5,
            last_fit_time=0,
            ticks_since_fit=0,
        )
        # OFI = (2.0 - 1.0) / (2.0 + 1.0) = 1/3 = 0.333
        assert state.ofi > 0.0
        assert state.ofi == pytest.approx(1.0 / 3.0, rel=0.01)

    def test_hawkes_state_ofi_sell_dominant(self) -> None:
        """Test that sell_intensity > buy_intensity produces OFI < 0."""
        state = HawkesState(
            buy_intensity=1.0,
            sell_intensity=2.0,
            baseline=(0.1, 0.1),
            excitation=(0.5, 0.5),
            decay=1.0,
            branching_ratio=0.5,
            last_fit_time=0,
            ticks_since_fit=0,
        )
        # OFI = (1.0 - 2.0) / (1.0 + 2.0) = -1/3 = -0.333
        assert state.ofi < 0.0
        assert state.ofi == pytest.approx(-1.0 / 3.0, rel=0.01)

    def test_hawkes_state_ofi_max_buy(self) -> None:
        """Test that all buys (sell=0) produces OFI near 1.0."""
        state = HawkesState(
            buy_intensity=1.0,
            sell_intensity=0.0,
            baseline=(0.1, 0.0),
            excitation=(0.5, 0.0),
            decay=1.0,
            branching_ratio=0.5,
            last_fit_time=0,
            ticks_since_fit=0,
        )
        # OFI = (1.0 - 0.0) / (1.0 + 0.0 + eps) ~ 1.0
        assert state.ofi > 0.99

    def test_hawkes_state_ofi_max_sell(self) -> None:
        """Test that all sells (buy=0) produces OFI near -1.0."""
        state = HawkesState(
            buy_intensity=0.0,
            sell_intensity=1.0,
            baseline=(0.0, 0.1),
            excitation=(0.0, 0.5),
            decay=1.0,
            branching_ratio=0.5,
            last_fit_time=0,
            ticks_since_fit=0,
        )
        # OFI = (0.0 - 1.0) / (0.0 + 1.0 + eps) ~ -1.0
        assert state.ofi < -0.99

    def test_hawkes_state_ofi_zero_intensity(self) -> None:
        """Test that zero total intensity produces OFI = 0.0 (graceful)."""
        state = HawkesState(
            buy_intensity=0.0,
            sell_intensity=0.0,
            baseline=(0.0, 0.0),
            excitation=(0.0, 0.0),
            decay=1.0,
            branching_ratio=0.0,
            last_fit_time=0,
            ticks_since_fit=0,
        )
        # Division by zero case - should return 0.0
        assert state.ofi == pytest.approx(0.0, abs=1e-10)


# ==============================================================================
# T024: HawkesOFI Indicator Tests
# ==============================================================================


class TestHawkesInitialState:
    """Tests for initial indicator state (T024)."""

    def test_hawkes_initial_state_ofi(self, hawkes_indicator: HawkesOFI) -> None:
        """Test that new indicator has OFI = 0.0."""
        assert hawkes_indicator.ofi == pytest.approx(0.0, abs=1e-10)

    def test_hawkes_initial_state_is_fitted(self, hawkes_indicator: HawkesOFI) -> None:
        """Test that new indicator has is_fitted = False."""
        assert hawkes_indicator.is_fitted is False

    def test_hawkes_initial_state_buy_intensity(self, hawkes_indicator: HawkesOFI) -> None:
        """Test that new indicator has buy_intensity = 0.0."""
        assert hawkes_indicator.buy_intensity == pytest.approx(0.0, abs=1e-10)

    def test_hawkes_initial_state_sell_intensity(self, hawkes_indicator: HawkesOFI) -> None:
        """Test that new indicator has sell_intensity = 0.0."""
        assert hawkes_indicator.sell_intensity == pytest.approx(0.0, abs=1e-10)


class TestHawkesUpdate:
    """Tests for HawkesOFI.update() method (T024)."""

    def test_hawkes_update_buy_event(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that buy trade is stored in buy_times buffer."""
        classification = make_classification(
            side=TradeSide.BUY,
            timestamp_ns=1_000_000_000,
        )
        fixed_hawkes_indicator.update(classification)

        # After update, should have one buy event (stored as relative seconds)
        assert fixed_hawkes_indicator._buy_times is not None
        assert len(fixed_hawkes_indicator._buy_times) == 1
        # First event should be at t=0 (relative time)
        assert fixed_hawkes_indicator._buy_times[0] == pytest.approx(0.0, abs=1e-6)

    def test_hawkes_update_sell_event(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that sell trade is stored in sell_times buffer."""
        classification = make_classification(
            side=TradeSide.SELL,
            timestamp_ns=1_000_000_000,
        )
        fixed_hawkes_indicator.update(classification)

        assert fixed_hawkes_indicator._sell_times is not None
        assert len(fixed_hawkes_indicator._sell_times) == 1
        # First event should be at t=0 (relative time)
        assert fixed_hawkes_indicator._sell_times[0] == pytest.approx(0.0, abs=1e-6)

    def test_hawkes_update_unknown_event(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that unknown trade side is ignored."""
        classification = make_classification(
            side=TradeSide.UNKNOWN,
            timestamp_ns=1_000_000_000,
        )
        fixed_hawkes_indicator.update(classification)

        # Unknown side should not be stored
        assert len(fixed_hawkes_indicator._buy_times) == 0
        assert len(fixed_hawkes_indicator._sell_times) == 0

    def test_hawkes_update_multiple_events(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test multiple events are stored correctly."""
        for i in range(5):
            buy_classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 1_000_000_000,
            )
            fixed_hawkes_indicator.update(buy_classification)

        for i in range(3):
            sell_classification = make_classification(
                side=TradeSide.SELL,
                timestamp_ns=(i + 5) * 1_000_000_000,
            )
            fixed_hawkes_indicator.update(sell_classification)

        assert len(fixed_hawkes_indicator._buy_times) == 5
        assert len(fixed_hawkes_indicator._sell_times) == 3


class TestHawkesBufferSize:
    """Tests for buffer size limits (T024)."""

    def test_hawkes_buffer_respects_lookback_ticks(self, small_buffer_config: HawkesConfig) -> None:
        """Test that buffer respects lookback_ticks limit."""
        indicator = HawkesOFI(config=small_buffer_config)

        # Add more events than lookback_ticks (100)
        for i in range(150):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 1_000_000_000,
            )
            indicator.update(classification)

        # Buffer should be capped at lookback_ticks
        assert len(indicator._buy_times) <= small_buffer_config.lookback_ticks

    def test_hawkes_buffer_oldest_removed_first(self, small_buffer_config: HawkesConfig) -> None:
        """Test that oldest events are removed first (FIFO)."""
        indicator = HawkesOFI(config=small_buffer_config)

        # Add exactly lookback_ticks + 1 events
        for i in range(101):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 1_000_000_000,
            )
            indicator.update(classification)

        # First event (t=0) should have been removed
        # The oldest remaining event should be at t=1 second
        assert indicator._buy_times[0] > 0.0


class TestHawkesRefit:
    """Tests for HawkesOFI.refit() and auto-refit behavior (T024)."""

    def test_hawkes_refit_trigger(self, default_config: HawkesConfig) -> None:
        """Test that refit is triggered after refit_interval events."""
        indicator = HawkesOFI(config=default_config)

        # Add events up to refit_interval (100)
        for i in range(default_config.refit_interval):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 1_000_000_000,
            )
            indicator.update(classification)

        # Should be fitted after refit_interval events
        assert indicator.is_fitted is True

    def test_hawkes_fixed_params_still_refits(self, fixed_params_config: HawkesConfig) -> None:
        """Test that use_fixed_params=True still refits (using fixed values)."""
        indicator = HawkesOFI(config=fixed_params_config)

        # Add enough events to trigger refit
        for i in range(fixed_params_config.refit_interval + 10):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 1_000_000_000,
            )
            indicator.update(classification)

        # Should be fitted
        assert indicator.is_fitted is True


class TestHawkesIntensity:
    """Tests for intensity calculation (T024)."""

    def test_hawkes_intensity_after_events(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that intensity > 0 for recent events after update."""
        # Add some recent events
        for i in range(10):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 1_000_000,  # 1ms apart
            )
            fixed_hawkes_indicator.update(classification)

        # With fixed params and recent events, intensity should be positive
        assert fixed_hawkes_indicator.buy_intensity > 0.0


class TestHawkesResult:
    """Tests for HawkesOFI.get_result() method (T024)."""

    def test_hawkes_get_result_structure(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that get_result returns proper HawkesResult structure."""
        result = fixed_hawkes_indicator.get_result()

        # Check all required attributes exist
        assert hasattr(result, "ofi")
        assert hasattr(result, "buy_intensity")
        assert hasattr(result, "sell_intensity")
        assert hasattr(result, "branching_ratio")
        assert hasattr(result, "is_fitted")

    def test_hawkes_get_result_values(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that get_result returns consistent values."""
        # Add some events
        for i in range(5):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 1_000_000_000,
            )
            fixed_hawkes_indicator.update(classification)

        result = fixed_hawkes_indicator.get_result()

        # Values should match properties
        assert result.ofi == pytest.approx(fixed_hawkes_indicator.ofi, rel=0.01)
        assert result.buy_intensity == pytest.approx(fixed_hawkes_indicator.buy_intensity, rel=0.01)
        assert result.sell_intensity == pytest.approx(
            fixed_hawkes_indicator.sell_intensity, rel=0.01
        )


# ==============================================================================
# T025: Edge Case Tests
# ==============================================================================


class TestHawkesSparseEvents:
    """Tests for sparse event handling (T025)."""

    def test_hawkes_sparse_events_ofi(self, hawkes_indicator: HawkesOFI) -> None:
        """Test that very few events are handled gracefully with OFI = 0."""
        # Add just 2 events (not enough to fit)
        classification = make_classification(
            side=TradeSide.BUY,
            timestamp_ns=0,
        )
        hawkes_indicator.update(classification)
        classification = make_classification(
            side=TradeSide.SELL,
            timestamp_ns=1_000_000_000,
        )
        hawkes_indicator.update(classification)

        # With sparse events, should handle gracefully
        assert hawkes_indicator.ofi == pytest.approx(0.0, abs=0.1)
        assert hawkes_indicator.is_fitted is False

    def test_hawkes_sparse_events_no_crash(self, hawkes_indicator: HawkesOFI) -> None:
        """Test that sparse events don't cause crashes."""
        # Just one event
        classification = make_classification(
            side=TradeSide.BUY,
            timestamp_ns=0,
        )
        hawkes_indicator.update(classification)

        # Should not raise any exceptions
        _ = hawkes_indicator.ofi
        _ = hawkes_indicator.buy_intensity
        _ = hawkes_indicator.sell_intensity
        _ = hawkes_indicator.get_result()


class TestHawkesReset:
    """Tests for reset functionality (T025)."""

    def test_hawkes_empty_after_reset(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that reset() returns indicator to initial state."""
        # Add some events
        for i in range(50):
            classification = make_classification(
                side=TradeSide.BUY if i % 2 == 0 else TradeSide.SELL,
                timestamp_ns=i * 1_000_000_000,
            )
            fixed_hawkes_indicator.update(classification)

        # Verify we have data
        assert len(fixed_hawkes_indicator._buy_times) > 0
        assert len(fixed_hawkes_indicator._sell_times) > 0

        # Reset
        fixed_hawkes_indicator.reset()

        # Should be back to initial state
        assert fixed_hawkes_indicator.ofi == pytest.approx(0.0, abs=1e-10)
        assert fixed_hawkes_indicator.is_fitted is False
        assert len(fixed_hawkes_indicator._buy_times) == 0
        assert len(fixed_hawkes_indicator._sell_times) == 0

    def test_hawkes_usable_after_reset(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that indicator is usable after reset."""
        # Add data, reset, add more data
        for i in range(10):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 1_000_000_000,
            )
            fixed_hawkes_indicator.update(classification)

        fixed_hawkes_indicator.reset()

        # Should be able to add new data
        for i in range(10):
            classification = make_classification(
                side=TradeSide.SELL,
                timestamp_ns=i * 1_000_000_000,
            )
            fixed_hawkes_indicator.update(classification)

        # Should now have only sell events
        assert len(fixed_hawkes_indicator._buy_times) == 0
        assert len(fixed_hawkes_indicator._sell_times) == 10


class TestHawkesOFIBounds:
    """Tests for OFI value bounds (T025)."""

    def test_hawkes_ofi_bounded_minus_one_to_one(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that OFI is always in [-1.0, 1.0] range."""
        # Add various events
        for i in range(100):
            classification = make_classification(
                side=TradeSide.BUY if i % 2 == 0 else TradeSide.SELL,
                timestamp_ns=i * 1_000_000_000,
            )
            fixed_hawkes_indicator.update(classification)

        assert -1.0 <= fixed_hawkes_indicator.ofi <= 1.0

    def test_hawkes_ofi_extreme_buy_imbalance(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test OFI with extreme buy imbalance."""
        # Add only buy events
        for i in range(100):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 1_000_000_000,
            )
            fixed_hawkes_indicator.update(classification)

        # Trigger refit to get fitted state
        fixed_hawkes_indicator.refit()

        # Should approach 1.0 (all buys)
        assert fixed_hawkes_indicator.ofi > 0.5

    def test_hawkes_ofi_extreme_sell_imbalance(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test OFI with extreme sell imbalance."""
        # Add only sell events
        for i in range(100):
            classification = make_classification(
                side=TradeSide.SELL,
                timestamp_ns=i * 1_000_000_000,
            )
            fixed_hawkes_indicator.update(classification)

        # Trigger refit to get fitted state
        fixed_hawkes_indicator.refit()

        # Should approach -1.0 (all sells)
        assert fixed_hawkes_indicator.ofi < -0.5


class TestHawkesBranchingRatio:
    """Tests for branching ratio calculation (T025)."""

    def test_hawkes_branching_ratio_less_than_one(self, fixed_hawkes_indicator: HawkesOFI) -> None:
        """Test that branching ratio < 1 for stationarity."""
        # With fixed params: alpha=0.5, beta=1.0 -> eta = 0.5
        result = fixed_hawkes_indicator.get_result()
        assert result.branching_ratio < 1.0

    def test_hawkes_branching_ratio_matches_config(self, fixed_params_config: HawkesConfig) -> None:
        """Test that branching ratio matches alpha/beta from config."""
        indicator = HawkesOFI(config=fixed_params_config)

        expected_eta = fixed_params_config.fixed_excitation / fixed_params_config.decay_rate

        result = indicator.get_result()
        assert result.branching_ratio == pytest.approx(expected_eta, rel=0.01)


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestHawkesIntegration:
    """Integration tests for HawkesOFI with real-world scenarios."""

    def test_hawkes_realistic_trading_scenario(self, default_config: HawkesConfig) -> None:
        """Test HawkesOFI in realistic trading scenario."""
        indicator = HawkesOFI(config=default_config)

        # Simulate a period of balanced trading
        for i in range(50):
            side = TradeSide.BUY if i % 2 == 0 else TradeSide.SELL
            classification = make_classification(
                side=side,
                volume=1.0 + (i % 5) * 0.1,
                timestamp_ns=i * 100_000_000,  # 100ms apart
            )
            indicator.update(classification)

        # OFI should be close to 0 (balanced)
        assert abs(indicator.ofi) < 0.5

        # Now simulate aggressive buying
        for i in range(50, 150):
            classification = make_classification(
                side=TradeSide.BUY,
                volume=2.0,  # Larger volume
                timestamp_ns=i * 100_000_000,
            )
            indicator.update(classification)

        # OFI should now be positive (buy-heavy)
        assert indicator.ofi > 0.0

    def test_hawkes_momentum_detection(self, default_config: HawkesConfig) -> None:
        """Test that Hawkes detects momentum (clustered events)."""
        indicator = HawkesOFI(config=default_config)

        # First period: Sparse events
        for i in range(20):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 10_000_000_000,  # 10 seconds apart
            )
            indicator.update(classification)

        intensity_sparse = indicator.buy_intensity

        # Second period: Clustered events (same total count, shorter time)
        indicator.reset()
        for i in range(20):
            classification = make_classification(
                side=TradeSide.BUY,
                timestamp_ns=i * 100_000_000,  # 100ms apart (100x faster)
            )
            indicator.update(classification)

        intensity_clustered = indicator.buy_intensity

        # Clustered events should show higher intensity
        assert intensity_clustered > intensity_sparse


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
