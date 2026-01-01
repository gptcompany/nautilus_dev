# Data Model: Binance Exec Client (Spec 015)

**Created**: 2025-12-28
**Status**: Draft

---

## Entity Definitions

### Entity: BinanceExecClientConfig

**Purpose**: Configuration for Binance execution client

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `api_key` | str | None | None | Sources BINANCE_API_KEY env var if None |
| `api_secret` | str | None | None | Sources BINANCE_API_SECRET env var if None |
| `account_type` | BinanceAccountType | Yes | SPOT | Enum: SPOT, USDT_FUTURES, COIN_FUTURES |
| `testnet` | bool | Yes | False | - |
| `us` | bool | Yes | False | Cannot be True with testnet=True |
| `use_position_ids` | bool | Yes | True | Required True for HEDGE mode |
| `max_retries` | PositiveInt | None | None | Max 10 to avoid bans |
| `retry_delay_initial_ms` | PositiveInt | None | None | Recommended 500ms |
| `retry_delay_max_ms` | PositiveInt | None | None | Recommended 5000ms |
| `futures_leverages` | dict[str, int] | None | None | Symbol to leverage mapping |
| `futures_margin_types` | dict[str, str] | None | None | CROSS or ISOLATED |

**Relationships**:
- Part of TradingNodeConfig.exec_clients

### Entity: BinanceInstrumentProviderConfig

**Purpose**: Configure which instruments to load

**Fields**:
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `load_all` | bool | Yes | False | Don't load 500+ instruments |
| `load_ids` | list[InstrumentId] | None | None | Specific instruments to load |

**Relationships**:
- Part of InstrumentProviderConfig

### Entity: OrderSubmissionRequest

**Purpose**: Internal representation for order submission

**Fields**:
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `instrument_id` | InstrumentId | Yes | e.g., BTCUSDT-PERP.BINANCE |
| `order_side` | OrderSide | Yes | BUY or SELL |
| `order_type` | OrderType | Yes | MARKET, LIMIT, etc. |
| `quantity` | Quantity | Yes | Positive decimal |
| `price` | Price | Conditional | Required for LIMIT orders |
| `trigger_price` | Price | Conditional | Required for STOP orders |
| `time_in_force` | TimeInForce | Yes | GTC, IOC, FOK, GTD |
| `reduce_only` | bool | No | Close position only |
| `post_only` | bool | No | Maker only |

**Validation Rules**:
- `quantity > 0`
- `price > 0` if order_type is LIMIT
- `trigger_price > 0` if order_type is STOP_*
- `reduce_only` only valid for USDT_FUTURES/COIN_FUTURES

---

## State Transitions

### Order Lifecycle

```
INITIALIZED -> SUBMITTED -> [ACCEPTED] -> [PARTIALLY_FILLED] -> FILLED
                        \-> REJECTED
                         \-> [ACCEPTED] -> CANCELED
                          \-> [ACCEPTED] -> EXPIRED
```

### Connection State

```
DISCONNECTED -> CONNECTING -> CONNECTED -> [RECONNECTING] -> CONNECTED
                          \-> DISCONNECTED (failure)
```

---

## Enumerations

### BinanceAccountType (existing)
```python
class BinanceAccountType(Enum):
    SPOT = "SPOT"
    USDT_FUTURE = "usdt_future"  # Perpetual USDT-margined (note: singular)
    COIN_FUTURE = "coin_future"  # Coin-margined (note: singular)
```

**IMPORTANT**: Enum names changed from plural to singular in nightly (2025-12-31).

### Supported OrderType (existing)
```python
# For USDT_FUTURES
MARKET = "MARKET"
LIMIT = "LIMIT"
STOP_MARKET = "STOP_MARKET"      # Via Algo Order API
STOP_LIMIT = "STOP_LIMIT"        # Via Algo Order API
TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"
TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
TRAILING_STOP_MARKET = "TRAILING_STOP_MARKET"
```

---

## Integration Points

### From Spec 014 (TradingNode Configuration)

Uses:
- `TradingNodeConfigFactory` - Creates complete node config
- `LiveExecEngineConfig` - Reconciliation settings
- `CacheConfig` - Redis persistence

### To Spec 016 (Order Reconciliation)

Provides:
- `external_order_claims` configuration
- Order state reports for reconciliation

---

## Data Validation

### Pre-Submission Checks

1. **Instrument Validity**: Check instrument_id is loaded
2. **Quantity Validation**: Min notional, tick size compliance
3. **Price Validation**: Decimal precision, min/max bounds
4. **Balance Check**: Sufficient margin/balance (optional pre-check)

### Post-Submission Monitoring

1. **Order Status**: Track via WebSocket updates
2. **Fill Events**: Process ExecutionReport messages
3. **Rejection Handling**: Log reason, update state
