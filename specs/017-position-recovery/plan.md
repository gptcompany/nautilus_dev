# Implementation Plan: Position Recovery

**Feature Branch**: `017-position-recovery`
**Created**: 2025-12-30
**Status**: Ready for Implementation
**Spec Reference**: `specs/017-position-recovery/spec.md`

## Architecture Overview

Position recovery enables NautilusTrader to restore position state after TradingNode restarts, ensuring strategies resume with correct position awareness.

### System Context

```
Position recovery integrates with:
- Redis Cache (Spec 018): Position persistence
- Order Reconciliation (Spec 016): State synchronization
- TradingNode: Startup lifecycle
- Strategy: Warmup and state restoration
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TradingNode                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ LiveExecEngine│  │    Cache    │  │   StrategyManager    │  │
│  │              │  │   (Redis)    │  │                      │  │
│  │ reconciliation│  │ positions   │  │  on_start()          │  │
│  │ engine       │◄─┤ orders      │◄─┤  warmup indicators   │  │
│  │              │  │ accounts    │  │  restore references  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         ▼                 ▼                      ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Position Recovery Flow                   │  │
│  │                                                           │  │
│  │  1. Load positions from Redis                            │  │
│  │  2. Query exchange for current state                     │  │
│  │  3. Reconcile discrepancies (synthetic orders)           │  │
│  │  4. Notify strategies of recovered positions             │  │
│  │  5. Request historical data for warmup                   │  │
│  │  6. Resume trading                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    Exchange     │
                    │   (Binance)     │
                    │                 │
                    │ position_reports│
                    │ order_reports   │
                    │ fill_reports    │
                    └─────────────────┘
```

## Technical Decisions

### Decision 1: Recovery Mechanism

**Options Considered**:
1. **Native NautilusTrader Reconciliation**
   - Pros: Built-in, battle-tested, handles edge cases
   - Cons: Less customization control
2. **Custom Recovery System**
   - Pros: Full control over logic
   - Cons: Duplicates existing functionality, maintenance burden

**Selected**: Option 1 - Native Reconciliation

**Rationale**: NautilusTrader's reconciliation system is mature and handles complex scenarios (synthetic orders, price determination hierarchy). Custom implementation would add complexity without benefit.

---

### Decision 2: Cache Encoding

**Options Considered**:
1. **msgpack** - Binary encoding
   - Pros: Faster serialization/deserialization
   - Cons: Not human-readable
2. **JSON** - Text encoding
   - Pros: Human-readable, easier debugging
   - Cons: Slower, larger payload

**Selected**: Option 1 - msgpack

**Rationale**: Production performance is priority. Use Redis CLI or monitoring tools for debugging.

---

### Decision 3: Indicator Warmup Strategy

**Options Considered**:
1. **Historical Data Request** - Request bars on startup
   - Pros: Native pattern, reliable, uses exchange data
   - Cons: Adds startup delay
2. **State Persistence** - Save/restore indicator values
   - Pros: Faster startup
   - Cons: Complex, risk of stale state

**Selected**: Option 1 - Historical Data Request

**Rationale**: Reliability over speed. 2 days of historical data ensures accurate indicator state. Complexity of state persistence not justified.

---

## Implementation Strategy

### Phase 1: Foundation

**Goal**: Configure TradingNode for position persistence and recovery

**Deliverables**:
- [ ] TradingNode configuration with Redis cache and reconciliation
- [ ] RecoveryConfig Pydantic model
- [ ] Unit tests for configuration validation

**Dependencies**: Spec 018 (Redis Cache Backend)

**Key Configuration**:
```python
TradingNodeConfig(
    cache=CacheConfig(
        database=DatabaseConfig(type="redis", host="localhost", port=6379),
        encoding="msgpack",
        flush_on_start=False,  # CRITICAL
    ),
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,
    ),
)
```

---

### Phase 2: Core Implementation

**Goal**: Implement recovery-aware strategy base class

**Deliverables**:
- [ ] RecoverableStrategy base class with recovery hooks
- [ ] Position detection on startup
- [ ] Exit order recreation for recovered positions
- [ ] Historical data warmup pattern
- [ ] Unit tests for recovery scenarios

**Dependencies**: Phase 1

**Key Pattern**:
```python
class RecoverableStrategy(Strategy):
    def on_start(self) -> None:
        # 1. Detect recovered positions
        for position in self.cache.positions(instrument_id=self.instrument_id):
            if position.is_open:
                self._handle_recovered_position(position)

        # 2. Request warmup data
        self.request_bars(
            bar_type=self.bar_type,
            start=self.clock.utc_now() - timedelta(days=2),
        )
```

---

### Phase 3: Integration & Testing

**Goal**: End-to-end testing and documentation

**Deliverables**:
- [ ] Integration tests (cold start, warm start, position mismatch)
- [ ] Recovery event logging
- [ ] Quickstart documentation (already created)
- [ ] Performance benchmarks (recovery time < 30s)

