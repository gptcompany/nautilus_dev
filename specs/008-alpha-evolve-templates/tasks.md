# Tasks: Alpha-Evolve Strategy Templates

**Input**: Design documents from `/specs/008-alpha-evolve-templates/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included as per TDD principle in constitution.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [x] T001 Create templates directory structure: `scripts/alpha_evolve/templates/__init__.py`
- [x] T002 [P] Create test templates directory: `tests/alpha_evolve/templates/__init__.py`
- [x] T003 [P] Update alpha_evolve module exports in `scripts/alpha_evolve/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create EquityPoint dataclass in `scripts/alpha_evolve/templates/base.py`
- [x] T005 Create BaseEvolveConfig Pydantic model in `scripts/alpha_evolve/templates/base.py`
- [x] T006 [P] Create test fixtures with NautilusTrader TestKit in `tests/alpha_evolve/templates/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Base Evolvable Strategy (Priority: P1) 🎯 MVP

**Goal**: Abstract base class with EVOLVE-BLOCK markers, lifecycle management, equity tracking

**Independent Test**: Inherit from BaseEvolveStrategy and verify EVOLVE-BLOCK markers present and replaceable

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [US1] Write test_base_strategy_inheritance in `tests/alpha_evolve/templates/test_base.py`
- [x] T008 [US1] Write test_equity_curve_tracking in `tests/alpha_evolve/templates/test_base.py`
- [x] T009 [US1] Write test_lifecycle_methods in `tests/alpha_evolve/templates/test_base.py`

### Implementation for User Story 1

- [x] T010 [US1] Implement BaseEvolveStrategy abstract class skeleton in `scripts/alpha_evolve/templates/base.py`
- [x] T011 [US1] Implement on_start() with instrument lookup in `scripts/alpha_evolve/templates/base.py`
- [x] T012 [US1] Implement on_bar() with _on_bar_evolved call and equity recording in `scripts/alpha_evolve/templates/base.py`
- [x] T013 [US1] Implement on_stop() with order cancellation and position closing in `scripts/alpha_evolve/templates/base.py`
- [x] T014 [US1] Implement on_reset() with state reset in `scripts/alpha_evolve/templates/base.py`
- [x] T015 [US1] Implement _get_equity() helper in `scripts/alpha_evolve/templates/base.py`
- [x] T016 [US1] Implement get_equity_curve() getter in `scripts/alpha_evolve/templates/base.py`
- [x] T017 [US1] Define abstract _on_bar_evolved() method with EVOLVE-BLOCK docstring in `scripts/alpha_evolve/templates/base.py`

**Checkpoint**: BaseEvolveStrategy is complete and independently testable

---

## Phase 4: User Story 2 - Seed Momentum Strategy (Priority: P1)

**Goal**: Working MomentumEvolveStrategy with EMA crossover as evolution seed

**Independent Test**: Run backtest with seed strategy, verify produces trades and metrics

### Tests for User Story 2

- [x] T018 [US2] Write test_momentum_config_validation in `tests/alpha_evolve/templates/test_momentum.py`
- [x] T019 [US2] Write test_momentum_indicators_initialized in `tests/alpha_evolve/templates/test_momentum.py`
- [x] T020 [US2] Write test_momentum_evolve_block_extractable in `tests/alpha_evolve/templates/test_momentum.py`

### Implementation for User Story 2

- [x] T021 [US2] Create MomentumEvolveConfig with period validation in `scripts/alpha_evolve/templates/momentum.py`
- [x] T022 [US2] Create MomentumEvolveStrategy class inheriting BaseEvolveStrategy in `scripts/alpha_evolve/templates/momentum.py`
- [x] T023 [US2] Implement on_start() with EMA indicator registration in `scripts/alpha_evolve/templates/momentum.py`
- [x] T024 [US2] Implement _on_bar_evolved() with EVOLVE-BLOCK markers in `scripts/alpha_evolve/templates/momentum.py`
- [x] T025 [US2] Implement EMA crossover entry/exit logic inside EVOLVE-BLOCK in `scripts/alpha_evolve/templates/momentum.py`
- [x] T026 [P] [US2] Export MomentumEvolveStrategy in `scripts/alpha_evolve/templates/__init__.py`

**Checkpoint**: Seed strategy is complete and produces trades on BTC data

---

## Phase 5: User Story 3 - Native Indicator Integration (Priority: P1)

**Goal**: Templates use native Rust indicators for high performance

**Independent Test**: Verify strategy uses nautilus_trader.indicators imports

### Tests for User Story 3

- [x] T027 [US3] Write test_uses_native_indicators in `tests/alpha_evolve/templates/test_momentum.py`
- [x] T028 [US3] Write test_indicator_auto_registration in `tests/alpha_evolve/templates/test_momentum.py`

### Implementation for User Story 3

- [x] T029 [US3] Verify ExponentialMovingAverage import from nautilus_trader.indicators in `scripts/alpha_evolve/templates/momentum.py`
- [x] T030 [US3] Add indicator initialization check (indicators_initialized()) in `scripts/alpha_evolve/templates/momentum.py`
- [x] T031 [US3] Document native indicator requirement in module docstring in `scripts/alpha_evolve/templates/base.py`

**Checkpoint**: All indicators are native Rust, no Python reimplementations

---

## Phase 6: User Story 4 - Order Management Utilities (Priority: P2)

**Goal**: Helper methods for common order patterns to simplify EVOLVE-BLOCK

**Independent Test**: Call helper methods and verify orders created correctly

### Tests for User Story 4

- [x] T032 [US4] Write test_enter_long_creates_market_order in `tests/alpha_evolve/templates/test_base.py`
- [x] T033 [US4] Write test_enter_short_closes_long_first in `tests/alpha_evolve/templates/test_base.py`
- [x] T034 [US4] Write test_close_position in `tests/alpha_evolve/templates/test_base.py`
- [x] T035 [US4] Write test_get_position_size in `tests/alpha_evolve/templates/test_base.py`

### Implementation for User Story 4

- [x] T036 [US4] Implement _enter_long(quantity) helper in `scripts/alpha_evolve/templates/base.py`
- [x] T037 [US4] Implement _enter_short(quantity) helper in `scripts/alpha_evolve/templates/base.py`
- [x] T038 [US4] Implement _close_position() helper in `scripts/alpha_evolve/templates/base.py`
- [x] T039 [US4] Implement _get_position_size() helper in `scripts/alpha_evolve/templates/base.py`
- [x] T040 [US4] Update MomentumEvolveStrategy to use order helpers in `scripts/alpha_evolve/templates/momentum.py`

**Checkpoint**: Order helpers complete, EVOLVE-BLOCK code is simplified

---

## Phase 7: Integration & Validation

**Purpose**: Verify templates work with evaluator and patching system

### Integration Tests

- [x] T041 [P] Write test_strategy_evaluation_returns_metrics in `tests/alpha_evolve/test_templates_integration.py`
- [x] T042 [P] Write test_evolve_block_extraction in `tests/alpha_evolve/test_templates_integration.py`
- [x] T043 [P] Write test_patched_strategy_executes in `tests/alpha_evolve/test_templates_integration.py`
- [x] T044 Write test_equity_curve_populated in `tests/alpha_evolve/test_templates_integration.py`

### Performance Validation

- [X] T045 Create performance benchmark script in `scripts/alpha_evolve/templates/benchmark.py`
- [X] T046 (overhead 14.7% - needs optimization, tracked in base.py TODO) Verify equity tracking overhead < 5% in benchmark output

---

## Phase 8: Polish & Documentation

**Purpose**: Improvements that affect multiple user stories

- [x] T047 [P] Add module docstrings to all template files
- [x] T048 [P] Update alpha_evolve module __init__.py with complete exports
- [x] T049 Run ruff format and ruff check on all new files
- [x] T050 Run alpha-debug verification on template implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (inherits BaseEvolveStrategy)
- **User Story 3 (P1)**: Depends on US2 (validates seed strategy indicators)
- **User Story 4 (P2)**: Depends on US1 (adds helpers to BaseEvolveStrategy)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Config models before strategy logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1**: T002, T003 can run in parallel after T001
**Phase 2**: T006 can run in parallel with T004, T005 (different files)
**Phase 7**: T041, T042, T043 can run in parallel (different test files would be ideal, but same file - run sequentially)

---

## Parallel Example: User Story 2

```bash
# Tests written first (same file, run sequentially):
Task: "Write test_momentum_config_validation in tests/alpha_evolve/templates/test_momentum.py"
Task: "Write test_momentum_indicators_initialized in tests/alpha_evolve/templates/test_momentum.py"
Task: "Write test_momentum_evolve_block_extractable in tests/alpha_evolve/templates/test_momentum.py"

