# Spec 016: Order Reconciliation Research

**Date**: 2025-12-30
**NautilusTrader Version**: v1.221.0 (stable), v1.222.0+ (nightly)
**Sources**: Context7, Discord (90-day window), GitHub Issues

---

## 1. Current Implementation Status

### 1.1 Core Reconciliation Architecture

NautilusTrader implements reconciliation through three standardized methods in execution clients:

1. **`generate_order_status_reports`** - Query venue for order states
2. **`generate_fill_reports`** - Query venue for fill/execution history  
3. **`generate_position_status_reports`** - Query venue for position states

**Key stages in reconciliation flow**:
1. Duplicate checking (prevents client order ID conflicts)
2. Order reconciliation (generates missing events, processes external orders)
3. Position reconciliation (ensures net positions match venue exactly)
4. Exception handling (individual adapter failures don't abort entire process)

### 1.2 LiveExecEngineConfig Parameters

```python
LiveExecEngineConfig(
    # Startup Reconciliation
    reconciliation=True,                    # Enable startup reconciliation
    reconciliation_lookback_mins=None,      # Lookback window (None = max history)
    reconciliation_instrument_ids=None,     # Include list for specific instruments
    filtered_client_order_ids=None,         # Client order IDs to exclude
    reconciliation_startup_delay_secs=10.0, # MINIMUM 10s for production
    
    # In-Flight Order Monitoring
    inflight_check_interval_ms=2000,        # How often to check in-flight orders
    inflight_check_threshold_ms=5000,       # Delay before triggering venue check
    inflight_check_retries=5,               # Max retry attempts
    
    # Open Orders Polling (Continuous Reconciliation)
    open_check_interval_secs=None,          # Polling frequency (5-10s recommended)
    open_check_open_only=True,              # Only request open orders
    open_check_lookback_mins=60,            # Lookback window (MINIMUM 60 mins)
    open_check_threshold_ms=5000,           # Min time before acting on discrepancies
    open_check_missing_retries=5,           # Retries before resolving missing orders
    
    # Own Books Auditing
    own_books_audit_interval_secs=None,     # Compare own books vs venue public books
    
    # Memory Management
    purge_closed_orders_interval_mins=10,   # Purge frequency (10-15 min recommended)
    purge_closed_orders_buffer_mins=60,     # Grace period before purge
    purge_closed_positions_interval_mins=None,
    purge_account_events_interval_mins=None,
    purge_from_database=False,              # CAUTION: Also deletes from backing DB
)
```

### 1.3 External Order Claims Configuration

Strategies can claim external orders for specific instruments:

```python
StrategyConfig(
    external_order_claims=[
        "BTCUSDT-PERP.BINANCE",
        "ETHUSDT-PERP.BINANCE",
    ],
)
```

**Key behaviors**:
- Orders with `order.strategy_id.value == "EXTERNAL"` are external orders
- Orders with strategy ID `EXTERNAL` and tag `RECONCILIATION` cannot be claimed
- External orders are included in portfolio calculations

---

## 2. Known Issues (Open Bugs)

### 2.1 [#3104] Binance Futures HEDGING Mode Reconciliation Failure

**Status**: OPEN (Bug)
**Severity**: Critical
**Created**: 2025-10-21

**Problem**: Long-lived positions (>10 days) in hedge mode (`dualSidePosition=true`) fail to reconcile correctly. Position net quantity diverges from venue reported value.

**Root Cause**: 
- Hedge mode uses different code path that only validates quantity matches
- `generate_missing_orders` is bypassed in hedge mode pathway
- Lookback window insufficient for long-lived positions

**Workaround**: Switch to NETTING mode instead of HEDGING mode.

**Source**: https://github.com/nautechsystems/nautilus_trader/issues/3104

---

### 2.2 [#3042] Routing Clients Venue Mismatch

**Status**: OPEN (Bug/Enhancement)
**Created**: 2025-10-07

**Problem**: Position reconciliation fails when instrument venue differs from client venue (e.g., Interactive Brokers routes to NYSE but client venue is `INTERACTIVE_BROKERS`).

**Root Cause**: 
- Reconciliation filters by `venue=IB_VENUE` but positions stored under `NYSE`, `NASDAQ`
- Returns empty results, breaking reconciliation flow

**Workaround**: None documented; requires code fix using `venue=None` pattern.

**Source**: https://github.com/nautechsystems/nautilus_trader/issues/3042

---

### 2.3 [#3054] IB Flat Positions Not Closed (RESOLVED)

**Status**: CLOSED (2025-12-18)

**Problem**: Externally closed positions created "contrary positions" instead of being marked closed in NETTING accounts.

**Resolution**: "Substantial refinements to reconciliation" implemented in develop branch.

---

## 3. Exchange-Specific Issues

### 3.1 Binance Adapter

| Issue | Status | Notes |
|-------|--------|-------|
| HEDGING mode reconciliation | BUG | #3104 - Long-lived positions fail |
| ADL order handling | FIXED | v1.221.0+ - Both `x=CALCULATED` and `x=TRADE` handled |
| Chinese character tokens | FIXED | Nightly - '币安人生' token crash resolved |
| STOP_MARKET orders | FIXED | Must use Algo Order API |
| PositionStatusReports | BUG | Only returns last position in hedge mode |

**Discord Reference** (2025-10-11):
> "NT received two PositionStatusReports correctly but ends up with only one after the reconciliation" - User reported hedge mode only keeps last position.

### 3.2 Bybit Adapter (Rust Port)

| Issue | Status | Notes |
|-------|--------|-------|
| Hedge mode (`positionIdx`) | NOT SUPPORTED | Infrastructure exists but not wired up |
| `bars_timestamp_on_close` | BUG | Not applied to WebSocket bars |
| Stop-loss orders | FIXED | Nightly - Correct trigger behavior |
| Historical bars partial bar | FIXED | Nightly - Filters incomplete bars |

**Critical Limitation**: Cannot place hedge mode orders - `submit_order()` does not set `position_idx`.

### 3.3 Interactive Brokers

| Issue | Status | Notes |
|-------|--------|-------|
| Venue routing mismatch | BUG | #3042 - NYSE/NASDAQ vs IB_VENUE |
| Max tick-by-tick requests | WARNING | API limit can be hit during warmup |
| Bond instruments | ERROR | Unsupported in reconciliation |
| External positions | FIXED | Develop branch has substantial fixes |

**Discord Reference** (2025-11-19):
> "New errors popping up... reaching IBKR's API limits when starting strategies' subscriptions... Max number of tick-by-tick requests has been reached"

---

## 4. Position Reconciliation Patterns

### 4.1 INTERNAL-DIFF Positions

When reconciliation finds venue positions without matching cached state, it creates synthetic positions with strategy ID `INTERNAL-DIFF`:

```
Scenario: Venue has +1000 AAPL, Nautilus starts fresh
Result: Creates Position(LONG 1000 AAPL, strategy=INTERNAL-DIFF)
```

**Problem in NETTING mode** (Discord 2025-12-06):
> "I'm seeing synthetic INTERNAL-DIFF positions even though I'm not limiting reconciliation lookback... the INTERNAL-DIFF stays +1000 and MyStrategy goes to +100, so net is +1100, and in practice I have 2 positions existing for a single instrument even though NETTING is set."

**Recommendation**: Use develop branch - "many changes related to reconciliation" have been made.

### 4.2 Position Pricing Hierarchy

When generating missing orders, reconciliation uses hierarchical pricing:

1. Calculated reconciliation price (preferred)
2. Market mid-price fallback
3. Current position average price
4. MARKET order (last resort)

### 4.3 Partial Window Adjustment

When lookback is limited, system analyzes position lifecycles and adds synthetic opening fills if needed.

---

## 5. In-Flight Order Timeout Resolution

When orders exceed retry limits without venue confirmation:

| Current State | Resolution |
|---------------|------------|
| `SUBMITTED` | -> `REJECTED` (no confirmation received) |
| `PENDING_UPDATE` | -> `CANCELED` (modification unacknowledged) |
| `PENDING_CANCEL` | -> `CANCELED` (cancellation unconfirmed) |

---

## 6. Order Consistency Checks

The engine resolves discrepancies when cache state differs from venue:

| Cached State | Venue State | Resolution |
|--------------|-------------|------------|
| `ACCEPTED` | Not found | -> `REJECTED` |
| `ACCEPTED` | `CANCELED` | -> `CANCELED` |
| `PARTIALLY_FILLED` | `CANCELED` | -> `CANCELED` (preserving fills) |

---

## 7. Best Practices from Community

### 7.1 Production Configuration

```python
TradingNodeConfig(
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,  # MINIMUM 10s
        open_check_interval_secs=5.0,            # 5-10s recommended
        open_check_lookback_mins=60,             # NEVER reduce below 60
        inflight_check_interval_ms=2000,
        inflight_check_retries=5,
        graceful_shutdown_on_exception=True,
    ),
    cache=CacheConfig(
        database=DatabaseConfig(host="localhost", port=6379),
        persist_account_events=True,             # CRITICAL for recovery
    ),
)
```

### 7.2 Warmup Pattern (Live Trading)

```python
def on_start(self):
    """Request historical data for indicator warmup."""
    self.request_bars(
        bar_type=self.bar_type,
        start=self.clock.utc_now() - timedelta(days=2),
        callback=self._warm_up_complete,
    )

def on_historical_data(self, data):
    """Process historical bars to warm up indicators."""
    for bar in data.bars:
        self.ema.handle_bar(bar)
```

### 7.3 External Order Detection

```python
def on_order_event(self, event):
    if event.order.strategy_id.value == "EXTERNAL":
        # Handle external order
        self.log.info(f"External order detected: {event.order}")
```

---

## 8. Gap Detection Mechanisms

### 8.1 Startup Gap Detection

1. Query venue for all open orders and positions
2. Compare against cached state (Redis/database)
3. Generate missing fills for unreconciled positions
4. Create synthetic orders when `generate_missing_orders=True`

### 8.2 Continuous Gap Detection

1. **In-flight monitoring**: Check unconfirmed orders every 2s
2. **Open orders polling**: Check venue state every 5-10s
3. **Own books auditing**: Compare internal order book vs venue

---

## 9. Recommendations for Spec 016

### 9.1 Must Have
- Use NETTING mode (HEDGING has known issues)
- Set `reconciliation_startup_delay_secs >= 10.0`
- Never reduce `open_check_lookback_mins` below 60
- Use Redis/database cache for recovery

### 9.2 Should Avoid
- Mixing stable and nightly catalog schemas
- HEDGING mode on Binance Futures (bug #3104)
- Bybit hedge mode (not implemented)
- Reducing lookback windows for long-lived positions

### 9.3 Monitor for Fixes
- #3104: Binance HEDGING reconciliation
- #3042: IB venue routing mismatch
- Bybit `positionIdx` implementation (community PR in progress)

---

## 10. Documentation Links

- [Live Trading Concepts](https://nautilustrader.io/docs/nightly/concepts/live)
- [Reconciliation Configuration](https://nautilustrader.io/docs/nightly/concepts/live#reconciliation-configuration)
- [Execution Reconciliation](https://nautilustrader.io/docs/nightly/concepts/live#execution-reconciliation)
- [Cache Configuration](https://nautilustrader.io/docs/latest/concepts/cache#database-configuration)

---

*Research compiled from Context7, Discord (90-day window), and GitHub Issues*
