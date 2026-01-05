"""Audit Event Emitter (Spec 030).

This module implements the AuditEventEmitter for emitting audit events.
Extends the RecoveryEventEmitter pattern with sequence tracking and writer integration.

Key features:
- Thread-safe event emission
- Monotonic sequence numbers for ordering
- Convenience methods for common event types
- Optional callback for message bus integration
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from strategies.common.audit.config import AuditConfig
from strategies.common.audit.events import (
    AuditEvent,
    AuditEventType,
    ParameterChangeEvent,
    SignalEvent,
    SystemEvent,
    TradeEvent,
)
from strategies.common.audit.writer import AppendOnlyWriter

if TYPE_CHECKING:

    from pydantic import BaseModel


# Module logger
_log = logging.getLogger(__name__)


class AuditEventEmitter:
    """Emitter for audit events.

    Provides methods to emit audit events for logging, monitoring, and compliance.
    Integrates with AppendOnlyWriter for immutable storage.

    Attributes:
        trader_id: Trader identifier for all emitted events.
        sequence: Current sequence number (monotonic).

    Example:
        >>> from strategies.common.audit import AuditEventEmitter, AuditConfig
        >>> config = AuditConfig(base_path="./data/audit/hot")
        >>> emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)
        >>> emitter.emit_param_change(
        ...     param_name="risk_multiplier",
        ...     old_value=1.0,
        ...     new_value=0.5,
        ...     trigger_reason="drawdown > 10%",
        ...     source="meta_controller",
        ... )
        >>> emitter.close()
    """

    def __init__(
        self,
        trader_id: str,
        config: AuditConfig | None = None,
        writer: AppendOnlyWriter | None = None,
        logger: logging.Logger | None = None,
        on_event: Callable[[BaseModel], None] | None = None,
    ) -> None:
        """Initialize the AuditEventEmitter.

        Args:
            trader_id: Trader identifier for all emitted events.
            config: Audit configuration. If None, uses defaults.
            writer: Optional custom writer. If None, creates from config.
            logger: Optional custom logger. If None, uses module logger.
            on_event: Optional callback invoked for each emitted event.
        """
        self._trader_id = trader_id
        self._config = config or AuditConfig()
        self._log = logger or _log
        self._on_event = on_event
        self._sequence = 0

        # Create writer if not provided
        if writer is not None:
            self._writer = writer
            self._owns_writer = False
        else:
            self._writer = AppendOnlyWriter(
                base_path=self._config.base_path,
                sync_writes=self._config.sync_writes,
                rotate_daily=self._config.rotate_daily,
            )
            self._owns_writer = True

        _log.debug("AuditEventEmitter initialized: trader_id=%s", trader_id)

    @property
    def trader_id(self) -> str:
        """Trader identifier for all emitted events."""
        return self._trader_id

    @property
    def sequence(self) -> int:
        """Current sequence number (next event will use this)."""
        return self._sequence

    @property
    def writer(self) -> AppendOnlyWriter:
        """Underlying AppendOnlyWriter."""
        return self._writer

    def emit(self, event: AuditEvent) -> AuditEvent:
        """Emit an audit event.

        Sets trader_id and sequence, writes to log, invokes callback.

        Args:
            event: Audit event to emit.

        Returns:
            The emitted event (with trader_id and sequence set).
        """
        # Set trader_id and sequence
        event.trader_id = self._trader_id
        event.sequence = self._sequence
        self._sequence += 1

        # Write to append-only log
        self._writer.write(event)

        # Log for observability (debug level to avoid spam)
        self._log.debug(
            "Audit: %s seq=%d",
            event.event_type.value,
            event.sequence,
        )

        # Invoke callback if registered
        if self._on_event is not None:
            self._on_event(event)

        return event

    def emit_param_change(
        self,
        param_name: str,
        old_value: Any,
        new_value: Any,
        trigger_reason: str,
        source: str,
        event_type: AuditEventType = AuditEventType.PARAM_STATE_CHANGE,
    ) -> ParameterChangeEvent:
        """Emit a parameter change event.

        Convenience method for logging parameter changes.

        Args:
            param_name: Name of the parameter that changed.
            old_value: Previous value (will be stringified).
            new_value: New value (will be stringified).
            trigger_reason: Why the parameter changed.
            source: Source component that changed the parameter.
            event_type: Event type (default: PARAM_STATE_CHANGE).

        Returns:
            The emitted event.
        """
        event = ParameterChangeEvent(
            event_type=event_type,
            source=source,
            param_name=param_name,
            old_value=str(old_value),
            new_value=str(new_value),
            trigger_reason=trigger_reason,
        )
        return self.emit(event)

    def emit_trade(
        self,
        order_id: str,
        instrument_id: str,
        side: str,
        size: str | float,
        price: str | float,
        strategy_source: str,
        source: str = "nautilus_trader",
        slippage_bps: float = 0.0,
        realized_pnl: str | float = "0",
        event_type: AuditEventType = AuditEventType.TRADE_FILL,
    ) -> TradeEvent:
        """Emit a trade execution event.

        Convenience method for logging trade executions.

        Args:
            order_id: Client order ID.
            instrument_id: Traded instrument.
            side: Trade side (BUY/SELL).
            size: Trade size.
            price: Execution price.
            strategy_source: Strategy that generated the trade.
            source: Source component (default: nautilus_trader).
            slippage_bps: Slippage in basis points.
            realized_pnl: Realized P&L.
            event_type: Event type (default: TRADE_FILL).

        Returns:
            The emitted event.
        """
        event = TradeEvent(
            event_type=event_type,
            source=source,
            order_id=order_id,
            instrument_id=instrument_id,
            side=side,
            size=str(size),
            price=str(price),
            slippage_bps=slippage_bps,
            realized_pnl=str(realized_pnl),
            strategy_source=strategy_source,
        )
        return self.emit(event)

    def emit_signal(
        self,
        signal_value: float,
        regime: str,
        confidence: float,
        strategy_source: str,
        source: str,
    ) -> SignalEvent:
        """Emit a signal generation event.

        Convenience method for logging signals.

        Args:
            signal_value: Signal strength/direction.
            regime: Market regime at signal generation.
            confidence: Confidence level (0-1).
            strategy_source: Strategy that generated the signal.
            source: Source component.

        Returns:
            The emitted event.
        """
        event = SignalEvent(
            source=source,
            signal_value=signal_value,
            regime=regime,
            confidence=confidence,
            strategy_source=strategy_source,
        )
        return self.emit(event)

    def emit_system(
        self,
        event_type: AuditEventType,
        source: str,
        payload: dict[str, Any],
    ) -> SystemEvent:
        """Emit a system event.

        Convenience method for logging system-level events.

        Args:
            event_type: Event type (should be sys.* type).
            source: Source component.
            payload: Event-specific data.

        Returns:
            The emitted event.
        """
        event = SystemEvent(
            event_type=event_type,
            source=source,
            payload=payload,
        )
        return self.emit(event)

    def flush(self) -> None:
        """Flush pending writes to disk."""
        self._writer.flush()

    def close(self) -> None:
        """Close the emitter and writer.

        Should be called when shutting down the audit system.
        Only closes writer if emitter owns it.
        """
        if self._owns_writer:
            self._writer.close()
        _log.debug("AuditEventEmitter closed")

    def __enter__(self) -> "AuditEventEmitter":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
