# Quickstart: Position Recovery (Spec 017)

This guide demonstrates how to implement position recovery for NautilusTrader live trading using the recovery module.

## Prerequisites

- NautilusTrader nightly (v1.220.0+)
- Redis running (see Spec 018)
- TradingNode configured (see Spec 014)
- Order reconciliation enabled (see Spec 016)

## Installation

The recovery module is located in `strategies/common/recovery/`. Import as follows:

```python
from strategies.common.recovery import (
    RecoveryConfig,
    RecoverableStrategy,
    RecoverableStrategyConfig,
    RecoveryState,
    RecoveryStatus,
)
```

---

## Quick Setup

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

### 2. Create Recovery Configuration

```python
from strategies.common.recovery import RecoveryConfig

recovery_config = RecoveryConfig(
    trader_id="TRADER-001",
    recovery_enabled=True,
    warmup_lookback_days=2,           # Historical data for indicator warmup
    startup_delay_secs=10.0,          # Wait for reconciliation (min 5s)
    max_recovery_time_secs=30.0,      # Timeout for full recovery
    claim_external_positions=True,    # Claim positions from external sources
)
```

---

## RecoverableStrategy Usage

### Basic Example

```python
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.model.data import Bar
from nautilus_trader.model.position import Position

from strategies.common.recovery import (
    RecoverableStrategy,
    RecoverableStrategyConfig,
    RecoveryConfig,
)


class MyRecoverableStrategy(RecoverableStrategy):
    """Strategy with automatic position recovery support."""

    def __init__(self, config: RecoverableStrategyConfig) -> None:
        super().__init__(config)
        # Initialize indicators (will be warmed up automatically)
        self.ema_fast = ExponentialMovingAverage(period=12)
        self.ema_slow = ExponentialMovingAverage(period=26)

    def on_historical_data(self, bar: Bar) -> None:
        """Feed historical bars to indicators for warmup.
        
        This method is called for each historical bar during warmup.
        Override to warm up your specific indicators.
        """
        self.ema_fast.handle_bar(bar)
        self.ema_slow.handle_bar(bar)

    def on_position_recovered(self, position: Position) -> None:
        """Handle a recovered position.
        
        Called once for each open position found in cache at startup.
        Override to restore strategy-specific state.
        """
        self.log.info(
            f"Recovered: {position.instrument_id} "
            f"{position.side.value} {position.quantity} @ {position.avg_px_open}"
        )
        # Example: Restore internal tracking state
        self._has_position = True
        self._entry_price = float(position.avg_px_open)

    def on_warmup_complete(self) -> None:
        """Called when indicator warmup finishes.
        
        Strategy is now ready to trade.
        """
        self.log.info(
            f"Warmup complete: EMA fast={self.ema_fast.value:.2f}, "
            f"slow={self.ema_slow.value:.2f}"
        )

    def on_bar(self, bar: Bar) -> None:
        """Handle live bars - main trading logic."""
        # IMPORTANT: Skip until warmup completes
        if not self._warmup_complete:
            return

        # Update indicators
        self.ema_fast.handle_bar(bar)
        self.ema_slow.handle_bar(bar)

        # Your trading logic here...
        if self.ema_fast.value > self.ema_slow.value:
            # Entry signal
            pass


# Create strategy configuration
strategy_config = RecoverableStrategyConfig(
    strategy_id="EMA-CROSS-001",
    instrument_id="BTCUSDT-PERP.BINANCE",
    bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
    recovery=RecoveryConfig(
        trader_id="TRADER-001",
        warmup_lookback_days=2,
    ),
    # Claim positions for these instruments
    external_order_claims=["BTCUSDT-PERP.BINANCE"],
)

# Instantiate strategy
strategy = MyRecoverableStrategy(config=strategy_config)
```

---

## Configuration Options

### RecoveryConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trader_id` | str | required | Unique trader identifier |
| `recovery_enabled` | bool | `True` | Enable position recovery |
| `warmup_lookback_days` | int | `2` | Days of historical data (1-30) |
| `startup_delay_secs` | float | `10.0` | Reconciliation delay (5-60s) |
| `max_recovery_time_secs` | float | `30.0` | Recovery timeout (10-120s) |
| `claim_external_positions` | bool | `True` | Claim external positions |

