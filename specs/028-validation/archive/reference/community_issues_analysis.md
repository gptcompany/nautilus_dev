# Community Issues Analysis - Discord

**Analysis Date:** 2026-01-04
**Source:** NautilusTrader Discord Community (90-day window)
**Channels Analyzed:** #help, #questions, #data, #binance, #bybit, #dev-rust, #general, #trading

## Executive Summary

**Total Issues Found:** 28 distinct issues affecting live trading and backtesting
**Pattern Categories:** 7 major categories identified
**Most Critical:** Reconciliation issues (HIGH), Timestamp discrepancies (HIGH), Adapter-specific bugs (MEDIUM-HIGH)

**Key Finding:** The community frequently encounters issues that directly impact our Adaptive Control Framework, particularly around:
1. Position state recovery after restart
2. Timestamp consistency between backtest and live
3. Exchange adapter quirks that affect order execution

---

## Issues by Category

### 1. Live Trading / Reconciliation Issues

| ID | Issue | Description | Workaround | Relevance to Us |
|----|-------|-------------|------------|-----------------|
| R1 | IB Reconciliation creates phantom positions | After restart, NT creates SHORT position when closing existing LONG due to spot asset handling | Use `external_order_claims` explicitly | **HIGH** - Affects position recovery |
| R2 | Duplicate orders on restart with Redis cache | NT creates additional orders with wrong types (MARKET -> LIMIT) each restart | None documented | **HIGH** - Corrupts order state |
| R3 | Binance hedge mode position loss | Only one of two PositionStatusReports retained after reconciliation | None - possible bug | **HIGH** - Position mismatch |
| R4 | Client order ID chaos after restart | Orders get randomly generated IDs like "O-uuid" instead of original | None documented | **MEDIUM** - Traceability issues |
| R5 | Price serialization error in ExecEngine | `TypeError('Encoding objects of type nautilus_trader.model.objects.Price is unsupported')` | Update to latest nightly | **MEDIUM** - Blocks order processing |

### 2. Indicator Warmup Issues

| ID | Issue | Description | Workaround | Relevance to Us |
|----|-------|-------------|------------|-----------------|
| W1 | Historical bars arrive in WRONG ORDER | `request_bars()` returns newest-to-oldest, corrupts indicator warmup | Reverse bars manually before feeding to indicators | **HIGH** - Critical for our regime detection |
| W2 | 300-minute warmup wait in live trading | Must wait entire warmup period (5 hours) before trading | Use `request_bars()` with `on_historical_data()` callback | **MEDIUM** - Delays live start |
| W3 | Low-level API doesn't serve historical data | `BacktestEngine` (low-level) ignores `request_bars()` - only `BacktestNode` works | Use high-level API | **LOW** - We use high-level |

### 3. Timestamp / Data Consistency Issues

| ID | Issue | Description | Workaround | Relevance to Us |
|----|-------|-------------|------------|-----------------|
| T1 | Bybit bars_timestamp_on_close ignored on WebSocket | HTTP bars have close timestamp, WS bars have open timestamp - 1 bar offset | None - bug reported Dec 2025 | **HIGH** - Indicator 1-bar lag |
| T2 | Historical bars include current incomplete bar | Last bar from `request_bars()` is not yet closed | Filter last bar if ts_event > now - bar_duration | **MEDIUM** - Affects signal timing |
| T3 | Precision mismatch catalog vs engine | OrderBookDelta precision=1, Instrument precision=2 causes fill validation failure | Ensure catalog and instrument precision match | **HIGH** - Crashes backtest |

### 4. Exchange Adapter Issues

#### Binance

| ID | Issue | Description | Workaround | Relevance to Us |
|----|-------|-------------|------------|-----------------|
| B1 | Chinese character token crash | Currency code '币安人生' panics Rust validation | Install nightly >= 1.221.0a20251026 | **LOW** - We filter instruments |
| B2 | ADL orders not processed | TRADE execution type ADL fills dropped, only CALCULATED handled | Fixed in commit 32896d3 | **MEDIUM** - Position mismatch |
| B3 | STOP_MARKET requires Algo Order API | Error -4120: Order type not supported for this endpoint | Fixed in commit 62ef6f6 | **HIGH** - Affects SL orders |
| B4 | OrderFilled events missing on binance.us | Fills visible in UI but not in NT logs | Still under investigation | **HIGH** - Critical for execution |
| B5 | FundingRateUpdate not implemented | Need nightly Rust adapters for funding rate subscription | Implement in Python manually | **LOW** - Nice to have |

