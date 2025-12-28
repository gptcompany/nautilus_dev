# Spec 012: Circuit Breaker (Max Drawdown)

## Overview

Implement a circuit breaker that halts all trading when drawdown exceeds configured threshold. Prevents catastrophic losses.

## Problem Statement

Current system has no protection against runaway losses. If multiple strategies fail simultaneously or market conditions turn extreme, the entire account can be wiped out.

## Goals

1. **Real-time Drawdown Monitoring**: Track equity vs peak in real-time
2. **Circuit Breaker**: Halt trading when drawdown exceeds threshold
3. **Recovery Mode**: Gradual re-entry after drawdown recovery

## Requirements

### Functional Requirements

#### FR-001: Drawdown Calculation
- Track peak equity (high water mark)
- Calculate current drawdown: (peak - current) / peak * 100
- Update on every position change and periodic intervals

#### FR-002: Circuit Breaker Triggers
- **LEVEL 1** (Warning): Drawdown > 10% - Log warning, reduce position sizes by 50%
- **LEVEL 2** (Reducing): Drawdown > 15% - Close new entries, only exits allowed
- **LEVEL 3** (Halted): Drawdown > 20% - Close ALL positions, halt trading

#### FR-003: Recovery Mode
- After LEVEL 3 triggered, require manual reset OR
- Auto-recovery when drawdown recovers to < 10%
- Gradual position size increase (25% -> 50% -> 100%)

#### FR-004: Configuration
```python
class CircuitBreakerConfig(BaseModel):
    level1_drawdown_pct: Decimal = Decimal("0.10")  # 10%
    level2_drawdown_pct: Decimal = Decimal("0.15")  # 15%
    level3_drawdown_pct: Decimal = Decimal("0.20")  # 20%
    recovery_drawdown_pct: Decimal = Decimal("0.10")  # 10%
    auto_recovery: bool = False
    check_interval_secs: int = 60
```

### Non-Functional Requirements

#### NFR-001: Latency
- Drawdown check must complete within 1ms
- Circuit breaker activation within 100ms of threshold breach

#### NFR-002: Persistence
- Circuit breaker state must persist across restarts
- Publish state to monitoring (QuestDB)

## Technical Design

### Component: CircuitBreaker

```python
class CircuitBreakerState(Enum):
    ACTIVE = "active"
    WARNING = "warning"
    REDUCING = "reducing"
    HALTED = "halted"

class CircuitBreaker:
    """Global circuit breaker for drawdown protection."""

    def __init__(self, config: CircuitBreakerConfig, portfolio: Portfolio):
        self.config = config
        self.portfolio = portfolio
        self.peak_equity: Decimal = Decimal("0")
        self.state: CircuitBreakerState = CircuitBreakerState.ACTIVE

    def update(self) -> None:
        """Check drawdown and update state."""
        current_equity = self.portfolio.account().balance_total()
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        drawdown = (self.peak_equity - current_equity) / self.peak_equity
        self._update_state(drawdown)

    def can_open_position(self) -> bool:
        """Check if new positions are allowed."""
        return self.state in (CircuitBreakerState.ACTIVE, CircuitBreakerState.WARNING)

    def position_size_multiplier(self) -> Decimal:
        """Get position size adjustment based on state."""
        match self.state:
            case CircuitBreakerState.ACTIVE: return Decimal("1.0")
            case CircuitBreakerState.WARNING: return Decimal("0.5")
            case _: return Decimal("0.0")
```

### Integration with TradingNode

```python
# In strategy
def on_bar(self, bar: Bar) -> None:
    if not self.circuit_breaker.can_open_position():
        return  # Skip entry logic

    size = self.base_size * self.circuit_breaker.position_size_multiplier()
    # ... entry logic
```

## Monitoring Integration

### QuestDB Schema
```sql
CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    timestamp TIMESTAMP,
    trader_id SYMBOL,
    state SYMBOL,
    current_drawdown DOUBLE,
    peak_equity DOUBLE,
    current_equity DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY;
```

### Grafana Dashboard Panel
- Real-time drawdown gauge (green/yellow/red zones)
- State history timeline
- Alert on LEVEL 2+ trigger

## Testing Strategy

1. **Unit Tests**: Drawdown calculation, state transitions
2. **Integration Tests**: Multi-strategy drawdown aggregation
3. **Backtest Validation**: Historical drawdown scenarios

## Dependencies

- Spec 005 (QuestDB Monitoring)
- Spec 011 (Stop-Loss for position closure)

## Success Metrics

- Zero account wipeouts (drawdown > 50%)
- Circuit breaker activations logged and alerted
- Recovery time tracked
