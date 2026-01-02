# Feature Specification: ML Regime Detection Foundation

**Feature Branch**: `024-ml-regime-foundation`
**Created**: 2026-01-02
**Status**: Draft
**Input**: Implementation priority matrix - Phase 1 Foundation

## User Scenarios & Testing *(mandatory)*

### User Story 1 - HMM Regime Detection (Priority: P1)

As a trader, I want to detect market regimes (trending, ranging, volatile) using Hidden Markov Models so that I can adjust my strategy parameters dynamically.

**Why this priority**: Foundation for all regime-conditioned trading. Highest ROI item from research.

**Independent Test**: Can be tested with historical BTCUSDT data to verify regime transitions correlate with market behavior.

**Acceptance Scenarios**:

1. **Given** historical bar data, **When** HMM is fitted, **Then** it identifies 2-4 distinct regimes
2. **Given** new bar data, **When** regime is predicted, **Then** inference completes in <10ms
3. **Given** regime change detected, **When** strategy queries current regime, **Then** correct regime label is returned

---

### User Story 2 - GMM Volatility Clustering (Priority: P1)

As a trader, I want to cluster volatility states using Gaussian Mixture Models so that I can identify low/medium/high volatility periods.

**Why this priority**: Complements HMM for multi-factor regime detection. Easy to implement with sklearn.

**Independent Test**: Can verify volatility clusters match historical ATR distribution.

**Acceptance Scenarios**:

1. **Given** ATR/returns data, **When** GMM is fitted, **Then** it identifies 3 volatility clusters
2. **Given** current volatility, **When** cluster is predicted, **Then** returns cluster label (low/medium/high)
3. **Given** volatility spike, **When** GMM predicts, **Then** correctly identifies high-volatility state

---

### User Story 3 - Sub-linear Position Sizing (Giller) (Priority: P1)

As a trader, I want position sizing that uses sub-linear scaling (signal^0.5) so that I avoid over-betting on strong signals.

**Why this priority**: Immediate risk management improvement. Based on Graham Giller research.

**Independent Test**: Can verify position sizes follow sqrt scaling vs linear.

**Acceptance Scenarios**:

1. **Given** signal magnitude 4.0, **When** Giller sizing applied, **Then** size = 2.0 (sqrt scaling)
2. **Given** regime = high_volatility, **When** sizing calculated, **Then** regime_weight reduces size
3. **Given** VPIN toxicity > 0.7, **When** sizing calculated, **Then** toxicity penalty applied

---

### User Story 4 - FRED M2 Macro Filter (Priority: P2) ✅ ALREADY IMPLEMENTED

> **SKIP**: Già implementato separatamente. Integrazione opzionale in RegimeManager.

As a trader, I want to incorporate M2 money supply growth as a macro regime indicator so that I can align with expansionary/contractionary periods.

---

### User Story 5 - Fear & Greed Index Filter (Priority: P2) ✅ ALREADY IMPLEMENTED

> **SKIP**: Già implementato separatamente. Integrazione opzionale in RegimeManager.

As a trader, I want to use the Fear & Greed Index as a sentiment filter so that I can identify extreme market conditions.

---

### Edge Cases

- What happens when HMM fitted with insufficient data (<100 bars)?
- How does system handle FRED API rate limits?
- What if Fear & Greed API returns invalid JSON?
- How to handle regime transition during open position?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fit HMM with configurable number of states (2-5)
- **FR-002**: System MUST predict regime with latency <10ms per bar
- **FR-003**: System MUST cluster volatility into 3 states using GMM
- **FR-004**: System MUST calculate Giller sub-linear position sizes
- **FR-005**: ~~System MUST fetch and cache FRED M2 data~~ [SKIP - già implementato]
- **FR-006**: ~~System MUST fetch Fear & Greed index~~ [SKIP - già implementato]
- **FR-007**: System MUST provide unified RegimeFilter interface for strategies
- **FR-008**: System MUST log regime transitions for analysis

### Key Entities

- **RegimeState**: Enum of detected regimes (trending_up, trending_down, ranging, volatile)
- **VolatilityCluster**: Low, Medium, High volatility classification
- **MacroRegime**: Expansionary, Neutral, Contractionary based on M2
- **SentimentState**: Extreme Fear, Fear, Neutral, Greed, Extreme Greed

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: HMM regime detection completes fitting in <30 seconds on 1 year of daily data
- **SC-002**: Regime prediction latency <10ms (suitable for live trading)
- **SC-003**: GMM volatility clusters show >0.7 correlation with realized volatility
- **SC-004**: Giller sizing reduces max drawdown by >15% vs linear sizing in backtest
- **SC-005**: ~~FRED/Fear&Greed APIs cached~~ [SKIP - già implementato]
- **SC-006**: All components have >80% test coverage

## Technical Notes

### Dependencies

```bash
uv pip install hmmlearn scikit-learn
```

### File Structure

```
strategies/common/regime_detection/
├── __init__.py
├── types.py               # RegimeState, VolatilityCluster enums
├── config.py              # RegimeConfig Pydantic model
├── hmm_filter.py          # HMM regime detection
├── gmm_filter.py          # GMM volatility clustering
└── regime_manager.py      # Unified interface

strategies/common/position_sizing/
├── __init__.py
├── config.py              # GillerConfig Pydantic model
└── giller_sizing.py       # Sub-linear sizing

strategies/common/utils/
├── __init__.py
└── data_transforms.py     # Returns, volatility calculations

tests/
├── test_hmm_filter.py
├── test_gmm_filter.py
├── test_giller_sizing.py
└── test_regime_manager.py
```

### References

- `docs/research/trading_ml_research_final_2026.md`
- `docs/research/market_regime_detection_sota_2025.md`
- `docs/research/implementation_priority_matrix_2026.md`
