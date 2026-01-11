#!/usr/bin/env python3
"""
Immutable Audit Trail Module.

Implements blockchain-style hash chain for tamper-evident audit logging.
Each entry links to the previous via SHA-256 hash, making modifications detectable.

Usage:
    from security.audit_trail import AuditTrail, AuditEvent

    # Initialize
    audit = AuditTrail()

    # Log events
    audit.log(AuditEvent(
        event_type="order_submitted",
        actor="strategy_alpha",
        resource="BTCUSDT",
        action="buy",
        details={"quantity": 0.1, "price": 50000}
    ))

    # Verify integrity
    is_valid, errors = audit.verify_chain()

Security Features:
- SHA-256 hash chain (each entry references previous hash)
- Timestamped entries with microsecond precision
- Signature support for non-repudiation
- QuestDB persistence with hash verification
- Chain integrity validation
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Standard audit event types."""

    # Trading Events
    ORDER_SUBMITTED = "order_submitted"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    ORDER_REJECTED = "order_rejected"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"

    # Risk Events
    RISK_LIMIT_BREACH = "risk_limit_breach"
    TRADING_HALTED = "trading_halted"
    TRADING_RESUMED = "trading_resumed"
    DRAWDOWN_WARNING = "drawdown_warning"
    KILL_SWITCH_TRIGGERED = "kill_switch_triggered"

    # Security Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    WITHDRAWAL_REQUESTED = "withdrawal_requested"
    WITHDRAWAL_APPROVED = "withdrawal_approved"
    WITHDRAWAL_REJECTED = "withdrawal_rejected"

    # System Events
    CONFIG_CHANGED = "config_changed"
    MODEL_LOADED = "model_loaded"
    MODEL_PREDICTION = "model_prediction"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"

    # Admin Events
    USER_CREATED = "user_created"
    PERMISSION_CHANGED = "permission_changed"
    AUDIT_VERIFIED = "audit_verified"


