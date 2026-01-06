# Counter-Evidence: Practitioner Failures

## Executive Summary

Analysis of real-world algorithmic trading failures reveals **recurring failure patterns** that directly threaten adaptive trading systems like ours:

**Top 5 Killer Patterns**:
1. **Crowded Trades** - Similar quant strategies converge, liquidity evaporates during unwind
2. **Overfitting/Curve Fitting** - Backtest heroes, live trading zeros
3. **Regime Blindness** - Models trained on one regime, break in the next
4. **Leverage Amplification** - Small model errors → catastrophic losses with leverage
5. **Execution Reality Gap** - Slippage, latency, partial fills ignored in backtests

**Critical Finding**: Most failures are NOT from bad theory but from **implementation gaps** between backtest and reality. Systems that "work in theory" fail in practice due to:
- Unrealistic execution assumptions
- Insufficient stress testing for black swans
- Over-reliance on historical patterns
- Ignoring liquidity/market impact

**Relevance to Our System**: Our Adaptive Control Framework is **vulnerable to 4 of 5 patterns**. Position sizing and regime detection are our highest-risk components.

---

## Failure Stories

### 1. Long-Term Capital Management (LTCM) - 1998

**Type**: Institutional Quant Fund (Nobel Prize winners on team)

**What Failed**:
- Convergence arbitrage strategies based on mean reversion
- $125 billion leveraged positions (30:1 ratio)
- Value-at-Risk (VaR) models failed to predict extreme moves

**Root Cause**:
- **Model Risk**: Assumed future would resemble past (normality assumption)
- **Liquidity Risk**: Positions too large to exit during crisis
- **Tail Risk**: VaR models failed to capture "black swan" events (Russian default)
- **Leverage**: 30:1 leverage turned small losses into $4.6B wipeout

**Warning Signs**:
- Returns declining (43% in 1995 → 17% in 1997)
- Increasing leverage to maintain returns
- Concentrated bets on convergence trades
- Markets becoming "irrationally" divergent (flight to quality)

**Lesson**:
> "Capital is only as patient as its least patient provider. Lenders lose patience precisely when funds need them most—in times of crisis."

Quantitative models cannot account for unprecedented market behavior. Historical data is a poor predictor during regime shifts.

**Relevance to Us**: **HIGH**
- Our adaptive sizing uses historical volatility/drawdown → LTCM shows this fails during tail events
- Regime detection assumes finite regime space → what if new regime emerges?
- Liquidity assumptions in backtests may not hold during stress

**Mitigation**:
- Hard caps on leverage regardless of model confidence
- Stress test for 3-sigma+ events (not just 2-sigma)
- Emergency liquidity reserves (never fully deploy capital)
- Circuit breakers independent of model signals

---

### 2. Knight Capital - August 1, 2012

**Type**: Market Maker / High-Frequency Trading Firm

**What Failed**:
- Software deployment error (7 of 8 servers updated, 1 retained old code)
- Dormant "Power Peg" feature from 2003 reactivated
- Executed 4 million trades in 45 minutes, acquiring $7.65B unintended positions

**Root Cause**:
- **Deployment Failure**: No rollback testing, inconsistent server updates
- **Flag Reuse**: Reused flag bit accidentally triggered old code path
- **No Kill Switch**: No documented incident response procedures
- **Alert Fatigue**: 97 warning emails at 8:01am ignored (not designed for high-priority alerts)
- **Wrong Fix**: Reverted ALL servers to bad code instead of fixing one server

**Warning Signs**:
- 97 warning emails before market open (8:01am)
- NYSE alerted Knight's CIO early in the event
- No automated circuit breaker triggered despite massive volume anomaly

**Lesson**:
> "It took only ONE defect in a trading algorithm to lose $440M in 30 minutes—three times annual earnings."

Operational risk (deployment, testing, incident response) can exceed model risk.

**Relevance to Us**: **MEDIUM**
- We're not HFT, so 45-minute window is catchable
- BUT: Do we have kill switches? Deployment verification? Alert systems?
- Can we detect "unintended behavior" in live trading before catastrophic loss?

**Mitigation**:
- Pre-deployment validation (sandbox testing with production-like data)
- Automated kill switches triggered by volume/PnL anomalies
- Phased rollouts (canary deployments)
- Real-time monitoring with actionable alerts
- Documented incident response playbook

---

### 3. Quant Quake - August 6-9, 2007

**Type**: Quantitative Long/Short Equity Hedge Funds (Industry-Wide)

