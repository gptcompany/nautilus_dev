# Feature Specification: Grafana + QuestDB Production Monitoring

**Feature Branch**: `005-grafana-questdb-monitoring`
**Created**: 2025-12-25
**Status**: Draft
**Input**: Community recommendation: "This visual setup works across any strategy or backtest results I post to my database. It's once and done"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Infrastructure Health Dashboard (Priority: P1)

As a DevOps engineer, I need to monitor the health of all trading infrastructure components so that I can detect and resolve issues before they impact trading.

**Why this priority**: Core monitoring - if infra is down, nothing works.

**Independent Test**: Start DaemonRunner, verify metrics appear in Grafana within 30 seconds.

**Acceptance Scenarios**:

1. **Given** DaemonRunner is running, **When** viewing health dashboard, **Then** shows uptime, memory, CPU usage
2. **Given** WebSocket disconnection, **When** viewing dashboard, **Then** shows disconnected status with timestamp
3. **Given** API endpoint error, **When** viewing dashboard, **Then** shows error rate spike with alert

---

### User Story 2 - Data Pipeline Metrics (Priority: P1)

As an operator, I need to monitor the CCXT data pipeline so that I can ensure data quality and completeness.

**Why this priority**: Data is the foundation - bad data = bad trading decisions.

**Independent Test**: Run daemon for 1 hour, verify OI/Funding fetch counts match expected.

**Acceptance Scenarios**:

1. **Given** daemon running, **When** viewing pipeline dashboard, **Then** shows fetch counts per exchange
2. **Given** data gap detected, **When** viewing dashboard, **Then** shows gap duration and affected symbols
3. **Given** liquidation burst, **When** viewing dashboard, **Then** shows events/minute with aggregation

---

### User Story 3 - Exchange Connectivity (Priority: P1)

As an operator, I need to monitor connectivity to each exchange so that I can react to outages.

**Why this priority**: Exchange downtime directly impacts trading.

**Independent Test**: Simulate Binance disconnect, verify alert fires within 60 seconds.

**Acceptance Scenarios**:

1. **Given** all exchanges connected, **When** viewing connectivity panel, **Then** shows green status for each
2. **Given** exchange disconnect, **When** 5 minutes pass, **Then** alert notification sent
3. **Given** reconnection, **When** viewing timeline, **Then** shows downtime duration

---

### User Story 4 - Alerting System (Priority: P2)

As an operator, I need configurable alerts so that I'm notified of critical issues immediately.

**Why this priority**: Proactive notification prevents extended outages.

**Independent Test**: Trigger memory threshold, verify alert sent to configured channel.

**Acceptance Scenarios**:

1. **Given** alert rule configured, **When** threshold exceeded, **Then** notification sent (email/Telegram/Discord)
2. **Given** alert firing, **When** condition resolves, **Then** recovery notification sent
3. **Given** multiple alerts, **When** viewing alert dashboard, **Then** shows alert history with status

---

### User Story 5 - Trading Performance Metrics (Priority: P2)

As a trader, I need to see real-time trading performance so that I can monitor live strategies.

**Why this priority**: Important for live trading, but requires live infrastructure first.

**Independent Test**: Run live strategy, verify PnL updates in dashboard within 5 seconds.

**Acceptance Scenarios**:

1. **Given** live strategy running, **When** viewing performance dashboard, **Then** shows real-time PnL
2. **Given** orders being placed, **When** viewing orders panel, **Then** shows orders/minute rate
3. **Given** positions open, **When** viewing positions panel, **Then** shows current exposure per symbol

---

### User Story 6 - Historical Analysis Queries (Priority: P3)

As a quant, I need to query historical metrics so that I can analyze long-term patterns.

**Why this priority**: Advanced analysis, requires data accumulation first.

**Independent Test**: Query 30 days of OI data, verify results return in < 2 seconds.

**Acceptance Scenarios**:

1. **Given** 30 days of data, **When** querying via Grafana Explore, **Then** results return quickly
2. **Given** custom SQL query, **When** executed in QuestDB console, **Then** can export to CSV
3. **Given** time range selection, **When** zooming dashboard, **Then** all panels update accordingly

