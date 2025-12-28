# Implementation Plan: Circuit Breaker (Max Drawdown)

**Feature Branch**: `012-circuit-breaker-drawdown`
**Created**: 2025-12-28
**Status**: Ready for Implementation
**Spec Reference**: `specs/012-circuit-breaker-drawdown/spec.md`

## Architecture Overview

The Circuit Breaker provides global drawdown protection across all strategies running in a TradingNode. It monitors portfolio equity in real-time and enforces graduated risk reduction as drawdown increases.

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                         TradingNode                             │
│  ┌─────────────┐     ┌─────────────────┐     ┌──────────────┐  │
│  │  Strategy 1 │────▶│                 │────▶│ QuestDB      │  │
│  └─────────────┘     │  CircuitBreaker │     │ (Monitoring) │  │
│  ┌─────────────┐     │                 │     └──────────────┘  │
│  │  Strategy 2 │────▶│ - Equity Track  │                       │
│  └─────────────┘     │ - State Machine │     ┌──────────────┐  │
│  ┌─────────────┐     │ - Action Exec   │────▶│ Grafana      │  │
│  │  RiskManager│◀───│                 │     │ (Dashboard)  │  │
│  │  (Spec 011) │     └─────────────────┘     └──────────────┘  │
│  └─────────────┘              │                                │
│         ▲                     ▼                                │
│         │            ┌─────────────────┐                       │
│         └────────────│    Portfolio    │                       │
│                      │   account()     │                       │
│                      └─────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌──────────────────────────────────────────┐
│           CircuitBreaker                 │
├──────────────────────────────────────────┤
│ State Machine:                           │
│   ACTIVE ─▶ WARNING ─▶ REDUCING ─▶ HALTED│
│     ▲                                 │  │
│     └─────── (recovery) ◀─────────────┘  │
├──────────────────────────────────────────┤
│ Properties:                              │
│   - peak_equity: Decimal                 │
│   - state: CircuitBreakerState           │
│   - last_check: datetime                 │
├──────────────────────────────────────────┤
│ Methods:                                 │
│   + update() → None                      │
│   + can_open_position() → bool           │
│   + position_size_multiplier() → Decimal │
│   + reset() → None (manual recovery)     │
└──────────────────────────────────────────┘
```

## Technical Decisions

### Decision 1: Equity Source

**Options Considered**:
1. **Portfolio.account().balance_total()**
   - Pros: Simple, direct access to total account value
   - Cons: May not include unrealized PnL depending on account type
2. **Portfolio.net_exposures() + balance**
   - Pros: Includes unrealized PnL from open positions
   - Cons: More complex calculation

**Selected**: Option 1 (balance_total)

**Rationale**: For circuit breaker purposes, we want the most liquid equity measure. Unrealized PnL can be considered via position-level checks in RiskManager (Spec 011). The balance_total is sufficient for high-level drawdown protection.

---

### Decision 2: Integration Point

**Options Considered**:
1. **Standalone Actor** - Independent actor that subscribes to account events
   - Pros: Decoupled from strategies, single source of truth
   - Cons: Requires message bus coordination for position blocking
2. **Strategy Mixin** - Each strategy has its own circuit breaker reference
   - Pros: Tight integration, direct access to strategy methods
   - Cons: State synchronization across strategies
3. **Controller Integration** - Part of TradingNode controller
   - Pros: Natural fit for global state, existing lifecycle management
   - Cons: Requires controller refactoring

**Selected**: Option 1 (Standalone Actor)

**Rationale**: A standalone `CircuitBreakerActor` can subscribe to account events via MessageBus and maintain global state. Strategies query it before order submission. This is the cleanest separation and aligns with NautilusTrader's event-driven architecture.

---

### Decision 3: State Persistence

**Options Considered**:
1. **In-memory only** (MVP)
   - Pros: Simple, fast
   - Cons: State lost on restart
2. **Redis persistence**
   - Pros: Fast, survives restarts
   - Cons: Additional dependency
3. **QuestDB only** (for monitoring, not recovery)
   - Pros: Already integrated, useful for dashboards
   - Cons: Not suitable for fast state recovery

**Selected**: Option 1 (In-memory) for MVP, with QuestDB logging for monitoring

**Rationale**: For backtest scope, in-memory is sufficient. Live trading can add Redis persistence as a Phase 2 enhancement. QuestDB is used for monitoring/alerting only.

---

### Decision 4: Position Closure on HALTED

**Options Considered**:
1. **Automatic closure** - CircuitBreaker closes all positions when HALTED
   - Pros: Maximum protection
   - Cons: Can cause slippage in volatile markets
2. **Block-only** - Only prevent new entries, manual closure required
   - Pros: Allows trader discretion
   - Cons: Positions remain at risk

**Selected**: Option 2 (Block-only) for MVP

**Rationale**: Automatic closure in volatile markets can lock in losses. Better to block new entries and alert the trader. Automatic closure can be a configurable option in Phase 2.

---

## Implementation Strategy

### Phase 1: Core Implementation

**Goal**: CircuitBreaker state machine with equity monitoring

**Deliverables**:
- [ ] `CircuitBreakerState` enum (ACTIVE, WARNING, REDUCING, HALTED)
- [ ] `CircuitBreakerConfig` Pydantic model
- [ ] `CircuitBreaker` class with update() and state transitions
- [ ] Unit tests for state machine logic
- [ ] Unit tests for drawdown calculations

**Dependencies**: None

---

### Phase 2: Actor Integration

**Goal**: CircuitBreakerActor that integrates with TradingNode

**Deliverables**:
- [ ] `CircuitBreakerActor` extending Actor
- [ ] Subscribe to AccountState events
- [ ] Periodic check via timer
- [ ] Integration with RiskManager (Spec 011)
- [ ] Integration tests with BacktestNode

**Dependencies**: Phase 1, Spec 011

---

### Phase 3: Monitoring & Alerting

**Goal**: QuestDB metrics and Grafana dashboard

**Deliverables**:
- [ ] QuestDB schema: `circuit_breaker_state` table
- [ ] Metrics collector for state changes
- [ ] Grafana dashboard panel: drawdown gauge
- [ ] Grafana alert: LEVEL 2+ trigger notification

**Dependencies**: Phase 2, Spec 005 (QuestDB/Grafana)

---

## File Structure

```
risk/
├── __init__.py
├── circuit_breaker.py        # CircuitBreaker + CircuitBreakerActor
├── circuit_breaker_config.py # CircuitBreakerConfig model
├── circuit_breaker_state.py  # CircuitBreakerState enum
└── integration.py            # Integration with RiskManager

