# Feature Specification: Walk-Forward Validation Framework

**Feature Branch**: `feature/spec-020-walk-forward-validation`
**Created**: 2025-12-29
**Status**: Draft
**Input**: User description: "Walk-Forward Validation Framework for Backtesting - Implement comprehensive validation methods to reduce overfitting and provide realistic strategy performance estimates"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Walk-Forward Analysis on Strategy (Priority: P1)

A quantitative trader has developed a momentum strategy with configurable parameters (lookback period, threshold). Before deploying capital, they need to validate the strategy isn't overfit to historical data by running walk-forward analysis.

**Why this priority**: Core functionality - without this, the entire feature has no value. This is the MVP.

**Independent Test**: Can be fully tested by running a complete WFA cycle on a sample strategy with known parameters and verifying OOS performance is captured correctly.

**Acceptance Scenarios**:

1. **Given** a configured strategy with optimizable parameters and historical data, **When** user initiates walk-forward analysis with IS=70%, OOS=30%, **Then** system executes optimization on IS period, tests on OOS period, and reports concatenated OOS performance.

2. **Given** a walk-forward analysis in progress, **When** the IS/OOS cycle completes, **Then** system automatically advances the window and repeats until all data is consumed.

3. **Given** completed walk-forward analysis, **When** user requests results, **Then** system displays Walk-Forward Efficiency ratio (OOS/IS performance) with interpretation guidance.

---

### User Story 2 - Compare Rolling vs Anchored Windows (Priority: P2)

A researcher wants to compare how their strategy performs under different market regime assumptions - rolling windows (recent data more relevant) vs anchored windows (all historical data valuable).

**Why this priority**: Important configuration option that affects analysis quality, but P1 works with default rolling windows.

**Independent Test**: Can be tested by running same strategy with both window types and comparing WFE metrics.

**Acceptance Scenarios**:

1. **Given** user selects "rolling" window mode, **When** WFA executes, **Then** both IS start and end dates advance by step size each iteration.

2. **Given** user selects "anchored" window mode, **When** WFA executes, **Then** IS start date remains fixed while end date advances (expanding window).

3. **Given** both analyses complete, **When** user views comparison, **Then** system shows side-by-side WFE metrics and equity curves.

---

### User Story 3 - Run Combinatorial Purged Cross-Validation (Priority: P2)

A machine learning practitioner needs more rigorous validation than single-path WFA. They want to generate multiple backtest paths to compute Probability of Backtest Overfitting (PBO).

**Why this priority**: Advanced validation method that provides statistical rigor, but P1 WFA covers basic needs.

**Independent Test**: Can be tested by running CPCV on a sample ML-based strategy and verifying multiple paths are generated with PBO calculation.

**Acceptance Scenarios**:

1. **Given** strategy and data split into N sequential groups, **When** user runs CPCV with k test groups, **Then** system generates C(N,k) combinatorial train/test splits.

2. **Given** CPCV configuration with purge_window specified, **When** executing, **Then** system removes training samples whose labels overlap with test period.

3. **Given** CPCV configuration with embargo_window specified, **When** executing, **Then** system adds gap between test end and next training start to prevent leakage.

4. **Given** CPCV completes all paths, **When** user views results, **Then** system displays PBO (probability overfitting), DSR (deflated Sharpe ratio), and distribution of OOS performance.

---

### User Story 4 - Export Validation Report (Priority: P3)

After completing validation, user needs to document results for compliance, team review, or personal records.

**Why this priority**: Nice-to-have for documentation but doesn't affect core validation functionality.

**Independent Test**: Can be tested by running any validation and exporting report, verifying all metrics are captured.

**Acceptance Scenarios**:

1. **Given** completed WFA or CPCV analysis, **When** user requests export, **Then** system generates report with all metrics, equity curves, and parameter selections per period.

2. **Given** export in progress, **When** complete, **Then** report includes methodology description, data ranges used, and reproducibility parameters.

---

### Edge Cases

