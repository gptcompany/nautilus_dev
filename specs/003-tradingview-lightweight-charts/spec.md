# Feature Specification: TradingView Lightweight Charts Real-Time Trading Dashboard

**Feature Branch**: `003-tradingview-lightweight-charts`
**Created**: 2025-12-24
**Status**: Draft
**Input**: User description: "TradingView Lightweight Charts real-time trading dashboard - Display Open Interest, Funding Rates, and Liquidations using existing WebSocket streams. Support historical data overlay when Nautilus catalog is available. Target deployment as standalone HTML/JS dashboard."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-Time Open Interest Visualization (Priority: P1)

As a trader, I need to see Open Interest changes in real-time on a chart so that I can identify when large positions are being opened or closed in the market.

**Why this priority**: Open Interest is the primary indicator for position flow analysis. Real-time visualization enables immediate trading decisions.

**Independent Test**: Can be fully tested by connecting to the existing WebSocket stream and verifying OI data appears on the chart within 1 second of receiving updates.

**Acceptance Scenarios**:

1. **Given** the dashboard is open, **When** WebSocket connects to the OI stream, **Then** current OI value is displayed on the chart
2. **Given** OI data is streaming, **When** a new OI update arrives, **Then** the chart updates within 1 second showing the new value
3. **Given** OI is decreasing rapidly (>5% in 1 minute), **When** displayed on chart, **Then** a visual indicator (color change) highlights the significant move

---

### User Story 2 - Real-Time Funding Rate Display (Priority: P1)

As a trader, I need to see the current funding rate and historical funding rate trend so that I can understand the cost of holding positions and market sentiment.

**Why this priority**: Funding rates directly impact trading costs and indicate market sentiment (positive = longs pay shorts). Critical for position management.

**Independent Test**: Can be fully tested by displaying the current funding rate and verifying it updates at each 8-hour funding interval.

**Acceptance Scenarios**:

1. **Given** the dashboard is open, **When** funding rate data is available, **Then** current rate is displayed prominently with percentage format
2. **Given** funding rate is positive (longs pay), **When** displayed, **Then** rate is shown in red/orange indicating cost to longs
3. **Given** funding rate is negative (shorts pay), **When** displayed, **Then** rate is shown in green indicating cost to shorts
4. **Given** historical funding data exists, **When** user views chart, **Then** funding rate history is overlaid as a line series

---

### User Story 3 - Real-Time Liquidation Events (Priority: P2)

As a trader, I need to see liquidation events as they happen so that I can identify cascading liquidations and potential price reversals.

**Why this priority**: Liquidations indicate forced position closures and often precede significant price moves. Important for timing entries/exits.

**Independent Test**: Can be tested by simulating liquidation events from the WebSocket stream and verifying they appear as markers on the chart.

**Acceptance Scenarios**:

1. **Given** a long liquidation event occurs, **When** received via WebSocket, **Then** a downward marker appears on the chart at that timestamp
2. **Given** a short liquidation event occurs, **When** received via WebSocket, **Then** an upward marker appears on the chart at that timestamp
3. **Given** multiple liquidations occur in rapid succession (>10 in 1 minute), **When** displayed, **Then** an aggregated liquidation volume indicator is shown

---

### User Story 4 - Historical Data Overlay (Priority: P3)

As a trader, I need to view historical OI, funding, and price data so that I can analyze patterns and backtest visual strategies.

**Why this priority**: Historical context improves decision-making but requires the Nautilus catalog from Spec 002 to be available.

**Independent Test**: Can be tested by loading historical data from the Parquet catalog and displaying it on the chart with proper time alignment.

**Acceptance Scenarios**:

1. **Given** historical data catalog is available, **When** user selects a date range, **Then** historical data is loaded and displayed on the chart
2. **Given** real-time and historical data are both displayed, **When** viewing the chart, **Then** there is a clear visual distinction between historical and live data
3. **Given** a large date range is selected (>1 month), **When** loading data, **Then** the chart aggregates data appropriately to maintain performance

