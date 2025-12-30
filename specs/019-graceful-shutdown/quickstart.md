# Quickstart: Graceful Shutdown

## Prerequisites

- Spec 018 (Redis Cache Backend) completed
- NautilusTrader nightly installed

## Quick Setup

### 1. Import Handler

```python
from config.shutdown import GracefulShutdownHandler, ShutdownConfig
```

### 2. Configure TradingNode

```python
from nautilus_trader.config import TradingNodeConfig, LiveExecEngineConfig
from config.cache import create_redis_cache_config

config = TradingNodeConfig(
    trader_id="TRADER-001",
    cache=create_redis_cache_config(),
    exec_engine=LiveExecEngineConfig(
        graceful_shutdown_on_exception=True,  # Native support
    ),
)
```

### 3. Add Shutdown Handler

```python
from nautilus_trader.live.node import TradingNode

node = TradingNode(config)

# Setup graceful shutdown
shutdown_handler = GracefulShutdownHandler(
    node=node,
    config=ShutdownConfig(
        timeout_secs=30.0,
        cancel_orders=True,
        verify_stop_losses=True,
    ),
)
shutdown_handler.setup_signal_handlers()
```

### 4. Run with Protection

```python
try:
    node.run()
except Exception as e:
    logging.exception(f"Fatal error: {e}")
    asyncio.run(shutdown_handler.shutdown(reason="exception"))
```

## Docker Configuration

```yaml
# docker-compose.yml
services:
  trading-node:
    image: your-trading-image
    stop_grace_period: 60s  # Allow graceful shutdown
    stop_signal: SIGTERM
```

## Test Shutdown

```bash
# Start trading node
python run_trading_node.py &

# Send SIGTERM
kill -TERM $(pgrep -f run_trading_node)

# Check logs for graceful shutdown sequence
```

## What Happens on Shutdown

1. **Signal received** (SIGTERM/SIGINT)
2. **Trading halted** - no new orders accepted
3. **Orders cancelled** - all pending orders
4. **Stop-losses verified** - warnings for unprotected positions
5. **Cache flushed** - state persisted to Redis
6. **Exit** - clean process termination

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `timeout_secs` | 30.0 | Max shutdown time |
| `cancel_orders` | True | Cancel pending orders |
| `verify_stop_losses` | True | Check position protection |
| `flush_cache` | True | Persist state to Redis |
| `log_level` | "INFO" | Shutdown logging |
