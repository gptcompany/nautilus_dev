# Baseline Comparison: Simple vs Complex

**Date**: 2026-01-04
**Status**: CRITICAL VALIDATION REQUIRED
**Purpose**: Compare Adaptive Control Framework against simple baselines to justify complexity

---

## Executive Summary

**THE BRUTAL QUESTION**: Can we justify ~42 parameters when 1/N (0 params) beats 14 optimization models?

**Our System**:
- SOPS + Giller sizing: ~8 parameters
- Thompson Sampling + Particle Filter: ~6 parameters
- IIR/Spectral regime detection: ~8 parameters
- Multi-dimensional consensus: ~5 parameters
- Meta-portfolio coordination: ~15 parameters
- **TOTAL: ~42 tunable parameters**

**Academic Evidence**:
- DeMiguel et al. (2009): Need **3000+ months** (250 years) for optimization to beat equal weight
- Bailey & Lopez de Prado: Parameter count limits at ~3-5 for robust strategies
- AQR: Simple trend following (3 params) = 110 years validated performance

**VERDICT**: We are **8-14x over the safe parameter budget** without extraordinary evidence.

**RECOMMENDATION**: **WAIT** - Run baseline comparisons BEFORE deployment. If simple beats complex, simplify ruthlessly.

---

## Baseline Implementations

### 1. Fixed Fractional (FF)

**Formula**:
```python
position_size = f * equity / risk_per_trade
where f = 0.02 (2% risk per trade)
```

**Parameters**: 1 (f = fixed fraction)

**Pros**:
- Trivial to implement (5 lines of code)
- Constant risk exposure across account size
- Geometric growth (Kelly-like for known p, b)
- Zero estimation error
- Centuries of use in professional trading

**Cons**:
- No volatility adaptation
- No regime awareness
- Requires accurate risk_per_trade estimation
- Can be aggressive if f too high

**Expected Performance**:
- Sharpe: 0.6-1.0 (depends on signal quality)
- MaxDD: 15-25% (with f=0.02)
- Robustness: HIGH (single parameter, no overfitting)

**When It Wins**:
- Stationary markets (stable volatility)
- High-quality signals (win rate >55%)
- Low transaction costs

**Implementation**:
```python
class FixedFractionalSizer:
    def __init__(self, fraction: float = 0.02):
        self.f = fraction

    def size(self, equity: float, risk_per_trade: float) -> float:
        return self.f * equity / risk_per_trade
```

---

### 2. Equal Weight (1/N)

**Formula**:
```python
weight_i = 1 / N  for all strategies i
```

**Parameters**: 0

**Pros**:
- **ZERO estimation error** (no parameters to overfit)
- Maximum diversification benefit
- Robust to regime changes
- Low turnover (minimal rebalancing)
- DeMiguel: Beats 14 optimization models out-of-sample

**Cons**:
- Ignores strategy quality differences
- No adaptation to performance
- Allocates to losers equally with winners
- Can underperform in concentrated alpha environments

**Expected Performance**:
- Sharpe: 0.4-0.6 (DeMiguel dataset)
- MaxDD: Varies by asset basket
- Robustness: **MAXIMUM** (impossible to overfit)

**When It Wins**:
- Multi-strategy portfolios (>5 strategies)
- Limited historical data (<3000 months)
- Non-stationary markets (optimization breaks down)
- High estimation uncertainty

**DeMiguel Key Finding**:
> "For a 25-asset portfolio, need **3000 months** for optimization to beat 1/N.
> For 50 assets, need **6000 months**."

**Implementation**:
```python
class EqualWeightAllocator:
    def allocate(self, strategies: List[str]) -> Dict[str, float]:
        n = len(strategies)
        return {s: 1.0 / n for s in strategies}
```

---

### 3. Kelly Classic

**Formula**:
```python
f_kelly = (p * b - q) / b
where:
    p = win_rate
    b = avg_win / avg_loss
    q = 1 - p
```

**Parameters**: 2 (estimated p, b from historical data)

**Pros**:
- Mathematically optimal for known p, b (maximizes log growth)
- Self-scaling (reduces size as uncertainty increases)
- Theoretical foundation (Kelly 1956, Thorp 2011)

**Cons**:
- **Estimation error dominates**: Overestimate p by 10% → catastrophic drawdowns
- Assumes stationary win rate (markets are non-stationary)
- Full Kelly can have >50% drawdowns
- Requires fractional Kelly (f_actual = 0.25 × f_kelly) for robustness

