# Feature Specification: CCXT Multi-Exchange Data Pipeline

**Feature Branch**: `001-ccxt-data-pipeline`
**Created**: 2025-12-22
**Status**: Draft
**Input**: CCXT Multi-Exchange Data Pipeline for fetching Open Interest, Funding Rates, and Liquidations from Binance Futures, Bybit, and Hyperliquid with Parquet storage compatible with NautilusTrader.

## Problem Statement

Trading strategy development requires access to derivative market metrics (Open Interest, Funding Rates, Liquidations) that are not natively available in NautilusTrader. Currently, traders must manually fetch this data from multiple exchanges using different APIs, leading to:

- Inconsistent data formats across exchanges
- Manual effort to normalize and store data
- No unified historical archive for backtesting
- Inability to correlate OI/funding data with price action in strategies

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fetch Current Open Interest (Priority: P1)

As a trader, I want to fetch current Open Interest for BTC and ETH perpetuals from all supported exchanges so I can monitor market positioning in real-time.

**Why this priority**: OI is the most critical metric for understanding market leverage and potential liquidation cascades. This is the foundation for all other features.

**Independent Test**: Can be tested by running a single command that returns OI values for specified symbols, verified against exchange websites.

**Acceptance Scenarios**:

1. **Given** the pipeline is configured with exchange credentials, **When** I request current OI for BTCUSDT-PERP on Binance, **Then** I receive the open interest value in contracts and USD equivalent within 5 seconds.
2. **Given** one exchange is unreachable, **When** I request OI from all exchanges, **Then** I receive data from available exchanges and a clear error message for the failed one.
3. **Given** an invalid symbol is requested, **When** I fetch OI, **Then** I receive a descriptive error message indicating the symbol is not found.

---

### User Story 2 - Fetch Historical Open Interest (Priority: P1)

As a trader, I want to fetch historical Open Interest data so I can analyze how OI changes correlate with price movements during backtesting.

**Why this priority**: Historical data is essential for strategy backtesting and research. Without history, the pipeline has limited value.

**Independent Test**: Can be tested by requesting OI history for a date range and verifying data completeness against known exchange data.

**Acceptance Scenarios**:

1. **Given** I specify a symbol and date range, **When** I request OI history, **Then** I receive time-series data with timestamps and OI values at regular intervals.
2. **Given** I request history for a period longer than exchange limits allow, **When** the fetch completes, **Then** data is paginated automatically and merged into a continuous series.
3. **Given** historical data already exists locally, **When** I request overlapping dates, **Then** only missing data is fetched (incremental update).

---

### User Story 3 - Fetch Funding Rates (Priority: P2)

As a trader, I want to fetch current and historical funding rates so I can understand the cost of holding positions and identify funding arbitrage opportunities.

**Why this priority**: Funding rates are updated every 8 hours and directly impact strategy profitability. Important but less frequently changing than OI.

**Independent Test**: Can be tested by fetching funding rate history and comparing values against exchange historical data.

**Acceptance Scenarios**:

1. **Given** a perpetual symbol, **When** I request the current funding rate, **Then** I receive the rate, next funding time, and predicted rate (if available).
2. **Given** a date range, **When** I request funding history, **Then** I receive all funding rate snapshots within that period.

---

### User Story 4 - Real-Time Liquidation Stream (Priority: P2)

As a trader, I want to receive real-time liquidation events so I can detect market stress and potential cascade liquidations as they happen.

**Why this priority**: Liquidations are real-time events critical for risk management. Requires persistent connection but valuable for live monitoring.

**Independent Test**: Can be tested by connecting to the liquidation stream and verifying events are received when liquidations occur on the exchange.

**Acceptance Scenarios**:

1. **Given** I start the liquidation stream for a symbol, **When** a liquidation occurs on the exchange, **Then** I receive the event within 2 seconds containing side, quantity, price, and timestamp.
2. **Given** the connection drops, **When** the stream reconnects, **Then** reconnection is automatic with exponential backoff and logged.
3. **Given** liquidation streaming is not available for an exchange, **When** I attempt to start, **Then** I receive a clear message indicating the limitation.

---

### User Story 5 - Persistent Storage (Priority: P1)

As a trader, I want all fetched data automatically saved to disk so I can access historical data without re-fetching from exchanges.

**Why this priority**: Storage enables backtesting and eliminates redundant API calls. Core infrastructure requirement.

**Independent Test**: Can be tested by fetching data, stopping the pipeline, and verifying data is readable from disk.

**Acceptance Scenarios**:

1. **Given** data is fetched from any exchange, **When** storage is enabled, **Then** data is persisted in a format compatible with NautilusTrader's data catalog structure.
2. **Given** stored data exists, **When** I query for a symbol and date range, **Then** data is returned from local storage without API calls.
3. **Given** storage directory doesn't exist, **When** the pipeline starts, **Then** directories are created automatically.

