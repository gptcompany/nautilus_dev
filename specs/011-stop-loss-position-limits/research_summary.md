# Research Summary: Coupled Optimal Stopping for Pairs Trading

**Paper**: "A Coupled Optimal Stopping Approach to Pairs Trading over a Finite Horizon" (Kitapbayev & Leung, 2025)

**Date**: 2025-12-28

**Researcher**: Claude Code (Sonnet 4.5)

---

## Executive Summary

This research investigates optimal stopping theory applied to pairs trading with mean-reverting spreads modeled by the Ornstein-Uhlenbeck (OU) process. The Kitapbayev & Leung (2025) paper provides a rigorous mathematical framework for determining optimal entry/exit boundaries over a finite time horizon, accounting for transaction costs and unbounded trading frequency. This summary evaluates the academic foundations, practical implementations, and applicability to NautilusTrader.

**Key Finding**: While the theoretical framework is elegant, practical implementation requires:
1. **Numerical solvers** for Volterra-type integral equations (no closed-form solutions for finite horizon)
2. **Robust OU parameter estimation** from real market data (μ, θ, σ)
3. **Time-varying boundary computations** via backward induction
4. **Integration with live trading systems** (NautilusTrader) for dynamic stop-loss adjustment

---

## 1. Academic Foundations

### 1.1 Core Paper: Kitapbayev & Leung (2025)

**Publication Details**:
- **Title**: "A Coupled Optimal Stopping Approach to Pairs Trading over a Finite Horizon"
- **Authors**: Yerkin Kitapbayev, Tim Leung
- **Date**: October 24, 2025
- **Journal**: Computational Economics (November 2025)
- **Availability**: [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5653650)

**Mathematical Framework**:

1. **Ornstein-Uhlenbeck Process**:
   ```
   dX_t = μ(θ - X_t)dt + σdW_t
   ```
   - **θ**: Long-term mean level (equilibrium spread)
   - **μ**: Mean reversion speed (rate of convergence to θ)
   - **σ**: Instantaneous volatility (spread noise)

2. **Coupled Value Functions**:
   - **V_0(x, t)**: Value function when not holding position
   - **V_1(x, t)**: Value function when holding long position
   - These are linked via optimal stopping decisions at boundaries

3. **Trading Boundaries**:
   - **b_0(t)**: Entry boundary (buy when spread X_t ≤ b_0(t))
   - **b_1(t)**: Exit boundary (sell when spread X_t ≥ b_1(t))
   - **Time-varying**: Boundaries change as expiration approaches

4. **Terminal Conditions** (as t → T):
   - **b_0(T-) = -∞**: No entry at expiration (no time to profit)
   - **b_1(T-) = (μθ + rc)/(μ + r)**: Final exit threshold accounting for transaction cost c and discount rate r

5. **Solution Method**:
   - Derives **Volterra-type integral equations** characterizing b_0(t) and b_1(t)
   - Solved numerically via **backward induction** from terminal time T
   - No closed-form analytical solution for finite horizon case

6. **Three-State Extension**:
   - Adds state -1 (short position) for long-short-flat strategies
   - Three coupled value functions: V_{-1}, V_0, V_1
   - More complex boundary system with b_{-1}(t), b_0^-(t), b_0^+(t), b_1(t)

**Key Insights**:
- **Transaction costs** increase the no-trade zone (b_0 lower, b_1 higher)
- **Time decay**: Entry boundaries narrow as t → T (less opportunity)
- **Sensitivity**: Boundaries highly sensitive to μ (mean reversion speed)

---

### 1.2 Related Academic Work

#### Foundational Papers

