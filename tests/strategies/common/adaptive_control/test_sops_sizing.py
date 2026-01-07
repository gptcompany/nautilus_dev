"""Comprehensive tests for SOPS sizing module.

Focus on:
- Adaptive K estimation with volatility
- SOPS tanh transformation
- TapeSpeed Poisson estimation
- Giller power law scaling
- Full SOPSGillerSizer pipeline
- Edge cases: zero signals, extreme volatility, NaN handling
"""

import math

import pytest

from strategies.common.adaptive_control.sops_sizing import (
    SOPS,
    AdaptiveKEstimator,
    GillerScaler,
    SOPSGillerSizer,
    SOPSState,
    TapeSpeed,
    TapeSpeedState,
    create_sops_sizer,
)


class TestAdaptiveKEstimator:
    """Test AdaptiveKEstimator."""

    def test_initialization(self):
        """Test estimator initialization."""
        estimator = AdaptiveKEstimator(k_base=1.0, vol_alpha=0.1, lookback=20)
        assert estimator.k_base == 1.0
        assert estimator.vol_alpha == 0.1
        assert estimator.lookback == 20

    def test_initial_k(self):
        """Test initial k value before any updates."""
        estimator = AdaptiveKEstimator(k_base=2.0)
        assert estimator.k == 2.0

    def test_update_with_return(self):
        """Test updating with return values."""
        estimator = AdaptiveKEstimator()
        k = estimator.update(0.01)
        assert isinstance(k, float)
        assert 0.1 <= k <= 5.0

    def test_high_volatility_lowers_k(self):
        """Test that high volatility lowers k."""
        estimator = AdaptiveKEstimator(k_base=1.0, vol_alpha=0.2)

        # Feed low volatility first
        for _ in range(30):
            estimator.update(0.001)
        k_low_vol = estimator.k

        # Feed high volatility - need MORE samples to overcome EMA smoothing
        for _ in range(100):
            estimator.update(0.1)
        k_high_vol = estimator.k

        # High vol should lower k
        assert k_high_vol < k_low_vol

    def test_low_volatility_raises_k(self):
        """Test that low volatility raises k."""
        estimator = AdaptiveKEstimator(k_base=1.0, vol_alpha=0.2)

        # Feed high volatility first
        for _ in range(30):
            estimator.update(0.1)
        k_high_vol = estimator.k

        # Feed low volatility - need MORE samples to overcome EMA smoothing
        for _ in range(100):
            estimator.update(0.001)
        k_low_vol = estimator.k

        # Low vol should raise k
        assert k_low_vol > k_high_vol

    def test_k_bounds(self):
        """Test that k is always in [0.1, 5.0]."""
        estimator = AdaptiveKEstimator()

        # Extreme cases
        for ret in [0.0, 0.001, 0.01, 0.1, 1.0]:
            for _ in range(50):
                estimator.update(ret)
            k = estimator.k
            assert 0.1 <= k <= 5.0

    def test_volatility_property(self):
        """Test volatility property."""
        estimator = AdaptiveKEstimator()
        assert estimator.volatility == 0.0

        estimator.update(0.02)
        assert estimator.volatility > 0

    def test_baseline_adaptation(self):
        """Test that baseline adapts with lookback."""
        estimator = AdaptiveKEstimator(lookback=20)

        # Feed consistent returns
        for _ in range(30):
            estimator.update(0.01)

        # Baseline should be set
        assert estimator._vol_baseline is not None


