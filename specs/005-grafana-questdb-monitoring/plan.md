# Implementation Plan: Grafana + QuestDB Production Monitoring

**Feature Branch**: `005-grafana-questdb-monitoring`
**Created**: 2025-12-26
**Status**: Ready for Implementation
**Spec Reference**: `specs/005-grafana-questdb-monitoring/spec.md`

## Architecture Overview

### System Context

The monitoring stack integrates with the existing CCXT data pipeline (Spec 001) to provide real-time visibility into daemon health, exchange connectivity, and data pipeline throughput. Grafana serves as the visualization layer with QuestDB as the high-performance time-series backend.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Production Environment                           │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐       │
│  │   DaemonRunner  │   │  Metrics        │   │   Trading       │       │
│  │   (Spec 001)    │──▶│  Collector      │◀──│   Strategies    │       │
│  └─────────────────┘   └────────┬────────┘   └─────────────────┘       │
│                                 │                                        │
│                                 │ ILP over HTTP                          │
│                                 ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        Monitoring Stack                           │  │
│  │  ┌─────────────────────────────────────────────────────────────┐ │  │
│  │  │                       Grafana :3000                          │ │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │ │  │
│  │  │  │ Health   │  │ Pipeline │  │ Exchange │  │ Trading  │    │ │  │
│  │  │  │Dashboard │  │Dashboard │  │Dashboard │  │Dashboard │    │ │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │ │  │
│  │  └───────────────────────────┬─────────────────────────────────┘ │  │
│  │                              │ PostgreSQL wire protocol          │  │
│  │  ┌───────────────────────────▼─────────────────────────────────┐ │  │
│  │  │                     QuestDB :9000/:8812                      │ │  │
│  │  │  • daemon_metrics    • exchange_status                       │ │  │
│  │  │  • pipeline_metrics  • trading_metrics                       │ │  │
│  │  └───────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                 │                                        │
│                                 ▼ Alerts                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │   Telegram   │   Discord   │   Email                              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      metrics_collector.py                        │
│  ┌─────────────────┐   ┌─────────────────┐   ┌───────────────┐  │
│  │ DaemonCollector │   │ ExchangeCollector│   │ PipelineCollector│
│  └────────┬────────┘   └────────┬────────┘   └───────┬───────┘  │
│           └────────────────┬────┴───────────────────┘           │
│                            │                                     │
│                    ┌───────▼────────┐                            │
│                    │ MetricsClient  │                            │
│                    │ (questdb lib)  │                            │
│                    └───────┬────────┘                            │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             ▼ HTTP ILP
                     ┌───────────────┐
                     │   QuestDB     │
                     │   Tables      │
                     └───────────────┘
