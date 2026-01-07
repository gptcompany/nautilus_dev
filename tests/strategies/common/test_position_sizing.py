"""
CRITICAL TESTS - Position Sizing Module

This module handles REAL MONEY. These tests are NON-NEGOTIABLE.
90% coverage REQUIRED.

Tests cover:
- GillerSizer: Sub-linear position sizing
- IntegratedSizer: Combined sizing with meta-learning
- GillerConfig: Configuration validation
- IntegratedSizingConfig: Configuration validation
"""

from __future__ import annotations

import math

import pytest

from strategies.common.position_sizing.config import GillerConfig, IntegratedSizingConfig
from strategies.common.position_sizing.giller_sizing import GillerSizer
from strategies.common.position_sizing.integrated_sizing import IntegratedSizer

# =============================================================================
# GillerConfig Tests
# =============================================================================


class TestGillerConfigValidation:
    """Tests for GillerConfig Pydantic validation."""

    def test_default_config(self) -> None:
        """Default config should have sensible values."""
        config = GillerConfig()
        assert config.base_size == 1.0
        assert config.exponent == 0.5
        assert config.max_size == 5.0
        assert config.min_size == 0.1

    def test_custom_config(self) -> None:
        """Should accept custom values within bounds."""
        config = GillerConfig(
            base_size=2.0,
            exponent=0.3,
            max_size=10.0,
            min_size=0.5,
        )
        assert config.base_size == 2.0
        assert config.exponent == 0.3

    def test_rejects_negative_base_size(self) -> None:
        """Should reject base_size <= 0."""
        with pytest.raises(ValueError):
            GillerConfig(base_size=-1.0)

    def test_rejects_zero_base_size(self) -> None:
        """Should reject base_size == 0."""
        with pytest.raises(ValueError):
            GillerConfig(base_size=0.0)

    def test_rejects_exponent_above_one(self) -> None:
        """Should reject exponent > 1 (would be super-linear)."""
        with pytest.raises(ValueError):
            GillerConfig(exponent=1.5)

    def test_rejects_negative_exponent(self) -> None:
        """Should reject exponent <= 0."""
        with pytest.raises(ValueError):
            GillerConfig(exponent=-0.5)

    def test_rejects_min_greater_than_max(self) -> None:
        """Should reject min_size > max_size."""
        with pytest.raises(ValueError, match="min_size"):
            GillerConfig(min_size=10.0, max_size=5.0)

    def test_config_is_frozen(self) -> None:
        """Config should be immutable."""
        config = GillerConfig()
        with pytest.raises(Exception):  # Pydantic ValidationError
            config.base_size = 2.0


# =============================================================================
# GillerSizer Tests - CRITICAL for money management
# =============================================================================


class TestGillerSizerBasic:
    """Basic functionality tests for GillerSizer."""

    @pytest.fixture
    def default_sizer(self) -> GillerSizer:
        """Create sizer with default config."""
        return GillerSizer(GillerConfig())

    @pytest.fixture
    def custom_sizer(self) -> GillerSizer:
        """Create sizer with custom config."""
        return GillerSizer(
            GillerConfig(
                base_size=2.0,
                exponent=0.5,
                max_size=10.0,
                min_size=0.2,
            )
        )

    def test_positive_signal(self, default_sizer: GillerSizer) -> None:
        """Positive signal should return positive size."""
        size = default_sizer.calculate(signal=1.0)
        assert size > 0

    def test_negative_signal(self, default_sizer: GillerSizer) -> None:
        """Negative signal should return negative size (SHORT)."""
        size = default_sizer.calculate(signal=-1.0)
        assert size < 0

    def test_zero_signal(self, default_sizer: GillerSizer) -> None:
        """Zero signal should return zero size."""
        size = default_sizer.calculate(signal=0.0)
        assert size == 0.0

    def test_nan_signal(self, default_sizer: GillerSizer) -> None:
        """NaN signal should return zero (safe fallback)."""
        size = default_sizer.calculate(signal=float("nan"))
        assert size == 0.0

    def test_inf_signal(self, default_sizer: GillerSizer) -> None:
        """Infinite signal should return zero (safe fallback)."""
        size = default_sizer.calculate(signal=float("inf"))
        assert size == 0.0

    def test_negative_inf_signal(self, default_sizer: GillerSizer) -> None:
        """Negative infinite signal should return zero."""
        size = default_sizer.calculate(signal=float("-inf"))
        assert size == 0.0


