"""Shared fixtures for Alpha-Evolve tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

# === SAMPLE STRATEGY FIXTURES ===


@pytest.fixture
def sample_strategy_single_block() -> str:
    """Strategy code with single EVOLVE-BLOCK marker."""
    return '''"""Simple momentum strategy."""

from nautilus_trader.trading.strategy import Strategy


class MomentumStrategy(Strategy):
    """Momentum-based trading strategy."""

    def on_start(self):
        """Initialize strategy."""
        self.ema = ExponentialMovingAverage(period=20)

    def on_bar(self, bar):
        """Handle bar data."""
        self.ema.handle_bar(bar)
        # === EVOLVE-BLOCK: entry_logic ===
        if self.ema.value > bar.close:
            self.buy()
        # === END EVOLVE-BLOCK ===
'''


@pytest.fixture
def sample_strategy_multiple_blocks() -> str:
    """Strategy code with multiple EVOLVE-BLOCK markers."""
    return '''"""Multi-block strategy."""

from nautilus_trader.trading.strategy import Strategy


class MultiBlockStrategy(Strategy):
    """Strategy with multiple evolvable sections."""

    def on_start(self):
        """Initialize strategy."""
        # === EVOLVE-BLOCK: indicators ===
        self.ema_fast = ExponentialMovingAverage(period=10)
        self.ema_slow = ExponentialMovingAverage(period=20)
        # === END EVOLVE-BLOCK ===

    def on_bar(self, bar):
        """Handle bar data."""
        # === EVOLVE-BLOCK: entry_logic ===
        if self.ema_fast.value > self.ema_slow.value:
            self.buy()
        # === END EVOLVE-BLOCK ===

        # === EVOLVE-BLOCK: exit_logic ===
        if self.ema_fast.value < self.ema_slow.value:
            self.sell()
        # === END EVOLVE-BLOCK ===
'''


@pytest.fixture
def sample_strategy_nested_indentation() -> str:
    """Strategy with deeply nested EVOLVE-BLOCK."""
    return '''"""Nested strategy."""

class NestedStrategy:
    def method(self):
        if True:
            for i in range(10):
                # === EVOLVE-BLOCK: inner_logic ===
                result = i * 2
                # === END EVOLVE-BLOCK ===
        return result
'''


@pytest.fixture
def sample_strategy_no_blocks() -> str:
    """Strategy code without any EVOLVE-BLOCK markers."""
    return '''"""Plain strategy."""

class PlainStrategy:
    def on_bar(self, bar):
        self.buy()
'''


@pytest.fixture
def sample_strategy_malformed() -> str:
    """Strategy with malformed EVOLVE-BLOCK markers (missing END)."""
    return '''"""Malformed strategy."""

class MalformedStrategy:
    def on_bar(self, bar):
        # === EVOLVE-BLOCK: broken ===
        self.buy()
        # Missing END marker
'''