**Expected Performance**:
- Sharpe: 0.8-1.2 (with fractional Kelly, accurate estimates)
- MaxDD: 20-40% (full Kelly), 10-20% (fractional)
- Robustness: MEDIUM (sensitive to p, b estimation)

**When It Wins**:
- Long track record (>1 year) for accurate p, b estimation
- Stationary environment (stable win rate)
- Used as **scaling layer** on top of base sizing (not standalone)

**When It Fails**:
- Non-stationary markets (p changes regime-to-regime)
- Limited data (estimation uncertainty high)
- Fat-tailed distributions (Kelly assumes Gaussian)

**Implementation**:
```python
class KellySizer:
    def __init__(self, lookback: int = 90, kelly_fraction: float = 0.25):
        self.lookback = lookback
        self.kelly_fraction = kelly_fraction
        self._returns = deque(maxlen=lookback)

    def update(self, win: bool, pnl: float):
        self._returns.append((win, pnl))

    def size(self) -> float:
        if len(self._returns) < 20:
            return 0.02  # Default to 2% until enough data

        wins = [pnl for win, pnl in self._returns if win]
        losses = [abs(pnl) for win, pnl in self._returns if not win]

        p = len(wins) / len(self._returns)
        b = np.mean(wins) / np.mean(losses) if losses else 1.0
        q = 1 - p

        f_kelly = (p * b - q) / b
        f_kelly = max(0, min(0.5, f_kelly))  # Clamp to [0, 0.5]

        return self.kelly_fraction * f_kelly
```

---

### 4. Volatility Targeting

**Formula**:
```python
position_size = (target_vol / realized_vol) * base_size
where:
    target_vol = 0.10 (10% annualized)
    realized_vol = sqrt(252) * std(returns, lookback)
```

**Parameters**: 2 (target_vol, lookback)

**Pros**:
- Prevents blowups (reduces exposure in volatile markets)
- Stabilizes Sharpe ratio across regimes
- Simple calculation (rolling std)
- AQR: Standard in managed futures, 110+ years evidence
- **Already part of our system** (ATR-based sizing)

**Cons**:
- Backward-looking (uses historical vol, not forward)
- Can whipsaw in regime transitions
- Requires lookback choice (parameter)

**Expected Performance**:
- Sharpe: Improves baseline by 0.1-0.2
- MaxDD: Reduces tail risk by 20-30%
- Robustness: HIGH (proven over century)

**When It Wins**:
- Volatile markets (crypto, leveraged instruments)
- Crisis periods (2008, 2020 COVID)
- Trend-following strategies (momentum)

**AQR Key Finding**:
> "Volatility scaling is **core** to managed futures success over 100+ years.
> Improves risk-adjusted returns without complex optimization."

**Implementation**:
```python
class VolatilityTargeter:
    def __init__(self, target_vol: float = 0.10, lookback: int = 20):
        self.target_vol = target_vol
        self.lookback = lookback
        self._returns = deque(maxlen=lookback)

    def update(self, return_value: float):
        self._returns.append(return_value)

    def scale_factor(self) -> float:
        if len(self._returns) < 10:
            return 1.0

        realized_vol = np.std(self._returns) * np.sqrt(252)
        if realized_vol < 1e-10:
            return 1.0

        return self.target_vol / realized_vol
```

---

## Comparison Matrix

| Metric | FF (1p) | 1/N (0p) | Kelly (2p) | VolTarget (2p) | **Ours (42p)** |
|--------|---------|----------|------------|----------------|----------------|
| **Parameters** | 1 | 0 | 2 | 2 | **~42** |
| **Overfitting Risk** | LOW | ZERO | MED | LOW | **HIGH** |
| **Expected OOS Decay** | 0% | 0% | 20-40% | 5-10% | **40-60%?** |
| **Adaptability** | NONE | NONE | LOW | MED | **HIGH** |
| **Complexity** | TRIVIAL | TRIVIAL | LOW | LOW | **HIGH** |
| **Sample Size Needed** | 10 trades | 0 | 90 days | 20 days | **???** |
| **Transaction Costs** | LOW | VERY LOW | MED | MED | **HIGH?** |
| **Regime Robustness** | MED | HIGH | LOW | MED | **UNKNOWN** |
| **Live Track Record** | Centuries | Decades | Decades | Century | **NONE** |
| **Evidence Quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **⭐ (backtest only)** |

---

## Statistical Analysis

### Required Sample Size (Bailey & Lopez de Prado)

**Rule**: 10:1 ratio of samples to parameters for robust estimation.

