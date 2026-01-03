# Tasks: Meta-Learning Pipeline

**Input**: Design documents from `/specs/026-meta-learning-pipeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.py, quickstart.md

**Tests**: Included - TDD required per spec.md requirements.

**Organization**: Tasks grouped by user story (US1-US4) from spec.md priorities.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - complex algorithmic tasks
- **[Story]**: Which user story (US1, US2, US3, US4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [X] T001 Create `strategies/common/labeling/` directory structure
- [X] T002 [P] Create `strategies/common/meta_learning/` directory structure
- [X] T003 [P] Create `strategies/common/labeling/__init__.py` with public exports
- [X] T004 [P] Create `strategies/common/meta_learning/__init__.py` with public exports
- [X] T005 Verify existing dependencies (numpy, scipy, scikit-learn) in nightly environment

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create Pydantic config models in `strategies/common/labeling/config.py` (TripleBarrierConfig)
- [X] T007 [P] Create Pydantic config models in `strategies/common/meta_learning/config.py` (MetaModelConfig, WalkForwardConfig)
- [X] T008 [P] Create Pydantic config models in `strategies/common/regime_detection/config.py` (BOCDConfig) - extend existing
- [X] T009 [P] Create Pydantic config models in `strategies/common/position_sizing/config.py` (IntegratedSizingConfig) - extend existing
- [X] T010 [VERIFY] Verify API contracts complete in `specs/026-meta-learning-pipeline/contracts/api.py` - Protocols already exist, confirm all methods defined
- [X] T011 [P] Create test fixtures in `tests/conftest.py` for meta-learning tests (price series, signals, labels)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Triple Barrier Labeling (Priority: P1)

**Goal**: Implement triple barrier labeling per AFML specification

**Independent Test**: Verify labels match expected outcomes on historical trades (+1 TP, -1 SL, 0 timeout)

### Tests for User Story 1

**Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [US1] Write unit tests for triple barrier labeling in `tests/test_triple_barrier.py`
  - Test +1 label when TP hit first
  - Test -1 label when SL hit first
  - Test 0 label on timeout
  - Test ATR-based barrier calculation
  - Test vectorized batch processing

### Implementation for User Story 1

- [X] T013 [E] [US1] Implement `TripleBarrierLabeler` class in `strategies/common/labeling/triple_barrier.py`
  - `apply()` method for vectorized labeling
  - `get_barrier_events()` for detailed event tracking
  - ATR-based barrier calculation
  - Support for long and short signals
  - **Edge case**: Handle "no barrier hit" (return 0 with final return sign)
- [X] T014 [US1] Create barrier calculation helpers in `strategies/common/labeling/label_utils.py`
  - `get_vertical_barriers()` - timeout indices
  - `get_horizontal_barriers()` - TP/SL price levels
  - `check_barrier_hit()` - vectorized barrier checking
- [X] T015 [US1] Update `strategies/common/labeling/__init__.py` with public API exports

**Checkpoint**: Triple barrier labeling functional, can process historical data independently

---

## Phase 4: User Story 2 - Meta-Model Training (Priority: P1)

**Goal**: Train secondary model to predict P(primary_model_correct)

**Independent Test**: Verify meta-model AUC > 0.6 on validation set

**Depends on**: US1 (triple barrier labels for training data)

### Tests for User Story 2

- [X] T016 [US2] Write unit tests for meta-label generation in `tests/test_meta_model.py`
  - Test meta-label creation (correct/incorrect classification)
  - Test feature extraction
  - Test model training/prediction API
  - Test AUC > 0.6 requirement
- [X] T017 [P] [US2] Write unit tests for walk-forward validation in `tests/test_walk_forward.py`
  - Test rolling window splits
  - Test embargo/purging
  - Test no look-ahead bias

### Implementation for User Story 2

- [X] T018 [US2] Implement `MetaLabelGenerator` class in `strategies/common/meta_learning/meta_label.py`
  - Create meta-labels from primary signals + true labels
  - Compute: meta_label = 1 if primary_signal == true_label else 0
- [X] T019 [US2] Implement feature extraction in `strategies/common/meta_learning/feature_engineering.py`
  - Volume features (relative volume, volume momentum)
  - Volatility features (rolling std, ATR ratio)
  - Momentum features (returns, RSI-like)
  - Regime features (HMM state, if available)
- [X] T020 [E] [US2] Implement `MetaModel` class in `strategies/common/meta_learning/meta_model.py`
  - RandomForest wrapper with `fit()` and `predict_proba()`
  - Feature importance tracking
  - Calibration check (reliability diagram)
  - **Edge case**: Return 0.5 confidence when insufficient training data (<100 samples)
- [X] T021 [US2] Implement walk-forward validation in `strategies/common/meta_learning/walk_forward.py`
  - `WalkForwardSplitter` class
  - Rolling 252/63/21/5 bar windows (train/test/step/embargo)
  - `walk_forward_train()` for proper training protocol
- [X] T022 [US2] Update `strategies/common/meta_learning/__init__.py` with public API exports

**Checkpoint**: Meta-model training functional, achieves AUC > 0.6

---

## Phase 5: User Story 3 - BOCD Regime Change Detection (Priority: P2)

**Goal**: Implement Bayesian Online Changepoint Detection for real-time regime detection

**Independent Test**: Verify BOCD detects known regime changes within 10 bars

### Tests for User Story 3

- [X] T023 [US3] Write unit tests for BOCD in `tests/test_bocd.py`
  - Test update mechanics (single observation)
  - Test changepoint probability calculation
  - Test run length distribution
  - Test detection on synthetic regime change data
  - Test threshold-based detection flag

### Implementation for User Story 3

- [X] T024 [E] [US3] Implement `BOCD` class in `strategies/common/regime_detection/bocd.py`
  - `update(observation)` - process single observation
  - `get_changepoint_probability()` - P(run_length = 0)
  - `get_run_length_distribution()` - full posterior
  - `is_changepoint(threshold)` - detection flag
  - `reset()` - clear state
  - Student-t conjugate prior (Adams & MacKay 2007)
  - **Edge case**: Handle non-stationary mean+variance via robust hazard rate
  - **FR-006**: When `is_changepoint()` returns True, caller should trigger regime refit
- [X] T025 [US3] Update `strategies/common/regime_detection/__init__.py` with BOCD exports

**Checkpoint**: BOCD functional, detects regime changes in streaming data

---

## Phase 6: User Story 4 - Integrated Bet Sizing Pipeline (Priority: P1)

**Goal**: Unified pipeline combining all factors into final position size

**Independent Test**: Verify position sizes reflect all input factors correctly

**Depends on**: US1-US3 (all previous components)

### Tests for User Story 4

- [X] T026 [US4] Write unit tests for integrated sizing in `tests/test_integrated_sizing.py`
  - Test multiplicative combination formula
  - Test edge cases (high toxicity, low confidence)
  - Test default values for missing factors
  - Test direction preservation
  - Test min/max size clamping

### Implementation for User Story 4

- [X] T027 [US4] Implement `IntegratedSizer` class in `strategies/common/position_sizing/integrated_sizing.py`
  - `calculate(signal, meta_confidence, regime_weight, toxicity)` -> IntegratedSize
  - Formula: direction * |signal|^0.5 * meta_confidence * regime_weight * (1-toxicity) * kelly
  - Factor breakdown tracking via `IntegratedSize.factors` property
  - Default values for missing inputs
  - **FR-008**: Log factor contributions at DEBUG level for debugging
- [X] T028 [US4] Update `strategies/common/position_sizing/__init__.py` with IntegratedSizer exports

**Checkpoint**: Integrated sizing functional, combines all factors correctly

---

## Phase 7: Integration & End-to-End Testing

**Purpose**: Verify full pipeline works together

- [ ] T029 Write integration test in `tests/integration/test_meta_learning_pipeline.py`
  - Full pipeline: bars -> labeling -> meta-model -> sizing
  - Verify no look-ahead bias
  - Test with BacktestNode
- [ ] T030 Create example strategy in `strategies/development/meta_learning_example.py`
  - Uses all components (Triple Barrier, Meta-Model, BOCD, IntegratedSizer)
  - Demonstrates warmup pattern
  - Shows logging of factor contributions
- [ ] T031 Verify performance requirements:
  - Triple barrier: <60s for 1M bars
  - Meta-model inference: <5ms
  - BOCD update: <5ms
  - Integrated sizing: <20ms end-to-end

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation

- [ ] T032 [P] Verify all type hints and docstrings complete
- [ ] T033 [P] Run ruff format and lint on all new files
- [ ] T034 [P] Verify test coverage > 80% for all new modules
- [ ] T035 Update `specs/026-meta-learning-pipeline/quickstart.md` with final API examples
- [ ] T036 Run alpha-debug verification on all [E] marked implementations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundational)**: Depends on Setup - BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Foundational
- **Phase 4 (US2)**: Depends on US1 (needs labels for training)
- **Phase 5 (US3)**: Depends on Foundational only (independent of US1/US2)
- **Phase 6 (US4)**: Depends on US1-US3 (integrates all components)
- **Phase 7 (Integration)**: Depends on US1-US4
- **Phase 8 (Polish)**: Depends on all previous phases

### User Story Dependencies

```
Foundational (Phase 2)
        │
        ├──────────────────┬────────────────────┐
        ▼                  ▼                    │
    US1 (P3)           US3 (P5)                 │
        │              (independent)            │
        ▼                  │                    │
    US2 (P4)               │                    │
        │                  │                    │
        └──────────────────┴────────────────────┘
                           │
                           ▼
                       US4 (P6)
                   (integrates all)
