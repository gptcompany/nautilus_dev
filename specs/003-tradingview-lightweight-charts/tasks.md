# Tasks: TradingView Lightweight Charts Real-Time Trading Dashboard

**Input**: Design documents from `/specs/003-tradingview-lightweight-charts/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Frontend JavaScript code - constitution TDD requirements apply to Python backend only. Server unit tests (test_server.py) will be added during Phase 2. E2E tests (Playwright) are recommended but optional for MVP.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks requiring multi-implementation exploration
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for the dashboard application

- [x] T001 Create dashboard directory structure per plan.md in dashboard/
- [x] T002 [P] Create package.json with esbuild dependency in dashboard/package.json
- [x] T003 [P] Create Python dependencies file in dashboard/requirements.txt
- [x] T004 Create base HTML template with CDN links in dashboard/index.html

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### WebSocket Bridge (Backend)

- [x] T005 Create FastAPI server skeleton with CORS in dashboard/server.py
- [x] T006 Implement WebSocket endpoint (/ws) with connection management in dashboard/server.py
- [x] T007 Create WebSocket message models (OI, Funding, Liquidation, Status) in dashboard/models.py
- [x] T008 Implement DaemonRunner callback integration for real-time data in dashboard/server.py

### REST API (Backend)

- [x] T009 Implement GET /api/status endpoint in dashboard/server.py
- [x] T010 Implement GET /api/symbols endpoint in dashboard/server.py
- [x] T011 [P] Implement GET /api/history/oi endpoint with Parquet query in dashboard/server.py
- [x] T012 [P] Implement GET /api/history/funding endpoint in dashboard/server.py
- [x] T013 [P] Implement GET /api/history/liquidations endpoint in dashboard/server.py

### WebSocket Client (Frontend)

- [x] T014 Create ReconnectingWebSocket class with exponential backoff in dashboard/src/data/ws-client.js
- [x] T015 Implement subscribe/unsubscribe message handling in dashboard/src/data/ws-client.js
- [x] T016 Implement ping/pong heartbeat mechanism in dashboard/src/data/ws-client.js

### Data Buffer (Frontend)

- [x] T017 Create DataBuffer class with rolling window (50k points max) in dashboard/src/data/buffer.js

### Chart Infrastructure (Frontend)

- [x] T018 Create base chart setup with dark theme in dashboard/src/charts/base-chart.js
- [x] T019 [P] Create CSS styles for dark theme dashboard in dashboard/styles/main.css

### Main Application (Frontend)

- [x] T020 Create main app entry point with chart initialization in dashboard/src/app.js

### Utilities (Frontend)

- [x] T020a [P] Create number formatters (OI values, percentages) in dashboard/src/utils/format.js
- [x] T020b [P] Create time formatters for chart axis in dashboard/src/utils/format.js

### Server Tests (Python - TDD)

- [x] T020c Write unit tests for server endpoints in tests/dashboard/test_server.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Real-Time Open Interest Visualization (Priority: P1) 🎯 MVP

**Goal**: Display Open Interest changes in real-time on a chart so traders can identify when large positions are being opened or closed

**Independent Test**: Connect to existing WebSocket stream and verify OI data appears on the chart within 1 second of receiving updates

### Implementation for User Story 1

- [x] T021 [US1] Create OI line chart component with series setup in dashboard/src/charts/oi-chart.js
- [x] T022 [US1] Implement OI data point transformation (timestamp → ChartDataPoint) in dashboard/src/charts/oi-chart.js
- [x] T023 [US1] Implement real-time OI update handler via WebSocket in dashboard/src/charts/oi-chart.js
- [x] T024 [US1] Implement significant OI change detection (>5% in 1 min) with visual highlight in dashboard/src/charts/oi-chart.js
- [x] T025 [US1] Wire OI chart to main app and WebSocket client in dashboard/src/app.js

**Checkpoint**: At this point, User Story 1 should be fully functional - OI chart updates in real-time

---

## Phase 4: User Story 2 - Real-Time Funding Rate Display (Priority: P1)

**Goal**: Display current funding rate and historical trend so traders understand position costs and market sentiment

**Independent Test**: Display current funding rate and verify it updates at each 8-hour funding interval

### Implementation for User Story 2

- [x] T026 [US2] Create Funding rate chart component with percentage formatting in dashboard/src/charts/funding-chart.js
- [x] T027 [US2] Implement color coding logic (positive=red, negative=green) in dashboard/src/charts/funding-chart.js
- [x] T028 [US2] Implement real-time funding rate update handler in dashboard/src/charts/funding-chart.js
- [x] T029 [US2] Create funding rate display panel (current rate prominent) in dashboard/src/ui/funding-display.js
- [x] T030 [US2] Wire Funding chart to main app and WebSocket client in dashboard/src/app.js

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Real-Time Liquidation Events (Priority: P2)

**Goal**: Display liquidation events as they happen so traders can identify cascading liquidations and potential price reversals

**Independent Test**: Simulate liquidation events from WebSocket stream and verify they appear as markers on the chart

### Implementation for User Story 3

- [x] T031 [US3] Create Liquidation marker layer component in dashboard/src/charts/liquidation-layer.js
- [x] T032 [US3] Implement marker positioning logic (LONG=below, SHORT=above) in dashboard/src/charts/liquidation-layer.js
- [x] T033 [US3] Implement marker styling (color, shape, text) per data-model.md in dashboard/src/charts/liquidation-layer.js
- [x] T034 [US3] Implement liquidation aggregation for rapid events (>10/min) in dashboard/src/charts/liquidation-layer.js
- [x] T035 [US3] Wire Liquidation layer to OI chart and WebSocket client in dashboard/src/app.js

**Checkpoint**: Core real-time visualization complete - OI, Funding, and Liquidations all functional

---

## Phase 6: User Story 4 - Historical Data Overlay (Priority: P3)

**Goal**: View historical OI, funding, and price data for pattern analysis

**Independent Test**: Load historical data from Parquet catalog and display on chart with proper time alignment

### Implementation for User Story 4

- [x] T036 [US4] Create REST API client for historical data endpoints in dashboard/src/data/api-client.js
- [x] T037 [US4] Implement date range selector UI component in dashboard/src/ui/date-range.js
- [x] T038 [US4] Implement historical data loading with progress indicator in dashboard/src/data/api-client.js
- [x] T039 [US4] Implement visual distinction between historical (faded) and live data in dashboard/src/charts/base-chart.js
- [x] T040 [US4] Implement data aggregation for large date ranges (>1 month) in dashboard/src/data/api-client.js
- [x] T041 [US4] Wire historical overlay to charts and UI in dashboard/src/app.js

**Checkpoint**: Historical overlay working alongside real-time data

---

## Phase 7: User Story 5 - Multi-Symbol Support (Priority: P3)

**Goal**: View data for different trading pairs (BTCUSDT, ETHUSDT) to monitor multiple markets

**Independent Test**: Switch between BTCUSDT and ETHUSDT and verify correct data streams connect

### Implementation for User Story 5

- [x] T042 [US5] Create symbol selector dropdown component in dashboard/src/ui/symbol-selector.js
- [x] T043 [US5] Implement symbol switch logic (unsubscribe old, subscribe new) in dashboard/src/data/ws-client.js
- [x] T044 [US5] Implement chart state preservation across symbol switches (zoom level, visible range) in dashboard/src/app.js
- [x] T045 [US5] Clear and reload chart data on symbol switch in dashboard/src/app.js
- [x] T046 [US5] Wire symbol selector to main app in dashboard/src/app.js

**Checkpoint**: Multi-symbol support complete

---

## Phase 8: UI & Connection Status (Cross-Cutting)

**Purpose**: User interface polish and connection status handling

### Connection Status

- [x] T047 Create connection status indicator component in dashboard/src/ui/status.js
- [x] T048 Implement status states (connected=green, reconnecting=yellow, disconnected=red) in dashboard/src/ui/status.js
- [x] T049 Wire status indicator to WebSocket client events in dashboard/src/app.js

### WebSocket Resilience

- [x] T050 Implement WebSocket data gap detection (missed sequence numbers) in dashboard/src/data/ws-client.js
- [x] T051 Implement gap recovery logic (request backfill from REST API) in dashboard/src/data/ws-client.js

---

## Phase 9: Standalone Bundle (FR-009)

**Purpose**: Create deployable standalone HTML file with embedded assets

- [x] T052 Create esbuild configuration for JS bundling in dashboard/build.js
- [x] T053 Implement inline CSS injection in build script in dashboard/build.js
- [x] T054 Implement Lightweight Charts library inlining in dashboard/build.js
- [x] T055 Generate dist/dashboard.html standalone file in dashboard/dist/dashboard.html
- [x] T056 Verify standalone HTML works without server (for static hosting) in dashboard/dist/

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T057 [P] Add error handling for failed WebSocket messages in dashboard/src/data/ws-client.js
- [x] T058 [P] Add error handling for failed REST API calls in dashboard/src/data/api-client.js
- [x] T059 Handle browser tab inactive state (pause updates) in dashboard/src/app.js
- [x] T060 Add graceful degradation when historical catalog unavailable in dashboard/src/data/api-client.js
- [x] T061 Handle extreme values (e.g., 1000% funding rate) in dashboard/src/charts/funding-chart.js
- [x] T062 Run alpha-debug verification on completed dashboard (24 issues found, 7 HIGH fixed)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (P1) and US2 (P1) have same priority - can run in parallel
  - US3 (P2) can start after Foundational, but logically follows US1 (markers on OI chart)
  - US4 (P3) and US5 (P3) can run in parallel after US1-US3
- **UI & Status (Phase 8)**: Can run in parallel with User Story phases
- **Standalone Bundle (Phase 9)**: Depends on all implementation complete
- **Polish (Phase 10)**: Depends on all features complete

### User Story Dependencies

| Story | Priority | Depends On | Can Start After |
|-------|----------|------------|-----------------|
| US1 (OI Chart) | P1 | Foundational | Phase 2 complete |
| US2 (Funding) | P1 | Foundational | Phase 2 complete |
| US3 (Liquidations) | P2 | Foundational, US1 (for markers on OI chart) | Phase 3 complete |
| US4 (Historical) | P3 | Foundational | Phase 2 complete |
| US5 (Multi-Symbol) | P3 | Foundational | Phase 2 complete |

### Within Each User Story

- Config/setup before visualization logic
- Data transformation before chart rendering
- Core implementation before UI integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002 and T003 can run in parallel (package.json, requirements.txt)

**Phase 2 (Foundational)**:
- T011, T012, T013 can run in parallel (different endpoints, same file but sequential addition)
- T018 and T019 can run in parallel (JS and CSS files)

**User Stories**:
- US1 (Phase 3) and US2 (Phase 4) can run in parallel (different chart components)
- US4 (Phase 6) and US5 (Phase 7) can run in parallel (different features)

**Phase 8 (UI)**:
- T050 and T051 can run in parallel (different utility functions)

---

## Parallel Example: Foundational Phase

```bash
# Launch parallel REST endpoints (after T009, T010 complete):
Task: "Implement GET /api/history/oi endpoint in dashboard/server.py"
Task: "Implement GET /api/history/funding endpoint in dashboard/server.py"
Task: "Implement GET /api/history/liquidations endpoint in dashboard/server.py"

