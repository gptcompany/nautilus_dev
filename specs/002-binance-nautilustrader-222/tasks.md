# Tasks: Binance to NautilusTrader v1.222.0 Data Ingestion Pipeline

**Input**: Design documents from `/specs/002-binance-nautilustrader-222/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md, quickstart.md

**Tests**: Integration tests included for critical components (BacktestEngine compatibility verification)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per plan.md in `strategies/binance2nautilus/`
- [x] T002 [P] Create `strategies/binance2nautilus/__init__.py` with public API exports
- [x] T003 [P] Create `strategies/binance2nautilus/config.py` with ConverterConfig Pydantic model

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Create `strategies/binance2nautilus/instruments.py` with CryptoPerpetual definitions (BTCUSDT-PERP, ETHUSDT-PERP)
- [x] T005 [P] Create `strategies/binance2nautilus/state.py` with ConversionState model and load/save functions
- [x] T006 [P] Create `strategies/binance2nautilus/wrangler_factory.py` with V1/V2 factory functions
  - `get_bar_wrangler(instrument, bar_type, config)` - Returns V1 or V2 based on config
  - `get_trade_wrangler(instrument, config)` - Returns V1 or V2 based on config
  - Uses `config.use_rust_wranglers` flag to select implementation
  - **Migration to V2**: Just flip flag when Rust BacktestEngine available
- [x] T007 [P] Create `strategies/binance2nautilus/converters/__init__.py` with converter exports
- [x] T008 Create `strategies/binance2nautilus/converters/base.py` with BaseConverter abstract class

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Initial Bulk Data Conversion (Priority: P1) MVP

**Goal**: Convert 5+ years of Binance historical CSV data to NautilusTrader v1.222.0 ParquetDataCatalog

**Independent Test**: Run conversion on 1-month subset, load catalog in BacktestEngine v1.222.0

### Implementation for User Story 1

- [x] T009 [P] [US1] Create klines CSV parser in `strategies/binance2nautilus/converters/klines.py`
  - Parse Binance klines CSV format (open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore)
  - Transform to DataFrame format expected by wrangler
  - Support 1m, 5m, 15m timeframes

- [x] T010 [P] [US1] Create trades CSV parser in `strategies/binance2nautilus/converters/trades.py`
  - Parse Binance trades CSV format (id, price, qty, quote_qty, time, is_buyer_maker)
  - Transform to DataFrame format expected by wrangler
  - Use chunked processing (100k rows) for memory efficiency

- [x] T011 [US1] Create catalog writer in `strategies/binance2nautilus/catalog.py`
  - Initialize ParquetDataCatalog at output directory
  - Write instrument FIRST, then data
  - Support batch writing for large datasets

- [x] T012 [US1] Implement klines conversion pipeline in `strategies/binance2nautilus/converters/klines.py`
  - Use `wrangler_factory.get_bar_wrangler()` (V2-ready)
  - Create BarType string (e.g., `BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL`)
  - Process all CSV files for specified symbol and timeframe

- [x] T013 [US1] Implement trades conversion pipeline in `strategies/binance2nautilus/converters/trades.py`
  - Use `wrangler_factory.get_trade_wrangler()` (V2-ready)
  - Implement generator pattern for memory-efficient processing
  - Map is_buyer_maker to aggressor_side (True = SELLER)

- [x] T014 [US1] Create validation module in `strategies/binance2nautilus/validate.py`
  - Verify catalog loads without schema errors
  - Check instrument count and data ranges
  - Perform BacktestEngine compatibility test
  - **FR-009**: Verify timestamp precision (nanoseconds) - check ts_event/ts_init are int64 ns
  - **SC-004**: Verify record count matches source CSV count (data integrity)

- [x] T015 [US1] Integration test: Verify BacktestEngine compatibility in `strategies/binance2nautilus/tests/test_integration.py`
  - Load catalog with ParquetDataCatalog
  - Add instrument and bars to BacktestEngine
  - Verify no errors with v1.222.0 full Rust engine

**Checkpoint**: User Story 1 complete - can convert bulk historical data and use with BacktestEngine

---

## Phase 4: User Story 2 - Incremental Daily Updates (Priority: P2)

**Goal**: Support incremental updates when n8n workflow downloads new daily data

**Independent Test**: Simulate new CSV files appearing, verify only new data is appended

### Implementation for User Story 2

- [x] T016 [US2] Implement file scanning in `strategies/binance2nautilus/state.py`
  - Detect new CSV files since last run
  - Track processed files in conversion_state.json
  - Support resumable operations

- [x] T017 [US2] Add incremental update logic to `strategies/binance2nautilus/converters/base.py`
  - Check state before processing each file
  - Skip already-processed files
  - Append new data to existing catalog

- [x] T018 [US2] Implement duplicate detection in `strategies/binance2nautilus/converters/base.py`
  - Check timestamp ranges for overlap
  - Skip duplicate records during incremental updates
  - Log skipped duplicates for audit trail

- [x] T019 [US2] Add update command to `strategies/binance2nautilus/cli.py`
  - Implement `binance2nautilus update [SYMBOL]` command
  - Auto-detect new files and process incrementally
  - Support `--force` flag for reprocessing

**Checkpoint**: User Story 2 complete - can run daily incremental updates

---

## Phase 5: User Story 3 - Multi-Symbol Support (Priority: P2)

**Goal**: Support multiple symbols (BTCUSDT, ETHUSDT) in same catalog

**Independent Test**: Convert both symbols, query each instrument independently

### Implementation for User Story 3

- [x] T020 [P] [US3] Add ETHUSDT instrument definition to `strategies/binance2nautilus/instruments.py`
  - CryptoPerpetual with correct precision (price_precision=2, size_precision=3)
  - Correct fees and margin requirements

- [x] T021 [US3] Update converters to support symbol parameter
  - Modify `strategies/binance2nautilus/converters/klines.py` to accept symbol
  - Modify `strategies/binance2nautilus/converters/trades.py` to accept symbol
  - Use correct instrument based on symbol parameter

- [x] T022 [US3] Add multi-symbol CLI support to `strategies/binance2nautilus/cli.py`
  - Support `--symbols BTCUSDT,ETHUSDT` parameter
  - Process each symbol sequentially (or parallel with --parallel flag)
  - Track state per symbol

- [x] T023 [US3] Validate multi-instrument catalog in `strategies/binance2nautilus/validate.py`
  - Query bars by specific instrument
  - Verify data separation between instruments
  - Test BacktestEngine with multiple instruments

**Checkpoint**: User Story 3 complete - multi-asset backtests possible

---

## Phase 6: User Story 4 - Funding Rate Data Conversion (Priority: P3)

**Goal**: Convert funding rate historical data for accurate perpetual futures PnL calculation

**Independent Test**: Convert funding rate CSV, query by timestamp range

### Implementation for User Story 4

- [x] T024 [P] [US4] Create funding rate converter in `strategies/binance2nautilus/converters/funding.py`
  - Parse Binance funding rate CSV format (calc_time, funding_interval_hours, last_funding_rate)
  - Create custom FundingRate data type compatible with NautilusTrader

- [x] T025 [US4] Implement funding rate storage in `strategies/binance2nautilus/catalog.py`
  - Store as custom data in ParquetDataCatalog via `write_funding_rates()` method
  - Support timestamp range queries

- [x] T026 [US4] Add funding rate to CLI in `strategies/binance2nautilus/cli.py`
  - Support `binance2nautilus convert BTCUSDT funding` command
  - Include in update command

**Checkpoint**: User Story 4 complete - funding rate data available for PnL calculations

---

## Phase 7: CLI & Polish

**Purpose**: Complete CLI interface and cross-cutting improvements

- [x] T027 [P] Create main CLI entry point in `strategies/binance2nautilus/cli.py`
  - Implement Click-based CLI with commands: convert, update, validate, status
  - Add progress bars for long operations (tqdm)
  - Support JSON output mode for automation

- [x] T028 [P] Add status command to `strategies/binance2nautilus/cli.py`
  - Show conversion progress per symbol/data type
  - Display catalog statistics
  - Support --json output

- [x] T029 Create `strategies/binance2nautilus/tests/test_instruments.py`
  - Test CryptoPerpetual creation
  - Verify instrument ID format
  - Test with catalog write/read
  - (Tests in test_integration.py: TestInstruments class)

- [x] T030 [P] Create `strategies/binance2nautilus/tests/test_klines.py`
  - Test CSV parsing
  - Test DataFrame transformation
  - Test wrangler output types

- [x] T031 [P] Create `strategies/binance2nautilus/tests/test_trades.py`
  - Test trades CSV parsing
  - Test chunked processing
  - Test aggressor_side mapping

- [x] T032 Run alpha-debug verification on complete implementation
  - Check for edge cases in timestamp handling
  - Verify precision mode compatibility
  - Check memory usage patterns
  - **Result**: 29/29 tests passing, no critical issues found

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately [DONE]
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in priority order (P1 -> P2 -> P3)
- **CLI & Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - **MVP**
- **User Story 2 (P2)**: Depends on US1 (needs conversion to exist before updates)
- **User Story 3 (P2)**: Can start after Foundational, but benefits from US1 patterns
- **User Story 4 (P3)**: Can start after Foundational, independent of other stories

### Within Each User Story

- CSV parser before conversion pipeline
- Conversion pipeline before validation
- Validation before integration test
- Story complete before moving to next priority

### Parallel Opportunities

- T004, T005, T006 can run in parallel (different files)
- T008, T009 can run in parallel (different converters)
- T019 can run in parallel with other tasks (instrument definition only)
- T028, T029, T030 can run in parallel (different test files)

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all foundational tasks together:
Task: "Create instruments.py with CryptoPerpetual definitions"
Task: "Create state.py with ConversionState model"
Task: "Create converters/__init__.py with exports"
# Then sequentially:
Task: "Create converters/base.py with BaseConverter" (depends on __init__.py)
```

