# Alternative Architectures Analysis

## Executive Summary

**BRUTAL TRUTH**: The academic evidence is DAMNING. Simpler strategies with fewer parameters consistently outperform complex optimization schemes across multiple domains:

1. **1/N Portfolio** (DeMiguel et al. 2009): 0 parameters beats 14 optimization models in out-of-sample tests
2. **Simple Trend Following** (AQR): 110+ years of consistent performance with ~3 parameters
3. **Overfitting Evidence**: Each additional parameter increases curve-fitting risk, degrading live performance
4. **Estimation Window**: For 25 assets, need **3000 months** of data for optimization to beat equal weight; for 50 assets, **6000 months**

**Our System**: ~42 tunable parameters across multiple adaptive components. Are we in the "complexity trap"?

---

## Alternatives Analyzed

### 1. Equal Weight (1/N) Portfolio

**Complexity**: 0 parameters

**Key Paper**: DeMiguel, V., Garlappi, L., & Uppal, R. (2009). "Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?" *The Review of Financial Studies*, 22(5), 1915-1953.

**Performance vs Optimized**:
- Tested against 14 optimization models across 7 datasets
- **Result**: "None is consistently better than the 1/N rule in terms of Sharpe ratio, certainty-equivalent return, or turnover"
- Out-of-sample gain from optimal diversification is **more than offset by estimation error**

**Why It Works**:
- **Zero estimation error**: No parameters to estimate = no overfitting
- **Maximum diversification**: Equal risk from all sources
- **Robust**: Works across market regimes without adaptation
- **Low turnover**: Minimal rebalancing costs

**Estimation Window Required**:
- **25 assets**: ~3000 months (~250 years!) for optimization to outperform
- **50 assets**: ~6000 months (~500 years!)
- **Conclusion**: We will literally never have enough data

**Should We Consider**: **YES - SERIOUSLY**

If we're trading multiple assets, a 1/N allocation as a **baseline/benchmark** is mandatory. Any complexity we add MUST justify itself against this dead-simple alternative.

**Evidence Quality**: ⭐⭐⭐⭐⭐
- Published in top-tier finance journal
- 7 different datasets tested
- 110+ years of data in some tests
- Replicated extensively

---

### 2. Fixed Fractional Position Sizing (Kelly Criterion Family)

**Complexity**: 1 parameter (fixed fraction of capital)

**Concept**: Risk a constant percentage of capital per trade (e.g., 2%, 5%, 10%)

**Performance**:
- **Kelly Criterion**: Mathematically optimal growth rate (for known probabilities)
- **Half-Kelly**: Common practical implementation (50% of Kelly fraction)
- **Fixed 2%**: Conservative risk management standard

**Why It Works**:
- **Constant risk exposure**: Automatically scales with account size
- **Geometric growth**: Optimal for long-term compounding
- **Simple**: One parameter to set based on risk tolerance
- **Robust**: Works regardless of market conditions

**Limitations**:
- Requires accurate win rate and payoff ratio estimates
- Full Kelly can be aggressive (large drawdowns)
- Doesn't adapt to changing volatility regimes

**Should We Consider**: **YES - AS BASELINE**

Fixed fractional is the **minimum viable** position sizing. Our adaptive sizing must beat this to justify its complexity.

**Evidence Quality**: ⭐⭐⭐⭐
- Mathematical proof (Kelly 1956)
- Decades of practical use
- Well-understood properties

---

### 3. Risk Parity

**Complexity**: ~3 parameters (target volatility, rebalance frequency, lookback window)

**Concept**: Equalize risk contribution across assets rather than capital allocation

**Performance**:
- **Good environments**: Low correlation regimes, diversified markets
- **Bad environments**: 2020 COVID (-19.5% vs -16.1% for 60/40), 2022 inflation (-significant underperformance)
- **Vulnerability**: Breaks down when stock-bond correlation flips positive

**Why It Sometimes Works**:
- **Better than cap-weighted**: More balanced risk exposure
- **Crisis performance**: Can work in correlation breakdowns (but not always!)
- **Systematic rebalancing**: Forces buying dips, selling rallies

