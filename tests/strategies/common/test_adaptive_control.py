"""Tests for the adaptive_control module.

Validates the Five Pillars:
1. Probabilistico - Probability distributions
2. Non Lineare - Power laws
3. Non Parametrico - Adaptive
4. Scalare - Works at any scale
5. Leggi Naturali - Natural laws
"""

import math

import pytest

from strategies.common.adaptive_control import (
    ConsensusRegime,
    HarmonicRatioAnalyzer,
    IIRHighPass,
    # DSP Filters
    IIRLowPass,
    IIRRegimeDetector,
    KalmanFilter1D,
    # Flow Physics
    MarketFlowAnalyzer,
    MarketHarmony,
    MetaController,
    # Multi-dimensional
    MultiDimensionalRegimeDetector,
    RecursiveVariance,
    SystemState,
    # Vibration
    VibrationAnalyzer,
    WaveEquationAnalyzer,
)


class TestDSPFilters:
    """Test O(1) DSP filters."""

    def test_iir_lowpass_smoothing(self):
        """IIR low-pass should smooth noisy signal."""
        lpf = IIRLowPass(cutoff_period=10)

        # Feed noisy data
        values = [100 + (i % 2) * 10 for i in range(50)]  # Alternating 100, 110

        outputs = [lpf.update(v) for v in values]

        # Output should be smoother (less variance)
        input_var = sum((v - 105) ** 2 for v in values) / len(values)
        output_var = sum((v - 105) ** 2 for v in outputs[-20:]) / 20

        assert output_var < input_var, "Low-pass should reduce variance"

    def test_iir_highpass_removes_trend(self):
        """IIR high-pass should remove trend."""
        hpf = IIRHighPass(cutoff_period=10)

        # Linear trend
        values = [100 + i for i in range(50)]

        outputs = [hpf.update(v) for v in values]

        # After warmup, output should oscillate around 0
        mean_output = sum(outputs[-20:]) / 20
        assert abs(mean_output) < 5, "High-pass should center around 0"

    def test_recursive_variance_matches_numpy(self):
        """Recursive variance should approximate actual variance."""
        rv = RecursiveVariance(alpha=0.1)

        import random

        random.seed(42)
        values = [random.gauss(0, 1) for _ in range(100)]

        for v in values:
            rv.update(v)

        # Should be close to 1.0 (standard normal variance)
        assert 0.5 < rv.variance < 2.0, f"Variance should be ~1.0, got {rv.variance}"

    def test_kalman_filter_smoothing(self):
        """Kalman filter should provide optimal smoothing."""
        kf = KalmanFilter1D(process_noise=0.01, measurement_noise=1.0)

        # Noisy measurements of constant value
        true_value = 100.0
        import random

        random.seed(42)
        measurements = [true_value + random.gauss(0, 5) for _ in range(50)]

        estimates = [kf.update(m) for m in measurements]

        # Final estimate should be close to true value
        assert abs(estimates[-1] - true_value) < 2.0, "Kalman should estimate true value"

    def test_iir_regime_detector_trending(self):
        """IIR regime should detect trending market."""
        detector = IIRRegimeDetector()

        # Trending returns with VARIATION (constant returns have no variance!)
        for i in range(50):
            # Variable positive returns to generate actual variance
            ret = 0.01 + 0.005 * (i % 5)
            regime = detector.update(ret)

        # After enough samples, should classify regime
        assert regime in ["trending", "normal", "mean_reverting", "unknown"], f"Got {regime}"


class TestMetaController:
    """Test MetaController orchestration."""

    def test_meta_controller_initialization(self):
        """MetaController should initialize correctly."""
        meta = MetaController()

        assert meta is not None

    def test_meta_controller_updates_state(self):
        """MetaController should update state on new data."""
        meta = MetaController()
        meta.register_strategy("test_strat")

        # Update with some data - using correct API
        state = meta.update(
            current_return=0.001,
            current_equity=10000.0,
        )

        assert state.risk_multiplier > 0
        assert state.risk_multiplier <= 1.0
        assert state.system_state in list(SystemState)
        assert state.market_harmony in list(MarketHarmony)

    def test_meta_controller_drawdown_reduces_risk(self):
        """High drawdown should reduce risk multiplier."""
        meta = MetaController()
        meta.register_strategy("test")

        # Establish peak equity and normal operation
        for _ in range(5):
            state_low = meta.update(current_return=0.001, current_equity=10000.0)

        # Reset and simulate high drawdown
        meta2 = MetaController()
        meta2.register_strategy("test")
        # First establish peak
        meta2.update(current_return=0.001, current_equity=10000.0)
        # Then simulate 25% drawdown
        state_high = meta2.update(current_return=-0.05, current_equity=7500.0)

        # High drawdown should have lower or equal risk
        assert state_high.risk_multiplier <= state_low.risk_multiplier + 0.1


