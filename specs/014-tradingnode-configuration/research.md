# Research: TradingNode Configuration

**Feature**: 014-tradingnode-configuration
**Date**: 2025-12-28
**NautilusTrader Version**: Nightly v1.222.0+

## Research Summary

This document consolidates findings from official NautilusTrader documentation (Context7) and Discord community discussions for production TradingNode configuration.

---

## 1. TradingNodeConfig Core Parameters

### Decision: Production Timeout Settings
**Chosen Values**:
- `timeout_connection`: 30.0s
- `timeout_reconciliation`: 15.0s (10s minimum per docs)
- `timeout_portfolio`: 10.0s
- `timeout_disconnection`: 10.0s
- `timeout_post_stop`: 5.0s

**Rationale**: These values allow sufficient time for venue connection and reconciliation while avoiding excessive delays on startup.

**Alternatives Considered**: Shorter timeouts (5s) - rejected due to potential race conditions with slow exchange APIs.

---

## 2. CacheConfig with Redis

### Decision: Use Redis with msgpack encoding
**Configuration**:
```python
CacheConfig(
    database=DatabaseConfig(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        timeout=2.0,
    ),
    encoding="msgpack",           # Faster than JSON
    timestamps_as_iso8601=True,   # Human-readable in logs
    buffer_interval_ms=100,       # 100ms flush buffer
    flush_on_start=False,         # Preserve cache on restart
    tick_capacity=10000,
    bar_capacity=10000,
)
```

**Rationale**:
- Redis required for crash recovery and position persistence
- msgpack is 2-3x faster than JSON for serialization
- 100ms buffer balances latency vs disk I/O

**Alternatives Considered**:
- In-memory cache: Rejected - no crash recovery
- JSON encoding: Rejected - slower serialization

**Discord Insight**: "Use Redis WITH reconciliation, not instead of it. Cache persists orders/positions; reconciliation syncs with venue."

---

## 3. LiveExecEngineConfig - Reconciliation

### Decision: Production Reconciliation Settings
**Configuration**:
```python
LiveExecEngineConfig(
    # Core reconciliation
    reconciliation=True,
    reconciliation_lookback_mins=60,          # MINIMUM 60 per docs
    reconciliation_startup_delay_secs=10.0,   # MINIMUM 10 per docs

    # In-flight order monitoring
    inflight_check_interval_ms=2000,
    inflight_check_threshold_ms=5000,
    inflight_check_retries=5,

    # Continuous open order checks
    open_check_interval_secs=5,
    open_check_lookback_mins=60,
    open_check_threshold_ms=5000,
    open_check_missing_retries=5,

    # Position snapshots
    snapshot_positions=True,
    snapshot_positions_interval_secs=60,

    # Memory management
    purge_closed_orders_interval_mins=15,
    purge_closed_orders_buffer_mins=60,
    purge_closed_positions_interval_mins=15,
    purge_closed_positions_buffer_mins=60,

    # Safety
    graceful_shutdown_on_exception=True,
    qsize=100000,
)
```

**Rationale**:
- 60-minute lookback catches orders placed before restart
- 10-second startup delay allows venue sync
- Position snapshots enable faster recovery
- Memory purging prevents long-running system bloat

**Known Issues (Changelog)**:
- Issue #3104: Reconciliation fails for long-lived Binance Futures HEDGING positions
- Issue #3042: Reconciliation fails when instrument venue differs from client venue

**Mitigation**: Use NETTING mode for Binance Futures, verify instrument/venue consistency.

---

## 4. LiveDataEngineConfig

### Decision: Standard Production Settings
**Configuration**:
```python
LiveDataEngineConfig(
    qsize=100000,
    time_bars_build_with_no_updates=True,
    time_bars_timestamp_on_close=True,
    validate_data_sequence=True,
    debug=False,
)
```

**Rationale**: Large queue prevents data loss during spikes; validation catches data issues early.

---

## 5. LiveRiskEngineConfig

### Decision: Conservative Rate Limits
**Configuration**:
```python
LiveRiskEngineConfig(
    bypass=False,                         # NEVER bypass in production
    max_order_submit_rate="100/00:00:01", # 100 orders/second
    max_order_modify_rate="100/00:00:01", # 100 mods/second
    debug=False,
)
```

**Rationale**:
- 100/second is well within exchange limits (Binance: 1200/min for futures)
- Never bypass risk engine in production

**Alternatives Considered**:
- No rate limiting: Rejected - risk of exchange ban
- Per-instrument limits: YAGNI for now

---

## 6. BinanceLiveExecClientConfig

### Decision: Production Settings for USDT Futures
**Configuration**:
```python
BinanceLiveExecClientConfig(
    account_type=BinanceAccountType.USDT_FUTURES,
    testnet=False,
    use_reduce_only=True,           # Safety for exits
    use_position_ids=True,          # Enable hedging mode tracking
    recv_window_ms=5000,
    max_retries=3,
    treat_expired_as_canceled=False,
    listen_key_ping_max_failures=3,
    update_instruments_interval_mins=60,
    instrument_provider=InstrumentProviderConfig(load_all=False),
)
```

**Environment Variables**:
```bash
BINANCE_API_KEY=xxx
BINANCE_API_SECRET=xxx
BINANCE_TESTNET_API_KEY=xxx
BINANCE_TESTNET_API_SECRET=xxx
```

**Known Issues (Discord)**:
- Chinese character tokens (e.g., '币安人生') - fixed in nightly
- STOP_MARKET requires Algo Order API
- ADL order handling requires recent version