---

### User Story 6 - Daemon Mode (Priority: P3)

As a trader, I want the pipeline to run continuously in the background so I can accumulate data 24/7 without manual intervention.

**Why this priority**: Automation is valuable but requires all other features to work first. Enhancement over manual fetching.

**Independent Test**: Can be tested by starting daemon mode and verifying scheduled fetches occur at expected intervals.

**Acceptance Scenarios**:

1. **Given** daemon mode is started, **When** the configured interval elapses, **Then** data is automatically fetched and stored.
2. **Given** daemon is running, **When** I send a stop signal, **Then** current operations complete gracefully and the process exits cleanly.
3. **Given** daemon is running, **When** an unrecoverable error occurs, **Then** the error is logged and the daemon continues for other symbols/exchanges.

---

### Edge Cases

- What happens when exchange rate limits are exceeded? → Automatic backoff and retry with clear logging.
- What happens when exchange returns malformed data? → Validation fails, error logged, data discarded (not stored).
- What happens when disk is full? → Error logged, fetch continues but storage fails gracefully.
- What happens when fetching data for a delisted symbol? → Clear error message, symbol skipped.
- What happens during exchange maintenance windows? → Retry with exponential backoff, log maintenance status.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch current Open Interest for perpetual contracts from Binance Futures, Bybit, and Hyperliquid.
- **FR-002**: System MUST fetch historical Open Interest with configurable date ranges and automatic pagination.
- **FR-003**: System MUST fetch current and historical funding rates for perpetual contracts.
- **FR-004**: System MUST stream real-time liquidation events for exchanges that support it (Binance, Bybit).
- **FR-005**: System MUST normalize data from all exchanges into a unified format.
- **FR-006**: System MUST persist all fetched data in a format compatible with NautilusTrader ParquetDataCatalog.
- **FR-007**: System MUST support incremental updates (fetch only new data since last fetch).
- **FR-008**: System MUST handle exchange API rate limits automatically with backoff.
- **FR-009**: System MUST provide a command-line interface for manual fetch operations.
- **FR-010**: System MUST support daemon mode for continuous data collection.
- **FR-011**: System MUST log all operations with timestamps and outcomes.
- **FR-012**: System MUST handle graceful shutdown preserving data integrity.
- **FR-013**: System MUST validate all fetched data before storage.
- **FR-014**: System MUST support concurrent fetching from multiple exchanges.

### Key Entities

- **OpenInterest**: Represents the total number of outstanding derivative contracts. Attributes: timestamp, symbol, venue, open_interest (contracts), open_interest_value (USD).
- **FundingRate**: Represents the periodic payment between longs and shorts. Attributes: timestamp, symbol, venue, funding_rate, next_funding_time.
- **Liquidation**: Represents a forced position closure. Attributes: timestamp, symbol, venue, side (long/short liquidated), quantity, price, value (USD).
- **Exchange**: Represents a supported trading venue. Attributes: name, supported_data_types, rate_limits, connection_status.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can fetch current OI for any supported symbol within 5 seconds.
- **SC-002**: Users can fetch 30 days of OI history within 60 seconds per exchange.
- **SC-003**: Liquidation events are received within 2 seconds of occurrence on the exchange.
- **SC-004**: Data format is 100% compatible with NautilusTrader ParquetDataCatalog (can be loaded without transformation).
- **SC-005**: System handles 1000 consecutive API calls without rate limit errors.
- **SC-006**: Daemon mode runs for 24+ hours without crashes or memory leaks.
- **SC-007**: Graceful shutdown completes within 10 seconds preserving all pending data.
- **SC-008**: 99% of valid API responses are successfully parsed and stored.

## Scope

### In Scope

- Binance USDT-Margined Futures
- Bybit Linear Perpetuals
- Hyperliquid Perpetuals
- Open Interest (current and historical)
- Funding Rates (current and historical)
- Liquidations (real-time stream where available)
- Local Parquet storage
- CLI interface
- Daemon mode with scheduling

### Out of Scope

- Spot market data (use NautilusTrader native adapters)
- Order execution (use NautilusTrader native adapters)
- Real-time OI streaming (not available from exchanges)
- Web UI or dashboard
- Cloud storage integration
- Alerting/notifications

## Assumptions

- Users have valid API credentials for exchanges requiring authentication (Binance requires API key for some endpoints).
- Hyperliquid liquidation streaming may not be available; polling will be used as fallback.
- Exchange API structures remain stable; breaking changes require pipeline updates.
- Local disk has sufficient space for data storage (estimated 1GB per month for 10 symbols).
- Network connectivity is generally stable; transient failures are handled with retries.

## Dependencies

- NautilusTrader ParquetDataCatalog (for storage format compatibility)
- Exchange API availability and uptime
- Valid API credentials where required