---

## Parallel Example: User Story 1 MVP

```bash
# Launch CSV parsers in parallel:
Task: "Create klines CSV parser in converters/klines.py"
Task: "Create trades CSV parser in converters/trades.py"

# Then implement pipelines sequentially:
Task: "Implement klines conversion pipeline"
Task: "Implement trades conversion pipeline"
Task: "Create catalog writer"

# Finally validate:
Task: "Create validation module"
Task: "Integration test: BacktestEngine compatibility"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup [DONE]
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Bulk Conversion)
4. **STOP and VALIDATE**: Test with quickstart.md guide
5. Verify BacktestEngine compatibility with v1.222.0

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test with BacktestEngine -> MVP!
3. Add User Story 2 -> Enable daily updates
4. Add User Story 3 -> Multi-symbol support
5. Add User Story 4 -> Funding rate data
6. Polish -> CLI completion and testing

---

## Notes

- Use **V1 Wranglers only** (BarDataWrangler, TradeTickDataWrangler) - V2 incompatible with BacktestEngine
- **128-bit precision** (fixed_size_binary[16]) - Linux nightly default
- Chunked processing (100k rows) for trades to avoid memory exhaustion
- All timestamps in nanoseconds (multiply ms * 1_000_000)
- Verify with quickstart.md before full conversion
- Instrument ID format: `BTCUSDT-PERP.BINANCE`
- BarType format: `BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL`
