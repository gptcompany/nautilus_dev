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
from nautilus_trader.adapters.binance.config import BinanceExecClientConfig
from nautilus_trader.adapters.binance.common.enums import BinanceAccountType

# Minimal configuration (uses env vars for API keys)
binance_exec = BinanceExecClientConfig(
    account_type=BinanceAccountType.USDT_FUTURES,
    testnet=True,  # Start with testnet!
)

# Production configuration
binance_exec_prod = BinanceExecClientConfig(
    account_type=BinanceAccountType.USDT_FUTURES,
    testnet=False,
    max_retries=3,
    use_position_ids=True,
    futures_leverages={"BTCUSDT": 10},
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
from nautilus_trader.model.enums import OrderSide, TimeInForce

class MyStrategy(Strategy):
    def submit_market_buy(self, quantity: Quantity) -> None:
        """Submit market buy order."""
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=quantity,
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def submit_limit_sell(self, quantity: Quantity, price: Price) -> None:
        """Submit limit sell order."""
        order = self.order_factory.limit(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=quantity,
            price=price,
            time_in_force=TimeInForce.GTC,
            post_only=True,  # Maker only
        )
        self.submit_order(order)

    def submit_stop_market(self, side: OrderSide, quantity: Quantity, trigger: Price) -> None:
        """Submit stop market order (uses Algo Order API)."""
        order = self.order_factory.stop_market(
            instrument_id=self.instrument_id,
            order_side=side,
            quantity=quantity,
            trigger_price=trigger,
        )
        self.submit_order(order)
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
# Solution: Increase retry delays
binance_exec = BinanceExecClientConfig(
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
