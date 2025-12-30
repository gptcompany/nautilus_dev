# Quickstart: Position Recovery (Spec 017)

This guide shows how to configure position recovery for NautilusTrader live trading.

## Prerequisites

- Redis running (see Spec 018)
- TradingNode configured (see Spec 014)
- Order reconciliation enabled (see Spec 016)

## Basic Setup

### 1. Configure TradingNode for Recovery

```python
from nautilus_trader.config import (
    TradingNodeConfig,
    CacheConfig,
    DatabaseConfig,
    LiveExecEngineConfig,
)

config = TradingNodeConfig(
    trader_id="TRADER-001",

    # Redis cache - CRITICAL: flush_on_start=False
    cache=CacheConfig(
        database=DatabaseConfig(
            type="redis",
            host="localhost",
            port=6379,
        ),
        encoding="msgpack",
        flush_on_start=False,  # Preserve state across restarts
        buffer_interval_ms=100,
    ),

    # Execution engine with reconciliation
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,
        generate_missing_orders=True,
    ),
)
```

### 2. Implement Recovery-Aware Strategy

```python
from datetime import timedelta
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.enums import OrderType
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage


class RecoveryAwareStrategy(Strategy):
    """Strategy with position recovery support."""

    def __init__(self, config):
        super().__init__(config)
        self.ema = ExponentialMovingAverage(period=20)
        self._warmup_complete = False
        self._recovered_position = None

    def on_start(self) -> None:
        # Step 1: Check for recovered positions
        positions = self.cache.positions(instrument_id=self.instrument_id)
        for position in positions:
            if position.is_open:
                self.log.info(f"Recovered position: {position}")
                self._recovered_position = position
                self._setup_exit_orders(position)

        # Step 2: Request historical data for indicator warmup
        self.request_bars(
            bar_type=self.bar_type,
            start=self.clock.utc_now() - timedelta(days=2),
        )

    def on_historical_data(self, data) -> None:
        """Process historical bars for indicator warmup."""
        for bar in data.bars:
            self.ema.handle_bar(bar)

        self._warmup_complete = True
        self.log.info(f"Warmup complete: EMA value = {self.ema.value}")

    def on_bar(self, bar) -> None:
        # Don't trade until warmup complete
        if not self._warmup_complete:
            return

        self.ema.handle_bar(bar)
        # Your trading logic here...

    def _setup_exit_orders(self, position) -> None:
        """Recreate exit orders for recovered position."""
        # Check if stop-loss already exists
        open_orders = self.cache.orders_open(instrument_id=position.instrument_id)
        has_stop = any(o.type == OrderType.STOP_MARKET for o in open_orders)

        if not has_stop:
            self.log.info("Creating stop-loss for recovered position")
            # Create stop-loss order
            # self.create_stop_loss(position)
```

### 3. Configure Strategy with External Order Claims

```python
from nautilus_trader.config import StrategyConfig

strategy_config = StrategyConfig(
    strategy_id="RecoveryStrategy-001",
    # Claim positions for these instruments
    external_order_claims=[
        "BTCUSDT-PERP.BINANCE",
        "ETHUSDT-PERP.BINANCE",
    ],
)
```

## Testing Recovery

### Test 1: Cold Start (No Prior State)

```bash
# Clear Redis and start fresh
redis-cli FLUSHDB

# Start TradingNode
python run_trading_node.py
```

Expected: Node starts with no positions, ready to trade.

### Test 2: Warm Start (Existing Positions)

```bash
# Start with existing Redis state
python run_trading_node.py
```

Expected:
1. Reconciliation delay (10s)
2. Positions loaded from cache
3. Reconciled with exchange
4. Indicators warmed up
5. Trading resumes

### Test 3: Position Mismatch

Simulate by manually modifying Redis:

```bash
# Set incorrect position in Redis
redis-cli SET "nautilus:TRADER-001:positions:BINANCE:BTCUSDT-PERP" '{"quantity": "1.0"}'

# Start TradingNode
python run_trading_node.py
```

Expected:
1. Cache shows 1.0 BTC position
2. Exchange shows different (or no) position
3. Reconciliation generates synthetic orders
4. Logs show `EXTERNAL` and `RECONCILIATION` tags

## Monitoring Recovery

### Log Messages to Watch

```
INFO  - Reconciliation starting...
INFO  - Loaded 2 positions from cache
INFO  - Exchange reports 2 positions
INFO  - Position BTCUSDT-PERP.BINANCE: cache matches exchange
INFO  - Reconciliation complete in 1.234s
INFO  - Strategy warmup starting...
INFO  - Warmup complete: processed 2880 bars
INFO  - Strategy ready for trading
```

### Redis Keys to Monitor

```bash
# List all position keys
redis-cli KEYS "nautilus:TRADER-001:positions:*"

# Get specific position
redis-cli GET "nautilus:TRADER-001:positions:BINANCE:BTCUSDT-PERP"

# Monitor writes in real-time
redis-cli MONITOR
```

## Troubleshooting

### Issue: Duplicate Orders After Restart

**Cause**: `flush_on_start=True` or stale cache state

**Solution**:
```python
CacheConfig(
    flush_on_start=False,  # MUST be False
)
```

### Issue: Indicators Not Ready

**Cause**: Historical data request failed or insufficient lookback

**Solution**:
```python
def on_start(self) -> None:
    self.request_bars(
        bar_type=self.bar_type,
        start=self.clock.utc_now() - timedelta(days=2),  # Increase lookback
        callback=self._on_warmup_complete,  # Use callback
    )
```

### Issue: Position Reconciliation Fails

**Cause**: HEDGING mode or venue mismatch

**Solution**:
- Use one-way mode (not HEDGING) - Bug #3104
- Ensure instrument venue matches execution venue - Bug #3042

### Issue: External Positions Not Claimed

**Cause**: Missing `external_order_claims` config

**Solution**:
```python
StrategyConfig(
    external_order_claims=["BTCUSDT-PERP.BINANCE"],
)
```

## Next Steps

1. **Spec 016**: Configure continuous reconciliation
2. **Spec 018**: Set up Redis for production
3. **Monitoring**: Add Grafana dashboards for recovery metrics
