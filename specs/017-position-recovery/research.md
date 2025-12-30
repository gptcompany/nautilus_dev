# Research: Position Recovery (Spec 017)

**Created**: 2025-12-30
**Status**: Complete

---

## Research Question 1: Position Restoration on TradingNode Restart

### Decision
Use `CacheConfig` with Redis backend + `LiveExecEngineConfig` reconciliation for complete position recovery.

### Rationale
NautilusTrader handles position restoration through a two-phase process:

**Phase 1: Cache Restoration**
- On startup, loads cached state from Redis database
- Positions, orders, and account states are deserialized from backing store
- `CacheConfig.flush_on_start=False` (default) preserves prior state

**Phase 2: Execution Reconciliation**
- After cache restoration, `LiveExecEngineConfig.reconciliation=True` triggers exchange state comparison
- Uses three standardized methods from execution clients:
  1. `generate_order_status_reports()` - Current order states from venue
  2. `generate_fill_reports()` - Historical fills within lookback window
  3. `generate_position_status_reports()` - Current position states from venue

### Alternatives Considered
1. **Parquet catalog only** - Not suitable for live trading state; designed for historical data
2. **In-memory only** - All state lost on restart; only for backtesting
3. **Postgres backend** - Supported but less common for real-time trading state

---

## Research Question 2: Redis Cache Schema

### Decision
Use the default `trader-` prefixed key structure with msgpack serialization.

### Rationale
**Key Structure** (from `CacheConfig`):
```
{trader_prefix}-{data_type}:{identifier}
```

Where:
- `trader_prefix` = `"trader-"` if `use_trader_prefix=True`
- `data_type` = `order`, `position`, `account`, `instrument`, etc.
- `identifier` = Client order ID, position ID, account ID, instrument ID

**Example Keys**:
```
trader-order:O-20251230-001
trader-position:BTCUSDT-PERP.BINANCE-EXTERNAL
trader-account:BINANCE-USDT_FUTURES-master
trader-instrument:BTCUSDT-PERP.BINANCE
```

**Position Snapshot Fields**:
- `position_id`: PositionId
- `instrument_id`: InstrumentId
- `strategy_id`: StrategyId
- `account_id`: AccountId
- `side`: PositionSide
- `signed_qty`: Decimal
- `quantity`: Quantity
- `avg_px_open`: Decimal
- `realized_pnl`: Money
- `unrealized_pnl`: Money | None
- `ts_opened`: int (nanoseconds)
- `ts_last`: int (nanoseconds)

### Alternatives Considered
1. **Custom key structure** - Increases complexity, no benefit
2. **Instance ID in keys** - Only if running multiple instances per trader

---

## Research Question 3: Reconciliation Best Practices

### Decision
Use three-phase reconciliation with synthetic fill generation for discrepancies.

### Rationale
The reconciliation process handles three scenarios:

**Scenario 1: Cached state matches venue**
- No action needed, positions aligned

**Scenario 2: No cached state exists**
- All external orders/positions reconstructed from venue reports
- Positions tagged with `strategy_id="EXTERNAL"`

**Scenario 3: Position discrepancy detected**
- System generates synthetic fills using priority:
  1. Calculated reconciliation price (weighted average)
  2. Market mid-price (fallback)
  3. Current position average price (secondary fallback)

**Critical Configuration**:
```python
exec_engine=LiveExecEngineConfig(
    reconciliation=True,
    reconciliation_lookback_mins=None,  # Max from venue
    reconciliation_startup_delay_secs=10.0,  # MINIMUM 10s
    generate_missing_orders=True,
    position_check_interval_secs=30.0,  # Continuous reconciliation
)
```

### Known Issues (from Discord)
| Issue | Description | Status |
|-------|-------------|--------|
| #3104 | HEDGING mode reconciliation fails for Binance Futures | Open |
| #3042 | Routing client venue mismatch breaks reconciliation | Open |

### Alternatives Considered
1. **Manual reconciliation** - Error-prone, not production-ready
2. **Ignoring discrepancies** - Leads to incorrect P&L

