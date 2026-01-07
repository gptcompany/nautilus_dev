"""Comprehensive tests for AdaptiveDecayCalculator.

Focus on:
- Volatility context normalization
- Decay calculation from variance ratios
- Edge cases: zero variance, extreme variance, negative values
- Integration with IIRRegimeDetector
"""
import pytest

from strategies.common.adaptive_control.adaptive_decay import (
    AdaptiveDecayCalculator,
    VolatilityContext,
)
from strategies.common.adaptive_control.dsp_filters import IIRRegimeDetector


class TestVolatilityContext:
    """Test VolatilityContext dataclass."""

    def test_volatility_context_creation(self):
        """Test creating VolatilityContext."""
        ctx = VolatilityContext(variance_ratio=1.0)
        assert ctx.variance_ratio == 1.0

    def test_normalized_volatility_low(self):
        """Test normalized volatility for low variance ratio."""
        ctx = VolatilityContext(variance_ratio=0.5)
        # variance_ratio <= 0.7 -> 0.0
        assert ctx.normalized_volatility == 0.0

    def test_normalized_volatility_at_threshold(self):
        """Test normalized volatility at low threshold."""
        ctx = VolatilityContext(variance_ratio=0.7)
        # Exactly at threshold -> 0.0
        assert ctx.normalized_volatility == 0.0

    def test_normalized_volatility_high(self):
        """Test normalized volatility for high variance ratio."""
        ctx = VolatilityContext(variance_ratio=2.0)
        # variance_ratio >= 1.5 -> 1.0
        assert ctx.normalized_volatility == 1.0

    def test_normalized_volatility_at_high_threshold(self):
        """Test normalized volatility at high threshold."""
        ctx = VolatilityContext(variance_ratio=1.5)
        # Exactly at threshold -> 1.0
        assert ctx.normalized_volatility == 1.0

    def test_normalized_volatility_middle(self):
        """Test normalized volatility in middle range."""
        # Test midpoint: (0.7 + 1.5) / 2 = 1.1
        ctx = VolatilityContext(variance_ratio=1.1)
        # Should be 0.5
        expected = (1.1 - 0.7) / (1.5 - 0.7)
        assert abs(ctx.normalized_volatility - expected) < 1e-10

    def test_normalized_volatility_linear_interpolation(self):
        """Test linear interpolation between thresholds."""
        # Test at 0.9 (25% between 0.7 and 1.5)
        ctx = VolatilityContext(variance_ratio=0.9)
        expected = (0.9 - 0.7) / (1.5 - 0.7)
        assert abs(ctx.normalized_volatility - expected) < 1e-10

    def test_normalized_volatility_zero(self):
        """Test with zero variance ratio."""
        ctx = VolatilityContext(variance_ratio=0.0)
        assert ctx.normalized_volatility == 0.0

    def test_normalized_volatility_negative(self):
        """Test with negative variance ratio (edge case)."""
        ctx = VolatilityContext(variance_ratio=-0.5)
        # Should clamp to 0.0
        assert ctx.normalized_volatility == 0.0

    def test_normalized_volatility_extreme_high(self):
        """Test with extremely high variance ratio."""
        ctx = VolatilityContext(variance_ratio=100.0)
        # Should clamp to 1.0
        assert ctx.normalized_volatility == 1.0


