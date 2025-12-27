# Quickstart: Alpha-Evolve Backtest Evaluator

**Feature**: 007-alpha-evolve-evaluator
**Created**: 2025-12-27

## Overview

The Backtest Evaluator enables dynamic strategy evaluation for the AlphaEvolve system. It loads strategy code from strings, runs backtests, and extracts standardized fitness metrics.

## Prerequisites

1. **NautilusTrader Nightly Environment**:
   ```bash
   source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
   ```

2. **Pre-populated ParquetDataCatalog** with historical data for your target instruments.

3. **spec-006 dependencies**: FitnessMetrics from `scripts/alpha_evolve/store.py`

## Installation

The evaluator is part of the alpha_evolve package:

```python
from scripts.alpha_evolve.evaluator import (
    BacktestConfig,
    EvaluationRequest,
    EvaluationResult,
    StrategyEvaluator,
)
from scripts.alpha_evolve.store import FitnessMetrics
```

## Basic Usage

### 1. Configure the Evaluator

```python
from scripts.alpha_evolve.evaluator import BacktestConfig, StrategyEvaluator

# Define default backtest configuration
config = BacktestConfig(
    catalog_path="/path/to/your/catalog",
    instrument_id="BTCUSDT-PERP.BINANCE",
    start_date="2024-01-01",
    end_date="2024-06-01",
    bar_type="1-MINUTE-LAST",
    initial_capital=100_000.0,
)

# Create evaluator with memory safety limits
evaluator = StrategyEvaluator(
    default_config=config,
    max_concurrent=2,       # Limit concurrent evaluations
    timeout_seconds=300,    # 5-minute timeout
)
```

### 2. Evaluate a Strategy

```python
from scripts.alpha_evolve.evaluator import EvaluationRequest

# Strategy code as string (e.g., from LLM generation)
strategy_code = '''
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar

class EvolvedStrategyConfig(StrategyConfig, frozen=True):
    instrument_id: str
    fast_period: int = 10
    slow_period: int = 20

class EvolvedStrategy(Strategy):
    def __init__(self, config: EvolvedStrategyConfig):
        super().__init__(config)

    def on_start(self):
        self.subscribe_bars(self.config.bar_type)

    def on_bar(self, bar: Bar):
        # Simple momentum logic
        pass
'''

# Create evaluation request
request = EvaluationRequest(
    strategy_code=strategy_code,
    strategy_class_name="EvolvedStrategy",
    config_class_name="EvolvedStrategyConfig",
)

# Run synchronous evaluation
result = evaluator.evaluate_sync(request)
```

### 3. Handle Results

```python
if result.success:
    print(f"Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
    print(f"Calmar Ratio: {result.metrics.calmar_ratio:.2f}")
    print(f"Max Drawdown: {result.metrics.max_drawdown:.2%}")
    print(f"CAGR: {result.metrics.cagr:.2%}")
    print(f"Total Return: {result.metrics.total_return:.2%}")
    print(f"Trade Count: {result.trade_count}")
    print(f"Duration: {result.duration_ms}ms")
else:
    print(f"Evaluation failed: {result.error}")
    print(f"Error type: {result.error_type}")
```

## Async Usage

For integration with the evolution controller (spec-009):

```python
import asyncio
from scripts.alpha_evolve.evaluator import StrategyEvaluator

async def evaluate_population(evaluator: StrategyEvaluator, strategies: list[str]):
    """Evaluate multiple strategies concurrently."""
    requests = [
        EvaluationRequest(strategy_code=code)
        for code in strategies
    ]

    # Concurrency is limited by evaluator's max_concurrent
    results = await asyncio.gather(*[
        evaluator.evaluate(req) for req in requests
    ])

    return results

# Run
async def main():
    evaluator = StrategyEvaluator(default_config=config, max_concurrent=2)
    results = await evaluate_population(evaluator, [strategy1, strategy2, strategy3])
    # With max_concurrent=2, at most 2 run simultaneously

asyncio.run(main())
```

## Error Handling

The evaluator classifies errors for proper handling:

```python
result = evaluator.evaluate_sync(request)

match result.error_type:
    case "syntax":
        # Invalid Python syntax - regenerate code
        print(f"Syntax error: {result.error}")
    case "import":
        # Missing module - check imports
        print(f"Import error: {result.error}")
    case "runtime":
        # Exception during backtest - review logic
        print(f"Runtime error: {result.error}")
    case "timeout":
        # Strategy took too long - simplify or optimize
        print(f"Timeout after {result.duration_ms}ms")
    case "data":
        # Missing or invalid data - check catalog
        print(f"Data error: {result.error}")
    case None:
        # Success
        assert result.success
```

## Integration with ProgramStore (spec-006)

Store evaluation results in the Hall-of-Fame:

```python
from scripts.alpha_evolve.store import ProgramStore

store = ProgramStore("/path/to/store.db")

# Insert strategy with metrics
if result.success:
    program_id = store.insert(
        code=request.strategy_code,
        metrics=result.metrics,
        parent_id=parent_id,  # For lineage tracking
        experiment="experiment_001",
    )
    print(f"Stored as: {program_id}")
```

## Performance Considerations

### Memory

- Each evaluation uses ~2-4GB RAM (6mo 1-minute data)
- Set `max_concurrent` based on available memory:
  ```python
  max_concurrent = (available_ram_gb - 4) // 4  # Conservative
  ```

### Timeout

- Default: 300 seconds (5 minutes)
- Adjust based on data size:
  ```python
  # Larger datasets need more time
  evaluator = StrategyEvaluator(
      default_config=config,
      timeout_seconds=600,  # 10 minutes for 12mo data
  )
  ```

### Data Loading

- Uses streaming via ParquetDataCatalog
- Data is loaded on-demand, not all at once
- Chunk size handled by NautilusTrader

## Fitness Metrics Reference

| Metric | Description | Good Values |
|--------|-------------|-------------|
| sharpe_ratio | Risk-adjusted return (annualized) | > 1.0 |
| calmar_ratio | CAGR / MaxDD | > 1.0 |
| max_drawdown | Maximum peak-to-trough loss | < 0.20 (20%) |
| cagr | Compound annual growth rate | > 0.10 (10%) |
| total_return | Total period return | Varies |
| win_rate | Winning trades / Total trades | > 0.50 (50%) |
| trade_count | Number of closed positions | Depends on strategy |

## Troubleshooting

### "Catalog path not found"

```python
# Ensure catalog exists and has data
from nautilus_trader.persistence.catalog import ParquetDataCatalog

catalog = ParquetDataCatalog(config.catalog_path)
print(catalog.instruments())  # Should list available instruments
```

### "Instrument not found"

```python
# Check available instruments
catalog = ParquetDataCatalog(config.catalog_path)
for inst in catalog.instruments():
    print(inst.id)

# Match your config
config = BacktestConfig(
    instrument_id="BTCUSDT-PERP.BINANCE",  # Must match catalog
    ...
)
```

### "No trades executed"

Strategy may not be generating signals. Check:
1. Bar subscription in `on_start()`
2. Signal logic in `on_bar()`
3. Order submission

### Timeout Issues

If evaluations frequently timeout:
1. Increase timeout_seconds
2. Check for infinite loops in strategy
3. Reduce data date range for testing

## Known Limitations

### Edge Cases Not Handled

The following edge cases are documented but not fully handled in the current implementation:

| Edge Case | Behavior | Workaround |
|-----------|----------|------------|
| **Infinite loops in strategy** | Timeout after configured limit (default 5min). May not interrupt Rust C extensions. | Use short timeouts during evolution; multiprocessing isolation planned for future |
| **Strategy imports unavailable modules** | Returns `error_type="import"` with module name | Only use NautilusTrader imports in evolved strategies |
| **Data has gaps or missing bars** | BacktestEngine handles gracefully; metrics may be affected | Validate data catalog before evaluation runs |
| **Timezone differences** | All data assumed UTC | Ensure catalog data is normalized to UTC |
| **Invalid ParquetDataCatalog path** | Returns `error_type="data"` before backtest starts | Validate paths in caller code |

### Performance Boundaries

- Evaluations on >12 months of 1-minute data may exceed default timeout
- Memory usage scales with data size; 4GB limit assumes 6-month datasets
- Concurrent evaluations share CPU; performance degrades with high concurrency

## Next Steps

- **spec-008**: Strategy templates for LLM prompting
- **spec-009**: Evolution controller for mutation/selection
- **spec-010**: Dashboard for monitoring evolution progress
