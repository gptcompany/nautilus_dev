# Feature Specification: CSRC Correlation-Aware Allocation

**Feature Branch**: `031-csrc-correlation`
**Created**: 2026-01-06
**Status**: Draft
**Source**: Gap #2 (HIGH) | [Canonical Mapping](../028-validation/gaps_to_specs_mapping.md)

## Problem Statement

Current ThompsonSelector in `particle_portfolio.py` treats strategies as independent. Weight allocation ignores inter-strategy correlation, causing over-allocation to correlated strategies (e.g., 30%+30%+30% to three correlated momentum strategies).

**Solution** (Varlashova & Bilokon 2025): Add covariance-penalized objective function:
```
reward = sharpe_portfolio - lambda * covariance_penalty
```

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prevent Over-Allocation to Correlated Strategies (Priority: P1)

A portfolio manager runs a multi-strategy portfolio with three momentum strategies (trend-following, breakout, and moving-average crossover). Currently, the particle portfolio allocates 30% to each strategy, not realizing they are highly correlated (correlation > 0.8). When the market reverses, all three strategies lose simultaneously, causing a 90% exposure to a single market factor.

With correlation-aware allocation, the system detects the high correlation between these strategies and reduces concentration. The portfolio might allocate 40% to the dominant momentum strategy, 20% to mean-reversion, and 20% to uncorrelated arbitrage strategies, reducing hidden concentration risk.

**Why this priority**: This is the core problem Gap #2 identifies. Without correlation awareness, portfolio risk is severely underestimated, violating P1 Probabilistico (treating strategies as independent when they're not). This is the MVP - correlation-penalized weighting is the entire feature.

**Independent Test**: Can be fully tested by creating a portfolio with intentionally correlated synthetic strategies (e.g., three strategies that all return +1% or -1% together). The system should detect correlation > 0.8 and reduce weight concentration compared to uncorrelated strategies. Delivers immediate risk reduction value.

**Acceptance Scenarios**:

1. **Given** three strategies with correlation > 0.8, **When** particle portfolio updates weights, **Then** total allocation to correlated group is significantly reduced (e.g., ~50% combined vs 90% without CSRC - exact reduction depends on lambda parameter)
2. **Given** strategies with low correlation < 0.3, **When** particle portfolio updates, **Then** weight allocation remains similar to current implementation (no penalty for diversification)
3. **Given** a portfolio with one dominant high-Sharpe strategy correlated with two weak strategies, **When** allocation is computed, **Then** system allocates to the dominant strategy and reduces weight to weaker correlated strategies (quality over quantity)

---

### User Story 2 - Online Correlation Matrix Update (Priority: P2)

The system must track rolling correlations between all strategy pairs without loading historical data into memory or causing performance degradation. For a 10-strategy portfolio, this means tracking 45 correlation pairs (N*(N-1)/2).