# Launch parallel CSS and chart setup:
Task: "Create base chart setup with dark theme in dashboard/src/charts/base-chart.js"
Task: "Create CSS styles for dark theme dashboard in dashboard/styles/main.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup (4 tasks)
2. Complete Phase 2: Foundational (16 tasks) - CRITICAL
3. Complete Phase 3: User Story 1 - OI Chart (5 tasks)
4. Complete Phase 4: User Story 2 - Funding Display (5 tasks)
5. Add Phase 8: Connection Status (3 tasks)
6. **STOP and VALIDATE**: Dashboard shows real-time OI and Funding
7. Deploy/demo if ready (30 tasks for MVP)

### Incremental Delivery

1. **MVP** (Phases 1-4, 8): OI + Funding real-time → Demo
2. **+ Liquidations** (Phase 5): Add liquidation markers → Demo
3. **+ Historical** (Phase 6): Historical overlay → Demo
4. **+ Multi-Symbol** (Phase 7): Symbol switching → Demo
5. **+ Standalone** (Phase 9): Bundled HTML → Final delivery

### Parallel Team Strategy

With 2 developers after Foundational phase:

- **Developer A**: User Story 1 (OI) + User Story 3 (Liquidations)
- **Developer B**: User Story 2 (Funding) + User Story 4 (Historical) + User Story 5 (Multi-Symbol)

---

## Summary

| Category | Count |
|----------|-------|
| **Total Tasks** | 65 |
| **Phase 1 (Setup)** | 4 |
| **Phase 2 (Foundational)** | 19 (includes formatters + server tests) |
| **Phase 3 (US1 - OI)** | 5 |
| **Phase 4 (US2 - Funding)** | 5 |
| **Phase 5 (US3 - Liquidations)** | 5 |
| **Phase 6 (US4 - Historical)** | 6 |
| **Phase 7 (US5 - Multi-Symbol)** | 5 |
| **Phase 8 (UI/Status)** | 5 (includes WebSocket resilience) |
| **Phase 9 (Bundle)** | 5 |
| **Phase 10 (Polish)** | 6 |
| **Parallel opportunities** | 17 tasks marked [P] |

### MVP Scope (Recommended)

- Phases 1-4 + Phase 8 = **36 tasks**
- Delivers: Real-time OI chart, Funding display, Connection status, WebSocket resilience
- Foundation for all future stories

---

## Notes

- [P] tasks = different files, no dependencies (processed by /speckit.implement)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Backend (server.py) should be developed first in Phase 2 as it's blocking
