# Tasks: Plotly Backtest Tearsheets

**Input**: Design documents from `/specs/004-plotly-backtest-tearsheets/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included per TDD discipline from constitution (coverage > 80%)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and tearsheet module structure

- [x] T001 Create tearsheet module directory structure: `strategies/common/tearsheet/`
- [x] T002 [P] Create module __init__.py with public API exports in `strategies/common/tearsheet/__init__.py`
- [x] T003 [P] Verify NautilusTrader visualization extra is installed in nightly environment
- [x] T004 [P] Create test directory structure: `tests/test_tearsheets.py` and `tests/integration/test_tearsheet_integration.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create base test fixtures for BacktestEngine mocking in `tests/conftest.py`
- [x] T006 [P] Create sample backtest data fixture (1-year daily BTCUSDT) in `tests/fixtures/sample_backtest_data.py`
- [x] T007 [P] Create project theme registration module in `strategies/common/tearsheet/themes.py`
- [x] T008 Register `nautilus_dev` custom theme with brand colors in `strategies/common/tearsheet/themes.py`
- [x] T009 Create edge case handler utilities in `strategies/common/tearsheet/edge_cases.py`
- [x] T010 Implement zero-trades detection and warning in `strategies/common/tearsheet/edge_cases.py`
- [x] T011 Implement open-positions-at-end detection (epoch bug workaround) in `strategies/common/tearsheet/edge_cases.py`
- [x] T011a [P] Verify native themes (`plotly_white`, `plotly_dark`, `nautilus`, `nautilus_dark`) work correctly
- [x] T011b [P] Implement long backtest handling (10+ years) with ScatterGL in `strategies/common/tearsheet/edge_cases.py`
- [x] T011c [P] Implement high-frequency trade aggregation (1000+ trades/day) in `strategies/common/tearsheet/edge_cases.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Backtest Report (Priority: P1) 🎯 MVP

**Goal**: Generate comprehensive HTML tearsheet from BacktestEngine results

**Independent Test**: Run backtest with sample strategy, generate tearsheet, verify all 8 chart types render correctly

### Tests for User Story 1

- [x] T012 [P] [US1] Unit test for create_tearsheet wrapper in `tests/test_tearsheets.py::test_create_tearsheet_basic`
- [x] T013 [P] [US1] Unit test for tearsheet output file creation in `tests/test_tearsheets.py::test_tearsheet_file_created`
- [x] T014 [P] [US1] Unit test for HTML self-contained check in `tests/test_tearsheets.py::test_tearsheet_self_contained`
- [x] T015 [P] [US1] Integration test with real BacktestEngine in `tests/integration/test_tearsheet_integration.py::test_full_tearsheet_generation`

### Implementation for User Story 1

- [x] T016 [US1] Create tearsheet wrapper function in `strategies/common/tearsheet/core.py`
- [x] T017 [US1] Implement edge case pre-checks (zero trades, open positions) in wrapper
- [x] T018 [US1] Add logging for tearsheet generation process in `strategies/common/tearsheet/core.py`
- [x] T019 [US1] Verify all 8 built-in charts render via integration test
- [x] T020 [US1] Document basic usage example in `strategies/common/tearsheet/__init__.py` docstring

**Checkpoint**: User Story 1 complete - can generate basic tearsheets with all 8 charts

---

## Phase 4: User Story 2 - Equity Curve & Drawdown Analysis (Priority: P1)

**Goal**: Verify equity curve and drawdown charts work correctly with proper interactive features

**Independent Test**: Generate tearsheet, verify equity curve shows cumulative returns and drawdown periods highlighted

### Tests for User Story 2

- [x] T021 [P] [US2] Unit test for equity curve data extraction in `tests/test_tearsheets.py::test_equity_curve_data`
- [x] T022 [P] [US2] Unit test for drawdown calculation verification in `tests/test_tearsheets.py::test_drawdown_calculation`
- [x] T023 [P] [US2] Integration test for equity+drawdown chart interactivity in `tests/integration/test_tearsheet_integration.py::test_equity_drawdown_charts`

### Implementation for User Story 2

- [x] T024 [US2] Create equity curve validation helper in `strategies/common/tearsheet/validation.py`
- [x] T025 [US2] Create drawdown validation helper in `strategies/common/tearsheet/validation.py`
- [ ] T026 [US2] Add benchmark comparison support wrapper in `strategies/common/tearsheet/core.py`
- [ ] T027 [US2] Test with real 1-year BTCUSDT backtest data

**Checkpoint**: User Story 2 complete - equity and drawdown charts fully validated

---

## Phase 5: User Story 3 - Returns Heatmaps (Priority: P2)

**Goal**: Verify monthly and yearly returns heatmaps display correctly with color coding

**Independent Test**: Generate tearsheet with 2+ years of data, verify monthly heatmap shows correct values

### Tests for User Story 3

- [x] T028 [P] [US3] Unit test for monthly returns extraction in `tests/test_tearsheets.py::test_monthly_returns_data`
- [x] T029 [P] [US3] Unit test for yearly returns extraction in `tests/test_tearsheets.py::test_yearly_returns_data`
- [x] T030 [P] [US3] Integration test for heatmap color coding in `tests/integration/test_tearsheet_integration.py::test_returns_heatmaps`

### Implementation for User Story 3

- [x] T031 [US3] Create returns data validation helper in `strategies/common/tearsheet/validation.py`
- [ ] T032 [US3] Add multi-year data handling check in edge_cases.py
- [ ] T033 [US3] Verify color coding for negative returns (red gradient)

**Checkpoint**: User Story 3 complete - heatmaps display seasonal patterns correctly

---

## Phase 6: User Story 4 - Trade Analysis (Priority: P2)

**Goal**: Verify trade distribution histogram and statistics table display correctly

**Independent Test**: Generate tearsheet with 100+ trades, verify trade distribution and stats table

### Tests for User Story 4

- [x] T034 [P] [US4] Unit test for trade distribution data in `tests/test_tearsheets.py::test_trade_distribution_data`
- [x] T035 [P] [US4] Unit test for stats table metrics in `tests/test_tearsheets.py::test_stats_table_metrics`
- [x] T036 [P] [US4] Integration test for bars_with_fills chart in `tests/integration/test_tearsheet_integration.py::test_trade_markers`

### Implementation for User Story 4

- [x] T037 [US4] Create trade metrics validation helper in `strategies/common/tearsheet/validation.py`
- [ ] T038 [US4] Add OHLC data availability check for bars_with_fills
- [ ] T039 [US4] Implement graceful degradation when OHLC missing (skip bars_with_fills chart)

**Checkpoint**: User Story 4 complete - trade analysis charts validated

---

## Phase 7: User Story 5 - Custom Charts Extension (Priority: P3)

**Goal**: Enable custom chart registration for strategy-specific metrics

**Independent Test**: Register custom chart, generate tearsheet, verify custom chart appears

### Tests for User Story 5

- [x] T040 [P] [US5] Unit test for chart registration in `tests/test_tearsheets.py::test_register_custom_chart`
- [x] T041 [P] [US5] Unit test for custom chart rendering in `tests/test_tearsheets.py::test_custom_chart_in_tearsheet`
- [x] T042 [P] [US5] Integration test for multiple custom charts in `tests/integration/test_tearsheet_integration.py::test_multiple_custom_charts`

### Implementation for User Story 5

- [x] T043 [US5] Create custom chart registration wrapper in `strategies/common/tearsheet/custom_charts.py`
- [x] T044 [US5] Create example custom chart (rolling volatility) in `strategies/common/tearsheet/custom_charts.py`
- [x] T045 [US5] Document custom chart creation in module docstring
- [x] T046 [US5] Add `register_custom_charts()` one-time setup function

**Checkpoint**: User Story 5 complete - custom charts can be registered and rendered

---

## Phase 8: User Story 6 - Multi-Strategy Comparison (Priority: P3)

**Goal**: Compare multiple strategy backtests side-by-side in single tearsheet

**Independent Test**: Run 3 backtests, generate comparison report, verify all strategies shown

### Tests for User Story 6

- [x] T047 [P] [US6] Unit test for StrategyMetrics dataclass in `tests/test_tearsheets.py::test_strategy_metrics_from_engine`
- [x] T048 [P] [US6] Unit test for ComparisonConfig validation in `tests/test_tearsheets.py::test_comparison_config_validation`
- [x] T049 [P] [US6] Unit test for comparison equity chart in `tests/test_tearsheets.py::test_comparison_equity_overlay`
- [x] T050 [P] [US6] Integration test for full comparison tearsheet in `tests/integration/test_tearsheet_integration.py::test_multi_strategy_comparison`

### Implementation for User Story 6

- [x] T051 [US6] Create StrategyMetrics dataclass in `strategies/common/tearsheet/comparison.py`
- [x] T052 [US6] Create ComparisonConfig dataclass in `strategies/common/tearsheet/comparison.py`
- [x] T053 [E] [US6] Implement comparison equity chart renderer in `strategies/common/tearsheet/comparison.py` (via alpha-evolve)
- [x] T054 [US6] Implement comparison drawdown chart renderer in `strategies/common/tearsheet/comparison.py`
- [x] T055 [US6] Implement comparison stats table renderer in `strategies/common/tearsheet/comparison.py`
- [x] T056 [US6] Create `create_comparison_tearsheet()` main function in `strategies/common/tearsheet/comparison.py`
- [x] T057 [US6] Register comparison charts on module import in `strategies/common/tearsheet/__init__.py`

**Checkpoint**: User Story 6 complete - multi-strategy comparison fully functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T058 [P] Performance test for 1-year daily backtest (< 5 seconds) in `tests/test_tearsheets.py::test_performance_1year`
- [x] T059 [P] Performance test for 10K+ data points in `tests/test_tearsheets.py::test_performance_large_dataset`
- [x] T060 [P] HTML file size validation (< 2MB) in `tests/test_tearsheets.py::test_file_size_limit`
- [ ] T061 [P] Documentation update in `docs/concepts/tearsheets.md`
- [x] T062 [P] Add quickstart example to module __init__.py
- [ ] T063 Code cleanup and type hint verification (mypy)
- [x] T064 Run ruff format and ruff check for code style
- [ ] T065 Run alpha-debug verification for edge cases

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 - can run in parallel
  - US3 and US4 are both P2 - can run in parallel after US1/US2
  - US5 and US6 are both P3 - can run in parallel after US3/US4
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

| Story | Priority | Dependencies | Can Start After |
|-------|----------|--------------|-----------------|
| US1 - Generate Report | P1 | Foundational | Phase 2 |
| US2 - Equity/Drawdown | P1 | Foundational | Phase 2 |
| US3 - Returns Heatmaps | P2 | Foundational | Phase 2 |
| US4 - Trade Analysis | P2 | Foundational | Phase 2 |
| US5 - Custom Charts | P3 | Foundational | Phase 2 |
| US6 - Multi-Strategy | P3 | Foundational | Phase 2 |

**Note**: All user stories are independently testable and can proceed in parallel if team capacity allows.

### Parallel Opportunities

- **Phase 1**: T002, T003, T004 can run in parallel
- **Phase 2**: T006, T007 can run in parallel
- **Phase 3-8**: All test tasks marked [P] within each story can run in parallel
- **Phase 9**: T058, T059, T060, T061, T062 can run in parallel

---

## Parallel Example: User Story 1 (MVP)

```bash
# Launch all tests for User Story 1 together:
Task: T012 "Unit test for create_tearsheet wrapper"
Task: T013 "Unit test for tearsheet output file creation"
Task: T014 "Unit test for HTML self-contained check"
Task: T015 "Integration test with real BacktestEngine"

