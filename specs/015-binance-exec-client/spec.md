# Spec 015: Binance Exec Client Integration

## Overview

Configure and integrate Binance execution client for live order submission and management.

## Problem Statement

Current system only reads data from Binance. For live trading, we need execution capability with proper configuration, error handling, and reconciliation.

## Goals

1. **Execution Client**: Configure BinanceExecClient for USDT Futures
2. **Order Types**: Support Market, Limit, Stop-Market, Stop-Limit
3. **Error Handling**: Graceful handling of Binance-specific errors

## Requirements

### Functional Requirements

#### FR-001: Client Configuration
```python
BinanceExecClientConfig(
    account_type=BinanceAccountType.USDT_FUTURES,
    base_url_http="https://fapi.binance.com",
    base_url_ws="wss://fstream.binance.com",
    api_key=os.environ["BINANCE_API_KEY"],
    api_secret=os.environ["BINANCE_API_SECRET"],
    testnet=False,
    us=False,
    clock_sync_interval_secs=60,
    warn_rate_limits=True,
    max_retries=3,
    retry_delay_secs=1.0,
)
```

#### FR-002: Supported Order Types
| Order Type | Support | Notes |
|------------|---------|-------|
| MARKET | Yes | Immediate execution |
| LIMIT | Yes | Post-only supported |
| STOP_MARKET | Yes | Requires Algo Order API |
| STOP_LIMIT | Yes | Requires Algo Order API |
| TAKE_PROFIT_MARKET | Yes | Via conditional orders |
| TRAILING_STOP_MARKET | Partial | Exchange-side only |

#### FR-003: Position Mode
- Support ONE-WAY mode (default)
- HEDGE mode has known issues (see Discord)

#### FR-004: Error Handling
- Rate limit errors: Exponential backoff
- Insufficient balance: Log and skip order
- Invalid symbol: Fail fast with clear error
- Network errors: Retry with backoff

#### FR-005: External Order Claims
```python
# For reconciliation of existing positions
strategy_config = StrategyConfig(
    external_order_claims=[
        InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
        InstrumentId.from_str("ETHUSDT-PERP.BINANCE"),
    ],
)
```

### Non-Functional Requirements

#### NFR-001: Latency
- Order submission < 100ms (network dependent)
- Fill notification < 50ms after exchange fill

#### NFR-002: Reliability
- Auto-reconnect on WebSocket disconnect
- Order state consistency after reconnect

## Technical Design

### Client Setup

```python
def create_binance_exec_client() -> dict:
    """Create Binance execution client configuration."""
    return {
        "BINANCE": BinanceExecClientConfig(
            account_type=BinanceAccountType.USDT_FUTURES,
            api_key=os.environ["BINANCE_API_KEY"],
            api_secret=os.environ["BINANCE_API_SECRET"],
            testnet=os.environ.get("BINANCE_TESTNET", "false").lower() == "true",
            warn_rate_limits=True,
            max_retries=3,
        ),
    }
```

### Instrument Provider
```python
InstrumentProviderConfig(
    load_all=False,  # Don't load all 500+ instruments
    load_ids=[
        InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
        InstrumentId.from_str("ETHUSDT-PERP.BINANCE"),
    ],
)
```

### Order Submission Pattern
```python
def submit_market_order(self, side: OrderSide, quantity: Quantity) -> None:
    order = self.order_factory.market(
        instrument_id=self.instrument_id,
        order_side=side,
        quantity=quantity,
        time_in_force=TimeInForce.GTC,
    )
    self.submit_order(order)
```

## Known Issues (Discord)

### ADL (Auto-Deleveraging)
- Binance sends ADL fills with either `x=CALCULATED` or `x=TRADE`
- Fixed in recent nightly versions

### Chinese Character Tokens
- Some Binance tokens have Chinese names (e.g., '币安人生')
- Fixed in nightly: `pip install nautilus_trader==1.221.0a20251026`

### STOP_MARKET Orders
- Requires Algo Order API endpoint
- Fixed in development wheels

## Testing Strategy

1. **Testnet Validation**: Full order cycle on testnet
2. **Order Types**: Test each supported order type
3. **Error Scenarios**: Rate limits, insufficient balance, invalid orders

## Dependencies

- Spec 014 (TradingNode Configuration)
- Binance API credentials

## Success Metrics

- Order fill rate > 99.9%
- Fill latency < 100ms (median)
- Zero lost orders
