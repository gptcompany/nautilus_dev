# NautilusTrader Binance Execution Client Research

**Version**: Nightly (v1.222.0+)  
**Last Updated**: 2025-12-31  
**Source**: Context7 + Discord Community + Local Docs

---

## 1. BinanceExecClientConfig Parameters

### Configuration Options (Nightly)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `venue` | `str` | `BINANCE` | Venue identifier |
| `api_key` | `str` | `None` | API key (uses `BINANCE_API_KEY` env var if None) |
| `api_secret` | `str` | `None` | API secret (uses `BINANCE_API_SECRET` env var if None) |
| `key_type` | `BinanceKeyType` | `HMAC` | `HMAC`, `RSA`, or `ED25519` |
| `account_type` | `BinanceAccountType` | `SPOT` | Account type (see section 2) |
| `base_url_http` | `str` | `None` | Override HTTP REST base URL |
| `base_url_ws` | `str` | `None` | Override WebSocket base URL |
| `proxy_url` | `str` | `None` | Optional proxy URL |
| `us` | `bool` | `False` | Use Binance US endpoints |
| `testnet` | `bool` | `False` | Use testnet endpoints |
| `use_gtd` | `bool` | `True` | Pass GTD to Binance (False = local expiry) |
| `use_reduce_only` | `bool` | `True` | Pass reduce_only to Binance (False for Hedge mode) |
| `use_position_ids` | `bool` | `True` | Enable Binance hedging position IDs |
| `use_trade_lite` | `bool` | `False` | Use TRADE_LITE events with derived fees |
| `treat_expired_as_canceled` | `bool` | `False` | Treat EXPIRED as CANCELED |
| `recv_window_ms` | `int` | `5000` | Receive window for signed requests |
| `max_retries` | `int` | `None` | Max retry attempts for order calls |
| `retry_delay_initial_ms` | `int` | `None` | Initial retry delay |
| `retry_delay_max_ms` | `int` | `None` | Maximum retry delay |
| `futures_leverages` | `dict` | `None` | Symbol -> leverage mapping |
| `futures_margin_types` | `dict` | `None` | Symbol -> margin type (isolated/cross) |
| `listen_key_ping_max_failures` | `int` | `3` | Listen key ping failures before recovery |
| `log_rejected_due_post_only_as_warning` | `bool` | `True` | Log post-only rejections as warnings |

### Example Configuration

```python
from nautilus_trader.adapters.binance import BINANCE
from nautilus_trader.adapters.binance import BinanceAccountType
from nautilus_trader.adapters.binance import BinanceExecClientConfig
from nautilus_trader.live.node import TradingNode

config = TradingNodeConfig(
    exec_clients={
        BINANCE: BinanceExecClientConfig(
            api_key=None,  # Uses BINANCE_API_KEY env var
            api_secret=None,  # Uses BINANCE_API_SECRET env var
            account_type=BinanceAccountType.USDT_FUTURES,
            testnet=False,
            use_reduce_only=True,  # Set False for Hedge mode
            max_retries=3,
            retry_delay_initial_ms=1000,
            retry_delay_max_ms=5000,
        ),
    },
)
```

---

## 2. BinanceAccountType Enum Values

| Enum Value | String | Description |
|------------|--------|-------------|
| `BinanceAccountType.SPOT` | `"spot"` | Spot trading |
| `BinanceAccountType.MARGIN` | `"margin"` | Cross margin (shared) |
| `BinanceAccountType.ISOLATED_MARGIN` | `"isolated_margin"` | Isolated margin (per position) |
| `BinanceAccountType.USDT_FUTURES` | `"usdt_future"` | USDT-margined perpetuals/delivery |
| `BinanceAccountType.COIN_FUTURES` | `"coin_future"` | Coin-margined futures |

### Import

```python
from nautilus_trader.adapters.binance import BinanceAccountType

# Usage
account_type = BinanceAccountType.USDT_FUTURES
```

### String Values in Config

When using dictionary configs:
```python
exec_clients={
    BINANCE: {
        "account_type": "usdt_future",  # String form
        # or
        "account_type": BinanceAccountType.USDT_FUTURES,  # Enum form
    },
}
```

---

## 3. Known Issues with Binance Adapter (from Discord)

### 3.1 ADL (Auto-Deleveraging) Handling

**Issue**: ADL fills with `x=TRADE` execution type were being dropped.

