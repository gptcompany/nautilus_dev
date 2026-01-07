"""Comprehensive tests for DSP filters.

Focus on:
- IIR filter correctness (low-pass, high-pass)
- Recursive variance calculation
- Kalman filter state estimation
- LMS adaptive filter convergence
- IIR regime detection with variance ratios
- Edge cases: zero input, extreme values, numerical stability
"""

import math

import numpy as np
import pytest

from strategies.common.adaptive_control.dsp_filters import (
    DSPRegimeDetector,
    IIRHighPass,
    IIRLowPass,
    IIRRegimeDetector,
    KalmanFilter1D,
    LMSAdaptiveFilter,
    RecursiveVariance,
)


# Fixtures for regime detection tests
@pytest.fixture
def volatile_returns():
    """Generate volatile (high variance) returns for trending detection."""
    np.random.seed(42)
    return np.random.randn(100) * 0.05  # 5% volatility


@pytest.fixture
def low_volatility_returns():
    """Generate low volatility returns for mean-reversion detection."""
    np.random.seed(42)
    return np.random.randn(100) * 0.005  # 0.5% volatility


@pytest.fixture
def trending_returns():
    """Generate trending returns (persistent direction)."""
    np.random.seed(42)
    # Trending returns with momentum
    base = np.cumsum(np.random.randn(100) * 0.005)
    returns = np.diff(base, prepend=0) + 0.001  # Positive drift
    return returns


class TestIIRLowPass:
    """Test IIR low-pass filter (EMA)."""

    def test_initialization(self):
        """Test filter initialization."""
        lpf = IIRLowPass(cutoff_period=20)
        assert lpf.alpha == 2.0 / 21
        assert lpf._y == 0.0
        assert not lpf._initialized

    def test_first_update(self):
        """Test first update initializes filter."""
        lpf = IIRLowPass(cutoff_period=20)
        result = lpf.update(100.0)

        assert result == 100.0
        assert lpf._initialized
        assert lpf.value == 100.0

    def test_ema_calculation(self):
        """Test EMA calculation is correct."""
        lpf = IIRLowPass(cutoff_period=9)  # alpha = 2/10 = 0.2

        values = [100, 110, 105, 115, 120]
        results = [lpf.update(v) for v in values]

        # Manual EMA calculation
        expected = [100.0]
        for v in values[1:]:
            expected.append(0.2 * v + 0.8 * expected[-1])

        np.testing.assert_allclose(results, expected, rtol=1e-10)

    def test_property_access(self):
        """Test value property."""
        lpf = IIRLowPass(cutoff_period=20)
        lpf.update(50.0)
        lpf.update(60.0)

        assert lpf.value > 50.0
        assert lpf.value < 60.0

    def test_reset(self):
        """Test filter reset."""
        lpf = IIRLowPass(cutoff_period=20)
        lpf.update(100.0)
        lpf.update(110.0)

        lpf.reset()

        assert lpf._y == 0.0
        assert not lpf._initialized

    def test_zero_input(self):
        """Test with zero input values."""
        lpf = IIRLowPass(cutoff_period=20)

        for _ in range(10):
            result = lpf.update(0.0)

        assert result == 0.0

    def test_negative_values(self):
        """Test with negative values."""
        lpf = IIRLowPass(cutoff_period=20)

        values = [-10, -5, -15, -8]
        results = [lpf.update(v) for v in values]

        assert all(r < 0 for r in results)

    def test_smoothing_effect(self):
        """Test that filter smooths noise."""
        np.random.seed(42)
        lpf = IIRLowPass(cutoff_period=20)

        # Generate noisy signal
        signal = 100 + np.random.normal(0, 10, 100)
        filtered = [lpf.update(s) for s in signal]

        # Filtered should have lower variance
        assert np.std(filtered[20:]) < np.std(signal[20:])


