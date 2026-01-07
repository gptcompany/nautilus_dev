"""Unit tests for Position Sizing module.

CRITICAL: This module handles REAL MONEY position sizing.
Every function MUST have comprehensive test coverage.

Tests cover:
- GillerSizer: Sub-linear position sizing (Giller 2015)
- IntegratedSizer: Meta-learning pipeline sizing (Spec 026)
- Config validation: Pydantic model validation
"""

from __future__ import annotations

import pytest

from strategies.common.position_sizing.config import (
    GillerConfig,
    IntegratedSizingConfig,
)
from strategies.common.position_sizing.giller_sizing import GillerSizer
from strategies.common.position_sizing.integrated_sizing import (
    IntegratedSize,
    IntegratedSizer,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def giller_config() -> GillerConfig:
    """Default Giller configuration for tests."""
    return GillerConfig(
        base_size=1.0,
        exponent=0.5,
        max_size=5.0,
        min_size=0.1,
    )


@pytest.fixture
def giller_sizer(giller_config: GillerConfig) -> GillerSizer:
    """Default GillerSizer for tests."""
    return GillerSizer(giller_config)


@pytest.fixture
def integrated_config() -> IntegratedSizingConfig:
    """Default IntegratedSizingConfig for tests."""
    return IntegratedSizingConfig(
        giller_exponent=0.5,
        fractional_kelly=0.5,
        min_size=0.01,
        max_size=1.0,
        default_meta_confidence=0.5,
        default_regime_weight=0.8,
        default_toxicity=0.0,
    )


@pytest.fixture
def integrated_sizer(integrated_config: IntegratedSizingConfig) -> IntegratedSizer:
    """Default IntegratedSizer for tests."""
    return IntegratedSizer(integrated_config)


# =============================================================================
# GillerConfig Validation Tests
# =============================================================================


class TestGillerConfigValidation:
    """Tests for GillerConfig Pydantic model validation."""

    def test_default_config_valid(self) -> None:
        """Default GillerConfig should be valid."""
        config = GillerConfig()
        assert config.base_size == 1.0
        assert config.exponent == 0.5
        assert config.max_size == 5.0
        assert config.min_size == 0.1

    def test_custom_config_valid(self) -> None:
        """Custom GillerConfig should be valid."""
        config = GillerConfig(
            base_size=2.0,
            exponent=0.3,
            max_size=10.0,
            min_size=0.5,
        )
        assert config.base_size == 2.0
        assert config.exponent == 0.3

    def test_min_size_greater_than_max_raises_error(self) -> None:
        """min_size > max_size should raise ValidationError."""
        with pytest.raises(ValueError, match="min_size.*must be <= max_size"):
            GillerConfig(min_size=10.0, max_size=5.0)

    def test_negative_base_size_raises_error(self) -> None:
        """Negative base_size should raise ValidationError."""
        with pytest.raises(ValueError):
            GillerConfig(base_size=-1.0)

    def test_exponent_greater_than_one_raises_error(self) -> None:
        """exponent > 1.0 should raise ValidationError."""
        with pytest.raises(ValueError):
            GillerConfig(exponent=1.5)

    def test_zero_exponent_raises_error(self) -> None:
        """exponent = 0 should raise ValidationError."""
        with pytest.raises(ValueError):
            GillerConfig(exponent=0.0)


# =============================================================================
# GillerSizer Tests
# =============================================================================


class TestGillerSizerBasicCalculation:
    """Tests for basic GillerSizer.calculate() functionality."""

    def test_positive_signal_returns_positive_size(self, giller_sizer: GillerSizer) -> None:
        """Positive signal should return positive position size."""
        result = giller_sizer.calculate(signal=1.0)
        assert result > 0.0

    def test_negative_signal_returns_negative_size(self, giller_sizer: GillerSizer) -> None:
        """Negative signal (SHORT) should return negative position size."""
        result = giller_sizer.calculate(signal=-1.0)
        assert result < 0.0

    def test_zero_signal_returns_zero(self, giller_sizer: GillerSizer) -> None:
        """Zero signal should return zero position size."""
        result = giller_sizer.calculate(signal=0.0)
        assert result == 0.0

    def test_small_signal_returns_small_size(self, giller_sizer: GillerSizer) -> None:
        """Small signal should return smaller size than large signal."""
        small_result = giller_sizer.calculate(signal=0.1)
        large_result = giller_sizer.calculate(signal=1.0)
        # Due to sub-linear scaling, large_result should be less than 10x small_result
        assert large_result > small_result
        assert large_result < 10 * small_result  # Sub-linear: sqrt(10) ≈ 3.16


class TestGillerSizerEdgeCases:
    """Tests for GillerSizer edge cases and invalid inputs."""

    def test_nan_signal_returns_zero(self, giller_sizer: GillerSizer) -> None:
        """NaN signal should return zero (safe default)."""
        result = giller_sizer.calculate(signal=float("nan"))
        assert result == 0.0

    def test_positive_inf_signal_returns_zero(self, giller_sizer: GillerSizer) -> None:
        """Positive infinity signal should return zero."""
        result = giller_sizer.calculate(signal=float("inf"))
        assert result == 0.0

    def test_negative_inf_signal_returns_zero(self, giller_sizer: GillerSizer) -> None:
        """Negative infinity signal should return zero."""
        result = giller_sizer.calculate(signal=float("-inf"))
        assert result == 0.0


class TestGillerSizerInputClamping:
    """Tests for regime_weight and toxicity input clamping."""

    def test_negative_regime_weight_clamped_to_zero(self, giller_sizer: GillerSizer) -> None:
        """Negative regime_weight should be clamped to 0."""
        result = giller_sizer.calculate(signal=1.0, regime_weight=-0.5)
        assert result == 0.0  # 0 regime_weight → 0 size

    def test_regime_weight_over_one_clamped(self, giller_sizer: GillerSizer) -> None:
        """regime_weight > 1.0 should be clamped to 1.0."""
        result_clamped = giller_sizer.calculate(signal=1.0, regime_weight=2.0)
        result_normal = giller_sizer.calculate(signal=1.0, regime_weight=1.0)
        assert result_clamped == result_normal

    def test_negative_toxicity_clamped_to_zero(self, giller_sizer: GillerSizer) -> None:
        """Negative toxicity should be clamped to 0."""
        result = giller_sizer.calculate(signal=1.0, toxicity=-0.5)
        result_zero = giller_sizer.calculate(signal=1.0, toxicity=0.0)
        assert result == result_zero

    def test_toxicity_over_one_clamped(self, giller_sizer: GillerSizer) -> None:
        """toxicity > 1.0 should be clamped to 1.0, resulting in 0 (don't trade)."""
        result = giller_sizer.calculate(signal=1.0, toxicity=2.0)
        # 1.0 toxicity → (1 - 1.0) = 0 multiplier → 0 size (don't trade in toxic conditions)
        assert result == 0.0

    def test_toxicity_one_returns_zero(self, giller_sizer: GillerSizer) -> None:
        """toxicity = 1.0 should give zero size (full penalty = don't trade)."""
        result = giller_sizer.calculate(signal=1.0, toxicity=1.0)
        # (1 - 1.0) = 0 → don't trade when flow is fully toxic
        assert result == 0.0


class TestGillerSizerSizeLimits:
    """Tests for min/max size enforcement."""

    def test_result_clamped_to_min_size(self) -> None:
        """Small signals should be clamped to min_size."""
        config = GillerConfig(base_size=0.001, min_size=0.1, max_size=5.0)
        sizer = GillerSizer(config)
        result = sizer.calculate(signal=0.01)
        # Very small result should be clamped to min_size
        assert abs(result) == config.min_size

    def test_result_clamped_to_max_size(self) -> None:
        """Large signals should be clamped to max_size."""
        config = GillerConfig(base_size=100.0, min_size=0.1, max_size=5.0)
        sizer = GillerSizer(config)
        result = sizer.calculate(signal=10.0)
        assert abs(result) == config.max_size

    def test_sign_preserved_after_max_clamp(self) -> None:
        """Sign should be preserved when clamping to max_size."""
        config = GillerConfig(base_size=100.0, min_size=0.1, max_size=5.0)
        sizer = GillerSizer(config)

        positive_result = sizer.calculate(signal=10.0)
        negative_result = sizer.calculate(signal=-10.0)

        assert positive_result == 5.0
        assert negative_result == -5.0


class TestGillerSizerSubLinearScaling:
    """Tests verifying sub-linear (sqrt) scaling behavior."""

    def test_sqrt_scaling_4x_signal_gives_2x_size(self) -> None:
        """With exponent=0.5, 4x signal should give 2x size (sqrt(4)=2)."""
        config = GillerConfig(base_size=1.0, exponent=0.5, min_size=0.0, max_size=100.0)
        sizer = GillerSizer(config)

        size_1 = sizer.calculate(signal=1.0)
        size_4 = sizer.calculate(signal=4.0)

        # sqrt(4) = 2, so size_4 should be 2x size_1
        assert abs(size_4 / size_1 - 2.0) < 0.001

    def test_linear_scaling_with_exponent_one(self) -> None:
        """With exponent=1.0, scaling should be linear."""
        config = GillerConfig(base_size=1.0, exponent=1.0, min_size=0.0, max_size=100.0)
        sizer = GillerSizer(config)

        size_1 = sizer.calculate(signal=1.0)
        size_4 = sizer.calculate(signal=4.0)

        # Linear: 4x signal → 4x size
        assert abs(size_4 / size_1 - 4.0) < 0.001


class TestGillerSizerFormulaVerification:
    """Tests verifying the complete formula calculation."""

    def test_full_formula_calculation(self) -> None:
        """Verify complete formula: sign * |signal|^exp * base * regime * (1-tox)."""
        config = GillerConfig(base_size=2.0, exponent=0.5, min_size=0.0, max_size=100.0)
        sizer = GillerSizer(config)

        signal = 4.0
        regime_weight = 0.8
        toxicity = 0.2

        result = sizer.calculate(signal=signal, regime_weight=regime_weight, toxicity=toxicity)

        # Manual calculation:
        # sign = 1 (positive signal)
        # scaled = |4.0|^0.5 = 2.0
        # size = 2.0 * 2.0 * 0.8 * (1.0 - 0.2) = 2.0 * 2.0 * 0.8 * 0.8 = 2.56
        expected = 2.0 * 2.0 * 0.8 * 0.8

        assert abs(result - expected) < 0.001


# =============================================================================
# IntegratedSizingConfig Validation Tests
# =============================================================================


class TestIntegratedSizingConfigValidation:
    """Tests for IntegratedSizingConfig Pydantic model validation."""

    def test_default_config_valid(self) -> None:
        """Default IntegratedSizingConfig should be valid."""
        config = IntegratedSizingConfig()
        assert config.giller_exponent == 0.5
        assert config.fractional_kelly == 0.5
        assert config.min_size == 0.01
        assert config.max_size == 1.0

    def test_min_size_greater_than_max_raises_error(self) -> None:
        """min_size > max_size should raise ValidationError."""
        with pytest.raises(ValueError, match="min_size.*must be <= max_size"):
            IntegratedSizingConfig(min_size=5.0, max_size=1.0)

    def test_negative_kelly_raises_error(self) -> None:
        """Negative fractional_kelly should raise ValidationError."""
        with pytest.raises(ValueError):
            IntegratedSizingConfig(fractional_kelly=-0.5)

    def test_kelly_over_one_raises_error(self) -> None:
        """fractional_kelly > 1.0 should raise ValidationError."""
        with pytest.raises(ValueError):
            IntegratedSizingConfig(fractional_kelly=1.5)


# =============================================================================
# IntegratedSizer Tests
# =============================================================================


class TestIntegratedSizerBasicCalculation:
    """Tests for basic IntegratedSizer.calculate() functionality."""

    def test_positive_signal_returns_positive_direction(
        self, integrated_sizer: IntegratedSizer
    ) -> None:
        """Positive signal should return direction=1."""
        result = integrated_sizer.calculate(signal=1.0)
        assert result.direction == 1
        assert result.final_size > 0

    def test_negative_signal_returns_negative_direction(
        self, integrated_sizer: IntegratedSizer
    ) -> None:
        """Negative signal should return direction=-1."""
        result = integrated_sizer.calculate(signal=-1.0)
        assert result.direction == -1
        assert result.final_size < 0

    def test_zero_signal_returns_zero_direction(self, integrated_sizer: IntegratedSizer) -> None:
        """Zero signal should return direction=0 and size=0."""
        result = integrated_sizer.calculate(signal=0.0)
        assert result.direction == 0
        assert result.final_size == 0.0

    def test_returns_integrated_size_dataclass(self, integrated_sizer: IntegratedSizer) -> None:
        """Result should be IntegratedSize dataclass."""
        result = integrated_sizer.calculate(signal=1.0)
        assert isinstance(result, IntegratedSize)
        assert hasattr(result, "final_size")
        assert hasattr(result, "direction")
        assert hasattr(result, "factors")


class TestIntegratedSizerDefaults:
    """Tests for default value handling."""

    def test_uses_default_meta_confidence_when_none(
        self, integrated_sizer: IntegratedSizer
    ) -> None:
        """Should use default_meta_confidence when None provided."""
        result = integrated_sizer.calculate(signal=1.0, meta_confidence=None)
        assert result.factors["meta_confidence"] == integrated_sizer.config.default_meta_confidence

    def test_uses_default_regime_weight_when_none(self, integrated_sizer: IntegratedSizer) -> None:
        """Should use default_regime_weight when None provided."""
        result = integrated_sizer.calculate(signal=1.0, regime_weight=None)
        assert result.factors["regime_weight"] == integrated_sizer.config.default_regime_weight

    def test_uses_default_toxicity_when_none(self, integrated_sizer: IntegratedSizer) -> None:
        """Should use default_toxicity when None provided."""
        result = integrated_sizer.calculate(signal=1.0, toxicity=None)
        expected_penalty = 1.0 - integrated_sizer.config.default_toxicity
        assert result.factors["toxicity_penalty"] == expected_penalty

    def test_none_config_uses_defaults(self) -> None:
        """IntegratedSizer(None) should use default config."""
        sizer = IntegratedSizer(None)
        assert sizer.config.giller_exponent == 0.5
        assert sizer.config.fractional_kelly == 0.5


class TestIntegratedSizerSizeLimits:
    """Tests for min/max size enforcement."""

    def test_below_min_size_clamped_to_zero(self) -> None:
        """Size below min_size should be clamped to 0 (no trade)."""
        config = IntegratedSizingConfig(
            min_size=0.5,
            max_size=1.0,
            fractional_kelly=0.001,  # Very small Kelly fraction
        )
        sizer = IntegratedSizer(config)
        result = sizer.calculate(signal=0.01)

        assert result.final_size == 0.0
        assert result.direction == 0  # Direction reset when clamped to 0

    def test_above_max_size_clamped(self) -> None:
        """Size above max_size should be clamped to max_size."""
        config = IntegratedSizingConfig(
            min_size=0.01,
            max_size=0.5,
            fractional_kelly=1.0,  # Full Kelly
        )
        sizer = IntegratedSizer(config)
        result = sizer.calculate(signal=10.0, meta_confidence=1.0, regime_weight=1.0)

        assert abs(result.final_size) == config.max_size

    def test_sign_preserved_after_max_clamp(self) -> None:
        """Sign should be preserved when clamping to max_size."""
        config = IntegratedSizingConfig(
            min_size=0.01,
            max_size=0.5,
            fractional_kelly=1.0,
        )
        sizer = IntegratedSizer(config)

        positive_result = sizer.calculate(signal=10.0, meta_confidence=1.0)
        negative_result = sizer.calculate(signal=-10.0, meta_confidence=1.0)

        assert positive_result.final_size == 0.5
        assert negative_result.final_size == -0.5
        assert positive_result.direction == 1
        assert negative_result.direction == -1


class TestIntegratedSizerFactorBreakdown:
    """Tests for factor breakdown in results."""

    def test_factor_breakdown_contains_all_factors(self, integrated_sizer: IntegratedSizer) -> None:
        """Factors dict should contain all contributing factors."""
        result = integrated_sizer.calculate(signal=1.0)

        assert "signal" in result.factors
        assert "meta_confidence" in result.factors
        assert "regime_weight" in result.factors
        assert "toxicity_penalty" in result.factors
        assert "kelly_fraction" in result.factors

    def test_factor_breakdown_for_zero_signal(self, integrated_sizer: IntegratedSizer) -> None:
        """Zero signal should have all-zero factors."""
        result = integrated_sizer.calculate(signal=0.0)

        for key, value in result.factors.items():
            assert value == 0.0, f"Factor {key} should be 0.0 for zero signal"


class TestIntegratedSizerFormulaVerification:
    """Tests verifying the complete formula calculation."""

    def test_full_formula_calculation(self) -> None:
        """Verify complete formula: dir * |sig|^exp * meta * regime * (1-tox) * kelly."""
        config = IntegratedSizingConfig(
            giller_exponent=0.5,
            fractional_kelly=0.5,
            min_size=0.0,
            max_size=10.0,
        )
        sizer = IntegratedSizer(config)

        signal = 4.0
        meta_confidence = 0.8
        regime_weight = 0.9
        toxicity = 0.1

        result = sizer.calculate(
            signal=signal,
            meta_confidence=meta_confidence,
            regime_weight=regime_weight,
            toxicity=toxicity,
        )

        # Manual calculation:
        # signal_factor = |4.0|^0.5 = 2.0
        # toxicity_penalty = 1 - 0.1 = 0.9
        # raw_size = 2.0 * 0.8 * 0.9 * 0.9 * 0.5 = 0.648
        # direction = 1
        # final_size = 1 * 0.648 = 0.648
        expected = 2.0 * 0.8 * 0.9 * 0.9 * 0.5

        assert abs(result.final_size - expected) < 0.001
        assert result.direction == 1


class TestIntegratedSizerConfigProperty:
    """Tests for config property access."""

    def test_config_property_returns_config(
        self, integrated_sizer: IntegratedSizer, integrated_config: IntegratedSizingConfig
    ) -> None:
        """config property should return the configuration."""
        assert integrated_sizer.config == integrated_config

    def test_config_is_immutable(self, integrated_sizer: IntegratedSizer) -> None:
        """Config should be immutable (frozen=True)."""
        with pytest.raises(Exception):  # Pydantic raises ValidationError
            integrated_sizer.config.giller_exponent = 0.9  # type: ignore
