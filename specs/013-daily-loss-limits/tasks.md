# Tasks: Daily Loss Limits (Spec 013)

**Input**: Design documents from `/specs/013-daily-loss-limits/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included per spec.md testing strategy (Unit Tests, Integration Tests, Edge Cases).

**Organization**: Tasks are grouped by functional requirement to enable independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which functional requirement this task belongs to (FR1=PnL Calculation, FR2=Loss Limit, FR3=Reset, FR4=Per-Strategy)

### Path Conventions
- **Risk module**: `risk/`
- **Tests**: `tests/`, `tests/integration/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization - extending existing risk module

- [X] T001 Verify existing risk module structure in risk/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Configuration model that MUST be complete before tracker implementation

**⚠️ CRITICAL**: No tracker work can begin until DailyLossConfig is complete

- [X] T002 Create DailyLossConfig Pydantic model in risk/daily_loss_config.py
- [X] T003 [P] Write unit tests for DailyLossConfig validation in tests/test_daily_loss_config.py
- [X] T004 Add DailyLossConfig export to risk/__init__.py

**Checkpoint**: ✅ Foundation ready - tracker implementation can now begin

---

## Phase 3: User Story 1 - Daily PnL Calculation (Priority: P1) 🎯 MVP

**Goal**: Track realized + unrealized PnL per day (FR-001)

**Independent Test**: Create tracker, simulate PositionClosed events, verify daily_realized accumulates correctly

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T005 [P] [FR1] Write test_daily_realized_accumulates in tests/test_daily_pnl_tracker.py
- [X] T006 [P] [FR1] Write test_unrealized_pnl_calculation in tests/test_daily_pnl_tracker.py
- [X] T007 [P] [FR1] Write test_total_daily_pnl_sum in tests/test_daily_pnl_tracker.py

### Implementation for User Story 1

- [X] T008 [FR1] Create DailyPnLTracker class skeleton in risk/daily_pnl_tracker.py
- [X] T009 [FR1] Implement daily_realized property and _on_position_closed handler in risk/daily_pnl_tracker.py
- [X] T010 [FR1] Implement daily_unrealized property using portfolio.unrealized_pnls() in risk/daily_pnl_tracker.py
- [X] T011 [FR1] Implement total_daily_pnl computed property in risk/daily_pnl_tracker.py
- [X] T012 [FR1] Implement handle_event() with PositionClosed routing in risk/daily_pnl_tracker.py
- [X] T013 [FR1] Add DailyPnLTracker export to risk/__init__.py

**Checkpoint**: At this point, PnL tracking should work and tests pass

---

## Phase 4: User Story 2 - Daily Loss Limit Enforcement (Priority: P1)

**Goal**: Halt trading when daily loss exceeds threshold (FR-002)

**Independent Test**: Set limit to $100, accumulate $150 loss, verify limit_triggered=True and can_trade()=False

### Tests for User Story 2

- [X] T014 [P] [FR2] Write test_limit_not_triggered_under_threshold in tests/test_daily_pnl_tracker.py
- [X] T015 [P] [FR2] Write test_limit_triggered_at_threshold in tests/test_daily_pnl_tracker.py
- [X] T016 [P] [FR2] Write test_can_trade_returns_false_when_triggered in tests/test_daily_pnl_tracker.py
- [X] T017 [P] [FR2] Write test_close_positions_on_limit_true in tests/test_daily_pnl_tracker.py

### Implementation for User Story 2

- [X] T018 [FR2] Implement limit_triggered property and state management in risk/daily_pnl_tracker.py
- [X] T019 [FR2] Implement check_limit() method with threshold comparison in risk/daily_pnl_tracker.py
- [X] T020 [FR2] Implement can_trade() method in risk/daily_pnl_tracker.py
- [X] T021 [FR2] Implement _close_all_positions() helper for limit trigger in risk/daily_pnl_tracker.py
- [X] T022 [FR2] Add warning threshold alert at 50% of limit in risk/daily_pnl_tracker.py

**Checkpoint**: At this point, loss limit enforcement should work independently

---

## Phase 5: User Story 3 - Daily Reset (Priority: P2)

**Goal**: Automatic reset at configurable time (FR-003)

**Independent Test**: Create tracker, set reset_time_utc="12:00", simulate time passing to 12:00, verify counters reset

### Tests for User Story 3

- [X] T023 [P] [FR3] Write test_reset_clears_daily_realized in tests/test_daily_pnl_tracker.py
- [X] T024 [P] [FR3] Write test_reset_clears_limit_triggered in tests/test_daily_pnl_tracker.py
- [X] T025 [P] [FR3] Write test_day_start_property_updates_on_reset in tests/test_daily_pnl_tracker.py

### Implementation for User Story 3

- [X] T026 [FR3] Implement reset() method in risk/daily_pnl_tracker.py
- [X] T027 [FR3] Implement day_start property and _get_day_start() helper in risk/daily_pnl_tracker.py
- [X] T028 [FR3] Implement timer-based reset using clock.set_timer() in risk/daily_pnl_tracker.py
- [X] T029 [FR3] Implement _next_reset_time() helper for calculating next reset in risk/daily_pnl_tracker.py

**Checkpoint**: At this point, daily reset should work independently

---

## Phase 6: User Story 4 - RiskManager Integration (Priority: P2)

**Goal**: Integrate DailyPnLTracker with existing RiskManager (FR-004 partial)