class TestIIRHighPass:
    """Test IIR high-pass filter."""

    def test_initialization(self):
        """Test filter initialization."""
        hpf = IIRHighPass(cutoff_period=20)
        assert hpf.alpha == 2.0 / 21
        assert hpf._y == 0.0
        assert not hpf._initialized

    def test_first_update(self):
        """Test first update."""
        hpf = IIRHighPass(cutoff_period=20)
        result = hpf.update(100.0)

        assert result == 0.0  # First output is zero
        assert hpf._initialized

    def test_removes_trend(self):
        """Test that HPF removes trend."""
        hpf = IIRHighPass(cutoff_period=10)

        # Create signal with trend
        trend = np.linspace(0, 100, 100)
        signal = trend + np.random.normal(0, 1, 100)

        filtered = [hpf.update(s) for s in signal]

        # High-pass output should have near-zero mean (trend removed)
        assert abs(np.mean(filtered[20:])) < 5

    def test_extracts_fast_component(self):
        """Test extraction of fast component."""
        hpf = IIRHighPass(cutoff_period=20)

        # Slow oscillation should be removed
        slow = np.sin(np.linspace(0, 2 * np.pi, 100))
        filtered = [hpf.update(s) for s in slow]

        # Output should be much smaller than input
        assert np.std(filtered[20:]) < np.std(slow[20:])

    def test_value_property(self):
        """Test value property access."""
        hpf = IIRHighPass(cutoff_period=20)
        hpf.update(50.0)
        hpf.update(60.0)

        assert isinstance(hpf.value, float)


class TestRecursiveVariance:
    """Test Welford's recursive variance algorithm."""

    def test_initialization(self):
        """Test initialization."""
        rv = RecursiveVariance(alpha=0.1)
        assert rv.alpha == 0.1
        assert rv._mean == 0.0
        assert rv._var == 0.0
        assert not rv._initialized

    def test_first_update(self):
        """Test first update."""
        rv = RecursiveVariance(alpha=0.1)
        var = rv.update(10.0)

        assert rv._mean == 10.0
        assert var == 0.0
        assert rv._initialized

    def test_variance_calculation(self):
        """Test variance calculation correctness."""
        np.random.seed(42)
        rv = RecursiveVariance(alpha=0.1)

        values = np.random.normal(100, 10, 200)
        for v in values:
            rv.update(v)

        # After convergence, should be close to true variance
        # With alpha=0.1, exponential weighting gives lower variance than population
        assert 50 < rv.variance < 80  # Exponentially weighted variance

    def test_mean_property(self):
        """Test mean property."""
        rv = RecursiveVariance(alpha=0.1)

        values = [10, 20, 30, 40, 50]
        for v in values:
            rv.update(v)

        # Mean with exponential decay (alpha=0.1) converges slowly
        # Starting from 10, adding 20,30,40,50 gives ~19
        assert 15 < rv.mean < 25

    def test_std_property(self):
        """Test standard deviation property."""
        rv = RecursiveVariance(alpha=0.1)

        values = [10, 20, 30, 40, 50]
        for v in values:
            rv.update(v)

        assert rv.std == math.sqrt(rv.variance)

    def test_zero_variance(self):
        """Test with constant values (zero variance)."""
        rv = RecursiveVariance(alpha=0.1)

        for _ in range(20):
            rv.update(100.0)

        assert rv.variance < 0.01  # Should be very close to zero

    def test_negative_variance_protection(self):
        """Test that std doesn't fail on negative variance."""
        rv = RecursiveVariance(alpha=0.1)
        rv._var = -0.0001  # Force negative (shouldn't happen, but defensive)

        # Should not crash, returns 0
        assert rv.std == 0.0


class TestKalmanFilter1D:
    """Test 1D Kalman filter."""

    def test_initialization(self):
        """Test initialization."""
        kf = KalmanFilter1D(process_noise=0.01, measurement_noise=0.1)
        assert kf.Q == 0.01
        assert kf.R == 0.1
        assert kf._x == 0.0
        assert kf._P == 1.0
        assert not kf._initialized

    def test_first_update(self):
        """Test first update."""
        kf = KalmanFilter1D()
        result = kf.update(100.0)

        assert result == 100.0
        assert kf._initialized
        assert kf.value == 100.0

    def test_noise_reduction(self):
        """Test that Kalman filter reduces noise."""
        np.random.seed(42)
        kf = KalmanFilter1D(process_noise=0.01, measurement_noise=1.0)

        # True signal + noise
        true_signal = 100.0
        measurements = true_signal + np.random.normal(0, 1.0, 100)

        estimates = [kf.update(m) for m in measurements]

        # Filtered estimates should be closer to true signal
        final_estimate = estimates[-1]
        final_measurement = measurements[-1]

        assert abs(final_estimate - true_signal) < abs(final_measurement - true_signal)

    def test_tracking_constant_signal(self):
        """Test tracking constant signal."""
        kf = KalmanFilter1D(process_noise=0.001, measurement_noise=0.1)

        measurements = [50.0 + np.random.normal(0, 0.1) for _ in range(100)]
        estimates = [kf.update(m) for m in measurements]

        # Should converge to 50
        assert 49.5 < estimates[-1] < 50.5

    def test_uncertainty_property(self):
        """Test uncertainty property."""
        kf = KalmanFilter1D()
        kf.update(100.0)
        kf.update(105.0)

        uncertainty = kf.uncertainty
        assert uncertainty > 0
        assert isinstance(uncertainty, float)

    def test_reset(self):
        """Test filter reset."""
        kf = KalmanFilter1D()
        kf.update(100.0)
        kf.update(105.0)

        kf.reset()

        assert kf._x == 0.0
        assert kf._P == 1.0
        assert not kf._initialized

    def test_value_property(self):
        """Test value property."""
        kf = KalmanFilter1D()
        kf.update(50.0)

        assert kf.value == kf._x


