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
from strategies.common.audit.converter import ParquetConverter
from strategies.common.audit.emitter import AuditEventEmitter
from strategies.common.audit.events import (
    AuditEvent,
    AuditEventType,
    ParameterChangeEvent,
    SignalEvent,
    SystemEvent,
    TradeEvent,
)
from strategies.common.audit.query import AuditQuery
from strategies.common.audit.writer import AppendOnlyWriter

# Observer requires NautilusTrader - import only if available
try:
    from strategies.common.audit.observer import AuditObserver, AuditObserverConfig

    _HAS_OBSERVER = True
except ImportError:
    AuditObserver = None  # type: ignore[assignment, misc]
    AuditObserverConfig = None  # type: ignore[assignment, misc]
    _HAS_OBSERVER = False

__all__ = [
    "AuditConfig",
    "AuditEvent",
    "AuditEventEmitter",
    "AuditEventType",
    "AuditObserver",
    "AuditObserverConfig",
    "AuditQuery",
    "AppendOnlyWriter",
    "ParameterChangeEvent",
    "ParquetConverter",
    "SignalEvent",
    "SystemEvent",
    "TradeEvent",
]