```

## Technical Decisions

### Decision 1: Time-Series Database

**Options Considered**:
1. **QuestDB** (Selected)
   - Pros: High throughput (100K+ writes/sec), native ILP support, PostgreSQL protocol
   - Cons: Less mature ecosystem than InfluxDB
2. **InfluxDB**
   - Pros: Mature, large community
   - Cons: Higher resource usage, commercial licensing concerns
3. **TimescaleDB**
   - Pros: PostgreSQL-based, familiar SQL
   - Cons: Heavier setup, more operational overhead

**Selected**: QuestDB

**Rationale**: Community-endorsed for NautilusTrader (Discord recommendation), optimal performance for trading metrics, native Grafana plugin available.

---

### Decision 2: Metrics Ingestion Protocol

**Options Considered**:
1. **HTTP ILP** (Selected)
   - Pros: Error feedback, automatic retries, batching support
   - Cons: Slightly higher overhead than TCP
2. **TCP ILP**
   - Pros: Lower overhead
   - Cons: No error feedback, legacy approach
3. **REST API**
   - Pros: Full error handling
   - Cons: Lowest throughput

**Selected**: HTTP ILP

**Rationale**: Error feedback critical for reliability, Python client `questdb>=4.1.0` provides excellent HTTP ILP support with nanosecond precision.

---

### Decision 3: Alerting System

**Options Considered**:
1. **Grafana Unified Alerting** (Selected)
   - Pros: Single system, file-based provisioning, multi-channel support
   - Cons: Requires Grafana 9+
2. **Alertmanager**
   - Pros: Prometheus-native, mature
   - Cons: Additional container, more complex routing

**Selected**: Grafana Unified Alerting

**Rationale**: Simplifies deployment, supports all required channels (Telegram, Discord, Email), integrates with dashboard provisioning.

---

## Implementation Strategy

### Phase 1: Infrastructure Setup

**Goal**: Deploy QuestDB + Grafana stack with Docker Compose

**Deliverables**:
- [x] `monitoring/docker-compose.yml` - Multi-container orchestration
- [x] `monitoring/questdb/server.conf` - QuestDB configuration
- [x] `monitoring/grafana/provisioning/datasources/questdb.yaml` - Data source config
- [x] `monitoring/.env.example` - Environment variables template

**Dependencies**: Docker, Docker Compose

---

### Phase 2: Metrics Collector

**Goal**: Implement Python metrics collector for DaemonRunner integration

**Deliverables**:
- [ ] `monitoring/metrics_collector.py` - Collector module
- [ ] `monitoring/models.py` - Pydantic models for metrics
- [ ] `monitoring/client.py` - QuestDB client wrapper
- [ ] Integration hook in DaemonRunner

**Dependencies**: Phase 1, Spec 001 (DaemonRunner)

---

### Phase 3: Dashboard Provisioning

**Goal**: Create pre-built dashboards for all metrics

**Deliverables**:
- [ ] `monitoring/grafana/dashboards/health.json` - Health dashboard
- [ ] `monitoring/grafana/dashboards/pipeline.json` - Pipeline dashboard
- [ ] `monitoring/grafana/dashboards/exchange.json` - Exchange dashboard
- [ ] `monitoring/grafana/provisioning/dashboards/default.yaml` - Provider config

**Dependencies**: Phase 1

---

### Phase 4: Alerting Configuration

**Goal**: Configure alerts for critical conditions

**Deliverables**:
- [ ] `monitoring/grafana/provisioning/alerting/alert-rules.yaml` - Alert rules
- [ ] `monitoring/grafana/provisioning/alerting/contact-points.yaml` - Notification channels
- [ ] `monitoring/grafana/provisioning/alerting/policies.yaml` - Routing policies

**Dependencies**: Phase 3

---

### Phase 5: Integration & Testing

**Goal**: End-to-end integration testing

**Deliverables**:
- [ ] `tests/monitoring/test_collector.py` - Collector unit tests
- [ ] `tests/monitoring/test_integration.py` - Integration tests
- [ ] Documentation updates

**Dependencies**: Phases 2, 3, 4

---

## File Structure

```
monitoring/
├── docker-compose.yml            # Container orchestration
├── .env.example                  # Environment template
├── questdb/
│   └── server.conf               # QuestDB configuration
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── questdb.yaml      # QuestDB data source
│   │   ├── dashboards/
│   │   │   └── default.yaml      # Dashboard provider
│   │   └── alerting/
│   │       ├── alert-rules.yaml
│   │       ├── contact-points.yaml
│   │       └── policies.yaml
│   └── dashboards/
│       ├── health.json
│       ├── pipeline.json
│       ├── exchange.json
│       └── trading.json          # Future
├── metrics_collector.py          # Collector implementation
├── models.py                     # Pydantic models
└── client.py                     # QuestDB client wrapper

tests/
└── monitoring/
    ├── test_collector.py
    └── test_integration.py
```

## API Design

### Metrics Client Interface

```python
from dataclasses import dataclass
from datetime import datetime
from questdb.ingress import Sender

