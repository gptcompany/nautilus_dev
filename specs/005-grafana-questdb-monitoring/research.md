# Research: Grafana + QuestDB Production Monitoring

**Feature**: 005-grafana-questdb-monitoring
**Created**: 2025-12-26
**Status**: Complete

## Research Summary

### Decision 1: Time-Series Database Selection

**Decision**: QuestDB

**Rationale**:
- Community-endorsed solution for NautilusTrader (Discord: @fudgemin recommendation)
- Native support for InfluxDB Line Protocol (ILP) - efficient for high-throughput metrics
- PostgreSQL wire protocol - Grafana has native support
- Handles 10,000+ writes/second sustained (meets SC-004)
- Nanosecond timestamp precision (critical for trading metrics)

**Alternatives Considered**:
- **InfluxDB**: Higher resource usage, commercial licensing concerns
- **TimescaleDB**: PostgreSQL-based (good), but heavier setup
- **Prometheus**: Pull-based model, better for infrastructure than trading metrics

### Decision 2: Metrics Ingestion Protocol

**Decision**: HTTP-based ILP (InfluxDB Line Protocol over HTTP)

**Rationale**:
- Error feedback and automatic retries (critical for reliability)
- Batching support (500-1000 rows optimal for throughput)
- Auto-detects protocol version (v2 for QuestDB 9.0+)
- Python client `questdb` v4.1.0+ supports DataFrame ingestion

**Alternatives Considered**:
- **TCP ILP**: Lower overhead but no error feedback, legacy
- **REST API**: Full feedback but lowest throughput

### Decision 3: Python Metrics Library

**Decision**: `questdb` Python client (v4.1.0+)

**Rationale**:
- Official library with HTTP transport support
- Nanosecond timestamp support (v4.0.0+)
- Native DataFrame ingestion (orders of magnitude faster)
- Automatic batching and retry logic

**Code Pattern**:
```python
from questdb.ingress import Sender

sender = Sender.from_conf("http::addr=questdb:9000")
sender.row(
    "daemon_metrics",
    symbols={"exchange": "binance", "env": "prod"},
    columns={"fetch_count": 100, "error_count": 0},
    at=int(time.time() * 1e9)  # Nanosecond timestamp
)
sender.flush()
```

### Decision 4: Grafana Provisioning Strategy

**Decision**: File-based provisioning (YAML/JSON)

**Rationale**:
- Infrastructure as Code (IaC) - version controlled
- Dashboard definitions in JSON, provider configs in YAML
- Supports folder organization via `foldersFromFilesStructure`
- Git Sync experimental in v12 for future enhancement

**Directory Structure**:
```
grafana/
├── provisioning/
│   ├── dashboards/default.yaml    # Provider config
│   ├── datasources/questdb.yaml   # QuestDB connection
│   └── alerting/alert-rules.yaml  # Alert definitions
└── dashboards/
    ├── health.json
    ├── pipeline.json
    ├── exchange.json
    └── trading.json
```

### Decision 5: Alerting Strategy

**Decision**: Grafana Unified Alerting (native)

**Rationale**:
- Single alerting system for all data sources
- Supports Telegram, Discord, Email (FR-009)
- File-based provisioning (YAML)
- Recovery notifications supported

**Alternatives Considered**:
- **Alertmanager**: Requires additional container, more complex
- **Custom alerting**: Development overhead, maintenance burden

### Decision 6: DaemonRunner Integration Pattern

**Decision**: Poll `get_status()` method

**Rationale**:
- Zero modifications needed to DaemonRunner
- All metrics exposed via `DaemonRunner.get_status()`:
  - `running`, `shutdown_requested` (state)
  - `fetch_count`, `error_count`, `liquidation_count` (counters)
  - `uptime_seconds`, `last_fetch_time`, `last_error` (status)
  - `symbols`, `exchanges` (configuration)