**Dependencies**: Phase 2

**Test Scenarios**:
1. Cold Start: No prior state, fresh start
2. Warm Start: Existing positions, successful recovery
3. Position Mismatch: Cache differs from exchange
4. Indicator Warmup: Verify correct indicator state after warmup

---

## File Structure

```
strategies/
├── common/
│   ├── __init__.py
│   └── recovery/                      # Recovery module (subdirectory)
│       ├── __init__.py
│       ├── config.py                  # RecoveryConfig model
│       ├── models.py                  # RecoveryState, PositionSnapshot, IndicatorState, StrategySnapshot
│       ├── provider.py                # PositionRecoveryProvider implementation
│       ├── recoverable_strategy.py    # Base class with recovery support
│       ├── events.py                  # Event schemas
│       ├── event_emitter.py           # RecoveryEventEmitter implementation
│       ├── state_manager.py           # RecoveryStateManager implementation
│       └── event_replay.py            # Event replay (FR-004, optional)
config/
├── trading_node_recovery.py           # Production config with recovery
tests/
├── unit/
│   └── recovery/                      # Unit tests for recovery module
│       ├── test_position_loading.py
│       ├── test_reconciliation.py
│       ├── test_recoverable_strategy.py
│       ├── test_indicator_warmup.py
│       └── test_exit_order_recreation.py
├── integration/
│   └── recovery/                      # Integration tests
│       ├── test_cold_start.py
│       ├── test_warm_start.py
│       └── test_strategy_recovery.py
└── performance/
    └── test_recovery_time.py          # NFR validation
specs/017-position-recovery/
├── spec.md                        # Feature specification
├── plan.md                        # This file
├── research.md                    # Research findings
├── data-model.md                  # Entity definitions
├── quickstart.md                  # Usage guide
└── contracts/
    ├── recovery_interface.py      # Interface contracts
    └── recovery_events.py         # Event schemas
```

## API Design

### Public Interface

```python
class RecoverableStrategy(Strategy):
    """Strategy base class with position recovery support."""

    def __init__(self, config: StrategyConfig) -> None: ...

    def on_start(self) -> None:
        """Detect positions and initiate warmup."""

    def on_position_recovered(self, position: Position) -> None:
        """Override to handle recovered positions."""

    def on_warmup_complete(self) -> None:
        """Override to handle warmup completion."""

    def _handle_recovered_position(self, position: Position) -> None:
        """Internal: Process a single recovered position."""

    def _setup_exit_orders(self, position: Position) -> None:
        """Internal: Recreate stop-loss/take-profit orders."""
```

### Configuration

```python
class RecoveryConfig(BaseModel):
    """Configuration for position recovery."""

    recovery_enabled: bool = True
    warmup_lookback_days: int = 2
    startup_delay_secs: float = 10.0
    max_recovery_time_secs: float = 30.0
    claim_external_positions: bool = True
```

## Testing Strategy

### Unit Tests
- [ ] RecoverableStrategy initialization
- [ ] Position detection logic
- [ ] Exit order recreation
- [ ] Configuration validation
- [ ] Recovery state transitions

### Integration Tests
- [ ] Cold start with BacktestNode
- [ ] Warm start with existing positions
- [ ] Position mismatch resolution
- [ ] Indicator warmup validation
- [ ] Recovery timeout handling

### Performance Tests
- [ ] Recovery time < 30 seconds
- [ ] Memory usage during recovery
- [ ] Redis read latency

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| HEDGING mode not supported | High | Medium | Document limitation, use one-way mode (Bug #3104) |
| Redis unavailable on start | High | Low | Health check before trading, alert on failure |
| Indicator warmup incomplete | Medium | Low | Wait for callback, timeout handling |
| External positions missed | Medium | Medium | Configure `external_order_claims` per strategy |
| Reconciliation timeout | Medium | Low | Configurable timeout, graceful degradation |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.220.0 (nightly)
- Redis 7.x
- Python 3.11+

### Internal Dependencies
- Spec 016 (Order Reconciliation) - COMPLETED
- Spec 018 (Redis Cache Backend) - IN PROGRESS

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Recovery time < 30 seconds (NFR-001)
- [ ] Zero duplicate orders after recovery (NFR-002)
- [ ] Position sizes match exchange exactly (NFR-002)
- [ ] Documentation complete (quickstart.md)
- [ ] Code review approved

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | PASS | Clean interface, hidden implementation |
| KISS & YAGNI | PASS | Uses native mechanisms, no over-engineering |
| Native First | PASS | Uses native reconciliation, indicators |
| Performance | PASS | msgpack encoding, buffered writes |
| TDD Discipline | PENDING | Tests to be written first |
| Type Hints | PENDING | All public functions |
| Coverage > 80% | PENDING | Target for implementation |
