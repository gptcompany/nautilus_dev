# Implementation Plan: Orderflow Indicators

**Feature Branch**: `025-orderflow-indicators`
**Created**: 2026-01-02
**Status**: Ready for Implementation
**Spec Reference**: `specs/025-orderflow-indicators/spec.md`

## Architecture Overview

This feature implements two orderflow indicators for detecting toxic flow and predicting short-term price movements:

1. **VPIN (Volume-Synchronized Probability of Informed Trading)** - Detects toxic orderflow
2. **Hawkes OFI (Order Flow Imbalance)** - Predicts orderflow clustering and momentum

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                      NautilusTrader Strategy                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────┐    │
│  │ Bar/Tick    │───►│ OrderflowManager │───►│ GillerSizer  │    │
│  │ Data        │    │                  │    │ (Spec 024)   │    │
│  └─────────────┘    │ ┌─────────────┐  │    └──────────────┘    │
│                     │ │ VPIN        │  │           │            │
│                     │ │ (toxicity)  │──┼───────────┘            │
│                     │ └─────────────┘  │                        │
│                     │ ┌─────────────┐  │                        │
│                     │ │ Hawkes OFI  │  │                        │
│                     │ │ (momentum)  │  │                        │
│                     │ └─────────────┘  │                        │
│                     └─────────────────┘                         │
│                              │                                   │
│                              ▼                                   │
│                     ┌─────────────────┐                         │
│                     │ RegimeManager   │                         │
│                     │ (Spec 024)      │                         │
│                     └─────────────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
strategies/common/orderflow/
├── __init__.py              # Public exports
├── config.py                # VPINConfig, HawkesConfig, OrderflowConfig
├── trade_classifier.py      # TickRuleClassifier, BVCClassifier, CloseVsOpenClassifier
├── vpin.py                  # VPINIndicator implementation
├── hawkes_ofi.py            # HawkesOFI implementation
└── orderflow_manager.py     # Unified OrderflowManager

tests/
├── test_trade_classifier.py
├── test_vpin.py
└── test_hawkes_ofi.py
```

## Technical Decisions

### Decision 1: Trade Classification Method

**Options Considered**:
1. **Tick Rule** (default)
   - Pros: Simple, works with any price data, no quotes needed
   - Cons: Less accurate for zero-tick trades
2. **Bulk Volume Classification (BVC)**
   - Pros: More accurate, academic standard
   - Cons: Requires high/low data
3. **Lee-Ready**
   - Pros: Most accurate
   - Cons: Requires L2 quote data (bid/ask)

**Selected**: Option 1 (Tick Rule) with BVC fallback

**Rationale**: Tick rule works with bar data (our primary use case). BVC available when high/low present. Lee-Ready excluded as we don't have L2 quotes.

---

### Decision 2: Hawkes Library

**Options Considered**:
1. **tick library** (X-DataInitiative)
   - Pros: Production-ready, C++ core, well-documented
   - Cons: Batch-oriented, not streaming
2. **Custom scipy.optimize**
   - Pros: Full control, streaming possible
   - Cons: Slow, complex implementation
3. **PyTorch Hawkes**
   - Pros: GPU acceleration
   - Cons: Overkill for 1D processes

**Selected**: Option 1 (tick library) with rolling window approach

**Rationale**: tick is production-ready. Rolling window refit solves streaming issue.

---

### Decision 3: VPIN Bucket Strategy

**Options Considered**:
1. **Fixed volume buckets** (Easley et al.)
   - Pros: Original methodology, volume-synchronized
   - Cons: Variable number of buckets per day
2. **Fixed time buckets**
   - Pros: Predictable, easier to implement
   - Cons: Not volume-synchronized, loses VPIN benefits

**Selected**: Option 1 (Fixed volume buckets)

**Rationale**: Volume synchronization is the key insight of VPIN - removes time-of-day effects.

---

## Implementation Strategy

### Phase 1: Foundation (Trade Classification + Config)

**Goal**: Implement trade classification and Pydantic configs

**Deliverables**:
- [x] `config.py` - VPINConfig, HawkesConfig, OrderflowConfig
- [ ] `trade_classifier.py` - TickRuleClassifier, BVCClassifier, CloseVsOpenClassifier
- [ ] Unit tests for classifiers

**Dependencies**: None (uses only stdlib + pydantic)

---

### Phase 2: VPIN Indicator

**Goal**: Implement streaming VPIN indicator

**Deliverables**:
- [ ] `vpin.py` - VPINIndicator class
- [ ] Volume bucketing logic
- [ ] Rolling VPIN calculation
- [ ] Integration with Bar data
- [ ] Unit tests (>80% coverage)

**Dependencies**: Phase 1 (trade_classifier)

**Key Implementation Details**:
```python
class VPINIndicator:
    def __init__(self, config: VPINConfig):
        self.config = config
        self._buckets: list[VPINBucket] = []
        self._current_bucket: VPINBucket | None = None
        self._classifier = create_classifier(config.classification_method)

    def handle_bar(self, bar: Bar) -> None:
        classification = self._classifier.classify(bar)
        self._update_bucket(classification)
        self._recalculate_vpin()

    @property
    def value(self) -> float:
        if len(self._buckets) < self.config.n_buckets:
            return 0.0
        oi_values = [b.order_imbalance for b in self._buckets[-self.config.n_buckets:]]
        return float(np.mean(oi_values))
