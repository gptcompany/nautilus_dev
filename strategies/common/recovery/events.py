"""Position Recovery Event Schemas (Spec 017).

This module defines the event schemas for position recovery.
Events are used for logging, monitoring, and alerting.
"""

from enum import Enum

from pydantic import BaseModel, Field


class RecoveryEventType(str, Enum):
    """Types of recovery events."""

    RECOVERY_STARTED = "recovery.started"
    POSITION_LOADED = "recovery.position.loaded"
    POSITION_RECONCILED = "recovery.position.reconciled"
    POSITION_DISCREPANCY = "recovery.position.discrepancy"
    INDICATORS_WARMING = "recovery.indicators.warming"
    INDICATORS_READY = "recovery.indicators.ready"
    RECOVERY_COMPLETED = "recovery.completed"
    RECOVERY_FAILED = "recovery.failed"
    RECOVERY_TIMEOUT = "recovery.timeout"


class RecoveryStartedEvent(BaseModel):
    """Emitted when recovery process begins."""

    event_type: str = RecoveryEventType.RECOVERY_STARTED
    trader_id: str = Field(description="Trader identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    cached_positions_count: int = Field(description="Number of positions in cache")


class PositionLoadedEvent(BaseModel):
    """Emitted when a position is loaded from cache."""

    event_type: str = RecoveryEventType.POSITION_LOADED
    trader_id: str = Field(description="Trader identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    instrument_id: str = Field(description="Position instrument")
    side: str = Field(description="Position side (LONG/SHORT)")
    quantity: str = Field(description="Position quantity as string")
    avg_entry_price: str = Field(description="Average entry price as string")


class PositionReconciledEvent(BaseModel):
    """Emitted when a position is successfully reconciled with exchange."""

    event_type: str = RecoveryEventType.POSITION_RECONCILED
    trader_id: str = Field(description="Trader identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    instrument_id: str = Field(description="Position instrument")
    cached_quantity: str = Field(description="Quantity from cache")
    exchange_quantity: str = Field(description="Quantity from exchange")
    reconciled: bool = Field(description="Whether reconciliation succeeded")


class PositionDiscrepancyEvent(BaseModel):
    """Emitted when cache and exchange positions differ."""

    event_type: str = RecoveryEventType.POSITION_DISCREPANCY
    trader_id: str = Field(description="Trader identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    instrument_id: str = Field(description="Position instrument")
    cached_side: str | None = Field(description="Side from cache")
    exchange_side: str | None = Field(description="Side from exchange")
    cached_quantity: str | None = Field(description="Quantity from cache")
    exchange_quantity: str | None = Field(description="Quantity from exchange")
    resolution: str = Field(description="How discrepancy was resolved")


class IndicatorsWarmingEvent(BaseModel):
    """Emitted when indicator warmup begins."""

    event_type: str = RecoveryEventType.INDICATORS_WARMING
    trader_id: str = Field(description="Trader identifier")
    strategy_id: str = Field(description="Strategy identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    indicator_count: int = Field(description="Number of indicators to warm")
    lookback_days: int = Field(description="Historical data lookback")


class IndicatorsReadyEvent(BaseModel):
    """Emitted when indicator warmup completes."""

    event_type: str = RecoveryEventType.INDICATORS_READY
    trader_id: str = Field(description="Trader identifier")
    strategy_id: str = Field(description="Strategy identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    warmup_duration_ms: float = Field(description="Warmup duration in milliseconds")
    bars_processed: int = Field(description="Number of bars processed")


class RecoveryCompletedEvent(BaseModel):
    """Emitted when recovery completes successfully."""

    event_type: str = RecoveryEventType.RECOVERY_COMPLETED
    trader_id: str = Field(description="Trader identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    positions_recovered: int = Field(description="Number of positions recovered")
    discrepancies_resolved: int = Field(description="Number of discrepancies resolved")
    total_duration_ms: float = Field(description="Total recovery duration in ms")
    strategies_ready: int = Field(description="Number of strategies ready")


class RecoveryFailedEvent(BaseModel):
    """Emitted when recovery fails."""

    event_type: str = RecoveryEventType.RECOVERY_FAILED
    trader_id: str = Field(description="Trader identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    error_code: str = Field(description="Error code")
    error_message: str = Field(description="Human-readable error message")
    positions_recovered: int = Field(description="Positions recovered before failure")
    recoverable: bool = Field(description="Whether recovery can be retried")


class RecoveryTimeoutEvent(BaseModel):
    """Emitted when recovery exceeds max time."""

    event_type: str = RecoveryEventType.RECOVERY_TIMEOUT
    trader_id: str = Field(description="Trader identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    timeout_secs: float = Field(description="Configured timeout")
    elapsed_secs: float = Field(description="Actual elapsed time")
    positions_recovered: int = Field(description="Positions recovered before timeout")
