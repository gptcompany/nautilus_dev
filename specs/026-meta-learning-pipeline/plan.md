# Implementation Plan: Meta-Learning Pipeline

**Feature Branch**: `026-meta-learning-pipeline`
**Created**: 2026-01-03
**Status**: Ready for Implementation
**Spec Reference**: `specs/026-meta-learning-pipeline/spec.md`

## Architecture Overview

The Meta-Learning Pipeline extends the existing ML infrastructure with triple barrier labeling, meta-model training, BOCD regime detection, and integrated bet sizing. It builds upon the foundation established in Spec 024 (ML Regime Foundation) and Spec 025 (Orderflow Indicators).

### System Context

```
Existing Foundation (Already Implemented):
├── strategies/common/regime_detection/hmm_filter.py  # HMM regime detection
├── strategies/common/regime_detection/gmm_filter.py  # GMM volatility clustering
├── strategies/common/position_sizing/giller_sizing.py # Sub-linear sizing
└── strategies/common/orderflow/vpin.py               # VPIN toxicity

This Spec (To Implement):
├── strategies/common/labeling/triple_barrier.py      # US1: Triple barrier labeling
├── strategies/common/meta_learning/meta_model.py     # US2: Meta-model training
├── strategies/common/regime_detection/bocd.py        # US3: BOCD changepoint
└── strategies/common/position_sizing/integrated_sizing.py # US4: Unified pipeline
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│   Tick/Bar Data → VPIN Buckets → OHLCV → Features → Labels          │
└─────────────────────────────────────────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │   EXISTING   │     │   EXISTING   │     │    NEW       │
   │     VPIN     │     │   HMM/GMM    │     │    BOCD      │
   │   Toxicity   │     │   Regime     │     │  Changepoint │
   │  (Spec 025)  │     │  (Spec 024)  │     │   (US3)      │
   └──────────────┘     └──────────────┘     └──────────────┘
          │                     │                     │
          │   toxicity          │   regime            │   changepoint_prob
          └─────────────────────┼─────────────────────┘
                                ▼
                    ┌────────────────────┐
                    │  NEW: Triple       │
                    │  Barrier Labeling  │
                    │      (US1)         │
                    └────────────────────┘
                                │
                                ▼ labels
                    ┌────────────────────┐
                    │  NEW: Meta-Model   │
                    │  P(will_profit)    │
                    │      (US2)         │
                    └────────────────────┘
                                │
                                ▼ meta_confidence
                    ┌────────────────────────────────────┐
                    │  NEW: IntegratedSizer (US4)        │
                    │  = direction *                     │
                    │    |signal|^0.5 *      (Giller)    │
                    │    meta_confidence *   (Meta)      │
                    │    regime_weight *     (HMM)       │
                    │    (1 - toxicity)      (VPIN)      │
                    └────────────────────────────────────┘
                                │
                                ▼
                    ┌────────────────────┐
                    │   ORDER SUBMIT     │
                    └────────────────────┘
```

## Technical Decisions

### Decision 1: Triple Barrier Labeling Library

**Options Considered**:
1. **Option A: mlfinlab library**
   - Pros: Official AFML implementation, well-tested, includes get_events/get_labels
   - Cons: May have dependency issues with Python 3.11+, Hudson & Thames licensing changes

2. **Option B: Custom implementation**
   - Pros: Full control, no external dependencies, tailored to NautilusTrader
   - Cons: Need to implement from scratch, potential for bugs

**Selected**: Option B (Custom implementation)

**Rationale**: mlfinlab has licensing concerns and potential Python compatibility issues. The triple barrier algorithm is well-documented in AFML and relatively simple to implement. Custom implementation also allows for streaming/incremental updates.

---

### Decision 2: Meta-Model Architecture

**Options Considered**:
1. **Option A: RandomForest (sklearn)**
   - Pros: Fast training, good feature importance, no hyperparameter tuning needed
   - Cons: May underperform on non-linear boundaries

2. **Option B: XGBoost**
   - Pros: Better performance, handles imbalanced data, built-in regularization
   - Cons: Additional dependency, more hyperparameters

3. **Option C: LightGBM**
   - Pros: Fastest training, handles categorical features, good for production
   - Cons: Additional dependency

**Selected**: Option A (RandomForest)

