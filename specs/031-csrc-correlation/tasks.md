# Tasks: CSRC Correlation-Aware Allocation

**Input**: Design documents from `/specs/031-csrc-correlation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md (available)
**Branch**: `031-csrc-correlation`

**Tests**: Tests are REQUIRED per TDD discipline in constitution.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create base structure for correlation tracking module

- [X] T001 Create `strategies/common/adaptive_control/correlation_tracker.py` with module docstring and imports
- [X] T002 [P] Create `tests/unit/test_correlation_tracker.py` with test class skeleton
- [X] T003 [P] Create `tests/integration/test_csrc_walk_forward.py` with test class skeleton

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core correlation estimation infrastructure that MUST be complete before user stories

**Critical**: No user story work can begin until this phase is complete

- [X] T004 [E] Implement `OnlineStats` dataclass for single-strategy statistics (mean, var, n) in `strategies/common/adaptive_control/correlation_tracker.py`
- [X] T005 Implement `OnlineCorrelationMatrix.__init__()` with parameters (strategies, decay=0.99, shrinkage=0.1, min_samples=30) in `strategies/common/adaptive_control/correlation_tracker.py`
- [X] T006 [E] Implement Welford's online update algorithm for `_update_stats()` method in `strategies/common/adaptive_control/correlation_tracker.py`
- [X] T007 [E] Implement Ledoit-Wolf shrinkage function `_apply_shrinkage()` in `strategies/common/adaptive_control/correlation_tracker.py`
- [X] T008 Implement `OnlineCorrelationMatrix.update(returns: Dict[str, float])` using EMA for covariance updates in `strategies/common/adaptive_control/correlation_tracker.py`
- [X] T009 Implement `get_correlation_matrix() -> np.ndarray` returning shrunk N×N matrix in `strategies/common/adaptive_control/correlation_tracker.py`
- [X] T010 Write unit tests for `OnlineCorrelationMatrix` initialization in `tests/unit/test_correlation_tracker.py`
- [X] T011 Write unit tests for correlation convergence (synthetic data, known correlation 0.9, verify within 5% after 150 samples) in `tests/unit/test_correlation_tracker.py`

**Checkpoint**: Foundation ready - OnlineCorrelationMatrix can track correlations. User story implementation can begin.

---

## Phase 3: User Story 1 - Prevent Over-Allocation to Correlated Strategies (Priority: P1)

**Goal**: Add covariance-penalized objective function to ParticlePortfolio to reduce concentration in correlated strategies

**Independent Test**: Create portfolio with 3 synthetic correlated strategies (correlation > 0.8). Verify total allocation to correlated group is capped (max 50% combined vs 90% without CSRC).

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Write test `test_penalty_calculation_with_known_weights` verifying penalty formula in `tests/unit/test_correlation_tracker.py`
- [ ] T013 [P] [US1] Write test `test_concentration_reduction_with_correlated_strategies` (SC-001: 20% reduction) in `tests/integration/test_csrc_walk_forward.py`
- [ ] T014 [P] [US1] Write test `test_no_regression_for_uncorrelated_strategies` (SC-006: weights within 5% of baseline) in `tests/integration/test_csrc_walk_forward.py`

### Implementation for User Story 1

- [ ] T015 [E] [US1] Implement `calculate_covariance_penalty(weights, corr_matrix, strategy_indices)` function in `strategies/common/adaptive_control/correlation_tracker.py`
- [ ] T016 [US1] Add `lambda_penalty: float = 1.0` parameter to `ParticlePortfolio.__init__()` in `strategies/common/adaptive_control/particle_portfolio.py`
- [ ] T017 [US1] Add `correlation_tracker: Optional[OnlineCorrelationMatrix] = None` parameter to `ParticlePortfolio.__init__()` in `strategies/common/adaptive_control/particle_portfolio.py`
- [ ] T018 [US1] Modify `ParticlePortfolio.update()` to call correlation_tracker.update() if tracker provided in `strategies/common/adaptive_control/particle_portfolio.py`
- [ ] T019 [US1] Modify particle fitness calculation: `fitness = portfolio_return - lambda * covariance_penalty` in `strategies/common/adaptive_control/particle_portfolio.py`
- [ ] T020 [US1] Run tests T012-T014 and verify they PASS in `tests/`

**Checkpoint**: User Story 1 complete - ParticlePortfolio reduces concentration in correlated strategies

---

## Phase 4: User Story 2 - Online Correlation Matrix Update (Priority: P2)

**Goal**: Efficient O(N^2) correlation updates with < 1ms latency for 20 strategies

**Independent Test**: Stream synthetic returns with known correlation (0.8*R + noise). Verify correlation estimate converges to 0.8 within 150 samples. Benchmark < 1ms for 10 strategies.

### Tests for User Story 2

- [ ] T021 [P] [US2] Write test `test_correlation_convergence_with_known_data` (FR-009: converge within 150 samples) in `tests/unit/test_correlation_tracker.py`
- [ ] T022 [P] [US2] Write test `test_performance_10_strategies` (FR-006: < 1ms for 10 strategies) in `tests/unit/test_correlation_tracker.py`
- [ ] T023 [P] [US2] Write test `test_adaptive_correlation_regime_change` (correlation changes 0.5 → 0.9, adapts within 100 samples) in `tests/unit/test_correlation_tracker.py`

### Implementation for User Story 2

- [ ] T024 [US2] Optimize `OnlineCorrelationMatrix.update()` using NumPy vectorization in `strategies/common/adaptive_control/correlation_tracker.py`
- [ ] T025 [US2] Add performance assertions to ensure < 1ms per update in `strategies/common/adaptive_control/correlation_tracker.py`
- [ ] T026 [US2] Implement `get_pairwise_correlation(strat_a, strat_b)` helper method in `strategies/common/adaptive_control/correlation_tracker.py`
- [ ] T027 [US2] Run tests T021-T023 and verify they PASS in `tests/`

**Checkpoint**: User Story 2 complete - Efficient online correlation tracking

---

## Phase 5: User Story 3 - Covariance Penalty Tuning (Priority: P3)

**Goal**: Tunable lambda parameter with observability metrics (Herfindahl index, effective N strategies)

**Independent Test**: Run portfolio with lambda = [0.0, 0.5, 1.0, 2.0] on same dataset. Verify higher lambda reduces concentration.

### Tests for User Story 3

- [ ] T028 [P] [US3] Write test `test_lambda_zero_matches_baseline` (FR-007: lambda=0.0 gives same behavior) in `tests/integration/test_csrc_walk_forward.py`
- [ ] T029 [P] [US3] Write test `test_lambda_sensitivity` (higher lambda = more diversification) in `tests/integration/test_csrc_walk_forward.py`
- [ ] T030 [P] [US3] Write test `test_concentration_metrics_reported` (FR-008: Herfindahl, effective N reported) in `tests/unit/test_correlation_tracker.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `CorrelationMetrics` dataclass (herfindahl_index, effective_n_strategies, max_pairwise_correlation, avg_correlation) in `strategies/common/adaptive_control/correlation_tracker.py`
- [ ] T032 [US3] Implement `OnlineCorrelationMatrix.get_metrics()` returning CorrelationMetrics in `strategies/common/adaptive_control/correlation_tracker.py`
- [ ] T033 [US3] Add `correlation_metrics: Optional[CorrelationMetrics] = None` field to `PortfolioState` dataclass in `strategies/common/adaptive_control/particle_portfolio.py`
- [ ] T034 [US3] Modify `ParticlePortfolio.update()` to populate `correlation_metrics` in returned PortfolioState in `strategies/common/adaptive_control/particle_portfolio.py`
- [ ] T035 [US3] Run tests T028-T030 and verify they PASS in `tests/`

