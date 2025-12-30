# Data Model: Position Recovery (Spec 017)

**Date**: 2025-12-30
**Status**: Complete

## Entity Relationship Diagram

```
┌─────────────────────┐       ┌─────────────────────┐
│   RecoveryConfig    │       │  PositionSnapshot   │
├─────────────────────┤       ├─────────────────────┤
│ trader_id           │       │ instrument_id       │
│ recovery_enabled    │       │ side                │
│ warmup_lookback_days│◄──────│ quantity            │
│ startup_delay_secs  │       │ avg_entry_price     │
│ max_recovery_time   │       │ unrealized_pnl      │
└─────────────────────┘       │ realized_pnl        │
         │                    │ ts_opened           │
         │                    │ ts_last_updated     │
         ▼                    └─────────────────────┘
┌─────────────────────┐                │
│   RecoveryState     │                │
├─────────────────────┤                │
│ status              │◄───────────────┘
│ positions_recovered │
│ indicators_warmed   │
│ orders_reconciled   │
│ ts_started          │
│ ts_completed        │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  StrategySnapshot   │
├─────────────────────┤
│ strategy_id         │
│ indicator_states    │
│ custom_state        │
│ pending_signals     │
│ ts_saved            │
└─────────────────────┘
```

---

## Entities

### RecoveryConfig

Configuration for position recovery behavior.

```python
from pydantic import BaseModel, Field

class RecoveryConfig(BaseModel):
    """Configuration for position recovery on TradingNode restart."""

    trader_id: str = Field(
        description="Unique identifier for the trader instance"
    )
    recovery_enabled: bool = Field(
        default=True,
        description="Enable position recovery from cache"
    )
    warmup_lookback_days: int = Field(
        default=2,
        ge=1,
        le=30,
        description="Days of historical data for indicator warmup"
    )
    startup_delay_secs: float = Field(
        default=10.0,
        ge=5.0,
        le=60.0,
        description="Delay before reconciliation starts"
    )
    max_recovery_time_secs: float = Field(
        default=30.0,
        ge=10.0,
        le=120.0,
        description="Maximum time allowed for full recovery"
    )
    claim_external_positions: bool = Field(
        default=True,
        description="Claim positions opened outside NautilusTrader"
    )
```

### PositionSnapshot

Snapshot of position state stored in Redis cache.

```python
from decimal import Decimal
from pydantic import BaseModel, Field

class PositionSnapshot(BaseModel):
    """Position state snapshot for cache persistence."""

    instrument_id: str = Field(
        description="Full instrument ID (e.g., BTCUSDT-PERP.BINANCE)"
    )
    side: str = Field(
        description="Position side: LONG, SHORT, or FLAT"
    )
    quantity: Decimal = Field(
        ge=0,
        description="Position quantity (absolute value)"
    )
    avg_entry_price: Decimal = Field(
        gt=0,
        description="Volume-weighted average entry price"
    )
    unrealized_pnl: Decimal = Field(
        default=Decimal("0"),
        description="Current unrealized P&L"
    )
    realized_pnl: Decimal = Field(
        default=Decimal("0"),
        description="Accumulated realized P&L"
    )
    ts_opened: int = Field(
        description="Timestamp position opened (nanoseconds)"
    )
    ts_last_updated: int = Field(
        description="Timestamp of last update (nanoseconds)"
    )

    class Config:
        json_encoders = {Decimal: str}
```

### RecoveryState

Tracks the current state of the recovery process.

```python
from enum import Enum
from pydantic import BaseModel, Field

class RecoveryStatus(str, Enum):
    """Status of the recovery process."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class RecoveryState(BaseModel):
    """Current state of the recovery process."""

    status: RecoveryStatus = Field(
        default=RecoveryStatus.PENDING,
        description="Current recovery status"
    )
    positions_recovered: int = Field(
        default=0,
        ge=0,
        description="Number of positions successfully recovered"
    )
    indicators_warmed: bool = Field(
        default=False,
        description="Whether indicators have completed warmup"
    )
    orders_reconciled: bool = Field(
        default=False,
        description="Whether order reconciliation completed (Spec 016)"
    )
    ts_started: int | None = Field(
        default=None,
        description="Timestamp recovery started (nanoseconds)"
    )
    ts_completed: int | None = Field(
        default=None,
        description="Timestamp recovery completed (nanoseconds)"
    )
    error_message: str | None = Field(
        default=None,
        description="Error message if recovery failed"
    )

    @property
    def recovery_duration_ms(self) -> float | None:
        """Calculate recovery duration in milliseconds."""
        if self.ts_started and self.ts_completed:
            return (self.ts_completed - self.ts_started) / 1_000_000
        return None
```

### StrategySnapshot

Optional strategy-specific state for advanced recovery.

```python
from typing import Any
from pydantic import BaseModel, Field

class IndicatorState(BaseModel):
    """State of a single indicator for recovery."""

    name: str = Field(description="Indicator name (e.g., EMA-20)")
    period: int = Field(ge=1, description="Indicator period")
    value: float | None = Field(default=None, description="Current value")
    is_ready: bool = Field(default=False, description="Indicator initialized")
    warmup_count: int = Field(default=0, ge=0, description="Warmup bar count")

class StrategySnapshot(BaseModel):
    """Strategy state snapshot for advanced recovery."""

    strategy_id: str = Field(
        description="Strategy identifier"
    )
    indicator_states: list[IndicatorState] = Field(
        default_factory=list,
        description="State of all strategy indicators"
    )
    custom_state: dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific custom state"
    )
    pending_signals: list[str] = Field(
        default_factory=list,
        description="Pending signal identifiers"
    )
    ts_saved: int = Field(
        description="Timestamp snapshot saved (nanoseconds)"
    )
```

---

## Redis Key Schema

Extends Spec 018 key schema for position recovery:

```
# Base namespace
nautilus:{trader_id}:

# Position snapshots (from Spec 018)
nautilus:{trader_id}:positions:{venue}:{instrument_id}

# Recovery state
nautilus:{trader_id}:recovery:state

# Strategy snapshots (optional, advanced)
nautilus:{trader_id}:recovery:strategy:{strategy_id}

# Recovery metrics
nautilus:{trader_id}:recovery:metrics
```

---

## Validation Rules

### PositionSnapshot

| Field | Rule | Error Message |
|-------|------|---------------|
| quantity | >= 0 | "Quantity cannot be negative" |
| avg_entry_price | > 0 | "Entry price must be positive" |
| side | in [LONG, SHORT, FLAT] | "Invalid position side" |
| ts_opened | <= ts_last_updated | "Opened time cannot be after last update" |

### RecoveryConfig

| Field | Rule | Error Message |
|-------|------|---------------|
| startup_delay_secs | >= 5.0 | "Startup delay must be at least 5 seconds" |
| max_recovery_time_secs | > startup_delay_secs | "Max recovery time must exceed startup delay" |
| warmup_lookback_days | 1-30 | "Warmup lookback must be 1-30 days" |

---

## State Transitions

### RecoveryStatus State Machine

```
PENDING ──────────► IN_PROGRESS
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
     COMPLETED       FAILED        TIMEOUT
```

**Transitions**:
- `PENDING → IN_PROGRESS`: Recovery process starts
- `IN_PROGRESS → COMPLETED`: All positions recovered, indicators warmed
- `IN_PROGRESS → FAILED`: Unrecoverable error occurred
- `IN_PROGRESS → TIMEOUT`: max_recovery_time_secs exceeded
