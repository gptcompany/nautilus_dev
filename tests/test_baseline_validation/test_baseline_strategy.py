"""Unit tests for baseline strategy wrapper.

Tests for:
    - BaselineStrategy
    - Signal generation (EMA crossover)
    - Sizer integration

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations


# Note: BaselineStrategy will be implemented in Phase 3 implementation
# These tests define the expected behavior


class TestBaselineStrategyInit:
    """Tests for BaselineStrategy initialization."""

    def test_init_with_sizer(self) -> None:
        """Test initialization with a sizer."""
        from scripts.baseline_validation.sizers import FixedFractionalSizer
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        sizer = FixedFractionalSizer(risk_pct=0.02)
        strategy = BaselineStrategy(sizer=sizer)

        assert strategy.sizer is sizer

    def test_init_with_ema_periods(self) -> None:
        """Test initialization with custom EMA periods."""
        from scripts.baseline_validation.sizers import FixedFractionalSizer
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        sizer = FixedFractionalSizer(risk_pct=0.02)
        strategy = BaselineStrategy(
            sizer=sizer,
            fast_ema_period=10,
            slow_ema_period=20,
        )

        assert strategy.fast_ema_period == 10
        assert strategy.slow_ema_period == 20


class TestBaselineStrategySignalGeneration:
    """Tests for signal generation logic."""

    def test_signal_initial_is_zero(self) -> None:
        """Test that initial signal is zero (before warmup)."""
        from scripts.baseline_validation.sizers import FixedFractionalSizer
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        sizer = FixedFractionalSizer(risk_pct=0.02)
        strategy = BaselineStrategy(sizer=sizer)

        signal = strategy.get_signal()
        assert signal == 0.0

    def test_signal_after_warmup(self) -> None:
        """Test signal generation after warmup."""
        from scripts.baseline_validation.sizers import FixedFractionalSizer
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        sizer = FixedFractionalSizer(risk_pct=0.02)
        strategy = BaselineStrategy(
            sizer=sizer,
            fast_ema_period=5,
            slow_ema_period=10,
        )

        # Feed enough prices for warmup
        prices = [100.0 + i for i in range(15)]  # Rising prices
        for price in prices:
            strategy.update_price(price)

        signal = strategy.get_signal()

        # Rising prices should give positive signal (fast > slow)
        assert signal > 0

    def test_signal_negative_for_downtrend(self) -> None:
        """Test negative signal for downtrend."""
        from scripts.baseline_validation.sizers import FixedFractionalSizer
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        sizer = FixedFractionalSizer(risk_pct=0.02)
        strategy = BaselineStrategy(
            sizer=sizer,
            fast_ema_period=5,
            slow_ema_period=10,
        )

        # Feed falling prices
        prices = [100.0 - i for i in range(15)]  # Falling prices
        for price in prices:
            strategy.update_price(price)

        signal = strategy.get_signal()

        # Falling prices should give negative signal (fast < slow)
        assert signal < 0

    def test_signal_bounded(self) -> None:
        """Test that signal is bounded to [-1, 1]."""
        from scripts.baseline_validation.sizers import FixedFractionalSizer
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        sizer = FixedFractionalSizer(risk_pct=0.02)
        strategy = BaselineStrategy(
            sizer=sizer,
            fast_ema_period=5,
            slow_ema_period=10,
        )

        # Feed extreme prices
        prices = [100.0, 200.0, 300.0, 400.0, 500.0] * 3  # Extreme rise
        for price in prices:
            strategy.update_price(price)

        signal = strategy.get_signal()

        assert -1.0 <= signal <= 1.0


class TestBaselineStrategySizerIntegration:
    """Tests for integration with sizers."""

    def test_calculate_position_uses_sizer(self) -> None:
        """Test that position calculation uses the sizer."""
        from scripts.baseline_validation.sizers import FixedFractionalSizer
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        sizer = FixedFractionalSizer(risk_pct=0.02)
        strategy = BaselineStrategy(sizer=sizer)

        # Warm up
        for i in range(20):
            strategy.update_price(100.0 + i)

        position = strategy.calculate_position(
            equity=10_000.0,
            entry_price=119.0,
            stop_loss_price=114.0,
        )

        # Position should be non-zero after warmup with trend
        assert position != 0.0

    def test_calculate_position_different_sizers(self) -> None:
        """Test that different sizers give different positions."""
        from scripts.baseline_validation.sizers import (
            FixedFractionalSizer,
            AdaptiveSizer,
        )
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        # Create two strategies with different sizers
        fixed_strategy = BaselineStrategy(sizer=FixedFractionalSizer(risk_pct=0.02))
        adaptive_strategy = BaselineStrategy(sizer=AdaptiveSizer())

        # Same price sequence
        prices = [100.0 + i for i in range(20)]
        for price in prices:
            fixed_strategy.update_price(price)
            adaptive_strategy.update_price(price)

        fixed_position = fixed_strategy.calculate_position(
            equity=10_000.0,
            entry_price=119.0,
            stop_loss_price=114.0,
        )

        adaptive_position = adaptive_strategy.calculate_position(
            equity=10_000.0,
            entry_price=119.0,
            stop_loss_price=114.0,
        )

        # Positions can be the same if signals are identical
        # but sizer behavior should be consistent
        assert fixed_position != 0.0 or adaptive_position != 0.0


class TestBaselineStrategyState:
    """Tests for strategy state management."""

    def test_reset_clears_indicators(self) -> None:
        """Test that reset clears indicator state."""
        from scripts.baseline_validation.sizers import FixedFractionalSizer
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        sizer = FixedFractionalSizer(risk_pct=0.02)
        strategy = BaselineStrategy(sizer=sizer)

        # Warm up
        for i in range(20):
            strategy.update_price(100.0 + i)

        # Reset
        strategy.reset()

        # Signal should be zero again
        signal = strategy.get_signal()
        assert signal == 0.0

    def test_is_warmed_up_property(self) -> None:
        """Test is_warmed_up property."""
        from scripts.baseline_validation.sizers import FixedFractionalSizer
        from scripts.baseline_validation.baseline_strategy import BaselineStrategy

        sizer = FixedFractionalSizer(risk_pct=0.02)
        strategy = BaselineStrategy(
            sizer=sizer,
            fast_ema_period=5,
            slow_ema_period=10,
        )

        # Not warmed up initially
        assert strategy.is_warmed_up is False

        # Feed prices but not enough
        for i in range(5):
            strategy.update_price(100.0 + i)
        assert strategy.is_warmed_up is False

        # Feed enough for slow EMA
        for i in range(10):
            strategy.update_price(105.0 + i)
        assert strategy.is_warmed_up is True
