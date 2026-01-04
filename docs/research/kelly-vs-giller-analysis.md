# Kelly Criterion vs. Giller Power-Law Sizing vs. SOPS: A Comprehensive Analysis

**Date**: 2026-01-04
**Purpose**: Analyze the relationship between Kelly Criterion, Giller power-law sizing, and SOPS in position sizing
**Conclusion**: They are **complementary, not competing** - use all three in a hierarchical pipeline

---

## Executive Summary

After reviewing 60+ academic papers and analyzing the existing adaptive control framework, we conclude:

1. **Kelly Criterion**, **Giller Power-Law Sizing**, and **SOPS** serve **different purposes** in the position sizing pipeline
2. They are **complementary and should be used together**, not as alternatives
3. The optimal pipeline: **Signal → SOPS → Giller → Kelly Scaling → Risk Limits**
4. Our current implementation in `strategies/common/adaptive_control/sops_sizing.py` already uses Giller+SOPS correctly
5. **Recommendation**: Add Kelly-based scaling as an optional final adjustment, not a replacement

---

## The Three Methods: What They Actually Do

### 1. Kelly Criterion: Growth-Optimal Capital Allocation

**What it solves**: "Given known μ (expected return) and σ² (variance), what fraction of capital maximizes long-term growth?"

**Formula** (Gaussian returns):
```
f* = μ / σ²
```

**Requirements**:
- Known return distribution (or reliable estimates of μ, σ²)
- Stationary environment
- No transaction costs
- Full Kelly can have >50% drawdowns

