# Tasks: Circuit Breaker (Max Drawdown)

**Input**: Design documents from `/specs/012-circuit-breaker-drawdown/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

**Tests**: Test tasks included based on plan.md testing strategy (TDD approach).

**Organization**: Tasks grouped by implementation phase from plan.md (Core → Actor → Monitoring).

## Format: `[ID] [Markers] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project structure and basic risk module setup

- [ ] T001 Create risk/ module structure per plan.md file structure
- [ ] T002 [P] Create risk/__init__.py with module exports
- [ ] T003 [P] Add risk module dependencies to pyproject.toml if needed

---

## Phase 2: Core Implementation - State Machine & Config

**Purpose**: CircuitBreaker state machine with equity monitoring (Plan Phase 1)

**Goal**: Working CircuitBreaker class with drawdown calculation and state transitions

**Independent Test**: CircuitBreaker correctly transitions states based on simulated equity changes

### Tests for Core Implementation

- [ ] T004 [P] Write failing test for CircuitBreakerState enum in tests/test_circuit_breaker.py
- [ ] T005 [P] Write failing test for CircuitBreakerConfig validation in tests/test_circuit_breaker_config.py
- [ ] T006 [P] Write failing test for drawdown calculation in tests/test_circuit_breaker.py
- [ ] T007 [P] Write failing test for state transitions (ACTIVE→WARNING→REDUCING→HALTED) in tests/test_circuit_breaker.py
- [ ] T008 [P] Write failing test for recovery transitions in tests/test_circuit_breaker.py
- [ ] T009 [P] Write failing test for can_open_position() logic in tests/test_circuit_breaker.py
- [ ] T010 [P] Write failing test for position_size_multiplier() logic in tests/test_circuit_breaker.py
- [ ] T011 Write failing test for manual reset() in tests/test_circuit_breaker.py
- [ ] T011b [P] Write failing tests for edge cases in tests/test_circuit_breaker.py:
  - Initial equity = 0 (startup)
  - Rapid drawdown (skip intermediate states)
  - Recovery oscillation near threshold
  - Division by zero protection (peak_equity = 0)

### Implementation for Core

- [ ] T012 [P] [E] Create CircuitBreakerState enum in risk/circuit_breaker_state.py
- [ ] T013 [P] Create CircuitBreakerConfig Pydantic model in risk/circuit_breaker_config.py (from contracts)
- [ ] T014 [E] Implement CircuitBreaker class in risk/circuit_breaker.py with:
  - __init__(config, portfolio)
  - Properties: state, peak_equity, current_equity, current_drawdown, last_check
  - Methods: update(), can_open_position(), position_size_multiplier(), reset()
  - Private: _update_state(drawdown), _calculate_drawdown()
- [ ] T015 Run tests via test-runner agent and verify all T004-T011b pass

**Checkpoint**: CircuitBreaker state machine fully functional with unit tests passing

---

## Phase 3: Actor Integration

**Purpose**: CircuitBreakerActor for TradingNode integration (Plan Phase 2)

**Goal**: Actor that subscribes to AccountState events and provides circuit breaker API

**Independent Test**: CircuitBreakerActor correctly updates state on simulated account events

### Tests for Actor Integration

- [ ] T016 [P] Write failing test for CircuitBreakerActor initialization in tests/test_circuit_breaker.py
- [ ] T017 [P] Write failing test for on_account_state handler in tests/test_circuit_breaker.py
- [ ] T018 [P] Write failing test for periodic timer check in tests/test_circuit_breaker.py
- [ ] T019 Write failing integration test with BacktestNode in tests/integration/test_circuit_breaker_backtest.py

### Implementation for Actor

- [ ] T020 Implement CircuitBreakerActor in risk/circuit_breaker.py with:
  - on_start() - subscribe to account events, set timer
  - on_stop() - cancel timers, log final state
  - on_account_state(event) - update equity, call update()
  - on_timer(event) - periodic safety check
- [ ] T021 Update risk/__init__.py to export CircuitBreakerActor
- [ ] T022 Run tests via test-runner agent and verify T016-T019 pass

**Checkpoint**: CircuitBreakerActor fully functional with integration tests passing

---

## Phase 4: RiskManager Integration

**Purpose**: Connect CircuitBreaker with RiskManager from Spec 011

**Goal**: RiskManager validates against circuit breaker before position limits

**Independent Test**: Order rejected when circuit breaker in HALTED state

### Tests for RiskManager Integration

