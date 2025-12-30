# Research: Stop-Loss & Position Limits

**Spec**: 011-stop-loss-position-limits
**Date**: 2025-12-28
**Status**: Complete

## Academic Foundation

### Paper Analysis: Kitapbayev & Leung (2025)

**Title**: "A Coupled Optimal Stopping Approach to Pairs Trading over a Finite Horizon"

#### Key Contributions

1. **Ornstein-Uhlenbeck (OU) Model for Spreads**:
   ```
   dX_t = μ(θ - X_t)dt + σdW_t
   ```
   - μ: Speed of mean reversion (higher = faster return to mean)
   - θ: Long-term mean level
   - σ: Volatility
   - W_t: Standard Brownian motion

2. **Coupled Optimal Stopping System**:
   - V_0(t,x): Value function in state 0 (no position)
   - V_1(t,x): Value function in state 1 (long position)
   - Functions are linked through switching decisions

3. **Time-Varying Trading Boundaries**:
   - b_0(t): Entry boundary (buy when spread ≤ b_0(t))
   - b_1(t): Exit boundary (sell when spread ≥ b_1(t))
   - **Terminal conditions**: b_0(T-) = -∞, b_1(T-) = (μθ + rc)/(μ + r)

4. **Volterra-Type Integral Equations**:
   - Recursive backward solution
   - Numerical discretization: N time steps
   - Convergence shown in Table 1 (paper)

#### Parameter Sensitivity

| Parameter | Effect on b_0 (entry) | Effect on b_1 (exit) |
|-----------|----------------------|---------------------|
| μ ↑ (faster reversion) | Moves higher | Moves lower → narrower band |
| σ ↑ (higher volatility) | Moves lower | Moves higher → wider band |
| c ↑ (higher cost) | Moves lower | Moves higher → wider band |

#### Practical Implementation Insights

1. **Why time-varying boundaries matter**:
   - Near deadline T: boundaries diverge sharply
   - Far from T: boundaries converge to infinite-horizon constants
   - **Implication**: Static stop-loss is suboptimal

2. **Three-state extension** (Section 5):
   - State -1: Short position
   - Four boundaries: b_{0,1}, b_{0,-1}, b_1, b_{-1}
   - More realistic for futures/margin trading

---

## Decision 1: Static vs Dynamic Stop-Loss

**Options Considered**:

1. **Option A: Static Stop-Loss** (percentage-based)
   - Pros: Simple to implement, easy to understand
   - Cons: Theoretically suboptimal, doesn't adapt to market conditions

2. **Option B: Dynamic Stop-Loss** (OU-based boundaries)
   - Pros: Theoretically optimal, adapts to time-to-horizon
   - Cons: Complex implementation, requires OU parameter estimation

3. **Option C: Hybrid Approach** (static with dynamic override)
   - Pros: Practical default with optional sophistication
   - Cons: More code paths to test

**Selected**: Option C - Hybrid Approach

**Rationale**:
- Static stop-loss covers 95% of use cases (simple strategies)
- Dynamic mode available for pairs trading / mean-reversion strategies
- Aligns with NautilusTrader's configuration-driven approach

---

## Decision 2: Stop Order Type

**Options Considered**:

1. **Option A: STOP_MARKET** (default)
   - Pros: Guaranteed fill, simpler logic
   - Cons: May slip in gaps

2. **Option B: STOP_LIMIT**
   - Pros: Better price control
   - Cons: May not fill at all

3. **Option C: Emulated Stop** (strategy-managed)
   - Pros: Full control, works with any venue
   - Cons: Latency, requires constant monitoring

**Selected**: Option A - STOP_MARKET as default, Option C as fallback

**Rationale**:
- Binance/Bybit now support STOP_MARKET via Algo Order API
- Emulated mode for venues without native support
- `reduce_only=True` prevents position flip errors

---

## Decision 3: Position Limit Implementation

**Options Considered**:

1. **Option A: RiskEngine Configuration**
   - Use `RiskEngineConfig.max_notional_per_order`
   - Pros: Built-in, validated at engine level
   - Cons: Limited granularity

2. **Option B: Strategy-Level Validation**
   - Custom `validate_order()` before submission
   - Pros: Full control, per-instrument limits
   - Cons: Must implement ourselves

3. **Option C: Combined Approach**
   - RiskEngine for global limits, Strategy for per-instrument
   - Pros: Defense in depth
   - Cons: More configuration

**Selected**: Option C - Combined Approach

**Rationale**:
- RiskEngine catches balance violations automatically
- Strategy-level adds instrument-specific max position
- Consistent with "defense in depth" trading principle

---

## NautilusTrader API Reference

### Stop Order Creation

```python
# StopMarketOrder (recommended)
stop_loss_order = self.order_factory.stop_market(
    instrument_id=instrument_id,
    order_side=OrderSide.SELL,  # For LONG stop-loss
    quantity=quantity,
    trigger_price=instrument.make_price(stop_price),
    reduce_only=True,  # CRITICAL: prevents position flip
)

# TrailingStopMarket (for trailing stops)
order = self.order_factory.trailing_stop_market(
    instrument_id=instrument_id,
    order_side=OrderSide.SELL,
    quantity=quantity,
    trailing_offset=Decimal("0.01"),
    trailing_offset_type=TrailingOffsetType.PRICE,
    trigger_type=TriggerType.DEFAULT,
    reduce_only=True,
)
```

