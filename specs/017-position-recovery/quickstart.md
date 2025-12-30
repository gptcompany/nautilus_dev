# Quickstart: Position Recovery (Spec 017)

**Estimated Setup Time**: 10 minutes

---

## Prerequisites

1. **NautilusTrader Nightly** (v1.222.0+)
2. **Redis** running locally (default port 6379)
3. **Python 3.11+**

## Quick Setup

### 1. Start Redis

```bash
# Using Docker (recommended)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Or using system Redis
sudo systemctl start redis
```

### 2. Configure TradingNode

```python
from nautilus_trader.config import (
    TradingNodeConfig,
    CacheConfig,
    LiveExecEngineConfig,
)
from nautilus_trader.common.config import DatabaseConfig

config = TradingNodeConfig(
    trader_id="TRADER-001",
    cache=CacheConfig(
        database=DatabaseConfig(
            type="redis",
            host="localhost",
            port=6379,
        ),
        persist_account_events=True,  # CRITICAL!
        flush_on_start=False,         # Preserve state
    ),
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,
        generate_missing_orders=True,
    ),
)
```

### 3. Create Recoverable Strategy

```python
from datetime import timedelta
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import Bar
from nautilus_trader.model.events import OrderFilled

class RecoverableStrategy(Strategy):
    """Strategy with position recovery support."""

    def __init__(self, config):
        super().__init__(config)
        self._is_warmed_up = False
        self._warmup_bars = 500

    def on_start(self):
        # 1. Check for existing positions
        positions = self.cache.positions_open(strategy_id=self.id)
        if positions:
            self._log.info(f"Recovering {len(positions)} positions")
            for position in positions:
                self._restore_position(position)
        
        # 2. Request historical data for indicator warmup
        self.request_bars(
            bar_type=self.bar_type,
            start=self.clock.utc_now() - timedelta(days=2),
            callback=self._on_warmup_complete,
        )

    def _restore_position(self, position):
        """Handle a recovered position."""
        self._log.info(f"Recovered: {position}")
        
        # Check if stop-loss exists
        open_orders = self.cache.orders_open(instrument_id=position.instrument_id)
        has_stop = any(o.type.name == "STOP_MARKET" for o in open_orders)
        
        if not has_stop and position.is_open:
            # Recreate stop-loss
            self._create_stop_loss(position)

    def _create_stop_loss(self, position):
        """Create stop-loss for position."""
        # Your stop-loss logic here
        pass

    def on_historical_data(self, data):
        """Warm up indicators with historical bars."""
        for bar in data.bars:
            # Update your indicators
            self.indicator.handle_bar(bar)

    def _on_warmup_complete(self, data):
        """Called when warmup finishes."""
        self._is_warmed_up = True
        self._log.info("Indicator warmup complete - ready to trade")

    def on_bar(self, bar: Bar):
        # Wait for warmup
        if not self._is_warmed_up:
            return
        
        # Normal trading logic
        ...
```

## Testing Recovery

### Simulate Restart

```python
# In backtest or sandbox:

# 1. Run strategy, open position
node.run()
# ... position opened ...

# 2. Stop node (simulates crash)
node.stop()

# 3. Restart node
node = TradingNode(config=config)
node.add_strategies([RecoverableStrategy(strategy_config)])
node.run()

# Strategy should recover position and resume trading
```

### Verify Recovery

```python
# In strategy on_start():
def on_start(self):
    positions = self.cache.positions_open(strategy_id=self.id)
    self._log.info(f"Found {len(positions)} positions on startup")
    
    orders = self.cache.orders_open(strategy_id=self.id)
    self._log.info(f"Found {len(orders)} open orders on startup")
```

## Common Issues

### Issue: Positions not recovered

**Cause**: `persist_account_events=False` in CacheConfig

**Fix**:
```python
cache=CacheConfig(
    database=DatabaseConfig(...),
    persist_account_events=True,  # Must be True!
)
```

### Issue: Duplicate orders after recovery

**Cause**: `flush_on_start=True` clearing cache

**Fix**:
```python
cache=CacheConfig(
    ...
    flush_on_start=False,  # Preserve state
)
```

### Issue: Position mismatch with exchange

**Cause**: Reconciliation disabled or insufficient delay

**Fix**:
```python
exec_engine=LiveExecEngineConfig(
    reconciliation=True,
    reconciliation_startup_delay_secs=10.0,  # Minimum 10s
    generate_missing_orders=True,
)
```

### Issue: Indicators producing bad signals after restart

**Cause**: Missing warmup

**Fix**: Always request historical data in `on_start()`:
```python
def on_start(self):
    self.request_bars(
        bar_type=self.bar_type,
        start=self.clock.utc_now() - timedelta(days=2),
        callback=self._on_warmup_complete,
    )
```

## Next Steps

1. **Read Full Spec**: `specs/017-position-recovery/spec.md`
2. **Review Data Model**: `specs/017-position-recovery/data-model.md`
3. **Check Research**: `specs/017-position-recovery/research.md`