- [ ] T023 Write failing test for RiskManager with circuit_breaker parameter in tests/test_risk_manager.py
- [ ] T024 Write failing test for order rejection on HALTED state in tests/test_risk_manager.py

### Implementation for Integration

- [ ] T025 Update RiskManager in risk/risk_manager.py to accept optional circuit_breaker parameter
- [ ] T026 Update RiskManager.validate_order() to check circuit breaker first
- [ ] T027 Create risk/integration.py with helper for registering circuit breaker with cache
- [ ] T028 Run tests via test-runner agent and verify T023-T024 pass

**Checkpoint**: RiskManager and CircuitBreaker fully integrated

---

## Phase 5: Monitoring & Alerting

**Purpose**: QuestDB metrics and Grafana dashboard (Plan Phase 3)

**Goal**: Circuit breaker state changes logged to QuestDB, viewable in Grafana

### Implementation for Monitoring

- [ ] T029 [P] Create QuestDB schema in monitoring/schemas/circuit_breaker_state.sql
- [ ] T030 [P] Create CircuitBreakerCollector in monitoring/collectors/circuit_breaker.py
- [ ] T031 Update CircuitBreakerActor to emit metrics on state change
- [ ] T032 [P] Create Grafana dashboard JSON in monitoring/grafana/dashboards/circuit_breaker.json with:
  - Real-time drawdown gauge (green/yellow/red zones)
  - State history timeline
  - Peak vs current equity chart
- [ ] T033 Add Grafana alert rule for LEVEL 2+ trigger

**Checkpoint**: Full monitoring stack operational

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup, documentation, performance validation

- [ ] T034 [P] Update risk/__init__.py with complete module docstring
- [ ] T035 [P] Add type hints to all public interfaces
- [ ] T036 Run ruff format and ruff check on risk/ module
- [ ] T037 Verify drawdown check latency < 1ms (p99) with simple benchmark
- [ ] T037b Verify activation latency < 100ms (p99) - time from threshold breach to state change
- [ ] T038 Run alpha-debug verification on risk/circuit_breaker.py
- [ ] T039 Update specs/012-circuit-breaker-drawdown/spec.md to mark requirements complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Core)**: Depends on Phase 1 completion
- **Phase 3 (Actor)**: Depends on Phase 2 completion
- **Phase 4 (RiskManager Integration)**: Depends on Phase 3 AND Spec 011 completion
- **Phase 5 (Monitoring)**: Depends on Phase 3, can run parallel to Phase 4
- **Phase 6 (Polish)**: Depends on Phases 3, 4, 5 completion

### Parallel Opportunities by Phase

**Phase 1**: T002, T003 can run in parallel

**Phase 2 Tests**: T004-T010 can ALL run in parallel (different test functions, same file but no conflict)

**Phase 2 Implementation**: T012, T013 can run in parallel (different files)

**Phase 3 Tests**: T016-T018 can run in parallel

**Phase 5**: T029, T030, T032 can run in parallel (different files)

**Phase 6**: T034, T035 can run in parallel

---

## Parallel Example: Phase 2 Implementation

```bash
# Launch config and state enum in parallel:
Task: "Create CircuitBreakerState enum in risk/circuit_breaker_state.py"
Task: "Create CircuitBreakerConfig Pydantic model in risk/circuit_breaker_config.py"
```

---

## Implementation Strategy

### MVP First (Phases 1-3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Core Implementation (state machine)
3. Complete Phase 3: Actor Integration
4. **STOP and VALIDATE**: Test with BacktestNode
5. Can deploy/demo MVP here - basic drawdown protection working

### Full Feature (Phases 4-6)

6. Complete Phase 4: RiskManager Integration
7. Complete Phase 5: Monitoring
8. Complete Phase 6: Polish

### Critical Path

```
Setup → Core Tests → Core Implementation → Actor Tests → Actor Implementation
                                                              ↓
                                                    RiskManager Integration
                                                              ↓
                                                    Monitoring → Polish
```

---

## Notes

- **Total Tasks**: 41 (39 original + 2 added: T011b, T037b)
- [P] tasks = different files, no dependencies
- [E] tasks = complex state machine logic, benefit from alpha-evolve exploration
- TDD approach: All test tasks MUST fail before implementation
- Use **test-runner agent** for all test execution (constitution requirement)
- Commit after each phase completion
- Spec 011 (RiskManager) must be complete before Phase 4
- Spec 005 (QuestDB/Grafana) must be complete before Phase 5
