"""Shared fixtures for Alpha-Evolve templates tests."""

from decimal import Decimal

import pytest

from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.test_kit.stubs.data import TestDataStubs
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs


# === NAUTILUS FIXTURES ===


@pytest.fixture
def instrument_id() -> InstrumentId:
    """Default test instrument ID."""
    return TestIdStubs.audusd_id()


@pytest.fixture
def bar_type() -> BarType:
    """Default test bar type."""
    return TestDataStubs.bartype_audusd_1min_bid()


@pytest.fixture
def trade_size() -> Decimal:
    """Default test trade size."""
    return Decimal("1.0")


@pytest.fixture
def sample_bar():
    """Sample bar for testing."""
    return TestDataStubs.bar_5decimal()


@pytest.fixture
def sample_bars():
    """Multiple sample bars for testing."""
    return [TestDataStubs.bar_5decimal() for _ in range(10)]


# === BASE STRATEGY FIXTURES ===


@pytest.fixture
def base_evolve_strategy_code() -> str:
    """Sample BaseEvolveStrategy subclass code for testing."""
    return '''"""Test strategy inheriting from BaseEvolveStrategy."""

from decimal import Decimal
from scripts.alpha_evolve.templates.base import BaseEvolveStrategy, BaseEvolveConfig
from nautilus_trader.model.data import Bar


class TestEvolveConfig(BaseEvolveConfig, frozen=True):
    """Test config."""
    pass


class TestEvolveStrategy(BaseEvolveStrategy):
    """Concrete test strategy for base class testing."""

    def _on_bar_evolved(self, bar: Bar) -> None:
        """Test decision logic."""
        # === EVOLVE-BLOCK: decision_logic ===
        if bar.close.as_double() > 1.0:
            self._enter_long(self.config.trade_size)
        # === END EVOLVE-BLOCK ===
'''


@pytest.fixture
def momentum_strategy_code() -> str:
    """Sample MomentumEvolveStrategy code for EVOLVE-BLOCK extraction."""
    return '''"""Momentum strategy with EMA crossover."""

from decimal import Decimal
from nautilus_trader.indicators import ExponentialMovingAverage
from scripts.alpha_evolve.templates.base import BaseEvolveStrategy, BaseEvolveConfig
from nautilus_trader.model.data import Bar


class MomentumEvolveConfig(BaseEvolveConfig, frozen=True):
    """Momentum strategy config."""
    fast_period: int = 10
    slow_period: int = 30


class MomentumEvolveStrategy(BaseEvolveStrategy):
    """EMA crossover strategy."""

    def __init__(self, config: MomentumEvolveConfig) -> None:
        super().__init__(config)
        self.fast_ema = ExponentialMovingAverage(config.fast_period)
        self.slow_ema = ExponentialMovingAverage(config.slow_period)

    def on_start(self) -> None:
        super().on_start()
        self.register_indicator_for_bars(self.config.bar_type, self.fast_ema)
        self.register_indicator_for_bars(self.config.bar_type, self.slow_ema)

    def _on_bar_evolved(self, bar: Bar) -> None:
        """Decision logic with EVOLVE-BLOCK."""
        if not self.indicators_initialized():
            return

        # === EVOLVE-BLOCK: decision_logic ===
        if self.fast_ema.value > self.slow_ema.value:
            if self.portfolio.is_flat(self.config.instrument_id):
                self._enter_long(self.config.trade_size)
        elif self.fast_ema.value < self.slow_ema.value:
            if self.portfolio.is_net_long(self.config.instrument_id):
                self._close_position()
        # === END EVOLVE-BLOCK ===
'''