---

## Research Question 4: Strategy State Restoration Patterns

### Decision
Use `StrategyConfig.external_order_claims` + `on_start()` warmup pattern.

### Rationale
**A. Position/Order Claiming**:
```python
config = MyStrategyConfig(
    strategy_id="MOMENTUM-001",
    oms_type="NETTING",
    external_order_claims=[InstrumentId.from_str("BTCUSDT-PERP.BINANCE")],
    manage_contingent_orders=True,
    manage_gtd_expiry=True,
)
```

**B. Indicator Warmup in `on_start()`**:
```python
def on_start(self):
    self.request_bars(
        bar_type=self.bar_type,
        start=self.clock.utc_now() - timedelta(days=2),
        callback=self._warm_up_complete,
    )
    # Check for existing positions
    for position in self.cache.positions_open(strategy_id=self.id):
        self._restore_position_management(position)
```

**C. Detecting External vs Internal Orders**:
```python
def on_order_filled(self, event: OrderFilled):
    order = self.cache.order(event.client_order_id)
    if order.strategy_id.value == "EXTERNAL":
        if "RECONCILIATION" in (order.tags or []):
            return  # Skip reconciliation fills
```

### Alternatives Considered
1. **No warmup** - Indicators produce garbage signals initially
2. **Pre-computed indicators** - Complex, requires external storage

---

## Research Question 5: Event Replay Mechanisms

### Decision
NautilusTrader does NOT provide explicit event replay; use cache restoration + reconciliation instead.

### Rationale
The system uses **state snapshots** rather than event sourcing:

1. **Order Events** - Each event updates order state in cache
2. **Position Snapshots** - Stored as current state, not event history
3. **Cache Restoration** - Loads latest snapshot on startup
4. **Reconciliation** - Fills gap from shutdown to restart

**What Gets Persisted**:
- Current order states (with event history attached)
- Current position states
- Account balances and margin
- Instrument definitions

**What Does NOT Get Persisted**:
- Raw event stream
- Strategy internal state (rebuild in `on_start()`)
- Indicator values (warmup required)

### Alternatives Considered
1. **Full event sourcing** - High complexity, not implemented
2. **External event store** - Possible via MessageBus external streams
3. **Log replay** - Manual process, not automated

---

## Production Configuration Template

```python
from nautilus_trader.config import TradingNodeConfig, CacheConfig, LiveExecEngineConfig
from nautilus_trader.common.config import DatabaseConfig

PRODUCTION_CONFIG = TradingNodeConfig(
    trader_id="PROD-TRADER-001",
    cache=CacheConfig(
        database=DatabaseConfig(
            type="redis",
            host="localhost",
            port=6379,
            timeout=2,
        ),
        encoding="msgpack",
        timestamps_as_iso8601=False,
        persist_account_events=True,
        buffer_interval_ms=100,
        use_trader_prefix=True,
        use_instance_id=False,
        flush_on_start=False,
        tick_capacity=10_000,
        bar_capacity=10_000,
    ),
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_lookback_mins=None,
        reconciliation_startup_delay_secs=10.0,
        generate_missing_orders=True,
        inflight_check_interval_ms=2_000,
        inflight_check_threshold_ms=5_000,
        inflight_check_retries=5,
        open_check_interval_secs=10.0,
        open_check_lookback_mins=60,
        position_check_interval_secs=30.0,
        position_check_lookback_mins=60,
        graceful_shutdown_on_exception=True,
    ),
)
```

---

## Summary

All research questions resolved. Key findings:

1. **Two-phase recovery**: Cache restoration + exchange reconciliation
2. **Redis key structure**: `trader-{type}:{identifier}` with msgpack encoding
3. **Reconciliation**: Automatic synthetic fills for discrepancies
4. **Strategy state**: Use `external_order_claims` + warmup pattern
5. **Event replay**: Not supported; use snapshots + reconciliation instead

**Recommendation**: Use `develop` branch or latest nightly for production - significant reconciliation fixes merged recently.
