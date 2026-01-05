# Tasks: Audit Trail System

**Input**: Design documents from `/specs/030-audit-trail/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete)

**Tests**: Tests ARE included as part of implementation for verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create audit trail module structure and base dependencies

- [ ] T001 Create audit module directory structure in `strategies/common/audit/`
- [ ] T002 Create `strategies/common/audit/__init__.py` with public exports
- [ ] T003 [P] Add duckdb dependency to project requirements (optional, for queries)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core audit infrastructure that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `AuditConfig` dataclass in `strategies/common/audit/config.py` with settings for: base_path, sync_writes, rotate_daily, retention_days
- [ ] T005 Create `AuditEventType` enum in `strategies/common/audit/events.py` with hierarchical event types (param.*, trade.*, sys.*)
- [ ] T006 Create `AuditEvent` base Pydantic model in `strategies/common/audit/events.py` with: ts_event (ns), event_type, source, trader_id, sequence, checksum property
- [ ] T007 Create `AppendOnlyWriter` class in `strategies/common/audit/writer.py` with O_APPEND flag, thread-safe writes, daily rotation
- [ ] T008 Create `AuditEventEmitter` class in `strategies/common/audit/emitter.py` with emit(), sequence tracking, writer integration
- [ ] T009 [P] Create unit test for `AppendOnlyWriter` O_APPEND behavior in `tests/unit/audit/test_writer.py`
- [ ] T010 [P] Create unit test for `AuditEvent` checksum computation in `tests/unit/audit/test_events.py`
- [ ] T010b [P] Create unit test for crash recovery (partial write handling) in `tests/unit/audit/test_writer.py`

**Checkpoint**: Foundation ready - can emit audit events to append-only JSON Lines files

---

## Phase 3: User Story 1 - Log Parameter Changes (Priority: P1)

**Goal**: Log every parameter change with timestamp, old value, new value, and trigger reason

**Independent Test**: Change a parameter and query the audit log to see old/new values

**Acceptance Criteria**:
- 100% of parameter changes logged (no silent changes)
- Append-only enforcement (historical entries immutable)
- Write latency < 1ms per event (p99)

### Implementation for User Story 1

- [ ] T011 [US1] Create `ParameterChangeEvent` Pydantic model in `strategies/common/audit/events.py` with: param_name, old_value, new_value, trigger_reason
- [ ] T012 [US1] Add `emit_param_change()` convenience method to `AuditEventEmitter` in `strategies/common/audit/emitter.py`
- [ ] T013 [US1] Create unit test for `ParameterChangeEvent` serialization in `tests/unit/audit/test_events.py`
- [ ] T014 [US1] Create unit test for `emit_param_change()` end-to-end in `tests/unit/audit/test_emitter.py`
- [ ] T015 [US1] Integrate audit emitter into `MetaController` for state transitions in `strategies/common/adaptive_control/meta_controller.py`
- [ ] T016 [US1] Integrate audit emitter into `SOPSGillerSizer` for k parameter changes in `strategies/common/adaptive_control/sops_sizing.py`
- [ ] T017 [US1] Create integration test verifying parameter logging from MetaController in `tests/integration/test_audit_integration.py`

**Checkpoint**: Parameter changes are logged immutably - MVP for security auditing

---

## Phase 4: User Story 2 - Log Trade Executions (Priority: P1)

**Goal**: Log every trade with execution details: size, price, slippage, P&L, strategy source

**Independent Test**: Execute a trade and query the audit log for all execution details

**Acceptance Criteria**:
- 100% of trade executions logged with full details
- Can reconstruct trade lifecycle (signal → order → fill → P&L)
- Sync writes for trade events (audit compliance)

### Implementation for User Story 2

- [ ] T018 [US2] Create `TradeEvent` Pydantic model in `strategies/common/audit/events.py` with: order_id, instrument_id, side, size, price, slippage_bps, realized_pnl, strategy_source
- [ ] T019 [US2] Add `emit_trade()` convenience method to `AuditEventEmitter` in `strategies/common/audit/emitter.py`
- [ ] T020 [US2] Create `AuditObserver` Actor in `strategies/common/audit/observer.py` that subscribes to NT MessageBus order events
- [ ] T021 [US2] Implement `_on_order_event()` handler in `AuditObserver` for OrderFilled, OrderRejected events
- [ ] T022 [US2] Implement `_on_position_event()` handler in `AuditObserver` for PositionOpened, PositionClosed events
- [ ] T023 [US2] Create unit test for `TradeEvent` serialization in `tests/unit/audit/test_events.py`
- [ ] T024 [US2] Create integration test for `AuditObserver` with mock NT events in `tests/integration/test_audit_observer.py`

**Checkpoint**: Trade executions are logged with full lifecycle - audit compliance ready

---

## Phase 5: User Story 3 - Log Signal Generation (Priority: P2)

**Goal**: Log every signal with value, regime, confidence, and source strategy

**Independent Test**: Generate a signal and query the audit log to see signal details

**Acceptance Criteria**:
- 100% of signals above threshold logged
- Can compute signal-to-trade conversion rate
- Can see why trades were NOT executed (signal filtered)

### Implementation for User Story 3

- [ ] T025 [US3] Create `SignalEvent` Pydantic model in `strategies/common/audit/events.py` with: signal_value, regime, confidence, strategy_source
- [ ] T026 [US3] Add `emit_signal()` convenience method to `AuditEventEmitter` in `strategies/common/audit/emitter.py`
- [ ] T027 [US3] Create `SystemEvent` Pydantic model in `strategies/common/audit/events.py` for regime changes, resampling, evolution triggers
- [ ] T028 [US3] Integrate signal logging into `ParticlePortfolio` for consensus signals in `strategies/common/adaptive_control/particle_portfolio.py`
- [ ] T029 [US3] Integrate signal logging into `AlphaEvolveBridge` for evolution triggers in `strategies/common/alpha_evolve/alpha_evolve_bridge.py`
- [ ] T030 [US3] Create unit test for `SignalEvent` and `SystemEvent` serialization in `tests/unit/audit/test_events.py`
- [ ] T031 [US3] Create integration test verifying signal-to-trade correlation in `tests/integration/test_audit_integration.py`

**Checkpoint**: Full signal attribution - can analyze signal quality and strategy performance

---

## Phase 6: User Story 4 - Query Audit Trail (Priority: P2)

**Goal**: Fast queries on audit trail for post-mortem analysis

**Independent Test**: Query 1M events in time range and verify < 5 second response

**Acceptance Criteria**:
- Query response time < 5 seconds for 1M entries
- Filter by time range, event type, source
- Support forensic analysis around incidents

### Implementation for User Story 4

- [ ] T032 [US4] Create `ParquetConverter` class in `strategies/common/audit/converter.py` for JSONL → Parquet conversion
- [ ] T033 [US4] Implement partitioned output (year/month/day) in `ParquetConverter`
- [ ] T034 [US4] Implement 90-day retention policy in `ParquetConverter`
- [ ] T035 [US4] Create `AuditQuery` class in `strategies/common/audit/query.py` with DuckDB backend
- [ ] T036 [US4] Implement `query_time_range()` method in `AuditQuery` with event_type and source filters
- [ ] T037 [US4] Implement `count_by_type()` aggregation method in `AuditQuery`
- [ ] T038 [US4] Implement `reconstruct_incident()` method in `AuditQuery` for ±N minutes around timestamp
- [ ] T039 [US4] Create unit test for `ParquetConverter` in `tests/unit/audit/test_converter.py`
- [ ] T040 [US4] Create unit test for `AuditQuery` time-range and filtering in `tests/unit/audit/test_query.py`
- [ ] T041 [US4] Create performance test for 1M event query in `tests/performance/test_audit_query_performance.py`

**Checkpoint**: Full forensic capability - can analyze incidents in < 5 seconds

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, documentation, and hardening

- [ ] T042 [P] Handle disk full scenario with graceful degradation in `AppendOnlyWriter`
- [ ] T043 [P] Handle high event rate with batching/throttling in `AuditEventEmitter`
- [ ] T044 [P] Implement log corruption detection via checksum verification in `AuditQuery`
- [ ] T045 [P] Create example forensics notebook in `notebooks/audit_forensics_example.ipynb`
- [ ] T046 Run alpha-debug verification on audit module
- [ ] T047 Performance benchmark: verify < 1ms write latency (p99)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Parameter logging
- **User Story 2 (Phase 4)**: Depends on Foundational - Trade logging (can parallel with US1)
- **User Story 3 (Phase 5)**: Depends on Foundational - Signal logging (can parallel with US1/US2)
- **User Story 4 (Phase 6)**: Depends on Foundational - Query interface (can parallel with US1/US2/US3)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Independence

All user stories can be implemented in parallel after Foundational phase:

| Story | Core Component | Integration Point | Can Parallel |
|-------|---------------|-------------------|--------------|
| US1 | ParameterChangeEvent | MetaController, SOPSGillerSizer | Yes |
| US2 | TradeEvent, AuditObserver | NautilusTrader MessageBus | Yes |
| US3 | SignalEvent | ParticlePortfolio, AlphaEvolveBridge | Yes |
| US4 | ParquetConverter, AuditQuery | None (analysis layer) | Yes |

### Within Each User Story

1. Create Pydantic event model first
2. Add convenience method to emitter
3. Create unit tests
4. Integrate with target components
5. Create integration tests

---

## Parallel Example: Foundational Phase

```bash
# Sequential tasks in Phase 2 (same files):
T004→T005→T006 (config.py, events.py)
T007→T008 (writer.py, emitter.py)

