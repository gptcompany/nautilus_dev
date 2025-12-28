# Data Model: Daily Loss Limits (Spec 013)

**Version**: 1.0
**Last Updated**: 2025-12-28

## Entities

### DailyLossConfig

Configuration for daily PnL tracking and loss limits.

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| `daily_loss_limit` | `Decimal` | Yes | `1000` | `> 0` | Absolute daily loss limit (USD) |
| `daily_loss_pct` | `Decimal \| None` | No | `None` | `0 < x < 1` | Alternative: % of starting capital |
| `reset_time_utc` | `str` | Yes | `"00:00"` | `HH:MM` format | Daily reset time in UTC |
| `per_strategy` | `bool` | Yes | `False` | - | Track per-strategy vs global |
| `close_positions_on_limit` | `bool` | Yes | `True` | - | Auto-close positions when limit hit |
| `warning_threshold_pct` | `Decimal` | Yes | `0.5` | `0 < x < 1` | Alert at this % of limit (50%) |

**Validation Rules**:
- At least one of `daily_loss_limit` or `daily_loss_pct` must be set
- `daily_loss_pct` takes precedence if both set
- `reset_time_utc` must be valid HH:MM format

---

### DailyPnLState

Runtime state for daily PnL tracking.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `daily_realized` | `Decimal` | `0` | Realized PnL today |
| `daily_unrealized` | `Decimal` | `0` | Current unrealized PnL |
| `total_daily_pnl` | `Decimal` | `0` | realized + unrealized |
| `day_start` | `datetime` | - | Start of current trading day |
| `starting_equity` | `Decimal` | `0` | Equity at day start (for % calc) |
| `limit_triggered` | `bool` | `False` | Whether limit was hit today |
| `trigger_time` | `datetime \| None` | `None` | When limit was triggered |

**State Transitions**:
```
TRACKING → LIMIT_TRIGGERED (when daily_loss > limit)
LIMIT_TRIGGERED → TRACKING (on daily reset)
```

---

### DailyPnLRecord (QuestDB)

Historical record of daily PnL for analysis.

| Column | Type | Index | Description |
|--------|------|-------|-------------|
| `timestamp` | `TIMESTAMP` | PARTITION BY DAY | Record timestamp |
| `trader_id` | `SYMBOL` | Yes | Trader identifier |
| `strategy_id` | `SYMBOL` | Yes | Strategy (if per_strategy) |
| `realized_pnl` | `DOUBLE` | No | Realized PnL at timestamp |
| `unrealized_pnl` | `DOUBLE` | No | Unrealized PnL at timestamp |
| `total_pnl` | `DOUBLE` | No | Total daily PnL |
| `limit_triggered` | `BOOLEAN` | No | Whether limit was active |
| `limit_value` | `DOUBLE` | No | Configured limit |

**SQL Schema**:
```sql
CREATE TABLE IF NOT EXISTS daily_pnl (
    timestamp TIMESTAMP,
    trader_id SYMBOL,
    strategy_id SYMBOL,
    realized_pnl DOUBLE,
    unrealized_pnl DOUBLE,
    total_pnl DOUBLE,
    limit_triggered BOOLEAN,
    limit_value DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

---

## Relationships

```
┌─────────────────────┐
│  DailyLossConfig    │
│  (immutable)        │
└─────────┬───────────┘
          │ configures
          ▼
┌─────────────────────┐     writes to    ┌─────────────────────┐
│  DailyPnLTracker    │ ───────────────► │  DailyPnLRecord     │
│  (runtime)          │                  │  (QuestDB)          │
└─────────┬───────────┘                  └─────────────────────┘
          │ maintains
          ▼
┌─────────────────────┐
│  DailyPnLState      │
│  (mutable)          │
└─────────────────────┘
```

---

## Value Objects

### PnLLimit

Represents a daily loss limit (either absolute or percentage).

```python
class PnLLimit:
    """Immutable daily loss limit."""

    absolute: Decimal | None = None  # e.g., 1000 USD
    percentage: Decimal | None = None  # e.g., 0.02 = 2%

    def exceeded(self, loss: Decimal, starting_equity: Decimal) -> bool:
        """Check if loss exceeds limit."""
        if self.percentage is not None:
            return loss > starting_equity * self.percentage
        return loss > self.absolute
```

---

## Invariants

1. **Daily PnL Accuracy**: `total_daily_pnl == daily_realized + daily_unrealized`
2. **Limit Check**: `limit_triggered == (total_daily_pnl < -effective_limit)`
3. **Reset Consistency**: After reset, `daily_realized == 0 AND limit_triggered == False`
4. **Monotonic Realized**: Realized PnL only changes on PositionClosed events
5. **Starting Equity**: Set once at day start, immutable until next reset
