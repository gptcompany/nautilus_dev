# Tasks: Stop-Loss & Position Limits

**Input**: Design documents from `/specs/011-stop-loss-position-limits/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included as this is a core risk management module requiring high reliability.

**Organization**: Tasks organized by user story for independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - complex algorithmic tasks
- **[Story]**: User story mapping (US1, US2, US3)

---

## Phase 1: Setup (Project Structure)

**Purpose**: Initialize risk module directory structure

- [X] T001 Create risk module directory structure: `risk/__init__.py`
- [X] T002 [P] Add risk module dependencies to project (Pydantic >= 2.0)
- [X] T003 [P] Create test directory structure: `tests/test_risk_config.py`, `tests/test_risk_manager.py`, `tests/integration/test_risk_backtest.py`

---

## Phase 2: Foundational (Core Types & Configuration)

**Purpose**: Define configuration model and enums - MUST complete before user stories

**⚠️ CRITICAL**: RiskConfig is required by all subsequent phases

- [X] T004 Create StopLossType enum in `risk/config.py` (market, limit, emulated)
- [X] T005 Create TrailingOffsetType enum in `risk/config.py` (price, basis_points)
- [X] T006 Create RiskConfig Pydantic model in `risk/config.py` with validation
- [X] T007 Add RiskConfig JSON serialization support (model_dump_json)
- [X] T008 [P] Write unit tests for RiskConfig validation in `tests/test_risk_config.py`
- [X] T009 Export public API in `risk/__init__.py` (RiskConfig, StopLossType, TrailingOffsetType)

**Checkpoint**: Foundation ready - RiskConfig validated, user story implementation can begin

---

## Phase 3: User Story 1 - Automatic Stop-Loss (Priority: P1) 🎯 MVP

**Goal**: Every position entry automatically generates a corresponding stop-loss order

**Independent Test**: Open a position in backtest → verify stop-loss order created with correct price

### Tests for User Story 1

**NOTE: Write tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `_calculate_stop_price()` LONG/SHORT in `tests/test_risk_manager.py`
- [X] T011 [P] [US1] Unit test for `_create_stop_order()` with reduce_only in `tests/test_risk_manager.py`
- [X] T012 [P] [US1] Unit test for `handle_event()` routing in `tests/test_risk_manager.py`
- [X] T013 [US1] Unit test for `_on_position_opened()` creates stop in `tests/test_risk_manager.py`
- [X] T014 [US1] Unit test for `_on_position_closed()` cancels stop in `tests/test_risk_manager.py`

### Implementation for User Story 1

- [X] T015 [US1] Create RiskManager class skeleton in `risk/manager.py` (implements IRiskManager)
- [X] T016 [US1] Implement `__init__()` with config and strategy reference in `risk/manager.py`
- [X] T017 [US1] Implement `active_stops` property (dict[PositionId, ClientOrderId]) in `risk/manager.py`
- [X] T018 [E] [US1] Implement `_calculate_stop_price()` for LONG and SHORT positions in `risk/manager.py`
- [X] T019 [US1] Implement `_create_stop_order()` with STOP_MARKET and reduce_only=True in `risk/manager.py`
- [X] T020 [US1] Implement `_on_position_opened()` - create and submit stop in `risk/manager.py`
- [X] T021 [US1] Implement `_on_position_closed()` - cancel stop order in `risk/manager.py`
- [X] T022 [US1] Implement `handle_event()` routing for PositionOpened/Closed in `risk/manager.py`
- [X] T023 [US1] Add logging for stop-loss operations in `risk/manager.py`
- [X] T024 [US1] Export RiskManager in `risk/__init__.py`

**Checkpoint**: US1 complete - positions automatically get stop-loss orders

---

## Phase 4: User Story 2 - Position Limits (Priority: P2)

**Goal**: Enforce maximum position size per instrument and total exposure

**Independent Test**: Attempt order exceeding limit → verify rejection with clear message

### Tests for User Story 2

- [X] T025 [P] [US2] Unit test for `validate_order()` per-instrument limit in `tests/test_risk_manager.py`
- [X] T026 [P] [US2] Unit test for `validate_order()` total exposure limit in `tests/test_risk_manager.py`
- [X] T027 [US2] Unit test for `validate_order()` returns True when within limits in `tests/test_risk_manager.py`

### Implementation for User Story 2

- [X] T028 [US2] Implement `_get_current_position_size()` helper in `risk/manager.py`
- [X] T029 [US2] Implement `_get_total_exposure()` helper in `risk/manager.py`
- [X] T030 [US2] Implement `validate_order()` per-instrument check in `risk/manager.py`
- [X] T031 [US2] Implement `validate_order()` total exposure check in `risk/manager.py`
- [X] T032 [US2] Add logging for order rejections in `risk/manager.py`

**Checkpoint**: US2 complete - orders exceeding limits are rejected

---

## Phase 5: User Story 3 - Integration Testing (Priority: P3)

**Goal**: Verify end-to-end behavior with BacktestNode

**Independent Test**: Run full backtest with risk management → verify stops execute, limits enforced

### Tests for User Story 3

- [ ] T033 [US3] Integration test: stop-loss execution on price drop in `tests/integration/test_risk_backtest.py`
- [ ] T034 [US3] Integration test: stop-loss with gap-through scenario in `tests/integration/test_risk_backtest.py`
- [ ] T035 [US3] Integration test: position limit rejection in `tests/integration/test_risk_backtest.py`
- [ ] T036 [US3] Integration test: multiple positions with separate stops in `tests/integration/test_risk_backtest.py`

### Implementation for User Story 3

- [ ] T037 [US3] Create example strategy using RiskManager in `strategies/examples/risk_managed_strategy.py`
- [ ] T038 [US3] Create backtest configuration for risk testing in `tests/integration/test_risk_backtest.py`
- [ ] T039 [US3] Add edge case handling: position closed before stop created in `risk/manager.py`
- [ ] T040 [US3] Add edge case handling: OrderFilled event for stop order in `risk/manager.py`

**Checkpoint**: US3 complete - full integration verified with BacktestNode

---

## Phase 6: User Story 4 - Advanced Features (Priority: P4 - Optional)

**Goal**: Trailing stops and STOP_LIMIT support

**Independent Test**: Enable trailing stop → verify stop price updates on favorable moves

### Tests for User Story 4

- [ ] T041 [P] [US4] Unit test for `_on_position_changed()` trailing update in `tests/test_risk_manager.py`
- [ ] T042 [P] [US4] Unit test for `_create_stop_order()` with STOP_LIMIT type in `tests/test_risk_manager.py`

### Implementation for User Story 4

- [ ] T043 [US4] Implement `_on_position_changed()` for trailing stop in `risk/manager.py`
- [ ] T044 [US4] Add trailing stop price calculation logic in `risk/manager.py`
- [ ] T045 [US4] Implement STOP_LIMIT order creation in `_create_stop_order()` in `risk/manager.py`
- [ ] T046 [US4] Update `handle_event()` to route PositionChanged events in `risk/manager.py`

**Checkpoint**: US4 complete - trailing stops and STOP_LIMIT working

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, verification

- [ ] T047 [P] Update quickstart.md with verified examples in `specs/011-stop-loss-position-limits/quickstart.md`
- [ ] T048 [P] Add docstrings to all public methods in `risk/manager.py`
- [ ] T049 Run `ruff check risk/ tests/` and fix any issues
- [ ] T050 Run alpha-debug verification on `risk/manager.py`
- [ ] T051 Verify test coverage > 80% for risk module

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3+ (User Stories)
                                          ├── US1: Stop-Loss (P1) 🎯 MVP
                                          ├── US2: Position Limits (P2)
                                          ├── US3: Integration Testing (P3)
                                          └── US4: Advanced Features (P4)
                                                        ↓
                                          Phase 7 (Polish)
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 (RiskConfig) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on Phase 2 - Independent of US1
- **User Story 3 (P3)**: Depends on US1 and US2 (integration testing requires both)
- **User Story 4 (P4)**: Depends on US1 (extends stop-loss functionality)

### Critical Path

```
T001 → T004-T006 → T015-T024 (US1 complete = MVP)
```

### Parallel Opportunities

**Phase 2 (can run together)**:
- T008 (tests) can run parallel with T004-T007 (implementation)

**Phase 3 - US1 Tests (can run together)**:
- T010, T011, T012 (different test functions)

**Phase 4 - US2 Tests (can run together)**:
- T025, T026 (different test functions)

**Phase 6 - US4 Tests (can run together)**:
- T041, T042 (different test functions)

**Phase 7 - Polish (can run together)**:
- T047, T048 (different files)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T009)
3. Complete Phase 3: User Story 1 (T010-T024)
4. **STOP and VALIDATE**: Test stop-loss generation independently
5. Deploy/demo if ready - basic risk protection working

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP! Stop-loss protection active**
3. Add User Story 2 → Test independently → Position limits enforced
4. Add User Story 3 → Integration verified
5. Add User Story 4 → Advanced features (optional)
6. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [E] tasks = complex algorithms triggering alpha-evolve (T018: stop price calculation)
- **CRITICAL**: Always use `reduce_only=True` for stop orders to prevent position flip
- **CRITICAL**: Use NautilusTrader nightly >= 1.222.0 for Binance/Bybit support
- Config validation tests (T008) should test: invalid percentages, negative values, edge cases
- Integration tests require real market data (use ParquetDataCatalog)

### Edge Cases Handled by Design

- **Partial fills**: No special task needed - NautilusTrader PositionOpened event contains actual filled quantity; stop-loss uses actual position size
- **OCO pairing**: Out of MVP scope - manual cancellation via `on_order_filled()` documented in spec.md
- **Persistence/restart recovery**: Out of MVP scope (backtest-only) - documented in spec.md NFR-002