**Checkpoint**: User Story 3 complete - Lambda tuning with full observability

---

## Phase 6: Edge Cases (Priority: P3+)

**Goal**: Handle degenerate cases per spec Edge Cases section

**Independent Test**: Verify graceful handling of singular matrices, zero variance, all-correlated strategies

### Tests for Edge Cases

- [ ] T036 [P] Write test `test_singular_matrix_regularization` (FR-005: regularization prevents crash) in `tests/unit/test_correlation_tracker.py`
- [ ] T037 [P] Write test `test_zero_variance_strategy` (FR-005: treated as uncorrelated) in `tests/unit/test_correlation_tracker.py`
- [ ] T038 [P] Write test `test_all_strategies_correlated` (allocate to highest Sharpe) in `tests/integration/test_csrc_walk_forward.py`
- [ ] T039 [P] Write test `test_two_strategy_portfolio` (N=2 works correctly) in `tests/unit/test_correlation_tracker.py`
- [ ] T055 [P] Write test `test_sliding_window_memory_constraint` (FR-004: max 1000 samples in memory) in `tests/unit/test_correlation_tracker.py`

### Implementation for Edge Cases

- [ ] T040 Add epsilon regularization (1e-6) to diagonal in `_apply_shrinkage()` in `strategies/common/adaptive_control/correlation_tracker.py`
- [ ] T041 Handle zero variance detection in `OnlineCorrelationMatrix.update()` - set correlation to 0 in `strategies/common/adaptive_control/correlation_tracker.py`
- [ ] T042 Run tests T036-T039, T055 and verify they PASS in `tests/`