```

### Parallel Opportunities

**Phase 2 (Foundational)**: T007, T008, T009, T011 can run in parallel

**After Foundational**:
- US1 (Phase 3) and US3 (Phase 5) can start in parallel
- US2 (Phase 4) must wait for US1 completion
- US4 (Phase 6) must wait for US1-US3 completion

**Phase 8 (Polish)**: T032, T033, T034 can run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch all config tasks together:
Task: "Create Pydantic config in strategies/common/meta_learning/config.py" [T007]
Task: "Create Pydantic config in strategies/common/regime_detection/config.py" [T008]
Task: "Create Pydantic config in strategies/common/position_sizing/config.py" [T009]
Task: "Create test fixtures in tests/conftest.py" [T011]
```

## Parallel Example: After Foundational

```bash
# US1 and US3 can start together:
Task: "Write unit tests for triple barrier in tests/test_triple_barrier.py" [T012]
Task: "Write unit tests for BOCD in tests/test_bocd.py" [T023]
```

---

## Implementation Strategy

### MVP First (User Story 1 + 4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 - Triple Barrier Labeling
4. **VALIDATE**: Test labeling independently
5. Skip to Phase 6: US4 - Integrated Sizing (use defaults for meta/BOCD)
6. Deploy basic pipeline

### Full Implementation

1. Setup + Foundational -> Foundation ready
2. US1 (Triple Barrier) -> Test independently
3. US2 (Meta-Model) -> Test independently
4. US3 (BOCD) -> Test independently (can parallel with US1)
5. US4 (Integrated) -> Test full pipeline
6. Integration tests + Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [E] tasks = complex algorithms triggering alpha-evolve (T013, T020, T024)
- [USn] label maps task to specific user story
- TDD: Write failing tests BEFORE implementation
- Commit after each task or logical group
- Stop at checkpoints to validate story independently
- Use existing Spec 024/025 components (HMM, GMM, VPIN, Giller)
