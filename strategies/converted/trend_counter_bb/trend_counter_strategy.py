"""
Trend Counter Strategy - BigBeluga Style.

Converted from Pine Script indicator to NautilusTrader strategy.
Uses TrendCounterIndicator for trend detection and entry signals.

Entry Logic:
    Long: Trend == STRONG_UP and strength > 0.7
    Short: Trend == STRONG_DOWN and strength > 0.7

Exit Logic:
    Long Exit: Trend changes to DOWN or STRONG_DOWN
    Short Exit: Trend changes to UP or STRONG_UP
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy

from .indicator import Trend, TrendCounterIndicator

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar


class TrendCounterBBConfig(StrategyConfig, frozen=True):  # type: ignore[call-arg]
    """
    Configuration for TrendCounterBB strategy.

    Parameters
    ----------
    instrument_id : str
        The instrument identifier.
    bar_type : str
        The bar type for data subscription.
    trade_size : Decimal
        Position size per trade.
    length : int
        Trend counter lookback period.
    smooth : int
        EMA smoothing period for counter.
    entry_strength : float
        Minimum strength required for entry (0-1).
    """

    instrument_id: str
    bar_type: str
    trade_size: Decimal = Decimal("0.1")
    length: int = 20
    smooth: int = 5
    entry_strength: float = 0.7


class TrendCounterBBStrategy(Strategy):
    """
    Trend Counter strategy based on BigBeluga pattern.

    This strategy enters positions when the trend counter shows
    strong trend with high strength, and exits when trend reverses.
    """

    def __init__(self, config: TrendCounterBBConfig) -> None:
        """Initialize the Trend Counter strategy."""
        super().__init__(config)

        # Parse configuration
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        self.trade_size = config.trade_size
        self.entry_strength = config.entry_strength

        # Create indicator
        self.trend_counter = TrendCounterIndicator(
            length=config.length,
            smooth=config.smooth,
        )

        # Track previous trend for change detection
        self._prev_trend: Trend = Trend.NEUTRAL

        # Instrument reference
        self.instrument = None

    def on_start(self) -> None:
        """Initialize strategy on start."""
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Instrument {self.instrument_id} not found")
            self.stop()
            return

        # Subscribe to bar data
        self.subscribe_bars(self.bar_type)

        # Register indicator (automatic updates)
        self.register_indicator_for_bars(self.bar_type, self.trend_counter)

        self.log.info(
            f"TrendCounterBBStrategy started: "
            f"length={self.trend_counter.length}, "
            f"smooth={self.trend_counter.smooth}"
        )

    def on_bar(self, bar: Bar) -> None:
        """Handle bar updates."""
        # Wait for indicator initialization
        if not self.trend_counter.initialized:
            return

        trend = self.trend_counter.trend
        strength = self.trend_counter.strength

        # Check entry conditions
        if self.portfolio.is_flat(self.instrument_id):
            if trend == Trend.STRONG_UP and strength >= self.entry_strength:
                self._enter_long(bar)
            elif trend == Trend.STRONG_DOWN and strength >= self.entry_strength:
                self._enter_short(bar)

        # Check exit conditions
        else:
            position = self.portfolio.position(self.instrument_id)
            if position is not None:
                if position.is_long and trend in (Trend.DOWN, Trend.STRONG_DOWN):
                    self._exit_long(bar)
                elif position.is_short and trend in (Trend.UP, Trend.STRONG_UP):
                    self._exit_short(bar)

        # Store previous trend
        self._prev_trend = trend

    def _enter_long(self, bar: Bar) -> None:
        """Enter long position."""
        if self.instrument is None:
            return

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self.log.info(
            f"LONG entry @ {bar.close} | "
            f"Counter={self.trend_counter.value} | "
            f"Strength={self.trend_counter.strength:.2f}"
        )

    def _enter_short(self, bar: Bar) -> None:
        """Enter short position."""
        if self.instrument is None:
            return

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self.log.info(
            f"SHORT entry @ {bar.close} | "
            f"Counter={self.trend_counter.value} | "
            f"Strength={self.trend_counter.strength:.2f}"
        )

    def _exit_long(self, bar: Bar) -> None:
        """Exit long position."""
        position = self.portfolio.position(self.instrument_id)
        if position and position.is_long:
            self.close_position(position)
            self.log.info(
                f"LONG exit @ {bar.close} | Trend reversed to {self.trend_counter.trend.name}"
            )

    def _exit_short(self, bar: Bar) -> None:
        """Exit short position."""
        position = self.portfolio.position(self.instrument_id)
        if position and position.is_short:
            self.close_position(position)
            self.log.info(
                f"SHORT exit @ {bar.close} | Trend reversed to {self.trend_counter.trend.name}"
            )

    def on_stop(self) -> None:
        """Clean up on stop."""
        self.close_all_positions(self.instrument_id)
        self.cancel_all_orders(self.instrument_id)
        self.log.info("TrendCounterBBStrategy stopped")