monitoring/
├── schemas/
│   └── circuit_breaker_state.sql   # QuestDB schema
├── collectors/
│   └── circuit_breaker.py          # CircuitBreaker metrics collector
└── grafana/
    └── dashboards/
        └── circuit_breaker.json    # Grafana dashboard

tests/
├── test_circuit_breaker.py         # Unit tests
├── test_circuit_breaker_config.py  # Config validation tests
└── integration/
    └── test_circuit_breaker_backtest.py  # BacktestNode integration
```

## API Design

### Public Interface

```python
from enum import Enum
from decimal import Decimal
from nautilus_trader.common.actor import Actor
from nautilus_trader.model.events import AccountState


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    ACTIVE = "active"      # Normal trading
    WARNING = "warning"    # Drawdown > level1 (10%)
    REDUCING = "reducing"  # Drawdown > level2 (15%)
    HALTED = "halted"      # Drawdown > level3 (20%)


class CircuitBreaker:
    """
    Global circuit breaker for drawdown protection.

    Example
    -------
    >>> cb = CircuitBreaker(config, portfolio)
    >>> cb.update()
    >>> if cb.can_open_position():
    ...     size = base_size * cb.position_size_multiplier()
    """

    def __init__(
        self,
        config: CircuitBreakerConfig,
        portfolio: Portfolio,
    ) -> None: ...

    @property
    def state(self) -> CircuitBreakerState: ...

    @property
    def current_drawdown(self) -> Decimal: ...

    @property
    def peak_equity(self) -> Decimal: ...

    def update(self) -> None:
        """Check drawdown and update state."""
        ...

    def can_open_position(self) -> bool:
        """Check if new positions are allowed."""
        ...

    def position_size_multiplier(self) -> Decimal:
        """Get position size adjustment (0.0 - 1.0)."""
        ...

    def reset(self) -> None:
        """Manual reset after HALTED (requires auto_recovery=False)."""
        ...


class CircuitBreakerActor(Actor):
    """
    Actor that maintains circuit breaker state.

    Subscribes to AccountState events and provides
    circuit breaker API to strategies.
    """

    def on_start(self) -> None:
        """Subscribe to account events and start timer."""
        ...

    def on_account_state(self, event: AccountState) -> None:
        """Update equity tracking on account changes."""
        ...

    def on_timer(self, event: TimeEvent) -> None:
        """Periodic state check."""
        ...
