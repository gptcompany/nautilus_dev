"""Unit tests for contender sizers.

Tests for:
    - FixedFractionalSizer
    - BuyAndHoldSizer
    - AdaptiveSizer
    - create_sizer factory

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations


import pytest

from scripts.baseline_validation.sizers import (
    AdaptiveSizer,
    BuyAndHoldSizer,
    ContenderSizer,
    FixedFractionalSizer,
    SizerState,
    create_sizer,
)


class TestFixedFractionalSizer:
    """Tests for FixedFractionalSizer."""

    def test_init_valid_params(self) -> None:
        """Test valid initialization."""
        sizer = FixedFractionalSizer(risk_pct=0.02, max_positions=10)
        assert sizer.name == "Fixed 2%"

    def test_init_invalid_risk_pct_zero(self) -> None:
        """Test rejection of zero risk_pct."""
        with pytest.raises(ValueError, match="risk_pct must be in"):
            FixedFractionalSizer(risk_pct=0)

    def test_init_invalid_risk_pct_negative(self) -> None:
        """Test rejection of negative risk_pct."""
        with pytest.raises(ValueError, match="risk_pct must be in"):
            FixedFractionalSizer(risk_pct=-0.02)

    def test_init_invalid_risk_pct_too_high(self) -> None:
        """Test rejection of risk_pct > 1."""
        with pytest.raises(ValueError, match="risk_pct must be in"):
            FixedFractionalSizer(risk_pct=1.5)

    def test_init_invalid_max_positions(self) -> None:
        """Test rejection of invalid max_positions."""
        with pytest.raises(ValueError, match="max_positions must be"):
            FixedFractionalSizer(risk_pct=0.02, max_positions=0)

    def test_calculate_positive_signal(self) -> None:
        """Test position sizing with positive signal."""
        sizer = FixedFractionalSizer(risk_pct=0.02)

        # $10,000 equity, 2% risk = $200 risk
        # Entry $100, Stop $95 = $5 risk per unit
        # Position = $200 / $5 = 40 units
        position = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        assert position == pytest.approx(40.0)

    def test_calculate_negative_signal(self) -> None:
        """Test position sizing with negative signal (short)."""
        sizer = FixedFractionalSizer(risk_pct=0.02)

        position = sizer.calculate(
            signal=-1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=105.0,  # Stop above for short
        )

        assert position == pytest.approx(-40.0)

    def test_calculate_zero_signal(self) -> None:
        """Test no position with zero signal."""
        sizer = FixedFractionalSizer(risk_pct=0.02)

        position = sizer.calculate(
            signal=0.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        assert position == 0.0

    def test_calculate_zero_equity(self) -> None:
        """Test no position with zero equity."""
        sizer = FixedFractionalSizer(risk_pct=0.02)

        position = sizer.calculate(
            signal=1.0,
            equity=0.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        assert position == 0.0

    def test_calculate_zero_stop_distance(self) -> None:
        """Test fallback when stop loss at entry."""
        sizer = FixedFractionalSizer(risk_pct=0.02)

        position = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=100.0,  # Same as entry
        )

        # Should use fixed fraction of equity / price
        # $200 risk / $100 = 2 units
        assert position == pytest.approx(2.0)

    def test_update_is_noop(self) -> None:
        """Test that update does nothing for fixed sizer."""
        sizer = FixedFractionalSizer(risk_pct=0.02)
        # Should not raise
        sizer.update(return_value=0.05, timestamp=1234567890.0)

    def test_get_state(self) -> None:
        """Test state retrieval."""
        sizer = FixedFractionalSizer(risk_pct=0.02, max_positions=10)
        state = sizer.get_state(signal=0.5)

        assert isinstance(state, SizerState)
        assert state.name == "Fixed 2%"
        assert state.signal == 0.5
        assert state.parameters["risk_pct"] == 0.02
        assert state.parameters["max_positions"] == 10.0

    def test_implements_protocol(self) -> None:
        """Test that FixedFractionalSizer implements ContenderSizer protocol."""
        sizer = FixedFractionalSizer(risk_pct=0.02)
        assert isinstance(sizer, ContenderSizer)


class TestBuyAndHoldSizer:
    """Tests for BuyAndHoldSizer."""

    def test_init_valid_params(self) -> None:
        """Test valid initialization."""
        sizer = BuyAndHoldSizer(allocation_pct=1.0)
        assert sizer.name == "Buy & Hold"

    def test_init_invalid_allocation_zero(self) -> None:
        """Test rejection of zero allocation."""
        with pytest.raises(ValueError, match="allocation_pct must be in"):
            BuyAndHoldSizer(allocation_pct=0)

    def test_init_invalid_allocation_too_high(self) -> None:
        """Test rejection of allocation > 1."""
        with pytest.raises(ValueError, match="allocation_pct must be in"):
            BuyAndHoldSizer(allocation_pct=1.5)

    def test_calculate_first_call(self) -> None:
        """Test first position calculation."""
        sizer = BuyAndHoldSizer(allocation_pct=1.0)

        # $10,000 equity / $100 price = 100 units
        position = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,  # Ignored for B&H
        )

        assert position == pytest.approx(100.0)

    def test_calculate_no_rebalancing(self) -> None:
        """Test that subsequent calls return zero (no rebalancing)."""
        sizer = BuyAndHoldSizer(allocation_pct=1.0)

        # First call - takes position
        position1 = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        # Second call - no rebalancing
        position2 = sizer.calculate(
            signal=1.0,
            equity=12_000.0,  # Equity increased
            entry_price=120.0,  # Price increased
            stop_loss_price=114.0,
        )

        assert position1 == pytest.approx(100.0)
        assert position2 == 0.0

    def test_calculate_ignores_signal(self) -> None:
        """Test that signal direction is ignored (always long)."""
        sizer = BuyAndHoldSizer(allocation_pct=1.0)

        position = sizer.calculate(
            signal=-1.0,  # Negative signal
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        # Should still be positive (long only)
        assert position == pytest.approx(100.0)

    def test_reset(self) -> None:
        """Test reset allows new position."""
        sizer = BuyAndHoldSizer(allocation_pct=1.0)

        # First position
        position1 = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        # Reset
        sizer.reset()

        # Should allow new position
        position2 = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        assert position1 == pytest.approx(100.0)
        assert position2 == pytest.approx(100.0)

    def test_calculate_partial_allocation(self) -> None:
        """Test partial allocation."""
        sizer = BuyAndHoldSizer(allocation_pct=0.5)  # 50% allocation

        position = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        # $5,000 / $100 = 50 units
        assert position == pytest.approx(50.0)

    def test_implements_protocol(self) -> None:
        """Test that BuyAndHoldSizer implements ContenderSizer protocol."""
        sizer = BuyAndHoldSizer()
        assert isinstance(sizer, ContenderSizer)


class TestAdaptiveSizer:
    """Tests for AdaptiveSizer."""

    def test_init_default_params(self) -> None:
        """Test default initialization."""
        sizer = AdaptiveSizer()
        assert sizer.name == "SOPS+Giller+Thompson"

    def test_init_custom_params(self) -> None:
        """Test custom initialization."""
        sizer = AdaptiveSizer(
            sops_k_base=2.0,
            giller_exponent=0.6,
            thompson_decay=0.95,
            max_position_pct=0.15,
        )
        assert sizer.name == "SOPS+Giller+Thompson"

    def test_calculate_positive_signal(self) -> None:
        """Test position sizing with positive signal."""
        sizer = AdaptiveSizer(max_position_pct=0.10)

        position = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        # Should be positive and within max position
        assert position > 0
        max_position = 10_000.0 * 0.10 / 100.0  # 10 units
        assert abs(position) <= max_position * 2  # Allow some Thompson multiplier

    def test_calculate_negative_signal(self) -> None:
        """Test position sizing with negative signal."""
        sizer = AdaptiveSizer(max_position_pct=0.10)

        position = sizer.calculate(
            signal=-1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=105.0,
        )

        # Should be negative (short position)
        assert position < 0

    def test_calculate_zero_signal(self) -> None:
        """Test no position with zero signal."""
        sizer = AdaptiveSizer()

        position = sizer.calculate(
            signal=0.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        assert position == 0.0

    def test_update_changes_state(self) -> None:
        """Test that update affects internal state."""
        sizer = AdaptiveSizer()

        # Warm up with returns
        for i in range(20):
            sizer.update(
                return_value=0.01 * (1 if i % 2 == 0 else -1),
                timestamp=float(i),
            )

        state = sizer.get_state(signal=1.0)

        # Should have non-default volatility
        assert state.parameters["volatility"] > 0

    def test_signal_dampening(self) -> None:
        """Test that large signals are dampened (Giller power law)."""
        sizer = AdaptiveSizer(max_position_pct=0.10)

        # Small signal
        position_small = sizer.calculate(
            signal=0.1,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        # Large signal (10x)
        position_large = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )

        # Due to Giller scaling, 10x signal should NOT give 10x position
        # sqrt(10) ~ 3.16x
        if position_small > 0:
            ratio = position_large / position_small
            assert ratio < 10  # Should be dampened

    def test_implements_protocol(self) -> None:
        """Test that AdaptiveSizer implements ContenderSizer protocol."""
        sizer = AdaptiveSizer()
        assert isinstance(sizer, ContenderSizer)


class TestCreateSizer:
    """Tests for create_sizer factory function."""

    def test_create_adaptive(self) -> None:
        """Test creating adaptive sizer."""
        sizer = create_sizer("adaptive")
        assert isinstance(sizer, AdaptiveSizer)
        assert sizer.name == "SOPS+Giller+Thompson"

    def test_create_fixed(self) -> None:
        """Test creating fixed sizer."""
        sizer = create_sizer("fixed")
        assert isinstance(sizer, FixedFractionalSizer)
        assert "Fixed" in sizer.name

    def test_create_buyhold(self) -> None:
        """Test creating buy and hold sizer."""
        sizer = create_sizer("buyhold")
        assert isinstance(sizer, BuyAndHoldSizer)
        assert sizer.name == "Buy & Hold"

    def test_create_with_config(self) -> None:
        """Test creating sizer with custom config."""
        sizer = create_sizer("fixed", {"risk_pct": 0.03})
        assert isinstance(sizer, FixedFractionalSizer)
        assert "Fixed 3%" in sizer.name

    def test_create_unknown_type(self) -> None:
        """Test error on unknown type."""
        with pytest.raises(ValueError, match="Unknown contender_type"):
            create_sizer("unknown")


class TestSizerEdgeCases:
    """Test edge cases across all sizers."""

    @pytest.mark.parametrize(
        "sizer_factory",
        [
            lambda: FixedFractionalSizer(risk_pct=0.02),
            lambda: BuyAndHoldSizer(),
            lambda: AdaptiveSizer(),
        ],
    )
    def test_negative_equity(self, sizer_factory) -> None:
        """Test behavior with negative equity."""
        sizer = sizer_factory()
        position = sizer.calculate(
            signal=1.0,
            equity=-10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )
        assert position == 0.0

    @pytest.mark.parametrize(
        "sizer_factory",
        [
            lambda: FixedFractionalSizer(risk_pct=0.02),
            lambda: BuyAndHoldSizer(),
            lambda: AdaptiveSizer(),
        ],
    )
    def test_negative_entry_price(self, sizer_factory) -> None:
        """Test behavior with negative entry price."""
        sizer = sizer_factory()
        position = sizer.calculate(
            signal=1.0,
            equity=10_000.0,
            entry_price=-100.0,
            stop_loss_price=-105.0,
        )
        assert position == 0.0

    @pytest.mark.parametrize(
        "sizer_factory",
        [
            lambda: FixedFractionalSizer(risk_pct=0.02),
            lambda: BuyAndHoldSizer(),
            lambda: AdaptiveSizer(),
        ],
    )
    def test_very_small_signal(self, sizer_factory) -> None:
        """Test behavior with very small signal."""
        sizer = sizer_factory()

        # Reset BuyAndHold if applicable
        if hasattr(sizer, "reset"):
            sizer.reset()

        position = sizer.calculate(
            signal=1e-15,  # Very small but non-zero
            equity=10_000.0,
            entry_price=100.0,
            stop_loss_price=95.0,
        )
        # For FixedFractional and Adaptive, very small signal should give zero
        # For BuyAndHold, signal is ignored
        if isinstance(sizer, BuyAndHoldSizer):
            assert position > 0  # B&H ignores signal magnitude
        else:
            assert position == 0.0