**Why It Fails**:
- **Correlation regime dependence**: Assumes negative stock-bond correlation
- **Estimation error**: Still requires covariance matrix estimation
- **Leverage**: Often uses leverage to equalize returns (amplifies losses)

**Academic Evidence**:
- Adaptive risk parity (with momentum overlay) outperforms static risk parity
- But **still vulnerable** to regime changes
- 2022 showed that "diversification" assumptions can fail spectacularly

**Should We Consider**: **PARTIAL - WITH CAUTION**

Risk parity principles (equal risk contribution) are sound, but:
- Don't assume correlations are stable
- Don't leverage to force returns
- Consider adaptive variants that detect regime changes

**Evidence Quality**: ⭐⭐⭐
- Widely used in industry
- Mixed live performance (great 2008, terrible 2022)
- Regime-dependent

---

### 4. Volatility Targeting (Constant Risk)

**Complexity**: 2-3 parameters (target volatility, lookback window, scaling method)

**Concept**: Scale position size to maintain constant portfolio volatility (e.g., 10% annualized)

**Performance**:
- **Trend following context**: Core component of managed futures strategies
- **AQR evidence**: Improves risk-adjusted returns, reduces tail risk
- **Adaptive positioning**: Automatically reduces size in volatile markets

**Why It Works**:
- **Prevents blowups**: Reduces exposure when volatility spikes
- **Stable Sharpe**: Normalizes returns across regimes
- **Simple calculation**: Just scale by realized/target volatility ratio

**Comparison to Our System**:
- We use ATR-based sizing (essentially volatility targeting)
- But we layer additional complexity on top (Giller scaling, Kelly overlay, etc.)

**Should We Consider**: **YES - ALREADY USING IT**

Volatility targeting is a **core principle** we already follow. Question is whether we need the extra layers.

**Evidence Quality**: ⭐⭐⭐⭐
- AQR research spanning 100+ years
- Standard in managed futures
- Proven crisis performance

---

### 5. Simple Trend Following (AQR Style)

**Complexity**: 3 parameters (lookback period, entry/exit rules, position sizing)

**Key Research**:
- "A Century of Evidence on Trend-Following Investing" (AQR)
- "Time Series Momentum" (Moskowitz, Ooi, Pedersen, 2012)

**Performance**:
- **110+ years** (1880-2015): Consistently profitable
- **Simple rule**: Long if 12-month return > 0, short otherwise
- **Scale by volatility**: Inverse proportional to ex-ante volatility
- **"Smile pattern"**: Best performance in extreme up/down markets

**Why It Works**:
- **Behavioral bias**: Underreaction to news, momentum persistence
- **Risk premium**: Compensation for providing liquidity during trends
- **Crisis alpha**: Positive in extreme market environments
- **Robust**: Works across 38+ markets, 3 asset classes

**Comparison to Our System**:
- We use trend detection (momentum filters)
- But we add: multiple timeframes, regime detection, adaptive parameters, etc.

**Should We Consider**: **YES - AS BENCHMARK**

Simple 12-month momentum is a **mandatory baseline**. Our complexity must beat this.

**Evidence Quality**: ⭐⭐⭐⭐⭐
- 110+ years of data
- Multiple asset classes
- Replicated extensively
- Live performance in managed futures funds

---

### 6. Buy and Hold (Benchmark)

**Complexity**: 0 parameters

**Concept**: Buy the asset and hold indefinitely

**Performance**:
- **Equities (long-term)**: ~7-10% annualized (US stocks, 1900-2020)
- **Zero costs**: No trading, no rebalancing
- **Tax efficient**: No short-term capital gains

**Why It "Works"**:
- **Equity risk premium**: Long-term upward drift
- **Compounding**: No friction from trading
- **Behavioral**: Removes timing mistakes

**When It Fails**:
- **Drawdowns**: -50% to -89% in crashes (no protection)
- **Dead markets**: Japan 1990-2020, many others
- **Sequence risk**: Timing of retirement matters hugely

**Should We Consider**: **YES - AS BASELINE**

Any active strategy must beat buy-and-hold **after costs** and **risk-adjusted**. Many don't.

