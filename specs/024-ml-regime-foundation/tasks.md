# Tasks: ML Regime Detection Foundation

**Input**: Design documents from `/specs/024-ml-regime-foundation/`
**Prerequisites**: plan.md, spec.md
**Branch**: `024-ml-regime-foundation`

**Tests**: Included (spec requires >80% coverage)

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - complex algorithmic tasks
- **[Story]**: US1, US2, US3 (maps to user stories from spec.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependencies

- [X] T001 Install dependencies: `uv pip install hmmlearn scikit-learn`
- [X] T002 [P] Create directory structure: `strategies/common/regime_detection/`
- [X] T003 [P] Create directory structure: `strategies/common/position_sizing/`
- [X] T004 [P] Create directory structure: `strategies/common/utils/`
- [X] T005 [P] Create `strategies/common/__init__.py` (already existed)
- [X] T006 [P] Create `strategies/common/regime_detection/__init__.py`
- [X] T007 [P] Create `strategies/common/position_sizing/__init__.py`
- [X] T008 [P] Create `strategies/common/utils/__init__.py`

---

## Phase 2: Foundational (Data Transforms)

**Purpose**: Shared utilities used by all regime detection components

**⚠️ CRITICAL**: Must complete before user story implementation

- [X] T009 Create data_transforms module with returns/volatility helpers in `strategies/common/utils/data_transforms.py`
- [X] T010 Create RegimeState enum (TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE) in `strategies/common/regime_detection/types.py`
- [X] T011 Create VolatilityCluster enum (LOW, MEDIUM, HIGH) in `strategies/common/regime_detection/types.py`
- [X] T012 Create RegimeConfig Pydantic model in `strategies/common/regime_detection/config.py`
- [X] T013 Create GillerConfig Pydantic model in `strategies/common/position_sizing/config.py`

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - HMM Regime Detection (Priority: P1) 🎯 MVP

**Goal**: Detect market regimes (trending, ranging, volatile) using Hidden Markov Models

**Independent Test**: Test with synthetic regime data, verify correct regime identification

### Tests for User Story 1

- [X] T014 [P] [US1] Create test file `tests/test_hmm_filter.py` with test fixtures
- [X] T015 [P] [US1] Write test_hmm_fit_with_sufficient_data in `tests/test_hmm_filter.py`
- [X] T016 [P] [US1] Write test_hmm_fit_fails_with_insufficient_data in `tests/test_hmm_filter.py`
- [X] T017 [P] [US1] Write test_hmm_predict_returns_regime_label in `tests/test_hmm_filter.py`
- [X] T018 [P] [US1] Write test_hmm_predict_latency_under_10ms in `tests/test_hmm_filter.py`

### Implementation for User Story 1

- [X] T019 [E] [US1] Implement HMMRegimeFilter class in `strategies/common/regime_detection/hmm_filter.py`:
  - `__init__(n_states: int = 3, n_iter: int = 100)`
  - `fit(returns: np.ndarray, volatility: np.ndarray) -> None`
  - `predict(returns: float, volatility: float) -> RegimeState`
  - `get_state_probabilities() -> np.ndarray`
- [X] T020 [US1] Add convergence checking with multiple random initializations in `hmm_filter.py`
- [X] T021 [US1] Add regime label mapping logic (state index → RegimeState enum) in `hmm_filter.py`
- [X] T022 [US1] Export HMMRegimeFilter in `strategies/common/regime_detection/__init__.py`

**Checkpoint**: HMM regime detection fully functional and tested

---

## Phase 4: User Story 2 - GMM Volatility Clustering (Priority: P1)

**Goal**: Cluster volatility states using Gaussian Mixture Models

**Independent Test**: Test with known volatility distribution, verify correct clustering

### Tests for User Story 2

- [ ] T023 [P] [US2] Create test file `tests/test_gmm_filter.py` with test fixtures
- [ ] T024 [P] [US2] Write test_gmm_fit_identifies_three_clusters in `tests/test_gmm_filter.py`
- [ ] T025 [P] [US2] Write test_gmm_predict_returns_volatility_cluster in `tests/test_gmm_filter.py`
- [ ] T026 [P] [US2] Write test_gmm_predict_probabilities in `tests/test_gmm_filter.py`

### Implementation for User Story 2

- [ ] T027 [E] [US2] Implement GMMVolatilityFilter class in `strategies/common/regime_detection/gmm_filter.py`:
  - `__init__(n_clusters: int = 3)`
  - `fit(volatility: np.ndarray) -> None`
  - `predict(volatility: float) -> VolatilityCluster`
  - `get_cluster_probabilities(volatility: float) -> np.ndarray`
- [ ] T028 [US2] Add cluster label mapping (cluster index → VolatilityCluster enum) in `gmm_filter.py`
- [ ] T029 [US2] Export GMMVolatilityFilter in `strategies/common/regime_detection/__init__.py`

**Checkpoint**: GMM volatility clustering fully functional and tested

---

## Phase 5: User Story 3 - Sub-linear Position Sizing (Priority: P1)

**Goal**: Position sizing using sub-linear scaling (signal^0.5) per Giller research

**Independent Test**: Test with known signals, verify sqrt scaling applied correctly

### Tests for User Story 3

- [ ] T030 [P] [US3] Create test file `tests/test_giller_sizing.py` with test fixtures
- [ ] T031 [P] [US3] Write test_giller_sqrt_scaling in `tests/test_giller_sizing.py`
- [ ] T032 [P] [US3] Write test_giller_with_regime_weight in `tests/test_giller_sizing.py`
- [ ] T033 [P] [US3] Write test_giller_edge_cases_zero_negative in `tests/test_giller_sizing.py`
- [ ] T034 [P] [US3] Write test_giller_respects_min_max_limits in `tests/test_giller_sizing.py`

### Implementation for User Story 3

- [ ] T035 [US3] Implement GillerSizer class in `strategies/common/position_sizing/giller_sizing.py`:
  - `__init__(config: GillerConfig)`
  - `calculate(signal: float, regime_weight: float = 1.0, toxicity: float = 0.0) -> float`
  - Sub-linear formula: `sign(signal) * |signal|^exponent * regime_weight * (1 - toxicity)`
- [ ] T036 [US3] Add min/max size clamping in `giller_sizing.py`
- [ ] T037 [US3] Export GillerSizer in `strategies/common/position_sizing/__init__.py`

**Checkpoint**: Giller position sizing fully functional and tested

---

## Phase 6: Integration - RegimeManager

**Goal**: Unified facade combining HMM, GMM, and optional macro filters

**Independent Test**: Test full pipeline: bars → regime → position size

### Tests for Integration

- [ ] T038 [P] Create test file `tests/test_regime_manager.py`
- [ ] T039 [P] Write test_regime_manager_update_returns_combined_regime in `tests/test_regime_manager.py`
- [ ] T040 [P] Write test_regime_manager_with_real_btcusdt_data in `tests/test_regime_manager.py`

### Implementation for Integration

- [ ] T041 Implement RegimeManager class in `strategies/common/regime_detection/regime_manager.py`:
  - `__init__(config: RegimeConfig)`
  - `fit(bars: list[Bar]) -> None`
  - `update(bar: Bar) -> RegimeResult`
  - `get_regime_weight() -> float`
- [ ] T042 Create RegimeResult dataclass (regime, volatility, weight, confidence) in `regime_manager.py`
- [ ] T043 Integrate HMMRegimeFilter and GMMVolatilityFilter in RegimeManager
- [ ] T044 Implement regime transition logging (FR-008) in `regime_manager.py`
- [ ] T045 Export RegimeManager, RegimeResult in `strategies/common/regime_detection/__init__.py`

**Checkpoint**: Full regime detection pipeline functional

---

## Phase 7: Polish & Documentation

**Purpose**: Final cleanup and documentation

- [ ] T046 [P] Add docstrings to all public classes/methods in `regime_detection/`
- [ ] T047 [P] Add docstrings to all public classes/methods in `position_sizing/`
- [ ] T048 [P] Add type hints validation (run mypy)
- [ ] T049 Run ruff format and ruff check on all new files
- [ ] T050 Run alpha-debug verification on implementation (use alpha-debug agent)
- [ ] T051 Update `strategies/common/regime_detection/__init__.py` with __all__ exports

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies
- **Phase 2 (Foundational)**: Depends on Phase 1
- **Phase 3-5 (User Stories)**: All depend on Phase 2, can run in parallel
- **Phase 6 (Integration)**: Depends on Phase 3, 4, 5
- **Phase 7 (Polish)**: Depends on Phase 6

### User Story Dependencies

- **US1 (HMM)**: Phase 2 → can start immediately after foundation
- **US2 (GMM)**: Phase 2 → can start immediately after foundation (parallel with US1)
- **US3 (Giller)**: Phase 2 → can start immediately after foundation (parallel with US1, US2)

### Parallel Opportunities

```
Phase 1: T002, T003, T004, T005, T006, T007, T008 (all [P])
Phase 3: T014, T015, T016, T017, T018 (all [P] tests)
Phase 4: T023, T024, T025, T026 (all [P] tests)
Phase 5: T030, T031, T032, T033, T034 (all [P] tests)
Phase 6: T038, T039, T040 (all [P] tests)
Phase 7: T045, T046, T047 (all [P])
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: HMM Regime Detection (US1)
4. **STOP and VALIDATE**: Test HMM independently
5. Proceed to US2, US3

### Recommended Order

```
Day 1: Phase 1 + Phase 2 + Phase 3 (HMM)
Day 2: Phase 4 (GMM) + Phase 5 (Giller)
Day 3: Phase 6 (Integration) + Phase 7 (Polish)
```

---

## Summary

| Phase | Tasks | Parallel Tasks |
|-------|-------|----------------|
| Setup | 8 | 7 |
| Foundational | 5 | 0 |
| US1 (HMM) | 9 | 5 |
| US2 (GMM) | 7 | 4 |
| US3 (Giller) | 8 | 5 |
| Integration | 8 | 3 |
| Polish | 6 | 3 |
| **Total** | **51** | **27** |

**MVP Scope**: Phase 1-3 (HMM only) = 22 tasks
**Full Scope**: All phases = 51 tasks

**Note**: US4 (FRED) e US5 (Fear&Greed) già implementati - non inclusi in questo scope.
