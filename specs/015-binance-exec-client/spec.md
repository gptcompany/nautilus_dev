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
    account_type=BinanceAccountType.USDT_FUTURE,  # Note: singular (nightly v1.222.0+)
    api_key=None,  # Sources from BINANCE_API_KEY env var
    api_secret=None,  # Sources from BINANCE_API_SECRET env var
    testnet=False,
    us=False,
    warn_rate_limits=True,
    max_retries=3,
    retry_delay_initial_ms=500,  # Native param name
    retry_delay_max_ms=5000,
)
```

**Note**: `base_url_http`, `base_url_ws`, and `clock_sync_interval_secs` are handled automatically by the adapter based on `account_type` and `testnet` settings.

#### FR-002: Supported Order Types
| Order Type | Support | Scope | Notes |
|------------|---------|-------|-------|
| MARKET | Yes | MVP | Immediate execution |
| LIMIT | Yes | MVP | Post-only supported |
| STOP_MARKET | Yes | MVP | Requires Algo Order API (fixed in nightly) |
| STOP_LIMIT | Yes | MVP | Requires Algo Order API (fixed in nightly) |
| TAKE_PROFIT_MARKET | Future | v2 | Via conditional orders - same API as STOP_MARKET |
| TRAILING_STOP_MARKET | Future | v2 | Exchange-side only, requires additional params |

**MVP Scope Note**: Initial implementation covers MARKET, LIMIT, STOP_MARKET, STOP_LIMIT. TAKE_PROFIT and TRAILING_STOP use same Algo Order API and can be added in v2 with minimal changes.

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
- Auto-reconnect on WebSocket disconnect (handled by native BinanceExecClient)
- Order state consistency after reconnect (handled by native adapter)

**Note**: WebSocket reconnection and state recovery are built into NautilusTrader's BinanceExecClient. No custom implementation required - integration tests validate this behavior.

## Technical Design

### Client Setup

```python
def build_binance_exec_client_config(credentials: BinanceCredentials) -> BinanceExecClientConfig:
    """Build Binance execution client configuration."""
    return BinanceExecClientConfig(
        account_type=BinanceAccountType.USDT_FUTURE,  # Note: singular (nightly v1.222.0+)
        api_key=credentials.api_key,
        api_secret=credentials.api_secret,
        testnet=credentials.testnet,
        warn_rate_limits=True,
        max_retries=3,
    )
```

### Instrument Provider
```python
# Example: Load specific instruments (parameterized in factory)
InstrumentProviderConfig(
    load_all=False,  # Don't load all 500+ instruments
    load_ids=instrument_ids,  # Passed as parameter to factory
)
```

**Note**: Instrument IDs are passed to `create_binance_instrument_provider()` as a parameter, not hardcoded.

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
- Fixed in nightly: `pip install nautilus_trader==1.222.0a20251026`

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
