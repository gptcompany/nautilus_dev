# Quickstart: Alpha-Evolve Controller

**Feature Branch**: `009-alpha-evolve-controller`
**Created**: 2025-12-27

## Prerequisites

1. **NautilusTrader Nightly** (v1.222.0+)
   ```bash
   source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
   ```

2. **ParquetDataCatalog** with historical data
   - BTC or ETH data recommended
   - Minimum 6 months for meaningful evolution

3. **Specs 006-008 Implemented**
   - Store (spec-006): `scripts/alpha_evolve/store.py`
   - Evaluator (spec-007): `scripts/alpha_evolve/evaluator.py`
   - Templates (spec-008): `scripts/alpha_evolve/templates/`

---

## Quick Start (CLI)

### 1. Basic Evolution Run

```bash
# Start evolution with momentum seed strategy
evolve start --seed momentum --iterations 50 --experiment my_first_run

# Watch progress
evolve status --watch

# When complete, view best strategies
evolve best -k 5

# Export winning strategy
evolve export <strategy_id> -o ./best_strategy.py
```

### 2. With Configuration File

Create `config.yaml`:
```yaml
population_size: 200
archive_size: 20
elite_ratio: 0.15
exploration_ratio: 0.25

backtest:
  catalog_path: /media/sam/1TB/data/catalog
  instrument_id: BTCUSDT-PERP.BINANCE
  start_date: "2024-01-01"
  end_date: "2024-06-01"
  initial_capital: 100000

stop_conditions:
  target_fitness: 2.0  # Stop early if Calmar >= 2.0
```

```bash
evolve start --config config.yaml --seed momentum --experiment btc_v1
```

### 3. Resume Interrupted Run

```bash
# List experiments
evolve list

# Resume paused experiment
evolve resume btc_v1

# Resume and add more iterations
evolve resume btc_v1 --iterations 50
```

---

## Quick Start (Python API)

### Basic Usage

```python
import asyncio
from pathlib import Path

from scripts.alpha_evolve.controller import EvolutionController
from scripts.alpha_evolve.config import EvolutionConfig
from scripts.alpha_evolve.store import ProgramStore
from scripts.alpha_evolve.evaluator import StrategyEvaluator, BacktestConfig

# Configure backtest
backtest_config = BacktestConfig(
    catalog_path="/media/sam/1TB/data/catalog",
    instrument_id="BTCUSDT-PERP.BINANCE",
    start_date="2024-01-01",
    end_date="2024-06-01",
    initial_capital=100_000.0,
)

# Initialize components
config = EvolutionConfig()
store = ProgramStore("./evolve.db")
evaluator = StrategyEvaluator(backtest_config)

# Create controller
controller = EvolutionController(
    config=config,
    store=store,
    evaluator=evaluator,
)

# Progress callback
def on_progress(event):
    print(f"[{event.event_type}] Iteration {event.iteration}: {event.data}")

# Run evolution
async def main():
    result = await controller.run(
        seed_strategy="momentum",
        experiment="quickstart_test",
        iterations=10,
        on_progress=on_progress,
    )

    print(f"\nEvolution complete!")
    print(f"Best fitness: {result.best_strategy.metrics.calmar_ratio:.2f}")
    print(f"Iterations: {result.iterations_completed}")
    print(f"Success rate: {result.successful_mutations}/{result.total_mutations}")

asyncio.run(main())
```

### With Early Stop Condition

```python
from scripts.alpha_evolve.controller import StopCondition

stop_condition = StopCondition(
    max_iterations=100,
    target_fitness=2.5,        # Stop if Calmar >= 2.5
    max_time_seconds=3600,     # 1 hour timeout
    no_improvement_generations=10,  # Stagnation detection
)

result = await controller.run(
    seed_strategy="momentum",
    experiment="early_stop_test",
    iterations=100,
    stop_condition=stop_condition,
)
```

### Viewing Results

```python
# Get top strategies
top_strategies = store.top_k(k=5, metric="calmar", experiment="quickstart_test")

for i, strategy in enumerate(top_strategies):
    print(f"{i+1}. ID: {strategy.id[:8]}...")
    print(f"   Generation: {strategy.generation}")
    print(f"   Calmar: {strategy.metrics.calmar_ratio:.2f}")
    print(f"   Sharpe: {strategy.metrics.sharpe_ratio:.2f}")
    print()

# Get lineage of best strategy
best = top_strategies[0]
lineage = store.get_lineage(best.id)
print(f"Lineage ({len(lineage)} generations):")
for ancestor in lineage:
    print(f"  <- {ancestor.id[:8]}... (gen {ancestor.generation})")
```

---

## Common Workflows

### A/B Testing Different Seeds

```bash
# Test momentum seed
evolve start --seed momentum --experiment btc_momentum_v1 --iterations 50

# (Future) Test mean-reversion seed
evolve start --seed mean_reversion --experiment btc_meanrev_v1 --iterations 50

# Compare results
evolve best btc_momentum_v1 -k 1
evolve best btc_meanrev_v1 -k 1
```

### Long-Running Evolution with Checkpoints

```bash
# Start with conservative target
evolve start --seed momentum --experiment long_run --iterations 1000 --timeout 28800

# Check progress periodically
evolve status long_run

# If needed, stop and resume later
evolve stop long_run
# ... later ...
evolve resume long_run
```

---

## Troubleshooting

### No Improvement After Many Iterations

1. Check selection ratios - may need more exploration
2. Review mutation quality - check logs for syntax errors
3. Verify data quality - ensure no gaps in historical data

### High Mutation Failure Rate

1. Increase retry count in config
2. Review EVOLVE-BLOCK markers are correct
3. Check LLM is available (Claude API connectivity)

### Memory Issues During Evolution

1. Reduce `max_concurrent` in config
2. Shorten backtest date range
3. Monitor with `evolve status --watch`

---

## Next Steps

1. **Customize Seed Strategy**: Create variants in `templates/` folder
2. **Tune Selection Ratios**: Experiment with elite/exploit/explore balance
3. **Multiple Instruments**: Run parallel experiments on different assets
4. **Dashboard Integration**: Connect to spec-010 Grafana dashboard
