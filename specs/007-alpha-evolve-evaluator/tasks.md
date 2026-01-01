# Tasks: Alpha-Evolve Backtest Evaluator

**Feature Branch**: `007-alpha-evolve-evaluator`
**Input**: Design documents from `/specs/007-alpha-evolve-evaluator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks

---

## Phase 1: Setup

**Purpose**: Project initialization and test infrastructure

- [x] T001 Create evaluator module file at scripts/alpha_evolve/evaluator.py
- [x] T002 Create test file at tests/alpha_evolve/test_evaluator.py
- [x] T003 Update exports in scripts/alpha_evolve/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core dataclasses and infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement BacktestConfig dataclass in scripts/alpha_evolve/evaluator.py
- [x] T005 Implement EvaluationRequest dataclass in scripts/alpha_evolve/evaluator.py
- [x] T006 Implement EvaluationResult dataclass in scripts/alpha_evolve/evaluator.py
- [x] T007 Create StrategyEvaluator class skeleton with __init__ in scripts/alpha_evolve/evaluator.py
- [x] T008 [P] Add test fixtures for sample strategy code in tests/alpha_evolve/conftest.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Dynamic Strategy Evaluation (Priority: P1)

**Goal**: Load and execute strategy code from strings, return metrics or errors

**Independent Test**: Provide valid strategy code string → receive EvaluationResult with metrics

### Tests for User Story 1

- [x] T009 [US1] Write test_load_strategy_valid_code in tests/alpha_evolve/test_evaluator.py
- [x] T010 [US1] Write test_load_strategy_syntax_error in tests/alpha_evolve/test_evaluator.py
- [x] T011 [US1] Write test_load_strategy_missing_class in tests/alpha_evolve/test_evaluator.py
- [x] T012 [US1] Write test_evaluate_sync_success in tests/alpha_evolve/test_evaluator.py
- [x] T013 [US1] Write test_evaluate_sync_runtime_error in tests/alpha_evolve/test_evaluator.py
- [x] T014 [US1] Write test_evaluate_timeout in tests/alpha_evolve/test_evaluator.py

### Implementation for User Story 1

- [x] T015 [US1] Implement _validate_syntax() method using ast.parse in scripts/alpha_evolve/evaluator.py
- [x] T016 [US1] Implement _load_strategy() method using exec + types.ModuleType in scripts/alpha_evolve/evaluator.py
- [x] T017 [US1] Implement _configure_venue() helper for BacktestEngine setup in scripts/alpha_evolve/evaluator.py
- [x] T018 [US1] Implement _configure_data() helper for ParquetDataCatalog loading in scripts/alpha_evolve/evaluator.py
- [x] T019 [E] [US1] Implement _run_backtest() method with BacktestEngine in scripts/alpha_evolve/evaluator.py
- [x] T020 [US1] Implement evaluate_sync() public method in scripts/alpha_evolve/evaluator.py
- [x] T021 [US1] Add timeout handling with asyncio.wait_for in evaluate_sync() in scripts/alpha_evolve/evaluator.py

**Checkpoint**: US1 complete - can evaluate strategy code and return success/error results

---

## Phase 4: User Story 2 - KPI Extraction (Priority: P1)

**Goal**: Extract standardized fitness metrics from completed backtests

**Independent Test**: Run backtest → verify all expected metrics present with correct values

### Tests for User Story 2

- [x] T022 [US2] Write test_extract_metrics_profitable in tests/alpha_evolve/test_evaluator.py
- [x] T023 [US2] Write test_extract_metrics_no_trades in tests/alpha_evolve/test_evaluator.py
- [x] T024 [US2] Write test_extract_metrics_negative_returns in tests/alpha_evolve/test_evaluator.py
- [x] T025 [US2] Write test_calculate_calmar_ratio in tests/alpha_evolve/test_evaluator.py
- [x] T026 [US2] Write test_calculate_cagr in tests/alpha_evolve/test_evaluator.py

### Implementation for User Story 2

- [x] T027 [US2] Implement _calculate_cagr() helper method in scripts/alpha_evolve/evaluator.py
- [x] T028 [US2] Implement _calculate_calmar() helper method in scripts/alpha_evolve/evaluator.py
- [x] T029 [E] [US2] Implement _extract_metrics() using PortfolioAnalyzer in scripts/alpha_evolve/evaluator.py
- [x] T030 [US2] Handle edge cases (no trades, division by zero) in _extract_metrics() in scripts/alpha_evolve/evaluator.py
- [x] T031 [US2] Integrate metrics extraction into evaluate_sync() in scripts/alpha_evolve/evaluator.py

**Checkpoint**: US2 complete - evaluation returns standardized FitnessMetrics

---

## Phase 5: User Story 3 - Historical Data Configuration (Priority: P2)

**Goal**: Configure backtest data source (symbols, date ranges, venue)

**Independent Test**: Configure different symbols/dates → verify backtest uses correct data

### Tests for User Story 3

- [x] T032 [US3] Write test_config_instrument_id in tests/alpha_evolve/test_evaluator.py
- [x] T033 [US3] Write test_config_date_range in tests/alpha_evolve/test_evaluator.py
- [x] T034 [US3] Write test_config_invalid_catalog_path in tests/alpha_evolve/test_evaluator.py
- [x] T035 [US3] Write test_config_missing_instrument in tests/alpha_evolve/test_evaluator.py

### Implementation for User Story 3

- [x] T036 [US3] Add catalog path validation in _configure_data() in scripts/alpha_evolve/evaluator.py
- [x] T037 [US3] Add instrument existence check in _configure_data() in scripts/alpha_evolve/evaluator.py
- [x] T038 [US3] Add date range validation in _configure_data() in scripts/alpha_evolve/evaluator.py
- [x] T039 [US3] Return data error_type for missing data conditions in scripts/alpha_evolve/evaluator.py

**Checkpoint**: US3 complete - data configuration is validated before backtest

---

## Phase 6: User Story 4 - Concurrent Evaluation Limits (Priority: P2)

**Goal**: Limit concurrent evaluations to prevent memory exhaustion

**Independent Test**: Submit multiple evaluations → verify max_concurrent respected

### Tests for User Story 4

- [x] T040 [US4] Write test_concurrent_limit_respected in tests/alpha_evolve/test_evaluator.py
- [x] T041 [US4] Write test_concurrent_slot_freed_on_failure in tests/alpha_evolve/test_evaluator.py
- [x] T042 [US4] Write test_async_evaluate in tests/alpha_evolve/test_evaluator.py

### Implementation for User Story 4

- [x] T043 [US4] Add asyncio.Semaphore to StrategyEvaluator.__init__ in scripts/alpha_evolve/evaluator.py
- [x] T044 [US4] Implement async evaluate() method with semaphore in scripts/alpha_evolve/evaluator.py
- [x] T045 [US4] Add asyncio.to_thread wrapper for blocking backtest in scripts/alpha_evolve/evaluator.py
- [x] T046 [US4] Add asyncio.wait_for timeout wrapper in evaluate() in scripts/alpha_evolve/evaluator.py

**Checkpoint**: US4 complete - concurrent evaluations respect memory limits

---

## Phase 7: Polish & Integration

**Purpose**: Final integration, edge cases, and cleanup

- [X] T047 [P] Write integration test with full evaluation cycle in tests/alpha_evolve/test_integration.py
- [X] T048 [P] Write integration test with ProgramStore in tests/alpha_evolve/test_integration.py
- [x] T049 Add module docstring and type hints review in scripts/alpha_evolve/evaluator.py
- [x] T050 Run ruff check and format on scripts/alpha_evolve/evaluator.py
- [X] T051 Run alpha-debug verification on evaluator implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Core evaluation
- **User Story 2 (Phase 4)**: Depends on US1 (needs working evaluate_sync)
- **User Story 3 (Phase 5)**: Depends on Foundational - Can run parallel to US1/US2
- **User Story 4 (Phase 6)**: Depends on US1 (needs working evaluate_sync)
- **Polish (Phase 7)**: Depends on all user stories

### User Story Dependencies

```
Phase 2 (Foundational)
         │
         ├──────────────┬───────────────┐
         ▼              ▼               ▼
    US1 (P1)       US3 (P2)        (independent)
    Dynamic Eval   Data Config
         │
         ├───────────────┐
         ▼               ▼
    US2 (P1)        US4 (P2)
    KPI Extract     Concurrency
