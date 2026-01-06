# Feature Specification: Strategic Controller (Level 3)

**Feature Branch**: `033-strategic-controller`
**Created**: 2026-01-06
**Status**: Draft
**Source**: Gap #1 + #7 merged (HIGH) | [Canonical Mapping](../028-validation/gaps_to_specs_mapping.md)

## Problem Statement

The framework has MetaController (Level 2) but NO Level 3 "meta-meta" controller for:
- Weekly/monthly risk budget allocation
- Evolution triggers (when to spawn new alpha-evolve)
- Circuit breakers at portfolio level
- Performance evaluation for strategy graduation/retirement
- Walk-Forward OOS integration with meta-portfolio

**Solution** (Sharma 2025): 3-level hierarchies outperform 2-level by 20-40% in Sharpe ratio.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Weekly Risk Budget Allocation (Priority: P1)

A trading system operator reviews portfolio performance weekly and adjusts capital allocation across strategy groups based on their track record and current market conditions. The system automatically recommends risk budget adjustments, but the operator has final approval before changes take effect.

**Why this priority**: Risk budget allocation is the foundation of portfolio management. Without strategic capital allocation across strategy groups, the system lacks portfolio-level control. This is the minimum viable product that delivers immediate value.

**Independent Test**: Can be fully tested by running a weekly review with mock strategy performance data and verifying that risk budgets are allocated correctly based on strategy group performance, drawdown levels, and market regime. Delivers immediate value by preventing over-allocation to underperforming strategy groups.

**Acceptance Scenarios**:

1. **Given** a portfolio with three strategy groups (momentum, mean-reversion, market-making), **When** the weekly review runs and momentum strategies show 15% drawdown, **Then** the risk budget allocator reduces momentum allocation by 50% and redistributes to other groups
2. **Given** all strategy groups performing within normal parameters, **When** weekly review runs, **Then** risk budgets remain unchanged and operator receives status summary
3. **Given** a new strategy group added to portfolio, **When** weekly review runs, **Then** new group receives initial conservative allocation (5% of total capital)
4. **Given** total portfolio drawdown exceeds 10%, **When** weekly review runs, **Then** all risk budgets scale down proportionally to reduce total exposure

---

### User Story 2 - Evolution Decision Gating (Priority: P2)

The system monitors strategy performance continuously and determines when to trigger alpha-evolve to generate new strategy variants. The evolution gate prevents wasteful re-evolution when performance degradation is due to luck rather than skill deterioration, using Deflated Sharpe Ratio (DSR) analysis.

**Why this priority**: Evolution gating prevents wasted computational resources and unnecessary strategy churn. It builds on the risk allocation foundation (P1) but is not required for basic portfolio management. Delivers value by improving strategy evolution efficiency.

**Independent Test**: Can be tested independently by simulating strategy performance degradation scenarios and verifying that alpha-evolve is only triggered when DSR analysis indicates skill degradation (not random variance). Measurable by reduction in false-positive evolution triggers.

**Acceptance Scenarios**:

1. **Given** a strategy with declining returns but DSR > 2.0, **When** evolution gate evaluates performance, **Then** evolution is NOT triggered (performance degradation likely due to luck)
2. **Given** a strategy with DSR < 1.5 over 30-day window, **When** evolution gate evaluates performance, **Then** evolution trigger recommendation is generated with confidence score
3. **Given** multiple strategies in same group showing correlated performance decline, **When** evolution gate evaluates, **Then** single group-level evolution is triggered (not individual strategy evolutions)
4. **Given** a strategy recently evolved (< 14 days ago), **When** evolution gate evaluates poor performance, **Then** evolution is deferred to allow warmup period completion

---

### User Story 3 - Portfolio Circuit Breaker (Priority: P1)

The system monitors portfolio-level risk metrics continuously and automatically halts all trading when critical thresholds are breached. This provides a safety net beyond individual strategy risk limits, protecting against systemic failures and correlated drawdowns.

**Why this priority**: Portfolio circuit breaker is critical safety infrastructure. While it builds on risk budgets (P1), it operates independently and provides essential protection against catastrophic loss. Required for production deployment.

**Independent Test**: Can be tested by simulating portfolio-level breach scenarios (total drawdown, correlation spike, volatility surge) and verifying that all trading halts, positions are protected, and alerts are generated. Delivers independent safety value regardless of other features.

**Acceptance Scenarios**:

1. **Given** portfolio total drawdown reaches 15%, **When** circuit breaker evaluates conditions, **Then** all trading is halted, stop-losses remain active, and operator is alerted via critical notification
2. **Given** inter-strategy correlation spikes above 0.85 across all groups, **When** circuit breaker evaluates, **Then** new position entry is blocked, existing positions remain, and correlation alert is raised
3. **Given** portfolio daily loss exceeds 5% of total capital, **When** circuit breaker evaluates, **Then** all strategies transition to close-only mode and daily loss report is generated
4. **Given** circuit breaker triggered, **When** operator manually resets after reviewing conditions, **Then** system requires explicit confirmation and stages gradual restart with reduced risk budgets

