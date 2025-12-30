# Data Model: Stop-Loss & Position Limits

**Spec**: 011-stop-loss-position-limits
**Date**: 2025-12-28

## Entity Overview

```
┌─────────────────┐      ┌─────────────────┐
│   RiskConfig    │◀─────│   RiskManager   │
│   (Pydantic)    │      │   (Runtime)     │
└─────────────────┘      └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
            ┌───────────┐ ┌───────────┐ ┌───────────┐
            │ ActiveStop│ │ Position  │ │   Order   │
            │  Mapping  │ │  Cache    │ │  Factory  │
            └───────────┘ └───────────┘ └───────────┘
```

## Entities

### 1. RiskConfig (Configuration)

**Purpose**: Immutable configuration for risk management behavior.

**Fields**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `stop_loss_enabled` | `bool` | `True` | Enable automatic stop-loss generation |
| `stop_loss_pct` | `Decimal` | `0.02` | Stop distance as fraction (2% = 0.02) |
| `stop_loss_type` | `StopLossType` | `"market"` | Order type: market/limit/emulated |
| `trailing_stop` | `bool` | `False` | Enable trailing stop mode |
| `trailing_distance_pct` | `Decimal` | `0.01` | Trailing distance as fraction |
| `trailing_offset_type` | `OffsetType` | `"price"` | price or basis_points |
| `max_position_size` | `dict[str, Decimal]` | `None` | Per-instrument max position |
| `max_total_exposure` | `Decimal` | `None` | Total portfolio exposure limit |
| `dynamic_boundaries` | `bool` | `False` | Enable OU-based boundaries (Phase 5) |
| `ou_lookback_days` | `int` | `30` | Days of history for OU estimation |

**Validation Rules**:
- `stop_loss_pct` must be > 0 and < 1
- `trailing_distance_pct` must be > 0 and <= `stop_loss_pct`
- `max_position_size` values must be positive
- `max_total_exposure` must be positive if set

**Example**:
```python
RiskConfig(
    stop_loss_pct=Decimal("0.02"),
    stop_loss_type="market",
    max_position_size={"BTC/USDT.BINANCE": Decimal("0.5")},
    max_total_exposure=Decimal("10000"),
)
```

---

### 2. StopLossType (Enum)

**Purpose**: Defines how stop-loss orders are submitted.

**Values**:
- `MARKET` = `"market"` - Native STOP_MARKET order (default)
- `LIMIT` = `"limit"` - Native STOP_LIMIT order
- `EMULATED` = `"emulated"` - Strategy-managed via price checks

---

### 3. TrailingOffsetType (Enum)

**Purpose**: Defines how trailing distance is measured.

**Values**:
- `PRICE` = `"price"` - Absolute price offset
- `BASIS_POINTS` = `"basis_points"` - Offset in basis points (1 bp = 0.01%)

---

### 4. ActiveStopMapping (Runtime State)

**Purpose**: Tracks active stop orders for each position.

**Type**: `dict[PositionId, ClientOrderId]`

**Behavior**:
- On `PositionOpened`: Add mapping `{position_id: stop_order_id}`
- On `PositionClosed`: Remove mapping, cancel stop order
- On `OrderFilled` (stop): Remove mapping (stop executed)

**Thread Safety**: Single-threaded event loop (NautilusTrader guarantees)

---

### 5. PositionLimitState (Runtime State)

**Purpose**: Tracks current position sizes for limit enforcement.

**Computed From**: `strategy.cache.positions_open()`

**Fields** (computed):
| Field | Type | Description |
|-------|------|-------------|
| `current_position` | `Quantity` | Net position size per instrument |
| `total_exposure` | `Decimal` | Sum of notional across all positions |

---

## State Transitions

### Stop-Loss Lifecycle

```
┌─────────────────┐
│     NONE        │──▶ PositionOpened ──▶┌─────────────────┐
│ (no position)   │                      │    ACTIVE       │
└─────────────────┘                      │ (stop pending)  │
        ▲                                └────────┬────────┘
        │                                         │
        │                              ┌──────────┼──────────┐
        │                              ▼          ▼          ▼
        │                        PositionClosed  StopFilled  StopCancelled
        │                              │          │          │
        └──────────────────────────────┴──────────┴──────────┘
```

### State Transitions Table