---

### User Story 5 - Multi-Symbol Support (Priority: P3)

As a trader, I need to view data for different trading pairs (BTCUSDT, ETHUSDT) so that I can monitor multiple markets simultaneously.

**Why this priority**: Multi-market awareness is valuable but single-symbol functionality delivers primary value first.

**Independent Test**: Can be tested by switching between BTCUSDT and ETHUSDT and verifying the correct data streams connect.

**Acceptance Scenarios**:

1. **Given** the dashboard is displaying BTCUSDT, **When** user selects ETHUSDT from dropdown, **Then** all charts switch to ETHUSDT data streams
2. **Given** multiple symbols are available, **When** switching symbols, **Then** transition completes within 2 seconds

---

### Edge Cases

- What happens when WebSocket connection is lost mid-session?
- How does the dashboard handle gaps in real-time data (missed updates)?
- What happens when historical data catalog is unavailable (graceful degradation to real-time only)?
- How does the chart handle extreme values (e.g., 1000% funding rate during extreme volatility)?
- What happens when the browser tab is inactive for extended periods?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dashboard MUST display Open Interest as a line chart with real-time updates
- **FR-002**: Dashboard MUST display funding rate with color coding (positive=red, negative=green)
- **FR-003**: Dashboard MUST display liquidation events as chart markers with direction indication
- **FR-004**: Dashboard MUST connect to existing WebSocket streams for OI, funding, and liquidation data
- **FR-005**: Dashboard MUST support symbol selection (minimum: BTCUSDT, ETHUSDT)
- **FR-006**: Dashboard MUST handle WebSocket disconnection with automatic reconnection attempts
- **FR-007**: Dashboard MUST display connection status indicator (connected/disconnected/reconnecting)
- **FR-008**: Dashboard MUST support historical data overlay when Nautilus catalog is available
- **FR-009**: Dashboard MUST be deployable as a standalone HTML file with embedded assets
- **FR-010**: Dashboard MUST maintain chart state (zoom level, visible range) across symbol switches

### Key Entities

- **OIDataPoint**: Open Interest value at a specific timestamp. Includes absolute OI and delta from previous value.
- **FundingRate**: Funding rate percentage at a specific 8-hour interval. Includes predicted next rate if available.
- **LiquidationEvent**: Single liquidation with side (long/short), size, price, and timestamp.
- **ChartSeries**: Collection of data points for a single indicator. Supports line, histogram, and marker types.
- **DataStream**: Real-time data feed configuration including WebSocket endpoint and message format.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Real-time data updates appear on chart within 1 second of WebSocket message receipt
- **SC-002**: Dashboard loads and displays initial data within 3 seconds of page load
- **SC-003**: Chart maintains smooth interaction (pan/zoom) with 24 hours of data displayed
- **SC-004**: WebSocket reconnection succeeds within 10 seconds of connection loss
- **SC-005**: User can identify a significant OI change (>5%) visually within 2 seconds of it occurring

## Assumptions

- Existing WebSocket streams are available for OI, funding rates, and liquidations (implemented in previous work)
- WebSocket message format follows the established schema from the streaming implementation
- TradingView Lightweight Charts library is suitable for this use case (open-source, performant)
- Browser supports modern JavaScript (ES2020+) and WebSocket API
- Dashboard will be used on desktop browsers (responsive mobile design is not required)

## Dependencies

- Existing WebSocket streaming infrastructure (OI, funding, liquidations)
- TradingView Lightweight Charts library (external)
- Nautilus Parquet Catalog (optional, for historical data - see Spec 002)

## Out of Scope

- Mobile-responsive design
- User authentication or access control
- Persistent user preferences (zoom level, selected symbol)
- Price candlestick charts (focus is on OI/funding/liquidations)
- Trading execution from the dashboard
- Multi-monitor or detachable panel layouts