| Method | Parameters | Required Months | Years | Available? |
|--------|-----------|-----------------|-------|------------|
| 1/N | 0 | 0 | 0 | ✅ Always works |
| Fixed Fractional | 1 | 10 | <1 | ✅ Yes |
| Kelly Classic | 2 | 20 | 2 | ✅ Yes |
| Vol Targeting | 2 | 20 | 2 | ✅ Yes |
| **Our System** | **~42** | **420** | **35** | **❌ NO** |

**Crypto Data Available**: ~5 years (60 months) for most pairs.

**Implications**:
- We have **14% of required sample size** (60/420)
- **High probability** of overfitting to noise
- OOS Sharpe degradation expected: **40-60%**

---

### DeMiguel Multiple Testing Penalty

**Finding**: Testing N strategies inflates Sharpe by factor of √(log N).

**Our Gap Analysis** (from specs/028-validation/gap_analysis.md):
- Tested 6 position sizing methods (SOPS, Kelly, Fixed, Vol-scaled, etc.)
- Reported SOPS Sharpe: 1.85
- **Deflated Sharpe** (correcting for selection bias):

```python
N_trials = 6
deflation_factor = 1 / sqrt(log(N_trials))
                 = 1 / sqrt(1.79)
                 = 0.75

DSR = 1.85 × 0.75 = 1.39
```

**Conclusion**: True out-of-sample Sharpe likely **1.4, not 1.85** (25% lower).

---

### Probability of OOS Failure

Using Wiecki et al. (2016) findings from 888 Quantopian algorithms:

> "Median OOS Sharpe = **50% of backtest Sharpe**"

**Our System**:
- Backtest Sharpe (deflated): 1.39
- Expected OOS Sharpe: **0.7 (50% decay)**
- Baseline Fixed Fractional: **0.9** (from literature)

**Probability our system underperforms simple baseline**: **>50%**

---

## Key Questions

### 1. Can we prove our system > 1/N with available data?

**Answer**: **NO**

- Need 3000 months for 25-asset optimization to beat 1/N (DeMiguel)
- We have 60 months (~2% of required)
- Even if backtest shows superiority, **estimation error dominates**

---

### 2. What's the OOS Sharpe decay estimate?

**Answer**: **40-60% degradation expected**

**Evidence**:
- Wiecki: Median OOS = 50% of backtest
- Bailey: Parameter count penalty
- Our system: 42 params, 60 months data
- **Best case**: OOS Sharpe = 1.4 × 0.5 = **0.7**
- **Worst case**: OOS Sharpe = **0.3 (below risk-free rate)**

---

### 3. Is complexity justified by performance?

**Answer**: **NOT YET PROVEN**

**Required Evidence** (MISSING):
- ❌ Walk-forward validation (12+ windows)
- ❌ Regime-conditional performance (BULL/BEAR/SIDEWAYS)
- ❌ Transaction cost analysis (turnover × 5bps)
- ❌ Parameter sensitivity (change ±5%, measure impact)
- ❌ Comparison to simple baselines (same data, same costs)
- ❌ Live trading results (>6 months)

**Until we have this evidence**: Complexity is **UNJUSTIFIED**.

---

## Recommendations

### GO: Deploy Simple Baselines First

**Phase 1**: Implement and test simple alternatives (THIS WEEK)

1. **Fixed Fractional (f=0.02)**: 1 hour implementation
2. **Volatility Targeting**: 2 hours implementation
3. **1/N Multi-Strategy**: 30 minutes implementation
4. **Kelly Classic (fractional)**: 3 hours implementation

**Run all on SAME backtest data** with SAME transaction costs (5 bps).

---

### WAIT: Validate Before Full Deployment

**Required validations** (THIS MONTH):

1. **Deflated Sharpe Ratio**: Report DSR, not raw Sharpe
2. **Walk-Forward Testing**: 12 non-overlapping windows (4 months each)
3. **Regime Breakdown**: Performance in BULL/BEAR/SIDEWAYS (separately)
4. **Transaction Cost Model**: Include turnover × cost
5. **Parameter Sensitivity**: ±5% change for each of 42 params

**Decision Rule**:
```
IF (complex_DSR - simple_Sharpe) > 0.3 AND all_validations_pass:
    → Proceed with complex system
ELSE:
    → Use simple baseline
```

---

### STOP: Red Flags

**DO NOT DEPLOY** our 42-parameter system if:

1. **1/N beats us out-of-sample** (DeMiguel test fails)
2. **Fixed fractional (2%) beats us** after transaction costs
3. **Parameter sensitivity fails**: Any ±5% change drops Sharpe >20%
4. **Regime instability**: Negative Sharpe in any regime OOS
5. **Turnover explosion**: >500% annual turnover (costs eat alpha)

---

## Alternative Architectures to Test

