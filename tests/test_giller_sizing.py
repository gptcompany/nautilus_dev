"""Tests for Giller sub-linear position sizing.

Tests cover:
- Sub-linear (sqrt) scaling
- Regime weight application
- Edge cases (zero, negative)
- Min/max limits
"""

from __future__ import annotations

import pytest

from strategies.common.position_sizing.config import GillerConfig
from strategies.common.position_sizing.giller_sizing import GillerSizer


@pytest.fixture
def default_config() -> GillerConfig:
    """Default Giller configuration."""
    return GillerConfig(
        base_size=1.0,
        exponent=0.5,
        max_size=5.0,
        min_size=0.1,
    )


@pytest.fixture
def giller_sizer(default_config: GillerConfig) -> GillerSizer:
    """Default Giller sizer instance."""
    return GillerSizer(config=default_config)


class TestGillerSqrtScaling:
    """Tests for sub-linear sqrt scaling."""

    def test_giller_sqrt_scaling_basic(self, giller_sizer: GillerSizer) -> None:
        """Test that signal magnitude 4.0 produces size 2.0 (sqrt scaling)."""
        # signal=4.0, exponent=0.5 -> sqrt(4) = 2.0
        size = giller_sizer.calculate(signal=4.0)
        assert size == pytest.approx(2.0, rel=0.01)

    def test_giller_sqrt_scaling_signal_1(self, giller_sizer: GillerSizer) -> None:
        """Test that signal 1.0 produces size 1.0."""
        size = giller_sizer.calculate(signal=1.0)
        assert size == pytest.approx(1.0, rel=0.01)

    def test_giller_sqrt_scaling_signal_9(self, giller_sizer: GillerSizer) -> None:
        """Test that signal 9.0 produces size 3.0."""
        size = giller_sizer.calculate(signal=9.0)
        assert size == pytest.approx(3.0, rel=0.01)

    def test_giller_sqrt_scaling_negative_signal(
        self, giller_sizer: GillerSizer
    ) -> None:
        """Test that negative signals produce negative sizes (same magnitude)."""
        size = giller_sizer.calculate(signal=-4.0)
        assert size == pytest.approx(-2.0, rel=0.01)

    def test_giller_preserves_sign(self, giller_sizer: GillerSizer) -> None:
        """Test that sign is preserved after sqrt transformation."""
        pos_size = giller_sizer.calculate(signal=4.0)
        neg_size = giller_sizer.calculate(signal=-4.0)

        assert pos_size > 0
        assert neg_size < 0
        assert abs(pos_size) == pytest.approx(abs(neg_size), rel=0.01)


class TestGillerRegimeWeight:
    """Tests for regime weight application."""

    def test_giller_with_regime_weight(self, giller_sizer: GillerSizer) -> None:
        """Test that regime weight scales the position size."""
        # signal=4.0 -> sqrt(4) = 2.0, then * 0.5 regime weight = 1.0
        size = giller_sizer.calculate(signal=4.0, regime_weight=0.5)
        assert size == pytest.approx(1.0, rel=0.01)

    def test_giller_with_full_regime_weight(self, giller_sizer: GillerSizer) -> None:
        """Test that regime weight 1.0 has no effect."""
        size_no_weight = giller_sizer.calculate(signal=4.0)
        size_full_weight = giller_sizer.calculate(signal=4.0, regime_weight=1.0)

        assert size_no_weight == pytest.approx(size_full_weight, rel=0.01)

    def test_giller_with_zero_regime_weight(self, giller_sizer: GillerSizer) -> None:
        """Test that regime weight 0.0 produces minimum size."""
        # Regime weight 0 should still produce min_size (not zero)
        size = giller_sizer.calculate(signal=4.0, regime_weight=0.0)
        assert abs(size) == pytest.approx(0.1, rel=0.01)  # min_size


