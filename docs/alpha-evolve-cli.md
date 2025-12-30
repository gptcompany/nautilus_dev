# Alpha-Evolve CLI

Command-line interface for evolutionary strategy optimization.

## Installation

The CLI is included in the nautilus_dev package. Activate the nightly environment:

```bash
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
```

## Quick Start

```bash
# Start evolution with momentum seed
evolve start --seed momentum --iterations 50 --experiment btc_v1

# Monitor progress
evolve status btc_v1

# View best strategies
evolve best btc_v1 -k 5

# Export winning strategy
evolve export <strategy_id> -o ./best_strategy.py
```

## Commands

### `evolve start`

Start a new evolution run.

```
evolve start [OPTIONS]

Options:
  --seed TEXT           Seed strategy name [required: "momentum"]
  --iterations INT      Number of iterations [default: 50]
  --experiment TEXT     Experiment name [default: auto-generated]
  --target-fitness FLOAT  Stop when fitness >= target
  --timeout INT         Max runtime in seconds
  -v, --verbose         Verbose output
```

**Examples:**

```bash
# Basic 50-iteration run
evolve start --seed momentum --iterations 50

# Named experiment with early stop
evolve start --seed momentum --experiment btc_v1 --target-fitness 2.5

# Long run with timeout
evolve start --seed momentum --iterations 200 --timeout 7200
```

### `evolve status`

Show evolution progress.

```
evolve status [OPTIONS] [EXPERIMENT]

Arguments:
  EXPERIMENT    Experiment name [optional]

Options:
  --json        Output as JSON
  --watch       Continuously update (1s interval)
```

**Output:**

```
Evolution Status: btc_v1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status:      RUNNING
Iteration:   42 / 50
Generation:  15
Best Fitness: 1.87 (Calmar)

Population:  127 strategies
Elapsed:     01:23:45
ETA:         00:19:30

Mutations:   45/50 (90% success)
Evaluations: 42/42 (100% success)
```

### `evolve best`

Display top strategies from hall-of-fame.

```
evolve best [OPTIONS] [EXPERIMENT]

Options:
  -k, --top-k INT     Number of strategies [default: 10]
  --metric TEXT       Sort by: calmar|sharpe|cagr [default: calmar]
  --json              Output as JSON
  --with-code         Include strategy code
```

**Output:**

```
Top 10 Strategies (by Calmar)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Rank  ID        Gen   Calmar   Sharpe   MaxDD    CAGR
────────────────────────────────────────────────────
 1    abc123     15    2.34     1.56    -12.3%   28.8%
 2    def456     14    2.18     1.42    -13.1%   28.5%
 3    ghi789     13    2.05     1.38    -14.2%   29.1%
```

### `evolve export`

Export strategy code to file.

```
evolve export [OPTIONS] STRATEGY_ID

Arguments:
  STRATEGY_ID    Strategy UUID [required]

Options:
  -o, --output PATH   Output file [default: ./<id>.py]
  --with-lineage      Include parent chain as comments
```

**Example:**

```bash
evolve export abc123 -o ./best_strategy.py --with-lineage
```

### `evolve stop`

Gracefully stop running evolution.

```
evolve stop [OPTIONS] [EXPERIMENT]

Options:
  --force       Immediate stop (don't wait for iteration)
```

### `evolve list`

List all experiments.

```
evolve list [OPTIONS]

Options:
  --json        Output as JSON
  --active      Show only running experiments
```

**Output:**

```
Experiments
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Name           Status      Iter   Best     Created
─────────────────────────────────────────────────
btc_v1         running     42/50  1.87     2025-12-27 10:30
btc_v0         completed   50/50  1.54     2025-12-26 15:20
eth_momentum   paused      20/100 0.92     2025-12-25 09:00
```

### `evolve resume`

Resume a paused evolution.

```
evolve resume [OPTIONS] EXPERIMENT

Arguments:
  EXPERIMENT    Experiment name [required]

Options:
  --iterations INT    Additional iterations [extends total]
```

**Examples:**

```bash
# Resume from checkpoint
evolve resume btc_v1

# Resume and add 50 more iterations
evolve resume btc_v1 --iterations 50
```

## Configuration

Create `config.yaml` for custom settings:

```yaml
# Evolution parameters
population_size: 500
archive_size: 50
elite_ratio: 0.1
exploration_ratio: 0.2
max_concurrent: 2

# Backtest configuration
backtest:
  catalog_path: /media/sam/1TB/data/catalog
  instrument_id: BTCUSDT-PERP.BINANCE
  start_date: "2024-01-01"
  end_date: "2024-06-01"
  initial_capital: 100000

# Stop conditions
stop_conditions:
  max_iterations: 50
  target_fitness: 2.5
  max_time_seconds: 7200
```

Use with:

```bash
evolve --config config.yaml start --seed momentum
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid configuration |
| 3 | Experiment not found |
| 4 | Strategy not found |
| 5 | Store error |
| 130 | User interrupt (Ctrl+C) |

## Benchmarking

Run success criteria benchmarks:

```bash
# Quick CLI benchmark only
python -m scripts.alpha_evolve.benchmark --quick

# Full benchmark (5 iterations)
python -m scripts.alpha_evolve.benchmark --iterations 5

# Extended benchmark
python -m scripts.alpha_evolve.benchmark --iterations 20
```

## Python API

For programmatic usage:

```python
import asyncio
from scripts.alpha_evolve.controller import EvolutionController, StopCondition
from scripts.alpha_evolve.config import EvolutionConfig
from scripts.alpha_evolve.store import ProgramStore
from scripts.alpha_evolve.evaluator import StrategyEvaluator, BacktestConfig
from scripts.alpha_evolve.mutator import LLMMutator

# Initialize
config = EvolutionConfig()
store = ProgramStore("./evolve.db")
evaluator = StrategyEvaluator(BacktestConfig(...))
controller = EvolutionController(config, store, evaluator, LLMMutator())

# Run evolution
async def main():
    result = await controller.run(
        seed_strategy="momentum",
        experiment="my_experiment",
        iterations=50,
        stop_condition=StopCondition(target_fitness=2.0),
        on_progress=lambda e: print(e),
    )
    print(f"Best: {result.best_strategy.metrics.calmar_ratio}")

asyncio.run(main())
```

## See Also

- [Spec 009: Alpha-Evolve Controller](../specs/009-alpha-evolve-controller/spec.md)
- [Quickstart Guide](../specs/009-alpha-evolve-controller/quickstart.md)