#### Bybit

| ID | Issue | Description | Workaround | Relevance to Us |
|----|-------|-------------|------------|-----------------|
| BY1 | Hedge mode (positionIdx) NOT supported | Cannot specify one-way/long hedge/short hedge mode | PR in progress (Dec 2025) | **HIGH** - Limits position management |
| BY2 | Stop-loss triggers immediately (Python adapter) | STOP BUY triggers at any price in stable release | Use Rust-based nightly | **HIGH** - Critical for risk management |
| BY3 | Current bar returned in historical request | Incomplete bar included in request_bars response | Fixed in commit a15a0f2 | **MEDIUM** - Already fixed |

#### Interactive Brokers

| ID | Issue | Description | Workaround | Relevance to Us |
|----|-------|-------------|------------|-----------------|
| IB1 | Reconciliation with external positions fails | Flat positions not closed entirely, duplicate orders | Use persistent Redis cache | **MEDIUM** - IB-specific |
| IB2 | Max tick-by-tick requests | Platform limits on real-time data requests | Limit concurrent subscriptions | **LOW** - Data volume issue |

### 5. Backtest vs Live Discrepancies

| ID | Issue | Description | Workaround | Relevance to Us |
|----|-------|-------------|------------|-----------------|
| BL1 | Fill price != bar.close | Market orders filled at avg_px different from close price | Normal slippage simulation | **LOW** - Expected behavior |
| BL2 | Order book prices wildly off | L3 MBO data shows $5+ price discrepancy in backtest | Investigate `apply_deltas` usage | **MEDIUM** - Data handling |
| BL3 | Dynamic instrument changes not supported | Cannot change instruments during backtest (FB->META) | Run separate backtests | **LOW** - Corporate actions |
| BL4 | 100GB options data impractical to preload | Cannot dynamically load SPX options during backtest | None - NT limitation | **MEDIUM** - Data scale issue |

### 6. Data Pipeline Issues

| ID | Issue | Description | Workaround | Relevance to Us |
|----|-------|-------------|------------|-----------------|
| D1 | Catalog cross-platform incompatibility | Windows/Linux precision mode mismatch causes panic | Use same precision mode | **MEDIUM** - Dev environment |
| D2 | CSV to Parquet OOM crash | 30GB tick files crash WSL2 | Split files, use yield/chunks | **HIGH** - Data wrangling |
| D3 | Feather files unreadable with pandas | Streaming feather files use custom format | Use `convert_stream_to_data()` | **LOW** - Internal format |

### 7. Strategy Development Issues

| ID | Issue | Description | Workaround | Relevance to Us |
|----|-------|-------------|------------|-----------------|
| S1 | Regime change risk with mean reversion | "Cauchy outlier steamrolls months of profits" | Always have stop-loss for regime change | **HIGH** - Our core concern |
| S2 | Overfitting with z-score regression | Concern about overfitting when adding signals | Use out-of-sample validation | **MEDIUM** - Strategy validation |
| S3 | Custom data subscription needs client_id | Not documented that `subscribe_data()` needs `client_id=ClientId("...")` | Read source code or docs | **LOW** - Documentation gap |

---

## Pattern Analysis

### Pattern 1: Reconciliation Fragility
**Frequency:** 5+ distinct issues
**Impact:** HIGH - Can cause position mismatch, phantom orders
**Root Cause:** Complex state recovery across broker reconnections
**Mitigation:** Always use persistent Redis cache, `external_order_claims`, test restart scenarios

### Pattern 2: Timestamp Consistency 
**Frequency:** 3+ issues
**Impact:** HIGH - Causes 1-bar indicator lag, signal timing errors
**Root Cause:** Inconsistent bar timestamp handling (open vs close) across data sources
**Mitigation:** Verify `bars_timestamp_on_close` config, use same timestamp convention everywhere

### Pattern 3: Adapter-Specific Quirks
**Frequency:** 10+ issues across Binance/Bybit/IB
**Impact:** MEDIUM-HIGH - Exchange-specific workarounds needed
**Root Cause:** API differences, incomplete feature parity, evolving exchange APIs
**Mitigation:** Use nightly builds, monitor Discord for adapter updates, test on testnet first

### Pattern 4: Historical Data Order Corruption
**Frequency:** 2+ issues
**Impact:** HIGH - Invalidates indicator warmup completely
**Root Cause:** API returns data in reverse order, incomplete bars included
**Mitigation:** Sort bars by timestamp before feeding to indicators, filter incomplete bars

