# Tasks: Kelly Criterion Portfolio Integration

**Feature**: spec-034-kelly-criterion
**Generated**: 2026-01-12
**Estimated Effort**: 4 hours
**Status**: Ready for Implementation

---

## User Stories Summary

| Story | Priority | Description | Tasks |
|-------|----------|-------------|-------|
| US1 | P1 | Fractional Kelly Scaling | T005-T008 |
| US2 | P1 | Pipeline Integration | T009-T013 |
| US3 | P2 | Uncertainty Handling | T014-T016 |

---

## Phase 1: Setup

- [ ] T001 Create kelly_allocator.py module file in strategies/common/adaptive_control/kelly_allocator.py
- [ ] T002 Create test_kelly_allocator.py test file in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T003 [P] Add KellyConfig dataclass with all fields (enabled, beta, min_samples, max_fraction, decay, uncertainty_adjustment, min_allocation) in strategies/common/adaptive_control/kelly_allocator.py
- [ ] T004 [P] Add imports and logger setup in strategies/common/adaptive_control/kelly_allocator.py

---

## Phase 2: Foundational (Blocking)

*No foundational tasks required - US1 and US2 can start in parallel after setup.*

---

## Phase 3: User Story 1 - Fractional Kelly Scaling (P1)

**Goal**: Calculate Kelly-optimal fractions for strategy allocation with fractional scaling.

**Independent Test**: Provide known μ/σ² for 5 strategies, verify f* = μ/σ², fractional scaling f_actual = β × f*, and normalization when sum > 100%.

**Acceptance Criteria**:
- AC1: f* = μ/σ² calculated correctly
- AC2: Fractional Kelly (β=0.25) applied
- AC3: Normalization when allocations > 100%
- AC4: Configurable β changes allocations proportionally

### Implementation Tasks

- [ ] T005 [US1] Implement KellyAllocator.__init__ with config and returns tracking dict in strategies/common/adaptive_control/kelly_allocator.py
- [ ] T006 [US1] Implement KellyAllocator.update_return(strategy_id, daily_return) method with deque storage in strategies/common/adaptive_control/kelly_allocator.py
- [ ] T007 [US1] Implement KellyAllocator.calculate_fraction(strategy_id) with μ/σ² calculation, fractional beta, and audit dict in strategies/common/adaptive_control/kelly_allocator.py
- [ ] T008 [US1] Implement KellyAllocator.allocate(strategy_ids) with normalization when sum > 1.0 in strategies/common/adaptive_control/kelly_allocator.py

### Tests (US1)

- [ ] T017 [P] [US1] Write test_kelly_fraction_calculation for f* = μ/σ² with known values in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T018 [P] [US1] Write test_fractional_kelly_scaling for f_actual = β × f* in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T019 [P] [US1] Write test_normalization_over_100pct for sum > 100% normalization in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T020 [P] [US1] Write test_configurable_beta for different β values in tests/strategies/common/adaptive_control/test_kelly_allocator.py

---

## Phase 4: User Story 2 - Pipeline Integration (P1)

**Goal**: Integrate Kelly scaling into MetaPortfolio as optional layer, backward compatible when disabled.

**Independent Test**: Run MetaPortfolio with Kelly disabled - verify identical to baseline. Enable Kelly - verify allocations change.

**Acceptance Criteria**:
- AC1: Kelly disabled (default) produces identical results to pre-integration
- AC2: Kelly enabled applies scaling after Thompson/Ensemble
- AC3: Insufficient data (<30 days) falls back to non-Kelly with warning

### Implementation Tasks

- [ ] T009 [US2] Add kelly_config parameter to MetaPortfolio.__init__ with default KellyConfig(enabled=False) in strategies/common/adaptive_control/meta_portfolio.py
- [ ] T010 [US2] Add KellyAllocator instantiation in MetaPortfolio.__init__ when kelly_config.enabled is True in strategies/common/adaptive_control/meta_portfolio.py
- [ ] T011 [US2] Modify MetaPortfolio.update_pnl to track returns via kelly_allocator.update_return in strategies/common/adaptive_control/meta_portfolio.py
- [ ] T012 [US2] Modify MetaPortfolio.aggregate to apply Kelly scaling after Thompson/Ensemble in strategies/common/adaptive_control/meta_portfolio.py
- [ ] T013 [US2] Export KellyConfig, KellyAllocator, EstimationUncertainty from strategies/common/adaptive_control/__init__.py

### Tests (US2)

- [ ] T021 [P] [US2] Write test_kelly_integration_disabled for backward compatibility in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T022 [P] [US2] Write test_kelly_integration_enabled for Kelly modifying allocations in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T023 [P] [US2] Write test_insufficient_data_fallback for <min_samples warning in tests/strategies/common/adaptive_control/test_kelly_allocator.py

---

## Phase 5: User Story 3 - Estimation Uncertainty (P2)

**Goal**: Adjust Kelly fractions based on sample size confidence - fewer samples = more conservative.

**Independent Test**: Provide strategies with 30, 90, 180 days of returns. Verify Kelly fractions decrease with fewer samples.