### RecoverableStrategyConfig Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `strategy_id` | str | Strategy identifier |
| `instrument_id` | str | Instrument to trade (e.g., `BTCUSDT-PERP.BINANCE`) |
| `bar_type` | str | Bar type for data subscription and warmup |
| `recovery` | RecoveryConfig | Recovery configuration (optional) |
| `external_order_claims` | list[str] | Instruments to claim external positions for |

---

## Common Patterns

### Pattern 1: Custom Stop-Loss Recreation

Override `_setup_exit_orders()` to recreate stop-loss orders for recovered positions:

```python
from nautilus_trader.model.enums import OrderSide, OrderType, TimeInForce
from nautilus_trader.model.orders import MarketOrder


class StrategyWithStopLoss(RecoverableStrategy):
    """Strategy that recreates stop-losses for recovered positions."""

    STOP_LOSS_PERCENT = 0.02  # 2% stop-loss

    def _setup_exit_orders(self, position: Position) -> None:
        """Create stop-loss for recovered position."""
        # Check if stop already exists (base class behavior)
        open_orders = self.cache.orders_open(instrument_id=position.instrument_id)
        has_stop = any(o.order_type == OrderType.STOP_MARKET for o in open_orders)

        if has_stop:
            self.log.info(f"Stop-loss exists for {position.instrument_id}")
            return

        # Calculate stop price
        if position.side.value == "LONG":
            stop_price = float(position.avg_px_open) * (1 - self.STOP_LOSS_PERCENT)
            order_side = OrderSide.SELL
        else:
            stop_price = float(position.avg_px_open) * (1 + self.STOP_LOSS_PERCENT)
            order_side = OrderSide.BUY

        self.log.info(
            f"Creating stop-loss: {position.instrument_id} "
            f"{order_side.value} @ {stop_price:.2f}"
        )

        # Submit stop-loss order
        # Note: Actual order submission depends on your risk management setup
        # self.submit_stop_order(...)
```

### Pattern 2: Multi-Indicator Warmup

```python
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.indicators.rsi import RelativeStrengthIndex
from nautilus_trader.indicators.atr import AverageTrueRange


class MultiIndicatorStrategy(RecoverableStrategy):
    """Strategy with multiple indicators requiring warmup."""

    def __init__(self, config: RecoverableStrategyConfig) -> None:
        super().__init__(config)
        self.ema = ExponentialMovingAverage(period=20)
        self.rsi = RelativeStrengthIndex(period=14)
        self.atr = AverageTrueRange(period=14)

    def on_historical_data(self, bar: Bar) -> None:
        """Warm up all indicators with historical data."""
        self.ema.handle_bar(bar)
        self.rsi.handle_bar(bar)
        self.atr.handle_bar(bar)

    def on_warmup_complete(self) -> None:
        """Verify all indicators are ready."""
        indicators_ready = all([
            self.ema.initialized,
            self.rsi.initialized,
            self.atr.initialized,
        ])

        if indicators_ready:
            self.log.info("All indicators initialized")
        else:
            self.log.warning("Some indicators not initialized after warmup")
```

### Pattern 3: Recovery State Inspection

Access recovery state for monitoring and debugging:

```python
class MonitoredStrategy(RecoverableStrategy):
    """Strategy with recovery state monitoring."""

    def on_warmup_complete(self) -> None:
        """Log recovery state details."""
        state = self.recovery_state

        self.log.info(
            f"Recovery completed: "
            f"status={state.status.value}, "
            f"positions={state.positions_recovered}, "
            f"indicators_warmed={state.indicators_warmed}, "
            f"duration_ms={state.recovery_duration_ms:.1f}"
        )

    def on_bar(self, bar: Bar) -> None:
        # Check if ready to trade
        if not self.is_ready:
            self.log.debug(f"Not ready: warming_up={self.is_warming_up}")
            return

        # Check recovered positions count
        if self.recovered_positions_count > 0:
            self.log.info(f"Managing {self.recovered_positions_count} recovered positions")

        # Trading logic...
```

---

## Testing Recovery

### Test 1: Cold Start (No Prior State)

