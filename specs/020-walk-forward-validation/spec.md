# Spec 020: Walk-Forward Validation

## Overview

Implement walk-forward validation for evolved strategies to prevent overfitting and ensure robustness before live deployment.

## Problem Statement

Alpha-Evolve can produce strategies that perform well on historical data but fail in live trading (overfitting). Walk-forward validation tests strategies on unseen data.

## Goals

1. **Out-of-Sample Testing**: Validate on data not used in evolution
2. **Walk-Forward Analysis**: Rolling window validation
3. **Robustness Score**: Quantify strategy robustness

## Requirements

### Functional Requirements

#### FR-001: Data Splitting
```
Total Data Period: 2023-01-01 to 2024-12-01 (24 months)

Walk-Forward Windows:
├── Window 1: Train: 2023-01-01 to 2023-06-30 | Test: 2023-07-01 to 2023-09-30
├── Window 2: Train: 2023-04-01 to 2023-09-30 | Test: 2023-10-01 to 2023-12-31
├── Window 3: Train: 2023-07-01 to 2023-12-31 | Test: 2024-01-01 to 2024-03-31
├── Window 4: Train: 2023-10-01 to 2024-03-31 | Test: 2024-04-01 to 2024-06-30
└── Window 5: Train: 2024-01-01 to 2024-06-30 | Test: 2024-07-01 to 2024-09-30
```

#### FR-002: Configuration

See `plan.md` for authoritative `WalkForwardConfig` definition with all fields.

**Key parameters**:
- `train_months`: Training window size (default: 6)
- `test_months`: Test window size (default: 3)
- `step_months`: Rolling step size (default: 3)
- `embargo_before_days`: Pre-test purge period (default: 5, per Lopez de Prado PKCV)
- `embargo_after_days`: Post-test purge period (default: 3)
- `min_windows`: Minimum windows required (default: 4)
- `min_profitable_windows_pct`: Min % profitable windows (default: 0.75)

#### FR-003: Metrics Per Window
- Sharpe Ratio
- Calmar Ratio
- Max Drawdown
- Total Return
- Win Rate
- Trade Count

#### FR-004: Robustness Score
```python
def calculate_robustness_score(window_results: list[WindowMetrics]) -> float:
    """
    Robustness Score (0-100):
    - Consistency: Std dev of returns across windows (lower = better)
    - Profitability: % of windows profitable
    - Degradation: Train vs Test performance ratio
    """
    consistency = 1 - min(np.std(returns) / np.mean(returns), 1)
    profitability = sum(r.total_return > 0 for r in window_results) / len(window_results)
    degradation = np.mean([r.test_sharpe / r.train_sharpe for r in window_results])

    return (consistency * 0.3 + profitability * 0.4 + min(degradation, 1) * 0.3) * 100
```

#### FR-005: Pass/Fail Criteria
- Robustness Score >= 60
- At least 75% of windows profitable
- Test Sharpe >= 0.5 in more than half of windows (> len(windows) // 2)
- No window with drawdown > 30%

### Non-Functional Requirements

#### NFR-001: Performance
- Walk-forward analysis < 10 minutes for 5 windows

#### NFR-002: Reproducibility
- Same strategy + config = same results
- Seed for random elements

## Technical Design

### WalkForwardValidator

```python
class WalkForwardValidator:
    """Validates strategies using walk-forward analysis."""

    def __init__(self, config: WalkForwardConfig, evaluator: StrategyEvaluator):
        self.config = config
        self.evaluator = evaluator

    async def validate(self, strategy_code: str) -> WalkForwardResult:
        """Run walk-forward validation on strategy."""
        windows = self._generate_windows()
        results = []

        for window in windows:
            # Train evaluation (for reference)
            train_metrics = await self.evaluator.evaluate(
                strategy_code,
                start_date=window.train_start,
                end_date=window.train_end,
            )

            # Test evaluation (out-of-sample)
            test_metrics = await self.evaluator.evaluate(
                strategy_code,
                start_date=window.test_start,
                end_date=window.test_end,
            )

            results.append(WindowResult(
                window=window,
                train_metrics=train_metrics,
                test_metrics=test_metrics,
            ))

        return WalkForwardResult(
            windows=results,
            robustness_score=self._calculate_robustness(results),
            passed=self._check_criteria(results),
        )

    def _generate_windows(self) -> list[Window]:
        """Generate walk-forward windows from config."""
        windows = []
        current_start = self.config.data_start

        while current_start + timedelta(days=self.config.train_months * 30 + self.config.test_months * 30) <= self.config.data_end:
            train_end = current_start + timedelta(days=self.config.train_months * 30)
            test_start = train_end
            test_end = test_start + timedelta(days=self.config.test_months * 30)

            windows.append(Window(
                train_start=current_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            ))

            current_start += timedelta(days=self.config.step_months * 30)

        return windows
```

### Integration with Alpha-Evolve

```python
# In controller.py
async def evolve_with_validation(self) -> Strategy:
    """Run evolution with walk-forward validation."""
    # Run evolution
    best_strategy = await self.evolve()

    # Validate best strategy
    validator = WalkForwardValidator(self.config.walk_forward, self.evaluator)
    validation_result = await validator.validate(best_strategy.code)

    if not validation_result.passed:
        self.log.warning(
            f"Strategy failed walk-forward validation. "
            f"Robustness: {validation_result.robustness_score:.1f}/100"
        )
        return None

    return best_strategy
```

### Report Generation

```python
def generate_report(result: WalkForwardResult) -> str:
    """Generate walk-forward validation report."""
    report = ["# Walk-Forward Validation Report\n"]

    report.append(f"**Robustness Score**: {result.robustness_score:.1f}/100")
    report.append(f"**Status**: {'PASSED' if result.passed else 'FAILED'}\n")

    report.append("## Window Results\n")
    report.append("| Window | Train Sharpe | Test Sharpe | Test Return | Test DD |")
    report.append("|--------|--------------|-------------|-------------|---------|")

    for w in result.windows:
        report.append(
            f"| {w.window.test_start:%Y-%m} | "
            f"{w.train_metrics.sharpe:.2f} | "
            f"{w.test_metrics.sharpe:.2f} | "
            f"{w.test_metrics.total_return:.1%} | "
            f"{w.test_metrics.max_drawdown:.1%} |"
        )

    return "\n".join(report)
```

## Testing Strategy

1. **Window Generation**: Correct date ranges
2. **Metric Calculation**: Robustness score accuracy
3. **Pass/Fail Logic**: Criteria enforcement
4. **Integration**: Full pipeline with alpha-evolve

## Dependencies

- Spec 007 (Alpha-Evolve Evaluator)
- Spec 009 (Alpha-Evolve Controller)

## Success Metrics

- 100% of deployed strategies pass walk-forward
- Robustness score > 60 for production strategies
- Live performance within 20% of walk-forward test metrics