**Leung & Li (2015)**: "Optimal Mean Reversion Trading with Transaction Costs and Stop-Loss Exit"
- **Journal**: International Journal of Theoretical and Applied Finance, Vol. 18, No. 3
- **arXiv**: [1411.5062](https://arxiv.org/abs/1411.5062)
- **Key Contributions**:
  - First rigorous treatment of **stop-loss constraints** in OU trading
  - Analytical solutions for entry/exit regions with stop-loss level S
  - Shows: Entry region is bounded interval **strictly above** S
  - Higher stop-loss → earlier voluntary exit (lower take-profit)
- **Limitation**: Infinite horizon (perpetual trading), not finite horizon

**Kitapbayev & Leung (2017)**: "Optimal Mean-Reverting Spread Trading: Nonlinear Integral Equation Approach"
- **arXiv**: [1701.00875](https://arxiv.org/abs/1701.00875)
- **Key Contributions**:
  - Extended Leung & Li (2015) to **finite horizon**
  - Three strategies analyzed: (i) long-short, (ii) short-long, (iii) chooser
  - Introduced Volterra integral equation framework (precursor to 2025 paper)
  - Numerical methods for computing optimal boundaries

**Mudchanatongsuk et al. (2008)**: "Optimal Pairs Trading: A Stochastic Control Approach"
- **Journal**: IEEE Conference Publication
- **Key Contributions**:
  - Formulated as **singular stochastic control problem**
  - Hamilton-Jacobi-Bellman (HJB) equation with free boundaries
  - Viscosity solution approach
  - Determined optimal **position sizes** (not just timing)

**Tourin & Yan (2013)**: "Dynamic Pairs Trading Using Stochastic Control"
- **Key Contributions**:
  - Added **gross market exposure constraints** (leverage limits)
  - Monotone finite difference scheme for HJB equation
  - Exponential utility framework (CARA preferences)

**Pham & Ngo (2016)**: "A Singular Stochastic Control Approach with Proportional Transaction Costs"
- **Journal**: MDPI Journal of Risk and Financial Management
- **arXiv**: [1911.10450](https://arxiv.org/abs/1911.10450)
- **Key Contributions**:
  - Proportional transaction costs (not fixed)
  - Proved existence/uniqueness via **quasi-variational inequality**
  - Characterized optimal strategy as free boundary problem

#### Comparative Summary

| Paper | Horizon | Transaction Costs | Stop-Loss | Solution Method | Position Sizing |
|-------|---------|-------------------|-----------|-----------------|-----------------|
| Leung & Li (2015) | Infinite | Fixed | Yes | Analytical | No (fixed) |
| Kitapbayev & Leung (2017) | Finite | Fixed | No | Volterra IEs | No (fixed) |
| Kitapbayev & Leung (2025) | Finite | Fixed | No | Volterra IEs | No (unbounded trades) |
| Mudchanatongsuk (2008) | Infinite | Proportional | No | HJB/Viscosity | Yes (optimal) |
| Tourin & Yan (2013) | Finite | Proportional | No | Finite Diff | Yes (optimal) |
| Pham & Ngo (2016) | Infinite | Proportional | No | QVI | Yes (optimal) |

**Gap Analysis**:
- **Missing**: Finite horizon + stop-loss + proportional costs + optimal sizing
- **Kitapbayev & Leung (2025)** addresses finite horizon but not stop-loss or position sizing

---

### 1.3 Mathematical Methods Review

#### Volterra Integral Equations

**Definition** (Second kind):
```
y(t) = f(t) + ∫₀ᵗ K(t,s) y(s) ds
```

**Properties**:
- **Memory effect**: Solution y(t) depends on entire history {y(s): s ≤ t}
- **Causal**: Future doesn't affect past (unlike Fredholm equations)
- **Applications**: Finance (path-dependent options), physics (hereditary materials)

**Numerical Methods**:
1. **Collocation** (polynomial approximation)
2. **Block pulse functions** (piecewise constant)
3. **Newton iteration** (for nonlinear kernels)
4. **Deep learning** (recent: [arXiv:2505.18297](https://arxiv.org/html/2505.18297))

**Python Packages**:
- **inteq** ([PyPI](https://pypi.org/project/inteq/)): Volterra & Fredholm solvers
- **nssvie** ([PyPI](https://pypi.org/project/nssvie/)): Stochastic Volterra IEs
- **volterra** ([GitHub](https://github.com/oliverpierson/volterra)): Custom solver

**Challenges**:
- No general analytical solutions (except special kernels)
- Requires discretization (time grid T = {t₀, t₁, ..., t_N})
- Computational cost: O(N²) for N time steps
- Stability issues for stiff kernels

#### Backward Induction

**Algorithm** (for finite horizon T):
1. **Initialize**: Set b(T) from terminal condition
2. **Iterate backwards**: For t = T-Δt, T-2Δt, ..., 0:
   - Solve Volterra IE at time t using b(t+Δt), b(t+2Δt), ... (future values)
   - Store b(t)
3. **Output**: Complete boundary function b(·) on [0, T]

**Computational Requirements**:
- **Time discretization**: Δt small enough for accuracy (e.g., hourly for daily strategies)
- **Memory**: Store all future boundaries for integral evaluation
- **Convergence**: Δt → 0 should converge to continuous solution

**Connection to Dynamic Programming**:
- Bellman optimality: V(x,t) = max{immediate reward + discounted future V}
- Free boundary b(t) where V_0 = V_1 (indifference condition)

---

## 2. Practical Implementations

### 2.1 Hudson & Thames ArbitrageLab

**Overview**:
- **GitHub**: [hudson-and-thames/arbitragelab](https://github.com/hudson-and-thames/arbitragelab)
- **License**: Open-source (community-maintained)
- **Focus**: Academic algorithms for mean-reverting portfolios

**Key Modules**:

1. **optimal_mean_reversion/ou_model.py**:
   - Implements Leung & Li (2015) framework
   - OU parameter estimation (MLE, OLS)
   - Optimal boundary computation (infinite horizon only)

   **Example**:
   ```python
   from arbitragelab.optimal_mean_reversion import OrnsteinUhlenbeck

   ou = OrnsteinUhlenbeck()
   ou.fit(
       data=spread_df,
       data_frequency="D",
       discount_rate=[0.05, 0.05],  # Annual rate
       transaction_cost=[0.02, 0.02],  # Proportional
       stop_loss=0.2  # Maximum drawdown
   )

   # Get optimal boundaries
   entry_level = ou.optimal_entry_level()
   exit_level = ou.optimal_exit_level()
   ```

2. **stochastic_control_approach/ou_model_mudchanatongsuk.py**:
   - Implements Mudchanatongsuk et al. (2008) stochastic control
   - Solves HJB equation numerically (finite difference)
   - Outputs optimal position sizes (not just timing)

3. **optimal_mean_reversion/heat_potentials.py**:
   - Alternative approach using heat kernel methods
   - Steady-state solutions for stationary problems
   - Fast computation via analytical formulas

**Limitations**:
- **No finite horizon** in current release (v1.0.0)
- **No Volterra solver** for Kitapbayev & Leung (2025) approach
- **No live trading integration** (backtesting only)

**Practical Applicability**: 70/100
- Strong for research/backtesting
- Requires custom development for live trading
- Parameter estimation well-implemented

---

### 2.2 OU Parameter Estimation

**Critical Challenge**: OU parameters (μ, θ, σ) must be estimated from historical data, but they are **time-varying** in real markets.

#### Maximum Likelihood Estimation (MLE)

**Assumptions**:
- Equally-spaced observations: X(tᵢ), i = 0,1,...,N with tᵢ₊₁ - tᵢ = Δt
- Known process: dX_t = μ(θ - X_t)dt + σdW_t

**Transition Density** (exact for OU):
```
X(tᵢ₊₁) | X(tᵢ) ~ N(E[X(tᵢ₊₁)], Var[X(tᵢ₊₁)])

E[X(tᵢ₊₁)] = θ + (X(tᵢ) - θ)e^(-μΔt)
Var[X(tᵢ₊₁)] = σ²(1 - e^(-2μΔt)) / (2μ)
```

**Log-Likelihood**:
```
L(μ, θ, σ | data) = Σᵢ log p(X(tᵢ₊₁) | X(tᵢ))
```

**Optimization**: Use `scipy.optimize.minimize` to maximize L

**Python Implementation** (via ArbitrageLab):
```python
from arbitragelab.time_series_approach.ou_model import OUModelOptimalThreshold

ou_model = OUModelOptimalThreshold()
ou_model.fit(spread_series, data_frequency='1H')  # Hourly data

params = ou_model.ou_params
print(f"μ = {params['theta']}")  # Mean reversion speed
print(f"θ = {params['mu']}")     # Long-term mean
print(f"σ = {params['sigma']}")  # Volatility
```

#### Ordinary Least Squares (OLS) Approximation

**Discrete-time approximation**:
```
ΔX_t ≈ μ(θ - X_t)Δt + σ√Δt ε_t
X(tᵢ₊₁) - X(tᵢ) ≈ a + b·X(tᵢ) + ε_tᵢ

where: a = μθΔt, b = -μΔt
```

**Regression**: Fit Y = a + bX using `statsmodels.OLS`

**Parameter Recovery**:
```
μ = -b / Δt
θ = a / b  (equivalently: -a/μΔt)
σ = std(residuals) / √Δt
```

**Advantage**: Fast, simple
**Disadvantage**: Biased for small Δt (discretization error)

#### Rolling Window Estimation

**Problem**: Parameters drift over time (regime changes)

**Solution**: Estimate μ, θ, σ on rolling windows
```python
window_size = 30  # days
for t in range(window_size, len(spread)):
    window_data = spread[t-window_size:t]
    ou_model.fit(window_data)
    params_history.append(ou_model.ou_params)
```

**Challenge**: Trade-off between:
- **Short window**: Captures recent regime (but noisy estimates)
- **Long window**: Stable estimates (but lags regime changes)

**Best Practice** (from [Hudson & Thames](https://hudsonthames.org/caveats-in-calibrating-the-ou-process/)):
- Use **60-90 days** for daily data (balances bias-variance)
- Monitor **parameter stability** (flag large jumps)
- **Recalibrate boundaries** when parameters change significantly

#### Challenges & Caveats

**1. Microstructure Noise**:
- High-frequency data contaminated by bid-ask bounce
- **Result**: Overestimated μ and σ (false mean reversion)
- **Solution**: Use ultra-high-frequency estimators ([arXiv:1811.09312](https://arxiv.org/pdf/1811.09312))

**2. Non-Stationarity**:
- OU assumes stationary θ (but markets shift)
- **Detection**: Augmented Dickey-Fuller test for unit root
- **Solution**: Regime-switching models or adaptive θ

**3. Model Misspecification**:
- Real spreads may not be OU (jumps, leverage effects)
- **Test**: Residual diagnostics (QQ-plots, autocorrelation)

**Python Tools**:
- **statsmodels**: `statsmodels.tsa.stattools.adfuller` (stationarity test)
- **arch**: GARCH models for heteroskedasticity
- **statsmodels**: `AutoReg` for AR(1) approximation

---

### 2.3 Rust Implementations

**Key Finding**: Limited Rust implementations for OU processes exist compared to Python ecosystem.

**stochastic-rs Library**:
- **GitHub**: [dancixx/stochastic-rs](https://github.com/dancixx/rust-ai/tree/main/fou-lstm)
- **Features**:
  - Pure Rust implementation of stochastic processes
  - Includes fractional OU (fOU) for long memory
  - LSTM parameter estimation using `candle` (Rust ML framework)

  **Example**:
  ```rust
  use stochastic_rs::diffusions::ou::fou;

  let params = FouParams {
      mu: 0.5,      // Mean reversion level
      sigma: 0.2,   // Volatility
      theta: 1.0,   // Speed of reversion
      hurst: 0.7,   // Hurst exponent (fOU specific)
  };

  let paths = fou::simulate(params, n_steps, n_paths);
  ```

- **Performance**: Generates large datasets efficiently (GPU via `candle`)
- **Limitation**: No optimal stopping solver (just simulation)

**NautilusTrader Integration Potential**:
- NautilusTrader has **Rust core** for performance-critical components
- Could implement OU boundary computation in Rust for speed:
  1. **Volterra solver** in Rust (compile-time optimizations)
  2. **Parameter estimation** using `ndarray` + `argmin` (optimization)
  3. **Expose to Python** via PyO3 bindings (but NautilusTrader nightly uses V1 wranglers, not PyO3!)

**Blocker**: NautilusTrader nightly (v1.222.0) uses **V1 Wranglers** (not PyO3). Custom Rust extensions would require:
- Building against NautilusTrader's Rust API (complex)
- OR: Pure Python wrapper around Rust library (overhead)

**Recommendation**: Start with **Python implementation** using `numba` JIT for speed, defer Rust until proven bottleneck.

---

### 2.4 Time-Varying Boundary Implementations

**Challenge**: Optimal boundaries b_0(t), b_1(t) change continuously as time-to-expiration decreases.

#### Static vs. Dynamic Stop-Loss

| Approach | Entry | Exit | Stop-Loss | Pros | Cons |
|----------|-------|------|-----------|------|------|
| **Static** | Fixed threshold | Fixed threshold | Fixed level | Simple, fast | Ignores time decay |
| **Dynamic (ATR)** | ATR-scaled | ATR-scaled | Trailing ATR | Adapts to volatility | Not optimal (heuristic) |
| **Optimal (Finite Horizon)** | b_0(t) from Volterra | b_1(t) from Volterra | Embedded in b_1(t) | Theoretically optimal | Complex, recomputation |

#### Practical Implementation Strategies

**Strategy 1: Pre-Computed Lookup Table**

**Algorithm**:
1. **Offline**: Solve Volterra IEs for current OU parameters
   - Grid: t ∈ [0, T] with Δt = 1 hour (for daily T = 1 day)
   - Store: `[(t, b_0(t), b_1(t))...]` in database/cache
2. **Online**: Interpolate boundaries at current time t_now
   ```python
   import numpy as np

   def get_boundaries(t_now, t_grid, b0_grid, b1_grid):
       b0 = np.interp(t_now, t_grid, b0_grid)
       b1 = np.interp(t_now, t_grid, b1_grid)
       return b0, b1
   ```
3. **Update**: Recompute table when OU parameters change (e.g., daily)

**Pros**: Fast (O(1) lookup), suitable for high-frequency trading
**Cons**: Stale if parameters drift intraday

**Strategy 2: Adaptive Recomputation**

**Algorithm**:
1. **Monitor**: Track OU parameter estimates on rolling window
2. **Trigger**: Recompute boundaries if parameter change exceeds threshold:
   ```python
   if abs(mu_new - mu_old) / mu_old > 0.1:  # 10% change
       recompute_boundaries()
   ```
3. **Smooth**: Blend old/new boundaries to avoid discontinuous jumps
   ```python
   b0_new = alpha * b0_computed + (1-alpha) * b0_old
   ```

**Pros**: Adapts to regime changes
**Cons**: Computational overhead (Volterra solve takes seconds-minutes)

**Strategy 3: Heuristic Scaling**

**Algorithm**:
1. **Baseline**: Compute optimal boundaries for "average" parameters (μ̄, θ̄, σ̄)
2. **Scale**: Adjust boundaries based on current vs. average volatility:
   ```python
   b0_adjusted = b0_baseline * (sigma_current / sigma_baseline)
   b1_adjusted = b1_baseline * (sigma_current / sigma_baseline)
   ```

**Pros**: Very fast, no recomputation
**Cons**: Not theoretically justified (approximation)

**Recommendation**: Use **Strategy 1** (lookup table) for production, with **Strategy 2** (adaptive) for parameter drift detection.

---

## 3. Connection to NautilusTrader

### 3.1 NautilusTrader Architecture

**Relevant Components**:

1. **Strategy Class** (`nautilus_trader.trading.strategy.Strategy`):
   - `on_start()`: Initialize OU model, load boundary table
   - `on_data()`: Update spread, check boundaries, submit orders
   - `on_event()`: Handle fills, update position state

2. **Indicators** (Rust-native):
   - **Issue**: No native OU process indicator in NautilusTrader
   - **Solution**: Create custom Python indicator wrapping OU estimation

   ```python
   from nautilus_trader.indicators.base.indicator import Indicator

   class OUSpreadIndicator(Indicator):
       def __init__(self, window: int = 60):
           self.window = window
           self.spread_values = []

       def handle_bar(self, bar):
           # Update spread history
           spread = compute_spread(bar)  # Custom logic
           self.spread_values.append(spread)

           # Estimate OU parameters
           if len(self.spread_values) >= self.window:
               self.mu, self.theta, self.sigma = estimate_ou_params(
                   self.spread_values[-self.window:]
               )
   ```

3. **Risk Management**:
   - Use `self.trader.generate_order_id()` for market orders
   - Implement `max_quantity` checks before order submission
   - Monitor `self.cache.account()` for capital limits

4. **Data Management**:
   - **ParquetDataCatalog** for historical spread data
   - **BacktestNode** for strategy validation
   - **TradingNode** for live execution

### 3.2 Integration Architecture

**Proposed System**:

```
┌─────────────────────────────────────────────────────────────┐
│                    NautilusTrader Strategy                  │
├─────────────────────────────────────────────────────────────┤
│  1. Data Ingestion                                          │
│     ├─ Subscribe to Asset A & B bars                        │
│     └─ Compute spread: X_t = log(P_A/P_B)                   │
│                                                              │
│  2. OU Parameter Estimation (Rolling Window)                │
│     ├─ MLE estimation on 60-day window                      │
│     ├─ Update: μ, θ, σ                                      │
│     └─ Trigger boundary recomputation if change > 10%       │
│                                                              │
│  3. Optimal Boundary Computation (Offline/Periodic)         │
│     ├─ Solve Volterra IEs via Python solver                 │
│     ├─ Store: (t, b_0(t), b_1(t)) in Redis cache            │
│     └─ Interpolate boundaries at current time               │
│                                                              │
│  4. Trading Logic (on_data)                                 │
│     ├─ If no position & X_t ≤ b_0(t): Enter long spread     │
│     ├─ If long position & X_t ≥ b_1(t): Exit long spread    │
│     └─ Submit market orders via NautilusTrader API          │
│                                                              │
│  5. Risk Management                                         │
│     ├─ Position size: Kelly criterion or fixed fraction     │
│     ├─ Stop-loss: Embedded in b_1(t) (no separate order)    │
│     └─ Capital check: Ensure account.balance > required     │
└─────────────────────────────────────────────────────────────┘

External Components:
  - Redis: Boundary cache (fast lookup)
  - PostgreSQL: OU parameter history (audit trail)
  - Python solver: inteq or custom Volterra implementation
```

### 3.3 Implementation Roadmap

**Phase 1: OU Parameter Estimation (1-2 weeks)**

Tasks:
1. Implement `OUEstimator` class using MLE (ArbitrageLab as reference)
2. Add rolling window logic (30/60/90 day comparisons)
3. Create tests with synthetic OU data (known parameters)
4. Validate on real crypto pair data (BTC-ETH, BTC-SOL)

**Deliverable**: `nautilus_dev/strategies/utils/ou_estimation.py`

**Phase 2: Volterra Solver Integration (2-3 weeks)**

Tasks:
1. Evaluate `inteq` package vs. custom implementation
2. Implement backward induction algorithm for finite horizon
3. Create boundary computation function: `compute_boundaries(mu, theta, sigma, T, transaction_cost)`
4. Benchmark: Solution time vs. time discretization (target: <1 min for 24h horizon)

**Deliverable**: `nautilus_dev/strategies/utils/volterra_solver.py`

**Phase 3: Strategy Implementation (2 weeks)**

Tasks:
1. Create `OUPairsTradingStrategy` inheriting from `Strategy`
2. Integrate OU estimator + boundary computation
3. Implement spread calculation from dual bars
4. Add logging for parameter changes and boundary updates
5. Backtest on historical crypto data (Binance BTC-ETH 2024)

**Deliverable**: `nautilus_dev/strategies/ou_pairs_trading.py`

**Phase 4: Live Trading Integration (2 weeks)**

Tasks:
1. Add Redis caching for boundary lookups
2. Implement parameter drift monitoring (alerting)
3. Test on Binance testnet (paper trading)
4. Add Grafana dashboard for:
   - Spread time series with boundaries
   - OU parameter evolution (μ, θ, σ)
   - PnL attribution (entry/exit quality)
5. Production deployment with risk limits

**Deliverable**: Live strategy in `nautilus_nightly` environment

**Total Estimated Time**: 7-9 weeks

---

### 3.4 Practical Challenges & Mitigations

**Challenge 1: Volterra Solver Performance**

**Problem**: Solving Volterra IEs numerically can take minutes for fine time grids
- Example: T = 24 hours, Δt = 5 minutes → 288 time steps → O(288²) operations

**Mitigations**:
1. **Coarse grid offline**: Solve with Δt = 1 hour (24 steps), interpolate online
2. **Numba JIT**: Compile Volterra solver with `@numba.jit` (10-100x speedup)
3. **Parallel computation**: Solve multiple scenarios (different parameters) in parallel
4. **Caching**: Recompute only when parameters change >10%

**Target Performance**: <30 seconds per boundary computation

---

**Challenge 2: OU Model Validity**

**Problem**: Real spreads may violate OU assumptions (e.g., jumps during news events)

**Mitigations**:
1. **Model diagnostics**:
   - Plot residuals: Should be i.i.d. Gaussian
   - QQ-plot: Check for fat tails (indicates jumps)
   - Autocorrelation: Should decay exponentially

2. **Fallback strategy**:
   - If OU fit fails (e.g., R² < 0.5), use simpler heuristics:
     - Bollinger Bands (2σ from mean)
     - ATR-scaled thresholds

3. **Regime detection**:
   - Monitor variance ratio: Var(X_t - X_{t-1}) / Var(X_t)
   - If ratio >> 1, suspect non-stationarity → pause trading

**NautilusTrader Implementation**:
```python
class OUPairsTradingStrategy(Strategy):
    def on_start(self):
        self.ou_estimator = OUEstimator(window=60)
        self.regime_detector = RegimeDetector(threshold=0.5)

    def on_bar(self, bar):
        spread = self.compute_spread(bar)
        self.ou_estimator.update(spread)

        # Check model validity
        if not self.regime_detector.is_mean_reverting(spread):
            self.log.warning("Non-mean-reverting regime detected, pausing")
            return  # Skip trading

        # Normal trading logic
        b0, b1 = self.get_boundaries(self.clock.utc_now())
        if spread <= b0 and not self.has_position():
            self.enter_long()
```

---

**Challenge 3: Parameter Estimation Lag**

**Problem**: Rolling window estimator lags true parameter changes (e.g., volatility spikes)

**Mitigations**:
1. **Exponential weighting**: Give more weight to recent data
   ```python
   weights = np.exp(-lambda * np.arange(window_size)[::-1])
   weights /= weights.sum()
   # Use in weighted MLE
   ```

2. **Adaptive window size**:
   - Increase window during calm periods (stable estimates)
   - Decrease window during volatile periods (responsive estimates)

3. **Kalman filter**: Treat OU parameters as hidden state, update online
   - More complex but handles time-varying parameters gracefully

**Recommended**: Start with fixed 60-day window, add exponential weighting if lag observed in backtests

---

**Challenge 4: Finite Horizon Definition**

**Problem**: What is the "expiration" T for pairs trading? (No natural maturity like options)

**Solutions**:
1. **Rolling horizon**: Set T = 1 day, recompute boundaries daily
   - Treat each day as independent trading opportunity
   - Terminal condition: Liquidate by end of day (avoid overnight risk)

2. **Event-based horizon**: Set T based on mean reversion time
   - Estimate: E[τ_revert] = 1/μ (expected time to revert)
   - Set T = 2/μ or 3/μ (capture full cycle)

3. **Strategy-specific**: Align with trading session
   - Example: Crypto 24/7 → T = 24 hours
   - Example: US equities → T = 6.5 hours (9:30 AM - 4:00 PM)

**Practical Choice**: Use **T = 24 hours** for crypto (aligns with daily rhythm), recompute at midnight UTC

---

**Challenge 5: Transaction Costs in Live Trading**

**Problem**: Paper assumes fixed transaction cost c, but real costs are:
- Proportional (bps of notional)
- Variable (market impact for large orders)
- Asymmetric (taker > maker fees)

**NautilusTrader Modeling**:
```python
# Account for maker/taker fees
entry_cost = spread_value * (taker_fee_A + taker_fee_B)  # Market order
exit_cost = spread_value * (maker_fee_A + maker_fee_B)   # Limit order

# Adjust boundaries
b0_adjusted = b0_theoretical - entry_cost / spread_value
b1_adjusted = b1_theoretical + exit_cost / spread_value
```

**Best Practice**:
- Use conservative cost estimates in Volterra solver (e.g., 10 bps per leg)
- Monitor realized costs in backtests, adjust c accordingly
- Add slippage buffer (e.g., 5% wider no-trade zone)

---

## 4. Practical Applicability Assessment

### 4.1 Strengths of Optimal Stopping Approach

**1. Theoretical Rigor**:
- Provably optimal under OU model assumptions
- Accounts for time decay (finite horizon)
- Incorporates transaction costs explicitly

**2. Dynamic Adaptation**:
- Boundaries adjust as expiration approaches
- Responds to parameter changes (regime shifts)
- No ad-hoc threshold selection

**3. Risk Control**:
- Stop-loss implicitly embedded in exit boundary b_1(t)
- Maximum loss bounded by entry-exit spread
- Avoids over-trading (no-trade zone)

### 4.2 Weaknesses & Limitations

**1. Model Risk**:
- Real spreads may not be OU (jumps, non-stationarity)
- Parameter estimates are noisy (estimation error)
- Assumes continuous trading (but exchanges have latency)

**2. Computational Complexity**:
- Volterra solver not real-time (seconds to minutes)
- Requires periodic recomputation (not tick-by-tick adaptive)
- Boundary interpolation adds latency

**3. Implementation Challenges**:
- No off-the-shelf NautilusTrader integration
- Requires custom Volterra solver (or adapt ArbitrageLab)
- Testing/validation needs synthetic + real data

**4. Practical Deviations**:
- Ignores market microstructure (order book depth, maker/taker)
- Assumes infinite liquidity (no market impact)
- Fixed transaction cost c (real costs vary with size)

### 4.3 Scorecard (0-100)

| Criterion | Score | Justification |
|-----------|-------|---------------|
| **Theoretical Soundness** | 95 | Rigorous mathematical framework, published in top journal |
| **Computational Feasibility** | 70 | Volterra solver works but not real-time (pre-computation required) |
| **Parameter Estimation** | 65 | MLE feasible but suffers from lag and model misspecification |
| **NautilusTrader Integration** | 60 | Requires custom development (no native support) |
| **Backtesting Readiness** | 75 | Can implement in Python, test on historical data |
| **Live Trading Readiness** | 50 | Needs Redis caching, parameter monitoring, regime detection |
| **Robustness to Model Error** | 55 | Sensitive to OU assumption violations (jumps, non-stationarity) |
| **Scalability** | 70 | Works for single pair, but multi-pair requires parallel solvers |
| **Risk Management** | 80 | Stop-loss implicit, but no position sizing optimization |
| **Practicality** | 65 | Better than ad-hoc rules, but simpler alternatives exist (ATR stops) |

**Overall Applicability**: 68/100

**Verdict**: **Moderately Practical** for advanced quant traders with:
- Expertise in numerical methods (Volterra solvers)
- Infrastructure for parameter estimation (rolling windows)
- Computational resources (pre-computation + caching)
- Risk controls for model breakdown (regime detection)

**Not Recommended For**:
- Beginner traders (too complex)
- High-frequency strategies (latency issues)
- Multi-pair portfolios without parallel infrastructure

---

### 4.4 Comparison with Alternatives

| Approach | Complexity | Optimality | Robustness | NautilusTrader Support |
|----------|------------|------------|------------|------------------------|
| **Fixed Thresholds** (e.g., ±2σ) | Low | Poor | Medium | Native (`>` `<` operators) |
| **ATR-Based Dynamic** | Medium | Medium | High | Native (`ATR` indicator) |
| **Bollinger Bands** | Low | Medium | Medium | Native (`BollingerBands`) |
| **Optimal Stopping (Infinite Horizon)** | Medium | High | Medium | Via ArbitrageLab (offline) |
| **Optimal Stopping (Finite Horizon)** | **High** | **Highest** | **Low** | **Custom only** |
| **Stochastic Control (Mudchanatongsuk)** | Very High | Highest (with sizing) | Low | Custom only |
| **Machine Learning** (LSTM boundaries) | High | Unknown | Medium | Via PyTorch/TF integration |

**When to Use Optimal Stopping (Finite Horizon)**:
- **High Sharpe ratio pairs** (>1.5): Optimization worth the effort
- **Stable OU parameters** (low regime switching): Model assumptions hold
- **Long holding periods** (days): Time to amortize computation cost
- **Research-driven**: Interested in theoretical best-case performance

**When to Use Alternatives**:
- **High-frequency trading**: Use ATR or simple thresholds (low latency)
- **Unstable markets**: Use ML or adaptive heuristics (robust to model error)
- **Quick deployment**: Use Bollinger Bands or fixed thresholds (fast to code)

---

## 5. Recommendations for NautilusTrader Implementation

### 5.1 Short-Term (Next 4 Weeks)

**Objective**: Validate OU model on real data

**Tasks**:
1. **Data Collection**:
   - Download 1 year of Binance BTC-USDT, ETH-USDT data (1-minute bars)
   - Compute spread: X_t = log(BTC/ETH)
   - Store in ParquetDataCatalog

2. **OU Parameter Estimation**:
   - Implement MLE estimator (reference: ArbitrageLab)
   - Test on synthetic OU data (validate accuracy)
   - Apply to BTC-ETH spread (check stationarity via ADF test)
   - Plot parameter evolution (rolling 60-day window)

3. **Model Validation**:
   - Residual analysis: QQ-plot, autocorrelation
   - Half-life estimation: τ = log(2)/μ (expected reversion time)
   - Compare with Bollinger Band strategy (benchmark)

**Deliverable**: Report on OU model fit quality + parameter stability

**Decision Point**: If R² > 0.6 and ADF p-value < 0.05 → proceed to Phase 2. Otherwise, use ATR-based strategy.

---

### 5.2 Medium-Term (Next 8 Weeks)

**Objective**: Implement Volterra solver + backtest strategy

**Tasks**:
1. **Volterra Solver**:
   - Adapt `inteq` package for Kitapbayev-Leung integral equations
   - Implement backward induction (Δt = 1 hour, T = 24 hours)
   - Benchmark performance: Target <1 minute per solve
   - Cache solutions in Redis (key: `(mu, theta, sigma, T)`)

2. **Backtest Strategy**:
   - Create `OUPairsTradingStrategy` class
   - On `on_start()`: Load pre-computed boundaries
   - On `on_bar()`: Check spread vs. b_0(t), b_1(t)
   - Submit market orders (no limit orders for simplicity)
   - Log all trades + OU parameters for analysis

3. **Performance Analysis**:
   - Metrics: Sharpe ratio, max drawdown, win rate
   - Compare vs. baselines:
     - Buy & hold spread
     - Bollinger Band strategy (±2σ)
     - ATR-based strategy
   - Sensitivity analysis: Vary transaction cost c (5-20 bps)

**Deliverable**: Backtest report with PnL curves + boundary visualizations

**Decision Point**: If Sharpe ratio > Bollinger baseline → proceed to live testing. Otherwise, investigate parameter sensitivity.

---

### 5.3 Long-Term (Next 6 Months)

**Objective**: Deploy to live trading with monitoring

**Tasks**:
1. **Infrastructure**:
   - Set up Redis for boundary caching (TTL = 1 hour)
   - PostgreSQL for parameter history (audit trail)
   - Grafana dashboard:
     - Panel 1: Spread with b_0(t), b_1(t) overlays
     - Panel 2: OU parameters (μ, θ, σ) time series
     - Panel 3: PnL curve + Sharpe ratio
     - Panel 4: Trade log (entry/exit events)

2. **Monitoring & Alerts**:
   - Parameter drift: Alert if Δμ > 20% in 1 day
   - Model breakdown: Alert if ADF p-value > 0.1
   - Trading anomalies: Alert if no trades for 7 days (cointegration broken?)

3. **Live Deployment**:
   - Start with Binance testnet (paper trading)
   - Run for 30 days, validate behavior
   - Migrate to live with small capital (<1% portfolio)
   - Scale if Sharpe ratio > 1.0 for 90 days

4. **Continuous Improvement**:
   - A/B test: Finite horizon vs. infinite horizon boundaries
   - Add position sizing: Kelly criterion or constant volatility
   - Multi-pair extension: BTC-ETH, BTC-SOL, ETH-SOL (correlation matrix)

**Deliverable**: Production-ready strategy with 3-month track record

---

### 5.4 Research Extensions

**Potential Improvements**:

1. **Stop-Loss Integration**:
   - Extend Kitapbayev-Leung (2025) to include explicit stop-loss level S
   - Derive modified Volterra IEs with boundary conditions at S
   - Compare with Leung & Li (2015) infinite horizon + stop-loss

2. **Regime-Switching OU**:
   - Use Hidden Markov Model (HMM) to detect regimes
   - Estimate separate (μ₁, θ₁, σ₁) for regime 1, (μ₂, θ₂, σ₂) for regime 2
   - Compute boundaries for each regime, switch dynamically

3. **Portfolio Extension**:
   - Optimize position sizes across multiple pairs
   - Constraint: Total capital, correlation matrix
   - Method: Convex optimization (CVXPY) with OU boundary constraints

4. **Deep Learning Boundaries**:
   - Train LSTM to predict b_0(t), b_1(t) from features:
     - Current spread, volatility, volume
     - Historical OU parameters
   - Loss: Sharpe ratio on validation set
   - Advantage: Avoids Volterra solver (fast online inference)

---

## 6. Key Takeaways

### 6.1 Summary of Findings

**Academic Contribution**:
- **Kitapbayev & Leung (2025)** provides rigorous finite-horizon framework
- Extends prior work (Leung & Li 2015, Kitapbayev 2017) to coupled stopping
- Solution via Volterra integral equations (no closed form)

**Practical Implementation**:
- **ArbitrageLab** has infinite-horizon solver (Leung & Li 2015)
- **No existing** finite-horizon solver (requires custom development)
- **OU parameter estimation** well-studied (MLE, OLS) but faces lag/noise issues

**NautilusTrader Fit**:
- **Feasible** but requires significant custom development
- **Backtest-ready** in Python (no Rust bottleneck yet)
- **Live trading** needs infrastructure (Redis, monitoring, regime detection)

**Comparison with Alternatives**:
- **More optimal** than heuristics (Bollinger, ATR) under OU assumptions
- **Less robust** to model misspecification (jumps, regime shifts)
- **Higher complexity** (development + maintenance cost)

---

### 6.2 Go/No-Go Decision Framework

**Proceed with Optimal Stopping Implementation IF**:
1. ✅ OU model fits data well (R² > 0.6, ADF p < 0.05)
2. ✅ Parameter stability (μ, θ, σ don't jump >30% week-over-week)
3. ✅ Team has numerical methods expertise (Volterra solvers)
4. ✅ Infrastructure ready (Redis, Grafana, parameter monitoring)
5. ✅ Backtests show >0.3 Sharpe improvement over baselines

**Use Simpler Alternatives IF**:
1. ❌ OU model poor fit (R² < 0.5, non-stationary residuals)
2. ❌ High regime switching (parameters unstable)
3. ❌ Limited development time (<4 weeks)
4. ❌ Need low latency (< 100ms response time)
5. ❌ Backtests show marginal improvement (<0.1 Sharpe delta)

---

### 6.3 Next Steps

**Immediate (This Week)**:
1. Download BTC-ETH historical data (Binance 2024)
2. Run OU parameter estimation (ArbitrageLab)
3. Assess model fit quality (R², ADF test, half-life)

**Short-Term (Next Month)**:
1. Implement Volterra solver (adapt `inteq` or custom)
2. Backtest optimal stopping strategy
3. Compare with Bollinger Band baseline

**Medium-Term (Next Quarter)**:
1. Deploy to testnet (Binance paper trading)
2. Build Grafana monitoring dashboard
3. Collect 30-day live performance data

**Long-Term (6 Months)**:
1. Production deployment (small capital)
2. Research extensions (regime-switching, ML boundaries)
3. Multi-pair portfolio optimization

---

## 7. References

### 7.1 Academic Papers

**Primary**:
- Kitapbayev, Y., & Leung, T. (2025). A Coupled Optimal Stopping Approach to Pairs Trading over a Finite Horizon. *Computational Economics*. [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5653650)

**Foundational**:
- Leung, T., & Li, X. (2015). Optimal Mean Reversion Trading with Transaction Costs and Stop-Loss Exit. *International Journal of Theoretical and Applied Finance*, 18(3). [arXiv:1411.5062](https://arxiv.org/abs/1411.5062)
- Kitapbayev, Y., & Leung, T. (2017). Optimal Mean-Reverting Spread Trading: Nonlinear Integral Equation Approach. [arXiv:1701.00875](https://arxiv.org/abs/1701.00875)

**Stochastic Control**:
- Mudchanatongsuk, S., Primbs, J. A., & Wong, W. (2008). Optimal Pairs Trading: A Stochastic Control Approach. *IEEE Conference Publication*. [IEEE](https://ieeexplore.ieee.org/document/4586628/)
- Tourin, A., & Yan, R. (2013). Dynamic Pairs Trading Using the Stochastic Control Approach. *Journal of Economic Dynamics and Control*.
- Pham, H., & Ngo, M. (2016). A Singular Stochastic Control Approach for Optimal Pairs Trading with Proportional Transaction Costs. [arXiv:1911.10450](https://arxiv.org/abs/1911.10450)

**Parameter Estimation**:
- Estimation of Ornstein-Uhlenbeck Process Using Ultra-High-Frequency Data. [arXiv:1811.09312](https://arxiv.org/pdf/1811.09312)

### 7.2 Practical Implementations

**Python Libraries**:
- Hudson & Thames ArbitrageLab: [GitHub](https://github.com/hudson-and-thames/arbitragelab) | [Docs](https://hudson-and-thames-arbitragelab.readthedocs-hosted.com/)
- inteq (Volterra solvers): [PyPI](https://pypi.org/project/inteq/)
- nssvie (Stochastic Volterra): [PyPI](https://pypi.org/project/nssvie/)

**Rust Libraries**:
- stochastic-rs: [GitHub](https://github.com/dancixx/rust-ai/tree/main/fou-lstm)

### 7.3 NautilusTrader Resources

**Documentation**:
- Strategy Guide: [NautilusTrader Docs](https://nautilustrader.io/docs/latest/concepts/strategies/)
- GitHub Pairs Trading Example: [Nautilus_Pair_Trading_Jerry](https://github.com/zr7goat/Nautilus_Pair_Trading_Jerry)

**Discord Discussions**:
- `/media/sam/1TB/nautilus_dev/docs/discord/questions.md` (line 560: pairs trading timestamp sync)
- `/media/sam/1TB/nautilus_dev/docs/discord/help.md` (mean reversion discussions)

### 7.4 Educational Resources

**Tutorials**:
- Hudson & Thames: [Optimal Stopping in Pairs Trading](https://hudsonthames.org/optimal-stopping-in-pairs-trading-ornstein-uhlenbeck-model/)
- IBKR Quant Blog: [OU Model for Pairs Trading](https://www.interactivebrokers.com/campus/ibkr-quant-news/optimal-stopping-in-pairs-trading-ornstein-uhlenbeck-model/)
- QuantStart: [OU Simulation with Python](https://www.quantstart.com/articles/ornstein-uhlenbeck-simulation-with-python/)

**Books**:
- Leung, T., & Li, X. (2015). *Optimal Mean Reversion Trading: Mathematical Analysis and Practical Applications*. World Scientific.

**Blog Posts**:
- Hudson & Thames: [Caveats in Calibrating the OU Process](https://hudsonthames.org/caveats-in-calibrating-the-ou-process/)
- Hudson & Thames: [Pairs Trading with Stochastic Control](https://hudsonthames.org/pairs-trading-with-stochastic-control-and-ou-process/)

---

## Appendix A: Glossary

**Ornstein-Uhlenbeck (OU) Process**: Mean-reverting stochastic process with SDE `dX_t = μ(θ - X_t)dt + σdW_t`

**Volterra Integral Equation**: Equation where solution y(t) depends on integral of y(s) for s ≤ t (memory effect)

**Optimal Stopping**: Problem of choosing the best time to take an action (e.g., enter/exit trade) to maximize expected reward

**Coupled Stopping Problems**: Multiple linked optimal stopping problems (e.g., V_0 for no position, V_1 for long position)

**Free Boundary**: Unknown boundary b(t) where optimal action switches (e.g., from "wait" to "enter")

**Backward Induction**: Numerical method solving from terminal time T backwards to t = 0

**Maximum Likelihood Estimation (MLE)**: Statistical method to estimate parameters by maximizing likelihood of observed data

**Augmented Dickey-Fuller (ADF) Test**: Statistical test for unit root (non-stationarity) in time series

**Half-Life**: Expected time τ = log(2)/μ for OU process to revert halfway to mean

**Sharpe Ratio**: Risk-adjusted return metric: (mean return - risk-free rate) / std deviation of returns

---

## Appendix B: Code Snippets

### B.1 OU Parameter Estimation (MLE)

```python
import numpy as np
from scipy.optimize import minimize

def ou_mle(data, dt=1.0):
    """
    Estimate OU parameters via Maximum Likelihood.

    Args:
        data: Array of observations [X_0, X_1, ..., X_N]
        dt: Time step between observations

    Returns:
        dict: {'mu': mean reversion speed, 'theta': long-term mean, 'sigma': volatility}
    """
    X = data[:-1]
    Y = data[1:]
    N = len(X)

    def neg_log_likelihood(params):
        mu, theta, sigma = params
        if mu <= 0 or sigma <= 0:
            return 1e10  # Invalid parameters

        # Expected value and variance
        E_Y = theta + (X - theta) * np.exp(-mu * dt)
        Var_Y = sigma**2 * (1 - np.exp(-2 * mu * dt)) / (2 * mu)

        # Log-likelihood
        ll = -0.5 * N * np.log(2 * np.pi * Var_Y) - np.sum((Y - E_Y)**2) / (2 * Var_Y)
        return -ll

    # Initial guess (OLS approximation)
    b = np.polyfit(X, Y - X, 1)[0] / dt
    initial_guess = [-b, np.mean(data), np.std(np.diff(data)) / np.sqrt(dt)]

    result = minimize(neg_log_likelihood, initial_guess, method='L-BFGS-B',
                      bounds=[(1e-6, None), (None, None), (1e-6, None)])

    mu, theta, sigma = result.x
    return {'mu': mu, 'theta': theta, 'sigma': sigma}

# Example usage
spread_data = np.array([...])  # Your spread time series
params = ou_mle(spread_data, dt=1/24)  # Hourly data (dt in days)
print(f"Half-life: {np.log(2) / params['mu']:.2f} days")
```

### B.2 Volterra Solver (Backward Induction)

```python
import numpy as np
from scipy.integrate import quad

def solve_volterra_backward(mu, theta, sigma, r, c, T, n_steps=100):
    """
    Solve Volterra IE for optimal boundaries via backward induction.

    Args:
        mu, theta, sigma: OU parameters
        r: Discount rate
        c: Transaction cost
        T: Time horizon
        n_steps: Number of time discretization steps

    Returns:
        t_grid, b0_grid, b1_grid: Time grid and boundaries
    """
    dt = T / n_steps
    t_grid = np.linspace(0, T, n_steps + 1)

    # Initialize boundaries (terminal conditions)
    b0 = np.full(n_steps + 1, -np.inf)
    b1 = np.full(n_steps + 1, (mu * theta + r * c) / (mu + r))

    # Backward induction
    for i in range(n_steps - 1, -1, -1):
        t = t_grid[i]

        # Solve nonlinear equation for b0[i] (simplified version)
        # In practice, use root-finding on full Volterra IE
        # Here: heuristic based on expected value
        b0[i] = theta - sigma * np.sqrt(T - t)

        # Solve for b1[i] (similar approach)
        b1[i] = theta + sigma * np.sqrt(T - t) + c

    return t_grid, b0, b1

# Example usage
t, b0, b1 = solve_volterra_backward(mu=2.0, theta=0.0, sigma=0.3, r=0.05, c=0.01, T=1.0)

import matplotlib.pyplot as plt
plt.plot(t, b0, label='Entry boundary b_0(t)')
plt.plot(t, b1, label='Exit boundary b_1(t)')
plt.axhline(0, color='black', linestyle='--', label='Mean θ')
plt.xlabel('Time to expiration (T - t)')
plt.ylabel('Spread level')
plt.legend()
plt.title('Optimal Trading Boundaries')
plt.show()
```

### B.3 NautilusTrader Strategy Skeleton

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import Bar
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.enums import OrderSide
import numpy as np

class OUPairsTradingStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.instrument_a = None
        self.instrument_b = None
        self.spread_history = []
        self.ou_params = None
        self.boundaries = None

    def on_start(self):
        # Subscribe to bars
        self.subscribe_bars(self.instrument_a)
        self.subscribe_bars(self.instrument_b)

        # Load pre-computed boundaries from cache
        # self.boundaries = load_from_redis(...)

    def on_bar(self, bar: Bar):
        # Compute spread
        price_a = self.cache.price(self.instrument_a, PriceType.MID)
        price_b = self.cache.price(self.instrument_b, PriceType.MID)
        spread = np.log(price_a / price_b)

        self.spread_history.append(spread)

        # Update OU parameters (rolling window)
        if len(self.spread_history) >= 60:
            self.ou_params = ou_mle(self.spread_history[-60:])

        # Get current boundaries
        t_now = (self.clock.utc_now() - self.get_today_start()).total_seconds() / 86400
        b0, b1 = self.interpolate_boundaries(t_now)

        # Trading logic
        position = self.cache.position(self.id)

        if position is None and spread <= b0:
            self.enter_long_spread()
        elif position is not None and spread >= b1:
            self.exit_long_spread()

    def enter_long_spread(self):
        # Long A, short B
        self.submit_order(self.market_order(self.instrument_a, OrderSide.BUY, quantity=1.0))
        self.submit_order(self.market_order(self.instrument_b, OrderSide.SELL, quantity=1.0))

    def exit_long_spread(self):
        # Close positions
        self.submit_order(self.market_order(self.instrument_a, OrderSide.SELL, quantity=1.0))
        self.submit_order(self.market_order(self.instrument_b, OrderSide.BUY, quantity=1.0))

    def interpolate_boundaries(self, t):
        # Linear interpolation from cached grid
        # return np.interp(t, self.boundaries['t'], self.boundaries['b0']), ...
        pass
```

---

**End of Research Summary**

**Prepared by**: Claude Code (Sonnet 4.5)
**Date**: 2025-12-28
**Location**: `/media/sam/1TB/nautilus_dev/specs/011-stop-loss-position-limits/research_summary.md`
