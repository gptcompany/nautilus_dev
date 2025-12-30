# Feature Specification: Binance to NautilusTrader v1.222.0 Data Ingestion Pipeline

**Feature Branch**: `002-binance-nautilustrader-222`
**Created**: 2025-12-24
**Status**: Draft
**Input**: User description: "Binance to NautilusTrader v1.222.0 data ingestion pipeline - Convert existing raw CSV data (5+ years BTCUSDT/ETHUSDT klines, trades, funding rates from /media/sam/3TB-WDC/binance-history-data-downloader/) to ParquetDataCatalog compatible with Nautilus nightly v1.222.0 full Rust. Include incremental updates integration with existing n8n workflow. Output catalog to /media/sam/2TB-NVMe/nautilus_catalog_v1222/"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initial Bulk Data Conversion (Priority: P1)

As a quant developer, I need to convert my existing 5+ years of Binance historical data (CSV format) into a NautilusTrader v1.222.0 compatible ParquetDataCatalog so that I can run backtests using the full Rust engine.

**Why this priority**: Without the initial bulk conversion, no backtesting is possible. This is the foundational capability that enables all other features.

**Independent Test**: Can be fully tested by running the conversion on a subset of historical data (e.g., 1 month) and verifying the output catalog loads correctly in NautilusTrader v1.222.0 BacktestEngine.

**Acceptance Scenarios**:

1. **Given** raw CSV klines data exists at `/media/sam/3TB-WDC/binance-history-data-downloader/data/BTCUSDT/klines/1m/`, **When** the conversion pipeline runs, **Then** a ParquetDataCatalog is created at `/media/sam/2TB-NVMe/nautilus_catalog_v1222/` with properly formatted Bar objects
2. **Given** raw CSV trades data exists, **When** the conversion pipeline runs, **Then** TradeTick objects are created with correct instrument IDs (e.g., `BTCUSDT-PERP.BINANCE`)
3. **Given** the conversion completes, **When** loading the catalog in NautilusTrader v1.222.0, **Then** no schema errors occur and data is queryable

---

### User Story 2 - Incremental Daily Updates (Priority: P2)

As a quant developer using an automated n8n workflow that downloads new Binance data daily at 03:45, I need the pipeline to support incremental updates so that my catalog stays current without re-processing all historical data.

**Why this priority**: Once initial data exists, keeping it updated is essential for ongoing strategy development and live-to-backtest consistency.

**Independent Test**: Can be tested by simulating a new day's CSV files appearing and verifying only the new data is appended to the catalog.

**Acceptance Scenarios**:

1. **Given** the catalog exists with data up to 2025-12-22, **When** new CSV files for 2025-12-23 are detected, **Then** only the new day's data is converted and appended
2. **Given** the n8n workflow completes at 03:45, **When** the incremental update runs, **Then** processing completes within 10 minutes for a single day's data
3. **Given** duplicate timestamps exist in source data, **When** incremental update runs, **Then** duplicates are detected and skipped

---

### User Story 3 - Multi-Symbol Support (Priority: P2)

As a quant developer, I need to convert data for multiple symbols (BTCUSDT, ETHUSDT) into the same catalog so that I can run multi-asset backtests.

**Why this priority**: Multi-asset strategies require data from multiple symbols in a single catalog.

**Independent Test**: Can be tested by converting both BTCUSDT and ETHUSDT data and querying the catalog for each instrument.

**Acceptance Scenarios**:

1. **Given** CSV data exists for both BTCUSDT and ETHUSDT, **When** conversion runs, **Then** both instruments are available in the catalog with correct instrument IDs
2. **Given** the catalog contains multiple instruments, **When** querying bars for a specific instrument, **Then** only that instrument's data is returned

---

### User Story 4 - Funding Rate Data Conversion (Priority: P3)

As a quant developer, I need funding rate historical data converted so that I can incorporate funding costs into my perpetual futures backtests.

**Why this priority**: Funding rates are important for accurate PnL calculation in futures strategies but are not required for basic price-based strategies.

**Independent Test**: Can be tested by converting funding rate CSV files and verifying they load as custom data in NautilusTrader.

