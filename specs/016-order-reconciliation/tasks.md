# Tasks: Order Reconciliation System

**Input**: Design documents from `/specs/016-order-reconciliation/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Integration tests included as requested in spec (Testing Strategy section).

**Organization**: Tasks grouped by functional requirement (FR) as user stories.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger (not used - leveraging native NautilusTrader)
- **[Story]**: FR-based user story (US1-US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project structure and dependency setup

- [X] T001 Create directory structure per plan.md in config/reconciliation/
- [X] T002 [P] Create config/reconciliation/__init__.py with exports
- [X] T003 [P] Create config/trading_node/__init__.py with exports
- [X] T004 [P] Create tests/unit/ directory for unit tests
- [X] T005 [P] Create tests/integration/ directory for integration tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configuration models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement ReconciliationConfig Pydantic model with ALL fields (startup, inflight, open_check, purge) in config/reconciliation/config.py
- [X] T007 Add field validation (startup_delay >= 10.0, open_check_lookback >= 60, inflight threshold >= interval) in config/reconciliation/config.py
- [X] T008 Implement to_live_exec_engine_config() method in config/reconciliation/config.py
- [X] T009 [P] Implement ReconciliationPreset enum in config/reconciliation/presets.py
- [X] T010 [P] Create preset configurations (CONSERVATIVE, STANDARD, AGGRESSIVE, DISABLED) in config/reconciliation/presets.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Startup Reconciliation (FR-001) (Priority: P1) 🎯 MVP

**Goal**: Query exchange state and align internal state on TradingNode startup

**Independent Test**: Start TradingNode with open positions, verify reconciliation completes within 30s

### Tests for User Story 1

- [X] T011 [P] [US1] Unit test ReconciliationConfig defaults in tests/unit/test_reconciliation_config.py
- [X] T012 [P] [US1] Unit test ReconciliationConfig validation in tests/unit/test_reconciliation_config.py
- [X] T013 [P] [US1] Unit test to_live_exec_engine_config() conversion in tests/unit/test_reconciliation_config.py

### Implementation for User Story 1

- [X] T014 [US1] Create LiveTradingNodeConfig builder in config/trading_node/live_config.py
- [X] T015 [US1] Implement build_exec_engine_config() using ReconciliationConfig in config/trading_node/live_config.py
- [X] T016 [US1] Implement build_cache_config() with Redis in config/trading_node/live_config.py
- [X] T017 [US1] Add logging for reconciliation parameters in config/trading_node/live_config.py

**Checkpoint**: Startup reconciliation configurable and testable

---

## Phase 4: User Story 2 - Reconciliation Delay (FR-002) (Priority: P1)

**Goal**: Wait for all accounts to connect before starting reconciliation

**Independent Test**: Configure 10s delay, verify reconciliation waits before querying exchange

### Tests for User Story 2

- [X] T018 [US2] Unit test startup_delay_secs constraint (>= 10.0) in tests/unit/test_reconciliation_config.py

### Implementation for User Story 2

- [X] T019 [US2] Add graceful_shutdown_on_exception setting in config/trading_node/live_config.py

**Checkpoint**: Reconciliation delay configurable

**Note**: startup_delay_secs validation already implemented in T007 (Foundational)

---

## Phase 5: User Story 3 - Continuous Reconciliation (FR-003) (Priority: P2)

**Goal**: Periodic checks during operation to detect discrepancies

**Independent Test**: Run TradingNode, verify periodic check runs every 5 seconds

### Tests for User Story 3

- [X] T020 [US3] Unit test open_check_* fields validation in tests/unit/test_reconciliation_config.py
- [X] T021 [US3] Unit test STANDARD preset values in tests/unit/test_reconciliation_config.py

### Implementation for User Story 3

- [X] T022 [US3] Verify open_check fields included in to_live_exec_engine_config() in config/reconciliation/config.py
- [X] T023 [US3] Verify memory purge settings included in to_live_exec_engine_config() in config/reconciliation/config.py

**Checkpoint**: Continuous reconciliation configurable

**Note**: open_check and purge fields already defined in T006 (Foundational)

---

## Phase 6: User Story 4 - In-Flight Order Monitoring (FR-004) (Priority: P2)

**Goal**: Monitor orders awaiting confirmation, resolve timeouts

**Independent Test**: Submit order, verify in-flight check runs at configured interval

### Tests for User Story 4

- [X] T024 [US4] Unit test inflight_check_* fields validation in tests/unit/test_reconciliation_config.py
- [X] T025 [US4] Unit test inflight threshold >= interval constraint in tests/unit/test_reconciliation_config.py

### Implementation for User Story 4

- [X] T026 [US4] Verify inflight_check fields included in to_live_exec_engine_config() in config/reconciliation/config.py

**Checkpoint**: In-flight monitoring configurable

**Note**: inflight_check fields and validation already defined in T006-T007 (Foundational)

---

## Phase 7: User Story 5 - External Order Claims (FR-005) (Priority: P3)

**Goal**: Claim positions opened outside NautilusTrader (web/app)

**Independent Test**: Place order via exchange web, verify NautilusTrader claims it

### Tests for User Story 5

- [X] T027 [P] [US5] Unit test ExternalOrderClaimConfig in tests/unit/test_external_claims.py
- [X] T028 [P] [US5] Unit test claim_all/instrument_ids mutual exclusion in tests/unit/test_external_claims.py

### Implementation for User Story 5

- [X] T029 [US5] Implement ExternalOrderClaimConfig Pydantic model in config/reconciliation/external_claims.py
- [X] T030 [US5] Add instrument_ids validation (pattern match) in config/reconciliation/external_claims.py
- [X] T031 [US5] Add claim_all/instrument_ids mutual exclusion validator in config/reconciliation/external_claims.py
- [X] T032 [US5] Create example strategy config with external claims in config/strategies/example_with_claims.py

**Checkpoint**: External order claims configurable

---

## Phase 8: Integration Testing

**Purpose**: End-to-end tests with TradingNode (NFR coverage)

- [ ] T033 [P] Create integration test fixtures with mock venue in tests/integration/conftest.py
- [ ] T034 Integration test TradingNode startup reconciliation in tests/integration/test_reconciliation.py
- [ ] T035 Integration test continuous polling in tests/integration/test_reconciliation.py
- [ ] T036 Integration test external order detection in tests/integration/test_reconciliation.py
- [ ] T037 [NFR-001] Test 100% fill completeness (count comparison) in tests/integration/test_reconciliation.py
- [ ] T038 [NFR-001] Test no duplicate fill events in tests/integration/test_reconciliation.py
- [ ] T039 [NFR-002] Performance test: startup < 30s in tests/integration/test_reconciliation.py
- [ ] T040 [NFR-002] Performance test: periodic check < 5s in tests/integration/test_reconciliation.py
- [ ] T041 [NFR-002] Performance test: memory usage during purge cycles in tests/integration/test_reconciliation.py
- [ ] T042 Integration test: disconnection simulation and recovery in tests/integration/test_reconciliation.py

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, monitoring, final validation

- [ ] T043 [P] Create user documentation in docs/guides/reconciliation.md
- [ ] T044 [P] Add Grafana dashboard panel for reconciliation status in monitoring/grafana/dashboards/reconciliation.json
- [ ] T045 [P] Add alert rules for position discrepancies in monitoring/grafana/alerts/reconciliation.yaml
- [ ] T046 Update quickstart.md with final examples in specs/016-order-reconciliation/quickstart.md
- [ ] T047 Run alpha-debug verification on config/reconciliation/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational completion
  - US1 + US2 can run in parallel (both are P1)
  - US3 + US4 can run in parallel (both are P2)
  - US5 can start after Foundational
- **Integration (Phase 8)**: Depends on US1-US5 completion
- **Polish (Phase 9)**: Depends on Integration

### User Story Dependencies

- **US1 (FR-001)**: Can start after Foundational - Core startup configuration
- **US2 (FR-002)**: Can start after Foundational - Enhances US1 with delay
- **US3 (FR-003)**: Can start after Foundational - Independent continuous polling
- **US4 (FR-004)**: Can start after Foundational - Independent in-flight monitoring
- **US5 (FR-005)**: Can start after Foundational - Independent external claims

### Within Each User Story

- Tests written first, must FAIL before implementation
- Config fields consolidated in Foundational (T006)
- Validation consolidated in Foundational (T007)
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002, T003, T004, T005 can all run in parallel

**Phase 2 (Foundational)**:
- T009, T010 can run in parallel after T006-T008

**User Stories (After Foundational)**:
- US1 + US2 can run in parallel (different aspects of startup)
- US3 + US4 can run in parallel (different monitoring features)
- US5 independent of all others

**Phase 8 (Integration)**:
- T033 (fixtures) first, then T034-T042 sequentially

**Phase 9 (Polish)**:
- T043, T044, T045 can all run in parallel

---

## Parallel Example: Foundational Phase

```bash
# After T006-T008 complete, run presets in parallel:
Task: "Implement ReconciliationPreset enum in config/reconciliation/presets.py"
Task: "Create preset configurations in config/reconciliation/presets.py"
```

## Parallel Example: P2 User Stories

```bash
# After Foundational, US3 and US4 can run in parallel:
# Developer A: US3 (Continuous Reconciliation)
Task: "Add open_check fields in config/reconciliation/config.py"
Task: "Add memory purge settings in config/reconciliation/config.py"

