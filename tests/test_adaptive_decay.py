"""Tests for Adaptive Decay Calculator (Spec 032).

Tests verify:
- Low volatility (variance_ratio < 0.7) -> decay = 0.99
- High volatility (variance_ratio > 1.5) -> decay = 0.95
- Normal volatility (0.7 < variance_ratio < 1.5) -> interpolated
- Edge cases: extreme high, zero, negative variance_ratio
"""

import pytest

from strategies.common.adaptive_control.adaptive_decay import (
    AdaptiveDecayCalculator,
    VolatilityContext,
)


class TestVolatilityContext:
    """Tests for VolatilityContext dataclass."""

    def test_low_volatility_normalized_zero(self) -> None:
        """Test: variance_ratio < 0.7 -> normalized_volatility = 0.0."""
        context = VolatilityContext(variance_ratio=0.5)
        assert context.normalized_volatility == 0.0

    def test_high_volatility_normalized_one(self) -> None:
        """Test: variance_ratio > 1.5 -> normalized_volatility = 1.0."""
        context = VolatilityContext(variance_ratio=2.0)
        assert context.normalized_volatility == 1.0

    def test_normal_volatility_interpolated(self) -> None:
        """Test: variance_ratio = 1.1 (midpoint) -> normalized_volatility = 0.5."""
        # Midpoint of [0.7, 1.5] is 1.1
        context = VolatilityContext(variance_ratio=1.1)
        assert context.normalized_volatility == pytest.approx(0.5, abs=0.01)

    def test_at_low_threshold(self) -> None:
        """Test: variance_ratio = 0.7 (boundary) -> normalized_volatility = 0.0."""
        context = VolatilityContext(variance_ratio=0.7)
        assert context.normalized_volatility == 0.0

    def test_at_high_threshold(self) -> None:
        """Test: variance_ratio = 1.5 (boundary) -> normalized_volatility = 1.0."""
        context = VolatilityContext(variance_ratio=1.5)
        assert context.normalized_volatility == 1.0

    def test_zero_variance_ratio(self) -> None:
        """Test: variance_ratio = 0 -> normalized_volatility = 0.0 (edge case)."""
        context = VolatilityContext(variance_ratio=0.0)
        assert context.normalized_volatility == 0.0

    def test_negative_variance_ratio(self) -> None:
        """Test: negative variance_ratio -> normalized_volatility = 0.0 (edge case)."""
        context = VolatilityContext(variance_ratio=-0.5)
        assert context.normalized_volatility == 0.0


class TestAdaptiveDecayCalculator:
    """Tests for AdaptiveDecayCalculator class."""

    @pytest.fixture
    def calculator(self) -> AdaptiveDecayCalculator:
        """Create calculator instance for tests."""
        return AdaptiveDecayCalculator()

    def test_low_volatility_high_decay(self, calculator: AdaptiveDecayCalculator) -> None:
        """Test: Low volatility (variance_ratio < 0.7) -> decay = 0.99.

        When market is stable (mean-reverting), we want slow forgetting
        to maintain stable estimates.
        """
        context = VolatilityContext(variance_ratio=0.5)
        decay = calculator.calculate(context)
        assert decay == 0.99

    def test_high_volatility_low_decay(self, calculator: AdaptiveDecayCalculator) -> None:
        """Test: High volatility (variance_ratio > 1.5) -> decay = 0.95.

        When market is volatile/trending, we want faster forgetting
        to adapt quickly to new conditions.
        """
        context = VolatilityContext(variance_ratio=2.0)
        decay = calculator.calculate(context)
        assert decay == 0.95

    def test_normal_volatility_interpolated(self, calculator: AdaptiveDecayCalculator) -> None:
        """Test: Normal volatility -> interpolated decay.

        Midpoint variance_ratio=1.1 should give midpoint decay=0.97.
        """
        context = VolatilityContext(variance_ratio=1.1)
        decay = calculator.calculate(context)
        # Midpoint: 0.99 - 0.04 * 0.5 = 0.97
        assert decay == pytest.approx(0.97, abs=0.001)

    def test_extreme_high_clamped(self, calculator: AdaptiveDecayCalculator) -> None:
        """Test: Extreme high variance_ratio -> decay clamped to 0.95.

        Even with very high variance_ratio (e.g., 10.0), decay should
        never go below 0.95 to prevent over-discounting.
        """
        context = VolatilityContext(variance_ratio=10.0)
        decay = calculator.calculate(context)
        assert decay == 0.95

    def test_zero_variance_ratio(self, calculator: AdaptiveDecayCalculator) -> None:
        """Test: Zero variance_ratio -> decay = 0.99 (edge case).

        Zero variance_ratio is treated as low volatility.
        """
        context = VolatilityContext(variance_ratio=0.0)
        decay = calculator.calculate(context)
        assert decay == 0.99

    def test_negative_variance_ratio(self, calculator: AdaptiveDecayCalculator) -> None:
        """Test: Negative variance_ratio -> decay = 0.99 (edge case).

        Negative variance_ratio (shouldn't happen in practice) is
        treated as low volatility for safety.
        """
        context = VolatilityContext(variance_ratio=-0.5)
        decay = calculator.calculate(context)
        assert decay == 0.99

    def test_calculate_from_ratio_convenience(self, calculator: AdaptiveDecayCalculator) -> None:
        """Test: calculate_from_ratio() convenience method works correctly."""
        # Low volatility
        assert calculator.calculate_from_ratio(0.5) == 0.99
        # High volatility
        assert calculator.calculate_from_ratio(2.0) == 0.95
        # Midpoint
        assert calculator.calculate_from_ratio(1.1) == pytest.approx(0.97, abs=0.001)

    def test_decay_range_boundaries(self, calculator: AdaptiveDecayCalculator) -> None:
        """Test: Decay is always within [0.95, 0.99] range.

        This verifies the formula bounds are respected regardless of input.
        """
        test_values = [-1.0, 0.0, 0.5, 0.7, 1.0, 1.1, 1.5, 2.0, 5.0, 100.0]
        for vr in test_values:
            decay = calculator.calculate_from_ratio(vr)
            assert 0.95 <= decay <= 0.99, f"Decay {decay} out of range for vr={vr}"

    def test_monotonically_decreasing(self, calculator: AdaptiveDecayCalculator) -> None:
        """Test: Higher variance_ratio -> lower decay (monotonically decreasing)."""
        ratios = [0.5, 0.7, 1.0, 1.1, 1.5, 2.0]
        decays = [calculator.calculate_from_ratio(vr) for vr in ratios]

        # Each decay should be <= the previous one
        for i in range(1, len(decays)):
            assert decays[i] <= decays[i - 1], (
                f"Not monotonic: decay[{i}]={decays[i]} > decay[{i - 1}]={decays[i - 1]}"
            )


class TestAdaptiveDecayIntegration:
    """Integration tests with IIRRegimeDetector."""

    def test_calculate_from_detector(self) -> None:
        """Test: calculate_from_detector() works with real IIRRegimeDetector."""
        from strategies.common.adaptive_control.dsp_filters import IIRRegimeDetector

        detector = IIRRegimeDetector()
        calculator = AdaptiveDecayCalculator()

        # Feed some data to the detector
        for i in range(100):
            # Simulate returns that create variance
            ret = 0.01 * (1 if i % 2 == 0 else -1)
            detector.update(ret)

        # Calculate decay from detector
        decay = calculator.calculate_from_detector(detector)

        # Should be in valid range
        assert 0.95 <= decay <= 0.99
