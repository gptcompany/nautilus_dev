# Implementation Plan: ML Regime Detection Foundation

**Feature Branch**: `024-ml-regime-foundation`
**Created**: 2026-01-02
**Status**: Draft
**Spec Reference**: `specs/024-ml-regime-foundation/spec.md`

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NautilusTrader Strategy                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ RegimeFilter │───▶│ PositionSizer│───▶│ Order Submission     │  │
│  └──────┬───────┘    └──────┬───────┘    └──────────────────────┘  │
│         │                   │                                        │
│         ▼                   ▼                                        │
│  ┌──────────────────────────────────────┐                           │
│  │         RegimeManager                 │                           │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ │                           │
│  │  │   HMM   │ │   GMM   │ │  Macro  │ │                           │
│  │  │ Filter  │ │ Filter  │ │ Filter  │ │                           │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ │                           │
│  └───────┼───────────┼───────────┼──────┘                           │
│          │           │           │                                   │
│          ▼           ▼           ▼                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌───────────────────────┐          │
│  │ Bar Data    │ │ ATR/Returns │ │ External APIs         │          │
│  │ (OHLCV)     │ │ (computed)  │ │ (FRED, Alternative.me)│          │
│  └─────────────┘ └─────────────┘ └───────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
strategies/common/
├── regime_detection/
│   ├── __init__.py           # Exports RegimeManager, RegimeState
│   ├── hmm_filter.py         # HMMRegimeFilter class
│   ├── gmm_filter.py         # GMMVolatilityFilter class
│   ├── macro_filter.py       # MacroRegimeFilter (FRED + Fear&Greed)
│   └── regime_manager.py     # Unified RegimeManager facade
│
├── position_sizing/
│   ├── __init__.py           # Exports GillerSizer
│   └── giller_sizing.py      # Sub-linear position sizing
│
└── utils/
    ├── api_cache.py          # TTL cache for external APIs
    └── data_transforms.py    # Returns, volatility calculations
```

## Technical Decisions

### Decision 1: HMM Library

**Options Considered**:
1. **hmmlearn**: Mature, well-documented, sklearn-compatible
   - Pros: Production-ready, good documentation, CPU-only (simple)
   - Cons: No GPU acceleration
2. **pomegranate**: Modern, faster, GPU support
   - Pros: Faster training, more flexible
   - Cons: Less stable API, fewer examples

**Selected**: Option 1 - hmmlearn

**Rationale**: Stability and documentation over speed. HMM fitting is infrequent (daily/weekly), so GPU acceleration not needed.

---

### Decision 2: Volatility Clustering

**Options Considered**:
1. **GMM (sklearn)**: Probabilistic clustering, soft assignments
   - Pros: Returns probabilities, handles overlapping clusters
   - Cons: Requires choosing n_components
2. **K-Means**: Hard clustering, simpler
   - Pros: Faster, deterministic
   - Cons: No probability output

**Selected**: Option 1 - GMM

**Rationale**: Probability output useful for position sizing (confidence weighting).

---

### Decision 3: API Caching Strategy

**Options Considered**:
1. **In-memory with TTL**: Simple dict with timestamp
   - Pros: Simple, no dependencies
   - Cons: Lost on restart
2. **File-based cache**: JSON/pickle to disk
   - Pros: Persists across restarts
   - Cons: Slightly more complex
3. **Redis**: External cache
   - Pros: Shared across processes
   - Cons: Overkill for 2 APIs

**Selected**: Option 2 - File-based cache

**Rationale**: Persists across restarts, no external dependencies. Use JSON for transparency.

---

### Decision 4: Regime State Representation

**Options Considered**:
1. **Enum**: Fixed states (TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE)
   - Pros: Type-safe, IDE autocomplete
   - Cons: Rigid
2. **String labels**: Flexible string names
   - Pros: Flexible
   - Cons: No type safety, typo-prone

**Selected**: Option 1 - Enum

**Rationale**: Type safety prevents bugs. Constitution mandates type hints.

---

## Implementation Strategy

### Phase 1: Core Filters (Day 1-2)

**Goal**: Implement HMM and GMM filters with unit tests

**Deliverables**:
- [x] `hmm_filter.py` - HMM regime detection
- [x] `gmm_filter.py` - GMM volatility clustering
- [x] `data_transforms.py` - Returns/volatility helpers
- [x] Unit tests for both filters

**Dependencies**: None

**Key Implementation Notes**:
```python
# HMM expects 2D array: [[feature1, feature2], ...]
# Use returns + volatility as features
features = np.column_stack([returns, volatility])
hmm.fit(features)
```

---

### Phase 2: Position Sizing (Day 2)

**Goal**: Implement Giller sub-linear sizing

**Deliverables**:
- [ ] `giller_sizing.py` - Position sizing calculator
- [ ] Integration with regime filters
- [ ] Unit tests

**Dependencies**: Phase 1

**Key Implementation Notes**:
```python
def giller_size(signal: float, regime_weight: float = 1.0) -> float:
    """Sub-linear sizing: size = signal^0.5 * regime_weight"""
    return np.sign(signal) * (abs(signal) ** 0.5) * regime_weight
