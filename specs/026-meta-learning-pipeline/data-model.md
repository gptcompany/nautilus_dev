# Data Model: Meta-Learning Pipeline (Spec 026)

**Date**: 2026-01-03
**Status**: Complete

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Core Entities                              │
└─────────────────────────────────────────────────────────────────────┘

┌───────────────────┐     generates     ┌───────────────────┐
│  TripleBarrier    │ ─────────────────>│ TripleBarrierLabel│
│    Labeler        │                   │    Enum           │
└───────────────────┘                   └───────────────────┘
        │                                        │
        │ uses                                   │ used by
        ▼                                        ▼
┌───────────────────┐                   ┌───────────────────┐
│ TripleBarrier     │                   │  MetaLabel        │
│    Config         │                   │  Generator        │
└───────────────────┘                   └───────────────────┘
                                                 │
                                                 │ produces
                                                 ▼
                                        ┌───────────────────┐
                                        │    MetaModel      │
                                        │ (RandomForest)    │
                                        └───────────────────┘
                                                 │
                                                 │ predicts
                                                 ▼
                                        ┌───────────────────┐
                                        │  MetaConfidence   │
                                        │   [0.0, 1.0]      │
                                        └───────────────────┘

┌───────────────────┐                   ┌───────────────────┐
│       BOCD        │ ─────────────────>│   Changepoint     │
│   (Detector)      │     detects       │     Event         │
└───────────────────┘                   └───────────────────┘
        │
        │ uses
        ▼
┌───────────────────┐
│    BOCDConfig     │
└───────────────────┘


┌───────────────────┐                   ┌───────────────────┐
│ IntegratedSizer   │ ─────────────────>│  IntegratedSize   │
│                   │    calculates     │    Result         │
└───────────────────┘                   └───────────────────┘
        │
        │ combines
        ▼
┌─────────────────────────────────────────────────────────────┐
│  Existing Components (Spec 024/025)                          │
│  - GillerSizer                                               │
│  - HMMRegimeFilter                                           │
│  - GMMVolatilityFilter                                       │
│  - VPINIndicator                                             │
└─────────────────────────────────────────────────────────────┘
```

## Entity Definitions

### 1. TripleBarrierLabel

**Description**: Enum representing the outcome of a trade based on which barrier was hit first.

**Values**:
| Value | Name | Description |
|-------|------|-------------|
| +1 | TAKE_PROFIT | Price reached take-profit barrier first |
| -1 | STOP_LOSS | Price reached stop-loss barrier first |
| 0 | TIMEOUT | Holding period expired without hitting either barrier |

**Usage**:
```python
class TripleBarrierLabel(Enum):
    STOP_LOSS = -1
    TIMEOUT = 0
    TAKE_PROFIT = 1
```

---

### 2. TripleBarrierConfig

**Description**: Configuration for triple barrier labeling.

**Fields**:
| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| pt_multiplier | float | 2.0 | >0 | Take-profit distance as multiple of ATR |
| sl_multiplier | float | 1.0 | >0 | Stop-loss distance as multiple of ATR |
| max_holding_bars | int | 10 | >0 | Maximum bars before timeout |
| atr_period | int | 14 | >0 | Period for ATR calculation |

**Validation Rules**:
- pt_multiplier > 0
- sl_multiplier > 0
- pt_multiplier >= sl_multiplier (for positive expectancy)
- max_holding_bars >= 1
- atr_period >= 2

**Example**:
```python
config = TripleBarrierConfig(
    pt_multiplier=2.0,
    sl_multiplier=1.0,
    max_holding_bars=10,
    atr_period=14,
)
```

---

### 3. BarrierEvent

**Description**: Represents a single barrier check event during label generation.

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| entry_idx | int | Index of entry bar |
| entry_price | float | Price at entry |
| entry_time | datetime | Timestamp of entry |
| tp_barrier | float | Take-profit price level |
| sl_barrier | float | Stop-loss price level |
| timeout_idx | int | Index of timeout bar |
| exit_idx | int | Index of actual exit |
| exit_price | float | Price at exit |
| label | TripleBarrierLabel | Resulting label |

---

### 4. MetaModelConfig

**Description**: Configuration for meta-model training.

**Fields**:
| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| n_estimators | int | 100 | 10-1000 | Number of RandomForest trees |
| max_depth | int | 5 | 1-20 | Maximum tree depth |
| window_size | int | 252 | 50-1000 | Training window in bars |
| test_size | int | 63 | 10-252 | Test window in bars |
| step_size | int | 21 | 1-63 | Step size for walk-forward |
| embargo_size | int | 5 | 0-20 | Gap between train/test |
| random_state | int | 42 | - | Random seed for reproducibility |

**Validation Rules**:
- window_size > test_size
- step_size <= test_size
- embargo_size < test_size

---

### 5. MetaLabel

**Description**: A single meta-label sample for training.

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| idx | int | Bar index |
| primary_signal | int | Primary model signal (+1, -1, 0) |
| true_label | TripleBarrierLabel | Actual outcome from triple barrier |
| meta_label | int | 1 if primary_signal == true_label, else 0 |
| features | NDArray | Feature vector for meta-model |

**State Transitions**:
```
Primary Signal → Triple Barrier Outcome → Meta-Label
     +1        →         +1              →    1 (correct)
     +1        →         -1              →    0 (incorrect)
     +1        →          0              →    0 (incorrect)
     -1        →         -1              →    1 (correct)
     ...