class TestSOPS:
    """Test SOPS sigmoidal position sizing."""

    def test_initialization(self):
        """Test SOPS initialization."""
        sops = SOPS(k_base=1.0, vol_alpha=0.1, max_position=1.0)
        assert sops.max_position == 1.0

    def test_size_zero_signal(self):
        """Test size with zero signal."""
        sops = SOPS()
        size = sops.size(0.0)
        assert size == 0.0

    def test_size_bounded_output(self):
        """Test that output is bounded."""
        sops = SOPS(max_position=1.0)

        # Even with extreme signals
        signals = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 100.0]
        for sig in signals:
            size = sops.size(sig)
            assert -1.0 <= size <= 1.0

    def test_size_symmetry(self):
        """Test that long and short are symmetric."""
        sops = SOPS()

        signal = 0.5
        long_size = sops.size(signal)
        short_size = sops.size(-signal)

        assert abs(long_size + short_size) < 1e-10

    def test_size_tanh_relationship(self):
        """Test that size follows tanh(k*signal)."""
        sops = SOPS(k_base=1.0)
        # Feed data to initialize k
        for _ in range(20):
            sops.update_volatility(0.01)

        signal = 0.5
        size = sops.size(signal)
        expected = math.tanh(sops.k * signal) * sops.max_position

        assert abs(size - expected) < 1e-10

    def test_update_volatility(self):
        """Test volatility update."""
        sops = SOPS()
        k = sops.update_volatility(0.02)

        assert isinstance(k, float)
        assert sops.k == k

    def test_k_property(self):
        """Test k property accessor."""
        sops = SOPS(k_base=2.0)
        assert sops.k == 2.0

    def test_volatility_property(self):
        """Test volatility property."""
        sops = SOPS()
        assert sops.volatility == 0.0

        sops.update_volatility(0.01)
        assert sops.volatility > 0


class TestTapeSpeed:
    """Test TapeSpeed estimator."""

    def test_initialization(self):
        """Test initialization."""
        tape = TapeSpeed(alpha=0.1, baseline_lambda=1.0)
        assert tape.alpha == 0.1
        assert tape.baseline_lambda == 1.0

    def test_first_update(self):
        """Test first update."""
        tape = TapeSpeed()
        state = tape.update(timestamp=1.0)

        assert isinstance(state, TapeSpeedState)
        # First update sets timestamp, no rate yet
        assert state.regime in ["fast", "normal", "slow"]

    def test_lambda_estimation(self):
        """Test lambda estimation from events."""
        tape = TapeSpeed()

        # Simulate events every 0.1 seconds -> lambda = 10
        for i in range(50):
            tape.update(timestamp=i * 0.1)

        # Lambda should be around 10
        assert 5 < tape.lambda_rate < 15

    def test_regime_detection(self):
        """Test regime detection."""
        tape = TapeSpeed(baseline_lambda=10.0, fast_threshold=1.5, slow_threshold=0.5)

        # Fast events -> fast regime
        for i in range(30):
            tape.update(timestamp=i * 0.05)  # High frequency

        state = tape.state
        # Should be fast or normal
        assert state.regime in ["fast", "normal"]

    def test_slow_regime(self):
        """Test slow regime detection."""
        tape = TapeSpeed(baseline_lambda=10.0)

        # Slow events
        for i in range(30):
            tape.update(timestamp=i * 2.0)  # Low frequency

        state = tape.state
        # Should be slow or normal
        assert state.regime in ["slow", "normal"]

    def test_weight_calculation(self):
        """Test weight calculation (sqrt of normalized)."""
        tape = TapeSpeed()

        for i in range(50):
            tape.update(timestamp=i * 0.1)

        state = tape.state
        expected_weight = math.sqrt(state.normalized_speed)
        assert abs(state.weight - expected_weight) < 1e-10

    def test_state_property(self):
        """Test state property."""
        tape = TapeSpeed()
        tape.update(1.0)

        state = tape.state
        assert hasattr(state, "lambda_rate")
        assert hasattr(state, "normalized_speed")
        assert hasattr(state, "regime")
        assert hasattr(state, "weight")

    def test_regime_property(self):
        """Test regime property."""
        tape = TapeSpeed()
        tape.update(1.0)

        assert tape.regime in ["fast", "normal", "slow"]