### Position Event Handling

```python
def on_event(self, event: Event) -> None:
    if isinstance(event, PositionOpened):
        self._create_stop_loss(event)
    elif isinstance(event, PositionClosed):
        self._cancel_stop_loss(event)
    elif isinstance(event, PositionChanged):
        self._update_stop_loss(event)
```

### Cache Access

```python
# Get open positions
positions = self.cache.positions_open(instrument_id)

# Check if net long
is_long = self.portfolio.is_net_long(instrument_id)

# Get position by ID
position = self.cache.position(position_id)
```

### RiskEngine Configuration

```python
from nautilus_trader.config import RiskEngineConfig

risk_config = RiskEngineConfig(
    max_order_submit_rate="100/00:00:01",  # 100 per second
    max_order_modify_rate="100/00:00:01",
    max_notional_per_order={"BTC/USDT.BINANCE": "10000"},  # Max $10k per order
)
```

---

## Known Issues & Workarounds

### Issue 1: Bybit Trigger Direction (FIXED in Rust adapter)

**Problem**: Stop orders triggering immediately regardless of price direction.

**Solution**: Use Rust-based nightly wheels (Python adapter has bug).

**Verification**:
- STOP BUY triggers when price >= trigger_price
- STOP SELL triggers when price <= trigger_price
- SHORT stop-loss: trigger ABOVE entry
- LONG stop-loss: trigger BELOW entry

### Issue 2: Binance STOP_MARKET API Change

**Problem**: `{'code': -4120, 'msg': 'Use Algo Order API'}`

**Solution**: Use nightly version after 2025-12-10.

**Commit**: `62ef6f63a025fae5300da405b218fc625d7b7f97`

### Issue 3: Backtest Stop Fill Prices

**Problem**: Stop orders filling at trigger price even in gaps.

**Solution**: Use `BestPriceFillModel` for realistic fills.

**Commit**: `e394d48bf783ea3da151315071f3bd67ad010f1d`

### Issue 4: Bracket Orders NOT OCO

**Problem**: NautilusTrader bracket orders don't automatically cancel other leg.

**Solution**: Manually cancel remaining leg on fill:
```python
def on_order_filled(self, event: OrderFilled) -> None:
    if event.order.client_order_id == self.take_profit_id:
        self.cancel_order(self.stop_loss_order)
    elif event.order.client_order_id == self.stop_loss_id:
        self.cancel_order(self.take_profit_order)
```

---

## OU Parameter Estimation

For dynamic stop-loss based on optimal stopping theory:

### Option 1: statsmodels (Simple)

```python
import numpy as np
from scipy.optimize import minimize

def estimate_ou_params(prices: np.ndarray, dt: float = 1.0) -> tuple[float, float, float]:
    """Estimate OU parameters via MLE."""
    n = len(prices) - 1
    x = prices[:-1]
    y = prices[1:]

    # Regression: y = a + b*x + noise
    sx, sy = x.sum(), y.sum()
    sxx, sxy, syy = (x*x).sum(), (x*y).sum(), (y*y).sum()

    b = (n*sxy - sx*sy) / (n*sxx - sx*sx)
    a = (sy - b*sx) / n

    residuals = y - (a + b*x)
    sigma_hat = np.sqrt(residuals.var())

    # Convert to OU params
    mu = -np.log(b) / dt  # Speed of mean reversion
    theta = a / (1 - b)    # Long-term mean
    sigma = sigma_hat * np.sqrt(2*mu / (1 - b**2))

    return mu, theta, sigma
```

### Option 2: arch library (Rolling estimation)

```python
from arch import arch_model

# For time-varying volatility
model = arch_model(returns, vol='Garch', p=1, q=1)
result = model.fit()
sigma_t = result.conditional_volatility
```

---

## Implementation Recommendations

### Phase 1: Static Stop-Loss (MVP)

1. `RiskConfig` Pydantic model with stop_loss_pct
2. `RiskManager` class attached to Strategy
3. Hook into PositionOpened/Closed events
4. Use `order_factory.stop_market()` with `reduce_only=True`

### Phase 2: Position Limits

1. Add `max_position_size` to RiskConfig
2. Pre-flight check in `validate_order()`
3. Integrate with RiskEngineConfig for global limits

### Phase 3: Advanced (Optional)

1. Trailing stop support
2. Dynamic OU-based boundaries
3. OCO emulation for TP/SL pairs

---

## References

1. Kitapbayev, Y. & Leung, T. (2025). "A Coupled Optimal Stopping Approach to Pairs Trading over a Finite Horizon"
2. Leung, T. & Li, X. (2015). "Optimal mean reversion trading with transaction costs and stop-loss exit"
3. Leung, T. & Li, X. (2016). "Optimal Mean Reversion Trading: Mathematical Analysis and Practical Applications"
4. NautilusTrader Discord Knowledge Base (2025)
5. NautilusTrader GitHub Issues #3287 (Binance API change)