---

### User Story 4 - Strategy Graduation and Retirement (Priority: P3)

The system evaluates strategy performance over extended periods and makes recommendations to graduate strategies from development to production, or retire underperforming strategies from active trading. Graduation requires consistent out-of-sample (OOS) performance validation.

**Why this priority**: Strategy lifecycle management improves portfolio quality over time but is not essential for initial operation. Can be performed manually initially. Delivers value by automating strategy quality control.

**Independent Test**: Can be tested by simulating strategy lifecycle scenarios with mock performance history and verifying correct graduation/retirement recommendations based on OOS performance, DSR, and robustness metrics.

**Acceptance Scenarios**:

1. **Given** a development strategy with 90-day OOS Sharpe > 1.5 and DSR > 2.0, **When** performance evaluator runs, **Then** graduation recommendation is generated with detailed performance report
2. **Given** a production strategy with 180-day rolling Sharpe < 0.5, **When** performance evaluator runs, **Then** retirement recommendation is generated with replacement strategy suggestions
3. **Given** a strategy showing performance degradation trend (-20% monthly decline), **When** evaluator runs, **Then** early warning is issued before full retirement criteria met
4. **Given** a strategy recommended for retirement, **When** operator confirms action, **Then** strategy allocation phases down over 7 days (not immediate halt)

---

### User Story 5 - Walk-Forward OOS Integration (Priority: P2)

The system automatically incorporates out-of-sample (OOS) walk-forward validation results into meta-portfolio strategy weighting. Strategies that show strong OOS performance receive higher allocations, while strategies with poor OOS results receive reduced weights, creating a continuous feedback loop between validation and allocation.

**Why this priority**: OOS integration improves allocation accuracy by using validation-derived confidence scores. Builds on risk allocation (P1) but requires walk-forward validation infrastructure to be operational. Delivers value by reducing overfitting in strategy weights.

**Independent Test**: Can be tested by providing mock walk-forward validation results with varying OOS performance and verifying that strategy weights adjust correctly based on robustness scores, OOS Sharpe ratios, and probability of backtest overfitting metrics.

**Acceptance Scenarios**:

1. **Given** walk-forward validation completes for Strategy A with OOS Sharpe 1.8 and PBO < 0.3, **When** OOS integrator processes results, **Then** Strategy A weight increases proportionally to confidence score
2. **Given** Strategy B shows OOS Sharpe 0.3 (but in-sample 2.0), **When** OOS integrator processes results, **Then** Strategy B weight decreases and overfitting warning is logged
3. **Given** multiple strategies in same group with varying OOS results, **When** integrator processes, **Then** group total allocation remains stable but internal weights rebalance based on OOS performance
4. **Given** insufficient OOS data for a new strategy, **When** integrator processes, **Then** strategy receives conservative baseline weight until validation completes

---

### Edge Cases

- What happens when all strategy groups simultaneously breach drawdown thresholds (portfolio-wide crisis)?
- How does system handle circuit breaker triggers during low-liquidity hours when position closing may be impaired?
- What happens when evolution gate recommends evolution but computational resources are unavailable?
- How does risk budget allocation behave when strategy group count changes mid-week (additions/removals)?
- What happens when OOS validation results conflict with live performance (strategy performs well live but poorly in OOS)?
- How does system handle manual operator override of automated recommendations?
- What happens when weekly review scheduling conflicts with active trading (market hours)?
- How does graduation/retirement work for strategies with limited history (< minimum required days)?

## Requirements *(mandatory)*

### Functional Requirements

#### Risk Budget Allocation
- **FR-001**: System MUST calculate weekly risk budgets for each strategy group based on recent performance, drawdown levels, and market regime
- **FR-002**: System MUST support manual override of automated risk budget recommendations with operator-provided rationale
- **FR-003**: System MUST persist risk budget history with timestamps, allocation decisions, and performance outcomes
- **FR-004**: System MUST scale risk budgets proportionally when portfolio-level constraints require total exposure reduction
- **FR-005**: System MUST enforce minimum allocation thresholds (1% per group) to prevent complete elimination of strategy diversity

#### Evolution Decision Gating
- **FR-006**: System MUST calculate Deflated Sharpe Ratio (DSR) for strategies using multiple testing correction as defined in Bailey & López de Prado (2014)
- **FR-007**: System MUST trigger evolution recommendations when DSR falls below configurable threshold (default: 1.5) for sustained period (default: 30 days)
- **FR-008**: System MUST enforce minimum time between evolution triggers for same strategy (default: 14 days) to allow warmup
- **FR-009**: System MUST detect correlated performance degradation across strategy groups and recommend group-level evolution (not individual)
- **FR-010**: System MUST log all evolution gate decisions with supporting metrics (DSR, p-values, performance trends) for audit trail

