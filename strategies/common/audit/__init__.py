"""Audit Trail System (Spec 030).

This module provides append-only audit logging for algorithmic trading systems.
All parameter changes, trade executions, and signals are logged immutably
for post-mortem analysis and regulatory compliance.

Key components:
- AuditEvent: Base event with checksum for tamper detection
- AuditEventEmitter: Thread-safe event emission
- AppendOnlyWriter: O_APPEND enforced file writes
- AuditQuery: DuckDB-based query interface (optional)

Example:
    >>> from strategies.common.audit import AuditEventEmitter, AuditConfig
    >>> config = AuditConfig(base_path="./data/audit")
    >>> emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)
    >>> emitter.emit_param_change(
    ...     param_name="risk_multiplier",
    ...     old_value=1.0,
    ...     new_value=0.5,
    ...     trigger_reason="drawdown > 10%",
    ...     source="meta_controller",
    ... )
"""

from strategies.common.audit.config import AuditConfig
from strategies.common.audit.emitter import AuditEventEmitter
from strategies.common.audit.events import (
    AuditEvent,
    AuditEventType,
    ParameterChangeEvent,
    SignalEvent,
    SystemEvent,
    TradeEvent,
)
from strategies.common.audit.writer import AppendOnlyWriter

__all__ = [
    "AuditConfig",
    "AuditEvent",
    "AuditEventEmitter",
    "AuditEventType",
    "AppendOnlyWriter",
    "ParameterChangeEvent",
    "SignalEvent",
    "SystemEvent",
    "TradeEvent",
]