class TestGillerSizerSubLinearScaling:
    """Tests for sub-linear scaling formula."""

    @pytest.fixture
    def sizer(self) -> GillerSizer:
        """Create sizer with sqrt exponent."""
        return GillerSizer(GillerConfig(base_size=1.0, exponent=0.5))

    def test_sqrt_scaling(self, sizer: GillerSizer) -> None:
        """Signal=4 with exponent=0.5 should give sqrt(4)=2."""
        size = sizer.calculate(signal=4.0)
        expected = math.sqrt(4.0) * 1.0  # 2.0
        assert abs(size - expected) < 0.001

    def test_sublinear_growth(self, sizer: GillerSizer) -> None:
        """Doubling signal should NOT double size (sub-linear)."""
        size1 = sizer.calculate(signal=1.0)
        size2 = sizer.calculate(signal=2.0)
        # If linear, size2 would be 2x size1
        # With sqrt, size2 = sqrt(2) * size1 ≈ 1.41 * size1
        assert size2 < 2 * size1

    def test_large_signal_doesnt_explode(self, sizer: GillerSizer) -> None:
        """Very large signal should be bounded by max_size."""
        size = sizer.calculate(signal=1000.0)
        assert size <= sizer.config.max_size


class TestGillerSizerRegimeWeight:
    """Tests for regime weight parameter."""

    @pytest.fixture
    def sizer(self) -> GillerSizer:
        return GillerSizer(GillerConfig(base_size=1.0, min_size=0.0))

    def test_regime_weight_one(self, sizer: GillerSizer) -> None:
        """Regime weight 1.0 should not reduce size."""
        size = sizer.calculate(signal=1.0, regime_weight=1.0)
        assert size > 0

    def test_regime_weight_zero(self, sizer: GillerSizer) -> None:
        """Regime weight 0.0 should give zero size (don't trade)."""
        size = sizer.calculate(signal=1.0, regime_weight=0.0)
        assert size == 0.0

    def test_regime_weight_half(self, sizer: GillerSizer) -> None:
        """Regime weight 0.5 should halve the size."""
        full_size = sizer.calculate(signal=1.0, regime_weight=1.0)
        half_size = sizer.calculate(signal=1.0, regime_weight=0.5)
        assert abs(half_size - full_size * 0.5) < 0.001

    def test_regime_weight_clamped_above(self, sizer: GillerSizer) -> None:
        """Regime weight > 1.0 should be clamped to 1.0."""
        size_clamped = sizer.calculate(signal=1.0, regime_weight=2.0)
        size_max = sizer.calculate(signal=1.0, regime_weight=1.0)
        assert size_clamped == size_max

    def test_regime_weight_clamped_below(self, sizer: GillerSizer) -> None:
        """Regime weight < 0.0 should be clamped to 0.0."""
        size = sizer.calculate(signal=1.0, regime_weight=-0.5)
        assert size == 0.0