class TestGillerScaler:
    """Test Giller power law scaler."""

    def test_initialization(self):
        """Test initialization."""
        scaler = GillerScaler(power=0.5)
        assert scaler.power == 0.5

    def test_initialization_invalid_power(self):
        """Test that invalid power raises error."""
        with pytest.raises(ValueError):
            GillerScaler(power=0.0)

        with pytest.raises(ValueError):
            GillerScaler(power=1.5)

    def test_scale_zero(self):
        """Test scaling zero."""
        scaler = GillerScaler()
        assert scaler.scale(0.0) == 0.0

    def test_scale_positive(self):
        """Test scaling positive values."""
        scaler = GillerScaler(power=0.5)

        # sqrt(4) = 2
        assert scaler.scale(4.0) == 2.0
        # sqrt(9) = 3
        assert scaler.scale(9.0) == 3.0

    def test_scale_negative(self):
        """Test scaling negative values."""
        scaler = GillerScaler(power=0.5)

        # -sqrt(4) = -2
        assert scaler.scale(-4.0) == -2.0

    def test_scale_preserves_sign(self):
        """Test that scaling preserves sign."""
        scaler = GillerScaler()

        assert scaler.scale(1.0) > 0
        assert scaler.scale(-1.0) < 0

    def test_scale_dampens_magnitude(self):
        """Test that scaling dampens large values."""
        scaler = GillerScaler(power=0.5)

        # For power < 1, |output| < |input| when |input| > 1
        for val in [2.0, 4.0, 10.0, 100.0]:
            scaled = abs(scaler.scale(val))
            assert scaled < val

    def test_scale_amplifies_small(self):
        """Test that scaling amplifies small values."""
        scaler = GillerScaler(power=0.5)

        # For power < 1, |output| > |input| when 0 < |input| < 1
        for val in [0.25, 0.5, 0.75]:
            scaled = abs(scaler.scale(val))
            assert scaled > val

    def test_different_powers(self):
        """Test scaling with different powers."""
        for power in [0.3, 0.5, 0.7, 0.9]:
            scaler = GillerScaler(power=power)
            result = scaler.scale(4.0)
            expected = 4.0**power
            assert abs(result - expected) < 1e-10


class TestSOPSGillerSizer:
    """Test full SOPSGillerSizer pipeline."""

    def test_initialization(self):
        """Test initialization."""
        sizer = SOPSGillerSizer(
            k_base=1.0,
            vol_alpha=0.1,
            giller_power=0.5,
            max_position=100.0,
        )
        assert sizer.max_position == 100.0

    def test_update(self):
        """Test update method."""
        sizer = SOPSGillerSizer()
        sizer.update(return_value=0.01, timestamp=1.0)

        # Should not crash
        assert sizer.k > 0

    def test_size_zero_signal(self):
        """Test size with zero signal."""
        sizer = SOPSGillerSizer()
        size = sizer.size(0.0)
        assert size == 0.0

    def test_size_bounded(self):
        """Test that output is bounded by max_position."""
        sizer = SOPSGillerSizer(max_position=100.0)

        # Even with extreme signals
        for signal in [0, 1, 10, 100, 1000]:
            size = sizer.size(signal)
            assert -100.0 <= size <= 100.0

    def test_size_pipeline(self):
        """Test full sizing pipeline."""
        sizer = SOPSGillerSizer(max_position=1.0)

        # Initialize with some data
        for i in range(30):
            sizer.update(return_value=0.01, timestamp=i * 0.1)

        signal = 1.0
        size = sizer.size(signal)

        # Should go through: SOPS -> Giller -> Tape -> final
        assert isinstance(size, float)
        assert -1.0 <= size <= 1.0

    def test_size_nan_handling(self):
        """Test that NaN signals return 0."""
        sizer = SOPSGillerSizer()
        size = sizer.size(float("nan"))
        assert size == 0.0

    def test_size_inf_handling(self):
        """Test that infinite signals return 0."""
        sizer = SOPSGillerSizer()
        size = sizer.size(float("inf"))
        assert size == 0.0

        size = sizer.size(float("-inf"))
        assert size == 0.0

    def test_get_state(self):
        """Test get_state method."""
        sizer = SOPSGillerSizer()

        for i in range(20):
            sizer.update(return_value=0.01, timestamp=i * 0.1)

        state = sizer.get_state(signal=0.5)

        assert isinstance(state, SOPSState)
        assert state.raw_signal == 0.5
        assert hasattr(state, "sops_position")
        assert hasattr(state, "giller_position")
        assert hasattr(state, "tape_weight")
        assert hasattr(state, "final_position")
        assert hasattr(state, "adaptive_k")

    def test_enable_tape_weight(self):
        """Test enabling/disabling tape weight."""
        sizer_with = SOPSGillerSizer(enable_tape_weight=True)
        sizer_without = SOPSGillerSizer(enable_tape_weight=False)

        # Feed same data
        for i in range(30):
            sizer_with.update(return_value=0.01, timestamp=i * 0.1)
            sizer_without.update(return_value=0.01, timestamp=i * 0.1)

        # Sizes will differ if tape weight != 1.0
        size_with = sizer_with.size(1.0)
        size_without = sizer_without.size(1.0)

        # Without tape weight should use weight=1.0
        state_without = sizer_without.get_state(1.0)
        assert state_without.tape_weight == 1.0

    def test_properties(self):
        """Test property accessors."""
        sizer = SOPSGillerSizer()

        for i in range(20):
            sizer.update(return_value=0.01, timestamp=i * 0.1)

        assert isinstance(sizer.k, float)
        assert isinstance(sizer.volatility, float)
        assert isinstance(sizer.tape_regime, str)
        assert isinstance(sizer.tape_lambda, float)


