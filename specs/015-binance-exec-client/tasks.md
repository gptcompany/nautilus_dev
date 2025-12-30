# Tasks: Binance Exec Client Integration (Spec 015)

**Input**: Design documents from `/specs/015-binance-exec-client/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Integration tests included for testnet validation per spec.md Testing Strategy.

**Organization**: Tasks grouped by functional requirement (FR-001 through FR-005).

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which functional requirement this task belongs to (FR1, FR2, etc.)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency on Spec 014

- [ ] T001 Verify Spec 014 (TradingNode Configuration) is complete in config/tradingnode_factory.py
- [ ] T002 Create config/binance_exec.py with module docstring and imports
- [ ] T003 [P] Verify nightly environment has NautilusTrader >= 2025-12-10 (Algo Order API fix)
- [ ] T004 [P] Configure environment variables template in config/.env.example

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core factory function that MUST be complete before order types can be implemented

**⚠️ CRITICAL**: No FR-002+ work can begin until this phase is complete

- [ ] T005 Implement create_binance_exec_client() factory in config/binance_exec.py
- [ ] T006 Add environment variable sourcing (BINANCE_API_KEY, BINANCE_API_SECRET) in config/binance_exec.py
- [ ] T007 Add testnet vs production configuration logic in config/binance_exec.py
- [ ] T008 [P] Add create_binance_instrument_provider() in config/binance_exec.py
- [ ] T009 [P] Write unit test for factory in tests/test_binance_exec.py
- [ ] T010 Update config/__init__.py to export new functions

**Checkpoint**: Factory ready - order type implementation can now begin

---

## Phase 3: FR-001 - Client Configuration (Priority: P1) 🎯 MVP

**Goal**: Complete BinanceExecClientConfig with all required parameters

**Independent Test**: Factory creates valid config that can be passed to TradingNode

### Implementation for FR-001

- [ ] T011 [FR1] Add account_type parameter (USDT_FUTURES default) in config/binance_exec.py
- [ ] T012 [FR1] Add use_position_ids=True (NETTING mode) in config/binance_exec.py
- [ ] T013 [FR1] Add max_retries, retry_delay_initial_ms, retry_delay_max_ms params in config/binance_exec.py
- [ ] T014 [FR1] Add futures_leverages and futures_margin_types mapping in config/binance_exec.py
- [ ] T015 [FR1] Add warn_rate_limits=True in config/binance_exec.py
- [ ] T016 [FR1] Update unit test for all config parameters in tests/test_binance_exec.py

**Checkpoint**: FR-001 complete - client config fully parameterized

---

## Phase 4: FR-002 - Order Types Support (Priority: P2)

**Goal**: Helper functions for MARKET, LIMIT, STOP_MARKET, STOP_LIMIT orders

**Independent Test**: Each order type creates valid NautilusTrader order objects

### Implementation for FR-002

- [ ] T017 [P] [FR2] Create config/order_helpers.py with module docstring
- [ ] T018 [FR2] Implement create_market_order() helper in config/order_helpers.py
- [ ] T019 [FR2] Implement create_limit_order() helper in config/order_helpers.py
- [ ] T020 [FR2] Implement create_stop_market_order() helper (Algo API) in config/order_helpers.py
- [ ] T021 [FR2] Implement create_stop_limit_order() helper (Algo API) in config/order_helpers.py
- [ ] T022 [FR2] Add order validation utilities (quantity, price checks) in config/order_helpers.py
- [ ] T023 [P] [FR2] Write unit tests for order helpers in tests/test_order_helpers.py

**Checkpoint**: FR-002 complete - all order types supported

---

## Phase 5: FR-003 - Position Mode (Priority: P2)

**Goal**: Configure ONE-WAY (NETTING) mode as default, document HEDGE mode limitation

**Independent Test**: Config enforces NETTING mode, warns on HEDGE mode attempt

### Implementation for FR-003

- [ ] T024 [FR3] Add position_mode parameter with NETTING default in config/binance_exec.py
- [ ] T025 [FR3] Add warning log if HEDGE mode requested (known bug #3104) in config/binance_exec.py
- [ ] T026 [FR3] Document HEDGE mode limitation in config/binance_exec.py docstring
- [ ] T027 [FR3] Update unit test for position mode in tests/test_binance_exec.py

**Checkpoint**: FR-003 complete - position mode safely configured

---

## Phase 6: FR-004 - Error Handling (Priority: P2)

**Goal**: Graceful handling of Binance-specific errors

**Independent Test**: Error scenarios logged correctly, no crashes on transient errors

### Implementation for FR-004

- [ ] T028 [P] [FR4] Create config/binance_errors.py with error code definitions
- [ ] T029 [FR4] Define BINANCE_ERROR_CODES dict (rate limit, insufficient balance, etc.) in config/binance_errors.py
- [ ] T030 [FR4] Implement is_retryable_error() function in config/binance_errors.py
- [ ] T031 [FR4] Implement get_error_message() function in config/binance_errors.py
- [ ] T032 [FR4] Add exponential backoff helper calculate_backoff_delay() in config/binance_errors.py
- [ ] T033 [P] [FR4] Write unit tests for error handling in tests/test_binance_errors.py

**Checkpoint**: FR-004 complete - robust error handling

---

## Phase 7: FR-005 - External Order Claims (Priority: P3)

**Goal**: Support reconciliation of existing positions

**Independent Test**: Strategy config accepts external_order_claims list

### Implementation for FR-005

- [ ] T034 [FR5] Add external_order_claims helper in config/binance_exec.py
- [ ] T035 [FR5] Document external_order_claims pattern in config/binance_exec.py docstring
- [ ] T036 [FR5] Update unit test for external claims in tests/test_binance_exec.py

**Checkpoint**: FR-005 complete - reconciliation ready

---

## Phase 8: Integration Testing (Testnet)

**Purpose**: Validate complete order lifecycle on Binance testnet

### Integration Tests

- [ ] T037 [P] Create tests/integration/test_binance_testnet.py with base fixtures
- [ ] T038 Add testnet connection test in tests/integration/test_binance_testnet.py
- [ ] T039 Add market order round-trip test with latency assertion (<100ms) in tests/integration/test_binance_testnet.py
- [ ] T040 Add limit order lifecycle test in tests/integration/test_binance_testnet.py
- [ ] T041 Add stop market order (Algo API) test in tests/integration/test_binance_testnet.py
- [ ] T041b Add fill notification latency assertion (<50ms) in tests/integration/test_binance_testnet.py
- [ ] T042 Add rate limit handling test in tests/integration/test_binance_testnet.py
- [ ] T043 Add WebSocket reconnection test in tests/integration/test_binance_testnet.py

**Checkpoint**: All testnet integration tests passing

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and final validation

- [ ] T044 [P] Update quickstart.md with final usage examples in specs/015-binance-exec-client/quickstart.md
- [ ] T045 Run ruff format and ruff check on config/ and tests/
- [ ] T046 Run alpha-debug verification on config/binance_exec.py
- [ ] T047 Update CLAUDE.md if architecture changes required

**Note**: config/__init__.py exports are handled in T010 (Foundational phase).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Depends on Spec 014 completion
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all FRs
- **FR-001 (Phase 3)**: Depends on Foundational
- **FR-002 to FR-005 (Phase 4-7)**: All depend on Foundational, can run in parallel
- **Integration Testing (Phase 8)**: Depends on all FRs complete
- **Polish (Phase 9)**: Depends on Integration Testing

### Functional Requirement Dependencies

- **FR-001 (Client Config)**: Foundation - required for all others
- **FR-002 (Order Types)**: Independent of other FRs, depends on FR-001
- **FR-003 (Position Mode)**: Independent, integrates with FR-001
- **FR-004 (Error Handling)**: Independent, used by all order operations
- **FR-005 (External Claims)**: Independent, for restart/recovery scenarios

### Within Each FR

- Unit tests can be written in parallel with implementation
- Config changes before validation logic
- Core implementation before integration points

### Parallel Opportunities

- T003, T004: Setup tasks in parallel
- T008, T009: Foundational tasks in parallel
- T017, T023: FR-002 file creation and tests in parallel
- T028, T033: FR-004 file creation and tests in parallel
- T037: Integration test setup in parallel with FR implementation

---

## Parallel Example: FR-002 (Order Types)

```bash
# Phase 4 can parallelize file creation and tests:
Task: "Create config/order_helpers.py with module docstring" (T017)
Task: "Write unit tests for order helpers in tests/test_order_helpers.py" (T023)

