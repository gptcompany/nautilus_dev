# Feature Specification: Kelly Criterion Portfolio Integration

**Feature Branch**: `034-kelly-criterion`
**Created**: 2026-01-06
**Status**: Draft
**Source**: Gap #4 (MED) | [Canonical Mapping](../028-validation/gaps_to_specs_mapping.md)

## Problem Statement

Current position sizing pipeline (Signal → SOPS → Giller → Risk Limits) produces sizes based on signal strength and volatility, but does NOT optimize for long-term growth rate at the portfolio level.

**Solution** (Baker & McHale 2013, `docs/research/kelly-vs-giller-analysis.md`): Integrate Kelly Criterion as optional final layer:
```
Signal → SOPS → Giller → [Kelly Scaling] → Risk Limits
```

**Impact**: Without Kelly-based portfolio allocation, the system may:
- Over-allocate to high-variance strategies (sub-optimal growth)
- Under-utilize capital in high-Sharpe strategies
- Miss the growth-optimal balance between return and risk

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fractional Kelly Scaling at Portfolio Level (Priority: P1)

A portfolio manager runs 5 strategies with different Sharpe ratios and volatilities. The system calculates the optimal Kelly fraction for each strategy based on estimated returns and variances, then applies fractional Kelly (default: 0.25) to avoid excessive drawdowns. The final allocation respects both Kelly-optimal growth and risk limits.

**Why this priority**: Core value proposition - Kelly-based scaling is the main feature. Without it, the spec delivers no value. Fractional Kelly (not full Kelly) is essential to avoid 50%+ drawdowns.

**Independent Test**: Can be tested by providing known return/variance estimates for 5 mock strategies and verifying that Kelly fractions are calculated correctly, fractional scaling is applied, and resulting allocations improve simulated geometric growth rate vs equal-weight baseline.

**Acceptance Scenarios**:

1. **Given** Strategy A with μ=10%, σ²=4% (Sharpe 0.5), **When** Kelly allocation is calculated, **Then** f* = μ/σ² = 2.5, and fractional Kelly (β=0.25) produces f_actual = 0.625 (62.5% of capital)
2. **Given** Strategy B with μ=5%, σ²=25% (Sharpe 0.1), **When** Kelly allocation is calculated, **Then** f* = 0.2, and fractional Kelly produces f_actual = 0.05 (5% of capital)
3. **Given** Kelly allocations that sum to >100%, **When** normalization is applied, **Then** allocations are scaled proportionally to sum to 100% while preserving relative weights
4. **Given** user configures β=0.5 (half Kelly), **When** allocations are recalculated, **Then** all strategy allocations double (up to risk limits)

---

### User Story 2 - Integration with Existing Pipeline (Priority: P1)

A developer integrates Kelly scaling into the existing meta_portfolio.py without disrupting current functionality. The Kelly layer is **optional** and can be enabled/disabled via configuration. When disabled, the system behaves exactly as before.

**Why this priority**: Backward compatibility is essential. Existing strategies must continue working. Kelly is an enhancement, not a replacement.

**Independent Test**: Run existing meta-portfolio backtests with Kelly disabled and verify identical results to baseline. Then enable Kelly and verify allocations change as expected.

**Acceptance Scenarios**:

1. **Given** Kelly integration disabled (default), **When** meta_portfolio.update() is called, **Then** behavior is identical to pre-integration baseline
2. **Given** Kelly integration enabled, **When** strategy performance data is available, **Then** Kelly fractions are calculated and applied as final scaling layer before risk limits
3. **Given** Kelly integration enabled but insufficient data (< 30 days), **When** allocation is requested, **Then** system falls back to non-Kelly allocation with warning logged

---

### User Story 3 - Estimation Uncertainty Handling (Priority: P2)

Kelly Criterion requires estimates of μ (expected return) and σ² (variance). In practice, these estimates have uncertainty, especially with limited data. The system adjusts Kelly fractions based on estimation confidence, becoming more conservative when uncertainty is high.

**Why this priority**: Addresses the key weakness of Kelly - sensitivity to estimation error. Without this, Kelly can produce dangerous over-allocations from noisy estimates.

**Independent Test**: Provide mock strategy returns with varying sample sizes (30, 90, 180 days). Verify that Kelly fractions decrease as sample size decreases (higher uncertainty).

**Acceptance Scenarios**:

1. **Given** strategy with 180 days of returns, **When** Kelly fraction is calculated, **Then** full fractional Kelly is applied (high confidence)
2. **Given** strategy with 30 days of returns (= min_samples), **When** Kelly fraction is calculated, **Then** Kelly fraction is reduced by uncertainty factor: confidence = 0.5 (min_confidence), so f_adjusted = f_fractional × 0.5
3. **Given** strategy with < min_samples (default 30) days of returns, **When** Kelly fraction is requested, **Then** system returns conservative default allocation (not Kelly-based)

---

### Edge Cases

- **What happens when μ estimate is negative?** Kelly fraction is 0 (don't allocate to losing strategies)
- **What happens when σ² estimate is near zero?** Cap Kelly fraction to prevent division instability (max f* = 2.0)
- **What happens when all strategies have negative μ?** System warns operator and uses minimum allocation (min_allocation, default 1% per strategy) to maintain diversification
- **How does Kelly interact with existing risk limits?** Kelly allocations are capped by risk limits (Kelly suggests, limits enforce)
- **What happens during regime changes when μ/σ² shift rapidly?** Use exponential weighting on historical returns (decay similar to ADTS)

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate Kelly fraction f* = μ/σ² for each strategy using rolling return estimates
- **FR-002**: System MUST apply fractional Kelly scaling: f_actual = β × f*, where β is configurable (default: 0.25)
- **FR-003**: System MUST normalize Kelly allocations to sum to 100% when total exceeds available capital
- **FR-004**: System MUST integrate Kelly scaling as optional layer in meta_portfolio.py (disabled by default)
- **FR-005**: System MUST fallback to non-Kelly allocation when estimation data is insufficient (< min_samples)
- **FR-006**: System MUST adjust Kelly fractions based on estimation uncertainty (fewer samples → more conservative)
- **FR-007**: System MUST cap Kelly fractions to prevent extreme allocations (max_kelly_fraction, default: 2.0)
- **FR-008**: System MUST respect existing risk limits - Kelly allocations are suggestions, limits are hard constraints
- **FR-009**: System MUST log Kelly calculations including μ, σ², f*, f_actual, uncertainty adjustment for audit
- **FR-010**: System MUST use exponential weighting on historical returns (configurable decay) for non-stationarity

### Key Entities

- **KellyAllocator**: Calculates Kelly-optimal fractions for a set of strategies. Inputs: return estimates (μ), variance estimates (σ²), fractional beta (β). Outputs: allocation fractions per strategy.

- **EstimationUncertainty**: Quantifies confidence in μ/σ² estimates based on sample size and return stability. Higher uncertainty → more conservative Kelly fractions.

- **KellyConfig**: Configuration dataclass with: enabled (bool), beta (float, default 0.25), min_samples (int, default 30), max_fraction (float, default 2.0), decay (float, default 0.99), min_allocation (float, default 0.01), uncertainty_adjustment (bool, default True).

---

## Integration Point

**Pipeline after integration**:
```
Signal → SOPS → Giller → [Kelly Scaling] → Risk Limits → Final Position
```

**Target file**: `strategies/common/adaptive_control/meta_portfolio.py`

**Dependency**: Requires strategy return history from MetaController performance tracking.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Kelly integration improves geometric growth rate by 5-15% in backtest vs non-Kelly baseline (measured over 12-month simulation)
- **SC-002**: Maximum drawdown with fractional Kelly (β=0.25) does not exceed 1.5x baseline drawdown
- **SC-003**: Kelly calculations complete in < 1ms for portfolios up to 20 strategies
- **SC-004**: System correctly falls back to non-Kelly when data insufficient (verified by unit tests)
- **SC-005**: Backward compatibility verified: Kelly disabled produces identical results to pre-integration baseline
- **SC-006**: Estimation uncertainty adjustment reduces over-allocation by 30-50% when sample size < 60 days

---

## Effort Estimate

**From gap_analysis.md**: 4 hours

**Breakdown**:
- KellyAllocator class: 1.5h
- EstimationUncertainty: 0.5h
- Integration into meta_portfolio.py: 1h
- Unit tests: 1h

---

## References

- `docs/research/kelly-vs-giller-analysis.md` - Kelly/Giller/SOPS complementary analysis
- Baker & McHale 2013 - Kelly with parameter uncertainty
- Giller 2020 - Power-law sizing relationship to Kelly
