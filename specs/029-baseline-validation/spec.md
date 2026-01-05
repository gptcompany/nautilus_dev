# Feature Specification: Baseline Validation

**Feature Branch**: `029-baseline-validation`
**Created**: 2026-01-05
**Status**: Draft
**Input**: PMW validation comparing SOPS+Giller+Thompson vs Fixed 2% vs Buy&Hold

## Overview

Based on PMW (Prove Me Wrong) validation in specs/028-validation/research_vs_repos_analysis.md, we need empirical evidence that our complex adaptive system (~60 parameters) outperforms simple baselines (~3 parameters) in out-of-sample testing before deploying to production.

**Key Reference**: DeMiguel 2009 - "1/N beats 14 optimization models OOS"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Baseline Comparison (Priority: P1)

As a quantitative developer, I want to run a walk-forward comparison of the adaptive system against simple baselines so that I have empirical evidence of whether complexity is justified.

**Why this priority**: This is the core validation - without this, we risk deploying an over-engineered system that underperforms simple alternatives.

**Independent Test**: Can be fully tested by running the comparison script with historical data and verifying statistical significance of results.

**Acceptance Scenarios**:

1. **Given** historical price data (minimum 2 years), **When** I run the baseline comparison, **Then** I get performance metrics for all three contenders.
2. **Given** a completed comparison run, **When** I view the results, **Then** I see Sharpe ratio, MaxDD, and DSR for each contender.
3. **Given** statistical results, **When** the adaptive system Sharpe < Fixed 2% Sharpe + 0.2, **Then** the system flags "Complex does NOT justify".

---

### User Story 2 - Walk-Forward Validation (Priority: P1)

As a quantitative developer, I want to use walk-forward validation (not simple train/test split) so that I properly account for regime changes and avoid lookahead bias.

**Why this priority**: Walk-forward is the gold standard for OOS validation in trading - without it, results are meaningless.

**Independent Test**: Can be verified by checking that each test window uses only data from prior training windows.

**Acceptance Scenarios**:

1. **Given** a 10-year dataset, **When** I configure 12 walk-forward windows, **Then** each window trains on prior data and tests on subsequent period.
2. **Given** walk-forward configuration, **When** validation runs, **Then** no future data leaks into any training period.
3. **Given** completed walk-forward, **When** I view aggregate results, **Then** metrics are computed across all OOS windows (not cherry-picked).

---

### User Story 3 - Generate Validation Report (Priority: P2)

As a quantitative developer, I want a clear validation report so that I can make an informed GO/WAIT/STOP decision.

**Why this priority**: Without a clear report, the validation results are not actionable.

**Independent Test**: Can be verified by generating a report and checking it contains all required metrics and a clear recommendation.

**Acceptance Scenarios**:

1. **Given** completed validation, **When** I generate report, **Then** I see a comparison table with all contenders and metrics.
2. **Given** a validation report, **When** Adaptive beats Fixed 2% by Sharpe + 0.2 AND has lower MaxDD, **Then** report shows "GO: Deploy Adaptive".
3. **Given** a validation report, **When** Fixed 2% wins, **Then** report shows "STOP: Use Fixed 2%, complexity not justified".

---

### Edge Cases

- What happens when a strategy has zero trades in a walk-forward window?
- How does the system handle periods with extreme volatility (March 2020, Nov 2022)?
- What if Sharpe is negative for all contenders?
- How are transaction costs handled consistently across contenders?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement Contender A: Full SOPS+Giller+Thompson adaptive sizing stack
- **FR-002**: System MUST implement Contender B: Fixed 2% position sizing (risk=2%, max_positions=10, stop_loss=5%)
- **FR-003**: System MUST implement Contender C: Buy & Hold benchmark
- **FR-004**: System MUST use existing walk-forward infrastructure from scripts/alpha_evolve/walk_forward/
- **FR-005**: System MUST calculate Sharpe Ratio for each contender across all OOS windows
- **FR-006**: System MUST calculate Maximum Drawdown for each contender
- **FR-007**: System MUST calculate Deflated Sharpe Ratio (DSR) to distinguish skill from luck
- **FR-008**: System MUST enforce no lookahead bias (no future data in training)
- **FR-009**: System MUST apply consistent transaction costs to all contenders
- **FR-010**: System MUST generate a comparison report with GO/WAIT/STOP recommendation

### Key Entities

- **Contender**: A sizing strategy to be tested (Adaptive, Fixed 2%, Buy&Hold)
- **WalkForwardWindow**: A training period + test period pair
- **ValidationResult**: Metrics for a contender across all OOS windows
- **ComparisonReport**: Aggregate analysis with recommendation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Validation runs complete within 6 hours for 10-year BTC dataset
- **SC-002**: All 3 contenders produce valid performance metrics (no NaN/Inf values)
- **SC-003**: Walk-forward validation uses minimum 12 windows (1 year training, 1 month test each)
- **SC-004**: Report clearly states whether Adaptive Sharpe > Fixed Sharpe + 0.2 (statistically significant edge)
- **SC-005**: Report clearly states whether Adaptive MaxDD < Fixed MaxDD (better risk-adjusted)
- **SC-006**: DSR calculation confirms skill > luck (DSR > 0.5)
- **SC-007**: Validation is reproducible (same data + config = same results)

## Assumptions

- Historical price data is available and clean (no gaps, no bad ticks)
- The existing walk-forward infrastructure in scripts/alpha_evolve/walk_forward/ is functional
- Transaction costs of 0.1% per trade (configurable) are reasonable for comparison
- Statistical significance threshold of Sharpe + 0.2 is based on research_vs_repos_analysis.md
- Buy & Hold uses full capital allocation without rebalancing

## Out of Scope

- Live trading deployment (this is validation only)
- Optimization of adaptive system parameters (this validates current implementation)
- Multi-asset validation (BTC only for MVP)
- Real-time streaming validation (batch historical only)

## Dependencies

- scripts/alpha_evolve/walk_forward/validator.py
- scripts/alpha_evolve/walk_forward/config.py
- scripts/alpha_evolve/walk_forward/metrics.py
- strategies/common/adaptive_control/ (SOPS, Giller, Thompson implementations)
- Historical BTC price data (minimum 2 years, preferably 10 years)