# Developer B: US4 (In-Flight Monitoring)
Task: "Add inflight_check fields in config/reconciliation/config.py"
Task: "Add inflight validation in config/reconciliation/config.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 (Startup Reconciliation)
4. Complete Phase 4: US2 (Reconciliation Delay)
5. **STOP and VALIDATE**: TradingNode starts with reconciliation
6. Deploy if ready

### Incremental Delivery

1. Setup + Foundational → Configuration framework ready
2. Add US1 + US2 → Startup reconciliation working (MVP!)
3. Add US3 → Continuous polling enabled
4. Add US4 → In-flight monitoring enabled
5. Add US5 → External orders claimable
6. Integration tests → Full validation
7. Polish → Documentation and monitoring

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational done:
   - Developer A: US1 + US2 (startup features)
   - Developer B: US3 + US4 (monitoring features)
   - Developer C: US5 (external claims)
3. Stories integrate independently

---

## Notes

- **Total tasks**: 47 (T001-T047)
- [P] tasks = different files, no dependencies
- NO [E] tasks - using native NautilusTrader reconciliation (KISS)
- [Story] label maps to Functional Requirements (FR-001 to FR-005)
- [NFR-001] / [NFR-002] labels mark non-functional requirement coverage
- Each US independently testable after Foundational complete
- Spec explicitly requests tests (Testing Strategy section)
- All configs are Pydantic models per data-model.md
- Redis cache REQUIRED per plan.md decisions
- Foundational phase (T006-T007) consolidates ALL config fields and validation to avoid duplication