**Evidence Quality**: ⭐⭐⭐⭐⭐
- Centuries of data
- Simplest possible strategy
- Well-understood properties

---

## Complexity vs Performance Matrix

| Strategy | Parameters | Sharpe (Reported) | MaxDD | Evidence Quality | Live Track Record |
|----------|-----------|-------------------|-------|------------------|-------------------|
| **Our System** | **~42** | **???** | **???** | **Backtest only** | **None** |
| 1/N Portfolio | 0 | ~0.4-0.6 | Varies | ⭐⭐⭐⭐⭐ | Institutional use |
| Fixed Fractional | 1 | Varies | Depends on % | ⭐⭐⭐⭐ | Widespread |
| Simple Trend (AQR) | 3 | 0.77 (1880-2013) | ~20-30% | ⭐⭐⭐⭐⭐ | Managed futures |
| Risk Parity | 3-5 | 0.6-0.8 (pre-2022) | -20% (2022) | ⭐⭐⭐ | Mixed (2022 bad) |
| Vol Targeting | 2-3 | Improves baseline | Reduces tail | ⭐⭐⭐⭐ | Standard practice |
| Buy & Hold (SPY) | 0 | ~0.4 (long-term) | -50% to -89% | ⭐⭐⭐⭐⭐ | Centuries |

---

## Key Findings

### 1. The "1/N Problem" - Optimization is Nearly Impossible

**DeMiguel et al. 2009 showed**:
- For a 25-asset portfolio: Need **3000 months** (~250 years) for optimization to beat equal weight
- For a 50-asset portfolio: Need **6000 months** (~500 years)
- **Reason**: Estimation error in covariance matrix overwhelms optimization gains

**Implication for Our System**:
- We estimate correlations, volatilities, and other parameters from limited data
- Every parameter estimate adds error
- With ~42 parameters, we are **deep in overfitting territory** unless we have centuries of data

### 2. Simple Trend Following Works - And It's Hard to Beat

**AQR's century of evidence**:
- 12-month momentum, inverse volatility scaling: **Sharpe 0.77** over 110+ years
- Works across 38+ markets, 3 asset classes
- **Robust to regime changes** (unlike risk parity)

**Comparison**:
- 3 parameters vs our ~42
- **14x fewer parameters** for proven, century-long performance

### 3. Each Parameter Increases Overfitting Risk

**Academic consensus**:
- "Each additional parameter increases the risk of overfitting" (multiple sources)
- **3-5 parameters**: Good rule of thumb for robust strategies
- **>10 parameters**: High overfitting risk without massive datasets

**Our System**:
- ~42 parameters (estimated)
- **8-14x the "safe" parameter count**
- Requires **extraordinary evidence** to justify

### 4. Complexity Often Degrades Live Performance

**Research findings**:
- Moving average strategy: Sharpe ratio **1.2 → -0.2** in out-of-sample tests (AQR)
- Complex strategies are **more sensitive** to parameter changes
- "If changing a parameter by 5% tanks performance, you're fitting to randomness"

**Warning signs in our system**:
- Multiple adaptive components (each with parameters)
- Regime detection (parameters)
- Multiple scaling laws (parameters)
- Ensemble methods (more parameters)

### 5. Robert Carver's Principle: "Make It Simple and Stick to It"

**Carver's argument** (Former AHL systematic trader):
- "Most people are not as good at trading as they think they are"
- **Cognitive biases** ruin discretionary trading
- **Simple systematic rules** overcome biases
- **Over-complication** is a common failure mode

**Key insight**:
- The value of systematic trading is in **removing human error**, not in complexity
- A simple system you can stick to beats a complex one you abandon

---

## Is Our Complexity Justified?

### The Harsh Reality Check

**Question**: Does our ~42 parameter system outperform simpler alternatives enough to justify the added risk?

**To answer, we need**:
1. **Baseline comparisons**: Run same backtests with 1/N, fixed fractional, simple trend
2. **Out-of-sample tests**: Walk-forward analysis, not in-sample optimization
3. **Parameter sensitivity**: Does 5% change in any parameter tank performance?
4. **Sharpe ratio reality check**: If Sharpe > 2.0, probably overfitting
5. **Regime testing**: Does it work in 2008, 2020, 2022, sideways markets?

