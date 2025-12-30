# Graceful Shutdown Guide

This guide explains how to configure graceful shutdown for NautilusTrader TradingNode to ensure orderly termination without losing state or leaving orphan orders.

## Overview

Graceful shutdown handles:
1. **SIGTERM/SIGINT signals** - Docker stop, Ctrl+C, kill commands
2. **Unhandled exceptions** - Strategy errors, fatal crashes
3. **Manual shutdown** - Programmatic shutdown requests

## Quick Start

```python
from nautilus_trader.live.node import TradingNode
from config.shutdown import GracefulShutdownHandler, ShutdownConfig

# Create node
node = TradingNode(config)

# Setup graceful shutdown
shutdown_handler = GracefulShutdownHandler(
    node=node,
    config=ShutdownConfig(timeout_secs=30.0),
)
shutdown_handler.setup_signal_handlers()

# Run with protection
try:
    node.run()
except Exception as e:
    shutdown_handler.handle_exception(e)
```

## Configuration

### ShutdownConfig Options

| Option | Default | Description |
|--------|---------|-------------|
| `timeout_secs` | 30.0 | Max time for shutdown (5-300s) |
| `cancel_orders` | True | Cancel all pending orders |
| `verify_stop_losses` | True | Warn if positions lack stop-losses |
| `flush_cache` | True | Ensure state persisted |
| `log_level` | "INFO" | Logging verbosity |

### Example Configuration

```python
from config.shutdown import ShutdownConfig

# Production config
config = ShutdownConfig(
    timeout_secs=60.0,      # More time for order cancellation
    cancel_orders=True,      # Always cancel
    verify_stop_losses=True, # Check protection
    flush_cache=True,        # Ensure persistence
    log_level="INFO",
)

# Debug config
debug_config = ShutdownConfig(
    timeout_secs=10.0,       # Faster for testing
    log_level="DEBUG",       # Verbose logging
)
```

## Shutdown Sequence

When shutdown is triggered, the following sequence executes:

```
1. Trading HALTED
   └── Prevents new orders during shutdown

2. Cancel Pending Orders
   └── Iterates all open orders
   └── Cancels pending orders
   └── Waits 2s for confirmations

3. Verify Stop-Losses
   └── Checks each open position
   └── Warns if no stop-loss order exists
   └── Does NOT block shutdown

4. Cache Flush
   └── Handled by NautilusTrader native
   └── State persisted to Redis

5. Close Connections
   └── Stops TradingNode
   └── Disconnects from exchanges

6. Exit
   └── Process terminates
```

## Integration Patterns

### With TradingNodeConfig

```python
from nautilus_trader.config import TradingNodeConfig, LiveExecEngineConfig
from config.cache import create_redis_cache_config
from config.shutdown import GracefulShutdownHandler, ShutdownConfig

config = TradingNodeConfig(
    trader_id="TRADER-001",
    cache=create_redis_cache_config(),
    exec_engine=LiveExecEngineConfig(
        graceful_shutdown_on_exception=True,  # Native support
    ),
)

node = TradingNode(config)
shutdown_handler = GracefulShutdownHandler(node, ShutdownConfig())
shutdown_handler.setup_signal_handlers()
```

### With Docker

```yaml
# docker-compose.yml
services:
  trading-node:
    image: your-trading-image
    stop_grace_period: 60s  # Must be >= shutdown timeout
    stop_signal: SIGTERM
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
```

When Docker sends `docker stop`, the container receives SIGTERM and has 60 seconds to complete graceful shutdown before SIGKILL.

### With Systemd

```ini
# /etc/systemd/system/trading-node.service
[Service]
ExecStart=/usr/bin/python /path/to/trading_node.py
ExecStop=/bin/kill -SIGTERM $MAINPID
TimeoutStopSec=60
KillMode=mixed
```

## Manual Testing

### Test SIGTERM Handling