### Architecture A: "DeMiguel Special" (0 parameters)

**Components**:
- Allocation: 1/N equal weight across all strategies
- Rebalancing: Monthly (fixed)
- Risk management: Diversification only

**Expected Performance**:
- Sharpe: 0.4-0.6
- MaxDD: 20-30%
- Robustness: **MAXIMUM**

**Code**:
```python
def equal_weight_allocator(strategies: List[str]) -> Dict[str, float]:
    n = len(strategies)
    return {s: 1.0 / n for s in strategies}
```

---

### Architecture B: "AQR Trend Lite" (3 parameters)

**Components**:
1. **Trend**: 12-month momentum (1 param: lookback)
2. **Sizing**: Inverse volatility (1 param: vol lookback)
3. **Stop**: Fixed 2% (1 param)

**Expected Performance**:
- Sharpe: 0.77 (AQR 1880-2013 dataset)
- MaxDD: 20-30%
- Robustness: **HIGH** (110+ years evidence)

**Code**:
```python
class SimpleTrendSystem:
    def __init__(self, lookback: int = 252, vol_lookback: int = 20, stop_pct: float = 0.02):
        self.lookback = lookback
        self.vol_lookback = vol_lookback
        self.stop_pct = stop_pct

    def signal(self, prices: List[float]) -> float:
        # 12-month momentum
        if len(prices) < self.lookback:
            return 0.0
        ret_12m = (prices[-1] / prices[-self.lookback]) - 1
        return 1.0 if ret_12m > 0 else -1.0

    def size(self, signal: float, prices: List[float]) -> float:
        # Inverse volatility scaling
        returns = np.diff(prices[-self.vol_lookback:]) / prices[-self.vol_lookback:-1]
        vol = np.std(returns)
        target_vol = 0.10
        return signal * (target_vol / vol) if vol > 0 else 0.0
```

---

### Architecture C: "Fixed Fractional + Vol Target" (2 parameters)

**Components**:
1. **Base sizing**: Fixed 2% risk
2. **Vol scaling**: Target 10% annualized

**Expected Performance**:
- Sharpe: 0.8-1.1
- MaxDD: 15-20%
- Robustness: **HIGH**

**Code**:
```python
class HybridSizer:
    def __init__(self, base_fraction: float = 0.02, target_vol: float = 0.10):
        self.base_fraction = base_fraction
        self.target_vol = target_vol

    def size(self, equity: float, risk_per_trade: float, realized_vol: float) -> float:
        base_size = self.base_fraction * equity / risk_per_trade
        vol_scale = self.target_vol / realized_vol if realized_vol > 0 else 1.0
        return base_size * vol_scale
```

---

### Architecture D: "Our Current System" (42 parameters)

**Components**:
- SOPS + Giller + TapeSpeed (8 params)
- Thompson Sampling (6 params)
- Particle Filter (6 params)
- IIR Regime (8 params)
- Multi-dimensional consensus (5 params)
- Meta-portfolio (15 params)

**Expected Performance**:
- Sharpe: ??? (unknown, no OOS validation)
- MaxDD: ???
- Robustness: **LOW** (high parameter count)

**Status**: **UNVALIDATED**

---

## The Verdict: What Should We Do?

### Immediate Actions (THIS WEEK)

1. ✅ **Implement Architecture A (1/N)**: 30 minutes
2. ✅ **Implement Architecture B (AQR Trend)**: 4 hours
3. ✅ **Implement Architecture C (FF + Vol)**: 2 hours
4. ✅ **Run comparative backtests**: Same period, same costs, same data
5. ✅ **Report results**: Sharpe, MaxDD, Calmar, turnover

**Decision Rule**:
```
IF (Architecture_A OR B OR C) beats Architecture_D:
    → USE SIMPLE BASELINE
ELIF Architecture_D beats baselines by <0.2 Sharpe:
    → USE SIMPLE (robustness premium)
ELIF Architecture_D beats baselines by >0.3 Sharpe:
    → Proceed to validation phase (walk-forward, etc.)
ELSE:
    → ABANDON complex system, research alternatives
```

---

### Medium-Term Actions (THIS MONTH)

**If complex system survives baseline comparison**:

1. **Parameter Audit**: List all 42 params, justify each
2. **Sensitivity Analysis**: Change each ±5%, measure impact
3. **Walk-Forward Testing**: 12 windows, expanding train set
4. **Regime Testing**: 2008, 2020, 2022, sideways markets
5. **Transaction Cost Analysis**: Turnover × 5 bps slippage
6. **Deflated Sharpe Ratio**: Report DSR, not raw Sharpe

