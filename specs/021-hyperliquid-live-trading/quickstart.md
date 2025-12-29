# Quickstart: Hyperliquid Live Trading (Spec 021)

## Prerequisites

1. **NautilusTrader Nightly** >= 1.222.0
2. **Hyperliquid account** (testnet first, then mainnet)
3. **EVM wallet** with private key
4. **USDC** deposited on Hyperliquid

## Environment Setup

```bash
# Activate nightly environment
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate

# Testnet credentials (NEVER commit these!)
export HYPERLIQUID_TESTNET_PK="0x_your_testnet_private_key"
export HYPERLIQUID_TESTNET_VAULT=""  # Optional, leave empty if not using vault

# Mainnet credentials (use separate wallet!)
export HYPERLIQUID_MAINNET_PK="0x_your_mainnet_private_key"
export HYPERLIQUID_MAINNET_VAULT=""  # Optional
```

## Phase 1: Data Feed Only

```python
from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.adapters.hyperliquid import HyperliquidDataClientConfig
from nautilus_trader.config import InstrumentProviderConfig, TradingNodeConfig
from nautilus_trader.live.node import TradingNode

# Data-only configuration (no execution)
config = TradingNodeConfig(
    trader_id="TRADER-HL-DATA",
    data_clients={
        HYPERLIQUID: HyperliquidDataClientConfig(
            instrument_provider=InstrumentProviderConfig(
                load_all=False,
                load_ids=[
                    "BTC-USD-PERP.HYPERLIQUID",
                    "ETH-USD-PERP.HYPERLIQUID",
                ],
            ),
            testnet=False,  # Use mainnet for data (more liquidity)
        ),
    },
)

# Run node
node = TradingNode(config=config)
node.run()
```

## Phase 2: Testnet Trading

```python
from nautilus_trader.adapters.hyperliquid import HyperliquidExecClientConfig

# Full testnet configuration
config = TradingNodeConfig(
    trader_id="TRADER-HL-TEST",
    data_clients={
        HYPERLIQUID: HyperliquidDataClientConfig(
            instrument_provider=InstrumentProviderConfig(load_all=True),
            testnet=True,
        ),
    },
    exec_clients={
        HYPERLIQUID: HyperliquidExecClientConfig(
            private_key=None,  # Loads from HYPERLIQUID_TESTNET_PK
            instrument_provider=InstrumentProviderConfig(load_all=True),
            testnet=True,
            max_retries=3,
            retry_delay_initial_ms=100,
            retry_delay_max_ms=5000,
        ),
    },
)
```

## Phase 3: Strategy with RiskManager

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.enums import OrderSide
from risk import RiskConfig, RiskManager  # From Spec 011

class HyperliquidStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str("BTC-USD-PERP.HYPERLIQUID")

        # Integrate RiskManager from Spec 011
        self.risk_manager = RiskManager(
            config=config.risk,
            strategy=self,
        )

    def on_start(self) -> None:
        # Subscribe to market data
        self.subscribe_quote_ticks(self.instrument_id)
        self.subscribe_trade_ticks(self.instrument_id)

    def on_quote_tick(self, tick) -> None:
        # Your trading logic here
        pass

    def on_event(self, event) -> None:
        # RiskManager handles position events
        self.risk_manager.handle_event(event)
```

## Order Submission Examples

```python
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.objects import Quantity, Price

# Market order
def submit_market_buy(self, size: float) -> None:
    order = self.order_factory.market(
        instrument_id=self.instrument_id,
        order_side=OrderSide.BUY,
        quantity=Quantity.from_str(str(size)),
    )
    self.submit_order(order)

# Limit order
def submit_limit_sell(self, size: float, price: float) -> None:
    order = self.order_factory.limit(
        instrument_id=self.instrument_id,
        order_side=OrderSide.SELL,
        quantity=Quantity.from_str(str(size)),
        price=Price.from_str(str(price)),
        time_in_force=TimeInForce.GTC,
        post_only=True,  # Maker only
    )
    self.submit_order(order)

# Stop-market order (for stop-loss)
def submit_stop_loss(self, size: float, trigger: float) -> None:
    order = self.order_factory.stop_market(
        instrument_id=self.instrument_id,
        order_side=OrderSide.SELL,
        quantity=Quantity.from_str(str(size)),
        trigger_price=Price.from_str(str(trigger)),
        reduce_only=True,  # Only close position
    )
    self.submit_order(order)
```

## Testnet Validation Checklist

- [ ] Environment variables set correctly
- [ ] Connect to Hyperliquid testnet
- [ ] Subscribe to BTC-USD-PERP data
- [ ] Verify QuoteTick/TradeTick received
- [ ] Submit test MARKET order
- [ ] Submit test LIMIT order
- [ ] Submit test STOP_MARKET order
- [ ] Verify fill events received
- [ ] Test order cancellation
- [ ] Test RiskManager stop-loss

## Common Issues & Solutions

### Private Key Not Found
```python
# Error: HYPERLIQUID_TESTNET_PK not set
# Solution: Set environment variable
export HYPERLIQUID_TESTNET_PK="0x..."
```

### Connection Timeout
```python
# Increase timeout for DEX
config = HyperliquidExecClientConfig(
    http_timeout_secs=15,  # Default is 10
    ...
)
```

### Order Rejected
```python
# Check:
# 1. Sufficient USDC balance
# 2. Order size meets minimum
# 3. Price within valid range
def on_order_rejected(self, event) -> None:
    self.log.error(f"Order rejected: {event.reason}")
```

## Security Reminders

1. **NEVER** commit private keys to git
2. Use **separate wallets** for testnet vs mainnet
3. Start with **small sizes** on mainnet
4. **Monitor** positions actively during initial deployment
5. Have a **kill switch** ready (close all positions)

## Next Steps

1. Complete testnet validation
2. Verify RiskManager integration (Spec 011)
3. Set up monitoring and alerts
4. Deploy to mainnet with minimal size
5. Scale up gradually based on performance
