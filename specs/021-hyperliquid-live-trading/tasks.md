# Tasks: Hyperliquid Live Trading Integration (Spec 021)

**Input**: Design documents from `/specs/021-hyperliquid-live-trading/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Integration tests included per spec.md Testing Strategy.

**Organization**: Tasks grouped by user story (US1-US5) to enable independent implementation.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [X] T001 Create configs/hyperliquid/ directory structure
- [X] T002 Create configs/hyperliquid/__init__.py with module docstring
- [X] T003 [P] Create strategies/hyperliquid/__init__.py with module docstring
- [X] T004 [P] Create scripts/hyperliquid/ directory
- [X] T005 [P] Create tests/hyperliquid/ directory structure
- [X] T006 [P] Create .env.example with HYPERLIQUID_TESTNET_PK, HYPERLIQUID_MAINNET_PK template in configs/hyperliquid/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core factory functions that MUST be complete before user stories

**⚠️ CRITICAL**: No US1+ work can begin until this phase is complete

- [X] T007 Verify NautilusTrader nightly >= 1.222.0 installed with Hyperliquid adapter
- [X] T008 Implement create_hyperliquid_data_client() factory in configs/hyperliquid/data_client.py
- [X] T009 Add InstrumentProviderConfig with load_ids parameter in configs/hyperliquid/data_client.py
- [X] T010 [P] Write unit test for data client factory in tests/hyperliquid/test_data_client.py
- [X] T011 Update configs/hyperliquid/__init__.py to export factory functions

**Checkpoint**: Foundational complete - user story implementation can begin

---

## Phase 3: US1 - Live Data Feed (Priority: P1) 🎯 MVP

**Goal**: Stream real-time Hyperliquid market data

**Independent Test**: Subscribe to BTC-USD-PERP, receive QuoteTick/TradeTick events

### Implementation for US1

- [X] T012 [US1] Add BTC-USD-PERP, ETH-USD-PERP instrument IDs in configs/hyperliquid/data_client.py
- [X] T013 [US1] Add testnet parameter to factory in configs/hyperliquid/data_client.py
- [X] T014 [US1] Create data-only TradingNode config in configs/hyperliquid/data_client.py
- [X] T015 [P] [US1] Create scripts/hyperliquid/stream_data.py for data feed testing
- [X] T016 [US1] Add subscribe_quote_ticks() call in stream_data.py
- [X] T017 [US1] Add subscribe_trade_ticks() call in stream_data.py
- [X] T018 [US1] Add subscribe_order_book_deltas() call in stream_data.py
- [X] T019 [US1] Verify QuoteTick, TradeTick, OrderBookDelta types received (assert latency < 50ms per NFR-001)
- [X] T020 [P] [US1] Write integration test for data feed in tests/hyperliquid/test_data_client.py

**Checkpoint**: US1 complete - live data streaming operational

---

## Phase 4: US2 - Historical Data Persistence (Priority: P1) 🎯 MVP

**Goal**: Record live data to ParquetDataCatalog for backtesting

**Independent Test**: Record 5 minutes of data, load in BacktestNode

### Implementation for US2

- [X] T021 [P] [US2] Create configs/hyperliquid/persistence.py with PersistenceConfig
- [X] T022 [US2] Configure catalog_path="./catalog/hyperliquid" in persistence.py
- [X] T023 [US2] Add catalog_store="parquet" in persistence.py
- [X] T024 [US2] Create scripts/hyperliquid/record_data.py for data recording
- [X] T025 [US2] Add strategy that subscribes to data and auto-persists in record_data.py
- [X] T026 [US2] Verify Parquet files created in catalog directory
- [X] T027 [US2] Verify catalog compatible with BacktestNode
- [X] T028 [P] [US2] Write integration test for catalog loading in tests/hyperliquid/test_persistence.py

**Checkpoint**: US2 complete - data persistence operational

---

## Phase 5: US3 - Live Order Execution (Priority: P2)

**Goal**: Submit and manage orders on Hyperliquid

**Independent Test**: Submit MARKET order on testnet, receive fill confirmation

**⚠️ Note**: ExecClient is in "building" phase - testnet validation required

### Implementation for US3

- [X] T029 [P] [US3] Create configs/hyperliquid/exec_client.py with factory function
- [X] T030 [US3] Implement create_hyperliquid_exec_client() factory in exec_client.py
- [X] T031 [US3] Add private_key=None (loads from env) in exec_client.py
- [X] T032 [US3] Add max_retries, retry_delay params in exec_client.py
- [X] T033 [US3] Add testnet=True configuration in configs/hyperliquid/testnet.py
- [X] T034 [P] [US3] Create scripts/hyperliquid/test_orders.py for order testing
- [X] T035 [US3] Implement MARKET order submission in test_orders.py
- [X] T036 [US3] Implement LIMIT order submission in test_orders.py
- [X] T037 [US3] Implement STOP_MARKET order submission in test_orders.py
- [X] T038 [US3] Implement STOP_LIMIT order submission in test_orders.py
- [X] T039 [US3] Add reduce_only=True support for stop-loss orders
- [X] T040 [US3] Verify fill events received via WebSocket (assert latency < 100ms per NFR-001)
- [X] T041 [P] [US3] Write unit test for exec client factory in tests/hyperliquid/test_exec_client.py

**Checkpoint**: US3 complete - order execution operational on testnet

---

## Phase 6: US4 - Risk Manager Integration (Priority: P2)

**Goal**: Integrate with Spec 011 RiskManager for automatic stop-losses

**Independent Test**: Open position, verify stop-loss order auto-created

**Dependencies**: Spec 011 (Stop-Loss & Position Limits) ✅ **COMPLETE**

### Implementation for US4

- [X] T042 [P] [US4] Create strategies/hyperliquid/config.py with HyperliquidStrategyConfig
- [X] T043 [US4] Add RiskConfig integration from Spec 011 in config.py
- [X] T044 [US4] Add instrument_id, order_size, max_position_size fields in config.py
- [X] T045 [P] [US4] Create strategies/hyperliquid/base_strategy.py with RiskManager
- [X] T046 [US4] Implement on_start() with data subscriptions in base_strategy.py
- [X] T047 [US4] Implement on_event() with RiskManager.handle_event() in base_strategy.py
- [X] T048 [US4] Verify stop-loss orders placed on PositionOpened
- [X] T049 [US4] Verify position limits enforced before order submission
- [X] T050 [P] [US4] Write integration test for RiskManager in tests/hyperliquid/test_risk_integration.py

**Checkpoint**: US4 complete - RiskManager integration operational

---

## Phase 7: US5 - Testnet Validation (Priority: P3)

**Goal**: Full order lifecycle validation on Hyperliquid testnet

**Independent Test**: Execute complete trade cycle (open → stop-loss → close)

### Implementation for US5

- [X] T051 [US5] Document testnet credential setup in configs/hyperliquid/README.md
- [X] T052 [US5] Create end-to-end test script scripts/hyperliquid/validate_testnet.py
- [X] T053 [US5] Test: Connect to testnet with testnet=True
- [X] T054 [US5] Test: Open position (MARKET BUY)
- [X] T055 [US5] Test: Verify stop-loss auto-created by RiskManager
- [X] T056 [US5] Test: Close position (MARKET SELL reduce_only=True)
- [X] T057 [US5] Test: Verify reconciliation on TradingNode restart
- [X] T058 [P] [US5] Write comprehensive integration test in tests/hyperliquid/integration/test_live_cycle.py

**Checkpoint**: US5 complete - testnet validation passed

---

## Phase 8: Production Configuration

**Purpose**: Production-ready configuration and launcher scripts

- [X] T059 [P] Create configs/hyperliquid/trading_node.py with full production config
- [X] T060 Add data_clients and exec_clients to trading_node.py
- [X] T061 Add CacheConfig with Redis in trading_node.py (from Spec 014 patterns)
- [X] T062 Add LiveExecEngineConfig with reconciliation in trading_node.py
- [X] T063 [P] Create scripts/hyperliquid/run_live.py launcher script
- [X] T064 Add environment variable validation in run_live.py (verify HYPERLIQUID_*_PK not in code per NFR-003)
- [X] T065 Add graceful shutdown handling in run_live.py
- [X] T066 Add logging configuration in run_live.py

**Checkpoint**: Production config ready

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final validation

- [X] T067 [P] Update configs/hyperliquid/__init__.py with all exports
- [X] T068 [P] Update strategies/hyperliquid/__init__.py with all exports
- [X] T069 Run ruff format and ruff check on configs/ and strategies/
- [X] T070 Run alpha-debug verification on critical files
- [X] T071 Update quickstart.md with final usage examples
- [X] T072 Verify all tests pass with coverage > 80%

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational
- **US2 (Phase 4)**: Depends on US1 (needs data streaming)
- **US3 (Phase 5)**: Depends on Foundational (data client not required for exec)
- **US4 (Phase 6)**: Depends on US3 + Spec 011
- **US5 (Phase 7)**: Depends on US3, US4
- **Production (Phase 8)**: Depends on US1-US5
- **Polish (Phase 9)**: Depends on all phases

### User Story Dependencies

```
            ┌─────────────────┐
            │   Foundational  │
            │    (Phase 2)    │
            └────────┬────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │   US1   │ │   US3   │ │ (US3)   │
    │  Data   │ │  Exec   │ │ Parallel│
    └────┬────┘ └────┬────┘ └─────────┘
         │           │
         ▼           │
    ┌─────────┐      │
    │   US2   │      │
    │Persist  │      │
    └─────────┘      │
                     ▼
              ┌─────────────┐
              │    US4      │
              │ RiskManager │◄── Spec 011
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │    US5      │
              │  Testnet    │
              └─────────────┘
