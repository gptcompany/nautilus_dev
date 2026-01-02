# Feature Specification: Meta-Learning Pipeline

**Feature Branch**: `026-meta-learning-pipeline`
**Created**: 2026-01-02
**Status**: Draft
**Input**: Implementation priority matrix - Phase 3 & 4 (Meta-Learning + Production)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Triple Barrier Labeling (Priority: P1)

As a quant researcher, I want to label trades using the triple barrier method so that I can train ML models with proper profit-taking and stop-loss outcomes.

**Why this priority**: Foundation for meta-labeling. From "Advances in Financial Machine Learning" (AFML).

**Independent Test**: Can verify labels match expected outcomes on historical trades.

**Acceptance Scenarios**:

1. **Given** entry price and barriers (TP, SL, max_holding), **When** price path evaluated, **Then** returns label (-1, 0, +1)
2. **Given** price hits take-profit first, **When** labeled, **Then** returns +1
3. **Given** price hits stop-loss first, **When** labeled, **Then** returns -1
4. **Given** max holding period reached, **When** labeled, **Then** returns 0 or sign of return

---

### User Story 2 - Meta-Model Training (Priority: P1)

As a trader, I want a meta-model that predicts P(primary_model_correct) so that I can size bets based on confidence.

**Why this priority**: Enables dynamic bet sizing based on predicted accuracy.

**Independent Test**: Can verify meta-model AUC > 0.6 on validation set.

**Acceptance Scenarios**:

1. **Given** primary model signals + features, **When** meta-model trained, **Then** predicts probability [0, 1]
2. **Given** meta_confidence > 0.7, **When** bet sized, **Then** uses full position
3. **Given** meta_confidence < 0.3, **When** bet sized, **Then** reduces position or skips
4. **Given** new data, **When** meta-model predicts, **Then** latency <5ms

---

### User Story 3 - BOCD Regime Change Detection (Priority: P2)

As a trader, I want Bayesian Online Changepoint Detection so that I can detect regime changes in real-time without refitting the entire model.

**Why this priority**: Enables live regime switching. Critical for production.

**Independent Test**: Can verify BOCD detects known regime changes in historical data.

**Acceptance Scenarios**:

1. **Given** streaming returns, **When** BOCD runs, **Then** outputs changepoint probability
2. **Given** changepoint_prob > 0.8, **When** regime queried, **Then** triggers regime refit
3. **Given** stable regime, **When** BOCD monitors, **Then** changepoint_prob stays low
4. **Given** volatility spike, **When** BOCD evaluates, **Then** detects potential changepoint

---

### User Story 4 - Integrated Bet Sizing Pipeline (Priority: P1)

As a trader, I want a unified pipeline that combines all factors (regime, VPIN, meta-confidence, Giller) into final position size.

**Why this priority**: Combines all previous work into actionable output.

**Independent Test**: Can verify position sizes reflect all input factors correctly.

**Acceptance Scenarios**:

1. **Given** all factors computed, **When** final size calculated, **Then** combines multiplicatively
2. **Given** high toxicity + low confidence, **When** sized, **Then** position near zero
3. **Given** favorable regime + high confidence, **When** sized, **Then** position near max
4. **Given** any factor missing, **When** sized, **Then** uses safe default (0.5)

---

### Edge Cases

- What happens when meta-model has insufficient training data?
- How to handle BOCD with non-stationary mean AND variance?
- What if triple barrier never hits any barrier (extreme case)?
- How to retrain meta-model without look-ahead bias?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement triple barrier labeling per AFML spec
- **FR-002**: System MUST support configurable barrier multipliers (ATR-based)
- **FR-003**: System MUST train meta-model using walk-forward validation
- **FR-004**: System MUST prevent look-ahead bias in all labeling/training
- **FR-005**: System MUST implement BOCD with Gaussian likelihood
- **FR-006**: System MUST trigger regime refit when changepoint detected
- **FR-007**: System MUST provide integrated sizing pipeline
- **FR-008**: System MUST log all factor contributions for debugging

### Key Entities

- **TripleBarrierLabel**: Enum (-1=SL hit, 0=timeout, +1=TP hit)
- **MetaConfidence**: Probability that primary model is correct [0, 1]
- **Changepoint**: Detected regime boundary with probability
- **IntegratedSize**: Final position size with factor breakdown

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Triple barrier labeling processes 1M bars in <60 seconds
- **SC-002**: Meta-model achieves AUC > 0.6 on out-of-sample data
- **SC-003**: BOCD detects regime changes within 10 bars of actual change
- **SC-004**: Integrated pipeline latency <20ms end-to-end
- **SC-005**: Backtest with full pipeline shows Sharpe > 1.5
- **SC-006**: All components have >80% test coverage

## Technical Notes

### Dependencies

```bash
uv pip install mlfinlab ruptures  # or custom BOCD
```

### File Structure

```
strategies/common/labeling/
├── __init__.py
├── triple_barrier.py      # Triple barrier labeling
└── label_utils.py         # Barrier calculation helpers

strategies/common/meta_learning/
├── __init__.py
├── meta_model.py          # Meta-model training/inference
├── feature_engineering.py # Meta-features extraction
└── walk_forward.py        # Walk-forward validation

strategies/common/regime_detection/
├── bocd.py                # Bayesian Online Changepoint Detection
└── (existing hmm_filter.py, gmm_filter.py)

strategies/common/position_sizing/
├── integrated_sizing.py   # Full pipeline integration
└── (existing giller_sizing.py)

tests/
├── test_triple_barrier.py
├── test_meta_model.py
├── test_bocd.py
└── test_integrated_sizing.py
```

### Integrated Sizing Formula

```python
def integrated_position_size(
    signal_direction: int,      # +1 or -1
    signal_magnitude: float,    # Raw signal strength
    meta_confidence: float,     # P(correct) from meta-model
    regime_weight: float,       # From HMM/GMM
    vpin_toxicity: float,       # From VPIN
    fractional_kelly: float = 0.5
) -> float:
    """
    Full integrated sizing per Giller + meta-learning.
    """
    return (
        signal_direction *
        (abs(signal_magnitude) ** 0.5) *  # Sub-linear (Giller)
        meta_confidence *                  # Meta-model confidence
        regime_weight *                    # Regime adjustment
        (1 - vpin_toxicity) *             # Toxicity penalty
        fractional_kelly                   # Kelly fraction
    )
```

### References

- `docs/research/trading_ml_research_final_2026.md`
- `docs/research/implementation_priority_matrix_2026.md`
- López de Prado, M. (2018). "Advances in Financial Machine Learning"
- Adams, R. P., & MacKay, D. J. (2007). "Bayesian Online Changepoint Detection"