```

---

### Phase 3: Integration & Manager (Day 3)

**Goal**: Unified RegimeManager facade

**Deliverables**:
- [ ] `regime_manager.py` - Unified interface
- [ ] Integration tests with BacktestNode
- [ ] Documentation

**Dependencies**: Phase 1, 2

---

## File Structure

```
strategies/common/
├── regime_detection/
│   ├── __init__.py
│   ├── hmm_filter.py
│   ├── gmm_filter.py
│   └── regime_manager.py
├── position_sizing/
│   ├── __init__.py
│   └── giller_sizing.py
└── utils/
    ├── __init__.py
    └── data_transforms.py

tests/
├── test_hmm_filter.py
├── test_gmm_filter.py
├── test_giller_sizing.py
└── test_regime_manager.py
```

**Note**: FRED M2 e Fear&Greed già implementati separatamente - integrazione opzionale.

## API Design

### Public Interface

```python
from strategies.common.regime_detection import RegimeManager, RegimeState
from strategies.common.position_sizing import GillerSizer

class MyStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.regime_manager = RegimeManager(
            hmm_states=3,
            gmm_clusters=3,
            use_macro=True
        )
        self.sizer = GillerSizer(base_size=1.0)

    def on_bar(self, bar: Bar) -> None:
        # Update regime detection
        regime = self.regime_manager.update(bar)

        # Get position size
        signal = self.calculate_signal(bar)
        size = self.sizer.calculate(
            signal=signal,
            regime_weight=regime.weight,
            volatility_cluster=regime.volatility
        )
```

### Configuration

```python
from pydantic import BaseModel

class RegimeConfig(BaseModel):
    hmm_states: int = 3
    gmm_clusters: int = 3
    hmm_lookback: int = 252  # 1 year of daily bars
    use_fred: bool = True
    use_fear_greed: bool = True
    fred_api_key: str | None = None

class GillerConfig(BaseModel):
    base_size: float = 1.0
    exponent: float = 0.5  # Sub-linear exponent
    max_size: float = 5.0
    min_size: float = 0.1
```

## Testing Strategy

### Unit Tests
- [ ] Test HMM fitting with synthetic data
- [ ] Test GMM clustering with known distributions
- [ ] Test Giller sizing edge cases (zero, negative, extreme)
- [ ] Test data transforms (returns, volatility)

### Integration Tests
- [ ] Test RegimeManager with real BTCUSDT data
- [ ] Test full pipeline: bars → regime → size
- [ ] Test with BacktestNode

### Performance Tests
- [ ] HMM fitting time < 30s on 1 year data
- [ ] Regime prediction < 10ms per bar
- [ ] Memory usage < 500MB

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| HMM doesn't converge | High | Low | Use multiple random inits, check convergence |
| Regime labels arbitrary | Medium | High | Validate against historical volatility |
| Look-ahead bias in fitting | High | Medium | Use walk-forward validation |
| Insufficient training data | Medium | Low | Require min 100 bars for fitting |

## Dependencies

### External Dependencies
```bash
uv pip install hmmlearn scikit-learn
```

### Internal Dependencies
- NautilusTrader >= 1.220.0 (nightly)
- `strategies/common/utils/` (to be created)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | Clean RegimeManager interface |
| KISS & YAGNI | ✅ | Start with 2-3 states, expand if needed |
| Native First | ✅ | Using native ATR for volatility |
| No df.iterrows() | ✅ | Vectorized numpy operations |
| TDD Discipline | ⏳ | Write tests first |
| Type hints | ⏳ | All public functions typed |
| Coverage > 80% | ⏳ | Target for each module |

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] HMM fitting < 30s on 1 year data
- [ ] Regime prediction < 10ms per bar
- [ ] Giller sizing correctly applies sub-linear scaling
- [ ] Documentation in docstrings
- [ ] Code review approved

## Next Steps

1. Run `/speckit.tasks` to generate granular task list
2. Start TDD cycle with `test_hmm_filter.py`
3. Use `test-runner` agent for test execution