class TestGillerSizerToxicity:
    """Tests for VPIN toxicity penalty."""

    @pytest.fixture
    def sizer(self) -> GillerSizer:
        return GillerSizer(GillerConfig(base_size=1.0, min_size=0.0))

    def test_toxicity_zero(self, sizer: GillerSizer) -> None:
        """Toxicity 0.0 should not reduce size."""
        size = sizer.calculate(signal=1.0, toxicity=0.0)
        assert size > 0

    def test_toxicity_one(self, sizer: GillerSizer) -> None:
        """Toxicity 1.0 should give zero size (toxic market)."""
        size = sizer.calculate(signal=1.0, toxicity=1.0)
        assert size == 0.0

    def test_toxicity_half(self, sizer: GillerSizer) -> None:
        """Toxicity 0.5 should halve the size."""
        full_size = sizer.calculate(signal=1.0, toxicity=0.0)
        half_size = sizer.calculate(signal=1.0, toxicity=0.5)
        assert abs(half_size - full_size * 0.5) < 0.001

    def test_toxicity_clamped_above(self, sizer: GillerSizer) -> None:
        """Toxicity > 1.0 should be clamped to 1.0."""
        size = sizer.calculate(signal=1.0, toxicity=1.5)
        assert size == 0.0

    def test_toxicity_clamped_below(self, sizer: GillerSizer) -> None:
        """Toxicity < 0.0 should be clamped to 0.0."""
        size_clamped = sizer.calculate(signal=1.0, toxicity=-0.5)
        size_zero_tox = sizer.calculate(signal=1.0, toxicity=0.0)
        assert size_clamped == size_zero_tox


class TestGillerSizerMinMaxLimits:
    """Tests for min/max size limits - CRITICAL for risk control."""

    def test_min_size_applied(self) -> None:
        """Size below min_size should be clamped UP to min_size."""
        sizer = GillerSizer(GillerConfig(base_size=0.01, min_size=0.5, max_size=10.0))
        size = sizer.calculate(signal=1.0)  # Very small base
        assert abs(size) >= 0.5

    def test_max_size_applied(self) -> None:
        """Size above max_size should be clamped DOWN to max_size."""
        sizer = GillerSizer(GillerConfig(base_size=100.0, min_size=0.1, max_size=5.0))
        size = sizer.calculate(signal=1.0)  # Very large base
        assert abs(size) <= 5.0

    def test_min_size_preserves_sign(self) -> None:
        """Min size clamping should preserve SHORT direction."""
        sizer = GillerSizer(GillerConfig(base_size=0.01, min_size=0.5, max_size=10.0))
        size = sizer.calculate(signal=-1.0)
        assert size < 0
        assert abs(size) >= 0.5

    def test_max_size_preserves_sign(self) -> None:
        """Max size clamping should preserve SHORT direction."""
        sizer = GillerSizer(GillerConfig(base_size=100.0, min_size=0.1, max_size=5.0))
        size = sizer.calculate(signal=-1.0)
        assert size < 0
        assert abs(size) <= 5.0

    def test_zero_takes_precedence_over_min(self) -> None:
        """If regime=0 or toxicity=1, return 0 not min_size."""
        sizer = GillerSizer(GillerConfig(base_size=1.0, min_size=0.5))
        size = sizer.calculate(signal=1.0, regime_weight=0.0)
        assert size == 0.0  # NOT min_size


class TestGillerSizerCombinedFactors:
    """Tests for combined regime + toxicity."""

    @pytest.fixture
    def sizer(self) -> GillerSizer:
        return GillerSizer(GillerConfig(base_size=1.0, min_size=0.0))

    def test_combined_factors(self, sizer: GillerSizer) -> None:
        """Combined regime and toxicity should multiply."""
        full = sizer.calculate(signal=1.0)
        combined = sizer.calculate(signal=1.0, regime_weight=0.5, toxicity=0.5)
        # Expected: full * 0.5 * (1 - 0.5) = full * 0.25
        expected = full * 0.5 * 0.5
        assert abs(combined - expected) < 0.001


# =============================================================================
# IntegratedSizingConfig Tests
# =============================================================================