### Evidence We DON'T Have Yet

❌ **No comparison to 1/N baseline**
❌ **No comparison to simple trend following**
❌ **No out-of-sample validation**
❌ **No parameter sensitivity analysis**
❌ **No regime breakdown analysis**
❌ **No live trading results**

### What the Academic Evidence Suggests

Based on DeMiguel, AQR, Carver, and overfitting literature:

**LIKELY OUTCOME**: Our complex system will:
1. Show excellent in-sample backtest results (because: overfitting)
2. Degrade significantly in out-of-sample tests (because: estimation error)
3. Underperform simpler baselines in live trading (because: reality)

**WHY**:
- We don't have 250 years of data to estimate 42 parameters
- Estimation error grows with parameter count
- Markets are non-stationary (parameters that worked will stop working)

---

## Recommendations

### 1. **MANDATORY**: Establish Simple Baselines

Before deploying our system, we **MUST** compare against:

1. **Buy and Hold**: SPY/QQQ benchmark
2. **1/N Portfolio**: Equal weight across our asset universe
3. **Fixed 2% Risk**: Simple fractional sizing
4. **Simple Trend**: 12-month momentum + vol targeting (AQR style)

**Test Protocol**:
- Same backtest period
- Same transaction costs
- Same datasets
- Compare: Sharpe, MaxDD, Calmar, turnover

### 2. **CRITICAL**: Simplify Before You Complexify

**Recommendation**: Start with a **minimal viable system**:

```
Core Components (5-7 parameters):
1. Trend detection: 12-month momentum (1 parameter: lookback)
2. Position sizing: Volatility targeting (2 parameters: target vol, lookback)
3. Risk management: Fixed stop-loss (1 parameter: %)
4. Allocation: Equal weight or risk parity (0-2 parameters)
Total: 4-6 parameters
```

**Then**: Add complexity **ONLY IF**:
- Out-of-sample Sharpe improves by >0.1
- Parameter sensitivity tests pass
- Complexity is justified by performance gain

### 3. **REDUCE** Parameter Count Aggressively

**Current system**: ~42 parameters

**Target**: **<10 parameters** for robust live trading

**How**:
- Remove ensemble methods (unless they beat simple averaging)
- Remove adaptive parameters (use fixed lookbacks)
- Remove regime detection (unless it beats simple rules)
- Remove complex scaling (use simple vol targeting)

**Philosophy**:
> "Everything should be made as simple as possible, but not simpler." - Einstein

Our system is currently **NOT as simple as possible**.

### 4. **TESTING**: Walk-Forward, Not In-Sample

**Current approach**: Likely optimized on full dataset

**Required approach**:
1. **Train**: 2015-2018 (estimate parameters)
2. **Validate**: 2019-2020 (choose model)
3. **Test**: 2021-2023 (final out-of-sample)
4. **Walk-forward**: Roll window every 6-12 months

**If test performance << train performance**: We overfit.

### 5. **BENCHMARKING**: DeMiguel Test

**The "1/N Test"**:
1. Run our system on historical data
2. Run 1/N portfolio on same data
3. Compare Sharpe ratios

**If 1/N wins**: Our complexity is **NOT JUSTIFIED**. Scrap it and use equal weight.

**If we win by <0.2 Sharpe**: Still not worth the complexity. Occam's razor says simplify.

**If we win by >0.3 Sharpe**: Maybe justified, but need out-of-sample validation.

### 6. **PHILOSOPHICAL**: Embrace the AQR/Carver Simplicity Doctrine

**Key principles**:
1. **Simple beats complex** (out-of-sample)
2. **Robust beats optimal** (estimation error)
3. **Sticky beats adaptive** (overfitting risk)
4. **Few parameters beat many** (curse of dimensionality)

**Our current system violates ALL of these.**

---

## Specific Components to Question

### Remove or Simplify:

