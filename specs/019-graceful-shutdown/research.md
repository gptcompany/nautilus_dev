# Research: Graceful Shutdown

## NautilusTrader Native Support

### LiveExecEngineConfig

NautilusTrader already provides graceful shutdown configuration:

```python
from nautilus_trader.config import LiveExecEngineConfig

config = LiveExecEngineConfig(
    graceful_shutdown_on_exception=True,  # Trigger shutdown on unhandled exceptions
)
```

**Decision**: Leverage existing `graceful_shutdown_on_exception` flag.
**Rationale**: Native support, no reinvention.
**Alternatives**: Custom exception handler - rejected (duplicates functionality).

### TradingState

NautilusTrader has built-in trading state:

```python
from nautilus_trader.trading.trader import TradingState

# States: RUNNING, PAUSED, HALTED
node.trader.trading_state = TradingState.HALTED
```

**Decision**: Use `TradingState.HALTED` to stop new orders.
**Rationale**: Native state management, strategies respect this.
**Alternatives**: Custom flag - rejected (strategies wouldn't check it).

### Order Cancellation

NautilusTrader provides order cancellation:

```python
# Get all open orders
open_orders = node.cache.orders_open()

# Cancel each order
for order in open_orders:
    if order.is_pending:
        node.cancel_order(order)
```

**Decision**: Use `cache.orders_open()` and `cancel_order()`.
**Rationale**: Native methods, handles all order types.
**Alternatives**: Manual exchange API calls - rejected (bypasses NautilusTrader).

## Signal Handling

### Python asyncio Signal Handlers

```python
import asyncio
import signal

def setup_signal_handlers(handler):
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(handler(s)))
```

**Decision**: Use `loop.add_signal_handler()`.
**Rationale**: Works with TradingNode's event loop.
**Alternatives**: `signal.signal()` - rejected (not async-safe).

### Docker Signal Forwarding

Docker stop sends SIGTERM, then SIGKILL after grace period:

```yaml
services:
  trading-node:
    stop_grace_period: 60s  # Wait 60s before SIGKILL
    stop_signal: SIGTERM    # Default, explicit for clarity
```

**Decision**: Configure `stop_grace_period` >= shutdown timeout.
**Rationale**: Allows graceful shutdown to complete.
**Alternatives**: SIGQUIT - rejected (non-standard).

## Timeout Implementation

### asyncio.wait_for

```python
import asyncio

async def shutdown_with_timeout(handler, timeout_secs):
    try:
        await asyncio.wait_for(handler.shutdown(), timeout=timeout_secs)
    except asyncio.TimeoutError:
        logging.error(f"Shutdown timed out after {timeout_secs}s, force exiting")
        sys.exit(1)
```

**Decision**: Use `asyncio.wait_for` with configurable timeout.
**Rationale**: Simple, no threading, respects async model.
**Alternatives**: Threading.Timer - rejected (adds complexity).

## Cache Flush

### Redis Persistence

From Spec 018, Redis is configured with AOF persistence:

```yaml
# docker-compose.redis.yml
command: redis-server --appendonly yes
```

NautilusTrader auto-persists to Redis when configured. Explicit flush not needed if cache is properly configured.

**Decision**: Rely on NautilusTrader's cache persistence.
**Rationale**: Native behavior, no custom flush needed.
**Alternatives**: Manual Redis SAVE - rejected (cache handles this).

## Position Protection

### Stop-Loss Verification

Check if positions have stop-loss orders:

```python
for position in node.cache.positions_open():
    stops = [o for o in node.cache.orders_open()
             if o.instrument_id == position.instrument_id
             and o.type == OrderType.STOP_MARKET]
    if not stops:
        logging.warning(f"Position {position.id} has no stop-loss!")
```

**Decision**: Log warnings for unprotected positions, don't block shutdown.
**Rationale**: Informational, don't delay shutdown.
**Alternatives**: Block shutdown - rejected (could leave system hanging).

## Summary

| Topic | Decision | Native Support |
|-------|----------|----------------|
| Exception handling | `graceful_shutdown_on_exception=True` | ✅ |
| Trading halt | `TradingState.HALTED` | ✅ |
| Order cancellation | `cache.orders_open()` + `cancel_order()` | ✅ |
| Signal handling | `loop.add_signal_handler()` | Python stdlib |
| Timeout | `asyncio.wait_for()` | Python stdlib |
| Cache persistence | NautilusTrader native | ✅ |
| Stop-loss check | `cache.orders_open()` filter | ✅ |

**Conclusion**: Heavy reliance on NautilusTrader native features. Custom code minimal.
