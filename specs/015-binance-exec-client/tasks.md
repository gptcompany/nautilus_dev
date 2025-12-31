# Tasks: Binance Exec Client Integration

**Input**: Design documents from `/specs/015-binance-exec-client/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Integration tests on Binance testnet per spec.md Testing Strategy.

**Organization**: Tasks grouped by functional requirement (FR-001 through FR-005) from spec.md.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which functional requirement this task belongs to (FR1-FR5)

---

## Phase 1: Setup (Fix Existing Code)

**Purpose**: Fix enum values to work with NautilusTrader nightly v1.222.0+

- [X] T001 Fix BinanceAccountType enum mapping (USDT_FUTURES → USDT_FUTURE) in config/clients/binance.py
      *VERIFIED: NautilusTrader nightly v1.222.0 uses USDT_FUTURES (plural) - current code is correct*
- [X] T002 Fix BinanceAccountType enum mapping in config/factory.py
      *VERIFIED: NautilusTrader nightly v1.222.0 uses USDT_FUTURES (plural) - current code is correct*
- [X] T003 [P] Verify nightly environment has NautilusTrader >= 2025-12-10 (Algo Order API fix)
      *VERIFIED: OrderFactory has stop_market and stop_limit methods available*
- [X] T004 [P] Add BINANCE_TESTNET env var support in config/.env.example
      *CREATED: config/.env.example with all required environment variables*

**Checkpoint**: Enum values compatible with nightly - factory creates valid configs

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ensure TradingNodeConfigFactory integration works before adding new features

**⚠️ CRITICAL**: No FR work can begin until this phase is complete

- [X] T005 Verify Spec 014 (TradingNode Configuration) is complete - test config/factory.py creates TradingNodeConfig
      *VERIFIED: TradingNodeConfigFactory.from_settings() creates valid TradingNodeConfig with Binance exec client*
- [X] T006 [P] Create test fixtures for Binance config in tests/conftest.py (mock credentials, testnet=True)
      *VERIFIED: Fixtures already exist in tests/tradingnode_config/conftest.py*
- [X] T007 Write unit test for build_binance_exec_client_config() in tests/test_binance_config.py
      *VERIFIED: Unit tests exist in tests/tradingnode_config/test_config_clients.py*

**Checkpoint**: Factory integration verified - FR implementation can now begin

---

## Phase 3: FR-001 - Client Configuration (Priority: P1) 🎯 MVP

**Goal**: Complete BinanceExecClientConfig with all required parameters per spec.md

**Independent Test**: `build_binance_exec_client_config()` returns valid config that can be passed to TradingNode

### Implementation for FR-001

- [X] T008 [FR1] Add warn_rate_limits=True to build_binance_exec_client_config() in config/clients/binance.py
      *SKIPPED: warn_rate_limits not available in NautilusTrader nightly v1.222.0*
- [X] T009 [FR1] Add retry parameters (max_retries, retry_delay_initial_ms, retry_delay_max_ms) in config/clients/binance.py
      *IMPLEMENTED: Added with defaults 3, 500, 5000*
- [X] T010 [FR1] Add futures_leverages parameter support in config/clients/binance.py
      *IMPLEMENTED: Symbol to leverage mapping with BinanceSymbol keys*
- [X] T011 [FR1] Add futures_margin_types parameter support in config/clients/binance.py
      *IMPLEMENTED: Symbol to margin type (CROSS/ISOLATED) mapping*
- [X] T012 [FR1] Update build_binance_data_client_config() with matching account_type fix in config/clients/binance.py
      *VERIFIED: Already correct - added update_instruments_interval_mins param*
- [X] T013 [FR1] Update unit test for all config parameters in tests/test_binance_config.py
      *IMPLEMENTED: 13 tests in tests/tradingnode_config/test_config_clients.py - all passing*

**Checkpoint**: FR-001 complete - client config fully parameterized with all options

---

## Phase 4: FR-002 - Order Types Support (Priority: P1) 🎯 MVP

**Goal**: Helper functions for MARKET, LIMIT, STOP_MARKET, STOP_LIMIT orders per spec.md

**Independent Test**: Each helper creates valid NautilusTrader order objects

### Implementation for FR-002

- [X] T014 [P] [FR2] Create config/order_helpers.py with module docstring and imports
- [X] T015 [FR2] Implement create_market_order() helper in config/order_helpers.py
- [X] T016 [FR2] Implement create_limit_order() helper (with post_only param) in config/order_helpers.py
- [X] T017 [FR2] Implement create_stop_market_order() helper (Algo API) in config/order_helpers.py
- [X] T018 [FR2] Implement create_stop_limit_order() helper (Algo API) in config/order_helpers.py
- [X] T019 [FR2] Add order validation function validate_order_params() in config/order_helpers.py
- [X] T020 [FR2] Export helpers from config/__init__.py
- [X] T021 [P] [FR2] Write unit tests for all order helpers in tests/test_order_helpers.py
      *IMPLEMENTED: 25 tests passing in tests/tradingnode_config/test_order_helpers.py*

**Checkpoint**: FR-002 complete - all 4 MVP order types supported

---

## Phase 5: FR-003 - Position Mode (Priority: P2)

**Goal**: Configure ONE-WAY (NETTING) mode as default, document HEDGE mode limitation

**Independent Test**: Config enforces NETTING mode, warns on HEDGE mode attempt

### Implementation for FR-003

- [ ] T022 [FR3] Add use_reduce_only=True to ensure NETTING mode in config/clients/binance.py
- [ ] T023 [FR3] Add docstring warning about HEDGE mode bug #3104 in config/clients/binance.py
- [ ] T024 [FR3] Update research.md with HEDGE mode limitation details in specs/015-binance-exec-client/research.md
- [ ] T025 [FR3] Add unit test verifying use_reduce_only=True default in tests/test_binance_config.py

**Checkpoint**: FR-003 complete - position mode safely configured

---

## Phase 6: FR-004 - Error Handling (Priority: P2)

**Goal**: Graceful handling of Binance-specific errors per spec.md FR-004

**Independent Test**: Error scenarios logged correctly, retryable errors identified

### Implementation for FR-004

- [ ] T026 [P] [FR4] Create config/binance_errors.py with module docstring
- [ ] T027 [FR4] Define BINANCE_ERROR_CODES dict (rate limit -1003, balance -2010, algo -4120) in config/binance_errors.py
- [ ] T028 [FR4] Implement is_retryable_error() function in config/binance_errors.py
- [ ] T029 [FR4] Implement get_error_message() function in config/binance_errors.py
- [ ] T030 [FR4] Implement calculate_backoff_delay() with exponential backoff in config/binance_errors.py
- [ ] T031 [FR4] Export error helpers from config/__init__.py
- [ ] T032 [P] [FR4] Write unit tests for error handling in tests/test_binance_errors.py

**Checkpoint**: FR-004 complete - robust error handling with backoff

---

## Phase 7: FR-005 - External Order Claims (Priority: P3)

**Goal**: Support reconciliation of existing positions per spec.md FR-005

**Independent Test**: Strategy config accepts external_order_claims list

### Implementation for FR-005

- [ ] T033 [FR5] Add create_external_claims() helper in config/order_helpers.py
- [ ] T034 [FR5] Document external_order_claims pattern in config/order_helpers.py docstring
- [ ] T035 [FR5] Add unit test for external claims helper in tests/test_order_helpers.py

**Checkpoint**: FR-005 complete - reconciliation ready

---

## Phase 8: Integration Testing (Testnet)

**Purpose**: Validate complete order lifecycle on Binance testnet per spec.md Testing Strategy

### Integration Tests

- [ ] T036 [P] Create tests/integration/test_binance_testnet.py with base fixtures and skip marker
- [ ] T037 Add testnet connection test (requires BINANCE_TESTNET_API_KEY) in tests/integration/test_binance_testnet.py
- [ ] T038 Add MARKET order round-trip test with latency assertion (<100ms) in tests/integration/test_binance_testnet.py
- [ ] T039 Add LIMIT order lifecycle test (submit, verify, cancel) in tests/integration/test_binance_testnet.py
- [ ] T040 Add STOP_MARKET order test (Algo Order API) in tests/integration/test_binance_testnet.py
- [ ] T041 Add fill notification latency test (<50ms) in tests/integration/test_binance_testnet.py
- [ ] T042 Add WebSocket reconnection test in tests/integration/test_binance_testnet.py

**Checkpoint**: All testnet integration tests passing

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final validation

- [ ] T043 [P] Update quickstart.md with final usage examples in specs/015-binance-exec-client/quickstart.md
- [ ] T044 [P] Update CLAUDE.md with Binance exec client section if not present
- [ ] T045 Run ruff format and ruff check on config/ and tests/
- [ ] T046 Run alpha-debug verification on config/clients/binance.py and config/order_helpers.py
- [ ] T047 Verify test coverage >= 80% for new code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - CRITICAL fix for enum values
- **Foundational (Phase 2)**: Depends on Setup - verifies Spec 014 integration
- **FR-001 (Phase 3)**: Depends on Foundational - client config
- **FR-002 (Phase 4)**: Depends on Foundational - order helpers (can run parallel with FR-003, FR-004)
- **FR-003 (Phase 5)**: Depends on Foundational - position mode (can run parallel with FR-002, FR-004)
- **FR-004 (Phase 6)**: Depends on Foundational - error handling (can run parallel with FR-002, FR-003)
- **FR-005 (Phase 7)**: Depends on FR-002 (uses order_helpers.py)
- **Integration Testing (Phase 8)**: Depends on FR-001, FR-002, FR-004
- **Polish (Phase 9)**: Depends on Integration Testing

### Functional Requirement Dependencies

```
Setup (Phase 1) ─┐
                 ├─> Foundational (Phase 2) ─┬─> FR-001 (P1) ─────────────────┐
                 │                            ├─> FR-002 (P1) ─┬─> FR-005 (P3)├─> Integration ─> Polish
                 │                            ├─> FR-003 (P2)  │              │
                 │                            └─> FR-004 (P2) ─┴──────────────┘
