"""Tests for BaseEvolveStrategy base class."""

import pytest
from decimal import Decimal

from nautilus_trader.trading.strategy import Strategy

from scripts.alpha_evolve.templates.base import (
    BaseEvolveConfig,
    BaseEvolveStrategy,
    EquityPoint,
)


# =============================================================================
# T007: Test Base Strategy Inheritance
# =============================================================================


class TestBaseStrategyInheritance:
    """Tests for BaseEvolveStrategy inheritance from NautilusTrader Strategy."""

    def test_inherits_from_strategy(self) -> None:
        """BaseEvolveStrategy should inherit from nautilus_trader Strategy."""
        assert issubclass(BaseEvolveStrategy, Strategy)

    def test_is_abstract_class(self) -> None:
        """BaseEvolveStrategy should be abstract (cannot be instantiated directly)."""
        from nautilus_trader.model.data import BarType
        from nautilus_trader.model.identifiers import InstrumentId

        config = BaseEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )

        with pytest.raises(TypeError, match="abstract"):
            BaseEvolveStrategy(config)

    def test_config_has_required_fields(self) -> None:
        """BaseEvolveConfig should have instrument_id, bar_type, trade_size."""
        from nautilus_trader.model.data import BarType
        from nautilus_trader.model.identifiers import InstrumentId

        config = BaseEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
        )

        assert hasattr(config, "instrument_id")
        assert hasattr(config, "bar_type")
        assert hasattr(config, "trade_size")


# =============================================================================
# T008: Test Equity Curve Tracking
# =============================================================================


class TestEquityCurveTracking:
    """Tests for equity curve tracking functionality."""

    def test_equity_point_creation(self) -> None:
        """EquityPoint should be a frozen dataclass with timestamp and equity."""
        from datetime import datetime

        point = EquityPoint(timestamp=datetime.now(), equity=100000.0)

        assert hasattr(point, "timestamp")
        assert hasattr(point, "equity")
        assert point.equity == 100000.0

    def test_equity_point_is_immutable(self) -> None:
        """EquityPoint should be frozen (immutable)."""
        from datetime import datetime

        point = EquityPoint(timestamp=datetime.now(), equity=100000.0)

        with pytest.raises(AttributeError):
            point.equity = 200000.0

    def test_get_equity_curve_returns_list(self) -> None:
        """get_equity_curve() should return a list of EquityPoint."""
        # This requires a concrete implementation to test fully
        # For now, just verify the method signature exists
        assert hasattr(BaseEvolveStrategy, "get_equity_curve")

    def test_equity_curve_starts_empty(self) -> None:
        """Equity curve should be empty on initialization."""
        # Need concrete strategy for this test
        assert hasattr(BaseEvolveStrategy, "_equity_curve")


# =============================================================================
# T009: Test Lifecycle Methods
# =============================================================================


class TestLifecycleMethods:
    """Tests for strategy lifecycle management."""

    def test_has_on_start_method(self) -> None:
        """BaseEvolveStrategy should have on_start method."""
        assert hasattr(BaseEvolveStrategy, "on_start")

    def test_has_on_bar_method(self) -> None:
        """BaseEvolveStrategy should have on_bar method."""
        assert hasattr(BaseEvolveStrategy, "on_bar")

    def test_has_on_stop_method(self) -> None:
        """BaseEvolveStrategy should have on_stop method."""
        assert hasattr(BaseEvolveStrategy, "on_stop")

    def test_has_on_reset_method(self) -> None:
        """BaseEvolveStrategy should have on_reset method."""
        assert hasattr(BaseEvolveStrategy, "on_reset")

    def test_has_abstract_on_bar_evolved_method(self) -> None:
        """BaseEvolveStrategy should have abstract _on_bar_evolved method."""

        # Check that _on_bar_evolved is abstract
        assert hasattr(BaseEvolveStrategy, "_on_bar_evolved")
        method = getattr(BaseEvolveStrategy, "_on_bar_evolved")
        assert getattr(method, "__isabstractmethod__", False)


# =============================================================================
# T032-T035: Order Helper Tests (Phase 6 - implemented early as part of base)
# =============================================================================


class TestOrderHelpers:
    """Tests for order helper methods."""

    def test_has_enter_long_method(self) -> None:
        """BaseEvolveStrategy should have _enter_long method."""
        assert hasattr(BaseEvolveStrategy, "_enter_long")

    def test_has_enter_short_method(self) -> None:
        """BaseEvolveStrategy should have _enter_short method."""
        assert hasattr(BaseEvolveStrategy, "_enter_short")

    def test_has_close_position_method(self) -> None:
        """BaseEvolveStrategy should have _close_position method."""
        assert hasattr(BaseEvolveStrategy, "_close_position")

    def test_has_get_position_size_method(self) -> None:
        """BaseEvolveStrategy should have _get_position_size method."""
        assert hasattr(BaseEvolveStrategy, "_get_position_size")

    def test_has_get_equity_method(self) -> None:
        """BaseEvolveStrategy should have _get_equity method."""
        assert hasattr(BaseEvolveStrategy, "_get_equity")
