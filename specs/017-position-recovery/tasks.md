# Tasks: Position Recovery

**Input**: Design documents from `/specs/017-position-recovery/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included as per Testing Strategy in spec.md

**Organization**: Tasks organized by functional requirements (FR-001 to FR-004)

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - complex algorithmic tasks
- **[Story]**: Which user story/requirement this task belongs to (FR1, FR2, FR3, FR4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [x] T001 Create recovery module directory structure: `strategies/common/recovery/`
- [x] T002 Create `__init__.py` files for recovery module in `strategies/common/recovery/__init__.py`
- [x] T003 [P] Create test directory structure: `tests/unit/recovery/` and `tests/integration/recovery/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and configuration that ALL requirements depend on

**CRITICAL**: No FR implementation can begin until this phase is complete

- [x] T004 Create RecoveryConfig Pydantic model in `strategies/common/recovery/config.py` (from data-model.md)
- [x] T005 [P] Create RecoveryStatus enum in `strategies/common/recovery/models.py`
- [x] T006 [P] Create RecoveryState Pydantic model in `strategies/common/recovery/models.py`
- [x] T007 [P] Create PositionSnapshot Pydantic model in `strategies/common/recovery/models.py`
- [x] T007a [P] Create IndicatorState Pydantic model in `strategies/common/recovery/models.py` (from data-model.md)
- [x] T007b [P] Create StrategySnapshot Pydantic model in `strategies/common/recovery/models.py` (from data-model.md)
- [x] T008 Create recovery event schemas in `strategies/common/recovery/events.py` (from contracts/recovery_events.py)
- [x] T009 [P] Create test fixtures with NautilusTrader TestKit in `tests/conftest.py`
- [x] T010 Create TradingNode production config template with recovery settings in `config/trading_node_recovery.py`

**Checkpoint**: Foundation ready - FR implementation can now begin

---

## Phase 3: FR-001 - Position Loading (Priority: P1)

**Goal**: Load positions from Redis cache on startup, verify against exchange, resolve discrepancies

**Independent Test**: Start TradingNode with Redis cache containing positions, verify they are loaded correctly

### Tests for FR-001

- [x] T011 [P] [FR1] Unit test for position loading from cache in `tests/unit/recovery/test_position_loading.py`
- [x] T012 [P] [FR1] Unit test for position reconciliation logic in `tests/unit/recovery/test_reconciliation.py`
- [x] T013 [FR1] Integration test for cold start (no prior state) in `tests/integration/recovery/test_cold_start.py`
- [x] T014 [FR1] Integration test for warm start (existing positions) in `tests/integration/recovery/test_warm_start.py`

### Implementation for FR-001

- [x] T015 [FR1] Create PositionRecoveryProvider implementation in `strategies/common/recovery/provider.py` (implements contracts/recovery_interface.py)
- [x] T016 [FR1] Implement `get_cached_positions()` method in `strategies/common/recovery/provider.py`
- [x] T017 [FR1] Implement `get_exchange_positions()` method in `strategies/common/recovery/provider.py`
- [x] T018 [E] [FR1] Implement `reconcile_positions()` method with discrepancy detection in `strategies/common/recovery/provider.py`
- [x] T019 [FR1] Add logging for position loading events in `strategies/common/recovery/provider.py`

**Checkpoint**: Position loading works - can load and reconcile positions from Redis

---

## Phase 4: FR-002 - Strategy State Restoration (Priority: P1)

**Goal**: Restore indicator warmup state, pending order references, and custom strategy state

**Independent Test**: Restart strategy with position, verify indicators warm up and exit orders are recreated

### Tests for FR-002

- [x] T020 [P] [FR2] Unit test for RecoverableStrategy base class in `tests/unit/recovery/test_recoverable_strategy.py`
- [x] T021 [P] [FR2] Unit test for indicator warmup in `tests/unit/recovery/test_indicator_warmup.py`
- [x] T022 [FR2] Unit test for exit order recreation in `tests/unit/recovery/test_exit_order_recreation.py`
- [x] T023 [FR2] Integration test for strategy recovery with BacktestNode in `tests/integration/recovery/test_strategy_recovery.py`

### Implementation for FR-002

