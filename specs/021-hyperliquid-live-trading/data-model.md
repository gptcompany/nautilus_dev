# Data Model: Hyperliquid Live Trading (Spec 021)

**Created**: 2025-12-28
**Status**: Draft

---

## Entity Definitions

### Entity: HyperliquidDataClientConfig

**Purpose**: Configuration for Hyperliquid market data streaming

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `testnet` | bool | Yes | False | - |
| `base_url_http` | str | None | None | Auto-set based on testnet |
| `base_url_ws` | str | None | None | Auto-set based on testnet |
| `http_timeout_secs` | int | No | 10 | Positive integer |
| `http_proxy_url` | str | None | None | Valid URL |
| `ws_proxy_url` | str | None | None | Valid URL |
| `instrument_provider` | InstrumentProviderConfig | Yes | - | load_all or load_ids |

**Relationships**:
- Part of TradingNodeConfig.data_clients

---

### Entity: HyperliquidExecClientConfig

**Purpose**: Configuration for Hyperliquid order execution

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `private_key` | str | None | None | Sources from env var if None |
| `vault_address` | str | None | None | Optional for delegated trading |
| `testnet` | bool | Yes | False | - |
| `max_retries` | int | None | None | Positive integer, max 10 |
| `retry_delay_initial_ms` | int | None | None | Recommended 100ms |
| `retry_delay_max_ms` | int | None | None | Recommended 5000ms |
| `http_timeout_secs` | int | No | 10 | Positive integer |
| `instrument_provider` | InstrumentProviderConfig | Yes | - | load_all or load_ids |

**Relationships**:
- Part of TradingNodeConfig.exec_clients

**Environment Variables**:
| Variable | Testnet | Mainnet |
|----------|---------|---------|
| Private Key | HYPERLIQUID_TESTNET_PK | HYPERLIQUID_PK |
| Vault Address | HYPERLIQUID_TESTNET_VAULT | HYPERLIQUID_MAINNET_VAULT |

---

### Entity: HyperliquidStrategyConfig

**Purpose**: Strategy configuration for Hyperliquid trading

**Fields**:
| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `instrument_id` | str | Yes | - | e.g., "BTC-USD-PERP.HYPERLIQUID" |
| `risk` | RiskConfig | Yes | - | From Spec 011 |
| `order_size` | Decimal | Yes | - | Base order size |
| `max_position_size` | Decimal | Yes | - | Maximum position |

**Relationships**:
- Uses RiskConfig from Spec 011
- Passed to Strategy.__init__()

---

## Enumerations

### Hyperliquid Instrument Types
```python
# Perpetual Futures (primary)
"BTC-USD-PERP.HYPERLIQUID"
"ETH-USD-PERP.HYPERLIQUID"
"SOL-USD-PERP.HYPERLIQUID"

# Spot Markets
"PURR-USDC-SPOT.HYPERLIQUID"
"HYPE-USDC-SPOT.HYPERLIQUID"
```

### Supported Order Types
```python
MARKET = "MARKET"           # Executed as IOC limit
LIMIT = "LIMIT"             # GTC, IOC supported
STOP_MARKET = "STOP_MARKET" # Native trigger
STOP_LIMIT = "STOP_LIMIT"   # Native trigger
MARKET_IF_TOUCHED = "MARKET_IF_TOUCHED"  # Take profit
LIMIT_IF_TOUCHED = "LIMIT_IF_TOUCHED"    # Take profit
```

### Time in Force
```python
GTC = "GTC"  # Good Till Canceled
IOC = "IOC"  # Immediate or Cancel
# NOT supported: FOK, GTD
```

---

## State Transitions

### Order Lifecycle

```
INITIALIZED -> SUBMITTED -> [ACCEPTED] -> [PARTIALLY_FILLED] -> FILLED
                        \-> REJECTED (insufficient funds, invalid order)
                         \-> [ACCEPTED] -> CANCELED (user cancel)
                          \-> [ACCEPTED] -> EXPIRED (IOC not filled)
```

### Connection State

```
DISCONNECTED -> CONNECTING -> CONNECTED -> [RECONNECTING] -> CONNECTED
                          \-> DISCONNECTED (chain congestion, network error)
```

Note: Hyperliquid WebSocket implements auto-reconnect with resubscribe.

---

## Data Types

### QuoteTick (from DataClient)
```python
@dataclass
class QuoteTick:
    instrument_id: InstrumentId
    bid_price: Price
    ask_price: Price
    bid_size: Quantity
    ask_size: Quantity
    ts_event: int  # Unix nanoseconds
    ts_init: int   # Unix nanoseconds
```

### TradeTick (from DataClient)
```python
@dataclass
class TradeTick:
    instrument_id: InstrumentId
    price: Price
    size: Quantity
    aggressor_side: AggressorSide
    trade_id: str
    ts_event: int
    ts_init: int
```

### OrderBookDelta (from DataClient)
```python
@dataclass
class OrderBookDelta:
    instrument_id: InstrumentId
    action: BookAction  # ADD, UPDATE, DELETE, CLEAR
    order: BookOrder
    ts_event: int
    ts_init: int
```

---

## Integration Points

### From Spec 011 (Stop-Loss & Position Limits)

Uses:
- `RiskConfig` - risk parameters
- `RiskManager` - position management
- Auto stop-loss on PositionOpened

### From Spec 014 (TradingNode Configuration)

Uses:
- `TradingNodeConfig` patterns
- `LiveExecEngineConfig` for reconciliation
- `CacheConfig` for Redis persistence

### To Spec 023 (Auto-Update Pipeline)

Affected by:
- NautilusTrader adapter changes
- Config parameter changes
- New order types or features

---

## Data Validation

### Pre-Connection Checks

1. **Credentials**: Verify env vars set
2. **Network**: Check connectivity to Hyperliquid endpoints
3. **Instruments**: Verify requested instruments exist

### Pre-Order Checks

1. **Instrument Validity**: Check instrument_id is subscribed
2. **Quantity**: Min notional, precision compliance
3. **Price**: For limit orders, reasonable vs current market
4. **Balance**: Sufficient margin (if possible to pre-check)

### Post-Order Monitoring

1. **Fill Events**: Track via WebSocket
2. **Rejection Handling**: Log reason, notify strategy
3. **Partial Fills**: Update position tracking
