# Implementation Plan: Walk-Forward Validation

**Feature Branch**: `020-walk-forward-validation`
**Created**: 2025-12-29
**Status**: Planning
**Spec Reference**: `specs/020-walk-forward-validation/spec.md`

## Architecture Overview

Walk-forward validation is a critical component for preventing overfitting in evolved strategies. Based on academic research (arXiv:2512.12924), >90% of academic strategies fail when implemented with real capital due to backtesting overfitting.

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                     Alpha-Evolve Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│  Strategy Evolution → Walk-Forward Validation → Live Deployment │
│                              ↑                                   │
│                    ┌─────────┴─────────┐                        │
│                    │  WalkForwardValidator │                    │
│                    └─────────┬─────────┘                        │
│              ┌───────────────┼───────────────┐                  │
│              ↓               ↓               ↓                  │
│         Window 1        Window 2        Window N                │
│      (Train→Test)    (Train→Test)    (Train→Test)              │
│              └───────────────┼───────────────┘                  │
│                              ↓                                   │
│                    Robustness Score + Metrics                   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
scripts/alpha_evolve/
├── walk_forward/
│   ├── __init__.py
│   ├── validator.py      # WalkForwardValidator class
│   ├── config.py         # WalkForwardConfig Pydantic model
│   ├── window.py         # Window, WindowResult dataclasses
│   ├── metrics.py        # Robustness score, degradation ratio
│   └── report.py         # Markdown report generation
├── controller.py         # Integration point (existing)
└── evaluator.py          # Strategy evaluation (existing)

tests/
└── test_walk_forward/
    ├── test_validator.py
    ├── test_window_generation.py
    ├── test_metrics.py
    └── test_integration.py