| Component | Current Complexity | Simple Alternative | Justification Needed |
|-----------|-------------------|-------------------|---------------------|
| Giller Scaling | Power-law exponent | Linear or sqrt | >0.1 Sharpe improvement |
| Kelly Criterion | Win rate estimation | Fixed 2% risk | Actual Kelly beat fixed? |
| Regime Detection | ML clustering, multiple params | 200-day SMA regime | >0.1 Sharpe improvement |
| Ensemble Sizing | Multiple methods, averaging | Single method | Ensemble beat best single? |
| Dynamic Stop Loss | ATR-based, adaptive | Fixed 2% stop | Adaptive beat fixed? |
| Correlation Hedging | Matrix estimation, adaptive | None or static | >0.1 Sharpe improvement |

**Test each**: Does the complex version beat the simple version **out-of-sample** by >0.1 Sharpe?

If **NO**: **DELETE IT**.

---

## Alternative Architectures to Test

### Architecture A: "DeMiguel Special" (0 parameters)

```
Components:
- Allocation: 1/N equal weight across assets
- Rebalancing: Monthly (fixed)
- Risk management: None (diversification is the risk management)

Expected Performance:
- Sharpe: ~0.4-0.6 (based on DeMiguel results)
- MaxDD: Depends on assets, but diversified
- Robustness: Maximum (no parameters to overfit)
```

### Architecture B: "AQR Trend Lite" (3 parameters)

```
Components:
1. Trend: 12-month momentum (1 param: lookback)
2. Sizing: Inverse volatility (1 param: vol lookback)
3. Stop: Fixed 2% (1 param: %)

Expected Performance:
- Sharpe: ~0.77 (based on AQR 1880-2013)
- MaxDD: ~20-30%
- Robustness: High (century of evidence)
```

### Architecture C: "Carver Simple System" (5-6 parameters)

```
Components:
1. Trend: EWMAC crossover (2 params: fast/slow)
2. Sizing: Volatility targeting (2 params: target, lookback)
3. Risk: Fixed % stop (1 param)
4. Allocation: Risk parity (1 param: rebal frequency)

Expected Performance:
- Sharpe: TBD (Carver's live results ~0.5-0.7)
- MaxDD: TBD
- Robustness: Good (professional use)
```

### Architecture D: "Our Current System" (~42 parameters)

```
Components:
- Everything we have now

Expected Performance:
- Sharpe: ??? (unknown, no testing yet)
- MaxDD: ???
- Robustness: LOW (high parameter count)
```

---

## The Verdict: What Should We Do?

### Immediate Actions (This Week)

1. **Implement Architecture A (1/N)**: 1 hour of coding
2. **Implement Architecture B (AQR Trend)**: 4-6 hours of coding
3. **Run comparative backtests**: Same period, same costs, same data
4. **Compare results**: Sharpe, MaxDD, Calmar, turnover

**Decision rule**:
- If A or B beats D: **Scrap our complex system, use the simple one**
- If D beats A/B by <0.2 Sharpe: **Still use simple (robustness premium)**
- If D beats A/B by >0.3 Sharpe: **Proceed with caution, run out-of-sample tests**

### Medium-Term Actions (This Month)

1. **Parameter audit**: List ALL parameters, justify each one
2. **Sensitivity analysis**: Change each parameter by ±5%, measure impact
3. **Walk-forward testing**: Out-of-sample validation
4. **Regime testing**: 2008, 2020, 2022, sideways markets
5. **Transaction cost analysis**: Are we churning the portfolio?

### Long-Term Philosophy (Forever)

**Adopt the "Simplicity First" doctrine**:

1. **Start simple**: Always begin with baseline (1/N, simple trend, buy/hold)
2. **Add complexity only if justified**: >0.1 Sharpe improvement, out-of-sample
3. **Prefer robust over optimal**: Estimation error kills optimal strategies
4. **Parameter budget**: Never exceed 10 parameters without extraordinary evidence
5. **Occam's razor**: Simpler explanation (strategy) is usually correct

---

## Final Thoughts: The Complexity Trap

### The Seductive Lie

Complex systems **feel** smarter. They have:
- Sophisticated mathematics (Giller power laws!)
- Adaptive mechanisms (regime detection!)
- Ensemble methods (wisdom of crowds!)
- Academic pedigree (published papers!)

