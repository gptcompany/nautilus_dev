# Tasks: CCXT Multi-Exchange Data Pipeline

**Input**: Design documents from `/specs/001-ccxt-data-pipeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included (TDD approach for data pipeline reliability)

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger (complex algorithmic tasks)
- **[Story]**: User story mapping (US1-US6)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per plan.md in `scripts/ccxt_pipeline/`
- [x] T002 Initialize Python project with pyproject.toml in `scripts/ccxt_pipeline/pyproject.toml`
- [x] T003 [P] Add dependencies (ccxt>=4.4.0, pydantic>=2.0, pyarrow>=14.0, click, apscheduler)
- [x] T004 [P] Create __init__.py files in all subpackages
- [x] T005 [P] Configure logging setup in `scripts/ccxt_pipeline/utils/logging.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Data Models (Pydantic)

- [x] T006 [P] Create OpenInterest model in `scripts/ccxt_pipeline/models/open_interest.py`
- [x] T007 [P] Create FundingRate model in `scripts/ccxt_pipeline/models/funding_rate.py`
- [x] T008 [P] Create Liquidation model in `scripts/ccxt_pipeline/models/liquidation.py`
- [x] T009 Create models __init__.py with exports in `scripts/ccxt_pipeline/models/__init__.py`

### Configuration

- [x] T010 Create CCXTPipelineConfig (Pydantic Settings) in `scripts/ccxt_pipeline/config.py`

### Base Infrastructure

- [x] T011 Create BaseFetcher abstract class in `scripts/ccxt_pipeline/fetchers/base.py`
- [x] T012 Create ParquetStore base class in `scripts/ccxt_pipeline/storage/parquet_store.py`
- [x] T012a Create async concurrent fetcher orchestrator in `scripts/ccxt_pipeline/fetchers/orchestrator.py` (asyncio.gather for multi-exchange fetch, covers FR-014)

### Tests for Foundation