class TestAdaptiveDecayCalculator:
    """Test AdaptiveDecayCalculator."""

    def test_initialization(self):
        """Test calculator initialization."""
        calc = AdaptiveDecayCalculator()
        assert calc.decay_low == 0.95
        assert calc.decay_high == 0.99

    def test_calculate_low_volatility(self):
        """Test decay calculation for low volatility."""
        calc = AdaptiveDecayCalculator()
        ctx = VolatilityContext(variance_ratio=0.5)  # Low volatility
        
        decay = calc.calculate(ctx)
        # Low volatility -> high decay (0.99)
        assert decay == 0.99

    def test_calculate_high_volatility(self):
        """Test decay calculation for high volatility."""
        calc = AdaptiveDecayCalculator()
        ctx = VolatilityContext(variance_ratio=2.0)  # High volatility
        
        decay = calc.calculate(ctx)
        # High volatility -> low decay (0.95)
        assert decay == 0.95

    def test_calculate_medium_volatility(self):
        """Test decay calculation for medium volatility."""
        calc = AdaptiveDecayCalculator()
        # Midpoint between thresholds
        ctx = VolatilityContext(variance_ratio=1.1)
        
        decay = calc.calculate(ctx)
        # Should be midpoint: 0.97
        expected = 0.99 - (0.99 - 0.95) * 0.5
        assert abs(decay - expected) < 1e-10

    def test_calculate_linear_relationship(self):
        """Test linear relationship between volatility and decay."""
        calc = AdaptiveDecayCalculator()
        
        # Test several points
        test_cases = [
            (0.7, 0.99),   # At low threshold
            (1.5, 0.95),   # At high threshold
            (1.1, 0.97),   # Midpoint
            (0.9, 0.98),   # 25% from low
            (1.3, 0.96),   # 75% from low
        ]
        
        for var_ratio, expected_decay in test_cases:
            ctx = VolatilityContext(variance_ratio=var_ratio)
            decay = calc.calculate(ctx)
            assert abs(decay - expected_decay) < 1e-10

    def test_calculate_bounds(self):
        """Test that decay is always in [decay_low, decay_high]."""
        calc = AdaptiveDecayCalculator()
        
        # Test extreme values
        test_ratios = [0.0, 0.5, 0.7, 1.0, 1.5, 2.0, 10.0, 100.0]
        
        for ratio in test_ratios:
            ctx = VolatilityContext(variance_ratio=ratio)
            decay = calc.calculate(ctx)
            assert calc.decay_low <= decay <= calc.decay_high

    def test_calculate_from_ratio_convenience(self):
        """Test calculate_from_ratio convenience method."""
        calc = AdaptiveDecayCalculator()
        
        decay1 = calc.calculate_from_ratio(1.0)
        decay2 = calc.calculate(VolatilityContext(variance_ratio=1.0))
        
        assert decay1 == decay2

    def test_calculate_from_detector(self):
        """Test calculate_from_detector method."""
        calc = AdaptiveDecayCalculator()
        detector = IIRRegimeDetector()
        
        # Feed some data to detector
        for i in range(50):
            detector.update(0.01 if i % 2 == 0 else -0.01)
        
        decay = calc.calculate_from_detector(detector)
        
        # Should be valid decay value
        assert calc.decay_low <= decay <= calc.decay_high

    def test_defensive_clamping(self):
        """Test defensive clamping in calculate method."""
        calc = AdaptiveDecayCalculator()
        
        # Create context that might produce out-of-bounds value
        ctx = VolatilityContext(variance_ratio=1000.0)
        decay = calc.calculate(ctx)
        
        # Should be clamped
        assert decay == calc.decay_low


class TestIntegrationWithIIRRegimeDetector:
    """Test integration with IIRRegimeDetector."""

    def test_low_volatility_regime(self):
        """Test with low volatility returns."""
        calc = AdaptiveDecayCalculator()
        detector = IIRRegimeDetector(fast_period=5, slow_period=20)
        
        # Feed low volatility data
        for _ in range(100):
            detector.update(0.001)
        
        decay = calc.calculate_from_detector(detector)
        
        # Low volatility -> high decay
        assert decay > 0.97

    def test_high_volatility_regime(self):
        """Test with high volatility returns."""
        calc = AdaptiveDecayCalculator()
        detector = IIRRegimeDetector(fast_period=5, slow_period=20)
        
        # Feed high volatility data
        import numpy as np
        np.random.seed(42)
        for ret in np.random.normal(0, 0.05, 100):
            detector.update(ret)
        
        decay = calc.calculate_from_detector(detector)
        
        # High volatility -> lower decay
        assert decay < 0.99

    def test_volatility_transition(self):
        """Test decay adaptation during volatility transition."""
        calc = AdaptiveDecayCalculator()
        detector = IIRRegimeDetector(fast_period=5, slow_period=20)
        
        # Start with low volatility
        for _ in range(50):
            detector.update(0.001)
        
        decay1 = calc.calculate_from_detector(detector)
        
        # Spike to high volatility
        for _ in range(20):
            detector.update(0.05)
        
        decay2 = calc.calculate_from_detector(detector)
        
        # Decay should decrease (adapt faster)
        assert decay2 < decay1


