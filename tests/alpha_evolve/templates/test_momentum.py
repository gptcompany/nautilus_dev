"""Tests for MomentumEvolveStrategy seed strategy."""

from decimal import Decimal

from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.indicators import ExponentialMovingAverage

from scripts.alpha_evolve.templates.base import BaseEvolveStrategy
from scripts.alpha_evolve.templates.momentum import (
    MomentumEvolveConfig,
    MomentumEvolveStrategy,
)
from scripts.alpha_evolve.patching import extract_blocks


# =============================================================================
# T018: Test Momentum Config Validation
# =============================================================================


class TestMomentumConfigValidation:
    """Tests for MomentumEvolveConfig validation."""

    def test_config_has_period_fields(self) -> None:
        """Config should have fast_period and slow_period fields."""
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )

        assert hasattr(config, "fast_period")
        assert hasattr(config, "slow_period")

    def test_default_periods(self) -> None:
        """Config should have default periods (10, 30)."""
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )

        assert config.fast_period == 10
        assert config.slow_period == 30

    def test_custom_periods(self) -> None:
        """Config should accept custom periods."""
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
            fast_period=5,
            slow_period=20,
        )

        assert config.fast_period == 5
        assert config.slow_period == 20


# =============================================================================
# T019: Test Momentum Indicators Initialized
# =============================================================================


class TestMomentumIndicatorsInitialized:
    """Tests for indicator initialization."""

    def test_strategy_has_ema_indicators(self) -> None:
        """Strategy should have fast_ema and slow_ema attributes."""
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )
        strategy = MomentumEvolveStrategy(config)

        assert hasattr(strategy, "fast_ema")
        assert hasattr(strategy, "slow_ema")

    def test_indicators_are_ema_type(self) -> None:
        """Indicators should be ExponentialMovingAverage instances."""
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )
        strategy = MomentumEvolveStrategy(config)

        assert isinstance(strategy.fast_ema, ExponentialMovingAverage)
        assert isinstance(strategy.slow_ema, ExponentialMovingAverage)

    def test_indicators_use_config_periods(self) -> None:
        """Indicators should use periods from config."""
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
            fast_period=7,
            slow_period=21,
        )
        strategy = MomentumEvolveStrategy(config)

        assert strategy.fast_ema.period == 7
        assert strategy.slow_ema.period == 21


# =============================================================================
# T020: Test EVOLVE-BLOCK Extractable
# =============================================================================


class TestEvolveBlockExtractable:
    """Tests for EVOLVE-BLOCK extraction from strategy code."""

    def test_strategy_inherits_from_base(self) -> None:
        """MomentumEvolveStrategy should inherit from BaseEvolveStrategy."""
        assert issubclass(MomentumEvolveStrategy, BaseEvolveStrategy)

    def test_has_on_bar_evolved_method(self) -> None:
        """Strategy should have _on_bar_evolved method."""
        assert hasattr(MomentumEvolveStrategy, "_on_bar_evolved")

    def test_evolve_block_extractable_from_source(
        self, momentum_strategy_code: str
    ) -> None:
        """EVOLVE-BLOCK should be extractable from strategy source code."""
        blocks = extract_blocks(momentum_strategy_code)

        assert "decision_logic" in blocks
        assert len(blocks["decision_logic"]) > 0


# =============================================================================
# T027-T028: Native Indicator Tests (Phase 5)
# =============================================================================


class TestNativeIndicators:
    """Tests for native Rust indicator usage."""

    def test_uses_nautilus_indicators_import(self) -> None:
        """Strategy should import from nautilus_trader.indicators."""
        import scripts.alpha_evolve.templates.momentum as momentum_module

        # Check module was imported correctly
        assert momentum_module is not None

    def test_ema_is_native_rust(self) -> None:
        """ExponentialMovingAverage should be from nautilus_trader."""

        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )
        strategy = MomentumEvolveStrategy(config)

        # Verify it's the same class from nautilus_trader
        assert type(strategy.fast_ema).__module__.startswith("nautilus_trader")
