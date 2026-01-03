"""Tests for Integrated Position Sizing (Spec 026 - US4).

TDD RED Phase: These tests should FAIL until implementation is complete.
"""

from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.meta_learning
class TestIntegratedSizer:
    """Test suite for IntegratedSizer class."""

    def test_calculate_returns_integrated_size(self, integrated_sizing_config):
        """Test that calculate() returns IntegratedSize object."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        result = sizer.calculate(
            signal=1.0,
            meta_confidence=0.8,
            regime_weight=1.0,
            toxicity=0.1,
        )

        assert hasattr(result, "final_size")
        assert hasattr(result, "direction")
        assert hasattr(result, "factors")

    def test_multiplicative_combination_formula(self, integrated_sizing_config):
        """Test that formula combines factors multiplicatively."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        signal = 1.0
        meta_confidence = 0.8
        regime_weight = 1.0
        toxicity = 0.2

        result = sizer.calculate(
            signal=signal,
            meta_confidence=meta_confidence,
            regime_weight=regime_weight,
            toxicity=toxicity,
        )

        # Expected: direction * |signal|^0.5 * meta * regime * (1-toxicity) * kelly
        expected = (
            1  # direction
            * (abs(signal) ** integrated_sizing_config.giller_exponent)
            * meta_confidence
            * regime_weight
            * (1 - toxicity)
            * integrated_sizing_config.fractional_kelly
        )

        assert result.final_size == pytest.approx(expected, rel=1e-5)

    def test_direction_preserved(self, integrated_sizing_config):
        """Test that signal direction is preserved in output."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        # Long signal
        result_long = sizer.calculate(signal=1.0, meta_confidence=0.8)
        assert result_long.direction == 1
        assert result_long.final_size > 0

        # Short signal
        result_short = sizer.calculate(signal=-1.0, meta_confidence=0.8)
        assert result_short.direction == -1
        assert result_short.final_size < 0

    def test_zero_signal_returns_zero_size(self, integrated_sizing_config):
        """Test that zero signal results in zero position size."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        result = sizer.calculate(signal=0.0, meta_confidence=0.8)

        assert result.final_size == 0.0
        assert result.direction == 0


@pytest.mark.meta_learning
class TestEdgeCases:
    """Test edge cases for integrated sizing."""

    def test_high_toxicity_reduces_size(self, integrated_sizing_config):
        """Test that high toxicity significantly reduces position size."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        result_low_toxicity = sizer.calculate(
            signal=1.0,
            meta_confidence=0.8,
            regime_weight=1.0,
            toxicity=0.1,
        )

        result_high_toxicity = sizer.calculate(
            signal=1.0,
            meta_confidence=0.8,
            regime_weight=1.0,
            toxicity=0.9,
        )

        # High toxicity should result in much smaller position
        assert abs(result_high_toxicity.final_size) < abs(
            result_low_toxicity.final_size
        )
        # With toxicity=0.9, size should be ~11% of low toxicity
        ratio = abs(result_high_toxicity.final_size) / abs(
            result_low_toxicity.final_size
        )
        assert ratio < 0.15

    def test_low_confidence_reduces_size(self, integrated_sizing_config):
        """Test that low meta-confidence reduces position size."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        result_high_conf = sizer.calculate(
            signal=1.0,
            meta_confidence=0.9,
            regime_weight=1.0,
            toxicity=0.0,
        )

        result_low_conf = sizer.calculate(
            signal=1.0,
            meta_confidence=0.3,
            regime_weight=1.0,
            toxicity=0.0,
        )

        # Low confidence should result in smaller position
        assert abs(result_low_conf.final_size) < abs(result_high_conf.final_size)


@pytest.mark.meta_learning
class TestDefaultValues:
    """Test default value handling for missing factors."""

    def test_missing_meta_confidence_uses_default(self, integrated_sizing_config):
        """Test that missing meta_confidence uses config default."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        result = sizer.calculate(
            signal=1.0,
            meta_confidence=None,  # Missing
            regime_weight=1.0,
            toxicity=0.0,
        )

        # Should use default_meta_confidence from config
        expected = (
            1.0**integrated_sizing_config.giller_exponent
            * integrated_sizing_config.default_meta_confidence
            * 1.0
            * 1.0
            * integrated_sizing_config.fractional_kelly
        )

        assert result.final_size == pytest.approx(expected, rel=1e-5)

    def test_missing_regime_weight_uses_default(self, integrated_sizing_config):
        """Test that missing regime_weight uses config default."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        result = sizer.calculate(
            signal=1.0,
            meta_confidence=0.8,
            regime_weight=None,  # Missing
            toxicity=0.0,
        )

        # Should use default_regime_weight from config
        expected = (
            1.0**integrated_sizing_config.giller_exponent
            * 0.8
            * integrated_sizing_config.default_regime_weight
            * 1.0
            * integrated_sizing_config.fractional_kelly
        )

        assert result.final_size == pytest.approx(expected, rel=1e-5)

    def test_missing_toxicity_uses_default(self, integrated_sizing_config):
        """Test that missing toxicity uses config default."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        result = sizer.calculate(
            signal=1.0,
            meta_confidence=0.8,
            regime_weight=1.0,
            toxicity=None,  # Missing
        )

        # Should use default_toxicity from config (0.0)
        expected = (
            1.0**integrated_sizing_config.giller_exponent
            * 0.8
            * 1.0
            * (1 - integrated_sizing_config.default_toxicity)
            * integrated_sizing_config.fractional_kelly
        )

        assert result.final_size == pytest.approx(expected, rel=1e-5)

    def test_all_defaults_work_together(self, integrated_sizing_config):
        """Test that all defaults work when all optional params missing."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        # Only signal provided
        result = sizer.calculate(signal=1.0)

        # Should use all defaults
        expected = (
            1.0**integrated_sizing_config.giller_exponent
            * integrated_sizing_config.default_meta_confidence
            * integrated_sizing_config.default_regime_weight
            * (1 - integrated_sizing_config.default_toxicity)
            * integrated_sizing_config.fractional_kelly
        )

        assert result.final_size == pytest.approx(expected, rel=1e-5)