**Rate Limits**:
- Futures Global: 2,400 weight/minute
- Order Placement: 1,200 weight/minute

---

## 7. BybitLiveExecClientConfig

### Decision: Production Settings for LINEAR Perpetuals
**Configuration**:
```python
BybitLiveExecClientConfig(
    product_types=[BybitProductType.LINEAR],
    testnet=False,
    demo=False,
    recv_window_ms=5000,
    auto_repay_spot_borrows=True,
    use_ws_execution_fast=False,    # Standard latency is fine
    ws_trade_timeout_secs=10,
    ws_auth_timeout_secs=10,
    max_retries=3,
    retry_delay_initial_ms=1000,
    retry_delay_max_ms=10000,
    update_instruments_interval_mins=60,
)
```

**Environment Variables**:
```bash
BYBIT_API_KEY=xxx
BYBIT_API_SECRET=xxx
BYBIT_TESTNET_API_KEY=xxx
BYBIT_TESTNET_API_SECRET=xxx
```

**Known Limitations (CLAUDE.md)**:
- Hedge mode (`positionIdx`) NOT supported in Rust port
- `bars_timestamp_on_close` not applied to WebSocket bars
- 1-bar offset in indicators (WebSocket vs HTTP)
- Trailing stops: No client order ID on venue side
- Spot: Trailing stops and `reduce_only` not supported

**Mitigation**: Use NETTING mode only. Document hedge mode limitation.

---

## 8. LoggingConfig

### Decision: JSON Logs with Component-Level Control
**Configuration**:
```python
LoggingConfig(
    log_level="INFO",
    log_level_file="DEBUG",
    log_directory="/var/log/nautilus",
    log_file_format="json",
    log_file_max_size=100_000_000,   # 100 MB
    log_file_max_backup_count=10,
    log_colors=True,
    log_component_levels={
        "DataEngine": "INFO",
        "ExecEngine": "DEBUG",
        "RiskEngine": "WARNING",
    },
)
```

**Rationale**:
- JSON format integrates with Grafana Loki, ELK
- DEBUG for ExecEngine helps debug order issues
- 100MB rotation prevents disk space issues

---

## 9. StreamingConfig

### Decision: SIZE-Based Rotation for Catalog
**Configuration**:
```python
from nautilus_trader.persistence.config import RotationMode

StreamingConfig(
    catalog_path="/data/nautilus/catalog",
    fs_protocol="file",
    flush_interval_ms=2000,
    rotation_mode=RotationMode.SIZE,
    max_file_size=128 * 1024 * 1024,  # 128 MB
    include_types=[TradeTick, QuoteTick],
)
```

**Rationale**:
- SIZE rotation (128MB) prevents individual files from growing too large
- 2-second flush balances latency vs I/O
- Only stream needed data types

**Post-Run Conversion** (from Discord):
```python
catalog.convert_stream_to_data(
    instance_id=instance_id,
    data_cls=TradeTick,
    subdirectory="live",
)
```

---

## 10. Strategy Configuration

### Decision: Explicit OMS Type and External Order Claims
**Configuration**:
```python
class MyStrategyConfig(StrategyConfig):
    strategy_id: str = "MY-STRATEGY-001"
    order_id_tag: str = "MYS"
    oms_type: OmsType = OmsType.NETTING  # Explicit - avoid default confusion
    use_uuid_client_order_ids: bool = False
    external_order_claims: list = []     # Set on restart to claim positions
    manage_contingent_orders: bool = True
    manage_gtd_expiry: bool = True
```

**Discord Insight**: "Always set `oms_type` explicitly - default can cause position confusion on restart."

---

## 11. Environment Variable Structure

### Decision: Standardized Environment Variables
```bash
# Core
NAUTILUS_TRADER_ID=PROD-TRADER-001
NAUTILUS_ENVIRONMENT=LIVE  # or SANDBOX

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional

# Logging
NAUTILUS_LOG_DIRECTORY=/var/log/nautilus
NAUTILUS_LOG_LEVEL=INFO

# Data
NAUTILUS_CATALOG_PATH=/data/nautilus/catalog

# Binance
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_TESTNET=false

# Bybit
BYBIT_API_KEY=
BYBIT_API_SECRET=
BYBIT_TESTNET=false
```

**Rationale**: Prefixed variables avoid collision with other applications.

---

## 12. Key Production Recommendations

| Setting | Value | Reason |
|---------|-------|--------|
| `reconciliation` | `True` | Essential for crash recovery |
| `reconciliation_lookback_mins` | `>= 60` | Don't reduce below 60 |
| `reconciliation_startup_delay_secs` | `>= 10` | Allow venue sync |
| `graceful_shutdown_on_exception` | `True` | Prevent data loss |
| `snapshot_positions` | `True` | Track position state |
| Cache with Redis | Required | Persist execution events |
| `oms_type` | Always explicit | Avoid position confusion |
| `external_order_claims` | Set on restart | Claim existing positions |
| Environment variables | Required | Security best practice |
| Bybit hedge mode | NOT supported | Use NETTING only |

---

## Sources

- NautilusTrader Docs: https://nautilustrader.io/docs/nightly/concepts/live
- Binance Integration: https://nautilustrader.io/docs/nightly/integrations/binance
- Bybit Integration: https://nautilustrader.io/docs/nightly/integrations/bybit
- Discord Community: `docs/discord/help.md`, `docs/discord/questions.md`, `docs/discord/binance.md`
- Changelog: `docs/nautilus/nautilus-trader-changelog.json`