class TestIntegratedSizingConfigValidation:
    """Tests for IntegratedSizingConfig Pydantic validation."""

    def test_default_config(self) -> None:
        """Default config should have sensible values."""
        config = IntegratedSizingConfig()
        assert config.giller_exponent == 0.5
        assert config.fractional_kelly == 0.5
        assert config.min_size == 0.01
        assert config.max_size == 1.0

    def test_rejects_min_greater_than_max(self) -> None:
        """Should reject min_size > max_size."""
        with pytest.raises(ValueError, match="min_size"):
            IntegratedSizingConfig(min_size=5.0, max_size=1.0)

    def test_rejects_kelly_above_one(self) -> None:
        """Should reject fractional_kelly > 1.0."""
        with pytest.raises(ValueError):
            IntegratedSizingConfig(fractional_kelly=1.5)

    def test_default_meta_confidence(self) -> None:
        """Should have default meta confidence of 0.5."""
        config = IntegratedSizingConfig()
        assert config.default_meta_confidence == 0.5

    def test_default_regime_weight(self) -> None:
        """Should have default regime weight of 0.8."""
        config = IntegratedSizingConfig()
        assert config.default_regime_weight == 0.8


# =============================================================================
# IntegratedSizer Tests
# =============================================================================


class TestIntegratedSizerBasic:
    """Basic functionality tests for IntegratedSizer."""

    @pytest.fixture
    def sizer(self) -> IntegratedSizer:
        return IntegratedSizer(IntegratedSizingConfig())

    def test_positive_signal(self, sizer: IntegratedSizer) -> None:
        """Positive signal should return positive size."""
        result = sizer.calculate(signal=1.0)
        assert result.size > 0
        assert result.direction == 1

    def test_negative_signal(self, sizer: IntegratedSizer) -> None:
        """Negative signal should return negative size (SHORT)."""
        result = sizer.calculate(signal=-1.0)
        assert result.size < 0
        assert result.direction == -1

    def test_zero_signal(self, sizer: IntegratedSizer) -> None:
        """Zero signal should return zero size."""
        result = sizer.calculate(signal=0.0)
        assert result.size == 0.0
        assert result.direction == 0

    def test_returns_factor_breakdown(self, sizer: IntegratedSizer) -> None:
        """Should return breakdown of all factors."""
        result = sizer.calculate(signal=1.0)
        assert "signal_factor" in result.factor_breakdown
        assert "meta_confidence" in result.factor_breakdown
        assert "regime_weight" in result.factor_breakdown
        assert "toxicity_penalty" in result.factor_breakdown
        assert "kelly_fraction" in result.factor_breakdown


class TestIntegratedSizerWithMetaConfidence:
    """Tests for meta-confidence integration."""

    @pytest.fixture
    def sizer(self) -> IntegratedSizer:
        return IntegratedSizer(IntegratedSizingConfig(min_size=0.0))

    def test_high_confidence_larger_size(self, sizer: IntegratedSizer) -> None:
        """High meta confidence should give larger size."""
        low = sizer.calculate(signal=1.0, meta_confidence=0.3)
        high = sizer.calculate(signal=1.0, meta_confidence=0.9)
        assert high.size > low.size

    def test_zero_confidence_zero_size(self, sizer: IntegratedSizer) -> None:
        """Zero meta confidence should give zero size."""
        result = sizer.calculate(signal=1.0, meta_confidence=0.0)
        assert result.size == 0.0

    def test_uses_default_when_none(self, sizer: IntegratedSizer) -> None:
        """Should use default meta confidence when None provided."""
        result = sizer.calculate(signal=1.0, meta_confidence=None)
        assert result.factor_breakdown["meta_confidence"] == 0.5  # default


class TestIntegratedSizerMaxSize:
    """Tests for max size clamping - CRITICAL safety check."""

    def test_max_size_enforced(self) -> None:
        """Size should never exceed max_size."""
        sizer = IntegratedSizer(IntegratedSizingConfig(max_size=0.5, fractional_kelly=1.0))
        # Use very high signal to try to exceed max
        result = sizer.calculate(signal=100.0, meta_confidence=1.0, regime_weight=1.0)
        assert abs(result.size) <= 0.5

    def test_direction_reset_on_clamp(self) -> None:
        """Direction should be reset to 0 if size is clamped to 0."""
        sizer = IntegratedSizer(IntegratedSizingConfig(min_size=0.5, max_size=1.0))
        # Toxicity 1.0 should make size 0, not min_size
        result = sizer.calculate(signal=1.0, toxicity=1.0)
        assert result.size == 0.0
        assert result.direction == 0
