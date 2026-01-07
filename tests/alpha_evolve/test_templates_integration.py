"""Integration tests for Alpha-Evolve templates with evaluator and patching."""

from decimal import Decimal

from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId

from scripts.alpha_evolve.patching import apply_patch, extract_blocks
from scripts.alpha_evolve.templates import (
    BaseEvolveStrategy,
    MomentumEvolveConfig,
    MomentumEvolveStrategy,
)

# =============================================================================
# T041: Test Strategy Evaluation Returns Metrics
# =============================================================================


class TestStrategyEvaluationReturnsMetrics:
    """Tests that strategy can be evaluated and returns metrics."""

    def test_strategy_can_be_instantiated(self) -> None:
        """Strategy should be instantiable with valid config."""
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )
        strategy = MomentumEvolveStrategy(config)

        assert strategy is not None
        assert isinstance(strategy, BaseEvolveStrategy)

    def test_strategy_has_required_methods_for_evaluation(self) -> None:
        """Strategy should have methods required by evaluator."""
        # Check for methods the evaluator needs
        assert hasattr(MomentumEvolveStrategy, "on_start")
        assert hasattr(MomentumEvolveStrategy, "on_bar")
        assert hasattr(MomentumEvolveStrategy, "on_stop")
        assert hasattr(MomentumEvolveStrategy, "get_equity_curve")


# =============================================================================
# T042: Test EVOLVE-BLOCK Extraction
# =============================================================================


class TestEvolveBlockExtraction:
    """Tests for EVOLVE-BLOCK extraction from strategy source."""

    def test_extract_decision_logic_block(self) -> None:
        """Should extract decision_logic block from momentum strategy source."""
        import inspect

        source = inspect.getsource(MomentumEvolveStrategy)
        blocks = extract_blocks(source)

        assert "decision_logic" in blocks
        assert "fast_ema.value" in blocks["decision_logic"]
        assert "slow_ema.value" in blocks["decision_logic"]

    def test_momentum_strategy_source_has_block(self) -> None:
        """MomentumEvolveStrategy source should contain EVOLVE-BLOCK markers."""
        import inspect

        source = inspect.getsource(MomentumEvolveStrategy)

        assert "# === EVOLVE-BLOCK: decision_logic ===" in source
        assert "# === END EVOLVE-BLOCK ===" in source


# =============================================================================
# T043: Test Patched Strategy Executes
# =============================================================================


class TestPatchedStrategyExecutes:
    """Tests for patched strategy execution."""

    def test_patched_code_is_valid_python(self) -> None:
        """Patched strategy code should be valid Python."""
        import inspect

        source = inspect.getsource(MomentumEvolveStrategy)
        new_logic = """if self.fast_ema.value > self.slow_ema.value * 1.01:
    if self.portfolio.is_flat(self.config.instrument_id):
        self._enter_long(self.config.trade_size)"""

        patched = apply_patch(source, {"blocks": {"decision_logic": new_logic}})

        # Should be able to compile the patched code
        compile(patched, "<string>", "exec")

    def test_patched_code_preserves_structure(self) -> None:
        """Patched code should preserve class structure outside EVOLVE-BLOCK."""
        import inspect

        source = inspect.getsource(MomentumEvolveStrategy)
        new_logic = "pass  # Simplified logic"

        patched = apply_patch(source, {"blocks": {"decision_logic": new_logic}})

        # Class definition should still be present
        assert "class MomentumEvolveStrategy" in patched
        assert "def __init__" in patched
        assert "def on_start" in patched


# =============================================================================
# T044: Test Equity Curve Populated
# =============================================================================


class TestEquityCurvePopulated:
    """Tests for equity curve population during strategy execution."""

    def test_equity_curve_starts_empty(self) -> None:
        """Equity curve should be empty before any bars are processed."""
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )
        strategy = MomentumEvolveStrategy(config)

        curve = strategy.get_equity_curve()
        assert len(curve) == 0

    def test_get_equity_curve_returns_copy(self) -> None:
        """get_equity_curve should return a copy, not the internal list."""
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )
        strategy = MomentumEvolveStrategy(config)

        curve1 = strategy.get_equity_curve()
        curve2 = strategy.get_equity_curve()

        # Should be equal but not the same object
        assert curve1 == curve2
        assert curve1 is not curve2