**Integration Pattern**:
```python
# External metrics collector polls DaemonRunner
status = daemon_runner.get_status()
sender.row(
    "daemon_metrics",
    symbols={"exchange": ",".join(status["exchanges"])},
    columns={
        "fetch_count": status["fetch_count"],
        "error_count": status["error_count"],
        "liquidation_count": status["liquidation_count"],
        "uptime_seconds": status["uptime_seconds"],
    },
    at=int(time.time() * 1e9)
)
```

### Decision 7: Schema Design

**Decision**: SYMBOL columns for tags, designated timestamp

**Rationale**:
- SYMBOL type stores values as integers (8 bytes max)
- ~100x smaller storage vs VARCHAR for repeated values
- Designated timestamp enables partitioning and query optimization

**Schema Pattern**:
```sql
CREATE TABLE daemon_metrics (
  timestamp TIMESTAMP NOT NULL,
  host SYMBOL CAPACITY 50000,
  exchange SYMBOL CAPACITY 256,
  env SYMBOL CAPACITY 256,
  fetch_count LONG,
  error_count LONG,
  liquidation_count LONG,
  uptime_seconds DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
```

## Technical Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Docker | >= 24.0 | Container runtime |
| Docker Compose | >= 2.0 | Multi-container orchestration |
| QuestDB | >= 9.2.3 | Time-series storage |
| Grafana | >= 11.0.0 | Visualization & alerting |
| questdb (Python) | >= 4.1.0 | Metrics ingestion |
| questdb-questdb-datasource | latest | Grafana plugin |

## Edge Cases Identified

| Edge Case | Mitigation Strategy |
|-----------|---------------------|
| QuestDB down | Health check endpoint, retry with exponential backoff |
| Grafana restart | Dashboard persistence via provisioning + volumes |
| High ingestion rate | Batching (500-1000 rows), WAL configuration |
| Timezone differences | Store UTC timestamps, Grafana browser timezone |
| Long retention (1+ year) | Daily partitioning, automatic partition drop |

## Discord Community Insights

Source: `docs/discord/questions.md` (lines 245-275)

Key recommendation from @fudgemin:
> "Data ingestion is through QuestDB, simple query to the database with grafana... I dont think... i could not replicate the same thing, anywhere else, in such a fast manner, while having it remain dynamic and scalable."

Community patterns:
- **No built-in monitoring** in NautilusTrader
- **QuestDB + Grafana** is the community-endorsed solution
- **Integration pattern**: Write strategy metrics to QuestDB, query via Grafana
- **Setup time**: 1-2 days to get operational
- **Key advantage**: "One and done" - works across any strategy/backtest

## Performance Targets

From spec success criteria:

| Metric | Target | QuestDB Capability |
|--------|--------|-------------------|
| SC-001: Ingestion latency | < 1s | ~1ms with HTTP ILP |
| SC-002: Dashboard load | < 3s | Depends on query complexity |
| SC-003: Alert delivery | < 60s | ~5s with Grafana Unified |
| SC-004: Write throughput | 10,000/s | 100,000+/s sustained |
| SC-005: 90-day retention | < 10GB | ~2-5GB with SYMBOL compression |

## QuestDB Configuration Recommendations

```ini
# server.conf optimizations for trading metrics
cairo.wal.enabled=true
cairo.max.uncommitted.rows=100000
cairo.o3.max.lag.transition.time=1800000  # 30min WAL lag
cairo.o3.commit.lag=300000                 # 5min commit
http.enabled=true
pg.enabled=true                            # For Grafana queries
line.http.net.accept.workers=16
line.http.net.rw.workers=32
```

## References

### Official Documentation
- [QuestDB ILP Overview](https://questdb.com/docs/reference/api/ilp/overview/)
- [QuestDB Python Client](https://questdb.com/docs/clients/ingest-python/)
- [QuestDB Schema Design](https://questdb.com/docs/guides/schema-design-essentials/)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Grafana Alerting Best Practices](https://grafana.com/docs/grafana/latest/alerting/best-practices/)

### Community Sources
- [QuestDB + Grafana Dashboard Blog](https://questdb.com/blog/time-series-monitoring-dashboard-grafana-questdb/)
- NautilusTrader Discord (questions channel, lines 245-275)