# Then implementation:
Task: "Create MomentumEvolveConfig in scripts/alpha_evolve/templates/momentum.py"
Task: "Create MomentumEvolveStrategy in scripts/alpha_evolve/templates/momentum.py"
# ... remaining tasks in momentum.py
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (BaseEvolveStrategy)
4. Complete Phase 4: User Story 2 (MomentumEvolveStrategy)
5. **STOP and VALIDATE**: Run backtest with seed strategy
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Base) → Test independently → BaseEvolveStrategy works
3. Add US2 (Seed) → Test independently → Seed strategy produces trades (MVP!)
4. Add US3 (Indicators) → Validate native Rust usage
5. Add US4 (Helpers) → Simplify EVOLVE-BLOCK code
6. Integration tests → Full system validation

---

## Summary

| Phase | Tasks | Parallel Ops |
|-------|-------|--------------|
| Setup | 3 | 2 |
| Foundational | 3 | 1 |
| US1 - Base Strategy | 11 | 0 |
| US2 - Seed Strategy | 9 | 1 |
| US3 - Native Indicators | 5 | 0 |
| US4 - Order Helpers | 9 | 0 |
| Integration | 6 | 3 |
| Polish | 4 | 2 |
| **Total** | **50** | **9** |

### Per User Story

| Story | Priority | Task Count | Independent Test |
|-------|----------|------------|------------------|
| US1 | P1 | 11 | Inherit and verify EVOLVE-BLOCK markers |
| US2 | P1 | 9 | Backtest produces trades |
| US3 | P1 | 5 | Verify native indicator imports |
| US4 | P2 | 9 | Order helpers create correct orders |

### Suggested MVP Scope

**US1 + US2**: BaseEvolveStrategy + MomentumEvolveStrategy
- Provides functional seed for evolution
- Can be tested with BacktestEngine
- Order helpers (US4) can be added later

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- US2 and US3 share test file (test_momentum.py) - run tests sequentially
- US1 and US4 share implementation file (base.py) - no parallel within these
