"""TDD Tests for OrderflowManager Integration (Spec 025 - Phase 5).

Tests for OrderflowManager unified interface and GillerSizer integration.

Test IDs:
- T034: OrderflowManager integration tests
- T035: GillerSizer integration tests
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from strategies.common.orderflow.config import (
    HawkesConfig,
    OrderflowConfig,
    VPINConfig,
)
from strategies.common.orderflow.vpin import ToxicityLevel


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def default_config() -> OrderflowConfig:
    """Default OrderflowConfig for testing."""
    return OrderflowConfig(
        vpin=VPINConfig(
            bucket_size=100.0,
            n_buckets=10,
            classification_method="tick_rule",
            min_bucket_volume=10.0,
        ),
        hawkes=HawkesConfig(
            decay_rate=1.0,
            lookback_ticks=1000,
            refit_interval=10,
            use_fixed_params=True,
            fixed_baseline=0.1,
            fixed_excitation=0.5,
        ),
        enable_vpin=True,
        enable_hawkes=True,
    )


@pytest.fixture
def vpin_only_config() -> OrderflowConfig:
    """Config with only VPIN enabled."""
    return OrderflowConfig(
        vpin=VPINConfig(
            bucket_size=100.0,
            n_buckets=10,
        ),
        enable_vpin=True,
        enable_hawkes=False,
    )


@pytest.fixture
def hawkes_only_config() -> OrderflowConfig:
    """Config with only Hawkes enabled."""
    return OrderflowConfig(
        hawkes=HawkesConfig(
            decay_rate=1.0,
            lookback_ticks=1000,
            refit_interval=10,
            use_fixed_params=True,
            fixed_baseline=0.1,
            fixed_excitation=0.5,
        ),
        enable_vpin=False,
        enable_hawkes=True,
    )


@pytest.fixture
def mock_bar() -> MagicMock:
    """Create a mock NautilusTrader Bar object."""
    bar = MagicMock()
    bar.open = 100.0
    bar.high = 101.0
    bar.low = 99.0
    bar.close = 100.5
    bar.volume = 100.0
    bar.ts_event = 1_000_000_000
    return bar


def make_mock_bar(
    open_: float = 100.0,
    high: float = 101.0,
    low: float = 99.0,
    close: float = 100.5,
    volume: float = 100.0,
    ts_event: int = 1_000_000_000,
) -> MagicMock:
    """Helper to create mock Bar objects."""
    bar = MagicMock()
    bar.open = open_
    bar.high = high
    bar.low = low
    bar.close = close
    bar.volume = volume
    bar.ts_event = ts_event
    return bar


# ==============================================================================
# T034: OrderflowManager Integration Tests
# ==============================================================================


class TestOrderflowManagerInit:
    """Tests for OrderflowManager initialization (T034)."""

    def test_init_with_default_config(self, default_config: OrderflowConfig) -> None:
        """T034.1: OrderflowManager should initialize with default config."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        assert manager is not None
        assert manager._config == default_config

    def test_init_creates_vpin_when_enabled(self, default_config: OrderflowConfig) -> None:
        """T034.2: OrderflowManager should create VPIN indicator when enabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        assert manager._vpin is not None

    def test_init_creates_hawkes_when_enabled(self, default_config: OrderflowConfig) -> None:
        """T034.3: OrderflowManager should create Hawkes indicator when enabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        assert manager._hawkes is not None

    def test_init_skips_vpin_when_disabled(self, hawkes_only_config: OrderflowConfig) -> None:
        """T034.4: OrderflowManager should not create VPIN when disabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=hawkes_only_config)

        assert manager._vpin is None

    def test_init_skips_hawkes_when_disabled(self, vpin_only_config: OrderflowConfig) -> None:
        """T034.5: OrderflowManager should not create Hawkes when disabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=vpin_only_config)

        assert manager._hawkes is None


