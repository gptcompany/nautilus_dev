# Hyperliquid Configuration (Spec 021)

This directory contains configuration factories for Hyperliquid integration with NautilusTrader.

## Quick Start

### 1. Set Environment Variables

```bash
# Testnet (for development/testing)
export HYPERLIQUID_TESTNET_PK="0x_your_testnet_private_key"

# Mainnet (for production - KEEP SECURE!)
export HYPERLIQUID_MAINNET_PK="0x_your_mainnet_private_key"
```

### 2. Data Streaming Only

```python
from configs.hyperliquid import create_data_only_trading_node
from nautilus_trader.live.node import TradingNode

config = create_data_only_trading_node(testnet=False)
node = TradingNode(config=config)
node.run()
```

### 3. Testnet Trading

```python
from configs.hyperliquid.testnet import create_testnet_trading_node
from nautilus_trader.live.node import TradingNode

config = create_testnet_trading_node()
node = TradingNode(config=config)
node.trader.add_strategy(my_strategy)
node.run()
```

### 4. Production Trading

```python
from configs.hyperliquid.trading_node import create_hyperliquid_trading_node
from nautilus_trader.live.node import TradingNode

config = create_hyperliquid_trading_node(
    trader_id="TRADER-PROD-001",
    testnet=False,
    redis_enabled=True,
)
node = TradingNode(config=config)
node.trader.add_strategy(my_strategy)
node.run()
```

## Configuration Files

| File | Purpose |
|------|---------|
| `data_client.py` | Data-only configuration (no execution) |
| `exec_client.py` | Execution client configuration |
| `testnet.py` | Testnet configuration (data + exec) |
| `persistence.py` | Data recording to ParquetDataCatalog |
| `trading_node.py` | Full production configuration |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HYPERLIQUID_TESTNET_PK` | For testnet | Private key for testnet trading |
| `HYPERLIQUID_MAINNET_PK` | For mainnet | Private key for mainnet trading |
| `HYPERLIQUID_TESTNET_VAULT` | Optional | Vault address for delegated testnet trading |
| `HYPERLIQUID_MAINNET_VAULT` | Optional | Vault address for delegated mainnet trading |

## Security Reminders

1. **NEVER** commit private keys to git
2. Use **separate wallets** for testnet vs mainnet
3. Start with **small sizes** on mainnet
4. **Monitor** positions actively during initial deployment
5. Have a **kill switch** ready (close all positions)

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