class TestGillerToxicity:
    """Tests for toxicity penalty application."""

    def test_giller_with_toxicity_penalty(self, giller_sizer: GillerSizer) -> None:
        """Test that toxicity reduces position size."""
        # signal=4.0 -> 2.0, then * (1 - 0.5 toxicity) = 1.0
        size = giller_sizer.calculate(signal=4.0, toxicity=0.5)
        assert size == pytest.approx(1.0, rel=0.01)

    def test_giller_with_high_toxicity(self, giller_sizer: GillerSizer) -> None:
        """Test that high toxicity (>0.7) significantly reduces size."""
        size = giller_sizer.calculate(signal=4.0, toxicity=0.9)
        # signal=4.0 -> sqrt(4) = 2.0, then * (1 - 0.9) = 2.0 * 0.1 = 0.2
        assert abs(size) == pytest.approx(0.2, rel=0.01)


class TestGillerEdgeCases:
    """Tests for edge cases."""

    def test_giller_edge_cases_zero_signal(self, giller_sizer: GillerSizer) -> None:
        """Test that zero signal produces zero size."""
        size = giller_sizer.calculate(signal=0.0)
        assert size == 0.0

    def test_giller_edge_cases_very_small_signal(
        self, giller_sizer: GillerSizer
    ) -> None:
        """Test that very small signals produce minimum size."""
        size = giller_sizer.calculate(signal=0.001)
        # sqrt(0.001) = 0.0316..., below min_size
        assert abs(size) == pytest.approx(0.1, rel=0.01)  # clamped to min_size

    def test_giller_edge_cases_negative_signal(self, giller_sizer: GillerSizer) -> None:
        """Test that negative signals work correctly."""
        size = giller_sizer.calculate(signal=-1.0)
        assert size == pytest.approx(-1.0, rel=0.01)


class TestGillerMinMaxLimits:
    """Tests for min/max size limits."""

    def test_giller_respects_max_limit(self, giller_sizer: GillerSizer) -> None:
        """Test that large signals are clamped to max_size."""
        # signal=100.0 -> sqrt(100) = 10.0, clamped to max_size=5.0
        size = giller_sizer.calculate(signal=100.0)
        assert size == pytest.approx(5.0, rel=0.01)

    def test_giller_respects_min_limit(self, giller_sizer: GillerSizer) -> None:
        """Test that small signals are clamped to min_size."""
        # signal=0.001 -> sqrt(0.001) ≈ 0.0316, clamped to min_size=0.1
        size = giller_sizer.calculate(signal=0.001)
        assert size == pytest.approx(0.1, rel=0.01)

    def test_giller_negative_respects_max_limit(
        self, giller_sizer: GillerSizer
    ) -> None:
        """Test that large negative signals are clamped to -max_size."""
        size = giller_sizer.calculate(signal=-100.0)
        assert size == pytest.approx(-5.0, rel=0.01)

    def test_giller_negative_respects_min_limit(
        self, giller_sizer: GillerSizer
    ) -> None:
        """Test that small negative signals are clamped to -min_size."""
        size = giller_sizer.calculate(signal=-0.001)
        assert size == pytest.approx(-0.1, rel=0.01)


class TestGillerConfig:
    """Tests for different configurations."""

    def test_giller_custom_exponent(self) -> None:
        """Test with custom exponent (0.25 = fourth root)."""
        config = GillerConfig(base_size=1.0, exponent=0.25, max_size=10.0, min_size=0.1)
        sizer = GillerSizer(config=config)

        # signal=16.0, exponent=0.25 -> 16^0.25 = 2.0
        size = sizer.calculate(signal=16.0)
        assert size == pytest.approx(2.0, rel=0.01)

    def test_giller_base_size_multiplier(self) -> None:
        """Test that base_size acts as a multiplier."""
        config = GillerConfig(base_size=2.0, exponent=0.5, max_size=20.0, min_size=0.1)
        sizer = GillerSizer(config=config)

        # signal=4.0 -> sqrt(4) = 2.0, * base_size=2.0 = 4.0
        size = sizer.calculate(signal=4.0)
        assert size == pytest.approx(4.0, rel=0.01)