The correlation matrix updates incrementally each period using online covariance calculation (Welford's algorithm or exponential moving average). This allows the system to adapt to changing correlations without expensive batch recalculations.

**Why this priority**: Essential infrastructure for P1, but can be implemented independently. Without efficient online updates, correlation tracking becomes a bottleneck. This is P2 because correlation tracking alone doesn't deliver value - it must feed into allocation (P1) to matter.

**Independent Test**: Can be fully tested by streaming synthetic returns with known correlation (e.g., strategy A returns R, strategy B returns 0.8*R + noise). Verify correlation estimate converges to 0.8 within N samples. Performance test ensures < 1ms per update for 10 strategies.

**Acceptance Scenarios**:

1. **Given** two strategies with true correlation 0.9, **When** system observes 100 return pairs, **Then** estimated correlation is within 0.05 of true value (0.85-0.95)
2. **Given** 10 strategies (45 pairs), **When** correlation matrix is updated, **Then** update completes in < 1ms (O(N²) acceptable for N < 50)
3. **Given** correlation changes over time (e.g., 0.5 → 0.9 due to regime shift), **When** using exponential weighting with decay 0.99, **Then** correlation estimate adapts within 100 samples

---

### User Story 3 - Covariance Penalty Tuning (Priority: P3)

The covariance penalty strength (lambda) must balance two objectives:
- **Too high**: Portfolio becomes overly concentrated in single strategy (ignores diversification)
- **Too low**: Portfolio ignores correlation (current behavior)

The system allows tuning lambda parameter (default: 1.0) and reports portfolio concentration metrics (Herfindahl index, effective N strategies) so users can verify penalty is working.

**Why this priority**: Nice-to-have for calibration but not essential for MVP. Users can run with default lambda = 1.0 initially. This is P3 because it's a tuning/observability feature, not core functionality.

**Independent Test**: Can be tested by running particle portfolio with lambda = [0.0, 0.5, 1.0, 2.0] on same dataset. Verify higher lambda reduces concentration in correlated strategies. Report effective N strategies = 1 / sum(w_i²).

**Acceptance Scenarios**:

1. **Given** lambda = 0.0 (no penalty), **When** three correlated strategies exist, **Then** allocation behavior matches current implementation (baseline)
2. **Given** lambda = 2.0 (high penalty), **When** portfolio allocates, **Then** concentration in correlated groups is minimized (effective N strategies > 5 for 10 strategies)
3. **Given** lambda = 1.0 (default), **When** user requests portfolio state, **Then** system reports Herfindahl index and effective N strategies for transparency

---

### Edge Cases

- **What happens when all strategies are highly correlated (correlation > 0.9)?** System should allocate to the single highest Sharpe ratio strategy and reduce others to minimum weights (graceful degradation to single-strategy portfolio).
- **What happens when correlation matrix becomes singular (perfect multicollinearity)?** Use regularization (add small epsilon to diagonal) or fallback to equal weighting for degenerate cases.
- **What happens with only 2 strategies?** Correlation is a single value, penalty is straightforward. System should still work (no minimum N requirement).
- **What happens during market regime changes when correlations shift rapidly?** Exponential weighting allows fast adaptation (controlled by decay parameter). System should adapt within 50-100 samples.
- **What happens when a strategy has zero variance (constant returns)?** Division by zero in correlation calculation. Handle by treating as uncorrelated (correlation = 0) or excluding from covariance matrix.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain a rolling correlation matrix (`OnlineCorrelationMatrix` class) between all strategy pairs, stored as full N×N matrix with O(N²) total memory (20KB max for N=50)
- **FR-002**: System MUST calculate covariance penalty term: `penalty = sum_i sum_j (w_i * w_j * corr_ij)` where i ≠ j
- **FR-003**: Particle portfolio update MUST incorporate covariance penalty: `reward = sharpe_portfolio - lambda * covariance_penalty`
- **FR-004**: Correlation matrix MUST use exponential weighting or sliding window (max 1000 samples in memory) for non-stationarity
- **FR-005**: System MUST handle edge cases: singular matrices (regularization), zero variance (treat as uncorrelated), perfect correlation (allocate to best strategy)
- **FR-006**: Correlation updates MUST complete in < 1ms for portfolios with up to 20 strategies (400 pairs)
- **FR-007**: System MUST provide tunable lambda parameter (default: 1.0, range: [0.0, 5.0]) for penalty strength
- **FR-008**: System MUST report portfolio concentration metrics: Herfindahl index, effective N strategies, max pairwise correlation
- **FR-009**: Correlation estimates MUST converge to true value within 150 samples for stationary processes (research indicates 100 may be optimistic)
- **FR-010**: System MUST maintain backward compatibility with existing ParticlePortfolio API (no breaking changes to `update()` signature)

### Key Entities *(include if feature involves data)*

- **OnlineCorrelationMatrix**: N×N symmetric matrix tracking pairwise correlations between strategies. Updated online using Welford's algorithm + EMA + Ledoit-Wolf shrinkage. Stored as full N×N matrix for direct indexing (simplicity over memory efficiency for N < 50).
- **Covariance Penalty**: Scalar value representing portfolio concentration risk. Computed as weighted sum of correlations: `sum_i sum_j (weight_i * weight_j * correlation_ij)` for i ≠ j.
- **Portfolio State**: Existing PortfolioState object extended with correlation metrics (Herfindahl index, effective N, max correlation).
- **Strategy Return History**: Rolling window (max 1000 samples) or exponential statistics (mean, variance, covariance) for each strategy pair. Used to compute correlations without storing full history.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Portfolio concentration reduces by at least 20% when tested on synthetic dataset with 3 correlated strategies (correlation > 0.8) compared to baseline
- **SC-002**: Correlation matrix updates complete in under 1 millisecond for 10-strategy portfolio (45 pairs) on standard hardware
- **SC-003**: Correlation estimates converge to within 5% of true correlation value after observing 150 return pairs in stationary environment
- **SC-004**: System handles portfolios with up to 20 strategies without performance degradation (< 1ms per allocation decision)
- **SC-005**: Effective number of strategies increases by at least 30% when CSRC is enabled on correlated strategy portfolio (e.g., from Effective N = 2 to Effective N = 2.6 for 10 strategies)
- **SC-006**: Zero regression in allocation quality for uncorrelated strategies (correlation < 0.3) - allocation weights within 5% of baseline implementation

## Assumptions

- **Stationarity**: Correlations are assumed quasi-stationary over rolling window (500-1000 samples). For fast-changing correlations, exponential weighting with decay=0.99 provides sufficient adaptivity.
- **Strategy Independence Violations**: Current system assumes independence. This feature addresses violations where strategies share common factors (e.g., all momentum, all mean-reversion).
- **Sharpe Ratio Availability**: Assumes strategies report returns at consistent intervals. Sharpe calculation requires sufficient history (min 30 samples for meaningful estimates).
- **Min Samples Calibration**: Default `min_samples=30` is suitable for minute-bar strategies. For lower-frequency strategies (hourly, daily), increase `min_samples` proportionally (e.g., daily → min_samples=60-90).
- **Lambda Calibration**: Default lambda=1.0 chosen based on Varlashova & Bilokon (2025). Users may tune based on portfolio risk tolerance.
- **Matrix Invertibility**: Correlation matrices may become near-singular. Regularization (epsilon=1e-6 on diagonal) prevents numerical instability.
- **Computational Budget**: Target < 1ms per update assumes modern CPU (2+ GHz). For HFT applications, may need optimized linear algebra libraries (NumPy/BLAS).

## Dependencies

- **Spec 028 (Validation Framework)**: This feature addresses Gap #2 from gap_analysis.md
- **particle_portfolio.py**: Core module to be modified. Must maintain backward compatibility.
- **NumPy**: For efficient correlation matrix operations (optional - can use pure Python for small N)
- **audit_trail (Spec 030)**: Should emit correlation metrics and penalty values to audit log for observability

## Constraints

- **Performance Budget**: < 1ms overhead per allocation decision (critical for live trading)
- **Memory Budget**: O(N²) correlation matrix acceptable for N < 50 strategies (max 2500 floats = 20KB)
- **Backward Compatibility**: Cannot break existing ParticlePortfolio users. New CSRC behavior must be opt-in or transparent.
- **No External Dependencies**: Cannot add heavy ML libraries (scikit-learn, TensorFlow). Must use NumPy or pure Python.
- **NautilusTrader Integration**: Must work within NautilusTrader strategy on_bar() callback constraints (no blocking I/O, no threads)

## Out of Scope

- **Higher-Order Moments**: Only tracking pairwise correlations. No tracking of co-skewness, co-kurtosis (future extension).
- **Dynamic Lambda Tuning**: Lambda parameter is static (user-configured). Adaptive lambda based on market regime is out of scope (could be future Gap #3 ADTS integration).
- **Multi-Asset Correlation**: This feature focuses on strategy-strategy correlation. Asset-asset correlation within strategies is separate concern.
- **Copula-Based Dependencies**: Only tracking linear correlation (Pearson). Tail dependencies, copulas are out of scope.
- **Backtesting Integration**: Feature focuses on live allocation. Backtesting validation is separate task.
- **Transaction Cost Awareness**: Correlation penalty doesn't account for rebalancing costs (Gap #5 is separate feature).

## Future Enhancements (If OOS Shows Problems)

> **Philosophy**: KISS first, complexity only when evidence demands it.
> Per DeMiguel et al. (2009): estimation error often dominates, simpler methods win OOS.

### FE-001: Kendall Correlation (P2 Enhancement)

**Trigger**: OOS testing shows Pearson correlation fails to capture non-linear dependencies between strategies.

**Implementation**:
```python
# Current (linear)
correlation = pearson(returns_a, returns_b)

# P2-compliant (rank-based, captures non-linear)
from scipy.stats import kendalltau
tau, _ = kendalltau(returns_a, returns_b)
```

**Trade-off**: O(N log N) per pair vs O(1) for Pearson. Only add if OOS evidence justifies.

**Reference**: Espana, Le Coz & Smerlak (2024) - "Kendall beats Pearson for portfolios"

### FE-002: Power-Law Penalty Scaling

**Trigger**: Linear penalty causes over-reaction to correlation changes.

**Implementation**:
```python
# Current (linear)
penalty = sum(w_i * w_j * corr_ij)

# P2-compliant (Giller-style)
penalty = sum(w_i * w_j * corr_ij) ** 0.5
```

### FE-003: Tail Dependence (Copulas)

**Trigger**: Strategies show independent behavior normally but crash together (tail dependence).

**When to consider**: After significant drawdown event where correlated losses weren't predicted by Pearson correlation.

---

**Decision Log**: Pearson + Ledoit-Wolf shrinkage chosen for MVP (2026-01-06) based on:
1. Industry standard (Ledoit-Wolf 2004, 2020)
2. KISS principle over theoretical purity
3. P2 applies to sizing, not correlation estimation
4. Research shows simple often beats complex OOS

## Risks

- **Risk 1: Overfitting to Recent Correlations**: If correlations are non-stationary, recent estimates may be misleading. *Mitigation*: Use exponential weighting (decay=0.99) to balance recency vs stability.
- **Risk 2: Numerical Instability**: Correlation matrices can become ill-conditioned. *Mitigation*: Add regularization (epsilon on diagonal), use stable algorithms (Welford's method).
- **Risk 3: Performance Regression**: Adding O(N²) correlation updates could slow down particle updates. *Mitigation*: Profile critical path, use vectorized NumPy operations, add performance tests.
- **Risk 4: Unclear Lambda Calibration**: Users may not know how to set lambda. *Mitigation*: Provide sensible default (1.0), document tuning guidelines with sensitivity analysis (lambda=0.5 → mild penalty, lambda=1.0 → balanced, lambda=2.0 → strong diversification, lambda=5.0 → aggressive diversification), add observability metrics.
- **Risk 5: Correlation ≠ Causation**: High correlation doesn't mean strategies are redundant (could be different time horizons). *Mitigation*: Document limitation, recommend combining with qualitative strategy review.