**If ANY test fails**: Simplify or abandon.

---

### Long-Term Philosophy (FOREVER)

**Adopt "Simplicity First" Doctrine**:

1. **Start simple**: Always begin with baseline (1/N, trend, buy/hold)
2. **Add complexity ONLY if justified**: >0.3 Sharpe improvement OOS
3. **Prefer robust over optimal**: Estimation error kills optimal strategies
4. **Parameter budget**: Never exceed 10 without extraordinary evidence
5. **Occam's razor**: Simpler explanation (strategy) is usually correct

**The DeMiguel Principle**:
> "The gain from optimal diversification is **more than offset** by estimation error."

---

## Final Thoughts: The Complexity Trap

### The Seductive Lie

**Complex systems FEEL smarter**:
- Sophisticated mathematics (Giller power laws!)
- Adaptive mechanisms (regime detection!)
- Ensemble methods (particle filters!)
- Academic pedigree (published papers!)

**But the evidence is BRUTAL**:
- 1/N (0 params) beats 14 optimization models
- Simple trend (3 params) works for 110+ years
- Each parameter adds overfitting risk
- OOS Sharpe decay = 40-60% typical

---

### The Hard Truth

We've built a **potentially over-engineered system** with ~42 parameters:
- ❌ No evidence it beats simple baselines
- ❌ No out-of-sample testing yet
- ❌ High probability of overfitting (14% of required sample)
- ❌ Likely outcome: Great backtest, fails live

**Probability of Failure**: **>50%** (Wiecki et al.)

---

### The Path Forward

**BE HONEST**:
1. Test against simple baselines
2. If we lose, **admit it and simplify**
3. If we win, **prove it's not overfitting** (walk-forward, sensitivity)
4. **Parameter diet**: Cut to <10 parameters

**REMEMBER**:
- Markets don't care about our cleverness
- Simple, robust systems beat complex, optimal ones
- "The gain from optimization is offset by estimation error" (DeMiguel)

---

### The Ultimate Question

**Can we look ourselves in the mirror and say**:

> "I have **extraordinary evidence** that my 42-parameter system beats a 0-parameter equal-weight portfolio out-of-sample, after costs, in live trading."

**If NO**: We have work to do.
**If YES**: We need to publish a paper (we've overturned decades of research).

---

## Implementation Checklist

### Phase 1: Baselines (This Week)

- [ ] Implement Fixed Fractional (1 param)
- [ ] Implement Equal Weight (0 params)
- [ ] Implement Kelly Classic (2 params)
- [ ] Implement Vol Targeting (2 params)
- [ ] Run all on same backtest data
- [ ] Include transaction costs (5 bps)
- [ ] Report: Sharpe, MaxDD, Calmar, turnover

---

### Phase 2: Validation (This Month)

- [ ] Deflated Sharpe Ratio calculation
- [ ] Walk-forward testing (12 windows)
- [ ] Regime-conditional performance
- [ ] Parameter sensitivity analysis
- [ ] Transaction cost impact
- [ ] Comparison report (complex vs simple)

---

### Phase 3: Decision (End of Month)

- [ ] If simple wins → Deploy simple, archive complex
- [ ] If complex wins by <0.2 Sharpe → Deploy simple (robustness)
- [ ] If complex wins by >0.3 Sharpe → Proceed to live paper trading
- [ ] Document decision and rationale

---

## Sources

### Academic Papers

1. **DeMiguel, V., Garlappi, L., & Uppal, R. (2009)**. "Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?" *The Review of Financial Studies*, 22(5), 1915-1953.

2. **Bailey, D. & Lopez de Prado, M. (2014)**. "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality" *Journal of Portfolio Management*, 40(5), 94-107.

3. **Moskowitz, T., Ooi, Y. H., & Pedersen, L. H. (2012)**. "Time Series Momentum." *Journal of Financial Economics*, 104(2), 228-250.

4. **Wiecki, T. et al. (2016)**. "All That Glitters Is Not Gold: Comparing Backtest and Out-of-Sample Performance on a Large Cohort of Trading Algorithms". *Journal of Investment*, 25(3), 69-80.

### Web Resources

5. **AQR Capital Management**. "A Century of Evidence on Trend-Following Investing"
   https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing

6. **Robert Carver**. *Systematic Trading: A unique new method for designing trading and investing systems*

---

**Document Version**: 1.0
**Last Updated**: 2026-01-04
**Next Review**: Before any live deployment

**Critical Path**:
1. Implement baselines (1 week)
2. Run comparisons (1 week)
3. Make GO/WAIT/STOP decision (end of month)
