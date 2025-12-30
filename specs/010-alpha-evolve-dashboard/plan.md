# Implementation Plan: Alpha-Evolve Grafana Dashboard

**Feature Branch**: `010-alpha-evolve-dashboard`
**Created**: 2025-12-28
**Status**: Ready for Implementation
**Spec Reference**: `specs/010-alpha-evolve-dashboard/spec.md`

## Architecture Overview

The Alpha-Evolve Dashboard provides real-time visualization of strategy evolution progress. It integrates with the existing Grafana + QuestDB monitoring stack.

### System Context

```
┌─────────────────────┐     ┌────────────────────┐     ┌─────────────────┐
│  Evolution          │────▶│  QuestDB           │────▶│  Grafana        │
│  Controller         │     │  evolution_metrics │     │  Dashboard      │
│  (spec-009)         │     │  table             │     │  (evolution.json)
└─────────────────────┘     └────────────────────┘     └─────────────────┘
         │                           ▲
         │                           │
         ▼                           │
┌─────────────────────┐              │
│  SQLite Store       │──────────────┘
│  (spec-006)         │   (sync after evaluation)
│  programs table     │
└─────────────────────┘
```

### Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Evolution Dashboard                          │
├──────────────────┬──────────────────┬────────────────┬───────────────┤
│ Fitness Progress │ Top Strategies   │ Population     │ Mutation      │
│ (timeseries)     │ (table)          │ Stats (gauges) │ Stats (pie)   │
│                  │                  │                │               │
│ Best fitness/gen │ Rank, ID, Gen    │ Pop size       │ Success/Fail  │
│ with trend line  │ Sharpe, Calmar   │ Generation     │ Error types   │
│                  │ MaxDD, CAGR      │ Avg fitness    │ Success rate  │
└──────────────────┴──────────────────┴────────────────┴───────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ QuestDB         │
                    │ evolution_      │
                    │ metrics         │
                    └─────────────────┘
```

## Technical Decisions

### Decision 1: Data Source

**Options Considered**:
1. **SQLite Direct**: Use `frser-sqlite-datasource` plugin to query SQLite directly
   - Pros: No data duplication, simpler architecture
   - Cons: Requires plugin installation, Docker volume mount, no time-series optimization
2. **QuestDB Sync**: Sync evolution metrics from SQLite to QuestDB
   - Pros: Consistent with existing stack, SAMPLE BY/LATEST BY support, no new plugins
   - Cons: Data duplication between SQLite and QuestDB

**Selected**: Option 2 (QuestDB Sync)

**Rationale**: All existing dashboards use QuestDB. Reusing the same data source provides consistency, time-series optimization, and no additional infrastructure.

---

### Decision 2: Sync Approach

**Options Considered**:
1. **Event-driven sync**: Write to QuestDB after each evaluation
   - Pros: Real-time updates, minimal latency
   - Cons: Couples evolution to QuestDB
2. **Periodic batch sync**: Cron-like sync every N seconds
   - Pros: Decoupled, handles QuestDB downtime
   - Cons: Dashboard delay
3. **Dual-write**: Write to both SQLite and QuestDB simultaneously
   - Pros: No sync delay
   - Cons: More code changes, consistency issues

**Selected**: Option 1 (Event-driven sync)

**Rationale**: Evolution runs are relatively low-volume (1-10 strategies/minute). Event-driven sync provides real-time dashboard updates with minimal complexity.

---

### Decision 3: Dashboard Provisioning

**Options Considered**:
1. **JSON file in provisioning**: Dashboard JSON in `monitoring/grafana/dashboards/`
   - Pros: Infrastructure as Code, version controlled
   - Cons: None for this use case
2. **Manual dashboard creation**: Create via Grafana UI
   - Pros: Interactive design
   - Cons: Not reproducible, no version control

**Selected**: Option 1 (JSON provisioning)

**Rationale**: FR-004 requires IaC provisioning. Consistent with existing dashboards (health.json, trading.json).

---

## Implementation Strategy

### Phase 1: Data Infrastructure

**Goal**: Create QuestDB table and Pydantic model for evolution metrics

**Deliverables**:
- [x] Research data source approach (completed in research.md)
- [ ] QuestDB table schema: `monitoring/schemas/evolution_metrics.sql`
- [ ] Pydantic model: `EvolutionMetrics` in `monitoring/models.py`
- [ ] Metrics publisher: `scripts/alpha_evolve/metrics_publisher.py`

**Dependencies**: None

---

### Phase 2: Metrics Sync Integration

**Goal**: Hook metrics publisher into evolution controller

**Deliverables**:
- [ ] Update `scripts/alpha_evolve/controller.py` to call metrics publisher
- [ ] Add optional QuestDB client parameter to EvolutionController

**Note**: QuestDB sync is handled by `metrics_publisher.py` (Phase 1), not by modifying `store.py`. SQLite store remains unchanged.

**Dependencies**: Phase 1

---

### Phase 3: Dashboard Implementation

**Goal**: Create Grafana dashboard JSON with all 4 panels

**Deliverables**:
- [ ] Fitness Progress panel (timeseries)
- [ ] Top Strategies panel (table)
- [ ] Population Stats panel (gauges)
- [ ] Mutation Stats panel (pie chart)
- [ ] Experiment filter variable
- [ ] Complete dashboard JSON: `monitoring/grafana/dashboards/evolution.json`

**Dependencies**: Phase 2

---

### Phase 4: Testing & Validation

**Goal**: Verify dashboard with real evolution data

**Deliverables**:
- [ ] Test with sample evolution run
- [ ] Verify auto-refresh behavior
- [ ] Test edge cases (empty data, large populations)
- [ ] Performance validation (<3s load time)

**Dependencies**: Phase 3

---

## File Structure

```
monitoring/
├── schemas/
│   └── evolution_metrics.sql      # QuestDB table definition (NEW)
├── models.py                      # Add EvolutionMetrics model (EDIT)
└── grafana/
    └── dashboards/
        └── evolution.json         # Dashboard JSON (NEW)