```bash
# Terminal 1: Start trading node
python config/examples/trading_node_graceful.py

# Terminal 2: Send SIGTERM
kill -TERM $(pgrep -f trading_node_graceful)
```

### Test Script

```bash
python scripts/test_graceful_shutdown.py
```

Expected output:
```
=== Test: ShutdownConfig validation ===
✅ Valid config: timeout=30.0s
✅ Correctly rejected timeout=1.0
✅ Correctly rejected timeout=500
✅ Correctly rejected log_level='INVALID'

=== Test: Shutdown sequence ===
✅ is_shutdown_requested() returns False before shutdown
✅ is_shutdown_requested() returns True after shutdown
✅ Shutdown completed with exit code 0
✅ Cancelled 2 orders
✅ Found 2 unprotected positions
✅ TradingNode stopped

All tests passed! ✅
```

## Monitoring

### Logs to Watch

```bash
# Successful shutdown
INFO: Starting graceful shutdown (reason: SIGTERM, timeout: 30.0s)
INFO: Trading halted (TradingState.HALTED)
INFO: Found 5 open orders to cancel
INFO: Cancelled 5 orders
INFO: All 3 positions have stop-loss protection
INFO: Stopping TradingNode...
INFO: Shutdown complete in 4.23s (orders_cancelled=5, positions_unprotected=0)
INFO: Exiting with code 0

# Warning signs
WARNING: Position POS-001 (BTC/USDT) has no stop-loss order!
ERROR: Shutdown timed out after 30.0s, forcing exit
ERROR: Failed to cancel order ORDER-123: Connection lost
```

### Metrics (Future)

```python
# Prometheus metrics (planned)
shutdown_total = Counter("shutdown_total", ["reason"])
shutdown_duration_seconds = Histogram("shutdown_duration_seconds")
orders_cancelled_on_shutdown = Counter("orders_cancelled_on_shutdown")
```

## Troubleshooting

### Shutdown Times Out

**Symptoms**: `ERROR: Shutdown timed out after 30.0s, forcing exit`

**Causes**:
- Too many orders to cancel
- Slow exchange response
- Network issues

**Solutions**:
1. Increase `timeout_secs` (up to 300s)
2. Check exchange connectivity
3. Review order count before shutdown

### Orders Not Cancelled

**Symptoms**: Orders still open after restart

**Causes**:
- Shutdown interrupted (SIGKILL)
- Exchange API errors

**Solutions**:
1. Increase Docker `stop_grace_period`
2. Check exchange API status
3. Manual reconciliation on restart

### Positions Unprotected Warning

**Symptoms**: `WARNING: Position has no stop-loss order!`

**Action**: This is informational only. Consider:
1. Adding stop-loss orders in strategy
2. Using Spec 011 (Stop-Loss Position Limits)

## Dependencies

- **Spec 018**: Redis Cache Backend (state persistence)
- **Spec 011**: Stop-Loss Position Limits (position protection)
- **NautilusTrader >= 1.220.0**: TradingState, LiveExecEngineConfig

## API Reference

### GracefulShutdownHandler

```python
class GracefulShutdownHandler:
    def __init__(self, node: TradingNode, config: ShutdownConfig | None = None) -> None
    def setup_signal_handlers(self) -> None
    async def shutdown(self, reason: str = "signal") -> None
    def is_shutdown_requested(self) -> bool
    def handle_exception(self, exc: Exception) -> None
```

### ShutdownConfig

```python
@dataclass
class ShutdownConfig:
    timeout_secs: float = 30.0
    cancel_orders: bool = True
    verify_stop_losses: bool = True
    flush_cache: bool = True
    log_level: str = "INFO"
```

### ShutdownReason

```python
class ShutdownReason(Enum):
    SIGNAL_SIGTERM = "SIGTERM"
    SIGNAL_SIGINT = "SIGINT"
    EXCEPTION = "exception"
    MANUAL = "manual"
    TIMEOUT = "timeout"
```