**What Failed**:
- Market-neutral statistical arbitrage strategies
- Renaissance Technologies: -8.7% in one month
- Highbridge Statistical Opportunities: -18% in 8 days
- Goldman Sachs Global Equity Opportunities: -30% in one week

**Root Cause**:
- **Crowded Trades**: Too many quants running similar mean-reversion strategies
- **Forced Liquidation**: One large fund (likely multi-strat) hit margin call, unwound positions
- **Contagion**: Unwind caused prices to move against ALL similar strategies simultaneously
- **Liquidity Withdrawal**: Market makers pulled back, amplifying price impact
- **Common Factors**: "Ex-ante unobserved" common factors linked fund returns

**Warning Signs**:
- Unwinding began in **July 2007** (detectable in advance)
- Subprime mortgage crisis created margin pressure across funds
- Strategies had been profitable for years, attracted massive capital (overcrowding)

**Lesson**:
> "The crowded trade overwhelmed market fundamentals."

When quant strategies attract too much capital, their own trading becomes the dominant market signal, creating unstable feedback loops.

**Relevance to Us**: **HIGH**
- If our regime detection becomes popular (e.g., via open-source), we face crowding risk
- Adaptive position sizing assumes our trades don't impact price → false for crowded strategies
- "Diversification" across assets doesn't help if everyone uses same entry/exit signals