#### Portfolio Circuit Breaker
- **FR-011**: System MUST monitor portfolio total drawdown continuously and trigger circuit breaker when threshold breached (default: 15%)
- **FR-012**: System MUST monitor inter-strategy correlation continuously and trigger circuit breaker when correlation spike detected (default: > 0.85)
- **FR-013**: System MUST monitor daily loss limit at portfolio level and trigger close-only mode when threshold breached (default: 5% of capital)
- **FR-014**: System MUST halt new position entry when circuit breaker triggers, while maintaining stop-loss protection on existing positions
- **FR-015**: System MUST generate critical alerts via multiple channels (log, email, SMS) when circuit breaker triggers
- **FR-016**: System MUST require explicit operator confirmation and reason before resetting circuit breaker after trigger
- **FR-017**: System MUST implement staged restart with reduced risk budgets (50% of pre-trigger levels) after circuit breaker reset

#### Performance Evaluation
- **FR-018**: System MUST track strategy performance metrics over multiple timeframes (30d, 90d, 180d rolling windows)
- **FR-019**: System MUST calculate graduation eligibility based on OOS Sharpe > 1.5, DSR > 2.0, and minimum 90-day history
- **FR-020**: System MUST calculate retirement eligibility based on 180-day rolling Sharpe < 0.5 or sustained drawdown > 20%
- **FR-021**: System MUST detect performance degradation trends using linear regression on rolling Sharpe ratios
- **FR-022**: System MUST phase down allocations gradually (over 7 days) when retirement is confirmed, not immediate halt
- **FR-023**: System MUST generate performance reports with detailed metrics, charts, and statistical significance tests

#### Walk-Forward OOS Integration
- **FR-024**: System MUST consume walk-forward validation results from validator.py and extract OOS metrics (Sharpe, DSR, PBO, robustness score)
- **FR-025**: System MUST adjust strategy weights based on OOS performance confidence scores derived from validation metrics
- **FR-026**: System MUST flag strategies with high probability of backtest overfitting (PBO > 0.5) and reduce allocations
- **FR-027**: System MUST maintain stable group-level allocations while rebalancing internal weights based on OOS results
- **FR-028**: System MUST assign conservative baseline weights to new strategies pending OOS validation completion

#### System Integration
- **FR-029**: System MUST integrate with MetaController (Level 2) to receive performance data and publish risk budget adjustments
- **FR-030**: System MUST integrate with walk-forward validator to consume OOS metrics and validation results
- **FR-031**: System MUST expose scheduled review interface (weekly) and on-demand review interface (operator-triggered)
- **FR-032**: System MUST persist all decisions, recommendations, and operator actions to audit trail with timestamps

### Key Entities *(include if feature involves data)*

- **StrategicController**: Top-level coordinator managing weekly reviews, evolution gates, circuit breakers, and performance evaluation. Operates at portfolio level (Level 3) above MetaController (Level 2).

- **RiskBudgetAllocator**: Calculates weekly capital allocation across strategy groups based on performance, drawdown, and regime. Outputs allocation percentages per group with confidence scores.

- **EvolutionDecisionGate**: Evaluates whether to trigger alpha-evolve based on DSR analysis, performance trends, and recent evolution history. Outputs evolution recommendations with supporting metrics.

- **PortfolioCircuitBreaker**: Monitors portfolio-level risk metrics (total drawdown, correlation, daily loss) and triggers emergency halt when thresholds breached. Outputs circuit breaker state and alert notifications.

- **PerformanceEvaluator**: Tracks long-term strategy performance across multiple timeframes and generates graduation/retirement recommendations. Outputs lifecycle recommendations with detailed performance reports.

- **OOSIntegrator**: Consumes walk-forward validation results and adjusts strategy weights based on out-of-sample performance confidence. Outputs adjusted weight recommendations with OOS confidence scores.

- **StrategyGroup**: Collection of related strategies (e.g., momentum, mean-reversion) that share risk budget allocation. Contains group-level performance metrics and allocation constraints.

- **ReviewSchedule**: Configuration for weekly review timing, thresholds, and escalation rules. Defines when strategic decisions are made and operator involvement required.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Weekly risk budget allocation completes in under 60 seconds for portfolios with up to 50 strategies across 10 groups
- **SC-002**: Evolution gate reduces false-positive evolution triggers by 70% compared to threshold-based approach (measured over 90-day period)
- **SC-003**: Portfolio circuit breaker triggers within 5 seconds of threshold breach and halts new positions with 100% reliability
- **SC-004**: Strategy graduation process identifies candidates with 90% precision (graduated strategies maintain Sharpe > 1.0 in subsequent 90 days)
- **SC-005**: OOS integration improves meta-portfolio Sharpe ratio by 15-25% compared to equal-weighted allocation (measured over 180-day walk-forward)
- **SC-006**: System reduces maximum portfolio drawdown by 30-40% compared to no strategic oversight (stress test scenarios)
- **SC-007**: Operator intervention required for less than 20% of strategic decisions (80% automated with high confidence)
- **SC-008**: All strategic decisions logged to audit trail within 1 second with complete supporting metrics
- **SC-009**: Circuit breaker reset process completes in under 5 minutes from operator confirmation to staged restart
- **SC-010**: Performance degradation trends detected 14 days earlier than retirement criteria (early warning effectiveness)
