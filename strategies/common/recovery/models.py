"""Recovery Models (Spec 017).

This module defines the data models for position recovery state tracking.
"""

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class RecoveryStatus(str, Enum):
    """Status of the recovery process.

    States:
        PENDING: Recovery not yet started.
        IN_PROGRESS: Recovery is currently running.
        COMPLETED: Recovery finished successfully.
        FAILED: Recovery encountered an unrecoverable error.
        TIMEOUT: Recovery exceeded max_recovery_time_secs.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class RecoveryState(BaseModel):
    """Current state of the recovery process.

    Tracks recovery progress including positions recovered,
    indicator warmup status, and timing information.

    Attributes:
        status: Current recovery status.
        positions_recovered: Number of positions successfully recovered.
        indicators_warmed: Whether indicators have completed warmup.
        orders_reconciled: Whether order reconciliation completed (Spec 016).
        ts_started: Timestamp recovery started (nanoseconds).
        ts_completed: Timestamp recovery completed (nanoseconds).
        error_message: Error message if recovery failed.
    """

    status: RecoveryStatus = Field(
        default=RecoveryStatus.PENDING,
        description="Current recovery status",
    )
    positions_recovered: int = Field(
        default=0,
        ge=0,
        description="Number of positions successfully recovered",
    )
    indicators_warmed: bool = Field(
        default=False,
        description="Whether indicators have completed warmup",
    )
    orders_reconciled: bool = Field(
        default=False,
        description="Whether order reconciliation completed (Spec 016)",
    )
    ts_started: int | None = Field(
        default=None,
        description="Timestamp recovery started (nanoseconds)",
    )
    ts_completed: int | None = Field(
        default=None,
        description="Timestamp recovery completed (nanoseconds)",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if recovery failed",
    )

    @property
    def recovery_duration_ms(self) -> float | None:
        """Calculate recovery duration in milliseconds.

        Returns:
            Duration in milliseconds if both timestamps are set, else None.
        """
        if self.ts_started and self.ts_completed:
            return (self.ts_completed - self.ts_started) / 1_000_000
        return None

    @property
    def is_complete(self) -> bool:
        """Check if recovery is fully complete."""
        return (
            self.status == RecoveryStatus.COMPLETED
            and self.indicators_warmed
            and self.orders_reconciled
        )


class PositionSnapshot(BaseModel):
    """Position state snapshot for cache persistence.

    Represents a point-in-time snapshot of a position stored in Redis cache.

    Attributes:
        instrument_id: Full instrument ID (e.g., BTCUSDT-PERP.BINANCE).
        side: Position side: LONG, SHORT, or FLAT.
        quantity: Position quantity (absolute value).
        avg_entry_price: Volume-weighted average entry price.
        unrealized_pnl: Current unrealized P&L.
        realized_pnl: Accumulated realized P&L.
        ts_opened: Timestamp position opened (nanoseconds).
        ts_last_updated: Timestamp of last update (nanoseconds).
    """

    instrument_id: str = Field(
        description="Full instrument ID (e.g., BTCUSDT-PERP.BINANCE)",
    )
    side: str = Field(
        description="Position side: LONG, SHORT, or FLAT",
    )
    quantity: Decimal = Field(
        ge=0,
        description="Position quantity (absolute value)",
    )
    avg_entry_price: Decimal = Field(
        gt=0,
        description="Volume-weighted average entry price",
    )
    unrealized_pnl: Decimal = Field(
        default=Decimal("0"),
        description="Current unrealized P&L",
    )
    realized_pnl: Decimal = Field(
        default=Decimal("0"),
        description="Accumulated realized P&L",
    )
    ts_opened: int = Field(
        description="Timestamp position opened (nanoseconds)",
    )
    ts_last_updated: int = Field(
        description="Timestamp of last update (nanoseconds)",
    )

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str) -> str:
        """Validate position side is valid."""
        valid_sides = {"LONG", "SHORT", "FLAT"}
        if v.upper() not in valid_sides:
            raise ValueError(f"Invalid position side: {v}. Must be one of {valid_sides}")
        return v.upper()

    @field_validator("ts_last_updated")
    @classmethod
    def validate_timestamps(cls, v: int, info: ValidationInfo) -> int:
        """Validate ts_opened <= ts_last_updated."""
        ts_opened = info.data.get("ts_opened")
        if ts_opened is not None and v < ts_opened:
            raise ValueError("ts_last_updated cannot be before ts_opened")
        return v

    model_config = {
        "json_encoders": {Decimal: str},
    }


class IndicatorState(BaseModel):
    """State of a single indicator for recovery.

    Used to optionally persist indicator state for faster recovery.

    Attributes:
        name: Indicator name (e.g., EMA-20).
        period: Indicator period.
        value: Current value.
        is_ready: Whether indicator is initialized.
        warmup_count: Number of warmup bars processed.
    """

    name: str = Field(description="Indicator name (e.g., EMA-20)")
    period: int = Field(ge=1, description="Indicator period")
    value: float | None = Field(default=None, description="Current value")
    is_ready: bool = Field(default=False, description="Indicator initialized")
    warmup_count: int = Field(default=0, ge=0, description="Warmup bar count")


class StrategySnapshot(BaseModel):
    """Strategy state snapshot for advanced recovery.

    Optional model for strategies that need to persist custom state.

    Attributes:
        strategy_id: Strategy identifier.
        indicator_states: State of all strategy indicators.
        custom_state: Strategy-specific custom state.
        pending_signals: Pending signal identifiers.
        ts_saved: Timestamp snapshot saved (nanoseconds).
    """

    strategy_id: str = Field(
        description="Strategy identifier",
    )
    indicator_states: list[IndicatorState] = Field(
        default_factory=list,
        description="State of all strategy indicators",
    )
    custom_state: dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific custom state",
    )
    pending_signals: list[str] = Field(
        default_factory=list,
        description="Pending signal identifiers",
    )
    ts_saved: int = Field(
        description="Timestamp snapshot saved (nanoseconds)",
    )
