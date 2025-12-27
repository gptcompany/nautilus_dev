"""
Base Evolvable Strategy for Alpha-Evolve.

Provides abstract base class with:
- EVOLVE-BLOCK markers for targeted mutations
- Equity curve tracking
- Order helper methods
- Lifecycle management

Native Indicator Requirement:
    All indicators MUST use nautilus_trader.indicators (native Rust).
    Never reimplement EMA, RSI, etc. in Python.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.datetime import unix_nanos_to_dt
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.trading.strategy import Strategy

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar, BarType
    from nautilus_trader.model.identifiers import InstrumentId


@dataclass(frozen=True)
class EquityPoint:
    """Single equity curve entry."""

    timestamp: datetime
    equity: float


class BaseEvolveConfig(StrategyConfig, frozen=True):
    """
    Configuration for evolvable strategy base class.

    Attributes:
        instrument_id: Trading instrument identifier
        bar_type: Bar type for data subscription
        trade_size: Order quantity per trade
    """

    instrument_id: "InstrumentId"
    bar_type: "BarType"
    trade_size: Decimal


class BaseEvolveStrategy(Strategy, ABC):
    """
    Abstract base class for evolvable strategies.

    Provides:
    - Equity curve tracking (automatic on each bar)
    - Order helper methods (_enter_long, _enter_short, _close_position)
    - Lifecycle management (on_start, on_stop, on_reset)

    Subclasses must implement:
    - _on_bar_evolved(bar): Contains EVOLVE-BLOCK markers for mutation

    Example:
        class MyStrategy(BaseEvolveStrategy):
            def _on_bar_evolved(self, bar: Bar) -> None:
                # === EVOLVE-BLOCK: decision_logic ===
                if some_condition:
                    self._enter_long(self.config.trade_size)
                # === END EVOLVE-BLOCK ===
    """

    def __init__(self, config: BaseEvolveConfig) -> None:
        """Initialize base evolvable strategy."""
        super().__init__(config)
        self.instrument = None
        self._equity_curve: list[EquityPoint] = []

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    def on_start(self) -> None:
        """
        Initialize strategy on start.

        - Looks up instrument from cache
        - Subscribes to bar data
        """
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"Instrument not found: {self.config.instrument_id}")
            self.stop()
            return

        self.subscribe_bars(self.config.bar_type)
        self.log.info(f"Started with instrument: {self.config.instrument_id}")

    def on_bar(self, bar: "Bar") -> None:
        """
        Handle bar event.

        1. Calls _on_bar_evolved for trading logic
        2. Records equity point (protected from mutations)
        """
        # Execute evolvable trading logic
        self._on_bar_evolved(bar)

        # Record equity (infrastructure - not evolvable)
        equity = self._get_equity()
        point = EquityPoint(timestamp=unix_nanos_to_dt(bar.ts_event), equity=equity)
        self._equity_curve.append(point)

    def on_stop(self) -> None:
        """
        Cleanup on strategy stop.

        - Cancels all pending orders
        - Closes all open positions
        """
        self.cancel_all_orders(self.config.instrument_id)
        self.close_all_positions(self.config.instrument_id)
        self.log.info("Strategy stopped, orders cancelled, positions closed")

    def on_reset(self) -> None:
        """
        Reset strategy state.

        - Clears equity curve
        - Subclasses should override to reset indicators
        """
        self._equity_curve.clear()
        self.log.info("Strategy reset, equity curve cleared")

    # =========================================================================
    # Abstract Methods (MUST be implemented by subclasses)
    # =========================================================================

    @abstractmethod
    def _on_bar_evolved(self, bar: "Bar") -> None:
        """
        Handle bar with evolvable decision logic.

        This method MUST contain EVOLVE-BLOCK markers:

            # === EVOLVE-BLOCK: decision_logic ===
            # Trading logic here (entry/exit signals)
            # === END EVOLVE-BLOCK ===

        Everything outside the markers is fixed infrastructure.
        Everything inside is subject to mutation by the evolution system.

        Args:
            bar: The bar data to process
        """
        ...

    # =========================================================================
    # Equity Tracking
    # =========================================================================

    def get_equity_curve(self) -> list[EquityPoint]:
        """
        Return recorded equity curve.

        Returns:
            List of EquityPoint entries, one per bar processed.
        """
        return self._equity_curve.copy()

    def _get_equity(self) -> float:
        """
        Get current account equity.

        Returns:
            Account balance + unrealized PnL
        """
        venue = self.config.instrument_id.venue
        account = self.portfolio.account(venue)

        if account is None:
            return 0.0

        currency = account.base_currency
        balance = account.balance_total(currency)
        total = balance.as_double() if balance else 0.0

        # Add unrealized PnL if in position
        if not self.portfolio.is_flat(self.config.instrument_id):
            unrealized = self.portfolio.unrealized_pnl(self.config.instrument_id)
            if unrealized:
                total += unrealized.as_double()

        return total

    # =========================================================================
    # Order Helpers
    # =========================================================================

    def _enter_long(self, quantity: Decimal) -> None:
        """
        Submit market buy order.

        If currently short, closes short position first.

        Args:
            quantity: Size to buy (in base currency units)
        """
        if self.instrument is None:
            self.log.warning("Cannot enter long: instrument not initialized")
            return

        # Close short first if needed
        if self.portfolio.is_net_short(self.config.instrument_id):
            self._close_position()

        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(quantity),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def _enter_short(self, quantity: Decimal) -> None:
        """
        Submit market sell order.

        If currently long, closes long position first.

        Args:
            quantity: Size to sell (in base currency units)
        """
        if self.instrument is None:
            self.log.warning("Cannot enter short: instrument not initialized")
            return

        # Close long first if needed
        if self.portfolio.is_net_long(self.config.instrument_id):
            self._close_position()

        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(quantity),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def _close_position(self) -> None:
        """Close all positions for configured instrument."""
        self.close_all_positions(self.config.instrument_id)

    def _get_position_size(self) -> Decimal:
        """
        Get current net position size.

        Returns:
            Positive for long, negative for short, zero for flat.
        """
        return self.portfolio.net_position(self.config.instrument_id)
