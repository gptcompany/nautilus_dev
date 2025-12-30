# Feature Specification: Alpha-Evolve Backtest Evaluator

**Feature Branch**: `007-alpha-evolve-evaluator`
**Created**: 2025-12-27
**Status**: Draft
**Input**: Wrapper per NautilusTrader BacktestNode con estrazione KPIs. Carica strategy code dinamicamente, esegue backtest, estrae metriche fitness (Sharpe, Calmar, MaxDD, CAGR).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dynamic Strategy Evaluation (Priority: P1)

As a strategy evolution system, I need to evaluate strategy code provided as a string so that I can test mutations without creating permanent files.

**Why this priority**: Core evaluation capability - without this, evolution cannot measure fitness. The entire evolution loop depends on this.

**Independent Test**: Can be fully tested by providing valid strategy code as a string and receiving fitness metrics.

**Acceptance Scenarios**:

1. **Given** valid strategy code as a string, **When** evaluate() is called, **Then** strategy is dynamically loaded and executed against historical data.
2. **Given** strategy code with syntax errors, **When** evaluate() is called, **Then** returns error result with exception details (does not crash).
3. **Given** strategy code that compiles but fails at runtime, **When** evaluate() is called, **Then** returns error result with runtime exception details.
4. **Given** evaluation timeout (> 5 minutes), **When** evaluate() is called, **Then** evaluation is terminated and timeout error is returned.

---

### User Story 2 - KPI Extraction (Priority: P1)

As a strategy evolution system, I need standardized fitness metrics extracted from backtest results so that I can compare and rank strategies objectively.

**Why this priority**: Fitness metrics drive parent selection and hall-of-fame ranking. Without consistent KPIs, evolution has no guidance.

**Independent Test**: Can be fully tested by running a backtest and verifying all expected metrics are present with correct calculations.

**Acceptance Scenarios**:

1. **Given** completed backtest, **When** metrics are extracted, **Then** returns: sharpe_ratio, calmar_ratio, max_drawdown, cagr, total_return.
2. **Given** strategy with no trades, **When** metrics are extracted, **Then** returns zero/null values with appropriate flags (not errors).
3. **Given** strategy with negative returns, **When** metrics are extracted, **Then** metrics correctly reflect negative performance (negative Sharpe, etc.).
4. **Given** backtest error, **When** metrics extraction is attempted, **Then** returns null metrics with error flag set.

---

### User Story 3 - Historical Data Configuration (Priority: P2)

As a user, I need to configure which symbols and date ranges to use for evaluation so that I can test strategies on different market conditions.

**Why this priority**: Enables experimentation across different assets and time periods. Default configuration works for BTC/ETH.

**Independent Test**: Can be fully tested by configuring different symbols/dates and verifying backtests use correct data.

**Acceptance Scenarios**:

1. **Given** configuration specifying BTCUSDT-PERP.BINANCE, **When** evaluate() runs, **Then** backtest uses BTC perpetual futures data.
2. **Given** configuration specifying date range 2024-01-01 to 2024-06-01, **When** evaluate() runs, **Then** backtest uses only data within that range.
3. **Given** configuration specifying multiple symbols, **When** evaluate() runs, **Then** strategy can trade all specified symbols.
4. **Given** symbols not present in data catalog, **When** evaluate() starts, **Then** error is raised before backtest begins.

---

### User Story 4 - Concurrent Evaluation Limits (Priority: P2)

As a system operator, I need to limit concurrent evaluations so that backtests don't exhaust system memory.

**Why this priority**: BacktestNode is memory-intensive. Prevents OOM kills during evolution runs.

**Independent Test**: Can be fully tested by submitting multiple evaluations and verifying concurrency limit is respected.

**Acceptance Scenarios**:

1. **Given** max_concurrent=2 and 5 evaluations submitted, **When** all are processed, **Then** at most 2 run simultaneously.
2. **Given** running evaluation fails, **When** next evaluation starts, **Then** failed slot is freed for new evaluation.
3. **Given** semaphore fully utilized, **When** new evaluation submitted, **Then** evaluation waits in queue.

---

### Edge Cases

- What happens when ParquetDataCatalog path is invalid?
- What happens when strategy imports unavailable modules?
- How does system handle strategies that enter infinite loops?
- What happens when data has gaps or missing bars?
- How are timezone differences handled across data sources?

## Requirements *(mandatory)*

### Functional Requirements

#### Dynamic Loading
- **FR-001**: Evaluator MUST load strategy code from string without creating permanent files
- **FR-002**: Evaluator MUST isolate strategy execution (imports, global state) per evaluation
- **FR-003**: Evaluator MUST timeout evaluations exceeding configured limit (default 5 minutes)
- **FR-004**: Evaluator MUST capture and return all exceptions without crashing

#### Backtest Execution
- **FR-005**: Evaluator MUST use NautilusTrader BacktestEngine for strategy execution
- **FR-006**: Evaluator MUST use ParquetDataCatalog for streaming historical data
- **FR-007**: Evaluator MUST support configurable initial capital (default 100,000)
- **FR-008**: Evaluator MUST use deterministic random seeds for reproducibility

#### Metrics Extraction
- **FR-009**: Evaluator MUST extract Sharpe ratio from portfolio analyzer
- **FR-010**: Evaluator MUST calculate Calmar ratio (CAGR / Max Drawdown)
- **FR-011**: Evaluator MUST extract maximum drawdown percentage
- **FR-012**: Evaluator MUST calculate CAGR (compound annual growth rate)
- **FR-013**: Evaluator MUST extract total return percentage
- **FR-014**: Evaluator MUST return trade count and win rate as secondary metrics

#### Concurrency
- **FR-015**: Evaluator MUST respect max_concurrent limit using semaphore
- **FR-016**: Evaluator MUST be async-compatible for integration with evolution controller

### Key Entities

- **EvaluationRequest**: Input for evaluation. Attributes: strategy_code (str), config (BacktestConfig)
- **EvaluationResult**: Output from evaluation. Attributes: success (bool), metrics (FitnessMetrics), error (str optional), duration_ms (int)
- **BacktestConfig**: Configuration for backtest. Attributes: symbols (list), start_date, end_date, initial_capital, data_catalog_path
- **FitnessMetrics**: Extracted performance metrics (from spec-006)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Typical strategy evaluation completes in under 60 seconds for 6 months of 1-minute bar data
- **SC-002**: 95% of valid strategies evaluate successfully without errors
- **SC-003**: Memory usage stays under 4GB per concurrent evaluation
- **SC-004**: Metrics extraction adds less than 1 second overhead to backtest time
- **SC-005**: Failed evaluations return structured error within 5 seconds of failure

## Assumptions

- ParquetDataCatalog is pre-populated with historical data for configured symbols
- NautilusTrader nightly environment is activated
- Strategies inherit from nautilus_trader.trading.strategy.Strategy
- V1 wranglers are used (V2 PyO3 incompatible with BacktestEngine)

## Dependencies

- **spec-006**: Uses FitnessMetrics entity definition
- **NautilusTrader nightly**: v1.222.0 or compatible

## Out of Scope

- Data catalog population/management
- Strategy validation beyond Python syntax
- Real-time/live evaluation
- Multi-venue backtesting
