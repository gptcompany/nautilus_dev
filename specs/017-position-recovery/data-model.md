# Data Model: Position Recovery (Spec 017)

**Created**: 2025-12-30
**Status**: Complete

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TradingNode                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  CacheDatabase   │  │  ExecEngine      │  │   Strategy    │ │
│  │  (Redis)         │◄─┤  (Reconciliation)│◄─┤   (Recovery)  │ │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬───────┘ │
│           │                     │                     │         │
└───────────┼─────────────────────┼─────────────────────┼─────────┘
            │                     │                     │
            ▼                     ▼                     ▼
      ┌───────────┐        ┌───────────┐        ┌───────────────┐
      │ Position  │        │ Order     │        │ StrategyState │
      │ Snapshot  │        │ Snapshot  │        │ (Custom)      │
      └───────────┘        └───────────┘        └───────────────┘
```

---

## Entity: PositionSnapshot

Persisted to Redis cache for recovery.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `position_id` | PositionId | Required, unique | Position identifier |
| `instrument_id` | InstrumentId | Required | Trading instrument |
| `strategy_id` | StrategyId | Required | Owning strategy ("EXTERNAL" for unclaimed) |
| `account_id` | AccountId | Required | Trading account |
| `opening_order_id` | ClientOrderId | Required | Order that opened position |
| `closing_order_id` | ClientOrderId | Optional | Order that closed position |
| `side` | PositionSide | LONG / SHORT / FLAT | Current position side |
| `signed_qty` | Decimal | Signed value | Signed quantity (+long, -short) |
| `quantity` | Quantity | >= 0 | Absolute position size |
| `peak_qty` | Quantity | >= 0 | Maximum position size reached |
| `avg_px_open` | Decimal | > 0 | Average entry price |
| `avg_px_close` | Decimal | Optional, > 0 | Average exit price |
| `realized_pnl` | Money | Signed | Realized profit/loss |
| `unrealized_pnl` | Money | Optional, signed | Unrealized profit/loss |
| `ts_opened` | int (ns) | Unix epoch nanoseconds | Position open timestamp |
| `ts_closed` | int (ns) | Optional, Unix epoch ns | Position close timestamp |
| `ts_last` | int (ns) | Unix epoch nanoseconds | Last update timestamp |

**Redis Key Pattern**: `trader-position:{position_id}`

---

## Entity: OrderSnapshot

Persisted to Redis cache for recovery.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `client_order_id` | ClientOrderId | Required, unique | Client-assigned order ID |
| `venue_order_id` | VenueOrderId | Optional | Exchange-assigned order ID |
| `instrument_id` | InstrumentId | Required | Trading instrument |
| `strategy_id` | StrategyId | Required | Owning strategy |
| `account_id` | AccountId | Required | Trading account |
| `order_type` | OrderType | MARKET / LIMIT / STOP_MARKET / etc. | Order type |
| `side` | OrderSide | BUY / SELL | Order direction |
| `quantity` | Quantity | > 0 | Order size |
| `filled_qty` | Quantity | >= 0 | Amount filled |
| `avg_px` | Decimal | Optional, > 0 | Average fill price |
| `price` | Price | Optional, > 0 | Limit price |
| `trigger_price` | Price | Optional, > 0 | Stop trigger price |
| `time_in_force` | TimeInForce | GTC / IOC / FOK / GTD | Order validity |
| `status` | OrderStatus | PENDING / OPEN / FILLED / etc. | Current status |
| `events` | list[OrderEvent] | Event history | Full event sequence |
| `tags` | list[str] | Optional | Order tags (e.g., "RECONCILIATION") |
| `ts_init` | int (ns) | Unix epoch nanoseconds | Order creation time |
| `ts_last` | int (ns) | Unix epoch nanoseconds | Last update time |

**Redis Key Pattern**: `trader-order:{client_order_id}`

---

## Entity: AccountSnapshot

Persisted to Redis cache for recovery.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `account_id` | AccountId | Required, unique | Account identifier |
| `account_type` | AccountType | CASH / MARGIN | Account type |
| `base_currency` | Currency | Optional | Base currency (margin accounts) |
| `balances` | dict[Currency, Money] | Required | Currency balances |
| `margins` | dict[InstrumentId, Money] | Optional | Position margins |
| `is_reported` | bool | Default: False | Venue-reported state |
| `ts_last` | int (ns) | Unix epoch nanoseconds | Last update time |

**Redis Key Pattern**: `trader-account:{account_id}`

---

## Entity: RecoveryConfig

Strategy-side configuration for recovery behavior.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `external_order_claims` | list[InstrumentId] | Optional | Instruments to claim external orders |
| `oms_type` | OmsType | NETTING / HEDGING | Order management system type |
| `manage_contingent_orders` | bool | Default: True | Manage OUO/OCO orders |
| `manage_gtd_expiry` | bool | Default: True | Re-activate GTD timers |
| `warmup_bars` | int | >= 0 | Number of bars for indicator warmup |
| `warmup_timeframe` | timedelta | Optional | Historical data lookback period |

---

## Entity: ReconciliationReport

Generated during startup reconciliation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `venue` | Venue | Required | Exchange venue |
| `account_id` | AccountId | Required | Trading account |
| `timestamp` | datetime | UTC | Report generation time |
| `cached_positions` | list[PositionSnapshot] | Required | Positions from cache |
| `venue_positions` | list[PositionReport] | Required | Positions from exchange |
| `discrepancies` | list[PositionDiscrepancy] | Required | Detected mismatches |
| `synthetic_fills` | list[OrderFilled] | Required | Generated alignment fills |
| `status` | ReconciliationStatus | SUCCESS / PARTIAL / FAILED | Overall result |

---

## Entity: PositionDiscrepancy

Details of a single position mismatch.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `instrument_id` | InstrumentId | Required | Affected instrument |
| `cached_qty` | Decimal | Signed | Quantity in cache |
| `venue_qty` | Decimal | Signed | Quantity on exchange |
| `delta` | Decimal | Signed | Difference (venue - cached) |
| `resolution` | ResolutionType | SYNTHETIC_FILL / MANUAL / IGNORED | How resolved |
| `synthetic_order_id` | ClientOrderId | Optional | Generated fill order ID |

---

## State Transitions

### Position Lifecycle

```
                 ┌─────────────┐
                 │    FLAT     │
                 │  (No pos)   │
                 └──────┬──────┘
                        │ BUY/SELL order filled
                        ▼
                 ┌─────────────┐
                 │    OPEN     │
                 │  (LONG or   │◄─┐ Partial close
                 │   SHORT)    │──┘
                 └──────┬──────┘
                        │ Fully closed
                        ▼
                 ┌─────────────┐
                 │   CLOSED    │
                 │  (Realized) │
                 └─────────────┘
