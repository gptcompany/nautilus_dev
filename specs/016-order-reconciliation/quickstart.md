# Quickstart: Order Reconciliation

**Spec**: 016-order-reconciliation
**Prerequisites**: NautilusTrader >= 1.222.0, Redis running

## 1. Basic Setup (5 minutes)

### Minimal Configuration

```python
from nautilus_trader.config import (
    TradingNodeConfig,
    LiveExecEngineConfig,
    CacheConfig,
    DatabaseConfig,
)

config = TradingNodeConfig(
    trader_id="TRADER-001",
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,
    ),
    cache=CacheConfig(
        database=DatabaseConfig(host="localhost", port=6379),
        persist_account_events=True,  # CRITICAL for recovery
    ),
)
```

### Production Configuration

```python
config = TradingNodeConfig(
    trader_id="TRADER-001",
    exec_engine=LiveExecEngineConfig(
        # Startup Reconciliation
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,
        reconciliation_lookback_mins=None,  # Max history

        # In-Flight Monitoring
        inflight_check_interval_ms=2000,
        inflight_check_threshold_ms=5000,
        inflight_check_retries=5,

        # Continuous Polling
        open_check_interval_secs=5.0,
        open_check_lookback_mins=60,
        open_check_threshold_ms=5000,

        # Memory Management
        purge_closed_orders_interval_mins=10,
        purge_closed_orders_buffer_mins=60,

        # Safety
        graceful_shutdown_on_exception=True,
    ),
    cache=CacheConfig(
        database=DatabaseConfig(host="localhost", port=6379),
        persist_account_events=True,
    ),
)
```

## 2. External Order Claims

To claim orders placed via exchange web/app:

```python
from nautilus_trader.config import StrategyConfig

class MyStrategyConfig(StrategyConfig):
    instrument_ids: list[str]

    @property
    def external_order_claims(self) -> list[str]:
        return self.instrument_ids

# Usage
config = MyStrategyConfig(
    instrument_ids=[
        "BTCUSDT-PERP.BINANCE",
        "ETHUSDT-PERP.BINANCE",
    ],
)
```

## 3. Verify Redis is Running

```bash
# Check Redis status
redis-cli ping  # Should return PONG

# Start Redis if needed
sudo systemctl start redis
```

## 4. Monitor Reconciliation

Check logs for reconciliation status:

```
INFO  Reconciliation starting...
INFO  Querying venue for open orders
INFO  Querying venue for recent fills
INFO  Querying venue for positions
INFO  Reconciliation complete - 0 discrepancies found
```

## 5. Common Issues

### Issue: Reconciliation takes too long
**Solution**: Reduce `reconciliation_lookback_mins` (but never below actual position age)

### Issue: HEDGING mode fails
**Solution**: Use NETTING mode only (Bug #3104)

### Issue: External positions not detected
**Solution**: Ensure `external_order_claims` includes the instrument IDs

## 6. Quick Validation Test

```python
import asyncio
from nautilus_trader.live.node import TradingNode

async def test_reconciliation():
    node = TradingNode(config=config)
    node.add_data_client_factory(...)
    node.add_exec_client_factory(...)

    await node.start()
    # Wait for reconciliation
    await asyncio.sleep(15)

    # Check reconciliation status in logs
    # Look for "Reconciliation complete"

    await node.stop()

asyncio.run(test_reconciliation())
```

## Next Steps

- [ ] Read `research.md` for detailed findings
- [ ] Review `data-model.md` for entity definitions
- [ ] Check `plan.md` for full implementation phases