```

### Configuration

```python
from decimal import Decimal
from pydantic import BaseModel, field_validator


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker."""

    # Drawdown thresholds (as decimals, e.g., 0.10 = 10%)
    level1_drawdown_pct: Decimal = Decimal("0.10")  # WARNING
    level2_drawdown_pct: Decimal = Decimal("0.15")  # REDUCING
    level3_drawdown_pct: Decimal = Decimal("0.20")  # HALTED

    # Recovery threshold
    recovery_drawdown_pct: Decimal = Decimal("0.10")  # Return to ACTIVE

    # Recovery mode
    auto_recovery: bool = False  # Require manual reset after HALTED

    # Check interval (seconds)
    check_interval_secs: int = 60

    # Position size multipliers per state
    warning_size_multiplier: Decimal = Decimal("0.5")   # 50% in WARNING
    reducing_size_multiplier: Decimal = Decimal("0.0")  # No new in REDUCING

    @field_validator("level1_drawdown_pct", "level2_drawdown_pct", "level3_drawdown_pct")
    @classmethod
    def validate_thresholds(cls, v: Decimal) -> Decimal:
        if not (Decimal("0") < v < Decimal("1")):
            raise ValueError("Drawdown thresholds must be between 0 and 1")
        return v

    model_config = {"frozen": True}
```

## Integration with RiskManager (Spec 011)

```python
# In strategy initialization
class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig) -> None:
        super().__init__(config)

        # Get circuit breaker reference (registered by controller)
        self.circuit_breaker: CircuitBreaker | None = None

        # RiskManager with circuit breaker integration
        self.risk_manager = RiskManager(
            config=config.risk,
            strategy=self,
            circuit_breaker=self.circuit_breaker,
        )

    def on_start(self) -> None:
        # Retrieve circuit breaker from cache/registry
        self.circuit_breaker = self.cache.get("circuit_breaker")
        self.risk_manager.circuit_breaker = self.circuit_breaker

# In RiskManager
class RiskManager:
    def validate_order(self, order: Order) -> bool:
        """Check position limits AND circuit breaker."""
        # Check circuit breaker first
        if self.circuit_breaker and not self.circuit_breaker.can_open_position():
            self.log.warning(
                f"Order rejected: Circuit breaker in {self.circuit_breaker.state} state"
            )
            return False

        # Then check position limits
        return self._validate_position_limits(order)
```

## Testing Strategy

### Unit Tests
- [ ] Test CircuitBreakerState enum values
- [ ] Test drawdown calculation (peak tracking)
- [ ] Test state transitions (ACTIVE → WARNING → REDUCING → HALTED)
- [ ] Test recovery transitions (HALTED → ACTIVE with auto_recovery)
- [ ] Test manual reset requirement (auto_recovery=False)
- [ ] Test position_size_multiplier for each state
- [ ] Test can_open_position for each state
- [ ] Test config validation (threshold ordering)

### Integration Tests
- [ ] Test CircuitBreakerActor with BacktestNode
- [ ] Test equity updates from simulated fills
- [ ] Test state persistence across bar iterations
- [ ] Test integration with RiskManager (Spec 011)
- [ ] Test multiple strategies respecting circuit breaker

### Edge Cases
- [ ] Initial equity = 0 (startup)
- [ ] Rapid drawdown (skip states)
- [ ] Recovery oscillation near threshold
- [ ] Concurrent position updates

### Performance Tests
- [ ] Drawdown check latency < 1ms
- [ ] State update overhead minimal

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| False halt due to unrealized PnL | High | Medium | Use balance_total (realized), monitor carefully |
| Missed halt in rapid crash | High | Low | Check on every account event, not just timer |
| State desync across strategies | Medium | Low | Singleton actor pattern |
| Recovery oscillation | Medium | Medium | Hysteresis (different thresholds for down/up) |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.222.0 (nightly)
- Pydantic >= 2.0

### Internal Dependencies
- Spec 005: QuestDB/Grafana monitoring
- Spec 011: RiskManager integration (stop-loss)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | Clean API, hidden state machine |
| KISS & YAGNI | ✅ | MVP scope, no auto-close initially |
| Native First | ✅ | Uses NautilusTrader Actor pattern |
| Performance | ✅ | In-memory state, O(1) checks |
| TDD | 🔜 | Tests defined, ready for RED phase |

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Documentation updated (CLAUDE.md, if needed)
- [ ] Code review approved
- [ ] Drawdown check latency < 1ms verified
- [ ] QuestDB schema deployed
- [ ] Grafana dashboard created
