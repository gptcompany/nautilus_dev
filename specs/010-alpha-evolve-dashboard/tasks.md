# Tasks: Alpha-Evolve Grafana Dashboard

**Input**: Design documents from `/specs/010-alpha-evolve-dashboard/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: Not explicitly requested in spec - minimal validation tests included.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

---

## Phase 1: Setup (Infrastructure Foundation)

**Purpose**: Create QuestDB schema and Pydantic model for evolution metrics

- [x] T001 Copy QuestDB schema from specs/010-alpha-evolve-dashboard/contracts/evolution_metrics.sql to monitoring/schemas/evolution_metrics.sql
- [x] T002 Add EvolutionMetrics Pydantic model to monitoring/models.py
- [x] T003 Create EvolutionMetricsPublisher class in scripts/alpha_evolve/metrics_publisher.py

---

## Phase 2: Foundational (Metrics Sync Integration)

**Purpose**: Hook metrics publisher into evolution controller - BLOCKS all dashboard panels

**⚠️ CRITICAL**: No dashboard panels can show data until this phase is complete

- [x] T004 Update scripts/alpha_evolve/controller.py to import EvolutionMetricsPublisher
- [x] T005 Add publish_evaluation() call after successful evaluation in controller.py
- [x] T006 Add publish_mutation_failure() call after failed mutations in controller.py
- [x] T007 Add optional QuestDB client parameter to EvolutionController.__init__()

**Checkpoint**: Metrics sync active - dashboard panels can now receive data

---

## Phase 3: User Story 1 - Fitness Progress Visualization (Priority: P2) 🎯 MVP

**Goal**: Time-series chart showing best fitness per generation

**Independent Test**: Generate mock data, verify chart renders with trend line

### Implementation for User Story 1

- [x] T008 [US1] Create base dashboard JSON structure in monitoring/grafana/dashboards/evolution.json
- [x] T009 [US1] Add experiment filter variable to dashboard template
- [x] T010 [US1] Implement Fitness Progress timeseries panel with Calmar query
- [x] T011 [US1] Add Sharpe ratio toggle to Fitness Progress panel
- [x] T012 [US1] Add trend line/moving average overlay to Fitness Progress panel
- [x] T013 [US1] Configure 5-second auto-refresh for dashboard

**Checkpoint**: Fitness Progress panel shows evolving fitness over time with experiment filtering

---

## Phase 4: User Story 2 - Top Strategies Leaderboard (Priority: P2)

**Goal**: Table showing top 10 strategies with metrics

**Independent Test**: Populate store with strategies, verify table displays sorted by Calmar

### Implementation for User Story 2

- [x] T014 [US2] Implement Top Strategies table panel in evolution.json
- [x] T015 [US2] Add columns: Rank, ID (truncated), Generation, Sharpe, Calmar, MaxDD, CAGR
- [x] T016 [US2] Configure sortable columns with Calmar as default
- [x] T017 [US2] Add color thresholds for positive/negative metrics
- [x] T018 [US2] Add strategy code access link (copy program_id to clipboard on click) per FR-011

**Checkpoint**: Top 10 strategies displayed with sortable metrics table and code access

---

## Phase 5: User Story 3 - Population Statistics (Priority: P2)

**Goal**: Gauges and histogram for population-level metrics

**Independent Test**: Generate population data, verify gauges and histogram display

### Implementation for User Story 3

- [x] T019 [US3] Implement Population Size gauge panel in evolution.json
- [x] T020 [US3] Implement Generation Count gauge panel
- [x] T021 [US3] Implement Average Fitness gauge panel
- [x] T022 [US3] Implement Best vs Average fitness comparison stat
- [x] T023 [US3] Implement Fitness Distribution histogram panel
- [x] T024 [US3] Implement Average Mutations per Lineage stat per US3-AC3

**Checkpoint**: Population statistics visible with gauges, distribution histogram, and lineage stats

---

## Phase 6: User Story 4 - Mutation Success Tracking (Priority: P3)

**Goal**: Pie chart and success rate gauge for mutation outcomes

**Independent Test**: Log various mutation outcomes, verify pie chart segments

### Implementation for User Story 4

- [x] T025 [US4] Implement Mutation Outcomes pie chart panel in evolution.json
- [x] T026 [US4] Implement Success Rate percentage gauge panel
- [x] T027 [US4] Add color coding: success=green, syntax_error=yellow, runtime_error=red, timeout=orange
- [x] T028 [US4] Implement Success Rate Trend timeseries panel per FR-017

**Checkpoint**: Mutation success tracking visible with pie chart, rate gauge, and trend

---

## Phase 7: Polish & Validation

**Purpose**: Final touches and performance validation

- [x] T029 [P] Add panel descriptions and tooltips in evolution.json
- [x] T030 [P] Configure panel layout (grid positions) for optimal dashboard display
- [x] T031 Validate dashboard loads in <3 seconds with sample data (SC-001)
- [x] T032 Test edge case: empty dashboard (no evolution data yet)
- [x] T033 Test edge case: dashboard with 1000+ strategies (SC-002)
- [x] T034 Verify auto-refresh behavior (no flicker, data updates) (SC-003)
- [x] T035 Test edge case: QuestDB unavailable (dashboard shows error gracefully)
- [x] T036 Test edge case: concurrent dashboard refresh while evolution writes
- [x] T037 Deploy dashboard via Grafana provisioning and verify (SC-004)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Phase 2 completion
  - US1 (Fitness Progress) should be first as it creates base dashboard
  - US2, US3, US4 can proceed after US1 creates dashboard file
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P2)**: Creates base dashboard file - other stories ADD panels to it
- **User Story 2 (P2)**: Depends on US1 (needs dashboard file to exist)
- **User Story 3 (P2)**: Depends on US1 (needs dashboard file to exist)
- **User Story 4 (P3)**: Depends on US1 (needs dashboard file to exist)

### Within Each User Story

- Base structure before specific panels
- Queries before panel configuration
- Panel before styling/thresholds

### Parallel Opportunities

| Phase | Parallel Tasks |
|-------|----------------|
| Phase 1 | T002 + T003 (different files) |
| Phase 2 | None (sequential edits to controller.py) |
| Phase 3 | None (sequential edits to evolution.json) |
| Phase 4 | None (sequential edits to evolution.json) |
| Phase 5 | None (sequential edits to evolution.json) |
| Phase 6 | None (sequential edits to evolution.json) |
| Phase 7 | T029 + T030 (within same file, but different sections) |

⚠️ **Note**: Most tasks edit the same file (evolution.json), so parallelization is limited.

---

## Parallel Example: Phase 1

```bash
# After T001 completes, these can run in parallel:
Task: "Add EvolutionMetrics Pydantic model to monitoring/models.py"
Task: "Create EvolutionMetricsPublisher class in scripts/alpha_evolve/metrics_publisher.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T007)
3. Complete Phase 3: User Story 1 (T008-T013)
4. **STOP and VALIDATE**: Test Fitness Progress panel independently
5. Deploy/demo if ready - basic evolution monitoring available

**Total Tasks**: 37 (T001-T037)

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. Add User Story 1 → Test independently → **MVP Deployed**
3. Add User Story 2 → Test independently → Top Strategies visible
4. Add User Story 3 → Test independently → Population stats visible
5. Add User Story 4 → Test independently → Mutation tracking visible
6. Polish phase → Production-ready dashboard

### Story Completion Checkpoints

| Checkpoint | What's Deliverable |
|------------|-------------------|
| After US1 | Basic fitness monitoring dashboard |
| After US2 | + Top strategies leaderboard |
| After US3 | + Population statistics gauges |
| After US4 | Full dashboard with mutation tracking |

---

## Notes

- **File Conflict Risk**: Most dashboard tasks edit `evolution.json` - cannot be parallelized
- All user stories are P2 except US4 (P3) - implement US1-US3 first
- Dashboard JSON format follows existing patterns in `monitoring/grafana/dashboards/trading.json`
- Queries validated in `data-model.md` Query Patterns section
- Schema already exists in `contracts/evolution_metrics.sql` - just needs copy to final location