---

### Edge Cases

- What happens when QuestDB is down?
- How to handle Grafana restart (dashboard persistence)?
- What if metrics ingestion rate exceeds QuestDB capacity?
- How to handle timezone differences in dashboards?
- What happens with very long retention (1+ year)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST deploy QuestDB for time-series metrics storage
- **FR-002**: System MUST deploy Grafana for visualization
- **FR-003**: System MUST ingest DaemonRunner metrics (uptime, fetch counts, errors)
- **FR-004**: System MUST ingest exchange connectivity status
- **FR-005**: System MUST ingest OI/Funding/Liquidation event counts
- **FR-006**: System MUST provide pre-built dashboards (Health, Pipeline, Exchange, Trading)
- **FR-007**: System MUST support configurable alerts (thresholds, channels)
- **FR-008**: System MUST retain metrics for minimum 90 days
- **FR-009**: System MUST support Telegram/Discord/Email notifications
- **FR-010**: System MUST provide Docker Compose deployment
- **FR-011**: System MUST expose Prometheus-compatible metrics endpoint
- **FR-012**: System MUST support dashboard provisioning (IaC)

### Key Entities

- **Metric**: Time-series data point (timestamp, name, value, labels)
- **Dashboard**: Grafana dashboard definition (JSON)
- **Alert**: Alert rule with threshold and notification channel
- **DataSource**: QuestDB connection configuration
- **Panel**: Individual visualization within dashboard

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Metrics ingestion latency < 1 second
- **SC-002**: Dashboard load time < 3 seconds
- **SC-003**: Alert notification delivery < 60 seconds from trigger
- **SC-004**: QuestDB handles 10,000 writes/second sustained
- **SC-005**: 90-day data retention with < 10GB storage

## Assumptions

- Docker and Docker Compose available
- Network access to send notifications (Telegram/Discord/Email)
- DaemonRunner from Spec 001 provides metrics hook
- Sufficient disk space for QuestDB (10GB+)

## Dependencies

- Docker >= 24.0
- Docker Compose >= 2.0
- QuestDB >= 9.2.3
- Grafana >= 11.0.0
- questdb (Python) >= 4.1.0
- Spec 001: CCXT Pipeline (metrics source)

## Out of Scope

- Log aggregation (ELK stack)
- Distributed tracing (Jaeger)
- Kubernetes deployment (Docker only)
- Custom Grafana plugins
- Multi-tenant dashboards

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Monitoring Stack                             │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                      Grafana                                 │ │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │ │
│  │   │ Health   │  │ Pipeline │  │ Exchange │  │ Trading  │   │ │
│  │   │Dashboard │  │Dashboard │  │Dashboard │  │Dashboard │   │ │
│  │   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │ │
│  │        └─────────────┴─────────────┴─────────────┘         │ │
│  │                          │                                   │ │
│  │                    ┌─────▼─────┐                            │ │
│  │                    │  QuestDB  │                            │ │
│  │                    │(DataSource)│                            │ │
│  │                    └─────┬─────┘                            │ │
│  └──────────────────────────┼──────────────────────────────────┘ │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │    QuestDB        │
                    │  (Time-Series DB) │
                    │   Port: 9000      │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
      ┌───────▼───────┐ ┌─────▼─────┐ ┌───────▼───────┐
      │ DaemonRunner  │ │ Metrics   │ │ Trading       │
      │ (Spec 001)    │ │ Exporter  │ │ Strategies    │
      │               │ │           │ │               │
      └───────────────┘ └───────────┘ └───────────────┘
```

## Dashboard Panels

### Health Dashboard
- System uptime
- Memory usage (current + trend)
- CPU usage
- Process restarts count
- Last error timestamp

### Pipeline Dashboard
- OI fetches/hour (per exchange)
- Funding fetches/hour
- Liquidations/minute
- Data gaps timeline
- Parquet storage size

### Exchange Dashboard
- Connection status (per exchange)
- WebSocket latency
- Reconnection count
- Last message timestamp
- Rate limit status

### Trading Dashboard (Future)
- Real-time PnL
- Orders/minute
- Fill rate
- Position exposure
- Open orders count