**Acceptance Scenarios**:

1. **Given** funding rate CSV files exist at `fundingRate/` subdirectory, **When** conversion runs, **Then** funding rate data is stored as queryable custom data
2. **Given** funding rate data is loaded, **When** querying by timestamp range, **Then** correct funding rates are returned for the specified period

---

### Edge Cases

- What happens when CSV files have missing or corrupt data (e.g., empty rows, invalid timestamps)?
- How does the system handle timezone differences (Binance uses UTC, verify catalog timestamps are UTC)?
- What happens when disk space is insufficient during conversion?
- How does the system handle schema changes if NautilusTrader releases a new version with different Parquet schema?
- What happens when n8n downloads partial data (interrupted download)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST convert Binance klines CSV files (1m, 5m, 15m timeframes) to NautilusTrader Bar objects
- **FR-002**: System MUST convert Binance trades CSV files to NautilusTrader TradeTick objects
- **FR-003**: System MUST convert Binance funding rate CSV files to NautilusTrader-compatible custom data format
- **FR-004**: System MUST create instrument definitions with correct identifiers (e.g., `BTCUSDT-PERP.BINANCE` for perpetual futures)
- **FR-005**: System MUST output data to ParquetDataCatalog format compatible with NautilusTrader v1.222.0 full Rust engine
- **FR-006**: System MUST support incremental updates (process only new data since last run)
- **FR-007**: System MUST track conversion state to enable resumable operations and prevent duplicate processing
- **FR-008**: System MUST validate output catalog by loading it with NautilusTrader v1.222.0 without errors
- **FR-009**: System MUST preserve timestamp precision (nanosecond) during conversion
- **FR-010**: System MUST handle BTCUSDT and ETHUSDT symbols with option to add more symbols

### Key Entities

- **Bar**: OHLCV candle data with open, high, low, close, volume, and timestamp. Represents aggregated price action over a time period (1m, 5m, 15m).
- **TradeTick**: Individual trade execution with price, size, aggressor side, and timestamp. High-resolution tick data for detailed analysis.
- **Instrument**: Trading instrument definition with symbol, venue, asset class, and contract specifications. Used to identify data in the catalog.
- **FundingRate**: Periodic funding rate for perpetual futures contracts. Custom data type for cost calculations.
- **ConversionState**: Tracks last processed file/timestamp per data type and symbol. Enables incremental processing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Complete initial conversion of 5+ years of BTCUSDT data (all available klines, trades, funding rates) within 2 hours
- **SC-002**: Incremental daily updates complete within 10 minutes for a single day's data across all data types
- **SC-003**: Output catalog loads successfully in NautilusTrader v1.222.0 BacktestEngine with zero schema errors
- **SC-004**: Data integrity maintained: 100% of source records converted with no data loss (verified by record count comparison)
- **SC-005**: Catalog query performance: retrieve 1 month of 1-minute bars in under 5 seconds

## Assumptions

- Source CSV files follow Binance's standard format (columns: open_time, open, high, low, close, volume, close_time, etc.)
- n8n workflow continues to download data to the existing path structure (`/media/sam/3TB-WDC/binance-history-data-downloader/`)
- Target disk (`/media/sam/2TB-NVMe/`) has sufficient space for the Parquet catalog (estimated 50-100GB)
- NautilusTrader v1.222.0 nightly environment is available at `/media/sam/2TB-NVMe/prod/apps/nautilus_nightly/`
- All timestamps in source data are UTC
- Funding rates are stored at 8-hour intervals (standard Binance perpetual funding schedule)

## Dependencies

- NautilusTrader v1.222.0 nightly (for Parquet wranglers and catalog API)
- Existing n8n workflow for daily CSV downloads
- Source data storage at `/media/sam/3TB-WDC/binance-history-data-downloader/`
- Target storage at `/media/sam/2TB-NVMe/nautilus_catalog_v1222/`

## Out of Scope

- Real-time streaming data ingestion (this is for historical data only)
- Order book depth data conversion (bookDepth files)
- Mark price and index price klines conversion
- Automated n8n workflow modifications (integration point only)
- Data quality repair (fixing corrupted source files)