class TestCreateSOPSSizer:
    """Test factory function."""

    def test_create_conservative(self):
        """Test creating conservative sizer."""
        sizer = create_sops_sizer(aggressive=False, max_position=100.0)

        assert isinstance(sizer, SOPSGillerSizer)
        assert sizer.max_position == 100.0

    def test_create_aggressive(self):
        """Test creating aggressive sizer."""
        sizer = create_sops_sizer(aggressive=True, max_position=100.0)

        assert isinstance(sizer, SOPSGillerSizer)
        assert sizer.max_position == 100.0

    def test_create_with_tape(self):
        """Test creating with tape speed."""
        sizer = create_sops_sizer(use_tape_speed=True)
        assert sizer.enable_tape_weight is True

    def test_create_without_tape(self):
        """Test creating without tape speed."""
        sizer = create_sops_sizer(use_tape_speed=False)
        assert sizer.enable_tape_weight is False


class TestEdgeCases:
    """Test edge cases across all components."""

    def test_extreme_volatility_k_estimation(self):
        """Test k estimation with extreme volatility."""
        estimator = AdaptiveKEstimator()

        # Extreme volatility
        for _ in range(50):
            estimator.update(1.0)

        k = estimator.k
        # Should be clamped
        assert 0.1 <= k <= 5.0

    def test_zero_volatility_k_estimation(self):
        """Test k estimation with zero volatility."""
        estimator = AdaptiveKEstimator()

        for _ in range(50):
            estimator.update(0.0)

        k = estimator.k
        # Should be at or near k_base
        assert 0.1 <= k <= 5.0

    def test_sops_extreme_signals(self):
        """Test SOPS with extreme signals."""
        sops = SOPS()

        # Should saturate but not crash
        size = sops.size(1000.0)
        assert abs(size) <= 1.0

    def test_tape_zero_dt(self):
        """Test TapeSpeed with zero time delta."""
        tape = TapeSpeed()

        tape.update(1.0)
        tape.update(1.0)  # Same timestamp

        # Should not crash
        state = tape.state
        assert state.regime in ["fast", "normal", "slow"]

    def test_full_pipeline_extreme_conditions(self):
        """Test full pipeline with extreme conditions."""
        sizer = SOPSGillerSizer()

        # Extreme volatility
        for i in range(50):
            sizer.update(return_value=0.5, timestamp=i * 0.001)

        # Extreme signal
        size = sizer.size(1000.0)

        # Should be bounded
        assert -1.0 <= size <= 1.0

    def test_negative_returns_handling(self):
        """Test handling of negative returns."""
        sizer = SOPSGillerSizer()

        for i in range(30):
            sizer.update(return_value=-0.02, timestamp=i * 0.1)

        size = sizer.size(1.0)
        assert isinstance(size, float)