```bash
# Clear Redis and start fresh
redis-cli FLUSHDB

# Start TradingNode
python run_trading_node.py
```

**Expected**:
- Node starts with no positions
- Warmup completes (0 positions recovered)
- Strategy ready to trade

### Test 2: Warm Start (Existing Positions)

```bash
# Start with existing Redis state
python run_trading_node.py
```

**Expected**:
1. Reconciliation delay (10s)
2. Positions loaded from cache
3. `on_position_recovered()` called for each position
4. `on_historical_data()` called for warmup bars
5. `on_warmup_complete()` called
6. Trading resumes

### Test 3: Verify Recovery State

```python
# After startup, check recovery state
assert strategy.is_ready
assert strategy.recovery_state.status == RecoveryStatus.COMPLETED
assert strategy.recovery_state.indicators_warmed is True
print(f"Recovered {strategy.recovered_positions_count} positions")
print(f"Recovery took {strategy.recovery_state.recovery_duration_ms:.1f}ms")
```

---

## Monitoring Recovery

### Log Messages to Watch

```
INFO  - RecoverableStrategy started: instrument=BTCUSDT-PERP.BINANCE, recovery_enabled=True, warmup_days=2
INFO  - Requesting warmup data: bar_type=BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL, start=2025-12-28, lookback_days=2
INFO  - Recovered position: instrument=BTCUSDT-PERP.BINANCE, side=LONG, quantity=0.5, avg_price=42500.00
INFO  - Position detection complete: found 1 open positions
INFO  - Received 2880 warmup bars
INFO  - Warmup complete: bars_processed=2880, duration_ms=1234.5
INFO  - Strategy ready to trade
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

---

## Troubleshooting

### Issue: Duplicate Orders After Restart

**Cause**: `flush_on_start=True` or stale cache state

**Solution**:
```python
CacheConfig(
    flush_on_start=False,  # MUST be False for recovery
)
```

### Issue: Indicators Not Ready After Warmup

**Cause**: Insufficient lookback or failed historical data request

**Solution**:
```python
RecoveryConfig(
    warmup_lookback_days=3,  # Increase from default 2
)
```

### Issue: Position Not Recovered

**Cause**: Missing `external_order_claims` configuration

**Solution**:
```python
RecoverableStrategyConfig(
    external_order_claims=["BTCUSDT-PERP.BINANCE"],  # Must list instruments
)
```

### Issue: Recovery Timeout

**Cause**: Slow network or large historical data request

**Solution**:
```python
RecoveryConfig(
    max_recovery_time_secs=60.0,  # Increase from default 30s
)
```

### Issue: HEDGING Mode Positions Not Recovered

**Cause**: HEDGING mode not fully supported (Bug #3104)

**Solution**: Use one-way mode (NETTING) instead of HEDGING mode.

---

## API Reference

### RecoverableStrategy Methods

| Method | Description |
|--------|-------------|
| `on_start()` | Called on startup, initiates recovery |
| `on_position_recovered(position)` | Hook for recovered positions (override) |
| `on_historical_data(bar)` | Hook for warmup bars (override) |
| `on_warmup_complete()` | Hook when warmup finishes (override) |
| `_setup_exit_orders(position)` | Setup stop-loss for position (override) |

### RecoverableStrategy Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_warming_up` | bool | True if warmup in progress |
| `is_ready` | bool | True if recovery complete and ready to trade |
| `recovered_positions_count` | int | Number of recovered positions |
| `recovery_state` | RecoveryState | Current recovery state object |

### RecoveryState Properties

| Property | Type | Description |
|----------|------|-------------|
| `status` | RecoveryStatus | PENDING, IN_PROGRESS, COMPLETED, FAILED, TIMEOUT |
| `positions_recovered` | int | Count of recovered positions |
| `indicators_warmed` | bool | True if indicators warmed up |
| `orders_reconciled` | bool | True if reconciliation complete |
| `recovery_duration_ms` | float | Recovery duration in milliseconds |

---

## Next Steps

1. **Spec 016**: Configure continuous reconciliation
2. **Spec 018**: Set up Redis for production
3. **Monitoring**: Add Grafana dashboards for recovery metrics
4. **Testing**: Write integration tests for recovery scenarios