# Parallel tasks (different files, after dependencies ready):
T009: Create unit test for AppendOnlyWriter in tests/unit/audit/test_writer.py
T010: Create unit test for AuditEvent checksum in tests/unit/audit/test_events.py
T010b: Create crash recovery test in tests/unit/audit/test_writer.py
```

## Parallel Example: User Stories

```bash
# After Foundational phase completes, launch all user stories in parallel:

# US1 team:
T011→T012→T013→T014→T015→T016→T017

# US2 team:
T018→T019→T020→T021→T022→T023→T024

# US3 team:
T025→T026→T027→T028→T029→T030→T031

# US4 team:
T032→T033→T034→T035→T036→T037→T038→T039→T040→T041
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T010)
3. Complete Phase 3: User Story 1 (T011-T017)
4. **STOP and VALIDATE**: Test parameter logging independently
5. Deploy - can now detect parameter manipulation

### Incremental Delivery

| Milestone | Stories | Value Delivered |
|-----------|---------|-----------------|
| MVP | US1 | Parameter manipulation detection |
| +Trades | US1+US2 | Trade execution audit |
| +Signals | US1+US2+US3 | Full trading attribution |
| Complete | All | Forensic query capability |

### Critical Path

```
Setup → Foundational → US1 (MVP)
                    → US2 (parallel)
                    → US3 (parallel)
                    → US4 (parallel)
                    → Polish
```

---

## Notes

- All event models share `strategies/common/audit/events.py` - create in sequence (T005→T006→T011→T018→T025→T027)
- `AuditEventEmitter` methods added incrementally - sequence T008→T012→T019→T026
- Integration tests can run in parallel as they target different components
- DuckDB is optional dependency - US4 can be deferred if not needed immediately
- Sync writes enabled only for TradeEvent (audit compliance) - others use async
- **ALWAYS use test-runner agent** for executing tests (per constitution)