```

## Constitution Check

| Principle | Compliance | Notes |
|-----------|------------|-------|
| Black Box Design | ✅ | WalkForwardValidator is self-contained module |
| KISS & YAGNI | ✅ | Simple rolling window, no complex ML |
| Native First | ✅ | Uses NautilusTrader BacktestNode |
| No df.iterrows() | ✅ | Window generation uses timedelta math |
| TDD Discipline | ✅ | Tests for each component required |

## Technical Decisions

### Decision 1: Window Generation Strategy

**Options Considered**:
1. **Anchored (Expanding) Window**: Train always starts from beginning
   - Pros: More training data per window
   - Cons: Initial periods dominate training
2. **Rolling (Sliding) Window**: Fixed-size train window moves forward
   - Pros: Recent data weighted equally
   - Cons: Less training data

**Selected**: Rolling (Sliding) Window

**Rationale**: Based on arXiv:2512.12924 findings - rolling windows better capture regime changes and prevent early data from dominating. The paper used 34 independent test periods with rolling approach.

---

### Decision 2: Robustness Score Components

**Options Considered**:
1. **Simple Profitability %**: Just count profitable windows
   - Pros: Easy to understand
   - Cons: Ignores consistency and degradation
2. **Composite Score**: Consistency + Profitability + Degradation
   - Pros: Multi-dimensional assessment
   - Cons: Weighting is subjective

**Selected**: Composite Score with Advanced Metrics

**Rationale**: Academic research shows single metrics (Sharpe) are insufficient:
- **Base Composite Score**: Consistency (30%) + Profitability (40%) + Degradation (30%)
- **Deflated Sharpe Ratio (DSR)**: Lopez de Prado (2018, Ch. 14) adjusts Sharpe for multiple testing and non-normal returns
- **Probability of Backtest Overfitting (PBO)**: Lopez de Prado (2018, Ch. 11) estimates false positive probability

The DSR prevents "Sharpe ratio shopping" where strategies are optimized until they show high Sharpe by chance. PBO provides a probabilistic measure of overfitting risk.

---

### Decision 3: Purging (Embargo) Period

**Options Considered**:
1. **No Gap**: Test immediately after train
   - Pros: Maximum data utilization
   - Cons: Potential lookahead/leakage via lagging indicators
2. **Gap Period**: 1-5 day embargo between train/test
   - Pros: Removes serial correlation bias
   - Cons: Loses some test data

**Selected**: Configurable Gap Period (default: 5 days)

**Rationale**: Lopez de Prado (2018, Ch. 7 - "Cross-Validation in Finance") demonstrates that Purged K-Fold Cross-Validation (PKCV) requires embargo periods to prevent leakage from serially correlated labels. A 5-day default gap removes contamination from lagging indicators while balancing data utilization. The paper shows that without purging, cross-validation can overestimate performance by 50%+.

---

### Decision 4: Embargo Period Strategy

**Options Considered**:
1. **Pre-Test Embargo Only**: Gap before test period (existing `gap_days`)
   - Pros: Simple to implement, removes forward contamination
   - Cons: Doesn't prevent test data leaking into next training window
2. **Dual Embargo**: Gap before AND after test period
   - Pros: Complete isolation of test windows
   - Cons: Reduces available training data
3. **Symmetric Embargo**: Equal gaps on both sides
   - Pros: Balanced approach, recommended by Lopez de Prado
   - Cons: Most conservative (maximum data loss)

**Selected**: Dual Embargo with Configurable Periods

**Rationale**: Lopez de Prado (2018, Ch. 7.4.3) recommends both pre-test and post-test embargoes to prevent contamination in both directions:
- **Pre-test embargo** (`embargo_before_days`): Prevents training features from leaking into test via lagging indicators
- **Post-test embargo** (`embargo_after_days`): Prevents test observations from contaminating the next training window

The paper demonstrates that post-test embargo is equally important when test periods are followed by subsequent training windows, as serial correlation can cause test data to influence later model training.

**Configuration**:
```python
embargo_before_days: int = 5   # Pre-test purge (default 5)
embargo_after_days: int = 3    # Post-test purge (default 3)
```

---

## Implementation Strategy

### Phase 1: Foundation (Core Models)

**Goal**: Define data models and configuration

**Deliverables**:
- [x] `WalkForwardConfig` Pydantic model
- [x] `Window`, `WindowResult`, `WalkForwardResult` dataclasses
- [x] Window generation algorithm

**Dependencies**: None

---

### Phase 2: Core Implementation (Validator)

**Goal**: Implement WalkForwardValidator with evaluation

**Deliverables**:
- [ ] `WalkForwardValidator.validate()` method
- [ ] `_calculate_robustness()` scoring
- [ ] `_check_criteria()` pass/fail logic
- [ ] Integration with existing `StrategyEvaluator`

**Dependencies**: Phase 1, Spec-007 (Evaluator)

---

### Phase 2.5: Advanced Metrics (Lopez de Prado)

**Goal**: Implement advanced overfitting detection metrics from "Advances in Financial Machine Learning"

**Deliverables**:
- [ ] Deflated Sharpe Ratio (DSR) calculation (Ch. 14)
- [ ] Probability of Backtest Overfitting (PBO) estimation (Ch. 11)
- [ ] Combinatorial path simulation for PBO
- [ ] Add DSR and PBO to `WalkForwardResult` metrics
- [ ] Update robustness scoring to incorporate DSR

**Rationale**:
- **DSR** (Ch. 14): Adjusts Sharpe ratio for multiple testing and non-normal returns, preventing false positives from "Sharpe ratio shopping"
- **PBO** (Ch. 11): Estimates probability that the best-performing strategy in backtest is a false positive due to overfitting
- **Combinatorial Paths**: Generates alternative performance paths to test strategy robustness across different historical orderings

**Dependencies**: Phase 2 (Validator)

---

### Phase 3: Reporting & Integration

**Goal**: Generate reports and integrate with controller

**Deliverables**:
- [ ] Markdown report generation
- [ ] JSON result export
- [ ] Integration with `AlphaEvolveController`
- [ ] CLI command for standalone validation

**Dependencies**: Phase 2

---

### Phase 4: Testing & Documentation

**Goal**: Comprehensive test coverage and docs

**Deliverables**:
- [ ] Unit tests (>80% coverage)
- [ ] Integration test with sample strategy
- [ ] Update `docs/ARCHITECTURE.md`
- [ ] Add to CLAUDE.md agent guidelines

**Dependencies**: Phase 3

---

## Data Model Considerations

### WalkForwardResult Extensions

To support Lopez de Prado's advanced metrics, the `WalkForwardResult` dataclass must include:

```python
@dataclass
class WalkForwardResult:
    """Walk-forward validation results."""

    # Existing fields
    strategy_name: str
    windows: list[WindowResult]
    robustness_score: float
    passed: bool

    # New: Advanced overfitting metrics
    deflated_sharpe_ratio: float | None = None
    """Sharpe ratio adjusted for multiple testing (Lopez de Prado Ch. 14)"""

    probability_backtest_overfitting: float | None = None
    """PBO: Probability best strategy is false positive (Lopez de Prado Ch. 11)"""

    num_strategy_trials: int | None = None
    """N: Number of strategies/parameters tested (for DSR calculation)"""

    combinatorial_paths_tested: int | None = None
    """Number of permuted backtest paths used in PBO estimation"""
