# Spec 019: Graceful Shutdown

## Overview

Implement graceful shutdown procedures to safely stop TradingNode without losing state or leaving orphan orders.

## Problem Statement

Abrupt shutdown (kill -9, crash, power loss) can leave orders in flight, positions unprotected, and state inconsistent. Need orderly shutdown that preserves system integrity.

## Goals

1. **Order Cancellation**: Cancel all pending orders before shutdown
2. **State Persistence**: Flush all state to Redis before exit
3. **Position Protection**: Ensure stop-losses are active before shutdown

## Requirements

### Functional Requirements

#### FR-001: Shutdown Signal Handling
- Handle SIGTERM, SIGINT gracefully
- Configurable shutdown timeout (default: 30s)
- Force exit after timeout

#### FR-002: Shutdown Sequence
```
1. Stop accepting new orders (trading halted)
2. Cancel all pending orders
3. Verify stop-losses active for all positions
4. Flush cache to Redis
5. Close exchange connections
6. Exit
```

#### FR-003: Configuration
```python
LiveExecEngineConfig(
    graceful_shutdown_on_exception=True,
    shutdown_timeout_secs=30.0,
    cancel_orders_on_shutdown=True,
)
```

#### FR-004: Exception Handling
- Catch unhandled exceptions in strategies
- Trigger graceful shutdown on fatal errors
- Log exception details before shutdown

#### FR-005: Partial Shutdown
- Option to stop specific strategies without full shutdown
- Remove strategy while keeping positions protected

### Non-Functional Requirements

#### NFR-001: Reliability
- 100% of orders cancelled on shutdown
- Zero orphan orders after restart

#### NFR-002: Timing
- Shutdown complete within timeout
- All critical state persisted

## Technical Design

### Shutdown Handler

```python
class GracefulShutdownHandler:
    """Handles graceful shutdown of TradingNode."""

    def __init__(self, node: TradingNode, config: ShutdownConfig):
        self.node = node
        self.config = config
        self._shutdown_requested = False

    def setup_signal_handlers(self) -> None:
        """Register signal handlers."""
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:
        """Handle shutdown signal."""
        self.node.log.warning(f"Received signal {signum}, initiating shutdown")
        self._shutdown_requested = True
        asyncio.create_task(self.shutdown())

    async def shutdown(self) -> None:
        """Execute graceful shutdown sequence."""
        try:
            # 1. Halt trading
            self.node.trader.trading_state = TradingState.HALTED

            # 2. Cancel pending orders
            await self._cancel_all_orders()

            # 3. Verify stop-losses
            await self._verify_stop_losses()

            # 4. Flush cache
            await self._flush_cache()

            # 5. Close connections
            await self._close_connections()

        except Exception as e:
            self.node.log.error(f"Shutdown error: {e}")
        finally:
            self.node.log.info("Shutdown complete")
            sys.exit(0)

    async def _cancel_all_orders(self) -> None:
        """Cancel all open orders."""
        open_orders = self.node.cache.orders_open()
        for order in open_orders:
            if order.is_pending:
                self.node.cancel_order(order)

        # Wait for cancellations
        await asyncio.sleep(2.0)

    async def _verify_stop_losses(self) -> None:
        """Ensure all positions have stop-losses."""
        for position in self.node.cache.positions_open():
            # Check for existing stop-loss
            stops = [o for o in self.node.cache.orders_open()
                     if o.instrument_id == position.instrument_id
                     and o.type == OrderType.STOP_MARKET]
            if not stops:
                self.node.log.warning(
                    f"Position {position.id} has no stop-loss!"
                )
```

### Integration with TradingNode

```python
def main():
    config = TradingNodeConfig(...)
    node = TradingNode(config)

    shutdown_handler = GracefulShutdownHandler(node, ShutdownConfig())
    shutdown_handler.setup_signal_handlers()

    try:
        node.run()
    except Exception as e:
        logging.exception(f"Fatal error: {e}")
        asyncio.run(shutdown_handler.shutdown())
```

### Docker Stop Handling

```yaml
services:
  trading-node:
    # ...
    stop_grace_period: 60s  # Allow time for graceful shutdown
    stop_signal: SIGTERM
```

## Monitoring Integration

### Metrics
```python
shutdown_total = Counter("shutdown_total", ["reason"])
shutdown_duration_seconds = Histogram("shutdown_duration_seconds")
orders_cancelled_on_shutdown = Counter("orders_cancelled_on_shutdown")
```

### Alerts
- Alert on ungraceful shutdown (no proper sequence)
- Alert if shutdown takes > timeout

## Testing Strategy

1. **Signal Tests**: SIGTERM/SIGINT handling
2. **Order Cancellation**: All pending orders cancelled
3. **Timeout Tests**: Force exit after timeout
4. **State Tests**: State properly persisted

## Dependencies

- Spec 018 (Redis Cache Backend)
- Spec 011 (Stop-Loss for position protection)

## Success Metrics

- 100% of shutdowns graceful
- All orders cancelled within 10s
- State fully persisted before exit
