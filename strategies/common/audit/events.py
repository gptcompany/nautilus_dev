"""Audit Event Schemas (Spec 030).

This module defines Pydantic event schemas for the audit trail system.
All events include a checksum for tamper detection (Layer 1 integrity).

Event Types:
- param.*: Parameter changes (state, weights, k, risk)
- trade.*: Trading events (signal, order, fill)
- sys.*: System events (evolution trigger, regime change, resampling)
"""

from __future__ import annotations

import hashlib
import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class AuditEventType(str, Enum):
    """Hierarchical event types for audit trail.

    Categories:
    - param: Parameter changes (logged for manipulation detection)
    - trade: Trading lifecycle (logged for audit compliance)
    - sys: System events (logged for forensics)
    """

    # Parameter changes
    PARAM_STATE_CHANGE = "param.state_change"
    PARAM_WEIGHT_CHANGE = "param.weight_change"
    PARAM_K_CHANGE = "param.k_change"
    PARAM_RISK_CHANGE = "param.risk_change"

    # Trading events
    TRADE_SIGNAL = "trade.signal"
    TRADE_ORDER = "trade.order"
    TRADE_FILL = "trade.fill"
    TRADE_REJECTED = "trade.rejected"
    TRADE_POSITION_OPENED = "trade.position_opened"
    TRADE_POSITION_CLOSED = "trade.position_closed"

    # System events
    SYS_EVOLUTION_TRIGGER = "sys.evolution_trigger"
    SYS_REGIME_CHANGE = "sys.regime_change"
    SYS_RESAMPLING = "sys.resampling"
    SYS_CORRELATION_UPDATE = "sys.correlation_update"  # CSRC (Spec 031)
    SYS_DECAY_UPDATE = "sys.decay_update"  # ADTS (Spec 032)


def _now_ns() -> int:
    """Get current time in nanoseconds."""
    return int(time.time() * 1_000_000_000)


class AuditEvent(BaseModel):
    """Base audit event with common fields.

    All audit events inherit from this base class which provides:
    - Timestamp in nanoseconds (matches NautilusTrader convention)
    - Event type for filtering
    - Source component for attribution
    - Trader ID for multi-trader systems
    - Sequence number for ordering
    - Computed checksum for tamper detection

    The checksum is computed from all other fields (Layer 1 integrity).

    Attributes:
        ts_event: Event timestamp in nanoseconds.
        event_type: Type of audit event (hierarchical).
        source: Source component that generated the event.
        trader_id: Trader identifier.
        sequence: Monotonic sequence number (set by emitter).

    Example:
        >>> event = AuditEvent(
        ...     event_type=AuditEventType.PARAM_STATE_CHANGE,
        ...     source="meta_controller",
        ... )
        >>> print(event.checksum)  # 16-char hex
    """

    ts_event: int = Field(
        default_factory=_now_ns,
        description="Event timestamp in nanoseconds",
    )
    event_type: AuditEventType = Field(description="Type of audit event")
    source: str = Field(description="Source component that generated the event")
    trader_id: str = Field(default="TRADER-001", description="Trader identifier")
    sequence: int = Field(default=0, description="Monotonic sequence number")

    @computed_field
    @property
    def checksum(self) -> str:
        """Compute SHA-256 checksum of event (Layer 1 integrity).

        Returns:
            First 16 characters of SHA-256 hex digest.
        """
        # Exclude checksum from payload to avoid recursion
        payload = self.model_dump_json(exclude={"checksum"})
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class ParameterChangeEvent(AuditEvent):
    """Parameter change event for audit trail.

    Logs every parameter change with old/new values and trigger reason.
    Critical for detecting parameter manipulation (Two Sigma scenario).

    Attributes:
        param_name: Name of the parameter that changed.
        old_value: Previous value (serialized as string).
        new_value: New value (serialized as string).
        trigger_reason: Why the parameter changed.

    Example:
        >>> event = ParameterChangeEvent(
        ...     source="meta_controller",
        ...     param_name="system_state",
        ...     old_value="VENTRAL",
        ...     new_value="SYMPATHETIC",
        ...     trigger_reason="health_score=65.3",
        ... )
    """

    event_type: AuditEventType = Field(
        default=AuditEventType.PARAM_STATE_CHANGE,
        description="Type of audit event",
    )
    param_name: str = Field(description="Name of the parameter")
    old_value: str = Field(description="Previous value (as string)")
    new_value: str = Field(description="New value (as string)")
    trigger_reason: str = Field(description="Why the parameter changed")