**Checkpoint**: Edge cases handled - robust to degenerate inputs

---

## Phase 7: Integration & Polish

**Purpose**: Integration with existing systems, documentation, final verification

### Integration Tasks

- [ ] T043 [P] Integrate with `BayesianEnsemble` class - pass correlation_tracker through in `strategies/common/adaptive_control/particle_portfolio.py`
- [ ] T044 [P] Integrate with audit trail (Spec 030) - emit correlation metrics via audit_emitter in `strategies/common/adaptive_control/particle_portfolio.py`
- [ ] T045 [P] Update `strategies/common/adaptive_control/__init__.py` to export new classes (OnlineCorrelationMatrix, CorrelationMetrics, calculate_covariance_penalty)
- [ ] T046 [P] Write integration test `test_bayesian_ensemble_with_csrc` in `tests/integration/test_csrc_walk_forward.py`

### Documentation

- [ ] T047 [P] Create `docs/adaptive_control/csrc_correlation.md` with usage examples
- [ ] T048 [P] Update docstrings in `correlation_tracker.py` with usage examples
- [ ] T053 [P] Add lambda sensitivity section to documentation (examples: lambda=0.5 mild, 1.0 balanced, 2.0 strong, 5.0 aggressive)
- [ ] T054 Update `particle_portfolio.py` docstring to remove P5 "Leggi Naturali" reference (removed per CLAUDE.md 2026-01-05)

### Final Verification

- [ ] T049 Run full test suite: `uv run pytest tests/unit/test_correlation_tracker.py tests/integration/test_csrc_walk_forward.py -v`
- [ ] T050 Run alpha-debug verification on correlation_tracker.py and particle_portfolio.py modifications
- [ ] T051 Verify SC-001: 20% concentration reduction (run benchmark)
- [ ] T052 Verify SC-002: < 1ms for 10 strategies (run benchmark)

**Checkpoint**: Feature complete - CSRC ready for production use

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Core penalty feature
- **User Story 2 (Phase 4)**: Depends on Foundational - Can run parallel to US1
- **User Story 3 (Phase 5)**: Depends on US1 (needs penalty to test lambda sensitivity)
- **Edge Cases (Phase 6)**: Depends on Foundational - Can run parallel to user stories
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

```
Setup (T001-T003)
    │
    ▼
Foundational (T004-T011)
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
US1 (T012-T020)    US2 (T021-T027)   Edge Cases (T036-T042, T055)
    │                  │                  │
    ▼                  │                  │
US3 (T028-T035)◄───────┘                  │
    │                                     │
    ▼                                     ▼
Polish (T043-T054)◄───────────────────────┘
```

### Parallel Opportunities

**Phase 1** (all parallel):
- T001, T002, T003 can run in parallel (different files)

**Phase 2** (sequential for same file):
- T004-T009 are sequential (same file: correlation_tracker.py)
- T010-T011 are sequential (same file: test_correlation_tracker.py)

**Phase 3-5** (tests parallel, impl sequential):
- Tests T012-T014 can run in parallel (different test files)
- Implementations T015-T019 are sequential (modifying same files)

**Phase 7** (integration parallel):
- T043, T044, T045 can run in parallel (different files)

---

## Parallel Example: Phase 1 Setup

```bash
# Launch all setup tasks together:
Task: "Create correlation_tracker.py"
Task: "Create test_correlation_tracker.py"
Task: "Create test_csrc_walk_forward.py"
```

## Parallel Example: User Story Tests

```bash
# Launch all US1 tests together:
Task: "Write test_penalty_calculation"
Task: "Write test_concentration_reduction"
Task: "Write test_no_regression"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test concentration reduction independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. User Story 1 → Test: concentration reduces 20% → MVP!
3. User Story 2 → Test: < 1ms performance → Optimized
4. User Story 3 → Test: lambda tuning works → Configurable
5. Edge Cases → Test: robust to degenerate inputs → Production-ready

### Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**

This delivers:
- Correlation tracking infrastructure
- Covariance penalty in ParticlePortfolio
- 20% concentration reduction for correlated strategies

---

## Notes

- [P] tasks = different files, no dependencies
- [E] tasks = complex algorithms triggering alpha-evolve
- [Story] label maps task to specific user story
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 55 |
| Setup Tasks | 3 |
| Foundational Tasks | 8 |
| US1 Tasks | 9 |
| US2 Tasks | 7 |
| US3 Tasks | 8 |
| Edge Case Tasks | 8 (added T055 for FR-004 memory test) |
| Polish Tasks | 12 (added T053, T054 for docs + P5 cleanup) |
| Parallel Opportunities | 21 tasks marked [P] |
| MVP Scope | T001-T020 (20 tasks) |