- [x] T024 [FR2] Create RecoverableStrategy base class in `strategies/common/recovery/recoverable_strategy.py`
- [x] T025 [FR2] Implement `on_start()` with position detection in `strategies/common/recovery/recoverable_strategy.py`
- [x] T026 [FR2] Implement `on_position_recovered()` hook in `strategies/common/recovery/recoverable_strategy.py`
- [x] T027 [FR2] Implement `_handle_recovered_position()` method in `strategies/common/recovery/recoverable_strategy.py`
- [x] T028 [FR2] Implement `_setup_exit_orders()` for stop-loss recreation in `strategies/common/recovery/recoverable_strategy.py`
- [x] T029 [FR2] Implement historical data warmup pattern with `request_bars()` in `strategies/common/recovery/recoverable_strategy.py`
- [x] T030 [FR2] Implement `on_historical_data()` handler for indicator warmup in `strategies/common/recovery/recoverable_strategy.py`
- [x] T031 [FR2] Implement `on_warmup_complete()` callback in `strategies/common/recovery/recoverable_strategy.py`

**Checkpoint**: Strategy state restoration works - indicators warm up and positions are managed

---

## Phase 5: FR-003 - Account Balance Restoration (Priority: P2)

**Goal**: Load last known balances from cache, update with current exchange balances, track balance changes

**Independent Test**: Verify account balances are restored and updated after restart

### Tests for FR-003

- [x] T032 [P] [FR3] Unit test for balance loading in `tests/unit/recovery/test_balance_restoration.py`
- [x] T033 [FR3] Unit test for balance change tracking in `tests/unit/recovery/test_balance_tracking.py`

### Implementation for FR-003

- [x] T034 [FR3] Implement balance loading from cache in `strategies/common/recovery/provider.py`
- [x] T035 [FR3] Implement balance update with exchange state in `strategies/common/recovery/provider.py`
- [x] T036 [FR3] Add balance change tracking during downtime in `strategies/common/recovery/provider.py`

**Checkpoint**: Account balances are correctly restored and tracked

---

## Phase 6: FR-004 - Event Replay (Priority: P3 - Optional)

**Goal**: Replay missed events from cache, generate synthetic events for gap filling

**Skip Condition**: This phase can be skipped for MVP. Implement only if event gap handling is required for production.

**Independent Test**: Verify missed events are replayed in correct sequence

### Tests for FR-004

- [x] T037 [P] [FR4] Unit test for event replay logic in `tests/unit/recovery/test_event_replay.py`
- [x] T038 [FR4] Unit test for synthetic event generation in `tests/unit/recovery/test_synthetic_events.py`

### Implementation for FR-004

- [x] T039 [FR4] Implement event replay from cache in `strategies/common/recovery/event_replay.py`
- [x] T040 [FR4] Implement synthetic event generation for gap filling in `strategies/common/recovery/event_replay.py`
- [x] T041 [FR4] Implement event sequence maintenance in `strategies/common/recovery/event_replay.py`

**Checkpoint**: Event replay works - missed events are replayed correctly

---

## Phase 7: NFR Validation & Performance

**Goal**: Validate non-functional requirements (recovery time < 30s, no duplicates)

### Tests for NFRs

- [x] T042 [P] Performance test for recovery time < 5s (position recovery) in `tests/performance/test_recovery_time.py`
- [x] T043 [P] Performance test for recovery time < 30s (full state) in `tests/performance/test_full_recovery_time.py`
- [x] T044 Integration test for no duplicate orders after recovery in `tests/integration/recovery/test_no_duplicates.py`
- [x] T045 Integration test for position size accuracy in `tests/integration/recovery/test_position_accuracy.py`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, event logging, and final validation

- [x] T046 [P] Create RecoveryEventEmitter implementation in `strategies/common/recovery/event_emitter.py`
- [x] T047 [P] Create RecoveryStateManager implementation in `strategies/common/recovery/state_manager.py`
- [x] T048 Update quickstart.md with implementation examples in `specs/017-position-recovery/quickstart.md`
- [x] T049 [P] Add type hints validation with mypy in `strategies/common/recovery/`
- [x] T050 Run ruff format and check on recovery module
- [x] T051 Run alpha-debug verification on recovery implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all FRs
- **FR-001 (Phase 3)**: Depends on Foundational
- **FR-002 (Phase 4)**: Depends on Foundational (can run parallel with FR-001)
- **FR-003 (Phase 5)**: Depends on FR-001 (extends provider)
- **FR-004 (Phase 6)**: Depends on Foundational (can run parallel with FR-001, FR-002)
- **NFR Validation (Phase 7)**: Depends on FR-001, FR-002
- **Polish (Phase 8)**: Depends on all FRs