class TestEdgeCases:
    """Test edge cases."""

    def test_zero_variance_ratio(self):
        """Test with zero variance ratio."""
        calc = AdaptiveDecayCalculator()
        ctx = VolatilityContext(variance_ratio=0.0)
        
        decay = calc.calculate(ctx)
        assert decay == 0.99  # Maximum decay

    def test_negative_variance_ratio(self):
        """Test with negative variance ratio (shouldn't happen, but defensive)."""
        calc = AdaptiveDecayCalculator()
        ctx = VolatilityContext(variance_ratio=-1.0)
        
        decay = calc.calculate(ctx)
        assert decay == 0.99  # Treated as low volatility

    def test_very_small_variance_ratio(self):
        """Test with very small variance ratio."""
        calc = AdaptiveDecayCalculator()
        ctx = VolatilityContext(variance_ratio=1e-10)
        
        decay = calc.calculate(ctx)
        assert decay == 0.99

    def test_infinite_variance_ratio(self):
        """Test with very large variance ratio."""
        calc = AdaptiveDecayCalculator()
        ctx = VolatilityContext(variance_ratio=float('inf'))
        
        decay = calc.calculate(ctx)
        assert decay == 0.95  # Minimum decay

    def test_boundary_values(self):
        """Test exact boundary values."""
        calc = AdaptiveDecayCalculator()
        
        # Test exact thresholds
        decay_at_low = calc.calculate_from_ratio(0.7)
        decay_at_high = calc.calculate_from_ratio(1.5)
        
        assert decay_at_low == 0.99
        assert decay_at_high == 0.95

    def test_just_below_low_threshold(self):
        """Test just below low threshold."""
        calc = AdaptiveDecayCalculator()
        decay = calc.calculate_from_ratio(0.69999)
        
        assert decay == 0.99

    def test_just_above_high_threshold(self):
        """Test just above high threshold."""
        calc = AdaptiveDecayCalculator()
        decay = calc.calculate_from_ratio(1.50001)
        
        assert decay == 0.95

    def test_monotonic_decrease(self):
        """Test that decay decreases monotonically with variance ratio."""
        calc = AdaptiveDecayCalculator()
        
        ratios = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
        decays = [calc.calculate_from_ratio(r) for r in ratios]
        
        # Each decay should be <= previous (monotonic decrease)
        for i in range(1, len(decays)):
            assert decays[i] <= decays[i-1]

    def test_formula_consistency(self):
        """Test formula consistency across methods."""
        calc = AdaptiveDecayCalculator()
        
        variance_ratio = 1.2
        
        # Three ways to calculate
        decay1 = calc.calculate(VolatilityContext(variance_ratio=variance_ratio))
        decay2 = calc.calculate_from_ratio(variance_ratio)
        
        # Create detector and set variance ratio manually
        detector = IIRRegimeDetector()
        # Feed data to get specific ratio (approximate)
        for _ in range(50):
            detector.update(0.02)
        decay3 = calc.calculate_from_detector(detector)
        
        # First two should be identical
        assert decay1 == decay2
        # Third should be within valid range
        assert calc.decay_low <= decay3 <= calc.decay_high
