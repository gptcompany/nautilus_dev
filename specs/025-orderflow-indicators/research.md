# Research: Orderflow Indicators (Spec 025)

**Feature Branch**: `025-orderflow-indicators`
**Created**: 2026-01-02
**Status**: Complete

## Research Summary

This document consolidates research findings for implementing VPIN and Hawkes Order Flow Imbalance (OFI) indicators.

---

## 1. VPIN Implementation

### Decision: Custom Python Implementation
**Rationale**: No production-ready library exists. Custom implementation following Easley et al. (2012) paper.

**Alternatives Considered**:
1. `PINstimation` R package - Not Python native
2. GitHub implementations (yt-feng/VPIN) - Reference only, not production-ready
3. mlfinlab - Has BVC but not full VPIN streaming

### Key Papers

| Paper | Authors | Year | Key Contribution |
|-------|---------|------|------------------|
| The Microstructure of the "Flash Crash" | Easley, López de Prado, O'Hara | 2012 | Original VPIN methodology |
| Flow Toxicity and Liquidity | Easley, López de Prado, O'Hara | 2012 | Volume synchronization approach |
| An Improved Version of VPIN | Ke, Lin | 2017 | BVC improvements |
| Informed trading, flow toxicity | Wei, Gerace, Frino | 2013 | Australian market validation |

### Algorithm: Volume-Synchronized PIN

```
VPIN Calculation:
1. Classify trades as buy/sell (tick rule or BVC)
2. Create equal-volume buckets (not time buckets)
3. For each bucket: OI = |V_buy - V_sell| / (V_buy + V_sell)
4. VPIN = rolling mean of OI over n buckets (typically 50)
```

**Volume Bucket Size**: σ_daily / 50 (standard bar size from AFML)

**Trade Classification Options**:
1. **Tick Rule** (default): price > prev_price → buy, price < prev_price → sell
2. **Bulk Volume Classification (BVC)**: Use CDF of price change distribution
3. **Lee-Ready**: Use quote midpoint comparison (requires L2 data)

### Integration with GillerSizer

```python
# GillerSizer already supports toxicity parameter:
size = scaled * base_size * regime_weight * (1.0 - toxicity)

# VPIN feeds directly into toxicity:
toxicity = vpin_indicator.value  # [0.0, 1.0]
position_size = giller_sizer.calculate(signal, regime_weight, toxicity=toxicity)
```

### Edge Cases

| Edge Case | Solution |
|-----------|----------|
| Very low volume periods | Use minimum bucket size, carry forward last VPIN |
| Missing tick data | Interpolate or use bar close-vs-open heuristic |
| Zero volume in bucket | Skip bucket, don't contribute to average |
| All buys or all sells | VPIN = 1.0 (maximum toxicity) |

---

## 2. Hawkes Process OFI

### Decision: tick Library (X-DataInitiative)
**Rationale**: Production-ready, actively maintained (3k+ GitHub stars equivalent), fast C++ core with Python API.

**Alternatives Considered**:
1. Custom scipy.optimize implementation - Too slow for online fitting
2. PyTorch Hawkes - Overkill, GPU not needed for 1D processes
3. hawkes-estimator - Less documented, smaller community

### Key Papers

| Paper | Authors | Year | Key Contribution |
|-------|---------|------|------------------|
| Forecasting OFI with Hawkes | Various | 2024 | SOTA OFI forecasting |
| Estimation of Order Book Dependent Hawkes | Mucciante, Sancetta | 2023 | Order book integration |
| Optimal trade execution under endogenous order flow | Chen, Horst, Tran | 2021 | Execution with Hawkes |
| Transform analysis for Hawkes with dark pool | Gao, Zhou, Zhu | 2017 | Analytical solutions |

### Algorithm: Self-Exciting Point Process

```
Hawkes Intensity:
λ(t) = μ + Σ α * exp(-β * (t - t_i))

Where:
- μ = baseline intensity
- α = excitation (jump size when event occurs)
- β = decay rate (how quickly excitation fades)
- t_i = timestamps of past events

Branching Ratio: η = α/β (must be < 1 for stationarity)
```

### tick Library API

