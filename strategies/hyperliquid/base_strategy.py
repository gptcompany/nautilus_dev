"""Hyperliquid Base Strategy with RiskManager (Spec 021 - US4).

This module provides a base strategy class for Hyperliquid trading
with integrated risk management from Spec 011.

The base strategy:
- Subscribes to market data on start
- Integrates RiskManager for automatic stop-loss
- Enforces position limits before order submission

Example:
    >>> from strategies.hyperliquid.base_strategy import HyperliquidBaseStrategy
    >>> from strategies.hyperliquid.config import HyperliquidStrategyConfig
    >>>
    >>> class MyStrategy(HyperliquidBaseStrategy):
    ...     def on_quote_tick(self, tick):
    ...         # Your trading logic here
    ...         pass
"""

from nautilus_trader.model.data import OrderBookDelta, QuoteTick, TradeTick
from nautilus_trader.model.events import PositionChanged, PositionClosed, PositionOpened
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy

from risk import RiskManager
from strategies.hyperliquid.config import HyperliquidStrategyConfig


class HyperliquidBaseStrategy(Strategy):
    """Base strategy for Hyperliquid with RiskManager integration.

    This base class provides:
    - Automatic data subscription on start
    - RiskManager integration for stop-loss management
    - Position limit enforcement

    Subclasses should override:
    - on_quote_tick(): For quote-based trading logic
    - on_trade_tick(): For trade-based trading logic
    - on_signal(): Custom signal handling

    Attributes:
        strategy_config: Strategy configuration with risk settings.
        instrument_id: InstrumentId for the trading instrument.
        risk_manager: RiskManager instance for stop-loss management.
    """

    def __init__(self, config: HyperliquidStrategyConfig):
        """Initialize the base strategy.

        Args:
            config: Strategy configuration including risk parameters.
        """
        super().__init__()
        self.strategy_config = config
        self.instrument_id = InstrumentId.from_str(config.instrument_id)

        # Initialize RiskManager with config including position limits
        risk_config = config.get_risk_config_with_limits()
        self.risk_manager = RiskManager(
            config=risk_config,
            strategy=self,
        )

    def on_start(self) -> None:
        """Subscribe to market data for the configured instrument.

        Override this method in subclasses to add custom initialization,
        but be sure to call super().on_start() first.
        """
        # Subscribe to all data types
        self.subscribe_quote_ticks(self.instrument_id)
        self.subscribe_trade_ticks(self.instrument_id)
        self.subscribe_order_book_deltas(self.instrument_id)

        self.log.info(f"Subscribed to {self.instrument_id}")
        self.log.info(
            f"RiskManager enabled: stop_loss={self.strategy_config.risk.stop_loss_pct}, "
            f"max_position={self.strategy_config.max_position_size}"
        )

    def on_event(self, event) -> None:
        """Route events to RiskManager for stop-loss management.

        The RiskManager handles:
        - PositionOpened: Creates stop-loss order
        - PositionClosed: Cancels stop-loss order
        - PositionChanged: Updates trailing stop (if enabled)

        Override this method to handle additional events, but call
        super().on_event(event) to ensure RiskManager receives events.

        Args:
            event: The event to handle.
        """
        # Always route to RiskManager first
        self.risk_manager.handle_event(event)

        # Log position events for debugging
        if isinstance(event, PositionOpened):
            self.log.info(
                f"Position OPENED: {event.position_id} side={event.entry} qty={event.quantity}"
            )
        elif isinstance(event, PositionClosed):
            self.log.info(f"Position CLOSED: {event.position_id} realized_pnl={event.realized_pnl}")
        elif isinstance(event, PositionChanged):
            self.log.debug(f"Position CHANGED: {event.position_id} qty={event.quantity}")

    def on_quote_tick(self, tick: QuoteTick) -> None:
        """Handle incoming quote ticks.

        Override this method in subclasses to implement
        quote-based trading logic.

        Args:
            tick: The quote tick event.
        """
        pass  # Override in subclass

    def on_trade_tick(self, tick: TradeTick) -> None:
        """Handle incoming trade ticks.

        Override this method in subclasses to implement
        trade-based trading logic.

        Args:
            tick: The trade tick event.
        """
        pass  # Override in subclass

    def on_order_book_delta(self, delta: OrderBookDelta) -> None:
        """Handle incoming orderbook updates.

        Override this method in subclasses to implement
        orderbook-based trading logic.

        Args:
            delta: The orderbook delta event.
        """
        pass  # Override in subclass

    def validate_order_size(self, size) -> bool:
        """Validate order size against position limits.

        Uses RiskManager to check if the order would exceed
        position limits.

        Args:
            size: The order size to validate.

        Returns:
            True if order is within limits, False otherwise.
        """
        # Reject negative or zero sizes
        if size <= 0:
            self.log.warning(f"Order size must be positive, got {size}")
            return False
        # Check against max position size
        if size > self.strategy_config.max_position_size:
            self.log.warning(
                f"Order size {size} exceeds max_position_size "
                f"{self.strategy_config.max_position_size}"
            )
            return False
        return True

    def on_stop(self) -> None:
        """Clean up on strategy stop.

        Override this method in subclasses for custom cleanup,
        but call super().on_stop() to ensure proper shutdown.
        """
        self.log.info(f"Strategy stopped for {self.instrument_id}")
