# Feature Specification: Plotly Backtest Tearsheets & Analysis

**Feature Branch**: `004-plotly-backtest-tearsheets`
**Created**: 2025-12-25
**Status**: Draft
**Input**: Community recommendation: "Plotly is the go-to for backtest analysis" + NautilusTrader official tearsheet system (v1.221+)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Backtest Report (Priority: P1)

As a trader, I need to generate a comprehensive HTML report after running a backtest so that I can analyze strategy performance visually.

**Why this priority**: Core functionality - without this, no analysis possible.

**Independent Test**: Run backtest with sample strategy, generate tearsheet, verify all 8 chart types render correctly.

**Acceptance Scenarios**:

1. **Given** a completed backtest, **When** I call `create_tearsheet(engine)`, **Then** an interactive HTML file is generated
2. **Given** tearsheet is generated, **When** I open in browser, **Then** all charts are interactive (zoom, pan, hover tooltips)
3. **Given** tearsheet with trades, **When** viewing equity curve, **Then** I can see drawdown overlay and trade markers

---

### User Story 2 - Equity Curve & Drawdown Analysis (Priority: P1)

As a trader, I need to see equity curve with drawdown analysis so that I can understand risk-adjusted performance.

**Why this priority**: Most critical chart for strategy evaluation.

**Independent Test**: Generate tearsheet, verify equity curve shows account value over time with drawdown periods highlighted.

**Acceptance Scenarios**:

1. **Given** backtest with profits and losses, **When** viewing equity chart, **Then** shows cumulative returns over time
2. **Given** backtest with drawdowns, **When** viewing drawdown chart, **Then** shows underwater equity with max drawdown highlighted
3. **Given** multiple drawdown periods, **When** hovering on chart, **Then** shows drawdown percentage and duration

---

### User Story 3 - Returns Heatmaps (Priority: P2)

As a trader, I need to see monthly and yearly returns heatmaps so that I can identify seasonal patterns.

**Why this priority**: Important for understanding when strategy performs best/worst.

**Independent Test**: Generate tearsheet with 2+ years of data, verify monthly heatmap shows correct values.

**Acceptance Scenarios**:

1. **Given** backtest spanning multiple months, **When** viewing monthly heatmap, **Then** shows returns per month with color coding
2. **Given** backtest spanning multiple years, **When** viewing yearly heatmap, **Then** shows annual returns comparison
3. **Given** losing months, **When** viewing heatmap, **Then** negative returns shown in red gradient

---

### User Story 4 - Trade Analysis (Priority: P2)

As a trader, I need to see individual trade statistics and distribution so that I can optimize entry/exit logic.

**Why this priority**: Essential for strategy refinement.

**Independent Test**: Generate tearsheet with 100+ trades, verify trade distribution and stats table.

**Acceptance Scenarios**:

1. **Given** backtest with trades, **When** viewing distribution chart, **Then** shows histogram of trade returns
2. **Given** backtest with trades, **When** viewing stats table, **Then** shows win rate, avg win/loss, profit factor
3. **Given** OHLC data available, **When** viewing trades on price chart, **Then** shows entry/exit markers on candlesticks

---

### User Story 5 - Custom Charts Extension (Priority: P3)

As a quant developer, I need to add custom charts to tearsheets so that I can visualize strategy-specific metrics.

**Why this priority**: Extensibility for advanced users.

**Independent Test**: Register custom chart, generate tearsheet, verify custom chart appears.

**Acceptance Scenarios**:

1. **Given** custom chart class registered, **When** generating tearsheet, **Then** custom chart included in output
2. **Given** custom metrics computed, **When** viewing custom chart, **Then** shows strategy-specific visualization
3. **Given** multiple custom charts, **When** generating tearsheet, **Then** all custom charts render in order

---

### User Story 6 - Multi-Strategy Comparison (Priority: P3)

As a trader, I need to compare multiple strategy backtests side-by-side so that I can select the best performer.

**Why this priority**: Essential for strategy selection but requires multiple backtests first.

**Independent Test**: Run 3 backtests, generate comparison report, verify all strategies shown.

**Acceptance Scenarios**:

1. **Given** multiple backtest results, **When** generating comparison, **Then** shows equity curves overlaid
2. **Given** multiple strategies, **When** viewing stats table, **Then** shows side-by-side metrics comparison
3. **Given** different risk profiles, **When** comparing, **Then** shows Sharpe, Sortino, Calmar ratios

---

### Edge Cases

- What happens with zero trades (no fills)?
- How to handle extremely long backtests (10+ years)?
- What if strategy has only losses (no positive trades)?
- How to handle missing OHLC data for trade overlay?
- What happens with very high frequency (1000+ trades/day)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate interactive HTML tearsheet from BacktestEngine results
- **FR-002**: System MUST include equity curve with cumulative returns
- **FR-003**: System MUST include drawdown chart with max drawdown highlighted
- **FR-004**: System MUST include monthly returns heatmap
- **FR-005**: System MUST include yearly returns heatmap
- **FR-006**: System MUST include trade distribution histogram
- **FR-007**: System MUST include statistics table (win rate, profit factor, Sharpe, etc.)
- **FR-008**: System MUST include OHLC chart with trade markers (when data available)
- **FR-009**: System MUST support dark and light themes
- **FR-010**: System MUST allow custom chart registration via registry pattern
- **FR-011**: System MUST generate self-contained HTML (no external dependencies)
- **FR-012**: System MUST support multi-strategy comparison reports

### Key Entities

- **TearsheetConfig**: Configuration for tearsheet generation (theme, charts to include, output path)
- **ChartRegistry**: Registry of available chart types (built-in + custom)
- **PerformanceStats**: Computed statistics from backtest results
- **TradeAnalysis**: Per-trade metrics and aggregations
- **EquityCurve**: Time series of account value

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tearsheet generation completes in < 5 seconds for 1-year daily backtest
- **SC-002**: HTML file size < 2MB for standard tearsheet
- **SC-003**: All 8 built-in charts render without JavaScript errors
- **SC-004**: Charts remain responsive with 10,000+ data points
- **SC-005**: Tearsheet works offline (self-contained HTML)

## Assumptions

- NautilusTrader v1.221+ with visualization extras installed
- Plotly v6.3.1+ available
- BacktestEngine provides necessary data (trades, account, positions)
- Modern browser for viewing (Chrome, Firefox, Safari)

## Dependencies

- NautilusTrader >= 1.221.0
- Plotly >= 6.3.1
- Pandas (for data manipulation)
- Spec 002: Binance historical data for testing

## Out of Scope

- Real-time streaming charts (see Spec 003)
- Server-hosted dashboards (see Spec 005)
- PDF export (HTML only)
- Mobile-optimized layout