### Functional Requirement Dependencies

- **FR-001 (Position Loading)**: No FR dependencies - can start after Foundational
- **FR-002 (Strategy State)**: No FR dependencies - can start after Foundational
- **FR-003 (Account Balance)**: Extends FR-001 provider
- **FR-004 (Event Replay)**: No FR dependencies - optional feature

### Within Each Phase

- Tests MUST be written and FAIL before implementation (TDD)
- Models before logic implementation
- Core implementation before integration
- Phase complete before moving to next priority

### Parallel Opportunities

**Setup (all parallel):**
```
T001, T002, T003 → can run together
```

**Foundational (config first, then parallel):**
```
T004 (config) → then T005, T006, T007, T008, T009, T010 in parallel
```

**FR-001 + FR-002 (parallel tracks):**
```
Track A: T011-T019 (Position Loading)
Track B: T020-T031 (Strategy State)
→ Can run simultaneously
```

---

## Parallel Example: FR-001 + FR-002 Together

```bash
# Launch FR-001 tests:
Task: "[FR1] Unit test for position loading in tests/unit/recovery/test_position_loading.py"
Task: "[FR1] Unit test for reconciliation in tests/unit/recovery/test_reconciliation.py"

# Launch FR-002 tests in parallel:
Task: "[FR2] Unit test for RecoverableStrategy in tests/unit/recovery/test_recoverable_strategy.py"
Task: "[FR2] Unit test for indicator warmup in tests/unit/recovery/test_indicator_warmup.py"
```

---

## Implementation Strategy

### MVP First (FR-001 + FR-002 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all FRs)
3. Complete Phase 3: FR-001 (Position Loading)
4. Complete Phase 4: FR-002 (Strategy State Restoration)
5. **STOP and VALIDATE**: Test position recovery independently
6. Deploy/demo if ready

### Full Implementation

1. Setup + Foundational → Foundation ready
2. FR-001 + FR-002 in parallel → Core recovery (MVP!)
3. FR-003 → Account balance restoration
4. FR-004 → Event replay (optional)
5. NFR Validation + Polish → Production ready

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 53 |
| **Setup Tasks** | 3 |
| **Foundational Tasks** | 9 |
| **FR-001 Tasks** | 9 |
| **FR-002 Tasks** | 12 |
| **FR-003 Tasks** | 5 |
| **FR-004 Tasks** | 5 (Optional - can skip for MVP) |
| **NFR Tasks** | 4 |
| **Polish Tasks** | 6 |
| **Parallel Opportunities** | 20 tasks marked [P] |
| **Alpha-Evolve Tasks** | 1 task marked [E] (reconciliation algorithm) |

### MVP Scope

- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational): 9 tasks
- Phase 3 (FR-001): 9 tasks
- Phase 4 (FR-002): 12 tasks
- **MVP Total**: 33 tasks

### Key Files

| File | Purpose |
|------|---------|
| `strategies/common/recovery/config.py` | RecoveryConfig model |
| `strategies/common/recovery/models.py` | RecoveryState, PositionSnapshot |
| `strategies/common/recovery/provider.py` | PositionRecoveryProvider implementation |
| `strategies/common/recovery/recoverable_strategy.py` | RecoverableStrategy base class |
| `strategies/common/recovery/events.py` | Event schemas |
| `config/trading_node_recovery.py` | Production TradingNode config |

---

## Notes

- [P] tasks = different files, no dependencies (processed by /speckit.implement)
- [E] tasks = complex algorithms triggering alpha-evolve (reconciliation logic)
- [FR#] label maps task to specific functional requirement
- Each FR should be independently completable and testable
- Verify tests fail before implementing (TDD discipline)
- Commit after each task or logical group
- Stop at any checkpoint to validate FR independently
