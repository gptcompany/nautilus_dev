"""
Momentum Seed Strategy for Alpha-Evolve.

Provides a working seed strategy using dual EMA crossover:
- Long entry: fast EMA > slow EMA (bullish momentum)
- Exit: fast EMA < slow EMA (momentum fading)

This strategy serves as the starting point for evolutionary optimization.
The EVOLVE-BLOCK contains the decision logic that will be mutated.

Native Indicator Requirement:
    Uses ExponentialMovingAverage from nautilus_trader.indicators (native Rust).
    Never reimplement EMA in Python - native Rust is 100x faster.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nautilus_trader.indicators import ExponentialMovingAverage

from scripts.alpha_evolve.templates.base import BaseEvolveConfig, BaseEvolveStrategy

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar


class MomentumEvolveConfig(BaseEvolveConfig, frozen=True):  # type: ignore[call-arg]
    """
    Configuration for momentum seed strategy.

    Attributes:
        instrument_id: Trading instrument identifier
        bar_type: Bar type for data subscription
        trade_size: Order quantity per trade
        fast_period: Fast EMA period (must be >= 2)
        slow_period: Slow EMA period (must be > fast_period)
    """

    fast_period: int = 10
    slow_period: int = 30

    def __post_init__(self) -> None:
        """Validate that fast_period < slow_period and both are >= 2."""
        super().__post_init__()  # Validate trade_size from base class
        if self.fast_period < 2:
            raise ValueError(f"fast_period must be >= 2, got {self.fast_period}")
        if self.slow_period < 2:
            raise ValueError(f"slow_period must be >= 2, got {self.slow_period}")
        if self.fast_period >= self.slow_period:
            raise ValueError(
                f"fast_period ({self.fast_period}) must be < slow_period ({self.slow_period})"
            )


class MomentumEvolveStrategy(BaseEvolveStrategy):
    """
    Seed strategy using dual EMA crossover.

    Trading Logic:
    - Long entry: fast EMA > slow EMA (bullish momentum)
    - Exit: fast EMA < slow EMA (momentum fading)
    - No shorting (simplicity for seed)

    The EVOLVE-BLOCK contains the decision logic that can be mutated
    by the evolution system.

    Example:
        config = MomentumEvolveConfig(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
            bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
            trade_size=Decimal("0.1"),
            fast_period=10,
            slow_period=30,
        )
        strategy = MomentumEvolveStrategy(config)
    """

    def __init__(self, config: MomentumEvolveConfig) -> None:
        """
        Initialize momentum strategy.

        Args:
            config: Strategy configuration with EMA periods
        """
        super().__init__(config)
        self.fast_ema = ExponentialMovingAverage(config.fast_period)
        self.slow_ema = ExponentialMovingAverage(config.slow_period)

    def on_start(self) -> None:
        """
        Initialize strategy on start.

        - Calls parent on_start for instrument lookup
        - Registers EMA indicators for automatic bar updates
        """
        super().on_start()

        # Register indicators for automatic updates
        self.register_indicator_for_bars(self.config.bar_type, self.fast_ema)
        self.register_indicator_for_bars(self.config.bar_type, self.slow_ema)

        self.log.info(
            f"Momentum strategy started: fast_period={self.config.fast_period}, "
            f"slow_period={self.config.slow_period}"
        )

    def on_reset(self) -> None:
        """
        Reset strategy state.

        - Calls parent on_reset
        - Resets EMA indicators
        """
        super().on_reset()
        self.fast_ema.reset()
        self.slow_ema.reset()

    def _on_bar_evolved(self, bar: Bar) -> None:
        """
        Handle bar with evolvable decision logic.

        This method contains the EVOLVE-BLOCK that will be mutated
        by the evolution system.

        Args:
            bar: The bar data to process
        """
        # Wait for indicator warmup (fixed - not evolvable)
        if not self.indicators_initialized():
            return

        # === EVOLVE-BLOCK: decision_logic ===
        # Entry signal: fast EMA crosses above slow EMA
        if self.fast_ema.value > self.slow_ema.value:
            if self.portfolio.is_flat(self.config.instrument_id):
                self._enter_long(self.config.trade_size)

        # Exit signal: fast EMA crosses below slow EMA
        elif self.fast_ema.value < self.slow_ema.value:
            if self.portfolio.is_net_long(self.config.instrument_id):
                self._close_position()
        # === END EVOLVE-BLOCK ===