class MetricsClient:
    """Thread-safe QuestDB metrics client with batching."""

    def __init__(self, host: str = "localhost", port: int = 9000) -> None:
        self._sender = Sender.from_conf(f"http::addr={host}:{port}")

    def send_daemon_metrics(self, metrics: DaemonMetrics) -> None:
        """Send daemon health metrics."""
        self._sender.row(
            "daemon_metrics",
            symbols={"host": metrics.host, "env": metrics.env},
            columns={
                "fetch_count": metrics.fetch_count,
                "error_count": metrics.error_count,
                "liquidation_count": metrics.liquidation_count,
                "uptime_seconds": metrics.uptime_seconds,
                "running": metrics.running,
            },
            at=int(metrics.timestamp.timestamp() * 1e9)
        )

    def send_exchange_status(self, status: ExchangeStatus) -> None:
        """Send exchange connectivity status."""
        ...

    def flush(self) -> None:
        """Flush pending metrics to QuestDB."""
        self._sender.flush()

    def close(self) -> None:
        """Close the connection."""
        self._sender.close()
```

### Configuration

```python
from pydantic import BaseModel, Field

class MonitoringConfig(BaseModel):
    """Monitoring stack configuration."""

    questdb_host: str = "localhost"
    questdb_port: int = 9000
    batch_size: int = 500
    flush_interval_seconds: float = 1.0
    env: str = Field(default="dev", pattern="^(prod|staging|dev)$")

    # Alert thresholds
    error_rate_threshold: int = 10  # errors per minute
    latency_threshold_ms: float = 500.0
    disconnect_alert_minutes: int = 5
```

## Testing Strategy

### Unit Tests
- [x] Test DaemonMetrics model validation
- [x] Test ExchangeStatus model validation
- [x] Test PipelineMetrics model validation
- [ ] Test MetricsClient initialization
- [ ] Test MetricsClient batching behavior
- [ ] Test MetricsClient error handling

### Integration Tests
- [ ] Test QuestDB write/query cycle
- [ ] Test Grafana dashboard loading
- [ ] Test alert rule evaluation
- [ ] Test notification delivery (mocked)

### Performance Tests
- [ ] Benchmark: 10,000 writes/second sustained
- [ ] Benchmark: Dashboard load < 3 seconds
- [ ] Benchmark: Query latency < 100ms

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| QuestDB data loss | High | Low | WAL enabled, daily backups |
| Alert storm | Medium | Medium | Group alerts, rate limiting |
| High memory usage | Medium | Low | Partitioning, retention policy |
| Network partition | High | Low | Retry with exponential backoff |
| Grafana downtime | Low | Low | Dashboards persist in volumes |

## Dependencies

### External Dependencies
- Docker >= 24.0
- Docker Compose >= 2.0
- QuestDB >= 9.2.3
- Grafana >= 11.0.0
- questdb (Python) >= 4.1.0
- pydantic >= 2.0

### Internal Dependencies
- Spec 001: CCXT Data Pipeline (DaemonRunner.get_status())

## Constitution Check

### Compliance

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | MetricsClient encapsulates QuestDB complexity |
| KISS & YAGNI | ✅ | Minimal stack, no log aggregation or tracing |
| Native First | ✅ | Using questdb Python client, not custom ILP |
| No df.iterrows() | ✅ | Streaming metrics, not DataFrame processing |
| TDD Discipline | 🔲 | Tests planned for Phase 5 |

### Quality Gates

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Performance benchmarks met (10K writes/sec)

## Acceptance Criteria

From spec:

- [ ] SC-001: Metrics ingestion latency < 1 second
- [ ] SC-002: Dashboard load time < 3 seconds
- [ ] SC-003: Alert notification delivery < 60 seconds
- [ ] SC-004: QuestDB handles 10,000 writes/second sustained
- [ ] SC-005: 90-day data retention with < 10GB storage

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Research | `specs/005-grafana-questdb-monitoring/research.md` | ✅ Complete |
| Data Model | `specs/005-grafana-questdb-monitoring/data-model.md` | ✅ Complete |
| API Contract | `specs/005-grafana-questdb-monitoring/contracts/metrics-api.yaml` | ✅ Complete |
| Grafana Contract | `specs/005-grafana-questdb-monitoring/contracts/grafana-provisioning.yaml` | ✅ Complete |
| Quickstart | `specs/005-grafana-questdb-monitoring/quickstart.md` | ✅ Complete |
