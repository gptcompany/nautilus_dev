# Position Recovery Guide (Spec 018)

## Overview

This guide explains how NautilusTrader recovers trading state after a TradingNode restart using Redis cache.

## Recovery Flow

```
TradingNode Start
      │
      ▼
┌─────────────────┐
│ Load from Redis │ ← Positions, orders, accounts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Reconcile with  │ ← Compare with exchange
│ Exchange        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Strategy        │ ← on_start() warmup
│ Initialization  │
└────────┬────────┘
         │
         ▼
    Ready to Trade
```

## Configuration Requirements

### 1. Enable Persistence

```python
CacheConfig(
    persist_account_events=True,  # CRITICAL
    flush_on_start=False,         # Preserve state
)
```

### 2. Enable Reconciliation

```python
LiveExecEngineConfig(
    reconciliation=True,
    reconciliation_startup_delay_secs=10.0,  # Minimum
)
```

### 3. Full Example

```python
from config.cache import create_redis_cache_config

config = TradingNodeConfig(
    trader_id="TRADER-001",
    cache=create_redis_cache_config(),
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,
        generate_missing_orders=True,
    ),
)
```

## Strategy Recovery Pattern

```python
class MyStrategy(Strategy):
    def on_start(self):
        # 1. Check for existing positions
        positions = self.cache.positions_open(strategy_id=self.id)
        if positions:
            self._log.info(f"Recovered {len(positions)} positions")
            for pos in positions:
                self._restore_position(pos)

        # 2. Warmup indicators
        self.request_bars(
            bar_type=self.bar_type,
            start=self.clock.utc_now() - timedelta(days=2),
            callback=self._warmup_complete,
        )

    def _restore_position(self, position):
        # Recreate stop-loss if needed
        orders = self.cache.orders_open(instrument_id=position.instrument_id)
        has_stop = any(o.type.name == "STOP_MARKET" for o in orders)
        if not has_stop:
            self._create_stop_loss(position)
```

## Testing Recovery

### 1. Start Redis

```bash
cd config/cache
docker-compose -f docker-compose.redis.yml up -d
```

### 2. Run Recovery Test

```bash
python scripts/test_recovery.py
```

### 3. Manual Test

```bash
# 1. Start TradingNode, open position
# 2. Kill TradingNode (Ctrl+C or kill -9)
# 3. Restart TradingNode
# 4. Verify position recovered in logs
```

## Troubleshooting

### Positions Not Recovered

1. Check `persist_account_events=True`
2. Check `flush_on_start=False`
3. Verify Redis has data: `redis-cli keys "trader-position:*"`

### Duplicate Orders After Restart

1. Ensure `reconciliation=True`
2. Increase `reconciliation_startup_delay_secs` to 15+
3. Check for `RECONCILIATION` tagged orders in logs

### Indicators Garbage After Restart

1. Always warmup in `on_start()`
2. Request sufficient historical data (2+ days)
3. Wait for warmup callback before trading

## Redis Inspection

```bash
# Check stored positions
redis-cli keys "trader-position:*"

# Check stored orders
redis-cli keys "trader-order:*"

# Monitor real-time
redis-cli monitor | grep "trader-"

# Memory usage
redis-cli info memory
```