# Wait for tests to fail (RED phase), then implement:
Task: T016 "Create tearsheet wrapper function"
Task: T017 "Implement edge case pre-checks"
# ... continue sequentially
```

---

## Parallel Example: User Story 6 (Comparison)

```bash
# Launch all tests for User Story 6 together:
Task: T047 "Unit test for StrategyMetrics dataclass"
Task: T048 "Unit test for ComparisonConfig validation"
Task: T049 "Unit test for comparison equity chart"
Task: T050 "Integration test for full comparison tearsheet"

# Wait for tests to fail (RED phase), then implement:
Task: T051 "Create StrategyMetrics dataclass"
Task: T052 "Create ComparisonConfig dataclass"
# T053 marked [E] - triggers alpha-evolve for complex chart rendering
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - basic tearsheet generation works

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → **MVP Complete!** (basic tearsheet)
3. Add User Story 2 → Test → Equity/Drawdown validated
4. Add User Story 3 + 4 → Test → Returns heatmaps + Trade analysis
5. Add User Story 5 → Test → Custom chart extensibility
6. Add User Story 6 → Test → Multi-strategy comparison

### Recommended Order

| Step | Stories | Deliverable |
|------|---------|-------------|
| 1 | Setup + Foundational | Infrastructure ready |
| 2 | US1 + US2 (P1s in parallel) | Core tearsheet with equity/drawdown |
| 3 | US3 + US4 (P2s in parallel) | Full analytics suite |
| 4 | US5 + US6 (P3s in parallel) | Extensibility + comparison |
| 5 | Polish | Production-ready |

---

## Task Summary

| Phase | Task Count | Parallel Tasks | Story Tasks |
|-------|------------|----------------|-------------|
| Setup | 4 | 3 | 0 |
| Foundational | 10 | 5 | 0 |
| US1 - Generate Report | 9 | 4 | 9 |
| US2 - Equity/Drawdown | 7 | 3 | 7 |
| US3 - Returns Heatmaps | 6 | 3 | 6 |
| US4 - Trade Analysis | 6 | 3 | 6 |
| US5 - Custom Charts | 7 | 3 | 7 |
| US6 - Multi-Strategy | 11 | 4 | 11 |
| Polish | 8 | 5 | 0 |
| **Total** | **68** | **33** | **46** |

---

## Notes

- [P] tasks = different files, no dependencies (processed by /speckit.implement)
- [E] tasks = complex algorithms triggering alpha-evolve (T053)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Native First: Uses NautilusTrader's existing tearsheet system, only adds custom extensions
