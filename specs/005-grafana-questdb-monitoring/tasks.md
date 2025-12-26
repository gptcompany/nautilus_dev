# Tasks: Grafana + QuestDB Production Monitoring

**Input**: Design documents from `/specs/005-grafana-questdb-monitoring/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Not explicitly requested - test tasks omitted per spec.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

Include exact file paths in descriptions.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Docker Compose stack initialization and base configuration

- [X] T001 Create monitoring directory structure per implementation plan
- [X] T002 Create Docker Compose configuration in monitoring/docker-compose.yml
- [X] T003 [P] Create QuestDB server configuration in monitoring/questdb/server.conf
- [X] T004 [P] Create environment variables template in monitoring/.env.example
- [X] T005 Create Grafana data source provisioning in monitoring/grafana/provisioning/datasources/questdb.yaml
- [X] T006 Create dashboard provider configuration in monitoring/grafana/provisioning/dashboards/default.yaml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Python modules that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational (TDD: Write FIRST, ensure FAIL)

- [X] T007 [P] Write unit tests for DaemonMetrics model validation in tests/monitoring/test_models.py
- [X] T008 [P] Write unit tests for ExchangeStatus model validation in tests/monitoring/test_models.py
- [X] T009 [P] Write unit tests for PipelineMetrics model validation in tests/monitoring/test_models.py
- [X] T010 Write unit tests for MetricsClient in tests/monitoring/test_client.py

### Implementation for Foundational

- [X] T011 Create Pydantic models for all metrics in monitoring/models.py
- [X] T012 Create MonitoringConfig Pydantic model in monitoring/config.py
- [X] T013 Create QuestDB MetricsClient wrapper in monitoring/client.py
- [X] T014 Create base collector interface in monitoring/collectors/__init__.py

**Checkpoint**: Foundation ready - all tests pass, user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Infrastructure Health Dashboard (Priority: P1) 🎯 MVP

**Goal**: Monitor health of all trading infrastructure components (uptime, memory, CPU, errors)

**Independent Test**: Start DaemonRunner, verify metrics appear in Grafana within 30 seconds

### Implementation for User Story 1

- [X] T011 [US1] Create DaemonCollector class in monitoring/collectors/daemon.py
- [X] T012 [US1] Implement DaemonRunner.get_status() polling in monitoring/collectors/daemon.py
- [X] T013 [US1] Create daemon_metrics table schema SQL in monitoring/schemas/daemon_metrics.sql
- [X] T014 [US1] Create Health Dashboard JSON definition in monitoring/grafana/dashboards/health.json
- [X] T015 [US1] Add uptime panel to Health Dashboard
- [X] T016 [US1] Add memory/CPU usage panels to Health Dashboard
- [X] T017 [US1] Add error rate panel with threshold markers to Health Dashboard
- [X] T018 [US1] Add last error timestamp panel to Health Dashboard

**Checkpoint**: At this point, User Story 1 should be fully functional - daemon health visible in Grafana

---

## Phase 4: User Story 2 - Data Pipeline Metrics (Priority: P1)

**Goal**: Monitor CCXT data pipeline throughput (OI/Funding fetch counts, data gaps, liquidations)

**Independent Test**: Run daemon for 1 hour, verify OI/Funding fetch counts match expected

### Implementation for User Story 2

- [X] T019 [US2] Create PipelineCollector class in monitoring/collectors/pipeline.py
- [X] T020 [US2] Implement fetch_count tracking per exchange in monitoring/collectors/pipeline.py
- [X] T021 [US2] Implement data gap detection logic in monitoring/collectors/pipeline.py
- [X] T022 [US2] Create pipeline_metrics table schema SQL in monitoring/schemas/pipeline_metrics.sql
- [X] T023 [US2] Create Pipeline Dashboard JSON definition in monitoring/grafana/dashboards/pipeline.json
- [X] T024 [US2] Add OI fetches/hour panel (per exchange) to Pipeline Dashboard
- [X] T025 [US2] Add Funding fetches/hour panel to Pipeline Dashboard
- [X] T026 [US2] Add Liquidations/minute panel with aggregation to Pipeline Dashboard
- [X] T027 [US2] Add data gaps timeline panel to Pipeline Dashboard
- [X] T028 [US2] Add Parquet storage size panel to Pipeline Dashboard

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Exchange Connectivity (Priority: P1)

**Goal**: Monitor connectivity to each exchange (status, latency, reconnections)

**Independent Test**: Simulate Binance disconnect, verify status changes in dashboard within 30 seconds

### Implementation for User Story 3

- [X] T029 [US3] Create ExchangeCollector class in monitoring/collectors/exchange.py
- [X] T030 [US3] Implement WebSocket connection status tracking in monitoring/collectors/exchange.py
- [X] T031 [US3] Implement latency measurement in monitoring/collectors/exchange.py
- [X] T032 [US3] Implement reconnection counter in monitoring/collectors/exchange.py
- [X] T033 [US3] Create exchange_status table schema SQL in monitoring/schemas/exchange_status.sql
- [X] T034 [US3] Create Exchange Dashboard JSON definition in monitoring/grafana/dashboards/exchange.json
- [X] T035 [US3] Add connection status panel (traffic light per exchange) to Exchange Dashboard
- [X] T036 [US3] Add WebSocket latency panel to Exchange Dashboard
- [X] T037 [US3] Add reconnection count panel to Exchange Dashboard
- [X] T038 [US3] Add last message timestamp panel to Exchange Dashboard
- [X] T039 [US3] Add downtime timeline panel to Exchange Dashboard

**Checkpoint**: All P1 user stories now independently functional

---

## Phase 6: User Story 4 - Alerting System (Priority: P2)

**Goal**: Configurable alerts with multi-channel notifications (Telegram, Discord, Email)

**Independent Test**: Trigger memory threshold, verify alert sent to configured channel within 60 seconds

### Implementation for User Story 4

- [X] T040 [US4] Create alert rules YAML for daemon health in monitoring/grafana/provisioning/alerting/alert-rules.yaml
- [X] T041 [US4] Add exchange connectivity alert rules to alert-rules.yaml
- [X] T042 [US4] Add data pipeline gap alert rules to alert-rules.yaml
- [X] T043 [US4] Create contact points configuration in monitoring/grafana/provisioning/alerting/contact-points.yaml
- [X] T044 [US4] Configure Telegram notification channel in contact-points.yaml
- [X] T045 [US4] Configure Discord notification channel in contact-points.yaml
- [X] T046 [US4] Configure Email notification channel in contact-points.yaml
- [X] T047 [US4] Create notification routing policies in monitoring/grafana/provisioning/alerting/policies.yaml
- [X] T048 [US4] Implement severity-based routing (critical → all channels, warning → Telegram only)

**Checkpoint**: At this point, alerting system is functional for all metrics

---

## Phase 7: User Story 5 - Trading Performance Metrics (Priority: P2)

**Goal**: Real-time trading performance monitoring (PnL, orders, positions)

**Independent Test**: Run live strategy, verify PnL updates in dashboard within 5 seconds

### Implementation for User Story 5

- [X] T049 [US5] Create TradingCollector class in monitoring/collectors/trading.py
- [X] T050 [US5] Implement real-time PnL tracking in monitoring/collectors/trading.py
- [X] T051 [US5] Implement orders/minute rate calculation in monitoring/collectors/trading.py
- [X] T052 [US5] Implement position exposure tracking in monitoring/collectors/trading.py
- [X] T053 [US5] Create trading_metrics table schema SQL in monitoring/schemas/trading_metrics.sql
- [X] T054 [US5] Create Trading Dashboard JSON definition in monitoring/grafana/dashboards/trading.json
- [X] T055 [US5] Add real-time PnL panel to Trading Dashboard
- [X] T056 [US5] Add orders/minute rate panel to Trading Dashboard
- [X] T057 [US5] Add position exposure panel (per symbol) to Trading Dashboard
- [X] T058 [US5] Add fill rate panel to Trading Dashboard
- [X] T059 [US5] Add drawdown panel to Trading Dashboard

**Checkpoint**: Trading performance metrics now visible in real-time

---

## Phase 8: User Story 6 - Historical Analysis Queries (Priority: P3)

**Goal**: Fast historical metric queries for long-term analysis (30+ days)

**Independent Test**: Query 30 days of OI data, verify results return in < 2 seconds

### Implementation for User Story 6

- [X] T060 [US6] Configure QuestDB partitioning strategy for 90-day retention in monitoring/questdb/server.conf
- [X] T061 [US6] Create retention policy script in monitoring/scripts/retention_cleanup.py
- [X] T062 [US6] Add time range variable to all dashboards for flexible querying
- [X] T063 [US6] Optimize dashboard queries for large time ranges using SAMPLE BY
- [X] T064 [US6] Create CSV export query examples in monitoring/scripts/export_queries.sql
- [X] T065 [US6] Add Grafana Explore documentation section to quickstart.md

**Checkpoint**: Historical analysis queries now performant across all dashboards

---

## Phase 9: Integration & Polish

**Purpose**: End-to-end integration and cross-cutting concerns

- [X] T066 Create main metrics collector entry point in monitoring/metrics_collector.py
- [X] T067 Implement collector orchestration (all collectors running together) in monitoring/metrics_collector.py
- [X] T068 Implement batch flushing strategy (500-1000 rows per flush) in monitoring/client.py
- [X] T069 [P] Expose Prometheus-compatible /metrics endpoint in monitoring/metrics_collector.py (FR-011)
- [X] T070 Create startup health check script in monitoring/scripts/healthcheck.sh
- [X] T071 Update quickstart.md with complete setup instructions
- [X] T072 Create docker-compose commands reference in monitoring/README.md
- [X] T073 Verify all dashboards load in < 3 seconds (SC-002)
- [X] T074 Verify 10,000 writes/second sustained (SC-004)
- [X] T075 Run alpha-debug verification on monitoring/client.py
- [X] T076 Run alpha-debug verification on monitoring/collectors/*.py

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1, US2, US3 (P1): Can proceed in parallel after Foundational
  - US4 (P2): Can start after at least one P1 story has dashboards
  - US5 (P2): Can start after Foundational
  - US6 (P3): Can start after at least one dashboard exists
- **Integration (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

| User Story | Priority | Depends On | Can Start After |
|------------|----------|------------|-----------------|
| US1 - Health Dashboard | P1 | Foundational | Phase 2 complete |
| US2 - Pipeline Metrics | P1 | Foundational | Phase 2 complete |
| US3 - Exchange Connectivity | P1 | Foundational | Phase 2 complete |
| US4 - Alerting | P2 | Any dashboard | Any of US1/US2/US3 complete |
| US5 - Trading Performance | P2 | Foundational | Phase 2 complete |
| US6 - Historical Analysis | P3 | Any dashboard | Any of US1/US2/US3 complete |

### Within Each User Story

- Collector class before table schema
- Table schema before dashboard
- Dashboard structure before individual panels
- All panels complete before checkpoint

### Parallel Opportunities

- T003 + T004: Different files (server.conf vs .env.example)
- T005 + T006 after T002: Different provisioning files
- US1, US2, US3 can all start in parallel after Phase 2
- Dashboard panel tasks within each story can be parallelized IF different JSON sections

---

## Parallel Example: Phase 1 Setup

```bash
# After T002 completes, launch these in parallel:
Task: "Create QuestDB server configuration in monitoring/questdb/server.conf" [T003]
Task: "Create environment variables template in monitoring/.env.example" [T004]
```

## Parallel Example: P1 User Stories

```bash
# After Phase 2 completes, launch all P1 stories in parallel:
Task: "Create DaemonCollector class in monitoring/collectors/daemon.py" [T011 US1]
Task: "Create PipelineCollector class in monitoring/collectors/pipeline.py" [T019 US2]
Task: "Create ExchangeCollector class in monitoring/collectors/exchange.py" [T029 US3]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T010)
3. Complete Phase 3: User Story 1 - Health Dashboard (T011-T018)
4. **STOP and VALIDATE**: Test daemon health metrics in Grafana
5. Deploy if ready - basic monitoring operational