class TestOrderflowManagerHandleBar:
    """Tests for OrderflowManager.handle_bar() method (T034)."""

    def test_handle_bar_updates_vpin(self, default_config: OrderflowConfig) -> None:
        """T034.6: handle_bar should update VPIN indicator."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        # Process multiple bars with varying prices (tick rule needs price changes)
        # First bar establishes baseline, second bar can be classified
        for i in range(2):
            bar = make_mock_bar(
                close=100.0 + i,  # Price must change for tick rule
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # VPIN should have received the update (at least current bucket should exist)
        assert manager._vpin._current_bucket is not None or len(manager._vpin._buckets) > 0

    def test_handle_bar_updates_hawkes(self, default_config: OrderflowConfig) -> None:
        """T034.7: handle_bar should update Hawkes indicator."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        # Process multiple bars with varying prices (tick rule needs price changes)
        for i in range(2):
            bar = make_mock_bar(
                close=100.0 + i,  # Price must change
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # Hawkes should have received the update (check internal state)
        assert len(manager._hawkes._buy_times) > 0 or len(manager._hawkes._sell_times) > 0

    def test_handle_bar_updates_both_indicators(self, default_config: OrderflowConfig) -> None:
        """T034.8: handle_bar should update both VPIN and Hawkes."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        # Process multiple bars to fill buckets and trigger refit
        for i in range(20):
            bar = make_mock_bar(
                close=100.0 + (i % 5),  # Varying prices
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # Both should have been updated
        assert len(manager._vpin._buckets) > 0
        assert len(manager._hawkes._buy_times) > 0 or len(manager._hawkes._sell_times) > 0

    def test_handle_bar_only_vpin_when_hawkes_disabled(
        self, vpin_only_config: OrderflowConfig
    ) -> None:
        """T034.9: handle_bar should only update VPIN when Hawkes disabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=vpin_only_config)

        # Process multiple bars with varying prices
        for i in range(2):
            bar = make_mock_bar(
                close=100.0 + i,  # Price must change
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # VPIN should be updated
        assert manager._vpin._current_bucket is not None or len(manager._vpin._buckets) > 0
        # Hawkes should be None
        assert manager._hawkes is None

    def test_handle_bar_only_hawkes_when_vpin_disabled(
        self, hawkes_only_config: OrderflowConfig
    ) -> None:
        """T034.10: handle_bar should only update Hawkes when VPIN disabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=hawkes_only_config)

        # Process multiple bars with varying prices
        for i in range(2):
            bar = make_mock_bar(
                close=100.0 + i,  # Price must change
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # Hawkes should be updated
        assert len(manager._hawkes._buy_times) > 0 or len(manager._hawkes._sell_times) > 0
        # VPIN should be None
        assert manager._vpin is None


class TestOrderflowManagerProperties:
    """Tests for OrderflowManager property accessors (T034)."""

    def test_toxicity_returns_vpin_toxicity(self, default_config: OrderflowConfig) -> None:
        """T034.11: toxicity property should return VPINResult.toxicity."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        # Initially should return LOW (VPIN = 0.0)
        assert manager.toxicity == ToxicityLevel.LOW

    def test_toxicity_with_disabled_vpin_returns_low(
        self, hawkes_only_config: OrderflowConfig
    ) -> None:
        """T034.12: toxicity should return LOW when VPIN disabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=hawkes_only_config)

        assert manager.toxicity == ToxicityLevel.LOW

    def test_vpin_value_returns_float(self, default_config: OrderflowConfig) -> None:
        """T034.13: vpin_value should return VPIN value as float."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        assert isinstance(manager.vpin_value, float)
        assert 0.0 <= manager.vpin_value <= 1.0

    def test_ofi_returns_float(self, default_config: OrderflowConfig) -> None:
        """T034.14: ofi property should return Hawkes OFI as float."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        assert isinstance(manager.ofi, float)
        assert -1.0 <= manager.ofi <= 1.0

    def test_ofi_with_disabled_hawkes_returns_zero(self, vpin_only_config: OrderflowConfig) -> None:
        """T034.15: ofi should return 0.0 when Hawkes disabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=vpin_only_config)

        assert manager.ofi == pytest.approx(0.0, abs=1e-10)

    def test_is_valid_initially_false(self, default_config: OrderflowConfig) -> None:
        """T034.16: is_valid should be False initially."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        assert manager.is_valid is False

    def test_is_valid_true_after_sufficient_data(self, vpin_only_config: OrderflowConfig) -> None:
        """T034.17: is_valid should be True after enough data (VPIN only)."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=vpin_only_config)

        # Fill enough buckets for VPIN validity (10 buckets with 100 volume each)
        # Need varying prices for tick rule classification
        for i in range(11):  # 11 bars = 10 valid classifications (first is UNKNOWN)
            bar = make_mock_bar(
                close=100.0 + i,  # Varying prices for tick rule
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        assert manager.is_valid is True


class TestOrderflowManagerReset:
    """Tests for OrderflowManager.reset() method (T034)."""

    def test_reset_clears_vpin(self, default_config: OrderflowConfig) -> None:
        """T034.18: reset should clear VPIN state."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        # Add some data
        for i in range(10):
            bar = make_mock_bar(
                close=100.0 + i,
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # Reset
        manager.reset()

        # VPIN should be cleared
        assert manager._vpin.value == pytest.approx(0.0, abs=1e-10)
        assert len(manager._vpin._buckets) == 0

    def test_reset_clears_hawkes(self, default_config: OrderflowConfig) -> None:
        """T034.19: reset should clear Hawkes state."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        # Add some data
        for i in range(10):
            bar = make_mock_bar(
                close=100.0 + i,
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # Reset
        manager.reset()

        # Hawkes should be cleared
        assert manager._hawkes.ofi == pytest.approx(0.0, abs=1e-10)
        assert len(manager._hawkes._buy_times) == 0
        assert len(manager._hawkes._sell_times) == 0

    def test_reset_both_indicators(self, default_config: OrderflowConfig) -> None:
        """T034.20: reset should clear both VPIN and Hawkes."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        # Add data and verify state exists
        for i in range(20):
            bar = make_mock_bar(
                close=100.0 + i,
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # Reset
        manager.reset()

        # Both should be cleared
        assert manager.vpin_value == pytest.approx(0.0, abs=1e-10)
        assert manager.ofi == pytest.approx(0.0, abs=1e-10)
        assert manager.is_valid is False


class TestOrderflowManagerGetResult:
    """Tests for OrderflowManager.get_result() method (T034)."""

    def test_get_result_returns_orderflow_result(self, default_config: OrderflowConfig) -> None:
        """T034.21: get_result should return OrderflowResult dataclass."""
        from strategies.common.orderflow.orderflow_manager import (
            OrderflowManager,
            OrderflowResult,
        )

        manager = OrderflowManager(config=default_config)
        result = manager.get_result()

        assert isinstance(result, OrderflowResult)

    def test_get_result_structure(self, default_config: OrderflowConfig) -> None:
        """T034.22: OrderflowResult should have all required fields."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)
        result = manager.get_result()

        # Check all fields exist
        assert hasattr(result, "vpin_value")
        assert hasattr(result, "toxicity")
        assert hasattr(result, "ofi")
        assert hasattr(result, "is_valid")

    def test_get_result_values_match_properties(self, default_config: OrderflowConfig) -> None:
        """T034.23: OrderflowResult values should match manager properties."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        # Add some data
        for i in range(10):
            bar = make_mock_bar(
                close=100.0 + i,
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        result = manager.get_result()

        assert result.vpin_value == pytest.approx(manager.vpin_value, rel=0.01)
        assert result.toxicity == manager.toxicity
        assert result.ofi == pytest.approx(manager.ofi, rel=0.01)
        assert result.is_valid == manager.is_valid


# ==============================================================================
# T035: GillerSizer Integration Tests
# ==============================================================================


class TestOrderflowManagerGillerIntegration:
    """Tests for OrderflowManager integration with GillerSizer (T035)."""

    def test_toxicity_compatible_with_giller_sizer(self, default_config: OrderflowConfig) -> None:
        """T035.1: OrderflowManager.toxicity should work with GillerSizer."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager
        from strategies.common.position_sizing.giller_sizing import GillerSizer
        from strategies.common.position_sizing.config import GillerConfig

        manager = OrderflowManager(config=default_config)
        sizer = GillerSizer(config=GillerConfig())

        # Get toxicity as float for GillerSizer
        # VPIN toxicity is an enum, but GillerSizer needs a float
        toxicity_value = manager.vpin_value  # Use vpin_value directly

        # Should be usable in GillerSizer.calculate
        size = sizer.calculate(signal=1.0, toxicity=toxicity_value)

        assert isinstance(size, float)
        assert size > 0.0

    def test_vpin_value_as_toxicity_parameter(self, default_config: OrderflowConfig) -> None:
        """T035.2: vpin_value should be usable as GillerSizer toxicity param."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager
        from strategies.common.position_sizing.config import GillerConfig

        manager = OrderflowManager(config=default_config)
        _ = GillerConfig()  # Unused, just checking toxicity range

        # vpin_value is already [0.0, 1.0] - perfect for toxicity parameter
        toxicity = manager.vpin_value

        assert 0.0 <= toxicity <= 1.0

    def test_high_toxicity_reduces_position_size(self, default_config: OrderflowConfig) -> None:
        """T035.3: High VPIN should result in smaller position size."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager
        from strategies.common.position_sizing.giller_sizing import GillerSizer
        from strategies.common.position_sizing.config import GillerConfig

        manager = OrderflowManager(config=default_config)
        sizer = GillerSizer(config=GillerConfig())

        # Fill with imbalanced trades to create high VPIN
        for i in range(10):
            bar = make_mock_bar(
                open_=100.0,
                high=101.0,
                low=99.0,
                close=101.0,  # Always closing at high = all buys
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        high_toxicity = manager.vpin_value

        # Reset and fill with balanced trades for low VPIN
        manager.reset()
        for i in range(10):
            # Alternate buy/sell bars
            if i % 2 == 0:
                close = 101.0  # Buy bar
            else:
                close = 99.0  # Sell bar
            bar = make_mock_bar(
                open_=100.0,
                high=101.0,
                low=99.0,
                close=close,
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        low_toxicity = manager.vpin_value

        # Calculate position sizes
        size_high_toxicity = sizer.calculate(signal=1.0, toxicity=high_toxicity)
        size_low_toxicity = sizer.calculate(signal=1.0, toxicity=low_toxicity)

        # High toxicity should give smaller position size
        # (unless both are at min_size)
        assert size_high_toxicity <= size_low_toxicity

    def test_orderflow_manager_workflow_with_giller(self, default_config: OrderflowConfig) -> None:
        """T035.4: Complete workflow: OrderflowManager -> GillerSizer."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager
        from strategies.common.position_sizing.giller_sizing import GillerSizer
        from strategies.common.position_sizing.config import GillerConfig

        # Setup
        orderflow = OrderflowManager(config=default_config)
        sizer = GillerSizer(config=GillerConfig(base_size=1.0, min_size=0.01))

        # Simulate trading loop
        position_sizes = []
        for i in range(15):
            # Create bar with varying price
            bar = make_mock_bar(
                close=100.0 + (i % 3),
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )

            # Update orderflow
            orderflow.handle_bar(bar)

            # Calculate position size using VPIN as toxicity
            toxicity = orderflow.vpin_value
            signal = 0.5  # Example signal
            size = sizer.calculate(signal=signal, toxicity=toxicity)

            position_sizes.append(size)

        # Should have calculated position sizes
        assert len(position_sizes) == 15
        assert all(isinstance(s, float) for s in position_sizes)


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestOrderflowManagerIntegration:
    """Integration tests for complete OrderflowManager workflow."""

    def test_complete_workflow(self, vpin_only_config: OrderflowConfig) -> None:
        """Test complete workflow from initialization to result (VPIN only)."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=vpin_only_config)

        # Phase 1: Initial state
        assert manager.is_valid is False
        assert manager.toxicity == ToxicityLevel.LOW

        # Phase 2: Add data (11 bars for 10 valid classifications)
        for i in range(11):
            bar = make_mock_bar(
                close=100.0 + i,
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # Phase 3: Check valid state
        assert manager.is_valid is True
        result = manager.get_result()
        assert result.is_valid is True

        # Phase 4: Reset
        manager.reset()
        assert manager.is_valid is False

    def test_selective_enabling(self) -> None:
        """Test that indicators can be selectively enabled/disabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        # Test VPIN only
        vpin_config = OrderflowConfig(enable_vpin=True, enable_hawkes=False)
        vpin_manager = OrderflowManager(config=vpin_config)
        assert vpin_manager._vpin is not None
        assert vpin_manager._hawkes is None

        # Test Hawkes only
        hawkes_config = OrderflowConfig(enable_vpin=False, enable_hawkes=True)
        hawkes_manager = OrderflowManager(config=hawkes_config)
        assert hawkes_manager._vpin is None
        assert hawkes_manager._hawkes is not None

        # Test both disabled (edge case)
        none_config = OrderflowConfig(enable_vpin=False, enable_hawkes=False)
        none_manager = OrderflowManager(config=none_config)
        assert none_manager._vpin is None
        assert none_manager._hawkes is None

    def test_combined_vpin_hawkes_workflow(self, default_config: OrderflowConfig) -> None:
        """Test workflow with both VPIN and Hawkes enabled."""
        from strategies.common.orderflow.orderflow_manager import OrderflowManager

        manager = OrderflowManager(config=default_config)

        # Process enough bars to make both valid
        # VPIN needs 10 buckets, Hawkes needs refit_interval (10) events
        for i in range(15):
            bar = make_mock_bar(
                close=100.0 + i,
                volume=100.0,
                ts_event=i * 1_000_000_000,
            )
            manager.handle_bar(bar)

        # Get result with both indicator values
        result = manager.get_result()

        assert result.vpin_value >= 0.0
        assert result.toxicity in [
            ToxicityLevel.LOW,
            ToxicityLevel.MEDIUM,
            ToxicityLevel.HIGH,
        ]
        assert -1.0 <= result.ofi <= 1.0
        assert result.buy_intensity >= 0.0
        assert result.sell_intensity >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