@dataclass
class AuditEvent:
    """
    Immutable audit event with hash chain support.

    Once created, the hash is computed and the event cannot be modified
    without invalidating the chain.
    """

    event_type: str
    actor: str  # Who performed the action (user_id, strategy_id, system)
    resource: str  # What was affected (order_id, symbol, config_key)
    action: str  # What was done (create, update, delete, execute)
    details: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    previous_hash: str = ""
    hash: str = ""
    signature: str = ""  # Optional: ECDSA signature for non-repudiation

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of event data."""
        # Deterministic JSON serialization
        data = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "resource": self.resource,
            "action": self.action,
            "details": self.details,
            "previous_hash": self.previous_hash,
        }
        json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(json_str.encode()).hexdigest()

    def finalize(self, previous_hash: str = "") -> AuditEvent:
        """Finalize event with hash chain link."""
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()
        return self

    def verify(self) -> bool:
        """Verify event hash is valid."""
        return self.hash == self.compute_hash()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        """Create event from dictionary."""
        return cls(**data)


class AuditTrail:
    """
    Immutable audit trail with hash chain verification.

    Stores events in QuestDB with cryptographic linking for tamper detection.
    """

    GENESIS_HASH = "0" * 64  # Genesis block hash

    def __init__(
        self,
        questdb_url: str | None = None,
        table_name: str = "audit_trail",
        auto_verify: bool = True,
    ):
        """
        Initialize audit trail.

        Args:
            questdb_url: QuestDB HTTP URL. Uses QUESTDB_URL env var if not provided.
            table_name: Table name for audit events.
            auto_verify: Verify chain on startup.
        """
        self.questdb_url = questdb_url or os.getenv("QUESTDB_URL", "http://localhost:9000")
        self.table_name = table_name
        self._last_hash = self.GENESIS_HASH
        self._event_count = 0

        # Initialize table
        self._init_table()

        # Load last hash
        self._load_last_hash()

        # Verify chain on startup
        if auto_verify:
            is_valid, errors = self.verify_chain(limit=100)
            if not is_valid:
                logger.error(f"Audit trail integrity check failed: {errors}")

    def _init_table(self) -> None:
        """Create audit trail table if not exists."""
        import urllib.request

        query = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            timestamp TIMESTAMP,
            event_id STRING,
            event_type SYMBOL,
            actor STRING,
            resource STRING,
            action SYMBOL,
            details STRING,
            previous_hash STRING,
            hash STRING,
            signature STRING
        ) TIMESTAMP(timestamp) PARTITION BY DAY
        """
        try:
            url = f"{self.questdb_url}/exec?query={urllib.parse.quote(query)}"
            urllib.request.urlopen(url, timeout=5)
        except Exception as e:
            logger.warning(f"Failed to create audit table: {e}")

    def _load_last_hash(self) -> None:
        """Load the last hash from the chain."""
        import urllib.parse
        import urllib.request

        query = f"SELECT hash FROM {self.table_name} ORDER BY timestamp DESC LIMIT 1"
        try:
            url = f"{self.questdb_url}/exec?query={urllib.parse.quote(query)}"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read())
                if data.get("dataset") and len(data["dataset"]) > 0:
                    self._last_hash = data["dataset"][0][0]
                    logger.info(f"Loaded last audit hash: {self._last_hash[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to load last hash: {e}")

    def log(
        self,
        event: AuditEvent | None = None,
        event_type: str = "",
        actor: str = "system",
        resource: str = "",
        action: str = "",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """
        Log an audit event to the immutable trail.

        Can pass an AuditEvent object or individual parameters.
        """
        if event is None:
            event = AuditEvent(
                event_type=event_type,
                actor=actor,
                resource=resource,
                action=action,
                details=details or {},
            )

        # Finalize with hash chain
        event.finalize(self._last_hash)

        # Store in QuestDB
        self._store_event(event)

        # Update state
        self._last_hash = event.hash
        self._event_count += 1

        logger.debug(f"Audit logged: {event.event_type} by {event.actor}")
        return event

    def _store_event(self, event: AuditEvent) -> None:
        """Store event in QuestDB."""
        import urllib.parse
        import urllib.request

        details_json = json.dumps(event.details).replace("'", "''")
        query = f"""
        INSERT INTO {self.table_name} VALUES(
            '{event.timestamp}',
            '{event.event_id}',
            '{event.event_type}',
            '{event.actor}',
            '{event.resource}',
            '{event.action}',
            '{details_json}',
            '{event.previous_hash}',
            '{event.hash}',
            '{event.signature}'
        )
        """
        try:
            url = f"{self.questdb_url}/exec?query={urllib.parse.quote(query)}"
            urllib.request.urlopen(url, timeout=5)
        except Exception as e:
            logger.error(f"Failed to store audit event: {e}")
            raise

    def verify_chain(self, limit: int = 1000, offset: int = 0) -> tuple[bool, list[str]]:
        """
        Verify the integrity of the audit trail.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        import urllib.parse
        import urllib.request

        errors: list[str] = []

        query = f"""
        SELECT event_id, event_type, timestamp, actor, resource, action,
               details, previous_hash, hash
        FROM {self.table_name}
        ORDER BY timestamp ASC
        LIMIT {limit} OFFSET {offset}
        """

        try:
            url = f"{self.questdb_url}/exec?query={urllib.parse.quote(query)}"
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read())
                rows = data.get("dataset", [])

                if not rows:
                    return True, []

                expected_prev_hash = self.GENESIS_HASH if offset == 0 else None

                for row in rows:
                    event = AuditEvent(
                        event_id=row[0],
                        event_type=row[1],
                        timestamp=row[2],
                        actor=row[3],
                        resource=row[4],
                        action=row[5],
                        details=json.loads(row[6]) if row[6] else {},
                        previous_hash=row[7],
                        hash=row[8],
                    )

                    # Verify hash
                    if not event.verify():
                        errors.append(
                            f"Hash mismatch for event {event.event_id}: "
                            f"stored={event.hash[:16]}, computed={event.compute_hash()[:16]}"
                        )

                    # Verify chain link
                    if expected_prev_hash and event.previous_hash != expected_prev_hash:
                        errors.append(
                            f"Chain break at event {event.event_id}: "
                            f"expected_prev={expected_prev_hash[:16]}, "
                            f"actual_prev={event.previous_hash[:16]}"
                        )

                    expected_prev_hash = event.hash

                return len(errors) == 0, errors

        except Exception as e:
            logger.error(f"Failed to verify chain: {e}")
            return False, [str(e)]

    def get_events(
        self,
        event_type: str | None = None,
        actor: str | None = None,
        resource: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events with filters."""
        import urllib.parse
        import urllib.request

        conditions = []
        if event_type:
            conditions.append(f"event_type = '{event_type}'")
        if actor:
            conditions.append(f"actor = '{actor}'")
        if resource:
            conditions.append(f"resource = '{resource}'")
        if start_time:
            conditions.append(f"timestamp >= '{start_time.isoformat()}'")
        if end_time:
            conditions.append(f"timestamp <= '{end_time.isoformat()}'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
        SELECT event_id, event_type, timestamp, actor, resource, action,
               details, previous_hash, hash, signature
        FROM {self.table_name}
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT {limit}
        """

        try:
            url = f"{self.questdb_url}/exec?query={urllib.parse.quote(query)}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
                return [
                    AuditEvent(
                        event_id=row[0],
                        event_type=row[1],
                        timestamp=row[2],
                        actor=row[3],
                        resource=row[4],
                        action=row[5],
                        details=json.loads(row[6]) if row[6] else {},
                        previous_hash=row[7],
                        hash=row[8],
                        signature=row[9] or "",
                    )
                    for row in data.get("dataset", [])
                ]
        except Exception as e:
            logger.error(f"Failed to query events: {e}")
            return []


# Convenience functions
_default_trail: AuditTrail | None = None


def audit_log(
    event_type: str,
    actor: str = "system",
    resource: str = "",
    action: str = "",
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    """Log an audit event using the default trail."""
    global _default_trail
    if _default_trail is None:
        _default_trail = AuditTrail(auto_verify=False)

    return _default_trail.log(
        event_type=event_type,
        actor=actor,
        resource=resource,
        action=action,
        details=details,
    )


def verify_audit_trail(limit: int = 1000) -> tuple[bool, list[str]]:
    """Verify audit trail integrity using default trail."""
    global _default_trail
    if _default_trail is None:
        _default_trail = AuditTrail(auto_verify=False)

    return _default_trail.verify_chain(limit=limit)