### Incremental Delivery

| Increment | Stories | Capability Added |
|-----------|---------|-----------------|
| MVP | US1 | Daemon health monitoring |
| +P1 Complete | US2, US3 | Pipeline & exchange visibility |
| +P2 | US4, US5 | Alerting + trading performance |
| +P3 | US6 | Historical analysis |
| Polish | Integration | Production-ready |

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Health Dashboard)
   - Developer B: User Story 2 (Pipeline Metrics)
   - Developer C: User Story 3 (Exchange Connectivity)
3. Stories complete and integrate independently

---

## Task Summary

| Phase | Task Count | Parallel Opportunities |
|-------|------------|----------------------|
| Phase 1: Setup | 6 | T003+T004 |
| Phase 2: Foundational | 8 | T007+T008+T009 (tests) |
| Phase 3: US1 Health | 8 | Panels within dashboard |
| Phase 4: US2 Pipeline | 10 | Panels within dashboard |
| Phase 5: US3 Exchange | 11 | Panels within dashboard |
| Phase 6: US4 Alerting | 9 | Contact point configs |
| Phase 7: US5 Trading | 11 | Panels within dashboard |
| Phase 8: US6 Historical | 6 | Dashboard updates |
| Phase 9: Integration | 11 | Alpha-debug runs |
| **Total** | **80** | |

**MVP Scope**: T001-T022 (22 tasks) → Health Dashboard operational with TDD

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All dashboards should load in < 3 seconds (SC-002)
- Target 10,000 writes/second sustained (SC-004)
