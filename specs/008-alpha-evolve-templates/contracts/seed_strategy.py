"""
API Contract: MomentumEvolveStrategy (Seed Strategy)

This file defines the interface contract for the momentum seed strategy.
Implementation must adhere to this contract.
"""

from nautilus_trader.model.data import Bar

from .base_strategy import BaseEvolveConfig, BaseEvolveStrategy


class MomentumEvolveConfig(BaseEvolveConfig, frozen=True):
    """
    Configuration for momentum seed strategy.

    Attributes:
        instrument_id: Trading instrument
        bar_type: Bar type for data subscription
        trade_size: Order quantity per trade
        fast_period: Fast EMA period (default: 10)
        slow_period: Slow EMA period (default: 30)
    """

    fast_period: int = 10
    slow_period: int = 30

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.fast_period < 2:
            raise ValueError("fast_period must be >= 2")
        if self.slow_period <= self.fast_period:
            raise ValueError("slow_period must be > fast_period")


class MomentumEvolveStrategy(BaseEvolveStrategy):
    """
    Seed strategy using dual EMA crossover.

    Trading Logic:
    - Long entry: fast EMA > slow EMA (bullish momentum)
    - Exit: fast EMA < slow EMA (momentum fading)
    - No shorting (simplicity for seed)

    EVOLVE-BLOCK contains the decision logic that can be mutated.
    """

    def __init__(self, config: MomentumEvolveConfig) -> None:
        super().__init__(config)
        # Indicators initialized here (native Rust)
        # self.fast_ema = ExponentialMovingAverage(config.fast_period)
        # self.slow_ema = ExponentialMovingAverage(config.slow_period)

    def on_start(self) -> None:
        """
        Initialize strategy.

        1. Get instrument from cache
        2. Register indicators for auto-update
        3. Subscribe to bar data
        """
        ...

    def _on_bar_evolved(self, bar: Bar) -> None:
        """
        Handle bar with evolvable decision logic.

        Structure:
            1. Check indicator warmup (fixed)
            2. EVOLVE-BLOCK: decision_logic (mutable)
            3. Equity tracking (fixed, in parent on_bar)

        Expected EVOLVE-BLOCK content:
            # === EVOLVE-BLOCK: decision_logic ===
            if self.fast_ema.value > self.slow_ema.value:
                if self.portfolio.is_flat(self.config.instrument_id):
                    self._enter_long(self.config.trade_size)
            elif self.fast_ema.value < self.slow_ema.value:
                if self.portfolio.is_net_long(self.config.instrument_id):
                    self._close_position()
            # === END EVOLVE-BLOCK ===
        """
        ...


# === Expected Behavior ===
#
# 1. Given 6 months of BTC 1-minute bars:
#    - Produces at least 10 trades
#    - Non-zero Sharpe and Calmar ratios
#
# 2. Given trending market:
#    - Enters long on uptrend
#    - Exits on trend reversal
#
# 3. Given choppy market:
#    - May produce whipsaw losses
#    - This is expected and drives evolution pressure