**Independent Test**: Create RiskManager with daily_tracker, send PositionClosed event, verify tracker receives it

### Tests for User Story 4

- [X] T030 [P] [FR4] Write test_risk_manager_with_daily_tracker in tests/test_risk_manager.py
- [X] T031 [P] [FR4] Write test_risk_manager_without_daily_tracker in tests/test_risk_manager.py

### Implementation for User Story 4

- [X] T032 [FR4] Add daily_tracker parameter to RiskManager.__init__() in risk/manager.py
- [X] T033 [FR4] Add daily_tracker event routing in RiskManager.handle_event() in risk/manager.py
- [X] T034 [FR4] Add validate_order() integration with daily_tracker.can_trade() in risk/manager.py
- [X] T034a [FR4] Implement per_strategy=True tracking logic (strategy_id key in DailyPnLTracker) in risk/daily_pnl_tracker.py
- [X] T034b [P] [FR4] Write test_per_strategy_limits_independent in tests/test_daily_pnl_tracker.py

**Checkpoint**: At this point, RiskManager integration and per-strategy limits should work

---

## Phase 7: User Story 5 - QuestDB Monitoring (Priority: P3)

**Goal**: Publish daily PnL to QuestDB for dashboards

**Independent Test**: Create tracker with QuestDB writer, trigger limit, verify record written to daily_pnl table

### Tests for User Story 5

- [X] T035 [P] [MON] Write test_questdb_record_on_check_limit in tests/test_daily_pnl_tracker.py

### Implementation for User Story 5

- [X] T036 [MON] Create daily_pnl QuestDB table schema in monitoring/schemas/daily_pnl.sql
- [X] T037 [MON] Implement _publish_to_questdb() helper in risk/daily_pnl_tracker.py
- [X] T038 [MON] Add QuestDB publish on check_limit() call in risk/daily_pnl_tracker.py

**Checkpoint**: At this point, monitoring should work

---

## Phase 8: Integration Testing (Priority: P3)

**Goal**: Validate with BacktestNode

### Integration Tests

- [X] T039 [P] [INT] Write test_daily_limit_backtest_single_strategy in tests/integration/test_daily_limits_backtest.py
- [X] T040 [P] [INT] Write test_daily_limit_backtest_multi_position in tests/integration/test_daily_limits_backtest.py
- [X] T041 [INT] Write test_daily_limit_reset_at_midnight in tests/integration/test_daily_limits_backtest.py
- [X] T042 [INT] Write test_positions_spanning_midnight_edge_case in tests/integration/test_daily_limits_backtest.py

**Checkpoint**: All integration tests should pass

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Add comprehensive docstrings to DailyPnLTracker in risk/daily_pnl_tracker.py
- [X] T044 [P] Add logging for limit triggers and resets in risk/daily_pnl_tracker.py
- [X] T045 Run alpha-debug verification on risk/daily_pnl_tracker.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on User Story 1 (T008-T012)
- **User Story 3 (Phase 5)**: Depends on User Story 1 (T008)
- **User Story 4 (Phase 6)**: Depends on User Story 2 (limit enforcement)
- **User Story 5 (Phase 7)**: Depends on User Story 2 (limit enforcement)
- **Integration (Phase 8)**: Depends on all user stories
- **Polish (Phase 9)**: Depends on all desired features complete

### User Story Dependencies

- **FR1 (PnL Calculation)**: Foundation only - can start after Phase 2
- **FR2 (Loss Limit)**: Requires FR1 complete (needs PnL tracking)
- **FR3 (Daily Reset)**: Requires FR1 skeleton (tracker class exists)
- **FR4 (Integration)**: Requires FR2 complete (needs can_trade())
- **MON (Monitoring)**: Requires FR2 complete (needs check_limit())

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Core implementation before helpers
- Properties before methods that use them

### Parallel Opportunities

- All tests within a phase marked [P] can run in parallel (different test functions in same file)
- T005, T006, T007 can run in parallel (FR1 tests)
- T014, T015, T016, T017 can run in parallel (FR2 tests)
- T023, T024, T025 can run in parallel (FR3 tests)
- T030, T031 can run in parallel (FR4 tests)
- T039, T040 can run in parallel (INT tests)
- T043, T044 can run in parallel (Polish - different concerns)

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all FR1 tests together (different test functions):
Task: "Write test_daily_realized_accumulates in tests/test_daily_pnl_tracker.py"
Task: "Write test_unrealized_pnl_calculation in tests/test_daily_pnl_tracker.py"
Task: "Write test_total_daily_pnl_sum in tests/test_daily_pnl_tracker.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (DailyLossConfig)
3. Complete Phase 3: User Story 1 (PnL Calculation)
4. Complete Phase 4: User Story 2 (Loss Limit Enforcement)
5. **STOP and VALIDATE**: Test limit enforcement independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add FR1 (PnL Tracking) → Test independently (MVP-0)
3. Add FR2 (Loss Limit) → Test independently → Deploy/Demo (MVP!)
4. Add FR3 (Daily Reset) → Test independently
5. Add FR4 (RiskManager Integration) → Test independently
6. Add MON (QuestDB) → Test independently
7. Run Integration Tests → Validate all scenarios

---

## Notes

- [P] tasks = different files or different test functions, no dependencies
- [Story] label maps task to functional requirement for traceability
- Each user story should be independently testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing patterns: Follow RiskManager and CircuitBreaker patterns from Spec 011/012