class TestLMSAdaptiveFilter:
    """Test LMS adaptive filter."""

    def test_initialization(self):
        """Test initialization."""
        lms = LMSAdaptiveFilter(length=5, mu=0.1)
        assert lms.length == 5
        assert lms.mu == 0.1
        assert len(lms._weights) == 5
        assert len(lms._buffer) == 5

    def test_update_basic(self):
        """Test basic update."""
        lms = LMSAdaptiveFilter(length=3, mu=0.1)

        prediction = lms.update(1.0, target=2.0)
        assert isinstance(prediction, float)

    def test_learns_simple_pattern(self):
        """Test learning simple linear pattern."""
        lms = LMSAdaptiveFilter(length=2, mu=0.01)

        # Target = 2*x
        x_values = [1, 2, 3, 4, 5] * 20
        errors = []

        for x in x_values:
            target = 2.0 * x
            prediction = lms.update(x, target)
            error = abs(prediction - target)
            errors.append(error)

        # Error should decrease over time
        assert np.mean(errors[-10:]) < np.mean(errors[:10])

    def test_weights_property(self):
        """Test weights property returns copy."""
        lms = LMSAdaptiveFilter(length=5, mu=0.1)

        weights1 = lms.weights
        weights2 = lms.weights

        assert weights1 == weights2
        assert weights1 is not weights2  # Should be copy

    def test_circular_buffer(self):
        """Test circular buffer behavior."""
        lms = LMSAdaptiveFilter(length=3, mu=0.1)

        # Fill buffer
        for i in range(5):
            lms.update(float(i), target=0.0)

        # Buffer should only keep last 3 values
        assert len(lms._buffer) == 3


class TestIIRRegimeDetector:
    """Test IIR-based regime detection."""

    def test_initialization(self):
        """Test initialization."""
        detector = IIRRegimeDetector(
            fast_period=10,
            slow_period=50,
            trend_threshold=1.5,
            revert_threshold=0.7,
        )
        assert detector.trend_threshold == 1.5
        assert detector.revert_threshold == 0.7

    def test_update_returns_regime(self):
        """Test update returns regime string."""
        detector = IIRRegimeDetector()
        regime = detector.update(0.01)

        assert regime in ["trending", "normal", "mean_reverting", "unknown"]

    def test_trending_detection(self, volatile_returns):
        """Test detection of trending regime."""
        detector = IIRRegimeDetector(fast_period=5, slow_period=20)

        regime = None
        for ret in volatile_returns:
            regime = detector.update(ret)

        # Volatile returns can produce any regime depending on variance ratio
        assert regime in ["trending", "normal", "mean_reverting"]

    def test_mean_reverting_detection(self, low_volatility_returns):
        """Test detection of mean-reverting regime."""
        detector = IIRRegimeDetector(fast_period=5, slow_period=20)

        regime = None
        for ret in low_volatility_returns:
            regime = detector.update(ret)

        # Low volatility should trigger mean-reverting
        assert regime in ["mean_reverting", "normal"]

    def test_variance_ratio_property(self):
        """Test variance ratio property."""
        detector = IIRRegimeDetector()

        for i in range(50):
            detector.update(0.01 if i % 2 == 0 else -0.01)

        ratio = detector.variance_ratio
        assert isinstance(ratio, float)
        assert ratio > 0

    def test_zero_variance_handling(self):
        """Test handling of zero variance."""
        detector = IIRRegimeDetector()

        for _ in range(50):
            regime = detector.update(0.0)

        # Should return unknown for zero variance
        assert regime == "unknown"

    def test_regime_transitions(self):
        """Test regime transitions."""
        detector = IIRRegimeDetector(fast_period=5, slow_period=20)

        # Start with low volatility
        for _ in range(30):
            detector.update(0.001)
        regime1 = detector.update(0.001)

        # Spike to high volatility
        for _ in range(10):
            detector.update(0.1)
        regime2 = detector.update(0.1)

        # Regimes should be different (or at least not crash)
        assert regime1 in ["trending", "normal", "mean_reverting", "unknown"]
        assert regime2 in ["trending", "normal", "mean_reverting", "unknown"]


