# Tasks: Adaptive Discounted Thompson Sampling (ADTS)

**Input**: Design documents from `/specs/032-adts-discounting/`
**Prerequisites**: plan.md, spec.md, research.md
**Branch**: `032-adts-discounting`

**Tests**: Included as per TDD requirements in plan.md

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - complex algorithmic tasks
- **[Story]**: Which user story (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new module structure for adaptive decay

- [X] T001 Create adaptive_decay.py module file in strategies/common/adaptive_control/adaptive_decay.py
- [X] T002 Update __init__.py exports in strategies/common/adaptive_control/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure needed before user stories

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create VolatilityContext dataclass in strategies/common/adaptive_control/adaptive_decay.py
- [X] T004 Create AdaptiveDecayCalculator class skeleton in strategies/common/adaptive_control/adaptive_decay.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Adaptive Forgetting in Volatile Regimes (Priority: P1)

**Goal**: Core decay calculation that adapts to market volatility (FR-001, FR-002, FR-005)

**Independent Test**: Verify decay = 0.99 for low volatility (variance_ratio < 0.7), decay = 0.95 for high volatility (variance_ratio > 1.5), interpolated for normal

### Tests for User Story 1

- [ ] T005 [P] [US1] Write test_low_volatility_high_decay in tests/test_adaptive_decay.py
- [ ] T006 [P] [US1] Write test_high_volatility_low_decay in tests/test_adaptive_decay.py
- [ ] T007 [P] [US1] Write test_normal_volatility_interpolated in tests/test_adaptive_decay.py
- [ ] T008 [P] [US1] Write test_extreme_high_clamped in tests/test_adaptive_decay.py
- [ ] T009 [P] [US1] Write test_zero_variance_ratio in tests/test_adaptive_decay.py
- [ ] T009b [P] [US1] Write test_negative_variance_ratio in tests/test_adaptive_decay.py

### Implementation for User Story 1

- [ ] T010 [US1] Implement normalized_volatility property in VolatilityContext in strategies/common/adaptive_control/adaptive_decay.py
- [ ] T011 [US1] Implement calculate() method in AdaptiveDecayCalculator in strategies/common/adaptive_control/adaptive_decay.py
- [ ] T012 [US1] Implement calculate_from_ratio() convenience method in strategies/common/adaptive_control/adaptive_decay.py
- [ ] T013 [US1] Run tests via test-runner agent: verify T005-T009b pass, coverage >= 80% for adaptive_decay.py

**Checkpoint**: AdaptiveDecayCalculator fully functional - can calculate adaptive decay from variance_ratio

---

## Phase 4: User Story 2 - Seamless Integration with Regime Detection (Priority: P2)

**Goal**: ThompsonSelector automatically uses adaptive decay with IIRRegimeDetector (FR-003, FR-004, FR-006)

**Independent Test**: Instantiate ThompsonSelector with IIRRegimeDetector, verify decay adjusts automatically; without detector, verify fixed decay fallback

### Tests for User Story 2

- [ ] T014 [P] [US2] Write test_backward_compatibility_no_detector in tests/test_thompson_selector_adaptive.py
- [ ] T015 [P] [US2] Write test_adaptive_with_detector in tests/test_thompson_selector_adaptive.py
- [ ] T016 [P] [US2] Write test_update_uses_adaptive_decay in tests/test_thompson_selector_adaptive.py
- [ ] T017 [P] [US2] Write test_update_continuous_uses_adaptive_decay in tests/test_thompson_selector_adaptive.py

### Implementation for User Story 2

- [ ] T018 [US2] Modify ThompsonSelector.__init__() to accept regime_detector parameter in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T019 [US2] Add _fixed_decay and _regime_detector instance variables in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T020 [US2] Add _decay_calculator initialization logic in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T021 [US2] Implement _get_decay() internal method in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T022 [US2] Modify update() to call _get_decay() instead of self.decay in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T023 [US2] Modify update_continuous() to call _get_decay() instead of self.decay in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T024 [US2] Add current_decay property to ThompsonSelector in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T025 [US2] Run tests and verify all US2 tests pass plus US1 regression

**Checkpoint**: ThompsonSelector integrates with IIRRegimeDetector - adaptive decay works end-to-end

---

## Phase 5: User Story 3 - Observable Decay Behavior (Priority: P3)

**Goal**: Decay changes logged to audit trail for observability (FR-007)

**Independent Test**: Enable audit emitter, trigger decay calculation, verify DecayEvent emitted with correct payload

### Tests for User Story 3

- [ ] T026 [P] [US3] Write test_decay_event_emitted in tests/test_thompson_selector_adaptive.py
- [ ] T027 [P] [US3] Write test_no_emission_without_emitter in tests/test_thompson_selector_adaptive.py
- [ ] T028 [P] [US3] Write test_decay_event_payload_correct in tests/test_thompson_selector_adaptive.py

### Implementation for User Story 3

- [ ] T029 [US3] Add SYS_DECAY_UPDATE to AuditEventType enum in strategies/common/audit/events.py
- [ ] T030 [US3] Add DecayEvent dataclass in strategies/common/audit/events.py
- [ ] T031 [US3] Modify ThompsonSelector.__init__() to accept audit_emitter parameter in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T032 [US3] Implement _emit_decay_event() method in ThompsonSelector in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T033 [US3] Add audit emission call in _get_decay() when emitter configured in strategies/common/adaptive_control/particle_portfolio.py
- [ ] T034 [US3] Run tests and verify all US3 tests pass plus US1/US2 regression

**Checkpoint**: Full observability - decay changes visible in audit trail

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T035 Run existing ThompsonSelector tests for regression (SC-003) via test-runner agent
- [ ] T036 Run existing ParticlePortfolio tests for regression via test-runner agent
- [ ] T037 Run existing BayesianEnsemble tests for regression via test-runner agent
- [ ] T038 [P] Update strategies/common/adaptive_control/__init__.py to export new classes
- [ ] T039 [P] Add docstrings to all new public methods
- [ ] T040 Run alpha-debug verification on adaptive_decay.py
- [ ] T041 Run alpha-debug verification on particle_portfolio.py modifications
- [ ] T042 Verify SC-001: Measure adaptation speed (30% faster in volatile regimes)
- [ ] T043 Verify SC-002: Full [0.95, 0.99] range coverage in 3 transitions
- [ ] T044 [P] Verify O(1) decay calculation overhead (< 1ms per call)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2
- **User Story 2 (Phase 4)**: Depends on Phase 2 (and integrates US1 output)
- **User Story 3 (Phase 5)**: Depends on Phase 4 (needs ThompsonSelector changes from US2)
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Standalone - AdaptiveDecayCalculator can be tested in isolation
- **User Story 2 (P2)**: Uses US1 output (AdaptiveDecayCalculator) but independently testable
- **User Story 3 (P3)**: Extends US2 (adds audit to ThompsonSelector) - needs US2 changes first

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Implementation follows test order
- All tests pass before checkpoint

### Parallel Opportunities

**Phase 3 (US1) Tests** - All can run in parallel:
```bash
Task: "Write test_low_volatility_high_decay in tests/test_adaptive_decay.py"
Task: "Write test_high_volatility_low_decay in tests/test_adaptive_decay.py"
Task: "Write test_normal_volatility_interpolated in tests/test_adaptive_decay.py"
Task: "Write test_extreme_high_clamped in tests/test_adaptive_decay.py"
Task: "Write test_zero_variance_ratio in tests/test_adaptive_decay.py"
```

**Phase 4 (US2) Tests** - All can run in parallel:
```bash
Task: "Write test_backward_compatibility_no_detector in tests/test_thompson_selector_adaptive.py"
Task: "Write test_adaptive_with_detector in tests/test_thompson_selector_adaptive.py"
Task: "Write test_update_uses_adaptive_decay in tests/test_thompson_selector_adaptive.py"
Task: "Write test_update_continuous_uses_adaptive_decay in tests/test_thompson_selector_adaptive.py"
```

**Phase 5 (US3) Tests** - All can run in parallel:
```bash
Task: "Write test_decay_event_emitted in tests/test_thompson_selector_adaptive.py"
Task: "Write test_no_emission_without_emitter in tests/test_thompson_selector_adaptive.py"
Task: "Write test_decay_event_payload_correct in tests/test_thompson_selector_adaptive.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (AdaptiveDecayCalculator)
4. **STOP and VALIDATE**: Test decay calculation in isolation
5. Can already use AdaptiveDecayCalculator standalone

### Incremental Delivery

1. **Setup + Foundational** → Module structure ready
2. **Add User Story 1** → AdaptiveDecayCalculator works → Test independently
3. **Add User Story 2** → ThompsonSelector integrates → Test end-to-end
4. **Add User Story 3** → Audit trail added → Full observability
5. Each story adds value without breaking previous stories

### File Summary

| File | Action | User Stories |
|------|--------|--------------|
| `strategies/common/adaptive_control/adaptive_decay.py` | NEW | US1 |
| `strategies/common/adaptive_control/particle_portfolio.py` | MODIFY | US2, US3 |
| `strategies/common/adaptive_control/__init__.py` | MODIFY | Setup |
| `strategies/common/audit/events.py` | MODIFY | US3 |
| `tests/test_adaptive_decay.py` | NEW | US1 |
| `tests/test_thompson_selector_adaptive.py` | NEW | US2, US3 |

---

## Notes

- [P] tasks = different files, can run in parallel
- All tests follow TDD: RED (fail) → GREEN (pass) → REFACTOR
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- SC-003 requires zero regressions on existing tests
- SC-005 requires zero new hyperparameters (formula is fixed)