**Rationale**: RandomForest is sufficient for meta-labeling (binary classification: correct/incorrect). sklearn is already a dependency. We can upgrade to XGBoost/LightGBM later if needed.

---

### Decision 3: BOCD Implementation

**Options Considered**:
1. **Option A: ruptures library (offline)**
   - Pros: Well-maintained (1.8k stars), multiple algorithms, easy to use
   - Cons: Designed for offline batch processing, not true online/streaming

2. **Option B: Custom BOCD (Adams & MacKay 2007)**
   - Pros: True online algorithm, processes data point-by-point, probabilistic output
   - Cons: Need to implement from scratch, more complex

**Selected**: Option B (Custom BOCD)

**Rationale**: The spec requires real-time regime change detection for live trading. ruptures is offline-only. Adams & MacKay BOCD is the standard online algorithm with well-documented pseudocode.

---

### Decision 4: Walk-Forward Validation Strategy

**Options Considered**:
1. **Option A: Expanding window**
   - Pros: Uses all historical data, more stable estimates
   - Cons: Older data may not be representative

2. **Option B: Rolling/sliding window**
   - Pros: Adapts to recent market conditions, detects regime changes
   - Cons: Discards older data, may overfit to recent patterns

3. **Option C: Anchored walk-forward**
   - Pros: Balance between expanding and rolling, includes anchor periods
   - Cons: More complex to implement

**Selected**: Option B (Rolling window with configurable size)

**Rationale**: Markets are non-stationary, so recent data is more relevant. Rolling window with 252 trading days (1 year) is standard for meta-model training. Configurable window allows tuning.

---

## Implementation Strategy

### Phase 1: Triple Barrier Labeling (US1)

**Goal**: Implement triple barrier labeling per AFML specification

**Deliverables**:
- [x] `strategies/common/labeling/__init__.py`
- [x] `strategies/common/labeling/triple_barrier.py`
  - TripleBarrierLabel enum (-1, 0, +1)
  - TripleBarrierConfig (pt_multiplier, sl_multiplier, max_holding_bars)
  - get_vertical_barriers() - timeout barrier
  - get_horizontal_barriers() - TP/SL barriers (ATR-based)
  - apply_triple_barrier() - main labeling function
- [x] `tests/test_triple_barrier.py`

**Dependencies**: None (uses numpy only)

**Key Algorithm**:
```python
for each entry_bar:
    entry_price = bar.close
    atr = calculate_atr(bars, period=14)

    tp_barrier = entry_price + (pt_multiplier * atr)
    sl_barrier = entry_price - (sl_multiplier * atr)
    timeout = entry_bar + max_holding_bars

    for future_bar in bars[entry_bar:timeout]:
        if future_bar.high >= tp_barrier:
            label = +1  # Take profit hit
            break
        elif future_bar.low <= sl_barrier:
            label = -1  # Stop loss hit
            break
    else:
        # Timeout reached
        label = sign(final_price - entry_price) or 0
```

---

### Phase 2: Meta-Model Training (US2)

**Goal**: Train secondary model to predict P(primary_model_correct)

**Deliverables**:
- [x] `strategies/common/meta_learning/__init__.py`
- [x] `strategies/common/meta_learning/feature_engineering.py`
  - extract_meta_features() - Volume, volatility, momentum, regime
- [x] `strategies/common/meta_learning/meta_model.py`
  - MetaModelConfig (n_estimators, max_depth, window_size)
  - MetaLabelGenerator - creates meta-labels from primary signals + true labels
  - MetaModel - RandomForest wrapper with predict_proba
- [x] `strategies/common/meta_learning/walk_forward.py`
  - WalkForwardSplitter - rolling window train/test splits
  - walk_forward_train() - trains meta-model with proper splits
- [x] `tests/test_meta_model.py`

**Dependencies**: Phase 1 (triple barrier labels)

**Walk-Forward Protocol**:
```
|----- Train (252 bars) -----|--- Test (63 bars) ---|
                         |--- Train (252 bars) ---|--- Test (63 bars) ---|
                                              |--- Train (252 bars) ---|--- Test ---|
```

---

### Phase 3: BOCD Regime Detection (US3)

**Goal**: Implement Bayesian Online Changepoint Detection

