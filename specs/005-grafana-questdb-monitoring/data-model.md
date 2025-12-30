# Data Model: Grafana + QuestDB Production Monitoring

**Feature**: 005-grafana-questdb-monitoring
**Created**: 2025-12-26
**Status**: Draft

## Entity Overview

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   DaemonMetrics  │     │  ExchangeStatus  │     │   TradeMetrics   │
│   (time-series)  │     │   (time-series)  │     │   (time-series)  │
└────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │         QuestDB           │
                    │   (designated timestamp)  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │         Grafana           │
                    │  (dashboards + alerts)    │
                    └───────────────────────────┘
```

## Entity Definitions

### 1. DaemonMetrics

Metrics from CCXT DaemonRunner (Spec 001 integration).

**Table Schema (QuestDB)**:
```sql
CREATE TABLE daemon_metrics (
    -- Designated timestamp (partition key)
    timestamp TIMESTAMP NOT NULL,

    -- Dimensions (SYMBOL for efficient storage)
    host SYMBOL CAPACITY 1000,           -- Hostname running daemon
    env SYMBOL CAPACITY 256,             -- Environment: prod, staging, dev

    -- Counters (monotonically increasing)
    fetch_count LONG,                    -- Cumulative OI/Funding fetches
    error_count LONG,                    -- Cumulative errors
    liquidation_count LONG,              -- Cumulative liquidations streamed

    -- Gauges (current state)
    uptime_seconds DOUBLE,               -- Time since daemon start
    running BOOLEAN,                     -- Daemon running state

    -- Status
    last_error VARCHAR                   -- Last error message (if any)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL
DEDUP UPSERT KEYS(timestamp, host, env);
```

**Python Dataclass**:
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DaemonMetrics:
    timestamp: datetime
    host: str
    env: str
    fetch_count: int
    error_count: int
    liquidation_count: int
    uptime_seconds: float
    running: bool
    last_error: str | None = None
```

**Validation Rules**:
- `timestamp`: Must be UTC, not in future
- `host`: Non-empty string, max 255 chars
- `env`: One of ["prod", "staging", "dev"]
- `fetch_count`: >= 0, monotonically increasing
- `error_count`: >= 0
- `liquidation_count`: >= 0
- `uptime_seconds`: >= 0

---

### 2. ExchangeStatus

Connectivity status per exchange.

**Table Schema (QuestDB)**:
```sql
CREATE TABLE exchange_status (
    -- Designated timestamp
    timestamp TIMESTAMP NOT NULL,

    -- Dimensions
    exchange SYMBOL CAPACITY 256,        -- Exchange: binance, bybit, okx
    host SYMBOL CAPACITY 1000,
    env SYMBOL CAPACITY 256,

    -- Status
    connected BOOLEAN,                   -- WebSocket connected
    latency_ms DOUBLE,                   -- Round-trip latency
    reconnect_count LONG,                -- Cumulative reconnections

    -- Timestamps
    last_message_at TIMESTAMP,           -- Last message received
    disconnected_at TIMESTAMP            -- Last disconnect time (null if connected)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL
DEDUP UPSERT KEYS(timestamp, exchange, host);
```

**Python Dataclass**:
```python
@dataclass
class ExchangeStatus:
    timestamp: datetime
    exchange: str
    host: str
    env: str
    connected: bool
    latency_ms: float
    reconnect_count: int
    last_message_at: datetime | None = None
    disconnected_at: datetime | None = None
```

**Validation Rules**:
- `exchange`: One of ["binance", "bybit", "okx", "dydx"]
- `latency_ms`: >= 0, reasonable upper bound (10000ms)
- `reconnect_count`: >= 0
- `last_message_at`: Must be <= timestamp

**State Transitions**:
```
    ┌──────────────┐
    │  CONNECTED   │◄──────────────┐
    └──────┬───────┘               │
           │ disconnect            │ reconnect
           ▼                       │
    ┌──────────────┐               │
    │ DISCONNECTED │───────────────┘
    └──────────────┘
```

---

### 3. PipelineMetrics

Data pipeline throughput metrics.

**Table Schema (QuestDB)**:
```sql
CREATE TABLE pipeline_metrics (
    -- Designated timestamp
    timestamp TIMESTAMP NOT NULL,

    -- Dimensions
    exchange SYMBOL CAPACITY 256,
    symbol SYMBOL CAPACITY 10000,        -- e.g., BTC/USDT:USDT
    data_type SYMBOL CAPACITY 256,       -- oi, funding, liquidation
    host SYMBOL CAPACITY 1000,
    env SYMBOL CAPACITY 256,

    -- Metrics
    records_count LONG,                  -- Records in this interval
    bytes_written LONG,                  -- Bytes written to storage
    latency_ms DOUBLE,                   -- Processing latency

    -- Quality
    gap_detected BOOLEAN,                -- Data gap detected
    gap_duration_seconds DOUBLE          -- Gap duration (if detected)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
```

**Python Dataclass**:
```python
@dataclass
class PipelineMetrics:
    timestamp: datetime
    exchange: str
    symbol: str
    data_type: str  # "oi", "funding", "liquidation"
    host: str
    env: str
    records_count: int
    bytes_written: int
    latency_ms: float
    gap_detected: bool = False
    gap_duration_seconds: float | None = None
```

**Validation Rules**:
- `data_type`: One of ["oi", "funding", "liquidation"]
- `records_count`: >= 0
- `bytes_written`: >= 0
- `latency_ms`: >= 0
- `gap_duration_seconds`: Only set if `gap_detected` is True

---

### 4. TradingMetrics

Real-time trading performance (future use).

**Table Schema (QuestDB)**:
```sql
CREATE TABLE trading_metrics (
    -- Designated timestamp
    timestamp TIMESTAMP NOT NULL,

    -- Dimensions
    strategy SYMBOL CAPACITY 1000,       -- Strategy identifier
    symbol SYMBOL CAPACITY 10000,
    venue SYMBOL CAPACITY 256,           -- binance, bybit
    env SYMBOL CAPACITY 256,

    -- Performance
    pnl DOUBLE,                          -- Realized PnL
    unrealized_pnl DOUBLE,               -- Unrealized PnL
    position_size DOUBLE,                -- Current position

    -- Activity
    orders_placed LONG,                  -- Orders placed in interval
    orders_filled LONG,                  -- Orders filled
    fill_rate DOUBLE,                    -- fill_rate = filled/placed

    -- Risk
    exposure DOUBLE,                     -- Total exposure
    drawdown DOUBLE                      -- Current drawdown %
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
```

**Python Dataclass**:
```python
@dataclass
class TradingMetrics:
    timestamp: datetime
    strategy: str
    symbol: str
    venue: str
    env: str
    pnl: float
    unrealized_pnl: float
    position_size: float
    orders_placed: int = 0
    orders_filled: int = 0
    fill_rate: float = 0.0
    exposure: float = 0.0
    drawdown: float = 0.0
```

---

### 5. AlertRule

Alert configuration (stored in Grafana provisioning).

**YAML Schema**:
```yaml
# Not stored in QuestDB - Grafana provisioning file
type: object
properties:
  uid:
    type: string
    description: Unique alert identifier
  title:
    type: string
    maxLength: 255
  condition:
    type: string
    enum: [A, B, C, D]  # Reference to data query
  threshold:
    type: number
  for_duration:
    type: string
    pattern: "^[0-9]+[smh]$"  # e.g., "5m", "1h"
  severity:
    type: string
    enum: [critical, warning, info]
  channels:
    type: array
    items:
      type: string
      enum: [telegram, discord, email]
```

**Python Dataclass**:
```python
@dataclass
class AlertRule:
    uid: str
    title: str
    condition: str  # Query reference
    threshold: float
    for_duration: str  # "5m", "1h"
    severity: str  # "critical", "warning", "info"
    channels: list[str]  # ["telegram", "discord", "email"]
```

---

### 6. Dashboard

Grafana dashboard definition (JSON).

**Structure** (stored as JSON files):
```json
{
  "uid": "string",
  "title": "string",
  "tags": ["string"],
  "timezone": "browser",
  "refresh": "5s",
  "panels": [
    {
      "id": "number",
      "title": "string",
      "type": "timeseries|stat|gauge|table",
      "datasource": "QuestDB",
      "targets": [{"expr": "SQL query"}],
      "fieldConfig": {}
    }
  ]
}
```

---

## Relationships

```
DaemonMetrics (host, env)
    │
    ├──1:N──► ExchangeStatus (per exchange)
    │
    └──1:N──► PipelineMetrics (per symbol, data_type)

TradingMetrics (independent, future integration)
    │
    └──N:1──► Strategy configuration
```

## Retention Policy

| Table | Partition | Retention | Drop Script |
|-------|-----------|-----------|-------------|
| daemon_metrics | DAY | 90 days | `ALTER TABLE daemon_metrics DROP PARTITION LIST '2025-09-27';` |
| exchange_status | DAY | 90 days | Same pattern |
| pipeline_metrics | DAY | 90 days | Same pattern |
| trading_metrics | DAY | 365 days | Same pattern |

**Automated Cleanup (QuestDB query)**:
```sql
-- Run daily via cron/scheduled job
ALTER TABLE daemon_metrics DROP PARTITION
WHERE timestamp < dateadd('d', -90, now());
```

## Query Examples

### Health Dashboard Queries

```sql
-- Current daemon status
SELECT * FROM daemon_metrics
WHERE host = 'prod-server-01'
ORDER BY timestamp DESC
LIMIT 1;

-- Fetch rate (per hour)
SELECT
    timestamp,
    fetch_count - lag(fetch_count) OVER (ORDER BY timestamp) as fetches_per_interval
FROM daemon_metrics
WHERE timestamp > now() - interval '24h'
SAMPLE BY 1h;

-- Error rate trend
SELECT
    timestamp,
    error_count
FROM daemon_metrics
WHERE timestamp > now() - interval '7d'
SAMPLE BY 1h;
```

### Exchange Dashboard Queries

```sql
-- Current exchange status
SELECT
    exchange,
    connected,
    latency_ms,
    last_message_at
FROM exchange_status
WHERE timestamp > now() - interval '1m'
LATEST BY exchange;

-- Reconnection events
SELECT
    timestamp,
    exchange,
    reconnect_count
FROM exchange_status
WHERE reconnect_count > 0
AND timestamp > now() - interval '24h'
ORDER BY timestamp DESC;
```

### Pipeline Dashboard Queries

```sql
-- Data throughput by exchange
SELECT
    exchange,
    sum(records_count) as total_records,
    sum(bytes_written) as total_bytes
FROM pipeline_metrics
WHERE timestamp > now() - interval '1h'
GROUP BY exchange;

-- Data gaps
SELECT
    timestamp,
    exchange,
    symbol,
    gap_duration_seconds
FROM pipeline_metrics
WHERE gap_detected = true
AND timestamp > now() - interval '24h'
ORDER BY timestamp DESC;
```

## Indexing Strategy

QuestDB uses designated timestamp as primary index. Additional optimizations:

1. **SYMBOL columns**: Automatic dictionary encoding for low-cardinality fields
2. **DEDUP UPSERT KEYS**: Prevents duplicate records per unique key combination
3. **WAL (Write-Ahead Log)**: Enables concurrent writes without blocking queries

No additional indexes needed - QuestDB optimizes time-series queries automatically.