@pytest.mark.meta_learning
class TestSizeClamping:
    """Test min/max size clamping."""

    def test_min_size_clamping(self):
        """Test that very small sizes are clamped to min_size."""
        from strategies.common.position_sizing.config import IntegratedSizingConfig
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        config = IntegratedSizingConfig(
            min_size=0.1,
            max_size=1.0,
        )
        sizer = IntegratedSizer(config)

        # Very low confidence should produce small size
        result = sizer.calculate(
            signal=0.01,  # Very small signal
            meta_confidence=0.1,
            regime_weight=0.5,
            toxicity=0.9,
        )

        # Should be clamped to min_size or 0 if too small
        assert abs(result.final_size) >= config.min_size or result.final_size == 0

    def test_max_size_clamping(self):
        """Test that large sizes are clamped to max_size."""
        from strategies.common.position_sizing.config import IntegratedSizingConfig
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        config = IntegratedSizingConfig(
            min_size=0.01,
            max_size=0.5,  # Lower max
            giller_exponent=1.0,  # Linear scaling
            fractional_kelly=1.0,  # Full Kelly
        )
        sizer = IntegratedSizer(config)

        # All factors at maximum
        result = sizer.calculate(
            signal=10.0,  # Large signal
            meta_confidence=1.0,
            regime_weight=1.5,
            toxicity=0.0,
        )

        # Should be clamped to max_size
        assert abs(result.final_size) <= config.max_size


@pytest.mark.meta_learning
class TestFactorBreakdown:
    """Test factor contribution tracking."""

    def test_factors_property_returns_breakdown(self, integrated_sizing_config):
        """Test that factors property returns contribution breakdown."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        result = sizer.calculate(
            signal=1.0,
            meta_confidence=0.8,
            regime_weight=1.0,
            toxicity=0.2,
        )

        factors = result.factors

        assert "signal" in factors
        assert "meta_confidence" in factors
        assert "regime_weight" in factors
        assert "toxicity_penalty" in factors
        assert "kelly_fraction" in factors

    def test_factor_values_are_correct(self, integrated_sizing_config):
        """Test that factor values match inputs."""
        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        result = sizer.calculate(
            signal=2.0,
            meta_confidence=0.75,
            regime_weight=1.1,
            toxicity=0.15,
        )

        factors = result.factors

        # Signal contribution is |signal|^exponent
        expected_signal = abs(2.0) ** integrated_sizing_config.giller_exponent
        assert factors["signal"] == pytest.approx(expected_signal, rel=1e-5)

        assert factors["meta_confidence"] == pytest.approx(0.75, rel=1e-5)
        assert factors["regime_weight"] == pytest.approx(1.1, rel=1e-5)
        assert factors["toxicity_penalty"] == pytest.approx(1 - 0.15, rel=1e-5)
        assert factors["kelly_fraction"] == pytest.approx(
            integrated_sizing_config.fractional_kelly, rel=1e-5
        )


@pytest.mark.meta_learning
class TestIntegratedSizingPerformance:
    """Test performance requirements."""

    def test_calculation_latency(self, integrated_sizing_config):
        """Test that calculation completes in <20ms."""
        import time

        from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

        sizer = IntegratedSizer(integrated_sizing_config)

        # Warm up
        sizer.calculate(signal=1.0)

        # Measure
        start = time.time()
        for _ in range(100):
            sizer.calculate(
                signal=np.random.uniform(-1, 1),
                meta_confidence=np.random.uniform(0, 1),
                regime_weight=np.random.uniform(0.4, 1.2),
                toxicity=np.random.uniform(0, 0.5),
            )
        elapsed = (time.time() - start) / 100

        # Should be <20ms (actually should be microseconds)
        assert elapsed < 0.02, f"Calculation took {elapsed * 1000:.2f}ms (>20ms limit)"
