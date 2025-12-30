# Quickstart: Redis Cache Backend (Spec 018)

## 1. Start Redis

```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine redis-server --appendonly yes
```

## 2. Configure TradingNode

```python
from nautilus_trader.config import TradingNodeConfig, CacheConfig
from nautilus_trader.common.config import DatabaseConfig

config = TradingNodeConfig(
    trader_id="TRADER-001",
    cache=CacheConfig(
        database=DatabaseConfig(
            type="redis",
            host="localhost",
            port=6379,
        ),
        persist_account_events=True,
        flush_on_start=False,
    ),
)
```

## 3. Verify Connection

```bash
redis-cli ping
# PONG

redis-cli keys "trader-*"
# (empty if no trading yet)
```

## 4. Monitor

```bash
redis-cli monitor
# Watch all commands in real-time
```
