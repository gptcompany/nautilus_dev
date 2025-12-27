# Research: Alpha-Evolve Strategy Templates

**Created**: 2025-12-27
**Status**: Complete

## Research Questions

### Q1: NautilusTrader Strategy Base Class API

**Decision**: Inherit from `nautilus_trader.trading.strategy.Strategy`

**Key Lifecycle Methods**:
- `on_start()`: Initialize indicators, subscribe to data
- `on_bar(bar: Bar)`: Handle bar updates, execute trading logic
- `on_stop()`: Cleanup, cancel orders, close positions
- `on_reset()`: Reset indicators and internal state

**Rationale**: Standard NautilusTrader pattern. All strategy implementations inherit from this base.

**Source**: Context7 + `/nautilus_trader/trading/strategy.pyx`

---

### Q2: Equity Tracking Implementation

**Decision**: Use `portfolio.account(venue).balance_total()` + `portfolio.unrealized_pnl()`

**Implementation**:
```python
def _get_equity(self) -> float:
    """Get current account equity (balance + unrealized PnL)."""
    venue = self.config.instrument_id.venue
    account = self.portfolio.account(venue)

    if account is None:
        return 0.0

    currency = account.base_currency
    balance = account.balance_total(currency)
    total = balance.as_double() if balance else 0.0

    # Add unrealized PnL if in position
    if not self.portfolio.is_flat(self.config.instrument_id):
        unrealized = self.portfolio.unrealized_pnl(self.config.instrument_id)
        if unrealized:
            total += unrealized.as_double()

    return total
```

**EquityPoint Storage**:
```python
@dataclass
class EquityPoint:
    timestamp: datetime
    equity: float

# Tracked in list during on_bar()
self._equity_curve: list[EquityPoint] = []
```

**Rationale**: NautilusTrader provides portfolio facade with account access. Equity = balance + unrealized PnL.

**Alternatives Considered**:
- Portfolio analyzer stats: Only available post-backtest
- Custom accounting: Duplicates NautilusTrader functionality

---

### Q3: Native Rust Indicator Integration

**Decision**: Use `nautilus_trader.indicators.ExponentialMovingAverage` with auto-registration

**Implementation**:
```python
from nautilus_trader.indicators import ExponentialMovingAverage

def __init__(self, config):
    super().__init__(config)
    self.fast_ema = ExponentialMovingAverage(config.fast_period)
    self.slow_ema = ExponentialMovingAverage(config.slow_period)

def on_start(self) -> None:
    # Auto-update on each bar
    self.register_indicator_for_bars(self.config.bar_type, self.fast_ema)
    self.register_indicator_for_bars(self.config.bar_type, self.slow_ema)
```

**Key Attributes**:
- `ema.value`: Current EMA value (float)
- `ema.initialized`: True when count >= period
- `ema.count`: Number of updates received

**Rationale**: Native Rust indicators are 100x faster than Python. Auto-registration ensures indicators update before `on_bar()` is called.

**Available Indicators** (native Rust):
- `ExponentialMovingAverage`
- `SimpleMovingAverage`
- `DoubleExponentialMovingAverage`
- `HullMovingAverage`
- `RelativeStrengthIndex`
- `AverageTrueRange`

---

### Q4: Order Helper Methods

**Decision**: Wrap `order_factory` methods in helper functions

**Implementation**:
```python
def _enter_long(self, quantity: Decimal) -> None:
    """Submit market buy order."""
    if self.portfolio.is_net_short(self.config.instrument_id):
        self._close_position()  # Close short first

    order = self.order_factory.market(
        instrument_id=self.config.instrument_id,
        order_side=OrderSide.BUY,
        quantity=self.instrument.make_qty(quantity),
        time_in_force=TimeInForce.GTC,
    )
    self.submit_order(order)

def _enter_short(self, quantity: Decimal) -> None:
    """Submit market sell order."""
    if self.portfolio.is_net_long(self.config.instrument_id):
        self._close_position()  # Close long first

    order = self.order_factory.market(
        instrument_id=self.config.instrument_id,
        order_side=OrderSide.SELL,
        quantity=self.instrument.make_qty(quantity),
        time_in_force=TimeInForce.GTC,
    )
    self.submit_order(order)

def _close_position(self) -> None:
    """Close all positions for instrument."""
    self.close_all_positions(self.config.instrument_id)

def _get_position_size(self) -> Decimal:
    """Get current net position size."""
    return self.portfolio.net_position(self.config.instrument_id)
```

**Rationale**: Simplifies EVOLVE-BLOCK logic. LLM can use `self._enter_long(qty)` instead of full order creation.

**Edge Cases Handled**:
- Flip from long to short (close first)
- Flip from short to long (close first)
- Insufficient balance → order rejected by exchange

---

### Q5: EVOLVE-BLOCK Structure

**Decision**: Single block named `decision_logic` containing entry/exit signals

**Template**:
```python
def _on_bar_evolved(self, bar: Bar) -> None:
    """Handle bar with evolvable decision logic."""
    # Wait for indicator warmup
    if not self.indicators_initialized():
        return

    # === EVOLVE-BLOCK: decision_logic ===
    # Entry signal: fast EMA crosses above slow EMA
    if self.fast_ema.value > self.slow_ema.value:
        if self.portfolio.is_flat(self.config.instrument_id):
            self._enter_long(self.config.trade_size)

    # Exit signal: fast EMA crosses below slow EMA
    elif self.fast_ema.value < self.slow_ema.value:
        if self.portfolio.is_net_long(self.config.instrument_id):
            self._close_position()
    # === END EVOLVE-BLOCK ===
```

**Block Boundaries**:
- **Before block**: Indicator warmup check (fixed)
- **Inside block**: Entry/exit logic (evolvable)
- **After block**: Equity tracking (fixed)

**Rationale**: Clean separation between infrastructure (fixed) and trading logic (evolvable).

---

### Q6: Seed Strategy Design

**Decision**: Dual EMA crossover momentum strategy

**Configuration**:
```python
class MomentumEvolveConfig(BaseEvolveConfig):
    fast_period: int = 10
    slow_period: int = 30
    trade_size: Decimal = Decimal("0.1")  # 0.1 BTC
```

**Logic**:
- Long entry: fast EMA > slow EMA (bullish momentum)
- Exit: fast EMA < slow EMA (momentum fading)
- No shorting (simplicity)

**Expected Behavior**:
- Trades in trending markets
- Stops out in choppy markets
- Produces 10+ trades per 6-month period

**Rationale**: Simple, well-understood strategy. Good starting point for mutations (period adjustments, indicator additions).

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | BaseEvolveStrategy hides order mechanics |
| KISS & YAGNI | ✅ | Single symbol, market orders only |
| Native First | ✅ | Uses nautilus_trader.indicators |
| Performance | ✅ | No df.iterrows(), native indicators |
| TDD | ✅ | Test with BacktestEngine |

## Dependencies

- **NautilusTrader**: Strategy, indicators, order types
- **spec-006**: EVOLVE-BLOCK marker format (compatible)
- **Python stdlib**: `dataclasses`, `datetime`, `decimal`

## No External Research Needed

All technical decisions resolved using:
1. NautilusTrader source code (Context7)
2. spec-006 research and implementation
3. Existing project patterns
