# Research: Meta-Learning Pipeline (Spec 026)

**Date**: 2026-01-03
**Status**: Complete
**Sources**: arXiv, Semantic Scholar, Google Scholar, NautilusTrader Docs, Discord Community

---

## Executive Summary

This research consolidates findings from academic papers (2020-2025), NautilusTrader documentation, and community best practices for implementing a meta-learning pipeline. Key innovations include:

1. **Adaptive Event-Driven Labeling** (AEDL) - 2025 advancement over classic triple barrier
2. **Score-Driven BOCD** - Handles temporal correlations within regimes
3. **Rigorous Walk-Forward Framework** - 34 independent test periods protocol
4. **Meta-Labeling Architecture** - Three-component decomposition

---

## Research Task 1: Triple Barrier Labeling

### Academic Papers Found

| Paper | Year | Key Contribution | Relevance |
|-------|------|------------------|-----------|
| **Adaptive Event-Driven Labeling (AEDL)** - Kili et al. | 2025 | Multi-scale + causal inference + MAML | 10/10 |
| **Stock Price Prediction Using Triple Barrier** - Kang | 2025 | Optimal parameters (29 days, 9% barrier) | 9/10 |
| **Enhanced GA-Driven Triple Barrier** - Fu et al. | 2024 | Genetic algorithm barrier optimization | 8/10 |
| **Algorithmic Crypto Trading with Information-Driven Bars** - Gradzki | 2025 | Information bars + deep learning | 7/10 |

### Key Findings

#### AEDL Framework (SOTA 2025)

The **Adaptive Event-Driven Labeling** paper (DOI: 10.3390/app152413204) represents the state-of-the-art, addressing three critical deficiencies in traditional triple barrier:

1. **Temporal Rigidity** → Multi-scale temporal analysis (5 resolutions)
2. **Scale Blindness** → Hierarchical market patterns
3. **Correlation-Causation Conflation** → Granger causality + transfer entropy

**Performance Benchmarks (16 assets, 25 years)**:
- AEDL Average Sharpe: **0.48**
- Fixed Horizon Sharpe: **-0.29**
- Classic Triple Barrier: **-0.03**
- Trend Scanning: **0.00**
- Statistical significance: p=0.0024 (Wilcoxon test)

**Critical Insight**: Removing causal inference improved Sharpe to **0.65** - selective innovation outperforms "kitchen sink" approaches.

#### Optimal Parameters (Kang 2025)

- **Window**: 29 days
- **Barrier Height**: 9% (balanced class distribution)
- **Feature Engineering**: Raw OHLCV + technical indicators

#### Implementation Pseudocode

```python
def adaptive_triple_barrier(
    prices: np.ndarray,
    atr: np.ndarray,
    pt_mult: float = 2.0,
    sl_mult: float = 1.0,
    max_holding: int = 10,
) -> np.ndarray:
    """
    AFML-compliant triple barrier labeling.

    Key constraints to avoid look-ahead bias:
    1. ATR calculated from PAST data only (at entry time)
    2. Use high/low for barrier checks (not close)
    3. Labels are forward-looking from entry point
    """
    n = len(prices)
    labels = np.zeros(n)

    for i in range(n - max_holding):
        entry_price = prices[i]
        current_atr = atr[i]  # ATR at entry time (no peeking)

        # Set barriers at entry time
        tp_barrier = entry_price + (pt_mult * current_atr)
        sl_barrier = entry_price - (sl_mult * current_atr)

        # Check future prices (high/low for intraday accuracy)
        for j in range(i + 1, min(i + max_holding + 1, n)):
            if prices[j] >= tp_barrier:  # Use high in production
                labels[i] = 1  # Take profit
                break
            elif prices[j] <= sl_barrier:  # Use low in production
                labels[i] = -1  # Stop loss
                break
        else:
            # Timeout - use sign of return
            final_return = prices[i + max_holding] - entry_price
            labels[i] = np.sign(final_return) if final_return != 0 else 0

    return labels
```

### Decision

**Selected**: Custom implementation based on AFML + AEDL insights

**Rationale**:
- mlfinlab has licensing concerns (Hudson & Thames)
- Python 3.11+ compatibility issues reported
- Custom allows streaming/incremental updates
- Can incorporate AEDL multi-scale extension later

---

## Research Task 2: Meta-Labeling Architecture

### Academic Papers Found

