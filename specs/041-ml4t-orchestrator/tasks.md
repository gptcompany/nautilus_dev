# Tasks: ML4T Orchestrator

**Input**: Design documents from `/specs/041-ml4t-orchestrator/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md (required)

**Tests**: Tests are included for critical paths (inference latency, training pipeline, retrain trigger).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - complex algorithmic tasks
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

---

## Phase 1: Setup (Module Structure)

**Purpose**: Create `pipeline/orchestrator/` directory structure

- [ ] T001 Create directory structure `pipeline/orchestrator/` with `__init__.py`
- [ ] T002 [P] Create `pipeline/orchestrator/config.py` with OrchestratorConfig dataclass (from data-model.md)
- [ ] T003 [P] Create `pipeline/orchestrator/events.py` with SignalEvent, EnrichedSignalEvent, InferenceResult, TrainingResult, RetrainTrigger dataclasses (from data-model.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `pipeline/orchestrator/persistence.py` with ModelPersistence class (load/save joblib)
- [ ] T005 Verify existing dependencies are importable:
  - `strategies/common/meta_learning/meta_model.py` - MetaModel class
  - `strategies/common/meta_learning/feature_engineering.py` - extract_features function
  - `strategies/common/orderflow/vpin.py` - VPINIndicator class
  - `strategies/common/position_sizing/integrated_sizing.py` - IntegratedSizer class
- [ ] T006 Create test fixtures in `tests/pipeline/orchestrator/conftest.py` with mock bars, signals, and model

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Inference Loop (Priority: P1) 🎯 MVP

**Goal**: Real-time signal enrichment with meta-learning confidence for position sizing

**Independent Test**: Inject mock SignalEvent, verify RiskStage receives enriched alpha_output with meta_confidence, regime_weight, toxicity

### Tests for User Story 1

- [ ] T007 [US1] Unit test for InferenceLoop in `tests/pipeline/orchestrator/test_inference.py`:
  - Test feature extraction latency <5ms
  - Test model prediction latency <5ms
  - Test total inference <10ms (SC-001)
  - Test cold start returns default confidence 0.5 (FR-004)

### Implementation for User Story 1

- [ ] T008 [US1] Create `pipeline/orchestrator/inference.py` with InferenceLoop class:
  - Constructor takes OrchestratorConfig, optional MetaModel
  - `process(signal_event: SignalEvent) -> EnrichedSignalEvent`
  - Extract features using meta_learning.feature_engineering
  - Query VPINIndicator for toxicity
  - Predict confidence using MetaModel (or default 0.5)
  - Track latency breakdown (feature_extraction_ns, prediction_ns, total_latency_ns)
- [ ] T009 [US1] Add `to_meta_output()` method to EnrichedSignalEvent for RiskStage integration (FR-014)
- [ ] T010 [US1] Integration test verifying InferenceLoop output integrates with RiskStage in `tests/pipeline/orchestrator/test_inference_integration.py`

**Checkpoint**: User Story 1 complete - inference loop delivers enriched signals

---

## Phase 4: User Story 2 - Training Loop (Priority: P2)

**Goal**: Batch training of meta-model on historical data with walk-forward validation

**Independent Test**: Provide historical bars, verify model file produced with accuracy metrics

### Tests for User Story 2

- [ ] T011 [US2] Unit test for TrainingLoop in `tests/pipeline/orchestrator/test_training.py`:
  - Test minimum data requirement (1000 bars)
  - Test label generation from bars
  - Test walk-forward validation produces accuracy metric
  - Test model persistence to joblib file
  - Test TrainingResult contains logged metrics (accuracy, AUC, feature_importance) per FR-009

### Implementation for User Story 2

- [ ] T012 [US2] Create `pipeline/orchestrator/training.py` with TrainingLoop class:
  - Constructor takes OrchestratorConfig
  - `train(bars: list[Bar]) -> TrainingResult`
  - Generate triple-barrier labels using `strategies/common/labeling/`
  - Extract features using `meta_learning.feature_engineering`
  - Train MetaModel with walk-forward cross-validation (FR-007)
  - Return TrainingResult with model, accuracy, auc, feature_importance
- [ ] T013 [US2] Add model persistence after successful training using ModelPersistence (FR-008)
- [ ] T014 [US2] Integration test for full training pipeline in `tests/pipeline/orchestrator/test_training_integration.py`

**Checkpoint**: User Story 2 complete - training loop produces validated models

---

## Phase 5: User Story 3 - Automatic Retrain Trigger (Priority: P3)

**Goal**: Monitor live accuracy and trigger retrain on degradation

**Independent Test**: Simulate accuracy drop, verify RetrainTrigger event emitted

### Tests for User Story 3

- [ ] T015 [US3] Unit test for RetrainMonitor in `tests/pipeline/orchestrator/test_retrain.py`:
  - Test accuracy tracking (rolling window)
  - Test trigger when drop exceeds threshold (FR-011)
  - Test no trigger when accuracy stable
  - Test sample-based trigger (FR-013)

### Implementation for User Story 3

- [ ] T016 [US3] Create `pipeline/orchestrator/retrain.py` with RetrainMonitor class:
  - Constructor takes OrchestratorConfig, baseline_accuracy
  - `record_prediction(actual: int, predicted: int)` - track outcomes
  - `check_retrain() -> RetrainTrigger | None` - evaluate if retrain needed
  - Rolling accuracy calculation with configurable window
  - Support both accuracy-drop and sample-count triggers
- [ ] T017 [US3] Add atomic model hot-swap to InferenceLoop `hot_swap_model(model: MetaModel)` (SC-005):
  - Use threading.Lock for atomic reference swap
  - Covers edge case: "model hot-swap during retrain causes zero dropped signals"
- [ ] T018 [US3] Integration test for retrain trigger flow in `tests/pipeline/orchestrator/test_retrain_integration.py`

**Checkpoint**: User Story 3 complete - system auto-detects model degradation

---

## Phase 6: User Story 4 - Redis MessageBus Integration (Priority: P4)

**Goal**: Event-driven architecture via NautilusTrader Redis MessageBus

**Independent Test**: Publish SignalEvent to Redis, verify orchestrator processes and publishes EnrichedSignalEvent

### Tests for User Story 4

- [ ] T019 [US4] Unit test for Redis pub/sub in `tests/pipeline/orchestrator/test_redis.py`:
  - Test subscription to signal channel
  - Test publication to enriched channel
  - Test fallback when Redis unavailable (FR-016)

### Implementation for User Story 4

- [ ] T020 [US4] Add Redis MessageBus support to `pipeline/orchestrator/orchestrator.py`:
  - Subscribe to `redis_channel_signals` from config
  - Publish EnrichedSignalEvent to `redis_channel_enriched`
  - Implement fallback to direct method calls on connection failure
- [ ] T021 [US4] Integration test with actual Redis in `tests/pipeline/orchestrator/test_redis_integration.py`

**Checkpoint**: User Story 4 complete - loose-coupled event architecture enabled

---

## Phase 7: Main Orchestrator & Polish

**Purpose**: Assemble all components into ML4TOrchestrator facade

- [ ] T022 Create `pipeline/orchestrator/orchestrator.py` with ML4TOrchestrator class:
  - Constructor takes OrchestratorConfig
  - `start()` - load model, initialize loops, subscribe to MessageBus
  - `stop()` - graceful shutdown
  - `process_signal(event: SignalEvent) -> EnrichedSignalEvent` - delegate to InferenceLoop
  - `train(bars: list[Bar]) -> TrainingResult` - delegate to TrainingLoop
  - `hot_swap_model(model: MetaModel)` - atomic model replacement
- [ ] T023 Update `pipeline/orchestrator/__init__.py` with public exports:
  - ML4TOrchestrator, OrchestratorConfig, SignalEvent, EnrichedSignalEvent, TrainingResult
- [ ] T024 [P] End-to-end test in `tests/pipeline/orchestrator/test_orchestrator_e2e.py`:
  - Full flow: train → inference → retrain trigger
- [ ] T025 [P] Update `pipeline/stages/risk.py` docstring to reference ML4TOrchestrator integration
- [ ] T026 Performance benchmark in `tests/pipeline/orchestrator/test_benchmark.py`:
  - SC-001: Use pytest-benchmark with 1000 signal iterations, assert p99 < 10ms
  - SC-002: Time training on 260K synthetic bars, assert < 5 minutes
  - SC-004: Throughput test with 1000 signals in tight loop, measure signals/sec (direct call capacity, no queue)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Inference): No dependencies on other stories - **Start here for MVP**
  - US2 (Training): Independent of US1 (can parallelize if staffed)
  - US3 (Retrain): Requires US1 InferenceLoop for hot_swap_model
  - US4 (Redis): Requires US1 InferenceLoop for event processing
- **Polish (Phase 7)**: Depends on US1-US4 completion

### User Story Dependencies

```
              ┌─────────────────┐
              │  Foundational   │
              │   (Phase 2)     │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │   US1    │  │   US2    │  │   US4    │
   │Inference │  │ Training │  │  Redis   │
   │  (MVP)   │  │          │  │(optional)│
   └────┬─────┘  └──────────┘  └────┬─────┘
        │                           │
        └───────────┬───────────────┘
                    ▼
              ┌──────────┐
              │   US3    │
              │ Retrain  │
              └──────────┘
