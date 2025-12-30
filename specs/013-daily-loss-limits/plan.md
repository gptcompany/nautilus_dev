# Implementation Plan: Daily Loss Limits

**Feature Branch**: `013-daily-loss-limits`
**Created**: 2025-12-28
**Status**: Ready for Implementation
**Spec Reference**: `specs/013-daily-loss-limits/spec.md`

## Architecture Overview

Daily Loss Limits provides single-day protection as a complement to Circuit Breaker's total drawdown protection. Tracks realized + unrealized PnL and enforces configurable daily limits with automatic position closure.

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                         Strategy                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    RiskManager                           │    │
│  │  ┌─────────────────┐  ┌─────────────────┐               │    │
│  │  │ CircuitBreaker  │  │ DailyPnLTracker │ ◄── NEW      │    │
│  │  │ (Total DD)      │  │ (Daily Loss)    │               │    │
│  │  └─────────────────┘  └─────────────────┘               │    │
│  │                              │                           │    │
│  │                              ▼                           │    │
│  │                       ┌─────────────┐                    │    │
│  │                       │  QuestDB    │                    │    │
│  │                       │ daily_pnl   │                    │    │
│  │                       └─────────────┘                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
risk/
├── __init__.py              # Add DailyPnLTracker, DailyLossConfig exports
├── daily_loss_config.py     # NEW: Pydantic config model
├── daily_pnl_tracker.py     # NEW: Core tracker implementation
├── manager.py               # MODIFY: Add daily_tracker integration
├── circuit_breaker.py       # EXISTING: Drawdown protection
└── config.py                # EXISTING: RiskConfig

tests/
├── test_daily_loss_config.py      # NEW: Config validation tests
├── test_daily_pnl_tracker.py      # NEW: Tracker unit tests
└── integration/
    └── test_daily_limits_backtest.py  # NEW: BacktestNode integration
```

## Technical Decisions

### Decision 1: PnL Tracking Method

**Options Considered**:
1. **Option A**: Track from PositionClosed events only (realized)
   - Pros: Simple, accurate, no price lookups
   - Cons: Unrealized losses not captured until close
2. **Option B**: Track realized + unrealized continuously
   - Pros: Real-time total PnL, catches unrealized drawdowns
   - Cons: Requires price lookups, more complex

**Selected**: Option B

**Rationale**: Daily loss limits should include unrealized PnL to prevent holding large losing positions. PositionClosed provides realized, portfolio.unrealized_pnls() provides unrealized.

---

### Decision 2: Reset Mechanism

**Options Considered**:
1. **Option A**: Check time on every bar
   - Pros: Simple, no timer setup
   - Cons: May miss exact reset time, inefficient
2. **Option B**: Use clock.set_timer() for scheduled reset
   - Pros: Exact timing, efficient, NautilusTrader-native
   - Cons: Requires timer management

**Selected**: Option B

**Rationale**: NautilusTrader provides native timer support via clock.set_timer(). More accurate and efficient than checking on every bar.

---

### Decision 3: Position Closure on Limit

**Options Considered**:
1. **Option A**: Block new entries only
   - Pros: Allows recovery if unrealized reverses
   - Cons: May lock in larger losses
2. **Option B**: Close all positions immediately
   - Pros: Stops bleeding, known max loss
   - Cons: May lock in losses at worst time
3. **Option C**: Configurable (default: close)
   - Pros: Flexibility for different strategies
   - Cons: Slightly more complex config

**Selected**: Option C

**Rationale**: Different strategies may prefer different behavior. Default to closing for safety, but allow override via `close_positions_on_limit=False`.

---

### Decision 4: Integration with RiskManager

**Options Considered**:
1. **Option A**: Standalone component (strategy calls directly)
   - Pros: Simple, independent
   - Cons: Duplication of event routing logic
2. **Option B**: Integrated into RiskManager.handle_event()
   - Pros: Single event routing point, consistent API
   - Cons: Tighter coupling

**Selected**: Option B

**Rationale**: RiskManager already routes PositionOpened/Closed/Changed. Adding daily_tracker follows established pattern. Optional integration (daily_tracker=None skips).

---

## Implementation Strategy

### Phase 1: Configuration & Models

**Goal**: Define DailyLossConfig with validation

**Deliverables**:
- [x] `risk/daily_loss_config.py` - Config model
- [ ] `tests/test_daily_loss_config.py` - Validation tests

**Dependencies**: None

---

### Phase 2: Core Tracker

**Goal**: Implement DailyPnLTracker with PnL tracking and limit enforcement

**Deliverables**:
- [ ] `risk/daily_pnl_tracker.py` - Core implementation
- [ ] `tests/test_daily_pnl_tracker.py` - Unit tests
- [ ] Update `risk/__init__.py` - Exports

**Dependencies**: Phase 1

---

### Phase 3: RiskManager Integration

**Goal**: Integrate tracker with existing RiskManager

**Deliverables**:
- [ ] Update `risk/manager.py` - Add daily_tracker parameter
- [ ] Update existing tests for integration

**Dependencies**: Phase 2

---

### Phase 4: QuestDB Monitoring

**Goal**: Publish daily PnL to QuestDB for dashboards

**Deliverables**:
- [ ] Add QuestDB writer to tracker
- [ ] Create daily_pnl table schema
- [ ] Add Grafana dashboard panel

**Dependencies**: Phase 3, Spec 005 (QuestDB)

---

### Phase 5: Integration Testing

**Goal**: Validate with BacktestNode

**Deliverables**:
- [ ] `tests/integration/test_daily_limits_backtest.py`
- [ ] Multi-strategy daily limit scenarios
- [ ] Reset at midnight edge cases

**Dependencies**: Phase 4

---

## File Structure

```
risk/
├── __init__.py              # Add: DailyLossConfig, DailyPnLTracker
├── daily_loss_config.py     # NEW: Config validation
├── daily_pnl_tracker.py     # NEW: Core tracker
├── manager.py               # MODIFY: daily_tracker param
├── circuit_breaker.py       # EXISTING
├── circuit_breaker_config.py
├── circuit_breaker_state.py
└── config.py