### Pattern 5: Memory/Scale Limitations
**Frequency:** 2+ issues  
**Impact:** MEDIUM - Limits large-scale backtesting
**Root Cause:** Loading entire datasets into memory
**Mitigation:** Use streaming catalogs, chunk processing, Parquet over CSV

---

## Relevance to Our Adaptive Control Framework

### HIGH Relevance Issues

| Issue | Impact on Our System | Required Mitigation |
|-------|---------------------|---------------------|
| **W1: Historical bars wrong order** | Corrupts regime detection warmup | Implement bar sorting in warmup handler |
| **T1: Timestamp 1-bar offset** | Regime signal delayed by 1 bar | Use HTTP bars for critical calculations, or compensate |
| **R1-R3: Reconciliation issues** | Position mismatch after restart | Mandatory Redis persistence + restart testing |
| **B3, BY2: Stop orders break** | Risk management fails | Use nightly builds, test SL orders before production |
| **S1: Regime change risk** | Cauchy outlier wipes profits | Always have hard stop for regime change protection |
| **BY1: No hedge mode** | Cannot manage hedged positions | Wait for PR or use different exchange |

### MEDIUM Relevance Issues

| Issue | Impact on Our System | Required Mitigation |
|-------|---------------------|---------------------|
| **D2: OOM on large data** | Data wrangling crashes | Use chunked processing for tick data |
| **T3: Precision mismatch** | Backtest validation fails | Verify precision settings match data |
| **B2: ADL not processed** | Binance liquidations missed | Update to latest nightly |
| **BL4: Dynamic instruments** | Multi-asset backtests limited | Design around this limitation |

### LOW Relevance Issues

| Issue | Impact on Our System | Required Mitigation |
|-------|---------------------|---------------------|
| **B1: Chinese tokens** | None - we filter | No action |
| **BL1: Fill slippage** | Expected behavior | Accept as realistic simulation |
| **IB2: Tick limits** | Not using IB primarily | No action |

---

## Recommendations

Based on community feedback, implement these safeguards:

### 1. Warmup Pipeline Hardening
```python
def on_historical_data(self, bars: list[Bar]):
    # CRITICAL: Community reports bars arrive newest-to-oldest
    sorted_bars = sorted(bars, key=lambda b: b.ts_event)
    
    # CRITICAL: Filter incomplete bars
    now = self.clock.utc_now_ns()
    complete_bars = [b for b in sorted_bars if b.ts_event < now - self.bar_type.spec.timedelta]
    
    for bar in complete_bars:
        self.ema.handle_bar(bar)
```

### 2. Mandatory Restart Testing
- Test strategy restart with open positions
- Test Redis persistence recovery
- Test `external_order_claims` behavior
- Test after network disconnection

### 3. Exchange Adapter Version Policy
- **Always use nightly builds** for Binance/Bybit in production
- Monitor Discord #binance and #bybit for breaking changes
- Test stop-loss orders on testnet before live

### 4. Regime Change Protection
```python
# Community wisdom: "Cauchy outlier steamrolls profits"
# Always have hard stop for regime change scenarios
max_regime_drawdown = 0.05  # 5% max loss per regime
self.submit_stop_loss(trigger_price=entry * (1 - max_regime_drawdown))
```

### 5. Data Pipeline Robustness
- Chunk large CSV files before Parquet conversion
- Verify precision mode consistency across platforms
- Use streaming catalogs for large datasets

---

## Notable Quotes

> "you're hoping that some huge Cauchy outlier doesn't steamroll the last couple of months of profits with a sharp correction into a regime change"
> - @cjdsellers on mean reversion risk

> "I spent the last 2 hours on a very nuanced issue, that im sure others have covered themselves"
> - @fudgemin on documentation gaps

> "i had to seperate my historical from my live. Its not feasible to compute on demand: past n features, for past n timeframes, for n symbols"
> - @fudgemin on warmup architecture

> "Something that would help is to try to debug and fix stuff instead of ditching stuff. The library is open source"
> - @faysou on contributing vs workarounds

> "one key advantage of open source is that more users means more bugs reported and fixed"
> - @faysou on community value

---

## Appendix: Issue Sources

| Channel | Issues | Key Concerns |
|---------|--------|--------------|
| #help | 12 | Reconciliation, warmup, strategy bugs |
| #binance | 5 | ADL, STOP_MARKET, Chinese tokens |
| #bybit | 4 | Hedge mode, timestamps, stop-loss |
| #data | 4 | Catalog, persistence, precision |
| #questions | 2 | Order book, dynamic instruments |
| #general | 1 | Warmup patterns |