```

---

### Phase 3: Hawkes OFI Indicator

**Goal**: Implement Hawkes-based OFI indicator

**Deliverables**:
- [ ] `hawkes_ofi.py` - HawkesOFI class
- [ ] Rolling window event buffer
- [ ] Periodic refit logic
- [ ] Intensity calculation
- [ ] Pure Python fallback (if tick unavailable)
- [ ] Unit tests (>80% coverage)

**Dependencies**: Phase 1 (config), tick library

**Key Implementation Details**:
```python
class HawkesOFI:
    def __init__(self, config: HawkesConfig):
        self.config = config
        self._buy_times: list[float] = []
        self._sell_times: list[float] = []
        self._hawkes: HawkesExpKern | None = None
        self._ticks_since_fit = 0

    def handle_bar(self, bar: Bar) -> None:
        classification = self._classifier.classify(bar)
        self._add_event(classification)

        self._ticks_since_fit += 1
        if self._ticks_since_fit >= self.config.refit_interval:
            self.refit()
            self._ticks_since_fit = 0

    @property
    def ofi(self) -> float:
        if not self.is_fitted:
            return 0.0
        total = self.buy_intensity + self.sell_intensity
        if total <= 0:
            return 0.0
        return (self.buy_intensity - self.sell_intensity) / total
```

---

### Phase 4: OrderflowManager + Integration

**Goal**: Unified manager and integration with GillerSizer

**Deliverables**:
- [ ] `orderflow_manager.py` - OrderflowManager class
- [ ] Integration test with GillerSizer
- [ ] Integration test with RegimeManager
- [ ] Example strategy using orderflow
- [ ] Documentation updates

**Dependencies**: Phase 2, Phase 3

---

## File Structure

```
strategies/common/orderflow/
├── __init__.py              # Export: VPINIndicator, HawkesOFI, OrderflowManager, configs
├── config.py                # VPINConfig, HawkesConfig, OrderflowConfig
├── trade_classifier.py      # TradeClassifier implementations
├── vpin.py                  # VPINIndicator
├── hawkes_ofi.py            # HawkesOFI
└── orderflow_manager.py     # OrderflowManager

tests/
├── test_trade_classifier.py # Trade classification tests
├── test_vpin.py             # VPIN indicator tests
└── test_hawkes_ofi.py       # Hawkes OFI tests
```

## API Design

### Public Interface

```python
# strategies/common/orderflow/__init__.py
from strategies.common.orderflow.config import (
    VPINConfig,
    HawkesConfig,
    OrderflowConfig,
)
from strategies.common.orderflow.vpin import VPINIndicator
from strategies.common.orderflow.hawkes_ofi import HawkesOFI
from strategies.common.orderflow.orderflow_manager import OrderflowManager
from strategies.common.orderflow.trade_classifier import (
    TradeClassifier,
    TickRuleClassifier,
    BVCClassifier,
    CloseVsOpenClassifier,
)