**Status**: FIXED in commit `32896d3` (2025-11-22)

**Details**:
- Binance can send ADL fills with either `x=CALCULATED` or `x=TRADE` execution types
- Previous versions only checked for `CALCULATED`
- Fix adds `X=FILLED` status check so both ADL message variants are handled

**Detection**: ADL orders use client ID `adl_autoclose`

```python
# ADL, Liquidation, and Settlement order detection:
# - Liquidations: client_id starts with "autoclose-"
# - ADL: client_id = "adl_autoclose"
# - Settlements: client_id starts with "settlement_autoclose-"
```

### 3.2 STOP_MARKET Orders - Algo API Required

**Issue**: STOP_MARKET orders fail with error:
```
reason='{'code': -4120, 'msg': 'Order type not supported for this endpoint. Please use the Algo Order API endpoints instead.'}'
```

**Status**: FIXED in commit `62ef6f6` (2025-12-10)

**GitHub Issue**: [#3287](https://github.com/nautechsystems/nautilus_trader/issues/3287)

**Solution**: Install nightly version with the fix:
```bash
pip install nautilus_trader==1.221.0a20251210 --index-url=https://packages.nautechsystems.io/simple
```

### 3.3 Chinese Character Tokens (e.g., '币安人生')

**Issue**: Rust panics on non-ASCII currency codes:
```
Condition failed: invalid string for 'code' contained a non-ASCII char, was '币安人生'
```

**Status**: FIXED in nightly (2025-10-26+)

**GitHub Issue**: [#3053](https://github.com/nautechsystems/nautilus_trader/issues/3053)

**Solution**:
```bash
pip install nautilus_trader==1.221.0a20251026 --index-url=https://packages.nautechsystems.io/simple
```

**Temporary Workaround** (if can't upgrade):
Add filter in `binance.http.client` `send_request()` to skip non-ASCII symbols.

### 3.4 OrderFilled Events Not Received (Binance US)

**Issue**: Orders fill on Binance UI but `on_order_filled()` not triggered.

**Status**: INVESTIGATING (GitHub #3006)

**Likely Cause**: External order processing, missing instrument with silent return.

### 3.5 Hedge Mode Position Reconciliation

**Issue**: Two positions (LONG + SHORT) received but only one shows after reconciliation.

**Status**: OPEN BUG (GitHub #3104)

**Workaround**: Ensure `use_reduce_only=False` and position_id suffix (`-LONG`/`-SHORT`).

### 3.6 FundingRateUpdate Not Implemented

**Status**: Not implemented for Binance (only Rust-based adapters)

**Workaround**: Implement custom subscription in Python base class.

---

## 4. Order Types Supported

### Order Type Matrix

| Order Type | Spot | Margin | USDT Futures | COIN Futures |
|------------|------|--------|--------------|--------------|
| `MARKET` | Yes | Yes | Yes | Yes |
| `LIMIT` | Yes | Yes | Yes | Yes |
| `STOP_MARKET` | No | Yes | Yes | Yes |
| `STOP_LIMIT` | Yes | Yes | Yes | Yes |
| `MARKET_IF_TOUCHED` | No | No | Yes | Yes |
| `LIMIT_IF_TOUCHED` | Yes | Yes | Yes | Yes |
| `TRAILING_STOP_MARKET` | No | No | Yes | Yes |

### Order Submission Examples

#### MARKET Order
```python
from nautilus_trader.model.orders import MarketOrder

order = self.order_factory.market(
    instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    order_side=OrderSide.BUY,
    quantity=Quantity.from_str("0.001"),
)
self.submit_order(order)
```

#### LIMIT Order
```python
from nautilus_trader.model.orders import LimitOrder

order = self.order_factory.limit(
    instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    order_side=OrderSide.BUY,
    quantity=Quantity.from_str("0.001"),
    price=Price.from_str("50000.00"),
    time_in_force=TimeInForce.GTC,
)
self.submit_order(order)
```

#### STOP_MARKET Order (Futures only)
```python
order = self.order_factory.stop_market(
    instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    order_side=OrderSide.SELL,
    quantity=Quantity.from_str("0.001"),
    trigger_price=Price.from_str("49000.00"),
    trigger_type=TriggerType.LAST_TRADE,  # or MARK_PRICE
)
self.submit_order(order)
```

#### STOP_LIMIT Order
```python
order = self.order_factory.stop_limit(
    instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    order_side=OrderSide.SELL,
    quantity=Quantity.from_str("0.001"),
    price=Price.from_str("48900.00"),  # Limit price
    trigger_price=Price.from_str("49000.00"),  # Stop price
    time_in_force=TimeInForce.GTC,
)
self.submit_order(order)
```

#### TRAILING_STOP_MARKET Order (Futures only)
```python
order = self.order_factory.trailing_stop_market(
    instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    order_side=OrderSide.SELL,
    quantity=Quantity.from_str("0.001"),
    activation_price=Price.from_str("55000.00"),  # Optional: when to activate
    trailing_offset=Decimal("100"),  # Callback rate in basis points
    trailing_offset_type=TrailingOffsetType.BASIS_POINTS,
)
self.submit_order(order)
```

**WARNING**: Do NOT use `trigger_price` for trailing stops - use `activation_price` instead.

### Time in Force Options

| TIF | Spot | Futures | Notes |
|-----|------|---------|-------|
| `GTC` | Yes | Yes | Good Till Canceled |
| `GTD` | Yes* | Yes | *Converted to GTC for Spot with warning |
| `FOK` | Yes | Yes | Fill or Kill |
| `IOC` | Yes | Yes | Immediate or Cancel |

### Execution Instructions

| Instruction | Spot | Futures | Notes |
|-------------|------|---------|-------|
| `post_only` | Yes | Yes | LIMIT orders only (uses LIMIT_MAKER/GTX) |
| `reduce_only` | No | Yes | Disabled in Hedge Mode |

---

## 5. Error Handling Patterns

### 5.1 Rate Limit Handling

**Binance Rate Limits**:
| Endpoint | Limit (weight/min) |
|----------|-------------------|
| Global (Spot) | 6,000 |
| Global (Futures) | 2,400 |
| `/api/v3/order` | 3,000 |
| `/fapi/v1/order` | 1,200 |
| `/fapi/v1/klines` | 600 |

**HTTP 429 Response**: Rate limit exceeded - back off immediately.

**Best Practice**:
```python
# Configure retry behavior in exec client
BinanceExecClientConfig(
    max_retries=3,
    retry_delay_initial_ms=1000,
    retry_delay_max_ms=5000,
)
```

### 5.2 Reconnection Handling

The adapter automatically handles:
- WebSocket disconnections with automatic reconnect
- Listen key expiration (ping every ~30 min, max 3 failures before recovery)
- Order book snapshot rebuild on reconnect

**Listen Key Configuration**:
```python
BinanceExecClientConfig(
    listen_key_ping_max_failures=3,  # Triggers recovery after 3 consecutive failures
)
```

### 5.3 Order State Consistency

**Reconciliation on Startup**:
```python
from nautilus_trader.live.config import LiveExecEngineConfig

LiveExecEngineConfig(
    reconciliation=True,
    reconciliation_startup_delay_secs=10.0,  # Minimum 10s recommended
)
```

**Risk Event Handling** (Futures):
- Liquidations: Orders with client_id starting `autoclose-`
- ADL: Orders with client_id `adl_autoclose`
- Settlements: Orders with client_id starting `settlement_autoclose-`

All risk events generate:
1. Warning log with order details
2. `OrderStatusReport` to seed cache
3. `FillReport` with TAKER liquidity side

### 5.4 Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `-1000` | Unknown error | Retry with exponential backoff |
| `-1003` | Too many requests | Reduce request frequency |
| `-1015` | Too many orders | Reduce order rate |
| `-2010` | NEW_ORDER_REJECTED | Check order parameters |
| `-2011` | CANCEL_REJECTED | Order already filled/canceled |
| `-4120` | Order type not supported | Use Algo Order API (STOP_MARKET) |

---

## 6. Testnet Configuration

### Environment Variables

**Spot/Margin Testnet**:
```bash
export BINANCE_TESTNET_API_KEY="your_testnet_api_key"
export BINANCE_TESTNET_API_SECRET="your_testnet_api_secret"
```

**Futures Testnet**:
```bash
export BINANCE_FUTURES_TESTNET_API_KEY="your_futures_testnet_api_key"
export BINANCE_FUTURES_TESTNET_API_SECRET="your_futures_testnet_api_secret"
```

### Configuration

```python
from nautilus_trader.adapters.binance import BINANCE
from nautilus_trader.adapters.binance import BinanceAccountType
from nautilus_trader.adapters.binance import BinanceDataClientConfig
from nautilus_trader.adapters.binance import BinanceExecClientConfig

config = TradingNodeConfig(
    data_clients={
        BINANCE: BinanceDataClientConfig(
            api_key=None,  # Uses BINANCE_TESTNET_API_KEY
            api_secret=None,  # Uses BINANCE_TESTNET_API_SECRET
            account_type=BinanceAccountType.SPOT,  # or USDT_FUTURES
            testnet=True,  # CRITICAL: Enable testnet
        ),
    },
    exec_clients={
        BINANCE: BinanceExecClientConfig(
            api_key=None,
            api_secret=None,
            account_type=BinanceAccountType.SPOT,
            testnet=True,  # CRITICAL: Enable testnet
        ),
    },
)
```

### Testnet URLs (Automatic)

When `testnet=True`:
- **Spot**: `testnet.binance.vision`
- **Futures**: `testnet.binancefuture.com`

### Testnet Limitations

1. Limited liquidity
2. May not support all order types
3. ADL behavior more frequent (smaller insurance fund)
4. Some instruments may be missing

---

## 7. Complete Live Trading Example

```python
from decimal import Decimal

from nautilus_trader.adapters.binance import BINANCE
from nautilus_trader.adapters.binance import BinanceAccountType
from nautilus_trader.adapters.binance import BinanceDataClientConfig
from nautilus_trader.adapters.binance import BinanceExecClientConfig
from nautilus_trader.adapters.binance import BinanceLiveDataClientFactory
from nautilus_trader.adapters.binance import BinanceLiveExecClientFactory
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.config import LiveExecEngineConfig
from nautilus_trader.live.node import TradingNode

config = TradingNodeConfig(
    trader_id="TRADER-001",
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,
    ),
    data_clients={
        BINANCE: BinanceDataClientConfig(
            api_key=None,  # Uses env var
            api_secret=None,  # Uses env var
            account_type=BinanceAccountType.USDT_FUTURES,
            testnet=False,
            instrument_provider=InstrumentProviderConfig(load_all=True),
        ),
    },
    exec_clients={
        BINANCE: BinanceExecClientConfig(
            api_key=None,
            api_secret=None,
            account_type=BinanceAccountType.USDT_FUTURES,
            testnet=False,
            use_reduce_only=True,
            max_retries=3,
            retry_delay_initial_ms=1000,
            retry_delay_max_ms=5000,
            futures_leverages={"BTCUSDT": 10, "ETHUSDT": 5},
        ),
    },
)

node = TradingNode(config=config)
node.add_data_client_factory(BINANCE, BinanceLiveDataClientFactory)
node.add_exec_client_factory(BINANCE, BinanceLiveExecClientFactory)
node.build()
```

---

## 8. Hedge Mode Configuration

For Binance Futures Hedge Mode (simultaneous LONG + SHORT positions):

```python
# 1. Enable Hedge Mode on Binance first (via UI or API)

# 2. Configure execution client
BinanceExecClientConfig(
    account_type=BinanceAccountType.USDT_FUTURES,
    use_reduce_only=False,  # CRITICAL: Must be False for Hedge mode
    use_position_ids=True,  # Enable position ID tracking
)

# 3. Submit orders with position_id suffix
def buy_long(self):
    order = self.order_factory.market(
        instrument_id=self.instrument_id,
        order_side=OrderSide.BUY,
        quantity=Quantity.from_str("0.001"),
    )
    position_id = PositionId(f"{self.instrument_id}-LONG")  # LONG suffix
    self.submit_order(order, position_id)

def sell_short(self):
    order = self.order_factory.market(
        instrument_id=self.instrument_id,
        order_side=OrderSide.SELL,
        quantity=Quantity.from_str("0.001"),
    )
    position_id = PositionId(f"{self.instrument_id}-SHORT")  # SHORT suffix
    self.submit_order(order, position_id)
```

---

## References

- Official Docs: https://docs.nautilustrader.io/nightly/integrations/binance/
- GitHub Issues: #3287 (STOP_MARKET), #3053 (Chinese chars), #3104 (Hedge reconciliation)
- Discord: #binance channel (90-day archive in docs/discord/binance.md)
- Binance API: https://binance-docs.github.io/apidocs/futures/en/