**Deliverables**:
- [x] `strategies/common/regime_detection/bocd.py`
  - BOCDConfig (hazard_rate, mu0, kappa0, alpha0, beta0)
  - BOCD class with:
    - update(observation) - process single observation
    - get_changepoint_probability() - P(run_length = 0)
    - get_run_length_distribution() - full posterior
    - is_changepoint(threshold=0.8) - detection flag
- [x] `tests/test_bocd.py`

**Dependencies**: None (uses numpy, scipy.stats)

**Adams & MacKay Algorithm**:
```python
# Hazard function: P(changepoint) at each step
hazard = 1 / expected_run_length  # e.g., 1/250 for daily data

# Update step (per observation):
1. Calculate predictive probabilities for each run length
2. Growth probabilities = P(no changepoint) * pred_prob
3. Changepoint probability = sum(P(changepoint) * pred_prob)
4. Normalize run length distribution
5. Update sufficient statistics (Student-t conjugate prior)
```

---

### Phase 4: Integrated Bet Sizing (US4)

**Goal**: Unified pipeline combining all factors into final position size

**Deliverables**:
- [x] `strategies/common/position_sizing/integrated_sizing.py`
  - IntegratedSizingConfig (combine all sub-configs)
  - IntegratedSizer class with:
    - calculate(signal, meta_confidence, regime, toxicity) -> size
    - get_factor_breakdown() -> dict of individual factor contributions
- [x] `tests/test_integrated_sizing.py`

**Dependencies**: All previous phases + existing modules (HMM, GMM, VPIN, Giller)

**Formula**:
```python
position_size = (
    signal_direction *          # +1 or -1
    |signal_magnitude|^0.5 *    # Sub-linear (Giller)
    meta_confidence *           # P(correct) from meta-model [0, 1]
    regime_weight *             # From HMM/GMM [0.4, 1.2]
    (1 - toxicity) *            # VPIN penalty [0, 1]
    fractional_kelly            # Safety margin (default 0.5)
)
```

---

## File Structure

```
strategies/
├── common/
│   ├── labeling/                   # NEW: Triple barrier labeling
│   │   ├── __init__.py
│   │   ├── triple_barrier.py       # Core labeling logic
│   │   └── label_utils.py          # Barrier calculation helpers
│   │
│   ├── meta_learning/              # NEW: Meta-model training
│   │   ├── __init__.py
│   │   ├── meta_model.py           # Meta-model class
│   │   ├── feature_engineering.py  # Meta-feature extraction
│   │   └── walk_forward.py         # Walk-forward validation
│   │
│   ├── regime_detection/           # EXTEND: Add BOCD
│   │   ├── __init__.py             # (existing)
│   │   ├── hmm_filter.py           # (existing)
│   │   ├── gmm_filter.py           # (existing)
│   │   ├── bocd.py                 # NEW: Bayesian Online Changepoint
│   │   └── config.py               # (update with BOCDConfig)
│   │
│   ├── position_sizing/            # EXTEND: Add IntegratedSizer
│   │   ├── __init__.py             # (existing)
│   │   ├── giller_sizing.py        # (existing)
│   │   ├── integrated_sizing.py    # NEW: Full pipeline integration
│   │   └── config.py               # (update with IntegratedConfig)
│   │
│   └── orderflow/                  # (existing from Spec 025)
│       ├── vpin.py
│       └── ...

tests/
├── test_triple_barrier.py          # NEW
├── test_meta_model.py              # NEW
├── test_bocd.py                    # NEW
└── test_integrated_sizing.py       # NEW
```

## API Design

### Public Interface

```python
# Triple Barrier Labeling
from strategies.common.labeling import TripleBarrierLabeler, TripleBarrierConfig

labeler = TripleBarrierLabeler(TripleBarrierConfig(
    pt_multiplier=2.0,    # Take profit = 2 * ATR
    sl_multiplier=1.0,    # Stop loss = 1 * ATR
    max_holding_bars=10,  # Maximum 10 bars holding
))
labels = labeler.apply(bars, atr_values)

# Meta-Model
from strategies.common.meta_learning import MetaModel, MetaModelConfig

meta_model = MetaModel(MetaModelConfig(
    n_estimators=100,
    max_depth=5,
    window_size=252,
))
meta_model.fit(features, primary_signals, true_labels)
confidence = meta_model.predict_proba(features)

# BOCD
from strategies.common.regime_detection import BOCD, BOCDConfig

bocd = BOCD(BOCDConfig(
    hazard_rate=1/250,  # Expected run length = 250 bars
))
for returns in returns_stream:
    bocd.update(returns)
    if bocd.is_changepoint(threshold=0.8):
        trigger_regime_refit()

# Integrated Sizing
from strategies.common.position_sizing import IntegratedSizer, IntegratedSizingConfig

sizer = IntegratedSizer(IntegratedSizingConfig(
    giller_exponent=0.5,
    fractional_kelly=0.5,
))
position_size = sizer.calculate(
    signal=signal,
    meta_confidence=meta_confidence,
    regime_weight=regime_weight,
    toxicity=vpin_toxicity,
)
```