| Paper | Year | Key Contribution | Relevance |
|-------|------|------------------|-----------|
| **Meta-Labeling: Theory and Framework** - Joubert | 2022 | Three-component decomposition | 10/10 |
| **Meta-Labeling Architecture** - Meyer et al. | 2022 | Model complexity analysis | 9/10 |
| **Ensemble Meta-Labeling** - Thumm et al. | 2023 | Ensemble methods comparison | 8/10 |
| **Does Meta-Labeling Add to Signal Efficacy** - Singh | 2019 | Empirical validation | 7/10 |

### Key Findings

#### Three-Component Decomposition (Joubert 2022)

Meta-labeling consists of three distinct functions:

1. **Binary Classification Layer**
   - Predicts P(primary signal correct)
   - Acts as filter on primary signals
   - Uses same features as primary model + additional meta-features

2. **Position Sizing Module**
   - Adjusts position size based on confidence
   - Relationship: size ∝ confidence^0.5 (sub-linear per Giller)

3. **False Positive Filter**
   - Reduces whipsaw trades
   - Improves precision without sacrificing too much recall

#### Meta-Feature Engineering

Recommended meta-features from literature:

```python
META_FEATURES = {
    # Volatility-based (50-60% importance)
    "realized_vol_20": "rolling std of returns (20 bars)",
    "atr_normalized": "ATR / price",
    "vol_regime": "HMM state for volatility",

    # Regime-based (15-20% importance)
    "hmm_state": "Hidden Markov Model state",
    "hmm_confidence": "P(current_state)",
    "regime_age": "Bars since last regime change",

    # Orderflow (30-40% for HFT)
    "vpin": "Volume-Synchronized PIN",
    "ofi": "Order Flow Imbalance",
    "toxicity_level": "VPIN categorical",

    # Signal quality
    "signal_strength": "Magnitude of primary signal",
    "recent_win_rate": "Rolling win rate (last 20 trades)",
    "drawdown_pct": "Current drawdown from peak",
}
```

#### Performance Expectations

From empirical studies:
- **Precision improvement**: +10-20%
- **Sharpe ratio improvement**: +0.1-0.3
- **Max drawdown reduction**: 15-30%
- **Win rate**: 45% → 50-55% after filtering

### Decision

**Selected**: RandomForest (sklearn) for initial implementation

**Rationale**:
- Simple, interpretable, no hyperparameter tuning required
- Feature importance helps understand meta-features
- sklearn already a dependency
- Upgrade path to XGBoost/LightGBM if needed

---

## Research Task 3: Bayesian Online Changepoint Detection (BOCD)

### Academic Papers Found

| Paper | Year | Key Contribution | Relevance |
|-------|------|------------------|-----------|
| **Online Learning of Order Flow with BOCD** - Tsaknaki et al. | 2024 | Score-driven BOCD for finance | 10/10 |
| **Bayesian AR Online Change-Point Detection** - Tsaknaki | 2024 | Time-varying parameters within regimes | 9/10 |
| **Regime-Switching State-Space Models** - Kim & Nelson | 1999 | Classical regime-switching (1500+ citations) | 8/10 |
| **Intelligent Trading with BOCD** - Wu & Han | 2023 | BOCD + HMM hybrid | 8/10 |

### Key Findings

#### Score-Driven BOCD (SOTA 2024)

The Tsaknaki et al. paper (DOI: 10.1080/14697688.2024.2337300) introduces significant improvements:

1. **Within-Regime Dynamics**
   - Models data as autoregressive process (AR(p))
   - Allows variance AND correlation to vary within regimes
   - Score function updates for better adaptation

2. **Order Flow Application**
   - Detects regime shifts in market microstructure
   - Superior out-of-sample prediction vs. i.i.d. assumptions
   - Concave price impact within regimes (matches real market behavior)

#### Adams & MacKay Algorithm (Foundation)

```python
class BOCD:
    """Bayesian Online Changepoint Detection (Adams & MacKay 2007)."""

    def __init__(
        self,
        hazard_rate: float = 1/250,  # Expected 1 change per 250 bars
        mu0: float = 0.0,
        kappa0: float = 1.0,
        alpha0: float = 1.0,
        beta0: float = 1.0,
    ):
        self.hazard = hazard_rate
        # Student-t conjugate prior parameters
        self.mu = [mu0]
        self.kappa = [kappa0]
        self.alpha = [alpha0]
        self.beta = [beta0]

        # Run length distribution
        self.run_length_dist = [1.0]
        self.t = 0

    def update(self, x: float) -> float:
        """
        Process single observation, return P(changepoint).

        Algorithm:
        1. Calculate predictive probability for each run length
        2. Growth probability = P(no changepoint) * pred_prob
        3. Changepoint probability = sum(P(changepoint) * pred_prob)
        4. Normalize run length distribution
        5. Update sufficient statistics (Bayesian update)
        """
        self.t += 1

        # Predictive probabilities (Student-t)
        pred_probs = self._predictive_probs(x)

        # Growth and changepoint probabilities
        growth = self.run_length_dist * pred_probs * (1 - self.hazard)
        cp = np.sum(self.run_length_dist * pred_probs * self.hazard)

        # New run length distribution
        new_dist = np.zeros(self.t + 1)
        new_dist[0] = cp
        new_dist[1:] = growth

        # Normalize
        new_dist /= new_dist.sum()
        self.run_length_dist = new_dist

        # Update sufficient statistics
        self._update_params(x)

        return new_dist[0]  # P(changepoint)
```