```

### Parallel Opportunities

**Within Phase 1 (Setup)**:
- T001, T002, T003 are sequential (depend on each other)

**Within Phase 2 (Foundational)**:
- T004, T005, T006 are sequential (same file, order matters)
- T008 [P] can run in parallel with dataclass tasks

**Within User Stories**:
- Tests within each story are sequential (same file)
- Implementation tasks are sequential (building on each other)
- US1 and US3 can run in parallel after Foundational
- US2 and US4 can run in parallel after US1

---

## Parallel Example: After Foundational

```bash
# Team A: User Story 1 (Dynamic Evaluation)
Task: "Implement _load_strategy() in evaluator.py"

# Team B: User Story 3 (Data Configuration) - Can run in parallel
Task: "Add catalog path validation in evaluator.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Dynamic Evaluation)
4. Complete Phase 4: User Story 2 (KPI Extraction)
5. **STOP and VALIDATE**: Can evaluate strategies and extract metrics
6. Deploy/demo if ready

### Full Implementation

1. Setup + Foundational → Foundation ready
2. US1 + US2 → Core evaluation working (MVP!)
3. US3 → Data configuration validation
4. US4 → Concurrency control
5. Polish → Integration tests, cleanup

---

## Summary

| Metric | Count |
|--------|-------|
| Total Tasks | 51 |
| Phase 1 (Setup) | 3 |
| Phase 2 (Foundational) | 5 |
| Phase 3 (US1 - Dynamic Eval) | 13 |
| Phase 4 (US2 - KPI Extract) | 10 |
| Phase 5 (US3 - Data Config) | 8 |
| Phase 6 (US4 - Concurrency) | 7 |
| Phase 7 (Polish) | 5 |

**MVP Scope**: Phases 1-4 (31 tasks) - Dynamic evaluation with KPI extraction
**Parallel Opportunities**: US1+US3 after Foundational, US2+US4 after US1

---

## Notes

- [P] tasks = different files, no dependencies
- [E] tasks = complex algorithms triggering alpha-evolve
- [US*] label maps task to specific user story
- Each user story is independently testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