**Mitigation**:
- Monitor for strategy crowding (compare our signals to market-wide behavior)
- Capacity limits (don't scale beyond liquidity threshold)
- Proprietary signal tweaks (avoid pure textbook implementations)
- Stagger entries/exits to avoid telegraphing intent

---

### 4. Quantopian Shutdown - 2020

**Type**: Crowdsourced Quant Platform (300,000 users, backed by Steve Cohen)

**What Failed**:
- Hedge fund consistently underperformed
- User-generated strategies failed out-of-sample
- Crowdsourced alpha didn't scale

**Root Cause**:
- **Overfitting Epidemic**: 12 million backtests, most curve-fitted
- **Research from Quantopian (2016)**: "Backtest performance metrics offer little value in predicting out-of-sample performance"
- **Unrealistic Constraints**: Required market-neutral strategies (high Type-II error, rejected good strategies)
- **Incentive Misalignment**: Users optimized for backtest leaderboard, not real performance
- **Alpha Decay**: Strategies that worked were quickly arbitraged away

**Warning Signs**:
- Quantopian's own 2016 paper warned backtest performance doesn't predict live results
- Fund returns declining despite access to thousands of strategies
- Investors pulled money in early 2020

**Lesson**:
> "You can't crowdsource alpha. The difference between research and data mining is that a researcher has an idea to go with the data."

Strategies without theoretical foundation are curve-fitted noise.

**Relevance to Us**: **MEDIUM-HIGH**
- Our adaptive system has MANY parameters (regime detection thresholds, sizing formulas)
- Risk: We could be "fitting" to historical regime transitions, not capturing true dynamics
- Question: Can we explain WHY each component works, or just that it "worked in backtest"?

**Mitigation**:
- **Hypothesis-driven development**: Every parameter must have theoretical justification
- Walk-forward testing (not just out-of-sample, but FUTURE out-of-sample)
- Ensemble approaches (if one model fails, others compensate)
- Minimal parameter tuning (prefer robust defaults over optimized)

---

### 5. COVID-19 Crash - March 2020

**Type**: Industry-Wide Algo/HFT Failures

**What Failed**:
- Algorithms misjudged asset values during unprecedented volatility
- HFT liquidity providers withdrew, creating "phantom liquidity"
- VIX hit record high on March 16, 2020
- Multiple trading halts as algos adapted to new regime

**Root Cause**:
- **Regime Shift Speed**: Fastest bear market in U.S. history (algos couldn't adapt)
- **Liquidity Illusion**: HFTs provide liquidity under normal conditions, withdraw during stress
- **Volatility Clustering**: Algorithms trained on "normal" vol ranges failed with 5-10x spikes
- **Correlation Breakdown**: Diversification failed as correlations approached 1.0

**Warning Signs**:
- WHO pandemic declaration (January 30, 2020)
- China lockdowns (late January)
- Italy lockdowns (March 9)
- Observable warning period, but SPEED of crash was unprecedented

**Lesson**:
> "Algorithms did not cause the mess, but they were not very helpful in March."

Algorithms trained on incremental regime shifts fail during discontinuous jumps.

**Relevance to Us**: **VERY HIGH**
- Our regime detection assumes regime transitions are detectable before full onset
- Position sizing based on historical vol → what if vol spikes 10x overnight?
- Adaptive control assumes TIME to adapt → COVID allowed days, not weeks

**Mitigation**:
- **Tail hedges**: Always maintain protective positions (not just stop-losses)
- **Vol-of-vol monitoring**: Detect acceleration in volatility changes (2nd derivative)
- **Manual override capability**: Human can force "crisis mode" regardless of model
- **Stress test for discontinuous jumps**: Don't just test gradual regime shifts

---

### 6. Summer 2025 Quant Wobble

**Type**: Long/Short Equity Quant Funds (Recent)

**What Failed**:
- Goldman Sachs prime services estimated quant equity managers lost 4.2% (June-July 2025)
- Momentum stocks underperformed (unusual)
- Heavily shorted stocks outperformed ("junk rally")
- Profitable stocks underperformed

**Root Cause**:
- **Factor Decay**: Value and momentum signals losing effectiveness (per Goldman Sachs)
- **Crowding**: More quant investors managing more assets → diminishing alpha
- **Regime Anomaly**: Markets behaved opposite to historical factor patterns

**Warning Signs**:
- Steady daily losses over 6+ weeks (not sudden crash)
- Factor performance inversion (momentum/value reversals)

**Lesson**:
> "While quantitative algorithms may work for a while, even for a long while, eventually, they all just completely blow up."

Factors that worked for YEARS can suddenly reverse. Alpha half-life is shortening.

**Relevance to Us**: **HIGH**
- Our system assumes certain market relationships (vol clustering, trend persistence, mean reversion)
- What if these relationships break down?
- Are we monitoring for "factor decay" in our signals?

**Mitigation**:
- **Signal health monitoring**: Track predictive power of each signal over time
- **Adaptive signal weighting**: Down-weight signals that degrade
- **Regime diversity**: Don't rely on single factor (momentum, mean-reversion, etc.)

---

### 7. Individual Trader Failures (r/algotrading, QuantConnect Forums)

**Type**: Retail Algorithmic Traders

**What Failed**:
- Machine learning models trained for 8 months → failed live (low signal-to-noise in financial data)
- Strategies that worked in backtest "blew up" multiple live accounts
- Technical glitches (server downtime, dropped connections) during critical moments
- Strategies that worked on single asset failed when applied broadly

**Root Cause**:
- **Data Snooping**: Training ML on noise, not signal
- **Execution Reality Gap**: Backtests assumed perfect fills, no slippage
- **Platform Risk**: Infrastructure failures (power outages, broker issues)
- **Single-Asset Overfitting**: "Building strategies for a single asset looks a lot like overfitting"
- **Psychology**: Real money introduces emotions, deviations from plan

**Warning Signs**:
- Strategy performance degrading in forward testing
- Large discrepancy between backtest and paper trading
- Increasing parameter adjustments to "fix" recent losses

**Lesson**:
> "99% of equity curve increases gained by incrementally editing the algorithm will be fake."

Iterative "improvement" based on recent data is curve-fitting in disguise.

**Relevance to Us**: **MEDIUM**
- We're not retail traders, but discipline risks apply
- Are we guilty of "tweaking until it looks good"?
- Do we have proper train/test/validation splits with strict barriers?

**Mitigation**:
- **Lock-in periods**: Once strategy deployed, NO parameter changes for X months
- **Sandbox testing**: Always test infrastructure in production-like environment
- **Documented process**: Every parameter change must be justified in writing BEFORE implementation
- **Independent validation**: Someone other than developer reviews strategy

---

## Common Failure Patterns

### 1. Overfitting / Curve Fitting
**Pattern**: Backtest performance doesn't predict live results
**Frequency**: Most common failure mode (Quantopian: "little value in predicting out-of-sample")
**Symptoms**:
- High Sharpe in backtest, negative in live
- Performance degrades immediately after deployment
- Excessive parameters or indicator complexity
- Incremental "improvements" via parameter tweaking

**Relevance**: **HIGH** - Our adaptive system has many tunable components

### 2. Regime Blindness
**Pattern**: Strategies optimized for one regime fail in the next
**Frequency**: Chronic (COVID, Quant Quake, LTCM all regime-related)
**Symptoms**:
- Sudden performance cliff (not gradual decay)
- Correlations shift dramatically
- Historical relationships reverse

**Relevance**: **VERY HIGH** - We're building regime detection, but what if it fails to detect?

### 3. Crowded Trades
**Pattern**: Popular strategies self-destruct via overcrowding
**Frequency**: Recurring (Quant Quake 2007, ongoing factor decay)
**Symptoms**:
- Strategy works well, attracts capital
- Performance degrades as more participants enter
- Forced liquidations cascade across similar portfolios

**Relevance**: **MEDIUM-HIGH** - If our framework becomes popular, we face this

### 4. Leverage Amplification
**Pattern**: Small model errors → catastrophic losses with leverage
**Frequency**: Moderate but devastating (LTCM, some HFT failures)
**Symptoms**:
- Declining returns, increasing leverage to compensate
- Margin calls during volatility spikes
- Rapid drawdowns exceeding historical max

**Relevance**: **LOW-MEDIUM** - Depends on how we implement position sizing (Kelly can suggest high leverage)

### 5. Execution Reality Gap
**Pattern**: Backtests ignore slippage, latency, partial fills, market impact
**Frequency**: Very common (Knight Capital, retail failures)
**Symptoms**:
- Live performance worse than backtest even in similar market conditions
- Orders not filled at expected prices
- Latency causes missed entries/exits

**Relevance**: **MEDIUM** - Our backtests need realistic execution modeling

### 6. Liquidity Illusion
**Pattern**: Liquidity present in calm markets, vanishes during stress
**Frequency**: Moderate (LTCM, COVID, Quant Quake)
**Symptoms**:
- Wide bid-ask spreads during volatility
- Market depth evaporates
- Cannot exit positions at modeled prices

**Relevance**: **HIGH** - Our sizing assumes liquidity availability

### 7. Tail Risk Underestimation
**Pattern**: VaR and historical volatility fail to predict extreme moves
**Frequency**: Recurring (LTCM, COVID, Quant Quake)
**Symptoms**:
- Risk models calibrated to normal markets
- "Black swan" events cause multi-sigma moves
- Drawdowns exceed stress test predictions

**Relevance**: **VERY HIGH** - Our vol-based sizing vulnerable to this

### 8. Operational/Technical Risk
**Pattern**: Infrastructure failures, deployment bugs, monitoring gaps
**Frequency**: Moderate (Knight Capital is extreme example)
**Symptoms**:
- Unintended trades executed
- Strategies fail to start/stop correctly
- Alert fatigue, ignored warnings

**Relevance**: **MEDIUM** - We need robust DevOps, monitoring, kill switches

---

## Applicability to Our Adaptive Control Framework

### Components at Risk

| Component | Primary Failure Pattern | Risk Level | Evidence |
|-----------|------------------------|------------|----------|
| **Regime Detection** | Regime Blindness, Crowded Trades | **VERY HIGH** | COVID (algos couldn't adapt fast enough), HMM struggles with real-time detection |
| **Position Sizing** | Tail Risk, Overfitting, Leverage | **VERY HIGH** | LTCM (VaR failed), Kelly can suggest excessive leverage in fat-tailed markets |
| **Volatility Estimation** | Tail Risk, Execution Gap | **HIGH** | COVID (vol spikes 10x), historical vol is backward-looking |
| **Signal Generation** | Overfitting, Factor Decay | **HIGH** | Quantopian (backtest ≠ live), Summer 2025 (factor reversal) |
| **Risk Control** | Liquidity Illusion, Execution Gap | **MEDIUM-HIGH** | Quant Quake (can't exit during unwind), stop-losses slip during gaps |

### Specific Vulnerabilities

#### 1. Regime Detection Failure Modes
**Problem**: Our HMM/GMM assumes regime space is known and stable.

**Counter-Evidence**:
- COVID created a NEW regime (not just shift between known regimes)
- Quant Quake showed regimes can transition in HOURS, not days
- Regime detection requires lookback period → lags during rapid shifts

**Failure Scenario**:
1. Model identifies "low vol" regime
2. Sizes positions aggressively
3. Black swan event creates new "crisis" regime
4. By the time model detects shift, positions already deep underwater

#### 2. Position Sizing Overfitting
**Problem**: Kelly/volatility-based sizing uses historical parameters.

**Counter-Evidence**:
- LTCM's VaR models failed to predict tail events
- "Historical drawdown must be DOUBLED for live trading" (Monte Carlo studies)
- Quantopian showed backtest metrics don't predict forward performance

**Failure Scenario**:
1. Backtest shows max drawdown of 10%
2. Size positions for 2x safety margin → 20% max
3. Live trading encounters regime not in backtest data
4. Actual drawdown hits 40%+

#### 3. Liquidity Assumptions
**Problem**: Backtests assume we can enter/exit at modeled prices.

**Counter-Evidence**:
- Quant Quake: Liquidity vanished during unwind
- COVID: Bid-ask spreads widened 5-10x
- "Liquidity is only there when you DON'T need it"

**Failure Scenario**:
1. System detects regime shift, signals to reduce exposure
2. Attempts to sell positions
3. Market depth insufficient, slippage 5%+
4. By time orders fill, drawdown already occurred

#### 4. Crowding Risk
**Problem**: If our adaptive framework becomes popular, signals get crowded.

**Counter-Evidence**:
- Quant Quake 2007: Similar strategies caused cascade failure
- Summer 2025: Factor crowding → factor decay
- "When everyone runs the same algorithm, the algorithm becomes the market"

**Failure Scenario**:
1. We open-source adaptive control framework
2. 1000s of traders implement similar regime detection
3. All detect regime shift simultaneously
4. Correlated liquidation → price impact → losses for all

---

## Mitigation Recommendations

### Tier 1: Critical (Implement Before Live Deployment)

#### 1.1 Hard Risk Limits (Independent of Model)
- **Max Position Size**: 2% of capital per position (regardless of Kelly suggestion)
- **Max Leverage**: 1.5x (even if model suggests higher)
- **Max Drawdown Circuit Breaker**: Hard stop at -15% (human override only)
- **Daily Loss Limit**: Halt trading at -3% daily loss

**Rationale**: Knight Capital, LTCM show models can fail catastrophically. Hard limits prevent total ruin.

#### 1.2 Tail Risk Reserves
- **Always maintain 20% cash reserve** (never fully deploy capital)
- **Protective options**: Far OTM puts on correlated assets (not just stop-losses)
- **Stress test for 5-sigma events**: Not just 2-sigma

**Rationale**: LTCM, COVID show tail events exceed model predictions. Reserves provide survival capital.

#### 1.3 Kill Switches & Monitoring
- **Automated kill switch**: Triggered by volume/PnL anomalies (like Knight Capital should have had)
- **Real-time signal health monitoring**: Track predictive power of each signal
- **Regime detection confidence intervals**: If confidence < 70%, reduce position sizing

**Rationale**: Knight Capital lost $440M in 45 minutes due to lack of kill switch.

#### 1.4 Walk-Forward Validation
- **NO parameter optimization on full dataset**
- **Strict train/validate/test splits with time barriers**
- **Lock-in period**: Once deployed, NO parameter changes for 6 months

**Rationale**: Quantopian showed backtest performance doesn't predict live results. Walk-forward is minimum bar.

### Tier 2: Important (Implement Within 3 Months of Live)

#### 2.1 Execution Reality Modeling
- **Backtest with realistic slippage**: 0.1% + 0.05% market impact for mid-cap stocks
- **Partial fill simulation**: Assume only 70% of orders fill at desired price
- **Latency injection**: Add 100ms delay to backtest signals

**Rationale**: Retail trader failures show execution gaps cause significant live underperformance.

#### 2.2 Liquidity Constraints
- **ADV limits**: Never trade > 1% of average daily volume in single day
- **Bid-ask spread filters**: Skip trades when spread > 0.2%
- **Market depth checks**: Verify order book depth before large orders

**Rationale**: Quant Quake, LTCM show liquidity evaporates during stress.

#### 2.3 Regime Detection Robustness
- **Ensemble regime models**: HMM + GMM + rule-based (vote required for high confidence)
- **Vol-of-vol monitoring**: Detect acceleration in regime change speed
- **Manual override**: Human can force "crisis mode" regardless of model

**Rationale**: COVID showed single models fail during unprecedented regimes.

#### 2.4 Anti-Crowding Measures
- **Proprietary signal tweaks**: Don't use pure textbook implementations
- **Capacity limits**: Hard cap on AUM (e.g., $10M max) to avoid market impact
- **Monitor for crowding**: Compare our entry/exit timing to market-wide patterns

**Rationale**: Quant Quake shows strategy crowding creates systemic risk.

### Tier 3: Nice-to-Have (Continuous Improvement)

#### 3.1 Factor Decay Detection
- **Rolling out-of-sample testing**: Every 30 days, test last 30 days as "unseen" data
- **Signal half-life tracking**: Measure how long each signal remains predictive
- **Adaptive signal weighting**: Down-weight signals showing decay

**Rationale**: Summer 2025 shows factors can reverse after years of success.

#### 3.2 Operational Risk Controls
- **Canary deployments**: Test new code on 10% of capital first
- **Pre-deployment validation**: Sandbox with production-like data
- **Documented incident response**: Playbook for common failure modes

**Rationale**: Knight Capital shows deployment errors can be catastrophic.

#### 3.3 Psychology & Discipline
- **Pre-commitment**: Document strategy logic BEFORE deployment, no changes without new hypothesis
- **Blameless post-mortems**: Analyze losses without finger-pointing to extract lessons
- **Diversification**: Run multiple UNCORRELATED strategies to reduce single-model dependency

**Rationale**: Retail trader failures show psychology derails even good systems.

---

## Key Takeaways

### 1. Backtest Performance ≠ Live Performance
**Quantopian's own research**: "Backtest performance metrics offer little value in predicting out-of-sample performance."

### 2. Models Fail During Regime Shifts
**COVID, LTCM, Quant Quake**: All involved models trained on one regime failing in the next.

### 3. Tail Risk is Underestimated
**LTCM's VaR failed to predict Russian default.** Historical volatility is backward-looking.

### 4. Liquidity Vanishes When Needed
**Quant Quake**: "Liquidity is only there when you don't need it."

### 5. Crowded Trades Self-Destruct
**Quant Quake 2007**: Similar strategies created cascade failures.

### 6. Operational Risk = Model Risk
**Knight Capital**: Lost more in 45 minutes than LTCM lost in months. Software bugs can exceed model errors.

### 7. Hard Limits Save Lives
**None of the mega-failures had hard circuit breakers independent of models.** LTCM could have survived with leverage caps.

---

## Sources

### Institutional Failures
- [LTCM Case Study](https://www.bauer.uh.edu/rsusmel/7386/ltcm-2.htm)
- [Six Lessons from LTCM Collapse](https://www.timeline.co/blog/six-lessons-from-the-collapse-of-ltcm)
- [Knight Capital $440M Software Error](https://www.henricodolfing.com/2019/06/project-failure-case-study-knight-capital.html)
- [The Knight Capital Disaster](https://specbranch.com/posts/knight-capital/)
- [Quant Meltdown August 2007](https://web.mit.edu/Alo/www/Papers/august07.pdf)
- [What Happened to Quants in August 2007](https://www.nber.org/papers/w14465)
- [Summer 2025 Quant Fund Wobble](https://www.msci.com/research-and-insights/blog-post/unraveling-summer-2025s-quant-fund-wobble)

### Platform/Retail Failures
- [What Happened to Quantopian](https://www.sunsethq.com/blog/why-did-quantopian-fail)
- [Quantopian Shutdown Lessons](https://mikeharrisny.medium.com/quantopian-shutdown-offers-some-important-lessons-f8608535b7db)
- [Lessons from Failed Algorithmic Systems](https://bluechipalgos.com/blog/lessons-learned-from-failed-algorithmic-trading-systems/)
- [7 Years of Algo Trading Lessons](https://medium.com/@josh.malizzi/lessons-from-7-years-of-algorithmic-trading-research-and-development-c63f1d319831)

### Technical Analysis
- [10 Ways Trading Strategies Fail](https://blog.quantinsti.com/ways-trading-strategy-fail/)
- [Why Backtest Strategies Fail Live](https://www.quantman.in/ghostblog/why-back-tested-strategies-fail-in-live-trading-and-how-to-fix-it/)
- [Overfitting in Trading](https://www.luxalgo.com/blog/what-is-overfitting-in-trading-strategies/)
- [Market Regime Detection Challenges](https://www.quantstart.com/articles/market-regime-detection-using-hidden-markov-models-in-qstrader/)

### COVID-19 Impact
- [Algorithmic Trading in Turbulent Markets](https://pmc.ncbi.nlm.nih.gov/articles/PMC7276139/)
- [COVID-19 Market Structure Dynamics](https://pmc.ncbi.nlm.nih.gov/articles/PMC8603410/)

### Forum Discussions
- [QuantConnect: When is Strategy Good Enough to Go Live](https://www.quantconnect.com/forum/discussion/15725/when-is-a-strategy-quot-good-enough-quot-to-go-live/)
- [QuantConnect: Crash Error in Live Trading](https://www.quantconnect.com/forum/discussion/5636/crash-error-when-running-algorithm-in-paper-trading-production-not-when-backtesting/)