#### Hazard Rate Selection

Based on literature:
| Timeframe | Hazard Rate | Expected Run Length |
|-----------|-------------|---------------------|
| Daily bars | 1/250 | 1 year |
| Hourly bars | 1/2000 | ~3 months |
| Minute bars | 1/20000 | ~2 weeks |

#### Performance Benchmarks

From Tsaknaki et al. on NASDAQ data:
- Successfully detected regime changes during major events
- Superior predictive performance vs. standard HMM
- Concave price impact matches theoretical expectations

### Decision

**Selected**: Custom BOCD (Adams & MacKay base + extensions)

**Rationale**:
- ruptures library is offline-only (batch processing)
- Need true online/streaming for live trading
- Custom allows score-driven extension later
- Well-documented algorithm with Python pseudocode available

---

## Research Task 4: Walk-Forward Validation

### Academic Papers Found

| Paper | Year | Key Contribution | Relevance |
|-------|------|------------------|-----------|
| **Interpretable Hypothesis-Driven Trading** - Deep et al. | 2025 | Rigorous 34-period framework | 10/10 |
| **VIX Futures Walk-Forward ML Study** - Wang et al. | 2024 | Optimal window sizes | 9/10 |
| **KZ Decomposition Walk-Forward** - 2025 | Multi-scale validation | 8/10 |

### Key Findings

#### Rigorous Walk-Forward Protocol (Deep et al. 2025)

**34 Independent Test Periods Framework** (arXiv: 2512.12924):

```python
class WalkForwardValidator:
    """
    Information-disciplined walk-forward validation.

    Key principles:
    1. Strict train/test separation (no peeking)
    2. Embargo period between train and test
    3. Purging overlapping samples
    4. Rolling (not expanding) for non-stationary markets
    """

    def __init__(
        self,
        train_window: int = 252,   # 1 year
        test_window: int = 63,     # 1 quarter
        step_size: int = 21,       # 1 month
        embargo: int = 5,          # Gap to prevent leakage
    ):
        self.train_window = train_window
        self.test_window = test_window
        self.step_size = step_size
        self.embargo = embargo

    def generate_splits(
        self,
        n_samples: int,
    ) -> list[tuple[np.ndarray, np.ndarray]]:
        """Generate train/test index pairs."""
        splits = []

        i = 0
        while i + self.train_window + self.embargo + self.test_window <= n_samples:
            train_start = i
            train_end = i + self.train_window
            test_start = train_end + self.embargo
            test_end = test_start + self.test_window

            train_idx = np.arange(train_start, train_end)
            test_idx = np.arange(test_start, test_end)

            splits.append((train_idx, test_idx))
            i += self.step_size

        return splits

    def purge_overlapping_labels(
        self,
        labels: np.ndarray,
        max_holding: int,
    ) -> np.ndarray:
        """
        Remove samples whose labels depend on test period data.
        Critical for triple barrier where labels span multiple bars.
        """
        # Implementation: mask samples where label lookforward
        # extends into test period
        pass
```

#### Optimal Window Sizes

Consensus from literature:
| Component | Daily Strategy | Hourly Strategy |
|-----------|----------------|-----------------|
| Training | 252 bars (1 year) | 2000 bars (~3 months) |
| Validation | 63 bars (1 quarter) | 500 bars (~3 weeks) |
| Testing | 21 bars (1 month) | 168 bars (~1 week) |
| Embargo | 5 bars | 24 bars |
| Step | 21 bars | 168 bars |

#### Performance Expectations

From Deep et al. (100 US equities, 2015-2024):
- Annualized return: **0.55%**
- Sharpe ratio: **0.33**
- Max drawdown: **-2.76%**
- Market beta: **0.058**

**Critical Insight**: Even rigorous walk-forward often yields statistically insignificant results (p=0.34 in paper). This is honest reporting and expected for realistic strategies.

#### Regime Dependence