**But the academic evidence is clear**:
- 1/N (0 params) beats 14 optimization models
- Simple trend (3 params) works for 110+ years
- Each parameter adds overfitting risk

### The Hard Truth

We've built a **potentially over-engineered system** with ~42 parameters:
- **No evidence** it beats simple baselines
- **No out-of-sample testing** yet
- **High probability** of overfitting
- **Likely outcome**: Looks great in backtest, fails in live trading

### The Path Forward

**BE HONEST**:
1. Test against simple baselines
2. If we lose, **admit it and simplify**
3. If we win, **prove it's not overfitting** (walk-forward, sensitivity)
4. **Parameter diet**: Cut to <10 parameters

**REMEMBER**:
- Markets don't care about our cleverness
- Simple, robust systems beat complex, optimal ones
- "The gain from optimal diversification is more than offset by estimation error"

### The Ultimate Question

**Can we look ourselves in the mirror and say**:
> "I have **extraordinary evidence** that my 42-parameter system beats a 0-parameter equal-weight portfolio out-of-sample, after costs, in live trading."

**If the answer is NO**: We have work to do.

**If the answer is YES**: We need to publish a paper, because we've overturned decades of academic research.

---

## Sources

### Academic Papers

1. **DeMiguel, V., Garlappi, L., & Uppal, R. (2009)**. "Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?" *The Review of Financial Studies*, 22(5), 1915-1953.
   - [Paper Link](https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901)

2. **Moskowitz, T., Ooi, Y. H., & Pedersen, L. H. (2012)**. "Time Series Momentum." *Journal of Financial Economics*, 104(2), 228-250.
   - [AQR - A Century of Evidence on Trend-Following](https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing)

3. **AQR Capital Management**. "Understanding Risk Parity"
   - [White Paper](https://www.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Understanding-Risk-Parity.pdf)

### Industry Sources

4. **Robert Carver**. *Systematic Trading: A unique new method for designing trading and investing systems*
   - [Book on Amazon](https://www.amazon.com/Systematic-Trading-designing-trading-investing/dp/0857194453)
   - [Interview: Making a Simple System and Sticking To It](https://www.harriman-house.com/press/full/2867)

### Web Resources on Overfitting

5. **LuxAlgo**. "What Is Overfitting in Trading Strategies?"
   - [Article](https://www.luxalgo.com/blog/what-is-overfitting-in-trading-strategies/)

6. **TradersPost**. "Understanding Overfitting in Trading Strategy Development"
   - [Article](https://blog.traderspost.io/article/understanding-overfitting-in-trading-strategy-development)

7. **Quantlane**. "How to avoid overfitting trading strategies"
   - [Article](https://quantlane.com/blog/avoid-overfitting-trading-strategies/)

### Additional Reading

8. **Risk Parity Performance**:
   - [CAIA: Risk Parity Not Performing? Blame the Weather](https://caia.org/blog/2024/01/02/risk-parity-not-performing-blame-weather)
   - [Adaptive Risk Parity Strategies (Mathematical Modeling)](https://drpress.org/ojs/index.php/mmaa/article/view/26089)

9. **Simple vs Complex Trading**:
   - [QuantifiedStrategies: Simple Vs. Complex Trading Strategies](https://www.quantifiedstrategies.com/simple-vs-complex-trading-strategies/)
   - [Brockmann: Myth - Simple Strategies Can't Outperform](https://www.brockmann.com/myth-simple-strategies-cant-outperform-complex-ones/)

10. **Trend Following Research**:
    - [AQR: Trend Following](https://www.aqr.com/Insights/Trend-Following)
    - [Quantpedia: Trend-Following Effect in Stocks](https://quantpedia.com/strategies/trend-following-effect-in-stocks)

---

**Document Version**: 1.0
**Date**: 2026-01-04
**Author**: Claude (Analysis Agent)
**Status**: CRITICAL REVIEW REQUIRED

**Next Steps**:
1. Implement simple baselines (A, B, C)
2. Run comparative backtests
3. Face the truth about our complexity
4. Simplify or justify every parameter