```

### Recovery State Machine

```
┌─────────────────┐
│   NODE_START    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CACHE_LOADING  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  RECONCILING    │────►│  DISCREPANCY    │
│                 │     │   DETECTED      │
└────────┬────────┘     └────────┬────────┘
         │                       │ Synthetic fill
         │                       ▼
         │              ┌─────────────────┐
         └─────────────►│    ALIGNED      │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  WARMING_UP     │
                        │  (Indicators)   │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │    READY        │
                        │  (Trading)      │
                        └─────────────────┘
```

---

## Validation Rules

### Position Validation
- `quantity` must equal `abs(signed_qty)`
- `side` must match sign of `signed_qty` (positive = LONG, negative = SHORT)
- `ts_opened` <= `ts_last`
- If `ts_closed` set, `ts_closed` >= `ts_opened`

### Order Validation
- `filled_qty` <= `quantity`
- If `status == FILLED`, `filled_qty == quantity`
- If `order_type == LIMIT`, `price` required
- If `order_type == STOP_MARKET`, `trigger_price` required

### Reconciliation Validation
- `delta` must equal `venue_qty - cached_qty`
- If `resolution == SYNTHETIC_FILL`, `synthetic_order_id` required
- Total reconciled position must match venue position exactly

---

## Serialization

### Msgpack Encoding (Default)

```python
# Position snapshot serialization
snapshot_bytes = msgpack.packb({
    "position_id": str(position.id),
    "instrument_id": str(position.instrument_id),
    "strategy_id": str(position.strategy_id),
    "account_id": str(position.account_id),
    "side": position.side.value,
    "signed_qty": str(position.signed_qty),
    "quantity": str(position.quantity),
    "avg_px_open": str(position.avg_px_open),
    "realized_pnl": str(position.realized_pnl),
    "ts_opened": position.ts_opened,
    "ts_last": position.ts_last,
})
```

### JSON Encoding (Debug Mode)

```json
{
  "position_id": "BTCUSDT-PERP.BINANCE-001",
  "instrument_id": "BTCUSDT-PERP.BINANCE",
  "strategy_id": "MOMENTUM-001",
  "account_id": "BINANCE-USDT_FUTURES-master",
  "side": "LONG",
  "signed_qty": "0.5",
  "quantity": "0.5",
  "avg_px_open": "42500.00",
  "realized_pnl": "0.00",
  "ts_opened": 1703721600000000000,
  "ts_last": 1703725200000000000
}
```