```python
from tick.hawkes import HawkesExpKern

# Fit bivariate Hawkes (buy and sell streams)
hawkes = HawkesExpKern(
    decays=1.0,  # β decay rate
    n_threads=4
)
hawkes.fit([buy_times, sell_times])

# Get current intensities
lambda_buy = hawkes.estimated_intensity_at(current_time, 0)
lambda_sell = hawkes.estimated_intensity_at(current_time, 1)

# Order Flow Imbalance
ofi = (lambda_buy - lambda_sell) / (lambda_buy + lambda_sell + 1e-10)
```

### Online Fitting Strategy

**Problem**: tick library is batch-oriented, not streaming.

**Solution**: Rolling window approach
1. Keep buffer of last N ticks (e.g., 10,000)
2. Refit every M ticks (e.g., 100)
3. Use warm-start from previous parameters

**Alternative**: Fixed-parameter approach
- Fit once on historical data
- Use fixed μ, α, β in production
- Only update intensity calculation online

### Edge Cases

| Edge Case | Solution |
|-----------|----------|
| Process doesn't converge | Use default parameters, log warning |
| Branching ratio ≥ 1 | Clip α to ensure η < 0.99 |
| Very sparse events | Increase lookback window |
| Timestamp collisions | Add small random jitter |

---

## 3. Trade Classification

### Decision: Tick Rule (Default) with BVC Fallback
**Rationale**: Tick rule is simple, works with bar data. BVC for more accuracy when needed.

### Implementation Options

1. **Tick Rule** (simplest):
```python
side = 1 if price > prev_price else -1 if price < prev_price else prev_side
```

2. **Close vs Open Heuristic** (for bars):
```python
side = 1 if bar.close > bar.open else -1
```

3. **Bulk Volume Classification (BVC)**:
```python
# Split volume proportionally based on price position in range
v_buy = volume * (close - low) / (high - low + 1e-10)
v_sell = volume - v_buy
```

---

## 4. NautilusTrader Integration Pattern

### Existing Codebase Patterns

From `strategies/common/`:
- `regime_detection/` - HMM, GMM filters (Spec 024)
- `position_sizing/giller_sizing.py` - Already supports toxicity parameter
- No existing trade classification utilities

### Proposed Structure

```
strategies/common/orderflow/
├── __init__.py
├── vpin.py              # VPIN indicator (streaming)
├── hawkes_ofi.py        # Hawkes OFI indicator
├── trade_classifier.py  # Tick rule, BVC, Lee-Ready
├── config.py            # Pydantic configs
└── orderflow_manager.py # Unified interface for strategies
```

### Integration with RegimeManager (Spec 024)

```python
# OrderflowManager could be a peer to RegimeManager
class OrderflowManager:
    def __init__(self, config: OrderflowConfig):
        self.vpin = VPINIndicator(config.vpin)
        self.hawkes = HawkesOFI(config.hawkes)

    def update(self, bar: Bar) -> None:
        self.vpin.handle_bar(bar)
        self.hawkes.handle_bar(bar)

    @property
    def toxicity(self) -> float:
        return self.vpin.value

    @property
    def ofi(self) -> float:
        return self.hawkes.ofi
```

---

## 5. Dependencies

### Required

```bash
# Already in project
numpy
scipy

# New dependency
uv pip install tick  # Hawkes processes
```

### tick Library Notes

- **Installation**: `pip install tick` or `uv pip install tick`
- **Requires**: Python 3.8-3.11 (check compatibility with 3.12+)
- **C++ core**: Fast but may have build issues on some systems
- **Alternative**: Pure Python fallback using scipy.optimize if tick unavailable

---

## 6. Performance Requirements (from Spec)

| Metric | Target |
|--------|--------|
| VPIN latency | <5ms per bucket |
| Hawkes fitting | <1s on 10K ticks |
| OFI prediction accuracy | >55% short-term direction |
| VPIN-volatility correlation | >0.7 |

---

## 7. References

### Academic
- Easley, D., López de Prado, M., & O'Hara, M. (2012). "Flow Toxicity and Liquidity in a High-Frequency World"
- Adams, R. P., & MacKay, D. J. (2007). "Bayesian Online Changepoint Detection"

### Implementation
- tick library: https://x-datainitiative.github.io/tick/
- PINstimation R package: https://github.com/monty-se/PINstimation
- mlfinlab: https://github.com/hudson-and-thames/mlfinlab

### Project Context
- `docs/research/trading_ml_research_final_2026.md` - Full research document
- `docs/research/implementation_priority_matrix_2026.md` - Priority ranking