__all__ = [
    "VPINConfig",
    "HawkesConfig",
    "OrderflowConfig",
    "VPINIndicator",
    "HawkesOFI",
    "OrderflowManager",
    "TradeClassifier",
    "TickRuleClassifier",
    "BVCClassifier",
    "CloseVsOpenClassifier",
]
```

### Configuration

```python
from pydantic import BaseModel, Field

class VPINConfig(BaseModel):
    bucket_size: float = Field(default=1000.0, gt=0)
    n_buckets: int = Field(default=50, ge=10, le=200)
    classification_method: str = Field(default="tick_rule")
    min_bucket_volume: float = Field(default=100.0, ge=0)

    model_config = {"frozen": True}


class HawkesConfig(BaseModel):
    decay_rate: float = Field(default=1.0, gt=0)
    lookback_ticks: int = Field(default=10000, ge=100)
    refit_interval: int = Field(default=100, ge=10)
    use_fixed_params: bool = Field(default=False)

    model_config = {"frozen": True}


class OrderflowConfig(BaseModel):
    vpin: VPINConfig = Field(default_factory=VPINConfig)
    hawkes: HawkesConfig = Field(default_factory=HawkesConfig)
    enable_vpin: bool = Field(default=True)
    enable_hawkes: bool = Field(default=True)

    model_config = {"frozen": True}
```

## Testing Strategy

### Unit Tests
- [ ] Test trade classification (tick rule, BVC, close-vs-open)
- [ ] Test VPIN bucket creation and completion
- [ ] Test VPIN calculation formula
- [ ] Test Hawkes fitting and intensity calculation
- [ ] Test OFI normalization
- [ ] Test edge cases (empty data, zero volume, NaN handling)

### Integration Tests
- [ ] Test with BacktestNode and sample bar data
- [ ] Test OrderflowManager with GillerSizer
- [ ] Test with RegimeManager (Spec 024)
- [ ] Test with real historical data (flash crash events)

### Performance Tests
- [ ] VPIN latency < 5ms per bucket
- [ ] Hawkes fitting < 1s on 10K ticks
- [ ] Memory usage stable over long runs

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| tick library incompatible with Python 3.12 | Medium | Medium | Pure Python fallback using scipy |
| VPIN not predictive for crypto | Medium | Low | Validate on historical flash crashes |
| Hawkes fitting fails to converge | Low | Medium | Fixed-parameter mode fallback |
| High memory usage from event buffer | Low | Low | Ring buffer with max size |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.220.0
- numpy
- scipy
- pydantic
- tick (optional, for Hawkes)

### Internal Dependencies
- `strategies/common/position_sizing/` (Spec 024) - GillerSizer
- `strategies/common/regime_detection/` (Spec 024) - RegimeManager (optional)

## Acceptance Criteria

- [x] Research complete (research.md)
- [x] Data model defined (data-model.md)
- [x] API contracts defined (contracts/)
- [x] Quickstart guide (quickstart.md)
- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Performance benchmarks met (VPIN <5ms, Hawkes <1s)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | Clean API, hidden implementation |
| KISS & YAGNI | ✅ | Minimal complexity, no over-engineering |
| Native First | ⚠️ | No native NautilusTrader orderflow indicators |
| NO df.iterrows() | ✅ | Using numpy vectorized operations |
| TDD Discipline | ⏳ | Tests first per phase |
| Coverage > 80% | ⏳ | To be verified |

## Next Steps

1. Run `/speckit.tasks` to generate task breakdown
2. Create feature branch: `git checkout -b 025-orderflow-indicators`
3. Start with Phase 1: Trade Classification + Config
4. Follow TDD: Write tests first, then implementation