scripts/
└── alpha_evolve/
    ├── metrics_publisher.py       # QuestDB sync (NEW)
    └── controller.py              # Hook metrics publisher (EDIT)
```

## API Design

### Metrics Publisher Interface

```python
from scripts.alpha_evolve.store import Program
from monitoring.client import MetricsClient

class EvolutionMetricsPublisher:
    """Publishes evolution metrics to QuestDB for Grafana dashboards."""

    def __init__(self, client: MetricsClient) -> None:
        """Initialize with existing MetricsClient."""
        ...

    async def publish_evaluation(
        self,
        program: Program,
        mutation_outcome: str = "success",
        mutation_latency_ms: float = 0.0,
    ) -> None:
        """Publish strategy evaluation result."""
        ...

    async def publish_mutation_failure(
        self,
        experiment: str,
        outcome: str,  # "syntax_error", "runtime_error", "timeout"
        latency_ms: float,
    ) -> None:
        """Publish failed mutation for tracking."""
        ...
```

### EvolutionMetrics Model

```python
from pydantic import BaseModel
from datetime import datetime

class EvolutionMetrics(BaseModel):
    """Evolution metrics for QuestDB."""

    timestamp: datetime
    program_id: str
    experiment: str
    generation: int
    parent_id: str | None

    # Fitness metrics
    sharpe: float
    calmar: float
    max_dd: float
    cagr: float
    total_return: float
    trade_count: int | None
    win_rate: float | None

    # Mutation tracking
    mutation_outcome: str  # success, syntax_error, runtime_error, timeout
    mutation_latency_ms: float
```

## Testing Strategy

### Unit Tests
- [ ] Test EvolutionMetrics model serialization
- [ ] Test metrics publisher write operations
- [ ] Test sync hook in store

### Integration Tests
- [ ] Test dashboard loads with empty data
- [ ] Test dashboard with 10 strategies (small population)
- [ ] Test dashboard with 1,000 strategies (medium population)
- [ ] Test auto-refresh behavior

### Performance Tests
- [ ] Dashboard loads in <3 seconds with 10,000 strategies
- [ ] QuestDB queries complete in <100ms

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| QuestDB unavailable | Medium | Low | SQLite remains primary; dashboard shows error |
| Dashboard slows evolution | Medium | Low | Async writes with timeout |
| Schema migration needed | Low | Low | QuestDB handles schema evolution automatically |
| Large populations slow queries | Medium | Medium | DAY partitioning, SYMBOL indexes |

## Dependencies

### External Dependencies
- Grafana (already running at localhost:3000)
- QuestDB (already running and healthy)
- QuestDB Grafana plugin (already installed)

### Internal Dependencies
- spec-006: ProgramStore provides strategy data
- spec-009: EvolutionController provides sync points
- monitoring/client.py: MetricsClient for QuestDB writes

## Constitution Check

| Principle | Compliant | Notes |
|-----------|-----------|-------|
| Black Box Design | Yes | Metrics publisher has clean interface |
| KISS & YAGNI | Yes | Minimal implementation, reuses existing MetricsClient |
| Native First | Yes | Uses existing NautilusTrader monitoring patterns |
| No df.iterrows() | N/A | No DataFrame operations |
| TDD Discipline | Yes | Tests planned for all components |

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Dashboard loads in <3 seconds (SC-001)
- [ ] Charts render with 10,000 strategies (SC-002)
- [ ] Auto-refresh works without flicker (SC-003)
- [ ] Dashboard deployable via provisioning (SC-004)
- [ ] All panels show content with 10 strategies (SC-005)
