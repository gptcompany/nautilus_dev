# Quickstart: TradingNode Configuration

**Feature**: 014-tradingnode-configuration
**Date**: 2025-12-28

## Prerequisites

1. **NautilusTrader Nightly** (v1.222.0+)
   ```bash
   source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
   ```

2. **Redis** running
   ```bash
   docker run -d --name redis -p 6379:6379 redis:7
   ```

3. **Exchange API Keys** configured

---

## Quick Setup

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env`:

```bash
# Core
NAUTILUS_TRADER_ID=PROD-TRADER-001
NAUTILUS_ENVIRONMENT=SANDBOX  # or LIVE

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Binance (at least one exchange required)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET=true  # Set to false for production

# Bybit (optional)
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
BYBIT_TESTNET=true
```

### 3. Create Your Strategy

```python
# my_strategy.py
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.trading.config import StrategyConfig
from nautilus_trader.model.enums import OmsType


class MyStrategyConfig(StrategyConfig):
    strategy_id: str = "MY-STRATEGY-001"
    order_id_tag: str = "MYS"
    oms_type: OmsType = OmsType.NETTING  # Required for Bybit


class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig):
        super().__init__(config)

    def on_start(self):
        self.log.info("Strategy started!")

    def on_stop(self):
        self.log.info("Strategy stopped!")
```

### 4. Run with TradingNode

```python
# run.py
from dotenv import load_dotenv
from nautilus_trader.live.node import TradingNode

from config.factory import TradingNodeConfigFactory
from my_strategy import MyStrategy, MyStrategyConfig

# Load environment
load_dotenv()

# Create config
config = TradingNodeConfigFactory.create_testnet(
    strategies=[MyStrategyConfig()],
)

# Create and run node
node = TradingNode(config=config)
node.trader.add_strategy(MyStrategy(MyStrategyConfig()))
node.build()

try:
    node.run()
except KeyboardInterrupt:
    pass
finally:
    try:
        node.stop()
    finally:
        node.dispose()
```

### 5. Run

```bash
python run.py
```

---

## Production Deployment

### Docker Compose

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  trading-node:
    build: .
    env_file:
      - .env.production
    volumes:
      - ./logs:/var/log/nautilus
      - ./data:/data/nautilus/catalog
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  redis_data:
```

### Production Checklist

- [ ] API keys configured (not testnet)
- [ ] Redis running and accessible
- [ ] Log directory exists and writable
- [ ] Catalog directory exists and writable
- [ ] Network connectivity to exchanges verified
- [ ] Testnet validation completed

---

## Common Patterns

### Switch Between Testnet and Production

```python
# Testnet
config = TradingNodeConfigFactory.create_testnet(strategies=[...])

# Production
config = TradingNodeConfigFactory.create_production(strategies=[...])
```

### Custom Settings

```python
from config.config_models import (
    TradingNodeSettings,
    ConfigEnvironment,
    BinanceCredentials,
)

settings = TradingNodeSettings(
    environment=ConfigEnvironment(
        trader_id="CUSTOM-001",
        environment="SANDBOX",
    ),
    binance=BinanceCredentials(
        api_key="...",
        api_secret="...",
        testnet=True,
    ),
    reconciliation_lookback_mins=120,  # Custom lookback
)

config = TradingNodeConfigFactory.from_settings(settings, strategies=[...])
```

### Claiming External Positions on Restart

```python
class MyStrategyConfig(StrategyConfig):
    strategy_id: str = "MY-STRATEGY-001"
    oms_type: OmsType = OmsType.NETTING
    external_order_claims: list = ["BTCUSDT-PERP.BINANCE"]  # Claim these
```

---

## Troubleshooting

### Redis Connection Failed

```bash
# Check Redis is running
redis-cli ping

# Check port
netstat -tlnp | grep 6379
```

### Reconciliation Timeout

Increase startup delay:
```bash
NAUTILUS_RECONCILIATION_STARTUP_DELAY_SECS=15.0
```

### Rate Limit Exceeded

Reduce order rate in environment:
```bash
NAUTILUS_MAX_ORDER_SUBMIT_RATE="50/00:00:01"
```

---

## Next Steps

1. Read `research.md` for detailed configuration options
2. Review `data-model.md` for validation rules
3. Check `plan.md` for implementation phases
