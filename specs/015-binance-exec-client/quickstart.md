# Quickstart: Binance Exec Client (Spec 015)

## Prerequisites

1. **NautilusTrader Nightly** (>= 2025-12-10 for Algo Order API fix)
2. **Binance API credentials** (Futures enabled)
3. **Spec 014 completed** (TradingNode Configuration)

## Environment Setup

```bash
# Required environment variables
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"
export BINANCE_TESTNET="true"  # Optional: Use testnet

# Activate nightly environment
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
```

## Basic Configuration

```python
from config import TradingNodeConfigFactory
from config.models import BinanceCredentials
from config.clients.binance import build_binance_exec_client_config

# Create credentials (uses env vars if api_key/api_secret not provided)
credentials = BinanceCredentials(
    api_key="your_api_key",  # Or set BINANCE_API_KEY env var
    api_secret="your_api_secret",  # Or set BINANCE_API_SECRET env var
    account_type="USDT_FUTURES",
    testnet=True,  # Start with testnet!
)

# Build exec client config using helper
binance_exec = build_binance_exec_client_config(
    credentials,
    max_retries=3,
    retry_delay_initial_ms=500,
    retry_delay_max_ms=5000,
    futures_leverages={"BTCUSDT": 10, "ETHUSDT": 5},
    futures_margin_types={"BTCUSDT": "CROSS"},
)
```

## Integration with TradingNode (Spec 014)

```python
from nautilus_trader.config import TradingNodeConfig
from config.tradingnode_factory import create_tradingnode_config

# Use factory from Spec 014
node_config = create_tradingnode_config(
    trader_id="TRADER-001",
    exec_clients={"BINANCE": binance_exec},
    redis_enabled=True,
)

# Create and run node
node = TradingNode(config=node_config)
node.run()
```

## Order Submission Pattern

```python
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.objects import Price, Quantity
from config import (
    create_market_order,
    create_limit_order,
    create_stop_market_order,
    create_external_claims,
)

class MyStrategy(Strategy):
    def submit_market_buy(self, quantity: Quantity) -> None:
        """Submit market buy order using helper."""
        order = create_market_order(
            self.order_factory,
            self.instrument_id,
            OrderSide.BUY,
            quantity,
        )
        self.submit_order(order)

    def submit_limit_sell(self, quantity: Quantity, price: Price) -> None:
        """Submit limit sell order using helper."""
        order = create_limit_order(
            self.order_factory,
            self.instrument_id,
            OrderSide.SELL,
            quantity,
            price,
            post_only=True,  # Maker only
        )
        self.submit_order(order)

    def submit_stop_loss(self, quantity: Quantity, trigger: Price) -> None:
        """Submit stop-loss (uses Algo Order API)."""
        order = create_stop_market_order(
            self.order_factory,
            self.instrument_id,
            OrderSide.SELL,  # For long positions
            quantity,
            trigger,
            reduce_only=True,  # Close position only
        )
        self.submit_order(order)
```

## External Order Claims (Position Recovery)

```python
from config import create_external_claims

# For strategy config - claim positions on restart
external_claims = create_external_claims([
    "BTCUSDT-PERP.BINANCE",
    "ETHUSDT-PERP.BINANCE",
])

# Use in strategy configuration
class MyStrategyConfig(StrategyConfig):
    external_order_claims = external_claims
```

## Testnet Validation Checklist

- [ ] Connect to Binance testnet
- [ ] Submit MARKET order
- [ ] Submit LIMIT order
- [ ] Submit STOP_MARKET order (Algo API)
- [ ] Cancel open order
- [ ] Verify fill events received
- [ ] Test reconnection after disconnect

## Common Issues & Solutions

### Rate Limiting
```python
# Error: -1003 TOO_MANY_REQUESTS
# Use error handling helpers
from config import is_retryable_error, calculate_backoff_delay, should_retry

error_code = -1003  # TOO_MANY_REQUESTS

# Check if retryable
if is_retryable_error(error_code):
    should, delay_ms = should_retry(error_code, attempt=1, max_retries=3)
    if should:
        print(f"Retrying in {delay_ms}ms")

# Or configure client with longer delays
binance_exec = build_binance_exec_client_config(
    credentials,
    max_retries=3,
    retry_delay_initial_ms=1000,  # 1 second
    retry_delay_max_ms=10000,     # 10 seconds max
)
```

### Algo Order API Required
```python
# Error: -4120 Order type not supported
# Solution: Use nightly >= 2025-12-10
pip install nautilus_trader --index-url=https://packages.nautechsystems.io/simple
```

### Insufficient Margin
```python
# Handle in strategy
def on_order_rejected(self, event: OrderRejected) -> None:
    if "insufficient" in str(event.reason).lower():
        self.log.warning(f"Margin insufficient: {event}")
        # Don't retry, wait for funds
```

## Next Steps

1. Run testnet validation
2. Configure external_order_claims (Spec 016)
3. Set up Redis persistence (Spec 018)
4. Implement graceful shutdown (Spec 019)