```

---

### 6. MetaConfidence

**Description**: Output of meta-model prediction.

**Type**: float [0.0, 1.0]

**Interpretation**:
| Range | Interpretation | Action |
|-------|----------------|--------|
| 0.0 - 0.3 | Low confidence | Skip or reduce position |
| 0.3 - 0.7 | Moderate confidence | Normal position sizing |
| 0.7 - 1.0 | High confidence | Full position sizing |

---

### 7. BOCDConfig

**Description**: Configuration for Bayesian Online Changepoint Detection.

**Fields**:
| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| hazard_rate | float | 0.004 (1/250) | 0 < x < 1 | P(changepoint) per step |
| mu0 | float | 0.0 | - | Prior mean for Gaussian |
| kappa0 | float | 1.0 | > 0 | Prior precision weight |
| alpha0 | float | 1.0 | > 0 | Prior shape (Student-t) |
| beta0 | float | 1.0 | > 0 | Prior scale (Student-t) |
| max_run_length | int | 500 | > 0 | Maximum tracked run length |

**Validation Rules**:
- 0 < hazard_rate < 1
- kappa0, alpha0, beta0 > 0
- max_run_length >= 100

---

### 8. Changepoint

**Description**: Detected regime change event.

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| idx | int | Bar index of detected changepoint |
| timestamp | datetime | Time of detection |
| probability | float | Changepoint probability [0, 1] |
| run_length_before | int | Estimated run length before change |
| trigger_refit | bool | Whether to trigger model refitting |

**State Transitions**:
```
Observations → BOCD Update → Run Length Distribution → Changepoint Detection
                                                           │
                            ┌──────────────────────────────┴──────────────────────────┐
                            ▼                                                          ▼
                   P(changepoint) > threshold                             P(changepoint) < threshold
                            │                                                          │
                            ▼                                                          ▼
                   Emit Changepoint Event                                    Continue monitoring
                   Trigger regime refit
```

---

### 9. IntegratedSizingConfig

**Description**: Configuration for unified position sizing.

**Fields**:
| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| giller_exponent | float | 0.5 | 0 < x <= 1 | Sub-linear scaling exponent |
| fractional_kelly | float | 0.5 | 0 < x <= 1 | Kelly fraction |
| min_size | float | 0.01 | >= 0 | Minimum position size |
| max_size | float | 1.0 | > min_size | Maximum position size |
| default_meta_confidence | float | 0.5 | [0, 1] | Default if meta-model unavailable |
| default_regime_weight | float | 0.8 | [0, 1.5] | Default if regime unavailable |
| default_toxicity | float | 0.0 | [0, 1] | Default if VPIN unavailable |

---

### 10. IntegratedSize

**Description**: Result of integrated position sizing calculation.

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| final_size | float | Final calculated position size |
| direction | int | Signal direction (+1 or -1) |
| signal_contribution | float | Contribution from signal magnitude |
| meta_contribution | float | Contribution from meta-confidence |
| regime_contribution | float | Contribution from regime weight |
| toxicity_contribution | float | Contribution from VPIN toxicity |
| kelly_fraction | float | Applied Kelly fraction |
| factors | dict | Breakdown of all factor values |

---

## Relationships

### Primary Relationships

1. **TripleBarrierLabeler** → generates → **TripleBarrierLabel**
   - One labeler produces many labels (one per bar with signal)

2. **MetaLabelGenerator** → uses → **TripleBarrierLabel**
   - Combines primary signals with true labels to create meta-labels

3. **MetaModel** → trained on → **MetaLabel**
   - RandomForest trained on meta-label features

4. **MetaModel** → predicts → **MetaConfidence**
   - Output is probability [0, 1]

5. **BOCD** → detects → **Changepoint**
   - One BOCD instance monitors one time series

6. **IntegratedSizer** → combines → **All Components**
   - Aggregates signal, meta-confidence, regime, toxicity

### Dependency Graph

```
TripleBarrierConfig ──────────┐
                              ▼
                    TripleBarrierLabeler
                              │
                              ▼
                    TripleBarrierLabel
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            MetaLabelGenerator    (Used for backtesting)
                    │
                    ▼
              MetaLabel
                    │
                    ▼
              MetaModel ──────────────> MetaConfidence
                                              │
                                              ▼
BOCDConfig ──> BOCD ──> Changepoint ──> IntegratedSizer
                                              │
                                              ▼
                                       IntegratedSize
```

## Data Flow

### Training Phase

```
Historical Bars
      │
      ├──> ATR Calculation ──> Barrier Levels
      │
      ├──> Primary Signal Generation (EMA crossover, etc.)
      │
      ├──> Triple Barrier Labeling ──> True Labels
      │
      ├──> Meta-Label Creation (primary_correct = true_label matches signal)
      │
      └──> Walk-Forward Training ──> Trained MetaModel
```

### Inference Phase (Live Trading)

```
New Bar Arrives
      │
      ├──> Update BOCD ──> Check Changepoint ──> Trigger Refit?
      │
      ├──> Update VPIN ──> Get Toxicity [0, 1]
      │
      ├──> Update HMM/GMM ──> Get Regime Weight [0.4, 1.2]
      │
      ├──> Generate Primary Signal ──> Direction (+1/-1)
      │
      ├──> Extract Features ──> MetaModel.predict ──> Confidence [0, 1]
      │
      └──> IntegratedSizer.calculate() ──> Final Position Size
```

## Validation Rules Summary

| Entity | Rule | Error |
|--------|------|-------|
| TripleBarrierConfig | pt_multiplier > sl_multiplier | ValueError |
| MetaModelConfig | window_size > test_size | ValueError |
| BOCDConfig | 0 < hazard_rate < 1 | ValueError |
| IntegratedSizingConfig | max_size > min_size | ValueError |
| MetaConfidence | 0 <= value <= 1 | AssertionError |
| IntegratedSize | -max_size <= final_size <= max_size | Clamped |