# Then sequential implementation in order_helpers.py:
Task: "Implement create_market_order()" (T018)
Task: "Implement create_limit_order()" (T019)
Task: "Implement create_stop_market_order()" (T020)
Task: "Implement create_stop_limit_order()" (T021)
```

---

## Implementation Strategy

### MVP First (FR-001 Only)

1. Complete Phase 1: Setup (verify Spec 014)
2. Complete Phase 2: Foundational (factory function)
3. Complete Phase 3: FR-001 (Client Configuration)
4. **STOP and VALIDATE**: Factory creates valid config
5. Can integrate with TradingNode from Spec 014

### Incremental Delivery

1. Setup + Foundational → Factory ready
2. Add FR-001 → Test config creation → Integrate with TradingNode (MVP!)
3. Add FR-002 → Test order types → Submit orders
4. Add FR-003 → Configure position mode
5. Add FR-004 → Robust error handling
6. Add FR-005 → Reconciliation support
7. Integration Testing → Testnet validation

### Key Milestones

| Milestone | Tasks Complete | Deliverable |
|-----------|----------------|-------------|
| Factory Ready | T001-T010 | `create_binance_exec_client()` works |
| Config Complete | T011-T016 | Full configuration with all params |
| Orders Ready | T017-T023 | All order types supported |
| Production Ready | T024-T036 | Error handling + reconciliation |
| Validated | T037-T043, T041b | Testnet tests passing |

---

## Notes

- [P] tasks = different files, no dependencies
- [FR#] label maps task to functional requirement from spec.md
- Uses native BinanceExecClientConfig - no custom wrappers (KISS)
- ONE-WAY mode only due to HEDGE mode bug #3104
- Requires NautilusTrader Nightly >= 2025-12-10 for Algo Order API
- Verify Spec 014 (TradingNode Configuration) is complete before starting
- MVP scope: MARKET, LIMIT, STOP_MARKET, STOP_LIMIT (TAKE_PROFIT/TRAILING_STOP deferred to v2)
- NFR-002 (auto-reconnect) handled by native adapter - integration tests validate behavior