### Configuration

```python
from pydantic import BaseModel

class TripleBarrierConfig(BaseModel):
    pt_multiplier: float = 2.0    # Take profit multiplier (ATR)
    sl_multiplier: float = 1.0    # Stop loss multiplier (ATR)
    max_holding_bars: int = 10    # Vertical barrier
    atr_period: int = 14          # ATR calculation period

class MetaModelConfig(BaseModel):
    n_estimators: int = 100       # RandomForest trees
    max_depth: int = 5            # Tree depth limit
    window_size: int = 252        # Training window (bars)
    test_size: int = 63           # Test window (bars)

class BOCDConfig(BaseModel):
    hazard_rate: float = 1/250    # P(changepoint) per step
    mu0: float = 0.0              # Prior mean
    kappa0: float = 1.0           # Prior precision weight
    alpha0: float = 1.0           # Prior shape
    beta0: float = 1.0            # Prior scale

class IntegratedSizingConfig(BaseModel):
    giller_exponent: float = 0.5          # Sub-linear exponent
    fractional_kelly: float = 0.5         # Kelly fraction
    default_regime_weight: float = 0.8    # If regime missing
    default_toxicity: float = 0.0         # If VPIN missing
    default_meta_confidence: float = 0.5  # If meta-model missing
```

## Testing Strategy

### Unit Tests
- [x] Test triple barrier label generation
- [x] Test meta-label creation
- [x] Test meta-model training/prediction
- [x] Test BOCD update mechanics
- [x] Test integrated sizing formula

### Integration Tests
- [x] Test full pipeline with BacktestNode
- [x] Test meta-model with walk-forward splits
- [x] Test BOCD with known regime changes

### Performance Tests
- [x] Triple barrier: <60s for 1M bars
- [x] Meta-model: <5ms inference
- [x] BOCD: <5ms per update
- [x] Integrated sizing: <20ms end-to-end

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Look-ahead bias in labeling | High | Medium | Strict chronological splits, no peeking |
| Meta-model overfitting | High | Medium | Walk-forward validation, limited depth |
| BOCD false positives | Medium | Medium | Threshold tuning, confirmation delay |
| Integration complexity | Medium | Low | Modular design, clear interfaces |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.222.0 (nightly)
- numpy >= 1.24.0
- scipy >= 1.10.0 (for BOCD Student-t)
- scikit-learn >= 1.2.0 (for RandomForest)
- pydantic >= 2.0.0 (for config validation)

### Internal Dependencies (Already Implemented)
- `strategies/common/regime_detection/hmm_filter.py` (Spec 024)
- `strategies/common/regime_detection/gmm_filter.py` (Spec 024)
- `strategies/common/position_sizing/giller_sizing.py` (Spec 024)
- `strategies/common/orderflow/vpin.py` (Spec 025)

## Acceptance Criteria

- [x] All unit tests passing (coverage > 80%)
- [x] Triple barrier processes 1M bars in <60 seconds
- [x] Meta-model achieves AUC > 0.6 on validation data
- [x] BOCD detects regime changes within 10 bars
- [x] Integrated sizing latency <20ms end-to-end
- [x] Documentation updated (quickstart.md)
- [x] All code follows PEP 8, type hints, docstrings

## Constitution Check

### Verified Compliance

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | Each component has clean API, hidden implementation |
| KISS & YAGNI | ✅ | Uses existing libs (sklearn), no over-engineering |
| Native First | ✅ | Uses NautilusTrader native indicators for features |
| No df.iterrows() | ✅ | Vectorized operations for labeling |
| TDD Discipline | ✅ | Tests written first per user story |
| Type Hints | ✅ | All public functions typed |
| Coverage > 80% | ✅ | Required for all new modules |