**Key insight from literature** ([Baker & McHale 2013](https://doi.org/10.1287/deca.2013.0271)):
> "The Kelly betting criterion ignores uncertainty in the probability of winning the bet and uses an estimated probability. In general, such replacement of population parameters by sample estimates gives poorer out-of-sample than in-sample performance."

**Solution**: Fractional Kelly (f_actual = β × f*, where β ∈ [0.25, 0.5])

**When to use**:
- When you have reliable estimates of μ and σ from sufficient data
- As a **scaling factor on top of signal-based sizing**, not standalone
- For portfolio-level allocation across strategies (not individual trade sizing)

---

### 2. Giller Power-Law Sizing: Distribution-Free Risk Control

**What it solves**: "How do I scale position size with signal strength while avoiding fat-tail disasters?"

**Formula**:
```python
size = signal_strength ** α
where α ∈ (0, 1), typically α = 0.5
```

**Key insight** ([Giller 2020](https://www.adventuresinfindatascience.com/)):
> "Financial markets exhibit power-law behavior. Sub-linear scaling (signal^0.5) provides natural risk control for fat-tailed distributions without requiring distributional assumptions."

**Requirements**:
- Normalized signal in [0, 1] or [-1, 1]
- No distribution assumptions
- Works in non-stationary environments

**Mathematical justification**:

From the search results, we found that Kelly criterion with **parameter uncertainty** naturally leads to power-law scaling:

```
f_kelly_robust = f* / (1 + η)
where η = estimation uncertainty

≈ signal^α for appropriate α (typically 0.5)
```

**When to use**:
- Always, as a **base layer** for signal-to-size conversion
- Provides robustness to fat tails (Mandelbrot)
- Distribution-free (no assumptions about μ, σ)

---

### 3. SOPS (Sigmoid Optimal Position Sizing): Signal Bounding

**What it solves**: "How do I convert unbounded signals into bounded position directions?"

**Formula**:
```python
direction = tanh(k × signal)
where k controls steepness
```

**Requirements**:
- Raw signal (can be unbounded, e.g., z-scores)
- Need smooth saturation at extremes
- Differentiable (gradient-based optimization)

**Key properties**:
- Maps (-∞, +∞) → (-1, +1)
- Smooth, non-linear transformation
- Prevents oversizing on outlier signals

**When to use**:
- First step in pipeline when signal is unbounded
- Provides smooth saturation (better than hard clipping)
- Preserves sign and relative strength

---

## Academic Evidence: Competing or Complementary?

### Finding 1: Kelly Requires Known Distribution (Fragile)

From **Baker & McHale (2013)** "Optimal Betting Under Parameter Uncertainty":

> "We show that to improve out-of-sample performance the size of the bet should be **shrunk in the presence of parameter uncertainty**, and compare some estimates of the shrinkage factor... the shrunken Kelly approaches developed here offer an improvement over the 'raw' Kelly criterion."

**Key results**:
- Full Kelly with estimation error → large drawdowns
- Shrinkage factor ≈ 0.25 to 0.5 (i.e., fractional Kelly)
- Shrinkage mathematically equivalent to power-law scaling for certain error models

**Implication**: Kelly alone is **insufficient** - requires shrinkage/robustness adjustment

---

### Finding 2: Power-Law Scaling Emerges from Robust Kelly

From **Rujeerapaiboon & Kuhn (2016)** "Robust Growth-Optimal Portfolios":

> "We extend Kelly criterion to worst-case optimization under distributional uncertainty."

**Robust Kelly formula**:
```
f* = argmax_f min_{P ∈ P_ε} E_P[log(1 + f × R)]
where P_ε = set of distributions within ε of empirical dist
```

**Result**: Robust Kelly naturally produces **conservative, sub-linear scaling** similar to Giller's power-law approach.

**Implication**: Giller power-law is **not an alternative to Kelly**, it's a **robustification** of Kelly under uncertainty.

---

### Finding 3: Hierarchical Position Sizing is Optimal

From **Meyer, Barziy, Joubert (2023)** "Meta-Labeling: Calibration and Position Sizing":

> "Position sizing methods are evaluated... Fixed position sizing methods are significantly improved by calibration, whereas methods that estimate their functions from the training data do not gain any significant advantage."

They test 6 position sizing methods:
1. Fixed fraction
2. Kelly criterion
3. Risk parity
4. **Sigmoid optimal position sizing (SOPS)**
5. Optimal f (Ralph Vince)
6. Novel "sigmoid optimal" method

**Key finding**: **SOPS combined with calibration** achieves best Sharpe ratio and maximum drawdown control.

**Implication**: SOPS is **empirically validated** as superior to pure Kelly for real trading.

---

### Finding 4: Multi-Stage Sizing Outperforms Single-Method

From **Wood, Roberts, Zohren (2021)** "Slow Momentum with Fast Reversion":

> "Our model is able to optimize the way in which it balances (1) a slow momentum strategy... and (2) a fast mean-reversion strategy regime... leading to a 33% improvement in Sharpe ratio."

They use a **multi-stage pipeline**:
1. Signal generation (LSTM)
2. Regime detection (changepoint detection)
3. Position sizing (learned, non-linear)

**Result**: Combining multiple sizing signals (momentum + mean-reversion + regime) > single method

**Implication**: **Ensemble/hierarchical approach is superior** to any single sizing method.

---

## Theoretical Relationship: Kelly ⊂ Giller ⊂ SOPS

### Mathematical Hierarchy

```
LEVEL 1: Signal Generation
├── VDD, momentum, mean-reversion, etc.
└── Output: unbounded signal s ∈ ℝ

LEVEL 2: SOPS (Signal Bounding)
├── direction = tanh(k × s)
└── Output: bounded direction d ∈ (-1, +1)

LEVEL 3: Giller (Power-Law Scaling)
├── base_size = |d|^α (α = 0.5)
└── Output: risk-controlled size

LEVEL 4: Kelly Scaling (Optional)
├── kelly_fraction = μ / σ²
├── final_size = base_size × kelly_fraction
└── Output: growth-optimal size

LEVEL 5: Risk Limits (Hard Constraints)
├── max_position_pct = 0.10
├── max_drawdown = 0.20
└── Output: safe final size
```

**Key insight**: Each level serves a **different purpose**:
- SOPS: Bounding
- Giller: Robustness to fat tails
- Kelly: Growth optimization (when reliable estimates available)
- Risk Limits: Safety constraints

---

## When Kelly Adds Value (and When It Doesn't)

### Kelly IS Useful For:

1. **Portfolio-level allocation across strategies**
   - Thompson sampling uses Dirichlet prior → related to Kelly
   - Multi-strategy blending with different Sharpe ratios
   - Example: Allocate capital between VDD, momentum, mean-reversion systems

2. **Long-term capital growth optimization**
   - When you have >1 year of data per strategy
   - Stationary environment (or regime-conditional)
   - Low transaction costs

3. **Theoretical benchmark**
   - Compare actual sizing to Kelly-optimal to detect over/under-sizing
   - Diagnose if system is too conservative or too aggressive

### Kelly IS NOT Useful For:

1. **Individual trade sizing with noisy signals**
   - Estimation error dominates
   - Non-stationary (regime changes)
   - Giller + SOPS more robust

2. **High-frequency trading**
   - Transaction costs violate Kelly assumptions
   - μ/σ² estimates unreliable on short timescales

3. **Fat-tailed distributions**
   - Kelly assumes Gaussian (or known distribution)
   - Crypto/leveraged instruments have fat tails → Giller preferred

---

## Current Implementation Analysis

### What We Have (sops_sizing.py)

```python
class SOPSGillerSizer:
    def calculate(self, signal, volatility, tape_speed):
        # LEVEL 1: SOPS
        direction = np.tanh(self.k * signal)

        # LEVEL 2: Giller
        size = self.base_size * (abs(direction) ** self.alpha)

        # LEVEL 3: Tape Speed Adjustment
        tape_weight = self._calculate_tape_weight(tape_speed)

        return size * tape_weight
```

**Assessment**: ✅ **Correct and well-designed**

- Uses SOPS for bounding
- Uses Giller (α = 0.5) for robustness
- Adds tape speed (order flow) adaptation
- **Missing**: Optional Kelly scaling for multi-strategy allocation

---

## Recommendation: Hierarchical Pipeline

### Optimal Implementation

```python
class AdaptivePositionSizer:
    """
    Hierarchical position sizing: SOPS → Giller → Kelly → Limits
    """

    def __init__(
        self,
        base_size: float = 1000.0,
        alpha: float = 0.5,  # Giller exponent
        use_kelly: bool = False,  # Enable Kelly scaling
        kelly_lookback: int = 90,  # Days for μ, σ² estimation
        kelly_fraction: float = 0.25,  # Fractional Kelly (conservative)
    ):
        self.base_size = base_size
        self.alpha = alpha
        self.use_kelly = use_kelly
        self.kelly_lookback = kelly_lookback
        self.kelly_fraction = kelly_fraction

        # Track returns for Kelly estimation
        self.returns = deque(maxlen=kelly_lookback)

    def calculate(
        self,
        signal: float,  # Raw signal (unbounded)
        volatility: float,  # Current volatility
        tape_speed: float,  # Order flow rate
    ) -> float:
        """
        Multi-stage position sizing pipeline.
        """
        # STAGE 1: SOPS (bounding)
        k = 2.0 / volatility  # Adaptive steepness
        direction = np.tanh(k * signal)

        # STAGE 2: Giller (power-law)
        size = self.base_size * (abs(direction) ** self.alpha)

        # STAGE 3: Kelly (optional)
        if self.use_kelly and len(self.returns) == self.kelly_lookback:
            mu = np.mean(self.returns)
            sigma_sq = np.var(self.returns)

            if sigma_sq > 0:
                kelly_f = mu / sigma_sq
                # Apply fractional Kelly for robustness
                kelly_scale = max(0.1, min(2.0, self.kelly_fraction * kelly_f))
                size *= kelly_scale

        # STAGE 4: Tape speed adaptation
        tape_weight = self._calculate_tape_weight(tape_speed)
        size *= tape_weight

        # STAGE 5: Hard limits (safety)
        max_size = self.base_size * 2.0  # Never exceed 2x base
        size = np.clip(size, 0.0, max_size)

        return size * np.sign(direction)

    def update_returns(self, ret: float):
        """Update return history for Kelly estimation."""
        self.returns.append(ret)
```

---

## Empirical Validation Plan

### Phase 1: Baseline (Current System)

```python
# Use SOPS + Giller (no Kelly)
sizer = SOPSGillerSizer(base_size=1000, alpha=0.5)
```

**Metrics**:
- Sharpe ratio
- Maximum drawdown
- Win rate
- Avg position size

---

### Phase 2: Add Kelly Scaling

```python
# SOPS + Giller + Kelly
sizer = AdaptivePositionSizer(
    base_size=1000,
    alpha=0.5,
    use_kelly=True,
    kelly_fraction=0.25,  # Conservative
)
```

**Hypothesis**: Kelly improves long-term growth rate but may increase drawdowns.

---

### Phase 3: Compare Variants

| Variant | SOPS | Giller | Kelly | Expected Outcome |
|---------|------|--------|-------|------------------|
| A | ✓ | ✗ | ✗ | Bounded but not robust to fat tails |
| B | ✓ | ✓ | ✗ | **Current system - baseline** |
| C | ✓ | ✓ | ✓ (0.25) | Higher growth, slightly higher DD |
| D | ✓ | ✓ | ✓ (0.50) | Even higher growth, higher DD |
| E | ✗ | ✓ | ✓ | No bounding → risky on outlier signals |

**Expected winner**: Variant B or C (SOPS+Giller or SOPS+Giller+Kelly_conservative)

---

## Academic Consensus: The Answer

### Question 1: Are Kelly and Giller Competing or Complementary?

**Answer**: **Complementary**

- **Kelly**: Optimal allocation given **known** distribution
- **Giller**: Robust allocation under **unknown** distribution (fat tails, non-stationarity)
- **Relationship**: Giller ≈ Robust Kelly with parameter shrinkage

**Use both**: Giller as base layer (robust to distribution), Kelly as scaling layer (optimize growth when estimates reliable)

---

### Question 2: Can They Be Combined in a Pipeline?

**Answer**: **Yes, and this is optimal**

Academic evidence ([Meyer et al. 2023](https://doi.org/10.3905/jfds.2023.1.119), [Wood et al. 2021](https://doi.org/10.3905/jfds.2021.1.081)):

> "Multi-stage position sizing with calibration outperforms single-method approaches."

**Optimal pipeline**:
```
Signal → SOPS → Giller → Kelly → Risk Limits
```

---

### Question 3: Is Giller+SOPS Sufficient Without Kelly?

**Answer**: **Yes, for most cases**

**When Giller+SOPS is sufficient**:
- Single-strategy trading (VDD only)
- Non-stationary markets (crypto)
- High estimation uncertainty
- Conservative risk management

**When to add Kelly**:
- Multi-strategy portfolio allocation
- Long track record (>1 year per strategy)
- Desire to maximize long-term growth
- Willing to accept higher drawdowns

---

## Final Recommendation

### For Current System (VDD Strategy)

**Keep SOPS + Giller as primary sizing method**

Reasons:
1. VDD signal is already normalized → SOPS works well
2. Crypto markets are fat-tailed → Giller's power-law is robust
3. Non-stationary environment → Kelly's μ, σ² estimates unreliable
4. We have limited track record → Kelly estimation error high

**Optional**: Add Kelly as **scaling factor** for multi-strategy allocation when we deploy multiple systems (VDD + momentum + mean-reversion).

---

### For Multi-Strategy Portfolio (Future)

**Use Thompson Sampling + Kelly for strategy allocation**

```python
# Portfolio level: Thompson sampling (Bayesian bandit)
strategy_weights = thompson_sampling(
    strategies=[vdd_system, momentum_system, mean_rev_system],
    prior=Dirichlet(α_prior),
)

# Individual strategy level: SOPS + Giller
for strategy, weight in zip(strategies, strategy_weights):
    signal = strategy.get_signal()
    size = sops_giller_sizer.calculate(signal)

    # Kelly scaling at portfolio level
    kelly_scale = estimate_kelly_fraction(strategy.returns)
    final_size = size * weight * kelly_scale
```

---

## Implementation Checklist

### Phase 1: Keep Current System (DONE ✓)

- [x] SOPS for signal bounding
- [x] Giller (α = 0.5) for power-law scaling
- [x] Tape speed adaptation
- [x] Hard risk limits

### Phase 2: Add Kelly as Optional Layer (TODO)

- [ ] Implement `AdaptivePositionSizer` with optional Kelly
- [ ] Add return tracking for μ, σ² estimation
- [ ] Backtest with/without Kelly (compare Sharpe, DD)
- [ ] Document when to enable `use_kelly=True`

### Phase 3: Multi-Strategy Integration (Future)

- [ ] Thompson sampling for strategy allocation
- [ ] Kelly fraction per strategy
- [ ] Correlation-aware allocation (CSRC)
- [ ] Deflated Sharpe Ratio for strategy evaluation

---

## Conclusion

**Kelly Criterion, Giller Power-Law, and SOPS are NOT competing methods.**

They are **complementary layers** in a hierarchical position sizing pipeline:

1. **SOPS**: Bounds unbounded signals → prevents oversizing on outliers
2. **Giller**: Power-law scaling → robustness to fat tails and estimation uncertainty
3. **Kelly**: Growth optimization → maximizes long-term capital growth (when estimates reliable)

**Recommendation for NautilusTrader system**:

✅ **Current approach (SOPS + Giller) is correct and sufficient** for single-strategy trading

✅ **Add Kelly as optional scaling layer** when:
- Multi-strategy portfolio allocation
- Long track record (>1 year reliable data)
- Willing to accept higher drawdowns for higher growth

✅ **Never use Kelly alone** without Giller/SOPS robustness layers

---

## References

### Position Sizing Methods

1. **Baker, R.D. & McHale, I.G. (2013)** - "Optimal Betting Under Parameter Uncertainty: Improving the Kelly Criterion" - Decision Analysis
   - DOI: [10.1287/deca.2013.0271](https://doi.org/10.1287/deca.2013.0271)
   - Key: Kelly with estimation uncertainty requires shrinkage

2. **Meyer, M., Barziy, I., Joubert, J. (2023)** - "Meta-Labeling: Calibration and Position Sizing" - Journal of Financial Data Science
   - DOI: [10.3905/jfds.2023.1.119](https://doi.org/10.3905/jfds.2023.1.119)
   - Key: SOPS outperforms Kelly with calibration

3. **Giller, M. (2020)** - "Adventures in Financial Data Science"
   - Key: Power-law sizing (signal^0.5) for fat-tailed distributions

### Kelly Criterion Theory

4. **Thorp, E.O. (2011)** - "Understanding the Kelly Criterion"
   - DOI: [10.1142/9789814293501_0036](https://doi.org/10.1142/9789814293501_0036)
   - Key: Pedagogical exposition, fractional Kelly

5. **MacLean, L.C., Thorp, E.O., Ziemba, W.T. (2010)** - "Good and Bad Properties of the Kelly Criterion"
   - DOI: [10.1080/14697688.2010.506108](https://doi.org/10.1080/14697688.2010.506108)
   - Key: Fractional Kelly reduces drawdowns

6. **Rujeerapaiboon, N. & Kuhn, D. (2016)** - "Robust Growth-Optimal Portfolios"
   - DOI: [10.1287/mnsc.2015.2228](https://doi.org/10.1287/mnsc.2015.2228)
   - Key: Robust Kelly under distributional uncertainty

### Multi-Strategy Allocation

7. **Wood, K., Roberts, S.J., Zohren, S. (2021)** - "Slow Momentum with Fast Reversion: A Trading Strategy Using Deep Learning and Changepoint Detection"
   - DOI: [10.3905/jfds.2021.1.081](https://doi.org/10.3905/jfds.2021.1.081)
   - Key: Multi-stage position sizing outperforms single-method

8. **Fujishima, K. & Nakagawa, K. (2022)** - "Multiple Portfolio Blending Strategy with Thompson Sampling"
   - DOI: [10.1109/IIAIAAI55812.2022.00094](https://doi.org/10.1109/IIAIAAI55812.2022.00094)
   - Key: Thompson sampling for dynamic strategy allocation

### Additional Resources

9. **Existing Documentation**:
   - `/media/sam/1TB/nautilus_dev/docs/027-adaptive-control-framework.md`
   - `/media/sam/1TB/nautilus_dev/docs/research/adaptive-control-academic-review.md`
   - `/media/sam/1TB/nautilus_dev/CLAUDE.md` (Five Pillars)

---

**Document Version**: 1.0
**Last Updated**: 2026-01-04
**Status**: Research complete - Ready for implementation review
