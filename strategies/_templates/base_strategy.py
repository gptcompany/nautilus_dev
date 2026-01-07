"""
Base Strategy Template for NautilusTrader.

All strategies should inherit from this base class.
Provides common functionality for position management, logging, and lifecycle.
"""

from decimal import Decimal

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.position import Position
from nautilus_trader.trading.strategy import Strategy


class BaseStrategyConfig(StrategyConfig, frozen=True):  # type: ignore[call-arg]
    """Base configuration for all strategies."""

    instrument_id: str
    bar_type: str
    trade_size: Decimal = Decimal("0.001")
    max_position_size: Decimal = Decimal("0.01")


class BaseStrategy(Strategy):
    """
    Base strategy class providing common functionality.

    Features:
    - Position tracking
    - Risk checks
    - Logging helpers
    - Lifecycle management
    """

    def __init__(self, config: BaseStrategyConfig) -> None:
        super().__init__(config)

        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type_str = config.bar_type
        self.trade_size = config.trade_size
        self.max_position_size = config.max_position_size

        # Will be set on_start
        self.instrument: Instrument | None = None

    def on_start(self) -> None:
        """Initialize strategy on start."""
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Instrument {self.instrument_id} not found")
            self.stop()
            return

        self.log.info(f"{self.__class__.__name__} started")
        self._on_start()

    def _on_start(self) -> None:
        """Override in subclass for custom start logic."""
        pass

    def on_stop(self) -> None:
        """Clean up on stop."""
        self.close_all_positions(self.instrument_id)
        self.cancel_all_orders(self.instrument_id)
        self.log.info(f"{self.__class__.__name__} stopped")
        self._on_stop()

    def _on_stop(self) -> None:
        """Override in subclass for custom stop logic."""
        pass

    # ─────────────────────────────────────────────────────────────────
    # Position Helpers
    # ─────────────────────────────────────────────────────────────────

    def get_position(self) -> Position | None:
        """Get current position for instrument."""
        return self.portfolio.position(self.instrument_id)

    def is_flat(self) -> bool:
        """Check if no position."""
        result = self.portfolio.is_flat(self.instrument_id)
        return bool(result)

    def is_long(self) -> bool:
        """Check if long position."""
        pos = self.get_position()
        return pos is not None and pos.is_long

    def is_short(self) -> bool:
        """Check if short position."""
        pos = self.get_position()
        return pos is not None and pos.is_short

    def position_quantity(self) -> Decimal:
        """Get current position quantity."""
        pos = self.get_position()
        return pos.quantity if pos else Decimal("0")

    # ─────────────────────────────────────────────────────────────────
    # Order Helpers
    # ─────────────────────────────────────────────────────────────────

    def buy(self, quantity: Decimal | None = None) -> None:
        """Submit market buy order."""
        if not self._can_trade():
            return

        qty = quantity or self.trade_size
        if not self._check_position_limit(qty):
            return

        if self.instrument is None:
            return

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(qty),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self.log.info(f"BUY {qty} @ MARKET")

    def sell(self, quantity: Decimal | None = None) -> None:
        """Submit market sell order."""
        if not self._can_trade():
            return

        qty = quantity or self.trade_size
        if not self._check_position_limit(qty):
            return

        if self.instrument is None:
            return

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(qty),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self.log.info(f"SELL {qty} @ MARKET")

    def close_position(self) -> None:
        """Close current position."""
        pos = self.get_position()
        if pos:
            super().close_position(pos)
            self.log.info("Position closed")

    # ─────────────────────────────────────────────────────────────────
    # Risk Checks
    # ─────────────────────────────────────────────────────────────────

    def _can_trade(self) -> bool:
        """Check if trading is allowed."""
        if self.instrument is None:
            self.log.warning("Cannot trade: instrument not loaded")
            return False
        return True

    def _check_position_limit(self, additional_qty: Decimal) -> bool:
        """Check if order would exceed position limit."""
        current = self.position_quantity()
        if current + additional_qty > self.max_position_size:
            self.log.warning(
                f"Position limit: {current} + {additional_qty} > {self.max_position_size}"
            )
            return False
        return True
