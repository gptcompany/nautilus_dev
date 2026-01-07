"""
Example: Risk-Managed Strategy

Demonstrates integration of RiskManager with a NautilusTrader strategy
for automatic stop-loss and position limit enforcement.

This is a reference implementation for T037.
"""

from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.message import Event
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.events import (
    OrderFilled,
    PositionClosed,
    PositionOpened,
)
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Quantity
from nautilus_trader.trading.strategy import Strategy

from risk import RiskConfig, RiskManager


class RiskManagedStrategyConfig(StrategyConfig, frozen=True):  # type: ignore[call-arg]
    """
    Configuration for RiskManagedStrategy.

    Attributes
    ----------
    instrument_id : str
        The instrument to trade.
    bar_type : str
        The bar type for data subscription.
    trade_size : str
        The size of each trade in base currency.
    risk : RiskConfig
        Risk management configuration.
    """

    instrument_id: str
    bar_type: str
    trade_size: str = "0.1"
    risk: RiskConfig = RiskConfig()


class RiskManagedStrategy(Strategy):
    """
    Example strategy demonstrating RiskManager integration.

    Features:
    - Automatic stop-loss on every position
    - Position limit validation before order submission
    - Proper event routing to RiskManager

    Usage
    -----
    >>> config = RiskManagedStrategyConfig(
    ...     instrument_id="BTC/USDT.BINANCE",
    ...     bar_type="BTC/USDT.BINANCE-1-MINUTE-LAST",
    ...     risk=RiskConfig(
    ...         stop_loss_pct=Decimal("0.02"),
    ...         max_position_size={"BTC/USDT.BINANCE": Decimal("1.0")},
    ...     ),
    ... )
    >>> strategy = RiskManagedStrategy(config)
    """

    def __init__(self, config: RiskManagedStrategyConfig) -> None:
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        self.trade_size = Quantity.from_str(config.trade_size)

        # Initialize RiskManager with strategy reference
        self.risk_manager = RiskManager(
            config=config.risk,
            strategy=self,
        )

        # Track last bar for simple signal generation
        self._last_bar: Bar | None = None

    def on_start(self) -> None:
        """Subscribe to data on strategy start."""
        self.subscribe_bars(self.bar_type)
        self.log.info(f"Started with stop_loss_pct={self.risk_manager.config.stop_loss_pct}")

    def on_bar(self, bar: Bar) -> None:
        """
        Handle incoming bar data.

        Simple momentum logic: Buy if current close > last close.
        """
        if self._last_bar is None:
            self._last_bar = bar
            return

        # Simple momentum signal
        if bar.close > self._last_bar.close and not self._has_position():
            self._enter_long()

        self._last_bar = bar

    def on_event(self, event: Event) -> None:
        """
        Route position events to RiskManager.

        CRITICAL: This is where RiskManager hooks into position lifecycle.
        """
        # Delegate to RiskManager for stop-loss management
        self.risk_manager.handle_event(event)

        # Log position events for debugging
        if isinstance(event, PositionOpened):
            self.log.info(f"Position opened: {event.position_id}")
        elif isinstance(event, PositionClosed):
            self.log.info(f"Position closed: {event.position_id}")
        elif isinstance(event, OrderFilled):
            self.log.info(f"Order filled: {event.client_order_id}")

    def _has_position(self) -> bool:
        """Check if we have an open position."""
        is_long = self.portfolio.is_net_long(self.instrument_id)
        is_short = self.portfolio.is_net_short(self.instrument_id)
        return bool(is_long or is_short)

    def _enter_long(self) -> None:
        """Submit a market buy order with position limit validation."""
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.trade_size,
        )

        # Validate against position limits BEFORE submission
        if not self.risk_manager.validate_order(order):
            self.log.warning(f"Order rejected by risk manager: {order.client_order_id}")
            return

        self.submit_order(order)
        self.log.info(f"Submitted buy order: {order.client_order_id}")

    def on_stop(self) -> None:
        """Clean up on strategy stop."""
        self.log.info(f"Stopped. Active stops: {len(self.risk_manager.active_stops)}")