| Current State | Event | Action | Next State |
|---------------|-------|--------|------------|
| NONE | PositionOpened | Create stop order | ACTIVE |
| ACTIVE | PositionClosed | Cancel stop order | NONE |
| ACTIVE | OrderFilled (stop) | Remove mapping | NONE |
| ACTIVE | PositionChanged | Update trailing stop | ACTIVE |

---

## Relationships

### RiskManager → Strategy

```
RiskManager ────composition────▶ Strategy
    │
    ├── strategy.order_factory  (for creating stops)
    ├── strategy.submit_order() (for submitting stops)
    ├── strategy.cancel_order() (for canceling stops)
    ├── strategy.cache          (for position queries)
    └── strategy.portfolio      (for exposure queries)
```

### RiskManager → Position Events

```
Event Bus
    │
    ├── PositionOpened  ────▶ RiskManager._on_position_opened()
    ├── PositionClosed  ────▶ RiskManager._on_position_closed()
    ├── PositionChanged ────▶ RiskManager._on_position_changed()
    └── OrderFilled     ────▶ RiskManager._on_order_filled()
```

---

## Data Flow

### Stop-Loss Creation Flow

```
1. Strategy receives PositionOpened event
2. Strategy.on_event() calls risk_manager.handle_event(event)
3. RiskManager._on_position_opened(event):
   a. Extract entry_price from event.position.avg_px_open
   b. Calculate stop_price = entry_price * (1 - stop_loss_pct)
   c. Create stop order via order_factory.stop_market()
   d. Submit stop order via strategy.submit_order()
   e. Store mapping: active_stops[position_id] = stop_order_id
```

### Position Limit Validation Flow

```
1. Strategy wants to submit new order
2. Strategy calls risk_manager.validate_order(order)
3. RiskManager.validate_order():
   a. Query current position via cache.positions_open()
   b. Calculate projected position = current + order.quantity
   c. Check: projected <= max_position_size
   d. Calculate total exposure after order
   e. Check: total_exposure <= max_total_exposure
   f. Return True/False
4. Strategy submits order only if validation passes
```

---

## Serialization

### RiskConfig JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "stop_loss_enabled": {"type": "boolean", "default": true},
    "stop_loss_pct": {"type": "string", "pattern": "^[0-9]+\\.?[0-9]*$"},
    "stop_loss_type": {"type": "string", "enum": ["market", "limit", "emulated"]},
    "trailing_stop": {"type": "boolean", "default": false},
    "trailing_distance_pct": {"type": "string"},
    "trailing_offset_type": {"type": "string", "enum": ["price", "basis_points"]},
    "max_position_size": {
      "type": "object",
      "additionalProperties": {"type": "string"}
    },
    "max_total_exposure": {"type": "string", "nullable": true},
    "dynamic_boundaries": {"type": "boolean", "default": false},
    "ou_lookback_days": {"type": "integer", "default": 30}
  },
  "required": []
}
```

### Example JSON

```json
{
  "stop_loss_enabled": true,
  "stop_loss_pct": "0.02",
  "stop_loss_type": "market",
  "trailing_stop": false,
  "max_position_size": {
    "BTC/USDT.BINANCE": "0.5",
    "ETH/USDT.BINANCE": "5.0"
  },
  "max_total_exposure": "10000"
}
```

---

## NautilusTrader Type Mappings

| Our Entity | NautilusTrader Type |
|------------|---------------------|
| Position ID | `nautilus_trader.model.identifiers.PositionId` |
| Order ID | `nautilus_trader.model.identifiers.ClientOrderId` |
| Price | `nautilus_trader.model.objects.Price` |
| Quantity | `nautilus_trader.model.objects.Quantity` |
| Instrument ID | `nautilus_trader.model.identifiers.InstrumentId` |
| Stop Order | `nautilus_trader.model.orders.StopMarketOrder` |
| Trailing Stop | `nautilus_trader.model.orders.TrailingStopMarketOrder` |

---

## Invariants

1. **One stop per position**: `len(active_stops) == len(open_positions)` when enabled
2. **Stop side opposite position**: LONG → SELL stop, SHORT → BUY stop
3. **Reduce only**: All stop orders have `reduce_only=True`
4. **Stop price validity**: `stop_price < entry_price` for LONG, `stop_price > entry_price` for SHORT
5. **Position limits respected**: No order exceeds configured limits when validation enabled
