"""Audit Observer Actor (Spec 030).

This module implements the AuditObserver Actor that subscribes to NautilusTrader
MessageBus events and logs them to the audit trail.

The observer listens for:
- Order events: OrderFilled, OrderRejected, OrderCanceled
- Position events: PositionOpened, PositionClosed, PositionChanged

Each event is converted to an audit event and emitted through the AuditEventEmitter.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from nautilus_trader.common.actor import Actor
from nautilus_trader.common.config import ActorConfig
from nautilus_trader.model.events.order import (
    OrderCanceled,
    OrderEvent,
    OrderFilled,
    OrderRejected,
)
from nautilus_trader.model.events.position import (
    PositionChanged,
    PositionClosed,
    PositionEvent,
    PositionOpened,
)

from strategies.common.audit.emitter import AuditEventEmitter
from strategies.common.audit.events import AuditEventType

if TYPE_CHECKING:

    pass


logger = logging.getLogger(__name__)


class AuditObserverConfig(ActorConfig):
    """Configuration for AuditObserver actor."""

    trader_id: str = "TRADER-001"
    """Trader identifier for audit events."""

    audit_base_path: str = "./data/audit/hot"
    """Base path for audit log files."""

    sync_writes: bool = True
    """Use synchronous writes for trade events (audit compliance)."""


class AuditObserver(Actor):
    """NautilusTrader Actor that observes and logs trading events.

    This actor subscribes to order and position events from the MessageBus
    and logs them to an immutable audit trail.

    Attributes:
        trader_id: Trader identifier for audit events.

    Example:
        >>> config = AuditObserverConfig(trader_id="TRADER-001")
        >>> observer = AuditObserver(config)
        >>> # Register with trading node
        >>> node.add_actor(observer)
    """

    def __init__(
        self,
        config: AuditObserverConfig,
        emitter: AuditEventEmitter | None = None,
    ) -> None:
        """Initialize the AuditObserver.

        Args:
            config: Actor configuration.
            emitter: Optional pre-configured emitter. If None, creates from config.
        """
        super().__init__(config)

        self._config = config
        self._emitter = emitter

        # Track expected prices for slippage calculation
        self._expected_prices: dict[str, float] = {}

    def on_start(self) -> None:
        """Called when the actor starts."""
        # Create emitter if not provided
        if self._emitter is None:
            from strategies.common.audit.config import AuditConfig

            audit_config = AuditConfig(
                base_path=self._config.audit_base_path,
                sync_writes=self._config.sync_writes,
            )
            self._emitter = AuditEventEmitter(
                trader_id=self._config.trader_id,
                config=audit_config,
            )

        # Subscribe to order events
        self.subscribe_order_events()

        # Subscribe to position events
        self.subscribe_position_events()

        logger.info(
            "AuditObserver started: trader_id=%s, path=%s",
            self._config.trader_id,
            self._config.audit_base_path,
        )

    def on_stop(self) -> None:
        """Called when the actor stops."""
        if self._emitter is not None:
            self._emitter.close()
        logger.info("AuditObserver stopped")

    def on_order_event(self, event: OrderEvent) -> None:
        """Handle order events.

        Args:
            event: Order event from MessageBus.
        """
        if self._emitter is None:
            return

        if isinstance(event, OrderFilled):
            self._on_order_filled(event)
        elif isinstance(event, OrderRejected):
            self._on_order_rejected(event)
        elif isinstance(event, OrderCanceled):
            self._on_order_canceled(event)

    def _on_order_filled(self, event: OrderFilled) -> None:
        """Handle OrderFilled event.

        Args:
            event: OrderFilled event.
        """
        # Calculate slippage if we have expected price
        order_id = str(event.client_order_id)
        expected_price = self._expected_prices.pop(order_id, None)

        slippage_bps = 0.0
        if expected_price is not None and expected_price > 0:
            actual_price = float(event.last_px)
            price_diff = actual_price - expected_price

            # Adjust sign based on side
            if event.order_side.name == "SELL":
                price_diff = -price_diff

            slippage_bps = (price_diff / expected_price) * 10000

        self._emitter.emit_trade(
            order_id=order_id,
            instrument_id=str(event.instrument_id),
            side=event.order_side.name,
            size=str(event.last_qty),
            price=str(event.last_px),
            strategy_source=str(event.strategy_id) if event.strategy_id else "unknown",
            slippage_bps=slippage_bps,
            event_type=AuditEventType.TRADE_FILL,
        )

    def _on_order_rejected(self, event: OrderRejected) -> None:
        """Handle OrderRejected event.

        Args:
            event: OrderRejected event.
        """
        self._emitter.emit_trade(
            order_id=str(event.client_order_id),
            instrument_id=str(event.instrument_id),
            side="UNKNOWN",  # Not available in rejection
            size="0",
            price="0",
            strategy_source=str(event.strategy_id) if event.strategy_id else "unknown",
            event_type=AuditEventType.TRADE_REJECTED,
        )

    def _on_order_canceled(self, event: OrderCanceled) -> None:
        """Handle OrderCanceled event.

        Args:
            event: OrderCanceled event.
        """
        # Log cancellations as system events (not trade events)
        self._emitter.emit_system(
            event_type=AuditEventType.SYS_REGIME_CHANGE,  # Using available type
            source="audit_observer",
            payload={
                "action": "order_canceled",
                "order_id": str(event.client_order_id),
                "instrument_id": str(event.instrument_id),
            },
        )

    def on_position_event(self, event: PositionEvent) -> None:
        """Handle position events.

        Args:
            event: Position event from MessageBus.
        """
        if self._emitter is None:
            return

        if isinstance(event, PositionOpened):
            self._on_position_opened(event)
        elif isinstance(event, PositionClosed):
            self._on_position_closed(event)
        elif isinstance(event, PositionChanged):
            self._on_position_changed(event)

    def _on_position_opened(self, event: PositionOpened) -> None:
        """Handle PositionOpened event.

        Args:
            event: PositionOpened event.
        """
        self._emitter.emit_trade(
            order_id=str(event.opening_order_id),
            instrument_id=str(event.instrument_id),
            side=event.entry.name,
            size=str(event.signed_qty),
            price=str(event.avg_px_open),
            strategy_source=str(event.strategy_id) if event.strategy_id else "unknown",
            event_type=AuditEventType.TRADE_POSITION_OPENED,
        )

    def _on_position_closed(self, event: PositionClosed) -> None:
        """Handle PositionClosed event.

        Args:
            event: PositionClosed event.
        """
        self._emitter.emit_trade(
            order_id=str(event.closing_order_id) if event.closing_order_id else "N/A",
            instrument_id=str(event.instrument_id),
            side=event.entry.name,
            size=str(event.signed_qty),
            price=str(event.avg_px_close),
            strategy_source=str(event.strategy_id) if event.strategy_id else "unknown",
            realized_pnl=str(event.realized_pnl),
            event_type=AuditEventType.TRADE_POSITION_CLOSED,
        )

    def _on_position_changed(self, event: PositionChanged) -> None:
        """Handle PositionChanged event.

        Args:
            event: PositionChanged event.
        """
        # Log significant position changes
        self._emitter.emit_system(
            event_type=AuditEventType.SYS_REGIME_CHANGE,
            source="audit_observer",
            payload={
                "action": "position_changed",
                "instrument_id": str(event.instrument_id),
                "quantity": str(event.signed_qty),
                "unrealized_pnl": str(event.unrealized_pnl),
            },
        )

    def set_expected_price(self, order_id: str, expected_price: float) -> None:
        """Set expected price for slippage calculation.

        Call this before submitting an order to track slippage.

        Args:
            order_id: Client order ID.
            expected_price: Expected execution price.
        """
        self._expected_prices[order_id] = expected_price

    @property
    def emitter(self) -> AuditEventEmitter | None:
        """Access the underlying audit emitter."""
        return self._emitter