```

### Parallel Opportunities

- T003, T004, T005, T006: Setup tasks in parallel
- T010: Unit test in parallel with implementation
- T015, T020: US1 scripts and tests in parallel
- T021, T028: US2 persistence and tests in parallel
- T029, T034, T041: US3 files in parallel
- T042, T045, T050: US4 files in parallel
- T059, T063: Production config and scripts in parallel
- T067, T068: Init file updates in parallel

---

## Parallel Example: US3 (Order Execution)

```bash
# Phase 5 can parallelize file creation:
Task: "Create configs/hyperliquid/exec_client.py" (T029)
Task: "Create scripts/hyperliquid/test_orders.py" (T034)
Task: "Write unit test for exec client" (T041)

# Then sequential implementation:
Task: "Implement create_hyperliquid_exec_client()" (T030)
Task: "Implement MARKET order submission" (T035)
Task: "Implement LIMIT order submission" (T036)
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (factory function)
3. Complete Phase 3: US1 (Live Data Feed)
4. Complete Phase 4: US2 (Data Persistence)
5. **STOP and VALIDATE**: Data streaming + recording works
6. Can start backtesting with real Hyperliquid data!

### Full Live Trading

1. MVP complete
2. Complete Phase 5: US3 (Order Execution)
3. Complete Phase 6: US4 (RiskManager)
4. Complete Phase 7: US5 (Testnet Validation)
5. Complete Phase 8: Production Config
6. **READY FOR MAINNET** (with small positions first!)

### Key Milestones

| Milestone | Tasks Complete | Deliverable |
|-----------|----------------|-------------|
| Data Streaming | T001-T020 | Live BTC/ETH data from Hyperliquid |
| Data Recording | T021-T028 | ParquetDataCatalog with HL data |
| Testnet Orders | T029-T041 | Orders executing on testnet |
| Risk Protected | T042-T050 | Auto stop-loss with RiskManager |
| Validated | T051-T058 | Full lifecycle tested |
| Production | T059-T066 | Ready for mainnet |

---

## Notes

- [P] tasks = different files, no dependencies
- [US#] label maps task to user story from spec.md
- Uses native HyperliquidDataClient/ExecClient - no custom wrappers (KISS)
- ExecClient is "building" phase - testnet validation critical
- Requires NautilusTrader Nightly >= 1.222.0
- Depends on Spec 011 (Stop-Loss) for US4 RiskManager integration
- Private keys ONLY via environment variables (HYPERLIQUID_TESTNET_PK, HYPERLIQUID_MAINNET_PK)
- Start with testnet=True, validate before mainnet