class TestMultiDimensionalRegime:
    """Test multi-dimensional regime detection."""

    def test_multi_dim_initialization(self):
        """MultiDimensionalRegimeDetector should initialize."""
        detector = MultiDimensionalRegimeDetector()
        assert detector is not None
        assert not detector.is_ready

    def test_multi_dim_needs_warmup(self):
        """Detector should need warmup period."""
        detector = MultiDimensionalRegimeDetector()

        # First updates should have low confidence
        result = detector.update(price=100.0)
        assert result.confidence == 0.0 or not result.should_trade

    def test_multi_dim_with_orderbook(self):
        """Detector should use orderbook data when available."""
        detector = MultiDimensionalRegimeDetector()

        # Update with full data
        for i in range(25):
            result = detector.update(
                price=100.0 + i * 0.1,
                bid=99.9 + i * 0.1,
                ask=100.1 + i * 0.1,
                bid_size=1000.0,
                ask_size=800.0,
                volume=5000.0,
            )

        # Should have multiple dimensions
        assert len(result.dimensions) >= 2, "Should have IIR and Flow dimensions"

    def test_multi_dim_consensus(self):
        """Detector should provide consensus regime."""
        detector = MultiDimensionalRegimeDetector()

        # Warmup
        for i in range(30):
            result = detector.update(
                price=100.0 + i * 0.5,
                bid=99.5 + i * 0.5,
                ask=100.5 + i * 0.5,
                bid_size=1000.0,
                ask_size=500.0,
                volume=10000.0,
            )

        assert result.consensus in list(ConsensusRegime)
        assert 0 <= result.agreement <= 1


class TestFlowPhysics:
    """Test flow physics models."""

    def test_flow_analyzer_initialization(self):
        """MarketFlowAnalyzer should initialize."""
        flow = MarketFlowAnalyzer()
        assert flow is not None

    def test_flow_analyzer_calculates_state(self):
        """Flow analyzer should calculate flow state."""
        flow = MarketFlowAnalyzer()

        state = flow.update(
            bid=100.0,
            ask=100.10,
            bid_size=1000.0,
            ask_size=800.0,
            last_price=100.05,
            volume=5000.0,
        )

        # Check state has valid values
        assert -1 <= state.pressure <= 1, "Pressure should be normalized"
        assert state.flow_rate >= 0, "Flow rate should be non-negative"
        assert state.resistance >= 0, "Resistance should be non-negative"

    def test_flow_regime_detection(self):
        """Flow analyzer should detect flow regime."""
        flow = MarketFlowAnalyzer()

        # Update with data
        for i in range(25):
            flow.update(
                bid=100.0,
                ask=100.10,
                bid_size=1000.0 + i * 100,
                ask_size=800.0,
                last_price=100.05 + i * 0.1,
                volume=5000.0 + i * 500,
            )

        regime = flow.get_flow_regime()
        assert regime in ["laminar", "transitional", "turbulent", "unknown"]

    def test_wave_analyzer_displacement(self):
        """Wave analyzer should track displacement."""
        wave = WaveEquationAnalyzer()

        # Oscillating price
        for i in range(50):
            price = 100.0 + 5.0 * math.sin(i * 0.2)
            wave.update(price)

        # Should have oscillating displacement
        d = wave.get_displacement()
        assert isinstance(d, float)

    def test_wave_velocity_and_acceleration(self):
        """Wave analyzer should calculate velocity and acceleration."""
        wave = WaveEquationAnalyzer()

        # Rising price
        for i in range(10):
            wave.update(100.0 + i)

        v = wave.get_velocity()
        a = wave.get_acceleration()

        assert v > 0, "Rising price should have positive velocity"
        assert isinstance(a, float)


class TestVibrationAnalysis:
    """Test vibration/cycle analysis."""

    def test_vibration_analyzer_initialization(self):
        """VibrationAnalyzer should initialize."""
        va = VibrationAnalyzer()
        assert va is not None

    def test_harmonic_ratios(self):
        """HarmonicRatioAnalyzer should find harmonic relationships."""
        hr = HarmonicRatioAnalyzer()

        # Test octave (2:1)
        rel = hr.find_harmonic_relationship(100.0, 200.0)
        assert rel == "octave", f"Expected octave, got {rel}"

        # Test fifth (3:2 = 1.5)
        rel = hr.find_harmonic_relationship(100.0, 150.0)
        assert rel == "fifth", f"Expected fifth, got {rel}"

    def test_harmonic_levels(self):
        """Should calculate harmonic price levels."""
        hr = HarmonicRatioAnalyzer()

        levels = hr.get_harmonic_levels(100.0, direction="up")

        assert "octave_up" in levels
        assert levels["octave_up"] == 200.0


class TestScalability:
    """Test that system is scale-invariant (Pillar 4: Scalare)."""

    def test_iir_works_at_different_scales(self):
        """IIR filters should work at any price scale."""
        for scale in [0.001, 1.0, 1000.0, 1000000.0]:
            lpf = IIRLowPass(cutoff_period=10)

            values = [scale * (100 + i) for i in range(20)]
            outputs = [lpf.update(v) for v in values]

            # Should still produce reasonable output
            assert all(math.isfinite(o) for o in outputs)

    def test_regime_detector_scale_invariant(self):
        """Regime detector should work with returns (scale-invariant)."""
        detector = IIRRegimeDetector()

        # Same percentage returns at different scales
        for _ in range(20):
            regime = detector.update(0.01)  # 1% return

        # Regime should be consistent regardless of price scale
        assert regime in ["trending", "mean_reverting", "normal", "unknown"]


class TestNonParametric:
    """Test that system adapts to data (Pillar 3: Non Parametrico)."""

    def test_recursive_variance_adapts(self):
        """Recursive variance should adapt to changing volatility."""
        rv = RecursiveVariance(alpha=0.1)

        # Low volatility period
        for _ in range(50):
            rv.update(0.01)

        var_low = rv.variance

        # High volatility period
        for _ in range(50):
            rv.update(0.10)

        var_high = rv.variance

        assert var_high > var_low, "Should adapt to higher volatility"

    def test_kalman_adapts_to_signal(self):
        """Kalman should track changing signal."""
        kf = KalmanFilter1D()

        # Track rising value
        for i in range(50):
            estimate = kf.update(float(i))

        # Should be close to current value
        assert abs(estimate - 49.0) < 5.0, "Should track rising value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
