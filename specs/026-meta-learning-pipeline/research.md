# Research: Meta-Learning Pipeline (Spec 026)

**Date**: 2026-01-03
**Status**: Complete

## Research Tasks

### Task 1: Triple Barrier Labeling Best Practices

**Question**: How to implement triple barrier labeling without look-ahead bias?

**Research Findings**:

1. **AFML Original Algorithm** (López de Prado, 2018):
   - Set barriers at ENTRY time using available information only
   - Vertical barrier: fixed holding period (e.g., 10 days)
   - Horizontal barriers: ATR-based, calculated from PAST data
   - Never peek at future prices when setting barriers

2. **Dynamic Barrier Levels** (MDPI paper, 2024):
   - Use realized volatility from rolling window (e.g., 20-bar ATR)
   - Asymmetric barriers (PT > SL) for positive expectancy
   - Recommended ratio: PT = 2.0 * ATR, SL = 1.0 * ATR

3. **Label Generation Pitfalls**:
   - Do NOT use future ATR when setting barriers
   - Do NOT use close price that breaks barrier (use intraday high/low)
   - Handle overnight gaps by checking open price

**Decision**: Implement custom triple barrier with ATR-based barriers calculated at entry. Use high/low for barrier checks (not close).

**References**:
- López de Prado, "Advances in Financial Machine Learning" (2018), Chapter 3
- https://www.mdpi.com/2227-7390/12/5/780 (Enhanced Triple Barrier, 2024)

---

### Task 2: Meta-Model Feature Engineering

**Question**: What features should be used for meta-labeling?

**Research Findings**:

1. **Primary Signal Features** (same as primary model):
   - Technical indicators (EMA, RSI, MACD)
   - Price action (momentum, mean reversion)
   - Volume (relative volume, VWAP deviation)

2. **Secondary Features** (meta-specific):
   - **Regime indicators**: HMM state, GMM volatility regime
   - **Orderflow**: VPIN toxicity, Hawkes OFI intensity
   - **Calendar features**: Day of week, hour of day
   - **Recent performance**: Rolling win rate, drawdown

3. **Feature Importance** (from mlfinlab studies):
   - Volatility-based features most predictive (50-60% importance)
   - Regime features add 15-20% additional lift
   - Orderflow features critical for HFT (30-40% importance)

**Decision**: Use volatility (ATR, realized vol), regime (HMM state probability), and orderflow (VPIN) as core meta-features.

**References**:
- López de Prado, "Advances in Financial Machine Learning", Chapter 8
- Hudson & Thames mlfinlab documentation

---

### Task 3: BOCD Prior Selection

**Question**: How to choose BOCD hyperparameters (hazard rate, Student-t prior)?

**Research Findings**:

1. **Hazard Rate** (λ):
   - Represents expected run length between changepoints
   - For daily data: λ = 1/250 (expect 1 regime change per year)
   - For hourly data: λ = 1/2000 (proportionally longer)
   - Tune based on historical regime change frequency

2. **Student-t Prior** (Normal-Gamma conjugate):
   - `mu0 = 0.0`: Center at zero (log returns centered)
   - `kappa0 = 1.0`: Low precision (uninformative)
   - `alpha0 = 1.0, beta0 = 1.0`: Vague prior on variance

3. **Detection Threshold**:
   - Default: 0.8 (conservative, fewer false positives)
   - Aggressive: 0.5 (more sensitive, more false positives)
   - Tune based on cost of false positives vs. missed changes

**Decision**: Use λ = 1/250 for daily bars, vague priors. Start with threshold = 0.8.

**References**:
- Adams & MacKay, "Bayesian Online Changepoint Detection" (2007)
- https://github.com/hildensia/bayesian_changepoint_detection

---

### Task 4: Walk-Forward Validation Design

**Question**: How to structure walk-forward validation for meta-model?

**Research Findings**:

1. **Window Sizes** (from AFML):
   - Training: 252 trading days (1 year)
   - Testing: 63 trading days (1 quarter)
   - Step size: 21 trading days (1 month)

2. **Embargo Period**:
   - Add gap between train and test to prevent leakage
   - Recommended: 5-10 bars (prevents label overlap)

3. **Purging**:
   - Remove overlapping samples from training set
   - Critical for triple barrier labels (span multiple bars)

4. **Evaluation Metrics**:
   - AUC-ROC (primary): >0.6 is acceptable
   - Precision at threshold: optimize for low false positives
   - Brier score: calibration measure