```

### Metrics Module Extensions

The `metrics.py` module will implement:

1. **`calculate_deflated_sharpe_ratio(sharpe: float, n_trials: int) -> float`**
   - Formula: `DSR = norm.ppf(norm.cdf(sharpe) - log(n_trials) / sqrt(n_trials))`
   - Adjusts for multiple hypothesis testing
   - Returns deflated Sharpe (always <= raw Sharpe)

2. **`estimate_probability_backtest_overfitting(window_results: list[WindowResult]) -> float`**
   - Generates combinatorial permutations of window orderings
   - Compares in-sample (train) vs out-of-sample (test) performance distributions
   - Returns P[median(IS) < median(OOS)]
   - PBO > 0.5 indicates likely overfitting

3. **`simulate_combinatorial_paths(windows: list[WindowResult], n_permutations: int = 100) -> list[float]`**
   - Helper for PBO: shuffles window orderings
   - Recalculates performance metrics for each permutation
   - Returns distribution of Sharpe ratios across paths

---

## File Structure

```
scripts/alpha_evolve/
├── walk_forward/
│   ├── __init__.py           # Public exports
│   ├── config.py             # WalkForwardConfig
│   ├── models.py             # Window, WindowResult, WalkForwardResult
│   ├── validator.py          # WalkForwardValidator
│   ├── metrics.py            # calculate_robustness_score()
│   └── report.py             # generate_report()
├── controller.py             # Add evolve_with_validation()
└── evaluator.py              # Existing (unchanged)

tests/test_walk_forward/
├── __init__.py
├── conftest.py               # Fixtures
├── test_config.py
├── test_window_generation.py
├── test_validator.py
├── test_metrics.py
└── test_integration.py
```

## API Design

### Public Interface

```python
from scripts.alpha_evolve.walk_forward import (
    WalkForwardConfig,
    WalkForwardValidator,
    WalkForwardResult,
)

# Configuration
config = WalkForwardConfig(
    data_start=datetime(2023, 1, 1),
    data_end=datetime(2024, 12, 1),
    train_months=6,
    test_months=3,
    step_months=3,
    embargo_before_days=5,  # Pre-test purge (Lopez de Prado PKCV)
    embargo_after_days=3,   # Post-test purge
    min_windows=4,
    min_profitable_windows_pct=0.75,
)

# Validation
validator = WalkForwardValidator(config, evaluator)
result: WalkForwardResult = await validator.validate(strategy_code)

# Results
print(f"Robustness: {result.robustness_score:.1f}/100")
print(f"Passed: {result.passed}")
print(f"Deflated Sharpe: {result.deflated_sharpe_ratio:.3f}")
print(f"PBO Risk: {result.probability_backtest_overfitting:.1%}")
```

### Configuration

```python
class WalkForwardConfig(BaseModel):
    """Walk-forward validation configuration."""

    # Date range
    data_start: datetime
    data_end: datetime

    # Window sizes
    train_months: int = 6
    test_months: int = 3
    step_months: int = 3          # Rolling step
    embargo_before_days: int = 5  # Pre-test purge (Lopez de Prado PKCV)
    embargo_after_days: int = 3   # Post-test purge (prevent next train contamination)

    # Validation criteria
    min_windows: int = 4
    min_profitable_windows_pct: float = 0.75
    min_test_sharpe: float = 0.5
    max_drawdown_threshold: float = 0.30
    min_robustness_score: float = 60.0

    # Reproducibility
    seed: int | None = None
```

## Testing Strategy

### Unit Tests
- [x] Test `WalkForwardConfig` validation
- [ ] Test window generation (date arithmetic)
- [ ] Test robustness score calculation
- [ ] Test pass/fail criteria logic

### Integration Tests
- [ ] Test with mock `StrategyEvaluator`
- [ ] Test with real strategy on sample data
- [ ] Test edge cases (insufficient windows, all losses)

### Performance Tests
- [ ] Benchmark 5-window validation < 10 minutes
- [ ] Memory profiling for large datasets

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Slow validation (>10min) | Medium | Medium | Parallel window evaluation |
| False positives (overfitting passes) | High | Low | Multiple metrics, strict thresholds |
| Data leakage in features | High | Medium | Configurable gap period |
| Inconsistent results | Medium | Low | Seed for randomness |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.220.0 (BacktestNode)
- Pydantic >= 2.0
- numpy (statistics)

### Internal Dependencies
- Spec 007: Alpha-Evolve Evaluator (`StrategyEvaluator`)
- Spec 009: Alpha-Evolve Controller (integration point)

## Research Insights Applied

Based on `/research walk-forward validation` findings:

1. **arXiv:2512.12924** (Deep et al., 2024):
   - 34 independent test periods using rolling windows
   - Strict information set discipline
   - Realistic transaction costs
   - Result: 0.55% annual return, 0.33 Sharpe (honest, not inflated)

2. **Costa & Gebbie (2020)**:
   - CSCV (Combinatorial Symmetric CV) for robustness
   - Deflated Sharpe Ratio adjusts for multiple testing
   - Feature: Consider adding DSR to metrics in future

3. **Key Takeaway**:
   - Honest validation produces modest but real returns
   - >90% academic strategies fail in practice
   - Regime dependence is critical (volatile markets differ)

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Validation completes < 10 minutes for 5 windows
- [ ] Robustness score correctly identifies overfitting
- [ ] Documentation updated (ARCHITECTURE.md)
- [ ] Code review approved
- [ ] Alpha-debug verification passed
