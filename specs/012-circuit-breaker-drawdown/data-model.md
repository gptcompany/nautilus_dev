# Data Model: Circuit Breaker (Max Drawdown)

**Created**: 2025-12-28
**Spec**: 012-circuit-breaker-drawdown

## Entities

### CircuitBreakerState (Enum)

State machine states for circuit breaker.

| Value | Description | Position Allowed | Size Multiplier |
|-------|-------------|------------------|-----------------|
| ACTIVE | Normal trading | Yes | 1.0 (100%) |
| WARNING | Drawdown > level1 | Yes | 0.5 (50%) |
| REDUCING | Drawdown > level2 | No (exits only) | 0.0 |
| HALTED | Drawdown > level3 | No | 0.0 |

**State Transitions**:
```
ACTIVE ──▶ WARNING ──▶ REDUCING ──▶ HALTED
   ▲                                   │
   └───────── (recovery) ◀─────────────┘
```

---

### CircuitBreakerConfig

Configuration for circuit breaker thresholds and behavior.

| Field | Type | Default | Validation | Description |
|-------|------|---------|------------|-------------|
| level1_drawdown_pct | Decimal | 0.10 | (0, 1) | WARNING threshold |
| level2_drawdown_pct | Decimal | 0.15 | (0, 1) | REDUCING threshold |
| level3_drawdown_pct | Decimal | 0.20 | (0, 1) | HALTED threshold |
| recovery_drawdown_pct | Decimal | 0.10 | (0, 1) | Return to ACTIVE |
| auto_recovery | bool | False | - | Auto-reset after HALTED |
| check_interval_secs | int | 60 | > 0 | Timer interval |
| warning_size_multiplier | Decimal | 0.5 | [0, 1] | Size factor in WARNING |
| reducing_size_multiplier | Decimal | 0.0 | [0, 1] | Size factor in REDUCING |

**Validation Rules**:
- `level1 < level2 < level3` (thresholds must increase)
- `recovery_drawdown_pct < level1_drawdown_pct` (hysteresis)
- All percentages in range (0, 1)

---

### CircuitBreaker

Core circuit breaker logic.

| Property | Type | Description |
|----------|------|-------------|
| config | CircuitBreakerConfig | Immutable configuration |
| state | CircuitBreakerState | Current state |
| peak_equity | Decimal | High water mark |
| current_equity | Decimal | Last known equity |
| current_drawdown | Decimal | Calculated drawdown |
| last_check | datetime | Timestamp of last update |

| Method | Signature | Description |
|--------|-----------|-------------|
| update | () → None | Recalculate drawdown, update state |
| can_open_position | () → bool | Check if entries allowed |
| position_size_multiplier | () → Decimal | Get size adjustment factor |
| reset | () → None | Manual reset (if !auto_recovery) |

---

### CircuitBreakerMetric

QuestDB record for monitoring.

| Column | Type | Description |
|--------|------|-------------|
| timestamp | TIMESTAMP | Event timestamp |
| trader_id | SYMBOL | Trader identifier |
| state | SYMBOL | CircuitBreakerState value |
| current_drawdown | DOUBLE | Drawdown as decimal |
| peak_equity | DOUBLE | High water mark |
| current_equity | DOUBLE | Current equity value |

---

## Relationships

```
┌─────────────────────┐
│ CircuitBreakerConfig │
└──────────┬──────────┘
           │ 1:1
           ▼
┌─────────────────────┐
│   CircuitBreaker    │
│                     │
│ - state: State      │
│ - peak_equity       │
│ - current_equity    │
└──────────┬──────────┘
           │ 1:N (events)
           ▼
┌─────────────────────┐
│ CircuitBreakerMetric │
│    (QuestDB row)    │
└─────────────────────┘
```

---

## State Machine Logic

### Drawdown Calculation

```python
drawdown = (peak_equity - current_equity) / peak_equity
# Result is in range [0, 1+] where 0.20 = 20% drawdown
```

### Transition Logic

```python
def _update_state(self, drawdown: Decimal) -> None:
    """Update state based on current drawdown."""
    if drawdown >= self.config.level3_drawdown_pct:
        self.state = CircuitBreakerState.HALTED
    elif drawdown >= self.config.level2_drawdown_pct:
        self.state = CircuitBreakerState.REDUCING
    elif drawdown >= self.config.level1_drawdown_pct:
        self.state = CircuitBreakerState.WARNING
    elif self.state == CircuitBreakerState.HALTED:
        # Recovery from HALTED requires manual reset OR auto_recovery
        if self.config.auto_recovery and drawdown <= self.config.recovery_drawdown_pct:
            self.state = CircuitBreakerState.ACTIVE
    else:
        # Recovery from WARNING/REDUCING
        if drawdown <= self.config.recovery_drawdown_pct:
            self.state = CircuitBreakerState.ACTIVE
```

---

## Validation Rules

### Config Validation

1. **Threshold Ordering**:
   ```python
   level1 < level2 < level3
   ```

2. **Recovery Hysteresis**:
   ```python
   recovery < level1  # Prevent oscillation
   ```

3. **Multiplier Range**:
   ```python
   0 <= warning_size_multiplier <= 1
   0 <= reducing_size_multiplier <= 1
   ```

### Runtime Validation

1. **Peak Tracking**:
   ```python
   peak_equity = max(peak_equity, current_equity)  # Never decreases
   ```

2. **Drawdown Range**:
   ```python
   drawdown >= 0  # Can exceed 1.0 if equity goes negative
   ```

3. **State Consistency**:
   ```python
   # If HALTED and !auto_recovery, require explicit reset()
   ```