- [x] T013 [P] Create test fixtures in `tests/ccxt_pipeline/conftest.py`
- [x] T014 [P] Unit tests for data models in `tests/ccxt_pipeline/test_models.py`
- [x] T015 [P] Unit tests for config in `tests/ccxt_pipeline/test_config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Fetch Current OI (Priority: P1) MVP

**Goal**: Fetch current Open Interest from all exchanges and display results

**Independent Test**: Run `ccxt-cli fetch-oi BTCUSDT-PERP` and verify OI values returned from all 3 exchanges

### Tests for User Story 1

- [x] T016 [P] [US1] Unit test for BinanceFetcher.fetch_open_interest in `tests/ccxt_pipeline/test_fetchers.py::test_binance_fetch_oi`
- [x] T017 [P] [US1] Unit test for BybitFetcher.fetch_open_interest in `tests/ccxt_pipeline/test_fetchers.py::test_bybit_fetch_oi`
- [x] T018 [P] [US1] Unit test for HyperliquidFetcher.fetch_open_interest in `tests/ccxt_pipeline/test_fetchers.py::test_hyperliquid_fetch_oi`
- [x] T019 [P] [US1] Integration test for concurrent fetching in `tests/ccxt_pipeline/test_integration.py::test_fetch_oi_all_exchanges`

### Implementation for User Story 1

- [x] T020 [P] [US1] Implement BinanceFetcher in `scripts/ccxt_pipeline/fetchers/binance.py`
- [x] T021 [P] [US1] Implement BybitFetcher in `scripts/ccxt_pipeline/fetchers/bybit.py`
- [x] T022 [P] [US1] Implement HyperliquidFetcher in `scripts/ccxt_pipeline/fetchers/hyperliquid.py`
- [x] T023 [US1] Create fetchers __init__.py with factory function in `scripts/ccxt_pipeline/fetchers/__init__.py`
- [x] T024 [US1] Implement basic CLI with fetch-oi command in `scripts/ccxt_pipeline/cli.py`
- [x] T025 [US1] Create __main__.py entry point in `scripts/ccxt_pipeline/__main__.py`

**Checkpoint**: User Story 1 complete - can fetch current OI from all exchanges via CLI

---

## Phase 4: User Story 5 - Persistent Storage (Priority: P1)

**Goal**: Store all fetched data to Parquet files compatible with NautilusTrader

**Independent Test**: Fetch OI, stop pipeline, verify data readable from disk with correct schema

### Tests for User Story 5

- [x] T026 [P] [US5] Unit test for ParquetStore.write in `tests/ccxt_pipeline/test_storage.py::test_write_open_interest`
- [x] T027 [P] [US5] Unit test for ParquetStore.read in `tests/ccxt_pipeline/test_storage.py::test_read_open_interest`
- [x] T028 [P] [US5] Unit test for ParquetStore.get_last_timestamp in `tests/ccxt_pipeline/test_storage.py::test_get_last_timestamp`
- [x] T029 [US5] Integration test for fetch-and-store flow in `tests/ccxt_pipeline/test_integration.py::test_fetch_and_store`

### Implementation for User Story 5

- [x] T030 [US5] Implement ParquetStore.write() for OpenInterest in `scripts/ccxt_pipeline/storage/parquet_store.py`
- [x] T031 [US5] Implement ParquetStore.read() with date range in `scripts/ccxt_pipeline/storage/parquet_store.py`
- [x] T032 [US5] Implement ParquetStore.get_last_timestamp() in `scripts/ccxt_pipeline/storage/parquet_store.py`
- [x] T033 [US5] Add --store flag to fetch-oi CLI command in `scripts/ccxt_pipeline/cli.py`
- [x] T034 [US5] Create storage __init__.py in `scripts/ccxt_pipeline/storage/__init__.py`
- [x] T034a [US5] Add Ctrl+C signal handler to CLI for graceful shutdown (flush pending writes, covers FR-012)

**Checkpoint**: User Stories 1+5 complete - can fetch and store OI data

---

## Phase 5: User Story 2 - Fetch Historical OI (Priority: P1)

**Goal**: Fetch historical OI with pagination and incremental updates

**Independent Test**: Run `ccxt-cli fetch-oi BTCUSDT-PERP --from 2025-01-01 --to 2025-01-31` and verify 30 days of data

### Tests for User Story 2

- [x] T035 [P] [US2] Unit test for fetch_open_interest_history in `tests/ccxt_pipeline/test_fetchers.py::test_fetch_oi_history`
- [x] T036 [P] [US2] Unit test for pagination handling in `tests/ccxt_pipeline/test_fetchers.py::test_pagination`
- [x] T037 [US2] Integration test for incremental updates in `tests/ccxt_pipeline/test_integration.py::test_incremental_update`

### Implementation for User Story 2

- [x] T038 [US2] Add fetch_open_interest_history to BinanceFetcher in `scripts/ccxt_pipeline/fetchers/binance.py`
- [x] T039 [US2] Add fetch_open_interest_history to BybitFetcher with chunk workaround in `scripts/ccxt_pipeline/fetchers/bybit.py`
- [x] T040 [US2] Add fetch_open_interest_history to HyperliquidFetcher in `scripts/ccxt_pipeline/fetchers/hyperliquid.py`
- [x] T041 [US2] Add --from and --to options to CLI in `scripts/ccxt_pipeline/cli.py`
- [x] T042 [US2] Implement incremental update logic (fetch only new) in `scripts/ccxt_pipeline/storage/parquet_store.py`

**Checkpoint**: User Stories 1+2+5 complete - full OI functionality (current + historical + storage)

---

## Phase 6: User Story 3 - Fetch Funding Rates (Priority: P2)

**Goal**: Fetch current and historical funding rates

**Independent Test**: Run `ccxt-cli fetch-funding BTCUSDT-PERP` and verify funding rates from all exchanges

### Tests for User Story 3

- [x] T043 [P] [US3] Unit test for fetch_funding_rate in `tests/ccxt_pipeline/test_fetchers.py::test_fetch_funding`
- [x] T044 [P] [US3] Unit test for fetch_funding_rate_history in `tests/ccxt_pipeline/test_fetchers.py::test_fetch_funding_history`
- [x] T045 [US3] Integration test for funding storage in `tests/ccxt_pipeline/test_integration.py::test_funding_storage`

### Implementation for User Story 3

- [x] T046 [P] [US3] Add fetch_funding_rate to all fetchers in `scripts/ccxt_pipeline/fetchers/*.py`
- [x] T047 [P] [US3] Add fetch_funding_rate_history to all fetchers in `scripts/ccxt_pipeline/fetchers/*.py`
- [x] T048 [US3] Add FundingRate storage support to ParquetStore in `scripts/ccxt_pipeline/storage/parquet_store.py`
- [x] T049 [US3] Add fetch-funding CLI command in `scripts/ccxt_pipeline/cli.py`

**Checkpoint**: User Stories 1-3+5 complete - OI and Funding functionality

---

## Phase 7: User Story 4 - Liquidation Stream (Priority: P2)

**Goal**: Stream real-time liquidation events via WebSocket

**Independent Test**: Run `ccxt-cli stream-liquidations BTCUSDT-PERP` and verify events received within 2s of occurrence

### Tests for User Story 4

- [x] T050 [P] [US4] Unit test for stream_liquidations with mock WebSocket in `tests/ccxt_pipeline/test_fetchers.py::test_stream_liquidations`
- [x] T051 [P] [US4] Unit test for reconnection logic in `tests/ccxt_pipeline/test_fetchers.py::test_websocket_reconnect`
- [x] T052 [US4] Integration test for liquidation storage in `tests/ccxt_pipeline/test_integration.py::test_liquidation_storage`

### Implementation for User Story 4

- [x] T053 [E] [US4] Implement stream_liquidations for BinanceFetcher in `scripts/ccxt_pipeline/fetchers/binance.py` (Alpha-Evolve: ReconnectingStream wrapper)
- [x] T054 [E] [US4] Implement stream_liquidations for BybitFetcher in `scripts/ccxt_pipeline/fetchers/bybit.py` (Alpha-Evolve: ReconnectingStream wrapper)
- [x] T054a [US4] Implement Hyperliquid liquidation polling fallback in `scripts/ccxt_pipeline/fetchers/hyperliquid.py` (when streaming unavailable, poll at 5s intervals)
- [x] T055 [US4] Add Liquidation storage support to ParquetStore in `scripts/ccxt_pipeline/storage/parquet_store.py` (already implemented in Phase 2)
- [x] T056 [US4] Add stream-liquidations CLI command in `scripts/ccxt_pipeline/cli.py`
- [x] T057 [US4] Implement reconnection with exponential backoff in `scripts/ccxt_pipeline/utils/reconnect.py` (ReconnectingStream class)

**Checkpoint**: User Stories 1-5 complete - Full data pipeline without daemon

---

## Phase 8: User Story 6 - Daemon Mode (Priority: P3)

**Goal**: Background service for continuous 24/7 data collection

**Independent Test**: Run `ccxt-cli daemon start`, wait 10 minutes, verify scheduled fetches occurred

### Tests for User Story 6

- [x] T058 [P] [US6] Unit test for DaemonRunner in `tests/ccxt_pipeline/test_daemon.py::TestDaemonScheduling`
- [x] T059 [P] [US6] Unit test for graceful shutdown in `tests/ccxt_pipeline/test_daemon.py::TestGracefulShutdown`
- [x] T060 [US6] Integration test for daemon stability in `tests/ccxt_pipeline/test_daemon.py::TestDaemonStability`

### Implementation for User Story 6

- [x] T061 [US6] Create DaemonRunner class with APScheduler in `scripts/ccxt_pipeline/scheduler/daemon.py`
- [x] T062 [US6] Implement scheduled OI fetching in `scripts/ccxt_pipeline/scheduler/daemon.py`
- [x] T063 [US6] Implement scheduled funding fetching in `scripts/ccxt_pipeline/scheduler/daemon.py`
- [x] T064 [US6] Integrate liquidation streaming in daemon mode in `scripts/ccxt_pipeline/scheduler/daemon.py`
- [x] T065 [US6] Implement graceful shutdown handling in `scripts/ccxt_pipeline/scheduler/daemon.py`
- [x] T066 [US6] Add daemon start/stop/status CLI commands in `scripts/ccxt_pipeline/cli.py`
- [x] T067 [US6] Create scheduler __init__.py in `scripts/ccxt_pipeline/scheduler/__init__.py`

**Checkpoint**: All user stories complete - Full daemon-capable pipeline

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T068 [P] Add query CLI command for stored data in `scripts/ccxt_pipeline/cli.py`
- [x] T069 [P] Create README.md with usage examples in `scripts/ccxt_pipeline/README.md`
- [x] T070 [P] Code quality checks (ruff check/format) - all checks pass
- [x] T071 Code cleanup and docstrings for public APIs (ruff formatted)
- [ ] T072 Performance profiling for concurrent fetching (manual task)
- [ ] T073 Run alpha-debug verification on complete codebase (manual task)
- [ ] T074 24-hour daemon stability test (manual task)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──────────────────────────────────────────┐
                                                         │
Phase 2: Foundational ◄──────────────────────────────────┘
    │
    ├───► Phase 3: US1 (Current OI) ─────► P1 MVP
    │         │
    │         ▼
    ├───► Phase 4: US5 (Storage) ────────► Can run after US1
    │         │
    │         ▼
    ├───► Phase 5: US2 (Historical OI) ──► Depends on US5
    │
    ├───► Phase 6: US3 (Funding) ────────► Independent of US2
    │
    ├───► Phase 7: US4 (Liquidations) ───► Independent
    │
    └───► Phase 8: US6 (Daemon) ─────────► Depends on US1-5
              │
              ▼
         Phase 9: Polish
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US1 (Current OI) | Foundational | - |
| US5 (Storage) | US1 | - |
| US2 (Historical OI) | US5 | - |
| US3 (Funding) | Foundational | US2 |
| US4 (Liquidations) | Foundational | US2, US3 |
| US6 (Daemon) | US1-5 | - |

### Parallel Opportunities

**Phase 2 (Foundational)**:
```bash
# All models can be created in parallel
Task: T006 [P] Create OpenInterest model
Task: T007 [P] Create FundingRate model
Task: T008 [P] Create Liquidation model
```

**Phase 3 (US1)**:
```bash
# All fetchers can be implemented in parallel
Task: T020 [P] Implement BinanceFetcher
Task: T021 [P] Implement BybitFetcher
Task: T022 [P] Implement HyperliquidFetcher
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Current OI)
4. **STOP and VALIDATE**: Test `ccxt-cli fetch-oi BTCUSDT-PERP`
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Current OI works → Demo!
3. Add US5 → Storage works → Demo!
4. Add US2 → Historical OI works → Demo!
5. Add US3 → Funding works → Demo!
6. Add US4 → Liquidations work → Demo!
7. Add US6 → Daemon works → Production ready!

---

## Summary

| Metric | Count |
|--------|-------|
| **Total Tasks** | 77 |
| **Phase 1 (Setup)** | 5 |
| **Phase 2 (Foundational)** | 11 |
| **US1 (Current OI)** | 10 |
| **US5 (Storage)** | 10 |
| **US2 (Historical OI)** | 8 |
| **US3 (Funding)** | 7 |
| **US4 (Liquidations)** | 9 |
| **US6 (Daemon)** | 10 |
| **Polish** | 7 |
| **Parallelizable [P]** | 32 |
| **Alpha-Evolve [E]** | 2 |

**MVP Scope**: Phases 1-3 (Setup + Foundational + US1) = 25 tasks

**Completed**: Phases 1-9 (113 tests passing) - All automated tasks complete. Manual tasks T072-T074 pending.

---

## Bug Fixes & Improvements (For Phase 7)

### BUG-001: None-safe parsing in fetcher methods

**Issue**: Parser methods use `data.get("key", 0)` which returns `None` (not `0`) when API returns explicit `None` values. This causes `float(None)` to crash.

**Solution Created**: Safe parsing utilities in `scripts/ccxt_pipeline/utils/parsing.py`

**Files to Update in Phase 7** (when implementing T053-T055):
- `scripts/ccxt_pipeline/fetchers/binance.py`
- `scripts/ccxt_pipeline/fetchers/bybit.py`
- `scripts/ccxt_pipeline/fetchers/hyperliquid.py`

**Usage**:
```python
from scripts.ccxt_pipeline.utils.parsing import safe_float

# Replace:
open_interest=float(data.get("openInterestAmount", 0))

# With:
open_interest=safe_float(data.get("openInterestAmount"))
```

**Tests**: `tests/ccxt_pipeline/test_utils_parsing.py`