From Deep et al.:
- High volatility (2020-2024): **+0.60% quarterly**
- Stable markets (2015-2019): **-0.16% quarterly**

Implication: Performance highly regime-dependent, reinforcing need for BOCD integration.

### Decision

**Selected**: Rolling window (252/63/21/5) with embargo and purging

**Rationale**:
- Markets are non-stationary (expanding window not appropriate)
- Embargo prevents label leakage
- Purging critical for triple barrier (labels span multiple bars)
- Matches consensus from literature

---

## Research Task 5: NautilusTrader Integration Patterns

### Findings from Documentation & Discord

#### Position Sizing API

```python
from nautilus_trader.risk.sizing import FixedRiskSizer

# Create position sizer
sizer = FixedRiskSizer(instrument=instrument)

# Calculate position size
quantity = sizer.calculate(
    entry=Price.from_str("50000.00"),
    stop_loss=Price.from_str("49000.00"),
    equity=Money(100000, USD),
    risk=Decimal("0.02"),
    hard_limit=Quantity.from_int(100),
)
```

**Discord Note**: RiskEngine validation errors include `NOTIONAL_EXCEEDS_FREE_BALANCE` - ensure sufficient margin.

#### State Persistence Pattern

```python
class MLStrategy(Strategy):
    def on_save(self) -> dict[str, bytes]:
        """Serialize ML model state."""
        return {
            "model_weights": pickle.dumps(self.model.get_weights()),
            "training_data": pickle.dumps(self.training_data[-1000:]),
        }

    def on_load(self, state: dict[str, bytes]) -> None:
        """Restore ML model state."""
        self.model.set_weights(pickle.loads(state["model_weights"]))
```

#### Warmup Pattern (Critical for ML)

```python
def on_start(self):
    """Request historical data for model warmup."""
    self.request_bars(
        bar_type=self.bar_type,
        start=self.clock.utc_now() - timedelta(days=365),
        callback=self._warmup_complete,
    )

def on_historical_data(self, data):
    """Process historical bars for model training."""
    for bar in data.bars:
        self.indicator.handle_bar(bar)
```

---

## Research Task 6: Integrated Pipeline Formula

### Giller Insights (Desktop Articles)

**Sub-linear Position Sizing**:
```python
# WRONG (linear)
position_size = signal_magnitude

# RIGHT (sub-linear - Giller)
position_size = signal_magnitude ** 0.5
```

**Reason**: Financial returns follow Laplace (not Gaussian) distribution. Linear sizing over-leverages outliers.

### Final Integrated Formula

```python
def integrated_position_size(
    signal_direction: int,          # +1 or -1
    signal_magnitude: float,        # Absolute signal strength
    meta_confidence: float,         # P(correct) from meta-model [0, 1]
    regime_weight: float,           # From HMM/GMM [0.4, 1.2]
    vpin_toxicity: float,           # From VPIN [0, 1]
    fractional_kelly: float = 0.5,  # Safety margin
) -> float:
    """
    Multiplicative combination of all factors.

    Formula:
        size = direction *
               |signal|^0.5 *      (sub-linear, Giller)
               meta_confidence *   (meta-model filter)
               regime_weight *     (regime adjustment)
               (1 - toxicity) *    (orderflow penalty)
               fractional_kelly    (Kelly fraction)
    """
    if signal_magnitude == 0:
        return 0.0

    return (
        signal_direction *
        (abs(signal_magnitude) ** 0.5) *
        meta_confidence *
        regime_weight *
        (1 - vpin_toxicity) *
        fractional_kelly
    )
```

---

## Summary of Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Triple Barrier | Custom (AFML + AEDL insights) | Licensing, Python 3.11+, streaming |
| Meta-Model | RandomForest (sklearn) | Simple, interpretable, upgrade path |
| BOCD | Custom (Adams & MacKay) | Online required, ruptures is offline |
| Walk-Forward | Rolling 252/63/21/5 | Non-stationarity, embargo, purging |
| Hazard Rate | 1/250 (daily) | Literature consensus |
| Fractional Kelly | 0.5 | Half-Kelly for safety |
| BOCD Threshold | 0.8 | Conservative default |

---

## Edge Cases Resolved

| Edge Case | Resolution |
|-----------|------------|
| Insufficient meta-model training data | Return default confidence (0.5) |
| BOCD non-stationary mean AND variance | Score-driven extension (future) |
| Triple barrier never hits any barrier | Return sign(final_return) or 0 |
| Retrain meta-model without look-ahead | Embargo period + purging |
| High toxicity + low confidence | Position near zero (multiplicative) |
| Missing factors at inference | Use safe defaults per config |

