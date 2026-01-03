# Market Making Implementation Guide
## Based on "Algorithmic and High-Frequency Trading" by Álvaro Cartea et al.

**Document Version**: 1.0
**Generated**: 2026-01-03
**Source**: Cartea, Álvaro, et al. "Algorithmic and High-Frequency Trading." Cambridge University Press, 2015.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Market Making Theory (Chapter 2 & 10)](#market-making-theory)
3. [Mathematical Models](#mathematical-models)
4. [Implementation Roadmap](#implementation-roadmap)
5. [NautilusTrader Integration](#nautilustrader-integration)
6. [Data Requirements](#data-requirements)
7. [Risk Management](#risk-management)
8. [Testing Strategy](#testing-strategy)

---

## Executive Summary

This document extracts all Market Making (MM) concepts from Cartea's book and maps them to NautilusTrader implementation. The book covers three primary MM strategies:

1. **Market Making with No Inventory Restrictions** (Section 10.2.1)
2. **Market Making At-The-Touch** (Section 10.2.2)
3. **Utility Maximising Market Maker** (Section 10.3)
4. **Market Making with Adverse Selection** (Section 10.4)

**Key Insight**: Market makers face a fundamental trade-off between:
- **Execution frequency** (how often their quotes get filled)
- **Expected profit per trade** (spread they capture)

This is controlled via **spread optimization** and **quote placement strategies**.

---

## Market Making Theory

### 2.1 Grossman-Miller Market Making Model (Chapter 2)

#### Core Concepts

**Definition**: Market makers provide liquidity by posting bid/ask quotes and profit from:
1. **Bid-ask spread** - Difference between sell and buy prices
2. **Inventory management** - Balancing long/short positions to minimize risk

**Economic Forces**:
- **Inventory Risk**: Holding positions exposes MM to adverse price movements
- **Adverse Selection**: Informed traders target MM quotes when they have superior information
- **Trading Costs**: Transaction fees, market impact, and operational costs

#### 2.1.1 Trading Costs (Page 24)

Market makers face three types of costs:

1. **Explicit Costs**:
   - Exchange fees (maker/taker fees)
   - Clearing and settlement fees
   - Technology infrastructure (colocation)

2. **Implicit Costs**:
   - Bid-ask spread (captured by MM, cost to liquidity traders)
   - Market impact (price movement from large orders)
   - Opportunity cost of capital

3. **Information Costs**:
   - Adverse selection (trading with better-informed counterparties)
   - Winner's curse (getting filled only when price moves against you)

#### 2.1.3 Measuring Liquidity (Page 26)

**Liquidity Metrics** for market making:

1. **Spread Metrics**:
   - Quoted spread: `S_quoted = P_ask - P_bid`
   - Effective spread: `S_eff = 2 * |P_trade - P_mid|`
   - Realized spread: `S_realized = 2 * (P_trade - P_mid_future)`

2. **Depth Metrics**:
   - Volume at best bid/ask
   - Cumulative volume at each price level
   - Order book imbalance: `OBI = (V_bid - V_ask) / (V_bid + V_ask)`

3. **Resilience Metrics**:
   - Time to replenish liquidity after large trade
   - Price impact decay rate

#### 2.1.4 Market Making using Limit Orders (Page 28)

**Quote Placement Strategies**:

Market makers face the **frequency-profitability trade-off**:

- **Tight spreads** (close to mid-price):
  - Higher fill probability
  - Lower profit per trade
  - More inventory risk

- **Wide spreads** (far from mid-price):
  - Lower fill probability
  - Higher profit per trade (if filled)
  - Less inventory risk

**Optimal Strategy**: Balance via dynamic spread adjustment based on:
1. Current inventory position
2. Market volatility
3. Order flow toxicity (adverse selection)

---

### 2.2 Trading on Informational Advantage (Page 30)

**Informed Traders** exploit:
1. **Private information** about future price movements
2. **Order flow information** (observing large institutional orders)
3. **Short-term alpha** (temporary price predictability)

**Market Maker Defense**:
- Widen spreads when detecting informed flow
- Adjust quote sizes based on order flow toxicity
- Use machine learning to classify order flow

---

### 2.3 Market Making with Informational Disadvantage (Page 34)

#### 2.3.1 Price Dynamics (Page 36)

When market makers face adverse selection:

**Price Update Rule**:
```
ΔS_mid = λ * (Direction of last trade) * (Trade size)
```

Where:
- `λ` = adverse selection coefficient (price impact)
- Direction: +1 for buy MO, -1 for sell MO
- Trade size: Volume of the executed order

**Inventory Penalty**:
Market makers adjust quotes to **push inventory back to zero**:
```
δ_bid = -γ * q  (inventory penalty on bid)
δ_ask = -γ * q  (inventory penalty on ask)
```

Where:
- `q` = current inventory (positive = long, negative = short)
- `γ` = inventory risk aversion parameter

#### 2.3.2 Price Sensitive Liquidity Traders (Page 37)

Liquidity demand is **elastic**: tighter spreads attract more flow.

**Arrival Rate Model**:
```
λ_bid(δ) = A * exp(-k * δ_bid)
λ_ask(δ) = A * exp(-k * δ_ask)
```

Where:
- `λ` = arrival rate of market orders
- `δ` = spread (distance from mid-price)
- `A` = baseline arrival intensity
- `k` = elasticity parameter (higher k = more price-sensitive traders)

---

## Mathematical Models

### 10.2 Market Making (Chapter 10, Page 247)

#### 10.2.1 Market Making with No Inventory Restrictions

**Problem Setup**:

Market maker posts bid/ask quotes at distances `δ_bid` and `δ_ask` from mid-price `S_t`.

**State Variables**:
- `t` = current time
- `x` = cash holdings
- `S_t` = mid-price (follows GBM or Ornstein-Uhlenbeck)
- `q` = inventory (number of shares held)

**Objective**: Maximize expected terminal wealth adjusted for inventory risk:
```
H(t, x, S, q) = 𝔼[x_T + q_T * (S_T - α * q_T)]
```

Where:
- `α` = terminal inventory penalty (liquidation cost)
- `q_T * S_T` = mark-to-market value of inventory
- `-α * q_T²` = quadratic penalty for unhedged inventory

**Dynamic Programming Equation (DPE)**:

```
0 = ∂_t H + ½σ² ∂_SS H
    + λ_bid(δ_bid) * [H(t, x - S + δ_bid, S, q+1) - H(t, x, S, q)]
    + λ_ask(δ_ask) * [H(t, x + S + δ_ask, S, q-1) - H(t, x, S, q)]
```

**Interpretation**:
- `∂_t H`: Time decay
- `½σ² ∂_SS H`: Volatility risk (Brownian motion)
- `λ_bid`: Arrival rate of buy market orders (MM sells)
- `λ_ask`: Arrival rate of sell market orders (MM buys)

**Arrival Rate Functions**:

Exponential model (elastic demand):
```
λ_bid(δ) = A * exp(-k * δ_bid)
λ_ask(δ) = A * exp(-k * δ_ask)
```

**Value Function Ansatz**:

Assume separable form:
```
H(t, x, S, q) = x + q * S + h(t, q)
```

Where `h(t, q)` captures inventory risk and terminal penalty.

**Optimal Spreads** (Page 253):

The first-order condition yields:
```
δ_bid* = (1/k) + (∂_q h + b*q) / (2*k)
δ_ask* = (1/k) - (∂_q h + b*q) / (2*k)
```

Where:
- `1/k` = base spread (liquidity cost)
- `b` = drift coefficient (permanent price impact)
- `∂_q h` = marginal value of inventory

**Symmetric Case** (no drift, `b = 0`):
```
δ* = (1/k) ± (γ * q) / (2*k)
```

**Key Insight**:
- When `q > 0` (long inventory): widen ask, tighten bid → incentivize selling
- When `q < 0` (short inventory): widen bid, tighten ask → incentivize buying

---

#### 10.2.2 Market Making At-The-Touch (Page 254)

**Constraint**: Market maker must quote at **best bid/ask** (tightest spread).

**Problem**: No control over spread (set by exchange tick size), only control **quote size**.

**Optimal Quote Size**:
```
Q_bid* = Q_0 - γ * q
Q_ask* = Q_0 + γ * q
```

Where:
- `Q_0` = baseline quote size
- `γ` = inventory adjustment coefficient

**Interpretation**: Reduce size on side with unwanted inventory, increase on the other side.

---

#### 10.2.3 Market Making Optimising Volume (Page 257)

**Objective**: Maximize **trading volume** while managing inventory risk.

**Modified Performance Criteria**:
```
H = 𝔼[x_T + q_T * S_T - α * q_T² + φ * ∫ (λ_bid + λ_ask) dt]
```

Where:
- `φ` = volume reward parameter (e.g., rebates from exchange)

**Optimal Spreads**:
```
δ* = (1/k) - φ/(2*k) ± inventory_adjustment
```

**Interpretation**: Volume incentives (rebates) → tighter spreads → more fills.

---

### 10.3 Utility Maximising Market Maker (Page 259)

**Exponential Utility**:
```
U(x) = -exp(-γ * x)
```

Where `γ` = risk aversion coefficient.

**Performance Criteria**:
```
H = 𝔼[-exp(-γ * (x_T + q_T * (S_T - α * q_T)))]
```

**Optimal Spreads** (Page 261):

Under exponential utility and GBM mid-price:
```
δ_bid* = (1/k) + (γ * σ² * (T-t)) / 2 + inventory_term
δ_ask* = (1/k) + (γ * σ² * (T-t)) / 2 - inventory_term
```

**Key Insight**:
- Higher risk aversion `γ` → wider spreads
- Higher volatility `σ` → wider spreads
- Time to maturity `(T-t)` → spreads widen as T approaches (less time to hedge)

---

### 10.4 Market Making with Adverse Selection (Page 261)

#### 10.4.1 Impact of Market Orders on Midprice (Page 262)

**Price Dynamics with Adverse Selection**:
```
dS_t = b * (dN_t^bid - dN_t^ask) + σ * dW_t
```

Where:
- `N_t^bid` = counting process for buy market orders (MM sells)
- `N_t^ask` = counting process for sell market orders (MM buys)
- `b` = permanent price impact parameter

**Interpretation**: Each filled order moves mid-price against the market maker.

**Adverse Selection Coefficient**:
```
b = Cov(Price change, Order flow) / Var(Order flow)
```

Estimated from historical data using tick-level regressions.

---

#### 10.4.2 Short-Term-Alpha and Adverse Selection (Page 266)

**Short-Term Alpha (STA)**: Temporary predictable price movements.

**Model**:
```
dS_t = μ_t * dt + σ * dW_t
dμ_t = -κ * μ_t * dt + η * dZ_t
```

Where:
- `μ_t` = short-term drift (mean-reverting)
- `κ` = reversion speed
- `η` = volatility of alpha shocks

**Optimal Spreads with STA**:
```
δ_bid* = (1/k) + (γ * q) + (β * μ_t)
δ_ask* = (1/k) - (γ * q) - (β * μ_t)
```

Where `β` = sensitivity to short-term alpha.

**Trading Rule**:
- When `μ_t > 0` (upward drift expected): tighten ask, widen bid → accumulate inventory
- When `μ_t < 0` (downward drift expected): tighten bid, widen ask → reduce inventory

---

## Implementation Roadmap

### Phase 1: Basic Market Making (No Inventory Risk)

**Goal**: Implement symmetric market maker with fixed spreads.

**Components**:
1. **Data Feed**: Subscribe to L2 OrderBook data
2. **Strategy Logic**:
   - Calculate mid-price: `S_mid = (best_bid + best_ask) / 2`
   - Post limit orders: `bid = S_mid - δ`, `ask = S_mid + δ`
   - Cancel and replace on mid-price movement
3. **Execution**: Use `SubmitOrder` with `LIMIT` order type

**Parameters**:
- `δ` = fixed spread (e.g., 0.5 * tick_size)
- `Q` = quote size (e.g., 100 shares)

---

### Phase 2: Inventory Risk Management

**Goal**: Add inventory-based spread adjustment.

**Enhancements**:
1. **Track Inventory**: Monitor `self.portfolio.net_position(instrument_id)`
2. **Asymmetric Spreads**:
   ```python
   inventory = self.portfolio.net_position(instrument_id).quantity
   inventory_adjustment = gamma * float(inventory)

   bid_spread = base_spread + inventory_adjustment
   ask_spread = base_spread - inventory_adjustment
   ```
3. **Quote Size Adjustment**:
   ```python
   bid_size = base_size - abs(inventory) if inventory > 0 else base_size
   ask_size = base_size - abs(inventory) if inventory < 0 else base_size
   ```

**Parameters**:
- `gamma` = inventory risk aversion (e.g., 0.01)
- `max_inventory` = position limit (e.g., 1000 shares)

---

### Phase 3: Adverse Selection Protection

**Goal**: Detect and avoid toxic order flow.

**Enhancements**:
1. **Order Flow Imbalance**:
   ```python
   OFI = (volume_bid - volume_ask) / (volume_bid + volume_ask)
   ```
2. **Spread Widening**:
   ```python
   if abs(OFI) > threshold:
       spread_multiplier = 1 + (abs(OFI) - threshold) * sensitivity
       adjusted_spread = base_spread * spread_multiplier
   ```
3. **Quote Skipping**:
   - If OFI strongly negative (sell pressure): pull bid quotes
   - If OFI strongly positive (buy pressure): pull ask quotes

**Parameters**:
- `ofi_window` = lookback period (e.g., 10 seconds)
- `ofi_threshold` = toxicity threshold (e.g., 0.3)
- `sensitivity` = spread adjustment factor (e.g., 2.0)

---

### Phase 4: Short-Term Alpha Integration

**Goal**: Incorporate mean-reverting price signals.

**Enhancements**:
1. **Alpha Signal**:
   ```python
   # Ornstein-Uhlenbeck residual
   residual = log(S_t) - MA(log(S_t), window=60)
   mu_t = -kappa * residual  # mean-reverting drift
   ```
2. **Directional Bias**:
   ```python
   alpha_adjustment = beta * mu_t
   bid_spread = base_spread - alpha_adjustment
   ask_spread = base_spread + alpha_adjustment
   ```

**Parameters**:
- `alpha_window` = MA window for mean reversion (e.g., 60 seconds)
- `kappa` = reversion speed (estimate from data)
- `beta` = alpha sensitivity (e.g., 0.5)

---

### Phase 5: Avellaneda-Stoikov Model (Full HJB Solution)

**Goal**: Solve Hamilton-Jacobi-Bellman equation for optimal quotes.

**Mathematical Framework**:

The Avellaneda-Stoikov model assumes:
- Mid-price follows **Arithmetic Brownian Motion**: `dS_t = σ * dW_t`
- Arrival rates: `λ(δ) = A * exp(-k * δ)`
- Terminal penalty: `-α * q_T²`

**Value Function**:
```
h(t, q) = -q * S * γ * σ² * (T-t) - (1/γ) * log(1 + γ * α * q²)
```

**Optimal Spreads** (closed-form):
```
δ_bid* = (1/k) * log(1 + k/γ) + (γ * σ² * (T-t)) / 2
δ_ask* = (1/k) * log(1 + k/γ) + (γ * σ² * (T-t)) / 2
```

**Reservation Price** (indifference price):
```
r_t = S_t - q * γ * σ² * (T-t)
```

**Quote Prices**:
```
P_bid = r_t - δ_bid*
P_ask = r_t + δ_ask*
```

**Implementation**:
```python
def calculate_reservation_price(self, mid_price, inventory, time_to_end):
    return mid_price - inventory * self.gamma * self.sigma**2 * time_to_end

def calculate_optimal_spread(self, time_to_end):
    term1 = (1 / self.k) * math.log(1 + self.k / self.gamma)
    term2 = (self.gamma * self.sigma**2 * time_to_end) / 2
    return term1 + term2

def on_order_book(self, order_book):
    mid_price = (order_book.best_bid + order_book.best_ask) / 2
    inventory = self.portfolio.net_position(self.instrument_id).quantity
    time_to_end = (self.end_time - self.clock.timestamp_ns()) / 1e9

    r_t = self.calculate_reservation_price(mid_price, inventory, time_to_end)
    spread = self.calculate_optimal_spread(time_to_end)

    bid_price = r_t - spread
    ask_price = r_t + spread

    self.update_quotes(bid_price, ask_price)
```

**Parameters to Calibrate**:
- `σ` = volatility (rolling std of returns)
- `k` = order arrival elasticity (estimate from LOB data)
- `A` = baseline arrival intensity
- `γ` = risk aversion (tune for desired inventory turnover)
- `α` = terminal penalty (cost of liquidating at T)

---

## NautilusTrader Integration

### Strategy Class Structure

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import OrderBookDeltas, QuoteTick
from nautilus_trader.model.orders import LimitOrder
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.core.datetime import dt_to_unix_nanos
import numpy as np

class AvellanedaStoikovMM(Strategy):
    """
    Avellaneda-Stoikov market making strategy.

    References:
    - Cartea, Álvaro, et al. "Algorithmic and High-Frequency Trading."
      Cambridge University Press, 2015. Chapter 10.
    """

    def __init__(self, config: dict):
        super().__init__(config)

        # Strategy parameters (from Cartea Chapter 10)
        self.instrument_id = InstrumentId.from_str(config['instrument_id'])
        self.gamma = config.get('risk_aversion', 0.1)  # Risk aversion
        self.k = config.get('order_arrival_elasticity', 1.5)  # Elasticity
        self.alpha = config.get('terminal_penalty', 0.01)  # Liquidation cost
        self.T = config.get('session_duration', 3600)  # seconds
        self.base_spread = config.get('base_spread', 0.0005)  # 5 bps

        # Risk limits
        self.max_position = config.get('max_position', 1000)
        self.quote_size = config.get('quote_size', 100)

        # Market data
        self.mid_price = None
        self.volatility = None  # Rolling volatility estimator

        # Order tracking
        self.active_bid = None
        self.active_ask = None

    def on_start(self):
        """Initialize strategy on start."""
        # Subscribe to order book updates
        self.subscribe_order_book_deltas(self.instrument_id)
        self.subscribe_quote_ticks(self.instrument_id)

        # Initialize volatility estimator
        self.request_quote_ticks(
            instrument_id=self.instrument_id,
            limit=1000,  # Last 1000 ticks for vol estimation
            callback=self._initialize_volatility
        )

    def _initialize_volatility(self, ticks):
        """Estimate initial volatility from historical ticks."""
        prices = np.array([tick.extract_price() for tick in ticks])
        returns = np.diff(np.log(prices))
        self.volatility = np.std(returns) * np.sqrt(252 * 24 * 3600)  # Annualized
        self.log.info(f"Initial volatility: {self.volatility:.4f}")

    def on_quote_tick(self, tick: QuoteTick):
        """Update mid-price and refresh quotes."""
        self.mid_price = (tick.bid_price.as_double() + tick.ask_price.as_double()) / 2
        self._update_volatility(tick)
        self._refresh_quotes()

    def _update_volatility(self, tick: QuoteTick):
        """Update rolling volatility estimator (EWMA)."""
        if self.volatility is None:
            return

        # Simple EWMA update (TODO: use proper rolling window)
        alpha_vol = 0.01  # Decay factor
        mid = (tick.bid_price.as_double() + tick.ask_price.as_double()) / 2
        if hasattr(self, '_last_mid'):
            ret = np.log(mid / self._last_mid)
            self.volatility = (1 - alpha_vol) * self.volatility + alpha_vol * abs(ret)
        self._last_mid = mid

    def _calculate_reservation_price(self):
        """Calculate reservation price r_t (Cartea Eq 10.X)."""
        inventory = self.portfolio.net_position(self.instrument_id)
        q = float(inventory.quantity) if inventory else 0.0

        time_elapsed = (self.clock.timestamp_ns() - self.start_time_ns) / 1e9
        time_to_end = max(self.T - time_elapsed, 1.0)  # Avoid division by zero

        # r_t = S_t - q * γ * σ² * (T-t)
        reservation_price = self.mid_price - q * self.gamma * (self.volatility ** 2) * time_to_end
        return reservation_price

    def _calculate_optimal_spread(self):
        """Calculate optimal spread δ* (Cartea Eq 10.X)."""
        time_elapsed = (self.clock.timestamp_ns() - self.start_time_ns) / 1e9
        time_to_end = max(self.T - time_elapsed, 1.0)

        # δ* = (1/k) * log(1 + k/γ) + (γ * σ² * (T-t)) / 2
        term1 = (1 / self.k) * np.log(1 + self.k / self.gamma)
        term2 = (self.gamma * (self.volatility ** 2) * time_to_end) / 2
        spread = term1 + term2

        # Apply minimum spread (exchange tick size)
        min_spread = self.instrument.price_increment.as_double()
        return max(spread, min_spread)

    def _refresh_quotes(self):
        """Cancel existing quotes and post new optimal quotes."""
        if self.mid_price is None or self.volatility is None:
            return

        # Check position limits
        inventory = self.portfolio.net_position(self.instrument_id)
        q = float(inventory.quantity) if inventory else 0.0
        if abs(q) >= self.max_position:
            self.log.warning(f"Position limit reached: {q}")
            self._cancel_all_quotes()
            return

        # Calculate optimal quotes
        r_t = self._calculate_reservation_price()
        spread = self._calculate_optimal_spread()

        bid_price = r_t - spread
        ask_price = r_t + spread

        # Round to tick size
        tick_size = self.instrument.price_increment.as_double()
        bid_price = round(bid_price / tick_size) * tick_size
        ask_price = round(ask_price / tick_size) * tick_size

        # Cancel existing quotes
        self._cancel_all_quotes()

        # Submit new quotes
        self._submit_quote(OrderSide.BUY, bid_price)
        self._submit_quote(OrderSide.SELL, ask_price)

    def _submit_quote(self, side: OrderSide, price: float):
        """Submit limit order quote."""
        order = self.order_factory.limit(
            instrument_id=self.instrument_id,
            order_side=side,
            quantity=self.instrument.make_qty(self.quote_size),
            price=self.instrument.make_price(price),
            time_in_force=TimeInForce.GTC,
            post_only=True,  # Ensure we provide liquidity
        )
        self.submit_order(order)

        if side == OrderSide.BUY:
            self.active_bid = order
        else:
            self.active_ask = order

    def _cancel_all_quotes(self):
        """Cancel all active quotes."""
        if self.active_bid and self.active_bid.is_open:
            self.cancel_order(self.active_bid)
        if self.active_ask and self.active_ask.is_open:
            self.cancel_order(self.active_ask)

    def on_order_filled(self, event):
        """Handle order fills."""
        self.log.info(f"Order filled: {event}")
        # Immediately refresh quotes after fill
        self._refresh_quotes()

    def on_stop(self):
        """Clean up on strategy stop."""
        self._cancel_all_quotes()
```

---

### Configuration Example

```python
# config/market_making/avellaneda_stoikov.py

from nautilus_trader.config import StrategyConfig
from decimal import Decimal

class AvellanedaStoikovConfig(StrategyConfig):
    """Configuration for Avellaneda-Stoikov market making strategy."""

    instrument_id: str
    risk_aversion: float = 0.1  # γ
    order_arrival_elasticity: float = 1.5  # k
    terminal_penalty: float = 0.01  # α
    session_duration: int = 3600  # T (seconds)
    base_spread: float = 0.0005  # 5 bps
    max_position: int = 1000
    quote_size: int = 100

# Example instantiation
config = AvellanedaStoikovConfig(
    instrument_id="BTCUSDT-PERP.BINANCE",
    risk_aversion=0.1,
    order_arrival_elasticity=1.5,
    terminal_penalty=0.01,
    session_duration=3600,
    max_position=1000,
    quote_size=100,
)
```

---

## Data Requirements

### Level 1 (Minimum Viable)

1. **Quote Ticks** (BBO - Best Bid/Offer):
   - `timestamp`
   - `bid_price`
   - `ask_price`
   - `bid_size`
   - `ask_size`

2. **Trade Ticks**:
   - `timestamp`
   - `price`
   - `size`
   - `side` (aggressor side)

**Use Case**: Basic spread calculation, inventory tracking.

---

### Level 2 (Optimal)

1. **OrderBook Deltas** (L2 LOB):
   - Full depth snapshot (top 20 levels)
   - Order book imbalance: `OBI = (V_bid - V_ask) / (V_bid + V_ask)`
   - Micro-price: Weighted mid-price

2. **Order Flow Metrics**:
   - Volume-weighted bid/ask ratio
   - Toxicity indicators (adverse selection signals)

**Use Case**: Adverse selection protection, spread optimization.

---

### Level 3 (Advanced)

1. **Order-level Data** (L3 LOB):
   - Individual order tracking (add/cancel/modify)
   - Hidden order detection
   - Order cancellation ratios

2. **Market Microstructure**:
   - Effective spread calculations
   - Price impact models
   - Liquidity resilience metrics

**Use Case**: Short-term alpha signals, high-frequency strategies.

---

## Risk Management

### Position Limits

```python
# Hard limits
MAX_POSITION = 1000  # shares
MAX_NOTIONAL = 100_000  # USD

# Soft limits (trigger spread widening)
SOFT_POSITION_THRESHOLD = 0.7 * MAX_POSITION
```

### Inventory Risk Controls

1. **Inventory-based spread adjustment**:
   ```python
   if abs(inventory) > SOFT_POSITION_THRESHOLD:
       spread_multiplier = 1 + (abs(inventory) / MAX_POSITION) * 2
       adjusted_spread = base_spread * spread_multiplier
   ```

2. **Emergency liquidation**:
   ```python
   if abs(inventory) >= MAX_POSITION:
       # Aggressive liquidation via market orders
       self.flatten_position(instrument_id)
   ```

### Adverse Selection Limits

```python
# Stop quoting if order flow imbalance exceeds threshold
OFI_THRESHOLD = 0.5

if abs(order_flow_imbalance) > OFI_THRESHOLD:
    self.pause_quoting(duration=30)  # seconds
```

### Volatility Circuit Breakers

```python
# Widen spreads or pause during volatility spikes
if current_volatility > 2 * historical_volatility:
    self.log.warning("Volatility spike detected")
    self.widen_spreads(factor=3)
```

---

## Risk Parameters (Calibration Guide)

### γ (Risk Aversion)

**Definition**: Controls inventory risk tolerance.

**Calibration**:
- High `γ` (0.5 - 1.0): Conservative, tight inventory control
- Medium `γ` (0.1 - 0.5): Balanced
- Low `γ` (0.01 - 0.1): Aggressive, willing to hold larger positions

**Estimation Method**:
```python
# Backtest grid search
gamma_grid = [0.01, 0.05, 0.1, 0.5, 1.0]
results = [backtest(gamma=g) for g in gamma_grid]
optimal_gamma = gamma_grid[argmax(sharpe_ratios)]
```

### k (Order Arrival Elasticity)

**Definition**: Sensitivity of order flow to spread.

**Calibration**:
- Estimate from LOB data via regression:
  ```python
  log(fill_rate) = log(A) - k * spread
  k = -slope of regression
  ```

**Typical Range**: 0.5 - 5.0 (higher for liquid assets)

### σ (Volatility)

**Estimation**:
1. **Rolling Window**:
   ```python
   returns = np.diff(np.log(prices))
   sigma = np.std(returns[-window:]) * sqrt(annualization_factor)
   ```

2. **EWMA** (Exponentially Weighted Moving Average):
   ```python
   sigma_t = sqrt(λ * sigma_(t-1)^2 + (1-λ) * r_t^2)
   ```

**Recommended**: 60-second rolling window for HFT, 1-day for longer horizons.

### α (Terminal Penalty)

**Definition**: Cost of unwinding inventory at session end.

**Calibration**:
- `α = k * average_spread / 2` (half the typical spread cost)
- Penalizes large terminal positions

---

## Testing Strategy

### Unit Tests

1. **Spread Calculation**:
   ```python
   def test_optimal_spread():
       mm = AvellanedaStoikovMM(config)
       mm.volatility = 0.02
       mm.gamma = 0.1
       mm.k = 1.5
       spread = mm._calculate_optimal_spread()
       assert spread > 0
   ```

2. **Reservation Price**:
   ```python
   def test_reservation_price_long_inventory():
       mm.inventory = 500  # Long 500 shares
       r_t = mm._calculate_reservation_price()
       assert r_t < mm.mid_price  # Should be below mid (want to sell)
   ```

### Backtests

**Test Cases**:
1. **Trending Market**: Does MM widen spreads and reduce fills?
2. **Mean-Reverting Market**: Does MM capture spread efficiently?
3. **Volatile Market**: Does MM adjust spreads dynamically?
4. **Adverse Selection**: Does MM detect and avoid toxic flow?

**Metrics**:
- **PnL**: Total profit/loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Fill Rate**: % of posted quotes filled
- **Inventory Turnover**: How quickly inventory reverts to zero
- **Max Drawdown**: Worst peak-to-trough loss

### Live Paper Trading

**Staged Rollout**:
1. **Phase 1**: Paper trading with full logging (2 weeks)
2. **Phase 2**: Small size live (10% of target size, 1 week)
3. **Phase 3**: Gradual scale-up to full size

**Monitoring**:
- Real-time PnL dashboard
- Inventory alerts
- Fill rate tracking
- Adverse selection signals

---

## Advanced Extensions

### 1. Multi-Asset Market Making

**Cross-Asset Inventory Risk**:
```python
# Correlation matrix
Σ = np.array([[σ1², ρ*σ1*σ2],
              [ρ*σ1*σ2, σ2²]])

# Portfolio variance
portfolio_var = q.T @ Σ @ q

# Adjust spreads based on portfolio risk
spread_adjustment = gamma * portfolio_var
```

### 2. Order Book Dynamics

**Micro-price** (Cartea Chapter 3):
```
P_micro = (V_ask * P_bid + V_bid * P_ask) / (V_bid + V_ask)
```

Use micro-price instead of mid-price for more accurate quote placement.

### 3. Machine Learning Enhancements

**Feature Engineering**:
- Order flow imbalance (last N seconds)
- Trade size distribution
- Cancel-to-fill ratios
- Time-of-day effects

**Model**: Classify order flow as "toxic" vs "benign" → adjust spreads.

### 4. Dynamic Session Duration

Instead of fixed `T`, use **adaptive horizon**:
```python
# End session early if inventory risk exceeds threshold
if abs(inventory) > emergency_threshold:
    T_effective = min(T_remaining, emergency_liquidation_horizon)
```

---

## References

### Primary Source

**Cartea, Álvaro, Sebastian Jaimungal, and José Penalva.**
*Algorithmic and High-Frequency Trading.*
Cambridge University Press, 2015.

**Key Chapters**:
- Chapter 2: Primer on Microstructure (Market Making Theory)
- Chapter 10: Market Making Models (Mathematical Framework)

### Recommended Papers

1. **Avellaneda, M., & Stoikov, S. (2008).**
   "High-frequency trading in a limit order book."
   *Quantitative Finance*, 8(3), 217-224.

2. **Guilbaud, F., & Pham, H. (2013).**
   "Optimal high-frequency trading with limit and market orders."
   *Quantitative Finance*, 13(1), 79-94.

3. **Cartea, Á., & Jaimungal, S. (2015).**
   "Risk metrics and fine tuning of high-frequency trading strategies."
   *Mathematical Finance*, 25(3), 576-611.

### NautilusTrader Documentation

- **Strategy Development**: https://nautilustrader.io/docs/latest/concepts/strategies
- **Order Book Data**: https://nautilustrader.io/docs/latest/concepts/data_types
- **Backtesting**: https://nautilustrader.io/docs/latest/concepts/backtesting

---

## Appendix A: Key Equations Summary

### 1. Optimal Spread (No Inventory Risk)

```
δ* = (1/k) * log(1 + k/γ)
```

### 2. Reservation Price

```
r_t = S_t - q * γ * σ² * (T-t)
```

### 3. Optimal Bid/Ask Quotes

```
P_bid = r_t - δ*
P_ask = r_t + δ*
```

### 4. Arrival Rate (Exponential)

```
λ(δ) = A * exp(-k * δ)
```

### 5. Value Function (Terminal Condition)

```
H(T, x, S, q) = x + q * S - α * q²
```

### 6. Inventory Adjustment Term

```
Δδ = (γ * σ² * (T-t)) * q
```

### 7. Adverse Selection Price Impact

```
dS_t = b * (dN_bid - dN_ask) + σ * dW_t
```

### 8. Order Flow Imbalance

```
OFI = (V_bid - V_ask) / (V_bid + V_ask)
```

---

## Appendix B: Parameter Ranges

| Parameter | Symbol | Typical Range | Units |
|-----------|--------|---------------|-------|
| Risk Aversion | γ | 0.01 - 1.0 | dimensionless |
| Elasticity | k | 0.5 - 5.0 | 1/price |
| Volatility | σ | 0.01 - 0.5 | annualized |
| Terminal Penalty | α | 0.001 - 0.1 | price/share² |
| Session Duration | T | 60 - 3600 | seconds |
| Max Position | Q_max | 100 - 10,000 | shares |
| Quote Size | Q | 10 - 1,000 | shares |

---

## Appendix C: NautilusTrader Native Components

**Use these instead of reimplementing**:

1. **Volatility Indicators**:
   ```python
   from nautilus_trader.indicators.atr import AverageTrueRange
   atr = AverageTrueRange(period=14)
   ```

2. **Moving Averages**:
   ```python
   from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
   ema = ExponentialMovingAverage(period=20)
   ```

3. **Order Book Analytics**:
   ```python
   order_book = self.cache.order_book(instrument_id)
   mid_price = order_book.mid_price()
   spread = order_book.spread()
   ```

---

## Implementation Checklist

- [ ] **Phase 1**: Basic MM with fixed spreads
  - [ ] Subscribe to L1 data (BBO)
  - [ ] Calculate mid-price
  - [ ] Post symmetric quotes
  - [ ] Handle fills and refresh quotes

- [ ] **Phase 2**: Inventory risk management
  - [ ] Track net position
  - [ ] Implement reservation price
  - [ ] Asymmetric spread adjustment
  - [ ] Position limits

- [ ] **Phase 3**: Volatility estimation
  - [ ] Rolling window volatility
  - [ ] EWMA volatility
  - [ ] Dynamic spread adjustment

- [ ] **Phase 4**: Adverse selection protection
  - [ ] Order flow imbalance calculation
  - [ ] Toxicity detection
  - [ ] Spread widening logic

- [ ] **Phase 5**: Avellaneda-Stoikov full model
  - [ ] Implement HJB solution
  - [ ] Parameter calibration
  - [ ] Backtesting framework

- [ ] **Phase 6**: Production hardening
  - [ ] Error handling
  - [ ] Logging and monitoring
  - [ ] Emergency liquidation
  - [ ] Paper trading validation

---

## Contact & Contributions

For questions or contributions, see:
- NautilusTrader Discord: [Link needed]
- GitHub Issues: [Link needed]

---

**End of Document**
