# Spec 013: Daily Loss Limits

## Overview

Implement daily PnL tracking with automatic trading halt when daily loss limit is exceeded.

## Problem Statement

Circuit breaker (Spec 012) protects against total drawdown, but a strategy can lose significant amounts in a single day before triggering. Daily loss limits provide faster protection.

## Goals

1. **Daily PnL Tracking**: Track realized + unrealized PnL per day
2. **Daily Loss Limit**: Halt trading when daily loss exceeds threshold
3. **Daily Reset**: Automatic reset at configurable time (e.g., 00:00 UTC)

## Requirements

### Functional Requirements

#### FR-001: Daily PnL Calculation
- Track realized PnL (closed positions)
- Track unrealized PnL (open positions mark-to-market)
- Total daily PnL = realized + unrealized

#### FR-002: Daily Loss Limit
- Configurable daily loss limit (absolute or percentage)
- When exceeded: close all positions, halt new entries
- Log and alert on trigger

#### FR-003: Daily Reset
- Reset daily PnL counter at configurable time
- Default: 00:00 UTC
- Option to use exchange trading day (e.g., Binance resets at 00:00 UTC)

#### FR-004: Per-Strategy Limits
- Option for per-strategy daily limits
- Global daily limit across all strategies

#### FR-005: Configuration
```python
class DailyLossConfig(BaseModel):
    daily_loss_limit: Decimal = Decimal("1000")  # Absolute USD
    daily_loss_pct: Decimal | None = None  # Alternative: % of starting capital
    reset_time_utc: str = "00:00"
    per_strategy: bool = False
    close_positions_on_limit: bool = True
```

### Non-Functional Requirements

#### NFR-001: Accuracy
- PnL tracking must be accurate to 0.01 USD
- No missed trades or double counting

#### NFR-002: Persistence
- Daily PnL must persist across restarts within the same day
- Historical daily PnL stored for analysis

## Technical Design

### Component: DailyPnLTracker

```python
class DailyPnLTracker:
    """Tracks daily PnL and enforces daily loss limits."""

    def __init__(self, config: DailyLossConfig, portfolio: Portfolio):
        self.config = config
        self.portfolio = portfolio
        self.daily_realized: Decimal = Decimal("0")
        self.day_start: datetime = self._get_day_start()
        self.limit_triggered: bool = False

    def on_position_closed(self, event: PositionClosed) -> None:
        """Update realized PnL on position close."""
        self.daily_realized += event.realized_pnl

    def check_limit(self) -> bool:
        """Check if daily loss limit exceeded."""
        total_pnl = self.daily_realized + self._unrealized_pnl()
        if total_pnl < -self.config.daily_loss_limit:
            self.limit_triggered = True
            self._trigger_limit()
            return True
        return False

    def _reset_if_new_day(self) -> None:
        """Reset counters if new trading day."""
        current_day_start = self._get_day_start()
        if current_day_start > self.day_start:
            self.daily_realized = Decimal("0")
            self.day_start = current_day_start
            self.limit_triggered = False
```

### Integration Pattern

```python
class MyStrategy(Strategy):
    def on_bar(self, bar: Bar) -> None:
        # Check daily limit before any action
        self.daily_tracker._reset_if_new_day()
        if self.daily_tracker.limit_triggered:
            return

        # ... trading logic

    def on_event(self, event: Event) -> None:
        if isinstance(event, PositionClosed):
            self.daily_tracker.on_position_closed(event)
            self.daily_tracker.check_limit()
```

## Monitoring Integration

### QuestDB Schema
```sql
CREATE TABLE IF NOT EXISTS daily_pnl (
    timestamp TIMESTAMP,
    trader_id SYMBOL,
    strategy_id SYMBOL,
    realized_pnl DOUBLE,
    unrealized_pnl DOUBLE,
    total_pnl DOUBLE,
    limit_triggered BOOLEAN
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

### Alerts
- Alert when daily PnL < -50% of limit (warning)
- Alert when limit triggered
- Daily summary at reset time

## Testing Strategy

1. **Unit Tests**: PnL calculation, day reset logic
2. **Integration Tests**: Multi-position scenarios
3. **Edge Cases**: Positions spanning midnight, timezone handling

## Dependencies

- Spec 005 (QuestDB Monitoring)
- Spec 011 (Stop-Loss for position closure on limit)

## Success Metrics

- Daily loss never exceeds limit by more than 10% (slippage allowance)
- 100% of limit triggers logged and alerted
- Accurate daily PnL reports