tests/
├── test_daily_loss_config.py     # NEW
├── test_daily_pnl_tracker.py     # NEW
└── integration/
    └── test_daily_limits_backtest.py  # NEW
```

## API Design

### Public Interface

```python
class DailyPnLTracker:
    """Daily PnL tracking with loss limit enforcement."""

    def __init__(
        self,
        config: DailyLossConfig,
        strategy: Strategy,
    ) -> None: ...

    @property
    def daily_realized(self) -> Decimal: ...
    @property
    def daily_unrealized(self) -> Decimal: ...
    @property
    def total_daily_pnl(self) -> Decimal: ...
    @property
    def limit_triggered(self) -> bool: ...

    def handle_event(self, event: Event) -> None: ...
    def check_limit(self) -> bool: ...
    def can_trade(self) -> bool: ...
    def reset(self) -> None: ...
```

### Configuration

```python
class DailyLossConfig(BaseModel):
    daily_loss_limit: Decimal = Decimal("1000")
    daily_loss_pct: Decimal | None = None
    reset_time_utc: str = "00:00"
    per_strategy: bool = False
    close_positions_on_limit: bool = True
    warning_threshold_pct: Decimal = Decimal("0.5")
```

## Testing Strategy

### Unit Tests
- [x] Config validation (reset_time format, limits > 0)
- [ ] PnL calculation accuracy
- [ ] Limit trigger logic
- [ ] Reset behavior
- [ ] can_trade() state

### Integration Tests
- [ ] BacktestNode with daily loss trigger
- [ ] Position closure on limit
- [ ] Multi-strategy with per_strategy=True
- [ ] Reset at midnight (00:00 UTC)

### Edge Cases
- [ ] Positions spanning midnight
- [ ] Timezone handling (always UTC)
- [ ] Starting equity = 0 (startup)
- [ ] Rapid losses (multiple positions closing)

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Unrealized PnL calculation error | High | Low | Use portfolio.unrealized_pnls() |
| Timer drift across days | Medium | Low | Re-sync timer on reset |
| Position closure fails | High | Low | Log and alert, retry mechanism |
| QuestDB unavailable | Low | Low | Continue tracking, buffer writes |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.222.0
- QuestDB (for monitoring - optional)

### Internal Dependencies
- Spec 005 (QuestDB Monitoring) - for daily_pnl table
- Spec 011 (Stop-Loss) - for position closure pattern
- Spec 012 (Circuit Breaker) - for integration pattern

## Acceptance Criteria

- [x] research.md complete with all clarifications resolved
- [x] data-model.md with entity definitions
- [x] contracts/ with interface definitions
- [x] quickstart.md with usage examples
- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Performance: limit check < 1ms
