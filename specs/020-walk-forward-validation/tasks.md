# Tasks: Walk-Forward Validation

**Input**: Design documents from `/specs/020-walk-forward-validation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md
**Branch**: `020-walk-forward-validation`

**Organization**: Tasks grouped by user story (functional requirements FR-001 to FR-005) for independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger for complex algorithmic tasks
- **[Story]**: Which user story (FR-XXX mapped to US1-US5)

---

## Phase 1: Setup (Project Structure)

**Purpose**: Create walk_forward module structure and dependencies

- [X] T001 Create module directory structure: `scripts/alpha_evolve/walk_forward/`
- [X] T002 [P] Create `scripts/alpha_evolve/walk_forward/__init__.py` with public exports
- [X] T003 [P] Create `tests/test_walk_forward/__init__.py` and `conftest.py`

---

## Phase 2: Foundational (Core Models)

**Purpose**: Data models that ALL user stories depend on - MUST complete before implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `WalkForwardConfig` Pydantic model in `scripts/alpha_evolve/walk_forward/config.py`
  - Fields: data_start, data_end, train_months, test_months, step_months
  - Fields: embargo_before_days (default 5), embargo_after_days (default 3)
  - Fields: min_windows, min_profitable_windows_pct, min_test_sharpe
  - Fields: max_drawdown_threshold, min_robustness_score, seed
  - Validation rules per data-model.md

- [X] T005 [P] Create `Window` dataclass in `scripts/alpha_evolve/walk_forward/models.py`
  - Fields: window_id, train_start, train_end, test_start, test_end
  - Constraints: train_start < train_end <= test_start < test_end

- [X] T006 [P] Create `WindowMetrics` dataclass in `scripts/alpha_evolve/walk_forward/models.py`
  - Fields: sharpe_ratio, calmar_ratio, max_drawdown, total_return, win_rate, trade_count

- [X] T007 Create `WindowResult` dataclass in `scripts/alpha_evolve/walk_forward/models.py`
  - Fields: window, train_metrics, test_metrics
  - Computed: degradation_ratio = test_sharpe / train_sharpe

- [X] T008 Create `WalkForwardResult` dataclass in `scripts/alpha_evolve/walk_forward/models.py`
  - Fields: config, windows, robustness_score, passed
  - Fields: deflated_sharpe_ratio, probability_backtest_overfitting (Lopez de Prado)
  - Computed: profitable_windows_pct, avg_test_sharpe, worst_drawdown
  - Field: validation_time_seconds

- [X] T009 [P] Create test fixtures in `tests/test_walk_forward/conftest.py`
  - Sample WalkForwardConfig with test dates
  - Mock WindowMetrics for consistent testing
  - Sample WindowResult fixtures

- [X] T010 Write unit tests for config validation in `tests/test_walk_forward/test_config.py`
  - Test valid config creation
  - Test validation errors (start > end, negative values)
  - Test defaults

**Checkpoint**: Foundation complete - all data models defined and tested

---

## Phase 3: User Story 1 - Window Generation (FR-001) 🎯 MVP

**Goal**: Generate rolling walk-forward windows from date range with embargo periods

**Independent Test**: Given a date range, verify correct train/test window boundaries with gaps

### Implementation for User Story 1

- [X] T011 [US1] Implement `_generate_windows()` in `scripts/alpha_evolve/walk_forward/validator.py`
  - Input: WalkForwardConfig with date range
  - Output: list[Window] with rolling windows
  - Apply embargo_before_days gap between train_end and test_start
  - Apply embargo_after_days gap after test_end (for next window)
  - Handle edge case: insufficient data for min_windows

- [X] T012 [US1] Write unit tests for window generation in `tests/test_walk_forward/test_window_generation.py`
  - Test 24-month data → 5 windows with 6-month train, 3-month test, 3-month step
  - Test embargo period applied correctly
  - Test edge case: data too short for min_windows
  - Test window boundaries don't overlap test periods

**Checkpoint**: Window generation produces correct date ranges with embargo periods

---

## Phase 4: User Story 2 - Validator Core (FR-002, FR-003)

**Goal**: WalkForwardValidator evaluates strategy on each window, collecting metrics

**Independent Test**: Run validator on mock strategy, verify train/test metrics collected per window

### Implementation for User Story 2

- [X] T013 [US2] Create `WalkForwardValidator` class skeleton in `scripts/alpha_evolve/walk_forward/validator.py`
  - Constructor: config, evaluator (StrategyEvaluator dependency)
  - Public method: async validate(strategy_code: str) -> WalkForwardResult

- [X] T014 [US2] Implement `validate()` method in `scripts/alpha_evolve/walk_forward/validator.py`
  - Generate windows via _generate_windows()
  - For each window:
    - Call evaluator.evaluate() for train period
    - Call evaluator.evaluate() for test period
    - Create WindowResult with train/test metrics
  - Track validation_time_seconds
  - Return WalkForwardResult

- [X] T015 [US2] Create mock StrategyEvaluator for testing in `tests/test_walk_forward/conftest.py`
  - Returns predictable WindowMetrics for given date ranges
  - Simulates async evaluate() calls

- [X] T016 [US2] Write integration test with mock evaluator in `tests/test_walk_forward/test_validator.py`
  - Test validate() returns correct number of WindowResults
  - Test train/test periods passed correctly to evaluator
  - Test timing tracked

**Checkpoint**: Validator can evaluate strategy on multiple windows

---

## Phase 5: User Story 3 - Robustness Scoring (FR-004)

**Goal**: Calculate composite robustness score from window results

**Independent Test**: Given known WindowResults, verify robustness score calculation

### Implementation for User Story 3

- [X] T017 [E] [US3] Implement `calculate_robustness_score()` in `scripts/alpha_evolve/walk_forward/metrics.py`
  - Consistency (30%): 1 - normalized std dev of test returns
  - Profitability (40%): % of windows with positive test return
  - Degradation (30%): avg(min(test_sharpe/train_sharpe, 1.0))
  - Return score 0-100
  - Handle edge cases: zero train_sharpe, all negative returns

- [X] T018 [US3] Implement Deflated Sharpe Ratio (DSR) in `scripts/alpha_evolve/walk_forward/metrics.py`
  - Formula: DSR = Z⁻¹[Φ(SR) - ln(N)/√N] (Lopez de Prado Ch. 14)
  - Input: observed sharpe, number of trials
  - Adjusts for multiple testing and non-normal returns

- [X] T019 [US3] Implement Probability of Backtest Overfitting (PBO) in `scripts/alpha_evolve/walk_forward/metrics.py`
  - Formula: PBO = P[median(IS) < median(OOS)] (Lopez de Prado Ch. 11)
  - Generate combinatorial permutations of window orderings
  - Compare in-sample vs out-of-sample distributions
  - Return probability 0-1 (>0.5 indicates likely overfitting)

- [X] T020 [US3] Implement helper `simulate_combinatorial_paths()` in `scripts/alpha_evolve/walk_forward/metrics.py`
  - Shuffle window orderings for PBO calculation
  - Configurable n_permutations (default 100)
  - Return distribution of Sharpe ratios across paths

- [X] T021 [US3] Write unit tests for metrics in `tests/test_walk_forward/test_metrics.py`
  - Test robustness score with known inputs
  - Test edge cases: zero sharpe, single window, all losses
  - Test DSR < raw Sharpe always
  - Test PBO bounds (0-1)

**Checkpoint**: Robustness score and advanced metrics calculate correctly

---

## Phase 6: User Story 4 - Pass/Fail Criteria (FR-005)

**Goal**: Determine if strategy passes walk-forward validation

**Independent Test**: Given edge-case WindowResults, verify correct pass/fail determination

### Implementation for User Story 4

- [X] T022 [US4] Implement `_check_criteria()` in `scripts/alpha_evolve/walk_forward/validator.py`
  - robustness_score >= config.min_robustness_score
  - profitable_windows_pct >= config.min_profitable_windows_pct
  - worst_drawdown <= config.max_drawdown_threshold
  - majority of windows have test_sharpe >= config.min_test_sharpe
  - Return bool

- [X] T023 [US4] Wire metrics and criteria into validate() method
  - Call _calculate_robustness() to get score
  - Call _check_criteria() to get passed bool
  - Add deflated_sharpe_ratio and probability_backtest_overfitting to result

- [X] T024 [US4] Write pass/fail criteria tests in `tests/test_walk_forward/test_validator.py`
  - Test passing scenario (all criteria met)
  - Test failing: low robustness score
  - Test failing: too few profitable windows
  - Test failing: excessive drawdown
  - Test failing: low test sharpe

**Checkpoint**: Validation pass/fail logic works correctly

---

## Phase 7: User Story 5 - Reporting & Integration (NFR)

**Goal**: Generate reports and integrate with AlphaEvolveController

**Independent Test**: Generate report from WalkForwardResult, verify markdown output

### Implementation for User Story 5

- [X] T025 [P] [US5] Implement `generate_report()` in `scripts/alpha_evolve/walk_forward/report.py`
  - Markdown format per quickstart.md
  - Include: robustness score, pass/fail, DSR, PBO
  - Window results table with train/test metrics
  - Interpretation guidance

- [X] T026 [P] [US5] Implement JSON export in `scripts/alpha_evolve/walk_forward/report.py`
  - Export WalkForwardResult to JSON for programmatic use
  - Include all computed metrics

- [X] T027 [US5] Integrate with AlphaEvolveController in `scripts/alpha_evolve/controller.py`
  - Add `evolve_with_validation()` method
  - Run evolution, then validate best strategy
  - Return None if validation fails
  - Log warning with robustness score on failure

- [X] T028 [US5] Create CLI command in `scripts/alpha_evolve/walk_forward/cli.py`
  - `validate --strategy <path> --start <date> --end <date>`
  - `report --strategy <path> --output <path>`
  - Use argparse or typer

- [X] T029 [US5] Write integration test for full pipeline in `tests/test_walk_forward/test_integration.py`
  - Test evolve_with_validation() flow
  - Test CLI command execution
  - Test report generation

**Checkpoint**: Full integration complete, CLI and reports working

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and verification

- [X] T030 [P] Update public exports in `scripts/alpha_evolve/walk_forward/__init__.py`
  - Export: WalkForwardConfig, WalkForwardValidator, WalkForwardResult, generate_report

- [X] T031 [P] Add docstrings to all public classes and methods
  - Follow Google-style docstrings
  - Include examples in docstrings

- [X] T032 Update `docs/ARCHITECTURE.md` with walk-forward validation component
  - Add to Alpha-Evolve Pipeline section
  - Document data flow

- [X] T033 Run alpha-debug verification on walk_forward module
  - 3-5 rounds of bug hunting
  - Focus on edge cases in date arithmetic
  - Verify no lookahead bias

- [X] T034 Verify test coverage >= 80% for walk_forward module (achieved 92%)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3-7 (User Stories)**: All depend on Phase 2 completion
  - US1 (Window Generation) → independent
  - US2 (Validator Core) → depends on US1
  - US3 (Robustness Scoring) → depends on US2
  - US4 (Pass/Fail) → depends on US3
  - US5 (Reporting) → depends on US4
- **Phase 8 (Polish)**: Depends on all user stories

### Parallel Opportunities

**Phase 1-2** (Foundational):
```bash
# Can run in parallel:
T002, T003  # Different directories
T004, T005, T006  # Different models in different concerns
T009  # Test fixtures independent
```

**Phase 7** (Reporting):
```bash
# Can run in parallel:
T025, T026  # Different report formats
```

---

## Implementation Strategy

### MVP First (User Stories 1-4)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T010)
3. Complete Phase 3: US1 - Window Generation (T011-T012)
4. Complete Phase 4: US2 - Validator Core (T013-T016)
5. Complete Phase 5: US3 - Robustness Scoring (T017-T021)
6. Complete Phase 6: US4 - Pass/Fail (T022-T024)
7. **STOP and VALIDATE**: Core validation working
8. Add Phase 7: US5 - Reporting & Integration
9. Complete Phase 8: Polish

### Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1. Setup | T001-T003 | Module structure |
| 2. Foundational | T004-T010 | Core models |
| 3. US1 | T011-T012 | Window generation |
| 4. US2 | T013-T016 | Validator core |
| 5. US3 | T017-T021 | Robustness scoring |
| 6. US4 | T022-T024 | Pass/fail criteria |
| 7. US5 | T025-T029 | Reporting & integration |
| 8. Polish | T030-T034 | Documentation & cleanup |

**Total Tasks**: 34
**Parallel Opportunities**: T002-T003, T004-T006, T009, T025-T026
**Alpha-Evolve Task**: T017 (robustness score algorithm)

---

## Notes

- [E] on T017 triggers alpha-evolve for robustness score algorithm exploration
- Lopez de Prado metrics (DSR, PBO) are in T018-T020 (research.md references)
- Embargo periods (embargo_before_days, embargo_after_days) per plan.md Decision 4
- All window arithmetic uses timedelta, not df.iterrows()
- Integration with existing StrategyEvaluator (Spec 007 dependency)