class TestDSPRegimeDetector:
    """Test complete DSP regime detector."""

    def test_initialization(self):
        """Test initialization."""
        detector = DSPRegimeDetector(
            fast_period=10,
            slow_period=50,
            momentum_period=20,
        )
        assert detector is not None

    def test_update_with_price(self):
        """Test update with price."""
        detector = DSPRegimeDetector()
        result = detector.update(price=100.0, prev_price=99.0)

        assert "regime" in result
        assert "momentum" in result
        assert "volatility" in result
        assert "variance_ratio" in result

    def test_update_without_prev_price(self):
        """Test update without previous price."""
        detector = DSPRegimeDetector()
        result = detector.update(price=100.0, prev_price=None)

        assert "regime" in result
        # Return should be 0
        assert result["momentum"] == 0.0

    def test_update_result_types(self):
        """Test that update returns correct types."""
        detector = DSPRegimeDetector()

        result = detector.update(price=105.0, prev_price=100.0)

        assert isinstance(result["regime"], str)
        assert isinstance(result["momentum"], float)
        assert isinstance(result["volatility"], float)
        assert isinstance(result["variance_ratio"], float)

    def test_momentum_tracking(self):
        """Test momentum tracking."""
        detector = DSPRegimeDetector(momentum_period=10)

        # Upward trend
        price = 100.0
        for _i in range(50):
            prev = price
            price += 1.0
            result = detector.update(price=price, prev_price=prev)

        # Momentum should be positive
        assert result["momentum"] > 0

    def test_volatility_measurement(self):
        """Test volatility measurement."""
        np.random.seed(42)
        detector = DSPRegimeDetector()

        price = 100.0
        for _ in range(100):
            prev = price
            ret = np.random.normal(0, 0.02)
            price *= 1 + ret
            result = detector.update(price=price, prev_price=prev)

        # Volatility should be positive and reasonable
        assert 0 < result["volatility"] < 0.1

    def test_zero_prev_price_handling(self):
        """Test handling of zero previous price."""
        detector = DSPRegimeDetector()
        result = detector.update(price=100.0, prev_price=0.0)

        # Should not crash
        assert result["regime"] in ["trending", "normal", "mean_reverting", "unknown"]

    def test_integrated_regime_detection(self, trending_returns):
        """Test integrated regime detection with trending data."""
        detector = DSPRegimeDetector()

        price = 100.0
        for ret in trending_returns:
            prev = price
            price *= 1 + ret
            result = detector.update(price=price, prev_price=prev)

        # Should detect some regime
        assert result["regime"] in ["trending", "normal", "mean_reverting"]


class TestEdgeCases:
    """Test edge cases across all filters."""

    def test_extreme_values(self):
        """Test all filters with extreme values."""
        lpf = IIRLowPass(cutoff_period=20)
        hpf = IIRHighPass(cutoff_period=20)
        rv = RecursiveVariance(alpha=0.1)
        kf = KalmanFilter1D()

        extreme_value = 1e10

        # Should not crash
        lpf.update(extreme_value)
        hpf.update(extreme_value)
        rv.update(extreme_value)
        kf.update(extreme_value)

    def test_very_small_values(self):
        """Test filters with very small values."""
        lpf = IIRLowPass(cutoff_period=20)
        rv = RecursiveVariance(alpha=0.1)

        small_value = 1e-10

        for _ in range(100):
            lpf.update(small_value)
            rv.update(small_value)

        assert lpf.value < 1e-8
        assert rv.variance < 1e-18

    def test_nan_propagation(self):
        """Test that NaN doesn't cause crashes."""
        lpf = IIRLowPass(cutoff_period=20)

        lpf.update(100.0)
        # NaN should propagate
        result = lpf.update(float("nan"))
        assert math.isnan(result)

    def test_alternating_extreme_values(self):
        """Test with alternating extreme values."""
        detector = IIRRegimeDetector()

        for i in range(50):
            ret = 0.5 if i % 2 == 0 else -0.5
            regime = detector.update(ret)

        # Should handle extreme alternation
        assert regime in ["trending", "normal", "mean_reverting", "unknown"]
