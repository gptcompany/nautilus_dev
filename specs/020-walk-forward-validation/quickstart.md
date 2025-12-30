# Quickstart: Walk-Forward Validation

## Installation

No additional dependencies required. Uses existing alpha-evolve infrastructure.

## Basic Usage

```python
from datetime import datetime
from scripts.alpha_evolve.walk_forward import (
    WalkForwardConfig,
    WalkForwardValidator,
)
from scripts.alpha_evolve.evaluator import StrategyEvaluator

# 1. Configure validation
config = WalkForwardConfig(
    data_start=datetime(2023, 1, 1),
    data_end=datetime(2024, 12, 1),
    train_months=6,
    test_months=3,
    step_months=3,
)

# 2. Initialize validator with evaluator
evaluator = StrategyEvaluator(...)  # Your existing evaluator
validator = WalkForwardValidator(config, evaluator)

# 3. Run validation
result = await validator.validate(strategy_code)

# 4. Check results
print(f"Robustness: {result.robustness_score:.1f}/100")
print(f"Passed: {result.passed}")

if result.passed:
    print("Strategy ready for live deployment!")
else:
    print("Strategy failed validation - likely overfitting")
```

## Integration with Alpha-Evolve

```python
from scripts.alpha_evolve.controller import AlphaEvolveController

controller = AlphaEvolveController(config)

# Run evolution with automatic walk-forward validation
strategy = await controller.evolve_with_validation()

if strategy:
    print(f"Evolved strategy passed validation: {strategy.name}")
else:
    print("No strategy passed walk-forward validation")
```

## CLI Usage

```bash
# Validate a strategy file
python -m scripts.alpha_evolve.walk_forward.cli validate \
    --strategy strategies/evolved/my_strategy.py \
    --start 2023-01-01 \
    --end 2024-12-01

# Generate validation report
python -m scripts.alpha_evolve.walk_forward.cli report \
    --strategy strategies/evolved/my_strategy.py \
    --output reports/wf_validation.md
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| train_months | 6 | Training window size |
| test_months | 3 | Test window size |
| step_months | 3 | Rolling step size |
| gap_days | 0 | Purge period (prevents leakage) |
| min_robustness_score | 60 | Minimum score to pass |
| min_profitable_windows_pct | 0.75 | % of windows that must profit |

## Interpreting Results

### Robustness Score (0-100)

- **80-100**: Excellent - robust strategy, likely to perform live
- **60-80**: Good - acceptable for cautious deployment
- **40-60**: Fair - possible overfitting, needs review
- **0-40**: Poor - significant overfitting, do not deploy

### Window Report Example

```
| Window   | Train Sharpe | Test Sharpe | Test Return | Test DD  |
|----------|--------------|-------------|-------------|----------|
| 2023-Q3  | 1.45         | 0.92        | 3.2%        | -4.1%    |
| 2023-Q4  | 1.38         | 0.78        | 2.1%        | -5.8%    |
| 2024-Q1  | 1.52         | 0.65        | 1.8%        | -6.2%    |
| 2024-Q2  | 1.61         | 0.88        | 2.9%        | -3.9%    |
```

**Interpretation**: Moderate degradation from train to test (normal). Test Sharpe above 0.5 threshold. All windows profitable. Likely to perform in live trading.
