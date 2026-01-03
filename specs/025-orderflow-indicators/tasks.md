# Tasks: Orderflow Indicators (Spec 025)

**Input**: Design documents from `/specs/025-orderflow-indicators/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Setup (Project Structure)

**Purpose**: Create orderflow module structure and install dependencies

- [x] T001 Create orderflow module directory at strategies/common/orderflow/
- [x] T002 Install tick library for Hawkes processes: `uv pip install tick` (skipped - Python 3.12 incompatible, using pure Python fallback)
- [x] T003 [P] Create module __init__.py with public exports at strategies/common/orderflow/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Configuration Models

- [x] T004 Create VPINConfig Pydantic model in strategies/common/orderflow/config.py
- [x] T005 Create HawkesConfig Pydantic model in strategies/common/orderflow/config.py
- [x] T006 Create OrderflowConfig Pydantic model in strategies/common/orderflow/config.py

### Trade Classification (Shared by US1 and US2)

- [x] T007 Create TradeClassification dataclass in strategies/common/orderflow/trade_classifier.py
- [x] T008 Implement TickRuleClassifier in strategies/common/orderflow/trade_classifier.py
- [x] T009 [P] Implement BVCClassifier (Bulk Volume Classification) in strategies/common/orderflow/trade_classifier.py
- [x] T010 [P] Implement CloseVsOpenClassifier for bar data in strategies/common/orderflow/trade_classifier.py
- [x] T011 Create create_classifier() factory function in strategies/common/orderflow/trade_classifier.py

### Tests for Foundational Components

- [x] T012 Write unit tests for trade classifiers in tests/test_trade_classifier.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - VPIN Toxicity Indicator (Priority: P1) 🎯 MVP

**Goal**: Calculate Volume-Synchronized Probability of Informed Trading (VPIN) to detect toxic order flow

**Independent Test**: Verify VPIN returns 0.0-1.0 values, shows elevated values during simulated flash crash conditions

### Tests for User Story 1

- [x] T013 [US1] Write unit tests for VPINBucket dataclass in tests/test_vpin.py
- [x] T014 [US1] Write unit tests for VPINIndicator in tests/test_vpin.py
- [x] T015 [US1] Write edge case tests (zero volume, NaN, empty buckets) in tests/test_vpin.py

### Implementation for User Story 1

- [x] T016 [US1] Create ToxicityLevel enum in strategies/common/orderflow/vpin.py
- [x] T017 [US1] Create VPINBucket dataclass in strategies/common/orderflow/vpin.py
- [x] T018 [US1] Implement VPINIndicator class with volume bucketing logic in strategies/common/orderflow/vpin.py
- [x] T019 [US1] Implement handle_bar() method for streaming updates in strategies/common/orderflow/vpin.py
- [x] T020 [US1] Implement rolling VPIN calculation (value property) in strategies/common/orderflow/vpin.py
- [x] T021 [US1] Implement toxicity_level property in strategies/common/orderflow/vpin.py
- [x] T022 [US1] Add reset() method for indicator state in strategies/common/orderflow/vpin.py

**Checkpoint**: User Story 1 complete - VPIN indicator is fully functional and independently testable

**Acceptance Criteria**:
- VPIN returns value 0.0-1.0
- VPIN > 0.7 returns HIGH toxicity level
- VPIN calculation latency < 5ms per bucket
- Test coverage > 80%

---

## Phase 4: User Story 2 - Hawkes Process Order Flow Imbalance (Priority: P2)

**Goal**: Model order arrival as self-exciting Hawkes process to detect order flow clustering and momentum

**Independent Test**: Verify Hawkes OFI returns intensity values, shows elevated buy/sell intensity during order bursts

### Tests for User Story 2

- [x] T023 [US2] Write unit tests for HawkesState dataclass in tests/test_hawkes_ofi.py
- [x] T024 [US2] Write unit tests for HawkesOFI indicator in tests/test_hawkes_ofi.py
- [x] T025 [US2] Write edge case tests (convergence failure, sparse events) in tests/test_hawkes_ofi.py

### Implementation for User Story 2

- [x] T026 [P] [US2] Create HawkesState dataclass in strategies/common/orderflow/hawkes_ofi.py
- [x] T027 [E] [US2] Implement HawkesOFI class with tick library integration in strategies/common/orderflow/hawkes_ofi.py
- [x] T028 [US2] Implement rolling window event buffer in strategies/common/orderflow/hawkes_ofi.py
- [x] T029 [US2] Implement refit() method for periodic model update in strategies/common/orderflow/hawkes_ofi.py
- [x] T030 [US2] Implement intensity calculation (buy_intensity, sell_intensity properties) in strategies/common/orderflow/hawkes_ofi.py
- [x] T031 [US2] Implement ofi property (Order Flow Imbalance) in strategies/common/orderflow/hawkes_ofi.py
- [x] T032 [US2] Implement pure Python fallback if tick unavailable in strategies/common/orderflow/hawkes_ofi.py
- [x] T033 [US2] Add reset() method for indicator state in strategies/common/orderflow/hawkes_ofi.py

**Checkpoint**: User Story 2 complete - Hawkes OFI is fully functional and independently testable

**Acceptance Criteria**:
- Hawkes returns intensity values for buy/sell
- OFI returns normalized imbalance [-1.0, 1.0]
- Hawkes fitting converges in < 1 second on 10K ticks
- Test coverage > 80%

---

## Phase 5: Integration & OrderflowManager

**Purpose**: Unified manager and integration with existing components (GillerSizer, RegimeManager)

### Tests for Integration

- [x] T034 Write integration test for OrderflowManager in tests/test_orderflow_manager.py
- [x] T035 Write integration test with GillerSizer (toxicity parameter) in tests/test_orderflow_manager.py

### Implementation

- [x] T036 Implement OrderflowManager class in strategies/common/orderflow/orderflow_manager.py
- [x] T037 Implement handle_bar() to update both VPIN and Hawkes in strategies/common/orderflow/orderflow_manager.py
- [x] T038 Implement toxicity and ofi properties for unified access in strategies/common/orderflow/orderflow_manager.py
- [x] T039 Update __init__.py to export all public classes in strategies/common/orderflow/__init__.py

**Checkpoint**: Integration complete - OrderflowManager provides unified interface

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T040 [P] Use test-runner agent to verify all tests pass with coverage > 80%
- [x] T041 [P] Run alpha-debug verification on orderflow module
- [x] T042 Update quickstart.md with final API examples in specs/025-orderflow-indicators/quickstart.md
- [x] T043 Performance benchmark: Verify VPIN < 5ms, Hawkes < 1s (VPIN: 0.031ms, Hawkes: 1.31ms)
- [ ] T044 Validate VPIN-volatility correlation >0.7 on historical flash crash data (DEFERRED: requires historical data)
- [ ] T045 Validate OFI prediction accuracy >55% on test dataset (DEFERRED: requires historical data)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Can run in parallel with US2
- **User Story 2 (Phase 4)**: Depends on Foundational - Can run in parallel with US1
- **Integration (Phase 5)**: Depends on US1 AND US2 completion
- **Polish (Phase 6)**: Depends on Integration

### User Story Dependencies

- **User Story 1 (VPIN)**: Independent after Foundational
- **User Story 2 (Hawkes OFI)**: Independent after Foundational
- Both stories share TradeClassifier from Foundational phase

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Dataclasses/models before main indicator class
- Core implementation before properties/methods
- Edge cases handled after happy path works

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T004, T005, T006 can run in parallel (different config classes in same file - but sequential safer)
- T009, T010 can run in parallel (different classifiers)

**Phase 3 (User Story 1)**:
- T016, T017 can run in parallel (different classes in same file)

**Phase 4 (User Story 2)**:
- T026 can run while T027 is being designed (dataclass before main class)

**Cross-Story Parallelism**:
- After Phase 2, US1 (T013-T022) and US2 (T023-T033) can run in parallel if multiple developers

---

## Parallel Example: User Story 1

```bash
# Launch tests first (all in same file, must be sequential):
Task: "Write unit tests for VPINBucket in tests/test_vpin.py"
Task: "Write unit tests for VPINIndicator in tests/test_vpin.py"
Task: "Write edge case tests in tests/test_vpin.py"

# Then launch implementation models together:
Task: "Create ToxicityLevel enum in strategies/common/orderflow/vpin.py"
Task: "Create VPINBucket dataclass in strategies/common/orderflow/vpin.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T012)
3. Complete Phase 3: User Story 1 (T013-T022)
4. **STOP and VALIDATE**: Test VPIN independently
5. VPIN can be used with GillerSizer immediately (toxicity parameter)

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 (VPIN) → Test independently → Can deploy MVP!
3. Add User Story 2 (Hawkes) → Test independently → Enhanced orderflow
4. Add Integration → OrderflowManager unified interface
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (VPIN)
   - Developer B: User Story 2 (Hawkes OFI)
3. Stories complete and integrate at Phase 5

---

## Notes

- [P] tasks = different files, no dependencies
- [E] tasks = complex algorithms triggering alpha-evolve (T027 Hawkes fitting)
- [USn] label maps task to specific user story
- Each user story is independently testable
- Verify tests fail before implementing
- Commit after each task or logical group
- tick library is optional - pure Python fallback available