```

### Within Each FR

- Unit tests can be written in parallel with implementation (if in different files)
- Config changes before validation logic
- Core implementation before integration points

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003, T004 can run in parallel (different files)

**Phase 2 (Foundational)**:
- T006 (conftest.py) can run parallel with T007 (test file)

**Phase 4 (FR-002)**:
- T014 (create file) || T021 (test file) - different files

**Phase 6 (FR-004)**:
- T026 (create file) || T032 (test file) - different files

**Phase 8 (Integration)**:
- T036 can run parallel while waiting for previous phases

**Phase 9 (Polish)**:
- T043, T044 can run in parallel (different files)

---

## Implementation Strategy

### MVP First (FR-001 + FR-002 Only)

1. Complete Phase 1: Setup (fix enum values - CRITICAL)
2. Complete Phase 2: Foundational (verify integration)
3. Complete Phase 3: FR-001 (client config)
4. Complete Phase 4: FR-002 (order helpers)
5. **STOP and VALIDATE**: Test config creation and order helpers
6. Can submit orders via TradingNode

### Incremental Delivery

1. Setup + Foundational → Factory works with nightly
2. Add FR-001 → Full config parameterization → Ship
3. Add FR-002 → Order helpers → Ship (MVP!)
4. Add FR-003 + FR-004 → Position mode + error handling → Ship
5. Add FR-005 → Reconciliation → Ship
6. Integration Testing → Testnet validation → Production ready

### Key Milestones

| Milestone | Tasks Complete | Deliverable |
|-----------|----------------|-------------|
| Enum Fixed | T001-T004 | Factory works with nightly |
| Config Complete | T005-T013 | Full BinanceExecClientConfig |
| Orders Ready | T014-T021 | All 4 MVP order types |
| Error Handling | T026-T032 | Robust error handling |
| Production Ready | T036-T042 | Testnet validated |

---

## Notes

- [P] tasks = different files, no dependencies
- [FR#] label maps task to functional requirement from spec.md
- Uses native BinanceExecClientConfig - no custom wrappers (KISS)
- ONE-WAY mode only due to HEDGE mode bug #3104
- Requires NautilusTrader Nightly >= 2025-12-10 for Algo Order API
- CRITICAL: T001-T002 fix enum values (USDT_FUTURES → USDT_FUTURE) - breaks without this
- NFR-002 (auto-reconnect) handled by native adapter - integration tests validate behavior
- MVP scope: MARKET, LIMIT, STOP_MARKET, STOP_LIMIT (TRAILING_STOP deferred to v2)