class TradeEvent(AuditEvent):
    """Trade execution event for audit trail.

    Logs every trade with execution details for audit compliance.
    Enables post-mortem analysis of trading decisions.

    Attributes:
        order_id: Client order ID.
        instrument_id: Traded instrument.
        side: Trade side (BUY/SELL).
        size: Trade size (as string for precision).
        price: Execution price (as string for precision).
        slippage_bps: Slippage in basis points.
        realized_pnl: Realized P&L (as string for precision).
        strategy_source: Strategy that generated the trade.

    Example:
        >>> event = TradeEvent(
        ...     source="nautilus_trader",
        ...     order_id="O-001",
        ...     instrument_id="BTCUSDT-PERP.BINANCE",
        ...     side="BUY",
        ...     size="0.5",
        ...     price="42000.00",
        ...     slippage_bps=1.5,
        ...     realized_pnl="0",
        ...     strategy_source="momentum_v1",
        ... )
    """

    event_type: AuditEventType = Field(
        default=AuditEventType.TRADE_FILL,
        description="Type of audit event",
    )
    order_id: str = Field(description="Client order ID")
    instrument_id: str = Field(description="Traded instrument")
    side: str = Field(description="Trade side (BUY/SELL)")
    size: str = Field(description="Trade size as string")
    price: str = Field(description="Execution price as string")
    slippage_bps: float = Field(default=0.0, description="Slippage in basis points")
    realized_pnl: str = Field(default="0", description="Realized P&L as string")
    strategy_source: str = Field(description="Strategy that generated the trade")


class SignalEvent(AuditEvent):
    """Signal generation event for audit trail.

    Logs every signal with value, regime, and confidence.
    Enables analysis of signal quality and trade conversion rate.

    Attributes:
        signal_value: Signal strength/direction.
        regime: Market regime at signal generation.
        confidence: Confidence level (0-1).
        strategy_source: Strategy that generated the signal.

    Example:
        >>> event = SignalEvent(
        ...     source="particle_portfolio",
        ...     signal_value=0.75,
        ...     regime="TRENDING",
        ...     confidence=0.85,
        ...     strategy_source="ensemble_v1",
        ... )
    """

    event_type: AuditEventType = Field(
        default=AuditEventType.TRADE_SIGNAL,
        description="Type of audit event",
    )
    signal_value: float = Field(description="Signal strength/direction")
    regime: str = Field(description="Market regime at signal generation")
    confidence: float = Field(description="Confidence level (0-1)")
    strategy_source: str = Field(description="Strategy that generated the signal")


class SystemEvent(AuditEvent):
    """System event for audit trail.

    Logs system-level events like regime changes, resampling, evolution triggers.
    Enables forensic analysis of system behavior.

    Attributes:
        payload: Event-specific data as dictionary.

    Example:
        >>> event = SystemEvent(
        ...     event_type=AuditEventType.SYS_EVOLUTION_TRIGGER,
        ...     source="alpha_evolve_bridge",
        ...     payload={
        ...         "trigger_reason": "DISSONANCE",
        ...         "underperforming_strategy": "momentum_v1",
        ...     },
        ... )
    """

    event_type: AuditEventType = Field(
        default=AuditEventType.SYS_REGIME_CHANGE,
        description="Type of audit event",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data",
    )