---

## Python Libraries Recommended

```bash
# Core ML
uv pip install numpy scipy scikit-learn

# Already available in nightly
# numpy >= 1.24.0
# scipy >= 1.10.0
# scikit-learn >= 1.2.0

# Optional for advanced features
# uv pip install xgboost lightgbm  # If RF insufficient
# uv pip install tigramite  # Causal inference (AEDL extension)
# uv pip install bayesflow  # Advanced Bayesian inference
```

---

## Implementation References (Custom Implementation Guidance)

### Triple Barrier Labeling - Open Source Reference Code

**Use as reference only for custom implementation** (DO NOT add as dependency):

1. **quantopian/mlfinlab** (pre-commercial fork): Algorithm reference
   - Source: https://github.com/hudson-and-thames/mlfinlab/blob/master/mlfinlab/labeling/labeling.py
   - Key functions: `get_events()`, `get_bins()`, `apply_pt_sl_on_t1()`
   - DeepWiki: https://deepwiki.com/quantopian/mlfinlab/6.3-triple-barrier-method

2. **mlfinlab 0.12.0 docs**: Algorithm explanation (last open version)
   - Docs: https://random-docs.readthedocs.io/en/latest/implementations/tb_meta_labeling.html

3. **mlfinpy**: Alternative reimplementation
   - Docs: https://mlfinpy.readthedocs.io/en/latest/Labelling.html

### Key Functions from mlfinlab Reference

```python
# Reference from mlfinlab/labeling/labeling.py - adapt for NautilusTrader

def get_events(close, t_events, pt_sl, target, min_ret=0, num_threads=1, vertical_barrier_times=None):
    """
    Finds the time of the first barrier touch.

    Args:
        close: Close prices series
        t_events: Timestamps of events (entries)
        pt_sl: [profit_taking, stop_loss] multipliers
        target: Series of targets (ATR or daily vol)
        min_ret: Minimum target return
        vertical_barrier_times: Timestamps of vertical barriers (timeouts)

    Returns:
        DataFrame with columns ['t1', 'trgt', 'side'] per event
    """
    pass  # Reference implementation - see source


def get_bins(events, close):
    """
    Labels events according to triple barrier method.

    Args:
        events: DataFrame from get_events()
        close: Close prices series

    Returns:
        DataFrame with ['ret', 'bin'] - return and label (-1, 0, +1)
    """
    pass  # Reference implementation - see source


def apply_pt_sl_on_t1(close, events, pt_sl, molecule):
    """
    Apply profit-taking/stop-loss on vertical barrier.
    Vectorized implementation for efficiency.
    """
    pass  # Reference implementation - see source
```

---

## References

### Meta-Labeling
1. Joubert, J. (2022). "Meta-Labeling: Theory and Framework." JFDS.
2. Meyer, M. et al. (2022). "Meta-Labeling Architecture." JFDS.
3. Thumm, D. et al. (2023). "Ensemble Meta-Labeling." JFDS.

### Triple Barrier
4. Kili, A. et al. (2025). "Adaptive Event-Driven Labeling." Applied Sciences. DOI: 10.3390/app152413204
5. Kang, S. (2025). "Stock Price Prediction Using Triple Barrier." arXiv:2504.02249
6. Fu, N. et al. (2024). "Enhanced GA-Driven Triple Barrier." Mathematics. DOI: 10.3390/math12050780

### BOCD
7. Tsaknaki, I. et al. (2024). "Online Learning of Order Flow with BOCD." Quantitative Finance. DOI: 10.1080/14697688.2024.2337300
8. Adams, R. & MacKay, D. (2007). "Bayesian Online Changepoint Detection."
9. Wu, B. & Han, X. (2023). "Intelligent Trading Strategy." arXiv:2309.15383

### Walk-Forward
10. Deep, G. et al. (2025). "Interpretable Hypothesis-Driven Trading." arXiv:2512.12924
11. Wang, S. et al. (2024). "VIX Walk-Forward ML Study." PLOS ONE. DOI: 10.1371/journal.pone.0302289

### Position Sizing
12. Giller, G. "The 10 Most Important Things." Desktop articles.
13. López de Prado, M. (2020). "Machine Learning for Asset Managers." Cambridge.

---

## Next Steps

1. ✅ Plan artifacts complete (plan.md, research.md, data-model.md, contracts/, quickstart.md)
2. Generate tasks.md via `/speckit.tasks`
3. Implement following TDD discipline (RED → GREEN → REFACTOR)
4. Use test-runner agent for all tests
5. Use alpha-debug agent after implementation phases