**Decision**: Use 252-bar train, 63-bar test, 5-bar embargo, 21-bar step.

**References**:
- López de Prado, "Advances in Financial Machine Learning", Chapter 7
- Prado, "Walk-Forward Optimization" (QuantResearch blog)

---

### Task 5: Integrated Sizing Formula Derivation

**Question**: How to combine multiple factors in position sizing?

**Research Findings**:

1. **Multiplicative Combination** (Giller):
   - Factors are multiplicative, not additive
   - Each factor acts as a "confidence weight"
   - Formula: size = base * factor1 * factor2 * ... * factorN

2. **Factor Ranges**:
   - Signal magnitude: transformed to [0, 1] via sqrt
   - Meta-confidence: already [0, 1] from predict_proba
   - Regime weight: [0.4, 1.2] based on volatility regime
   - Toxicity penalty: (1 - VPIN) gives [0, 1]

3. **Kelly Fraction**:
   - Full Kelly is too aggressive (ruin probability high)
   - Recommended: 0.25-0.5 of full Kelly
   - 0.5 is standard ("half-Kelly")

4. **Min/Max Size Limits**:
   - Minimum: 0.01 (avoid zero positions)
   - Maximum: 1.0 (never exceed full position)

**Decision**: Use multiplicative formula with 0.5 fractional Kelly. Apply min/max limits.

**References**:
- Graham Giller, "10 Most Important Things" (Desktop articles)
- Ed Thorp, "The Kelly Criterion in Blackjack"

---

### Task 6: mlfinlab License and Python Compatibility

**Question**: Can we use mlfinlab for triple barrier implementation?

**Research Findings**:

1. **License History**:
   - Original: MIT license (open source)
   - 2021: Hudson & Thames changed to proprietary license
   - Current: Requires paid subscription for commercial use

2. **Python Compatibility**:
   - Latest mlfinlab: Python 3.8-3.10 supported
   - Python 3.11/3.12: Compatibility issues reported
   - numba dependency causes JIT compilation errors

3. **Alternatives**:
   - Custom implementation (recommended)
   - fracdiff (10,000x faster frac diff, MIT license)
   - PyPortfolioOpt (portfolio optimization only)

**Decision**: Implement custom triple barrier. Avoid mlfinlab dependency.

**References**:
- https://github.com/hudson-and-thames/mlfinlab/issues
- Hudson & Thames licensing page

---

### Task 7: tick Library for Hawkes (Compatibility Check)

**Question**: Is tick library compatible with Python 3.11+?

**Research Findings**:

1. **Current Status** (2026-01):
   - tick: Last release 2022, Python 3.9 max
   - Python 3.11/3.12: Compilation issues with Cython
   - GitHub issues: Multiple reports of build failures

2. **Alternatives**:
   - Pure Python implementation (slower but compatible)
   - bayesian-optimization (for hyperparameter tuning)
   - Custom Hawkes using numba (10x faster than pure Python)

3. **Already Implemented** (Spec 025):
   - hawkes_ofi.py uses pure Python fallback
   - Works with Python 3.11+
   - Acceptable performance for bar-level data

**Decision**: Already resolved in Spec 025. Use pure Python Hawkes fallback.

**References**:
- https://github.com/X-DataInitiative/tick
- Spec 025 hawkes_ofi.py implementation

---

## Summary of Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Triple Barrier Library | Custom implementation | Licensing + Python 3.11 compatibility |
| Meta-Model Algorithm | RandomForest (sklearn) | Simple, sufficient, already a dependency |
| BOCD Implementation | Custom (Adams & MacKay) | Online algorithm required for live trading |
| Walk-Forward Window | 252 train / 63 test | Standard AFML recommendation |
| Hazard Rate | 1/250 | ~1 regime change per year (daily data) |
| Fractional Kelly | 0.5 | Half-Kelly for safety margin |
| BOCD Threshold | 0.8 | Conservative default, tunable |

## Edge Cases Resolved

1. **Insufficient meta-model training data**: Return default confidence (0.5)
2. **BOCD with non-stationary mean AND variance**: Use Gaussian likelihood with online mean/variance estimation
3. **Triple barrier never hits any barrier**: Return 0 (neutral) or sign of final return
4. **Retrain meta-model without look-ahead**: Use walk-forward with embargo period

## Next Steps

1. Generate data-model.md with entity definitions
2. Generate API contracts
3. Generate quickstart.md with usage examples
4. Proceed to implementation (tasks.md)