**Acceptance Criteria**:
- AC1: 180 days = full fractional Kelly (confidence 1.0)
- AC2: 30 days = reduced Kelly (confidence ~0.5)
- AC3: <20 days = conservative default (skip Kelly)

### Implementation Tasks

- [ ] T014 [US3] Implement EstimationUncertainty class with min_samples, max_samples, min_confidence in strategies/common/adaptive_control/kelly_allocator.py
- [ ] T015 [US3] Implement EstimationUncertainty.confidence_factor(sample_size) with linear interpolation in strategies/common/adaptive_control/kelly_allocator.py
- [ ] T016 [US3] Integrate EstimationUncertainty into KellyAllocator.calculate_fraction with uncertainty_adjustment flag in strategies/common/adaptive_control/kelly_allocator.py

### Tests (US3)

- [ ] T024 [P] [US3] Write test_uncertainty_high_samples for 180 days confidence=1.0 in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T025 [P] [US3] Write test_uncertainty_low_samples for 30 days reduced confidence in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T026 [P] [US3] Write test_uncertainty_insufficient for <20 days skip Kelly in tests/strategies/common/adaptive_control/test_kelly_allocator.py

---

## Phase 6: Edge Cases & Polish

- [ ] T027 [P] Write test_negative_mu_returns_zero for μ < 0 → f = 0 in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T028 [P] Write test_near_zero_variance_cap for σ² ≈ 0 → f capped at max_fraction in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T029 [P] Write test_exponential_decay_weighting for recent returns weighted more in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T033 [P] Write test_all_strategies_negative_mu for all strategies μ < 0 → min_allocation (1%) with warning in tests/strategies/common/adaptive_control/test_kelly_allocator.py
- [ ] T030 Add Kelly return history to MetaPortfolio.save_state() and load_state() in strategies/common/adaptive_control/meta_portfolio.py
- [ ] T031 Add docstrings and type hints to all public methods in strategies/common/adaptive_control/kelly_allocator.py
- [ ] T032 Run full test suite and verify all tests pass with `uv run pytest tests/strategies/common/adaptive_control/test_kelly_allocator.py -v`

---

## Dependencies

```
T001 ─┬─▶ T003 ─┬─▶ T005 ─▶ T006 ─▶ T007 ─▶ T008 (US1 complete)
      │         │
      └─▶ T004  └─▶ T014 ─▶ T015 ─▶ T016 (US3 complete)
                        │
T002 ─▶ T017-T020 (US1 tests - parallel)
      ─▶ T021-T023 (US2 tests - parallel)
      ─▶ T024-T026 (US3 tests - parallel)
      ─▶ T027-T029 (Edge case tests - parallel)

T008 ─┬─▶ T009 ─▶ T010 ─▶ T011 ─▶ T012 ─▶ T013 (US2 complete)
      │
T016 ─┘

T013 ─▶ T030 ─▶ T031 ─▶ T032 (Polish complete)
```

### Story Completion Order

1. **Setup** (T001-T004) - Required first
2. **US1** (T005-T008) and **US3** (T014-T016) - Can run in parallel
3. **US2** (T009-T013) - Requires US1 and US3 complete
4. **Tests** (T017-T029) - Can run in parallel after implementation
5. **Polish** (T030-T032) - Final phase

---

## Parallel Execution Examples

### Maximum Parallelism (4 workers)

```
Worker 1: T001 → T003 → T005 → T006 → T007 → T008 → T009 → T010
Worker 2: T002 → T004 → T014 → T015 → T016 → T011 → T012 → T013
Worker 3: (wait for T002) → T017 → T018 → T019 → T020 → T027
Worker 4: (wait for T002) → T021 → T022 → T023 → T024 → T025 → T026 → T028 → T029
All: T030 → T031 → T032
```

### Sequential (1 worker)

```
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T014 → T015 → T016 →
T009 → T010 → T011 → T012 → T013 → T017-T029 (tests) → T030 → T031 → T032
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**US1 only** (T001-T008 + T017-T020):
- KellyAllocator with basic f* calculation
- Fractional scaling
- Normalization
- Unit tests

**Delivers**: Core Kelly functionality, can be used standalone for portfolio allocation.

### Full Implementation

All tasks (T001-T032):
- Complete integration with MetaPortfolio
- Uncertainty handling
- State persistence
- Full test coverage

---

## Success Criteria Verification

| Criteria | Task(s) | Verification |
|----------|---------|--------------|
| SC-001: 5-15% growth improvement | - | Backtest (manual) |
| SC-002: DD ≤ 1.5x baseline | - | Backtest (manual) |
| SC-003: <1ms for 20 strategies | T032 | Performance test |
| SC-004: Fallback when insufficient | T023 | Unit test |
| SC-005: Identical when disabled | T021 | Unit test |
| SC-006: 30-50% reduction <60 days | T025 | Unit test |

---

## Notes

- All tests marked [P] can run in parallel
- US1 and US3 are independent (can develop in parallel)
- US2 depends on both US1 and US3
- Total: 33 tasks (4 setup, 4 US1, 5 US2, 3 US3, 14 tests, 3 polish)