- What happens when data is insufficient for minimum IS/OOS periods?
- How does system handle strategies with no optimizable parameters (fixed strategies)?
- What happens when optimization fails to converge in any IS period?
- How does system handle gaps or missing data in the historical dataset?
- What happens when CPCV combinatorial explosion exceeds memory limits?
- How does system handle strategies that produce no trades in OOS period?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support walk-forward analysis with configurable in-sample and out-of-sample period ratios
- **FR-002**: System MUST support both rolling and anchored window types for WFA
- **FR-003**: System MUST calculate Walk-Forward Efficiency (WFE) ratio as OOS/IS performance percentage
- **FR-004**: System MUST automatically advance windows and repeat optimization cycles until data exhausted
- **FR-005**: System MUST concatenate all OOS results to provide final aggregate performance metrics
- **FR-006**: System MUST support Combinatorial Purged Cross-Validation with configurable N groups and k test groups
- **FR-007**: System MUST implement purging logic to remove training samples with labels overlapping test period
- **FR-008**: System MUST implement embargo periods between test end and training start
- **FR-009**: System MUST calculate Probability of Backtest Overfitting (PBO) from CPCV results
- **FR-010**: System MUST calculate Deflated Sharpe Ratio (DSR) adjusted for multiple testing
- **FR-011**: System MUST provide visualization of equity curves per IS/OOS period
- **FR-012**: System MUST validate minimum data requirements before starting analysis
- **FR-013**: System MUST handle strategies with no optimizable parameters gracefully (run as validation-only)
- **FR-014**: System MUST warn users when WFE falls below 50% threshold (potential overfitting)
- **FR-015**: System MUST export validation reports with methodology, parameters, and results

### Key Entities

- **ValidationRun**: Represents a complete WFA or CPCV execution (type, config, status, results)
- **ValidationWindow**: Individual IS/OOS period within a run (start, end, type, performance metrics)
- **ValidationResult**: Aggregate results from a run (WFE, PBO, DSR, concatenated equity, parameter history)
- **OptimizationTarget**: Metric being optimized during IS periods (Sharpe, CAR/MDD, profit factor, custom)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a walk-forward analysis configuration and execution in under 5 minutes (excluding computation time)
- **SC-002**: WFA results provide clear pass/fail indication based on WFE threshold (>50% = likely robust, <30% = likely overfit)
- **SC-003**: CPCV generates minimum 10 backtest paths for statistical significance
- **SC-004**: System processes at least 5 years of daily data for WFA in under 10 minutes on standard hardware
- **SC-005**: 95% of users correctly interpret validation results based on provided guidance
- **SC-006**: Validation reports contain all information needed for strategy reproducibility
- **SC-007**: False positive rate for "robust" classification is below 20% (validated against known overfit strategies)

## Assumptions

- Users have access to sufficient historical data (minimum 2 years recommended for meaningful validation)
- Strategy parameters are defined with optimization ranges before running WFA
- Performance metrics (Sharpe, returns, drawdown) are already calculated by existing backtest infrastructure
- ParquetDataCatalog provides efficient data windowing for subset extraction
- Parallel execution of optimization cycles is handled by existing BacktestEngine infrastructure

## Dependencies

- BacktestEngine: Core backtesting infrastructure for running strategy simulations
- ParquetDataCatalog: Data access layer for efficient historical data windowing
- Strategy optimization framework: Parameter search and optimization infrastructure
- Results aggregation: Existing performance metrics calculation

## Out of Scope

- Real-time walk-forward (live re-optimization) - this spec covers historical validation only
- Automatic strategy rejection/approval - system provides metrics, user decides
- Integration with external optimization libraries (Optuna, etc.) - uses existing NautilusTrader optimization
- Monte Carlo simulation (separate validation method, may be future spec)

## References

- Robert Pardo (1992) - "Design, Testing, and Optimization of Trading Systems" - Walk-Forward Analysis original methodology
- Marcos Lopez de Prado (2018) - "Advances in Financial Machine Learning" - CPCV methodology
- Bailey et al. (2014) - "The Probability of Backtest Overfitting" (SSRN 2326253) - PBO calculation
- skfolio library - Reference implementation of CombinatorialPurgedCV