```

### Parallel Opportunities

Within Phase 1 (Setup):
- T002 [P] config.py and T003 [P] events.py can run in parallel

Within Phase 7 (Polish):
- T024 [P] e2e test and T025 [P] docstring update can run in parallel

### Critical Path (MVP)

1. T001 → T002, T003 (Setup)
2. T004, T005, T006 (Foundational)
3. T007 → T008 → T009 → T010 (US1 complete)
4. **MVP READY** - can demo inference loop

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006)
3. Complete Phase 3: User Story 1 (T007-T010)
4. **STOP and VALIDATE**: Test inference loop independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP DEMO!**
3. Add User Story 2 → Training capability
4. Add User Story 3 → Auto-retrain capability
5. Add User Story 4 → Event-driven architecture
6. Polish → Production ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests pass before moving to next story
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

### File Reference

| Task | File | Notes |
|------|------|-------|
| T002 | `pipeline/orchestrator/config.py` | OrchestratorConfig dataclass |
| T003 | `pipeline/orchestrator/events.py` | All event dataclasses (single source of truth) |
| T004 | `pipeline/orchestrator/persistence.py` | ModelPersistence class |
| T006 | `tests/pipeline/orchestrator/conftest.py` | Test fixtures |
| T007 | `tests/pipeline/orchestrator/test_inference.py` | Unit tests for inference |
| T008-T009 | `pipeline/orchestrator/inference.py` | InferenceLoop implementation |
| T010 | `tests/pipeline/orchestrator/test_inference_integration.py` | Integration test |
| T011 | `tests/pipeline/orchestrator/test_training.py` | Unit tests for training |
| T012-T013 | `pipeline/orchestrator/training.py` | TrainingLoop implementation |
| T014 | `tests/pipeline/orchestrator/test_training_integration.py` | Integration test |
| T015 | `tests/pipeline/orchestrator/test_retrain.py` | Unit tests for retrain |
| T016-T017 | `pipeline/orchestrator/retrain.py` | RetrainMonitor implementation |
| T018 | `tests/pipeline/orchestrator/test_retrain_integration.py` | Integration test |
| T019 | `tests/pipeline/orchestrator/test_redis.py` | Unit tests for Redis |
| T020 | `pipeline/orchestrator/orchestrator.py` | Redis integration |
| T021 | `tests/pipeline/orchestrator/test_redis_integration.py` | Integration test |
| T022-T023 | `pipeline/orchestrator/orchestrator.py` | ML4TOrchestrator facade |
| T024 | `tests/pipeline/orchestrator/test_orchestrator_e2e.py` | E2E test |
| T026 | `tests/pipeline/orchestrator/test_benchmark.py` | Performance benchmarks |

**Note**: `data-model.md` is reference documentation; `events.py` (T003) is the implementation source of truth for all dataclasses.
