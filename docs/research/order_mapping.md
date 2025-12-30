# NautilusTrader Order Type Mapping

Reference table for mapping academic paper order terminology to NautilusTrader order types.

## Order Type Mapping

| Paper Term | Alternative Names | NautilusTrader | Notes |
|------------|-------------------|----------------|-------|
| Market order | At-the-market | `OrderType.MARKET` | Immediate execution at best price |
| Limit order | Passive order | `OrderType.LIMIT` | Execute at specified price or better |
| Stop loss | Stop order | `OrderType.STOP_MARKET` | Use `reduce_only=True` for exits |
| Stop limit | Stop with limit | `OrderType.STOP_LIMIT` | Stop triggers limit order |
| Take profit | Profit target | `OrderType.LIMIT` | Or `MARKET_IF_TOUCHED` |
| Trailing stop | Dynamic stop | `OrderType.TRAILING_STOP_MARKET` | Not all exchanges support |
| Bracket order | OCO | Multiple orders | Entry + SL + TP |
| IOC | Immediate-or-cancel | `TimeInForce.IOC` | Time in force modifier |
| FOK | Fill-or-kill | `TimeInForce.FOK` | Time in force modifier |
| GTC | Good-till-cancel | `TimeInForce.GTC` | Default time in force |

## Order Type Usage Examples

### Basic Entry Orders

```python
from nautilus_trader.model.orders import MarketOrder, LimitOrder
from nautilus_trader.model.enums import OrderSide, TimeInForce

# Market order - immediate execution
order = self.order_factory.market(
    instrument_id=self.instrument.id,
    order_side=OrderSide.BUY,
    quantity=Quantity.from_str("1.0"),
)

# Limit order - specified price
order = self.order_factory.limit(
    instrument_id=self.instrument.id,
    order_side=OrderSide.BUY,
    quantity=Quantity.from_str("1.0"),
    price=Price.from_str("50000.00"),
    time_in_force=TimeInForce.GTC,
)
```

### Stop Loss Orders

```python
# Stop market (standard stop loss)
stop_order = self.order_factory.stop_market(
    instrument_id=self.instrument.id,
    order_side=OrderSide.SELL,
    quantity=Quantity.from_str("1.0"),
    trigger_price=Price.from_str("49000.00"),
    reduce_only=True,  # CRITICAL: Only reduces position
)

# Trailing stop (if exchange supports)
trailing_stop = self.order_factory.trailing_stop_market(
    instrument_id=self.instrument.id,
    order_side=OrderSide.SELL,
    quantity=Quantity.from_str("1.0"),
    trailing_offset=Decimal("0.02"),  # 2% trailing
    trailing_offset_type=TrailingOffsetType.PERCENTAGE,
    reduce_only=True,
)
```

### Take Profit Orders

```python
# Limit order as take profit
tp_order = self.order_factory.limit(
    instrument_id=self.instrument.id,
    order_side=OrderSide.SELL,
    quantity=Quantity.from_str("1.0"),
    price=Price.from_str("52000.00"),
    reduce_only=True,
    post_only=True,  # Maker order (lower fees)
)
```

## Exchange Support Matrix

| Order Type | Binance | Bybit | Hyperliquid | IB |
|------------|---------|-------|-------------|-----|
| MARKET | ✅ | ✅ | ✅ | ✅ |
| LIMIT | ✅ | ✅ | ✅ | ✅ |
| STOP_MARKET | ✅ | ✅ | ✅ | ✅ |
| STOP_LIMIT | ✅ | ✅ | ✅ | ✅ |
| TRAILING_STOP_MARKET | ✅ | ✅ | ❌ | ✅ |
| MARKET_IF_TOUCHED | ✅ | ✅ | ❌ | ✅ |

## Position Management Flags

| Flag | Purpose | When to Use |
|------|---------|-------------|
| `reduce_only=True` | Only reduces position | Stop loss, take profit |
| `post_only=True` | Maker order only | Limit orders (lower fees) |
| `close_on_trigger=True` | Close full position | Emergency exits |

## Academic Paper → NautilusTrader Translation

### "Enter long with stop loss at 2%"

```python
def _enter_long(self, price: Price):
    # Entry order
    entry = self.order_factory.market(
        instrument_id=self.instrument.id,
        order_side=OrderSide.BUY,
        quantity=self.position_size,
    )
    self.submit_order(entry)

    # Stop loss at 2% below entry
    stop_price = price * Decimal("0.98")
    stop = self.order_factory.stop_market(
        instrument_id=self.instrument.id,
        order_side=OrderSide.SELL,
        quantity=self.position_size,
        trigger_price=Price.from_str(str(stop_price)),
        reduce_only=True,
    )
    self.submit_order(stop)
```

### "Scale out 50% at +5%, remainder at +10%"

```python
def _setup_take_profits(self, entry_price: Price, total_qty: Quantity):
    half_qty = Quantity.from_str(str(float(total_qty) / 2))

    # TP1: 50% at +5%
    tp1_price = entry_price * Decimal("1.05")
    tp1 = self.order_factory.limit(
        instrument_id=self.instrument.id,
        order_side=OrderSide.SELL,
        quantity=half_qty,
        price=Price.from_str(str(tp1_price)),
        reduce_only=True,
    )

    # TP2: Remaining 50% at +10%
    tp2_price = entry_price * Decimal("1.10")
    tp2 = self.order_factory.limit(
        instrument_id=self.instrument.id,
        order_side=OrderSide.SELL,
        quantity=half_qty,
        price=Price.from_str(str(tp2_price)),
        reduce_only=True,
    )

    self.submit_order(tp1)
    self.submit_order(tp2)
```

## Event Mapping

| Paper Concept | NautilusTrader Event | Handler |
|---------------|---------------------|---------|
| Position opened | `PositionOpened` | `on_event()` |
| Position closed | `PositionClosed` | `on_event()` |
| Order filled | `OrderFilled` | `on_event()` |
| Stop triggered | `OrderFilled` | Check `order.order_type` |
| Order rejected | `OrderRejected` | `on_event()` |
| Order canceled | `OrderCanceled` | `on_event()` |

## Common Patterns from Papers

### "Market on close" (MOC)
Not directly supported. Use scheduled limit order near close.

### "Bracket order"
Submit entry + SL + TP as separate orders with contingency logic.

### "Iceberg order"
Use multiple smaller limit orders. Native iceberg not always available.

### "TWAP execution"
Implement as scheduled market orders over time window.

## Context7 Documentation Links

For the most up-to-date order documentation, query Context7:
- "Show NautilusTrader order types"
- "How to submit stop loss orders in NautilusTrader"
- "OrderFactory methods in NautilusTrader"
