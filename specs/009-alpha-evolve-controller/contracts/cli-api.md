# CLI API Contract: Alpha-Evolve

**Feature Branch**: `009-alpha-evolve-controller`
**Created**: 2025-12-27
**Framework**: Click

## Command Structure

```
evolve [OPTIONS] COMMAND [ARGS]...

Options:
  --config PATH       Path to config.yaml (optional)
  --db PATH           Path to SQLite database (default: ./evolve.db)
  --help              Show this message and exit

Commands:
  start   Start evolution run
  status  Show evolution progress
  best    Display top strategies
  export  Export strategy to file
  stop    Stop running evolution
  list    List experiments
  resume  Resume paused evolution
```

---

## Commands

### `evolve start`

Start a new evolution run.

```
evolve start [OPTIONS]

Options:
  --seed TEXT           Seed strategy name [required: "momentum"]
  --iterations INT      Number of iterations [default: 50]
  --experiment TEXT     Experiment name [default: auto-generated timestamp]
  --target-fitness FLOAT  Stop when fitness >= target [optional]
  --timeout INT         Max runtime in seconds [optional]
  -v, --verbose         Verbose output
```

**Examples**:
```bash
# Basic usage
evolve start --seed momentum --iterations 100

# Named experiment with target
evolve start --seed momentum --experiment btc_v1 --target-fitness 2.5

# Verbose with timeout
evolve start --seed momentum -v --timeout 7200
```

**Exit Codes**:
- 0: Success (completed all iterations or hit target)
- 1: General error
- 2: Invalid configuration
- 130: Interrupted (Ctrl+C)

---

### `evolve status`

Show current evolution progress.

```
evolve status [OPTIONS] [EXPERIMENT]

Arguments:
  EXPERIMENT    Experiment name [optional, default: active experiment]

Options:
  --json        Output as JSON
  --watch       Continuously update (1s interval)
```

**Example Output** (human-readable):
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

**Example Output** (JSON):
```json
{
  "experiment": "btc_v1",
  "status": "running",
  "iteration": 42,
  "max_iterations": 50,
  "generation": 15,
  "best_fitness": 1.87,
  "best_strategy_id": "abc123",
  "population_size": 127,
  "elapsed_seconds": 5025,
  "eta_seconds": 1170,
  "mutations_attempted": 50,
  "mutations_successful": 45,
  "evaluations_completed": 42,
  "evaluations_failed": 0
}
```

---

### `evolve best`

Display top strategies from hall-of-fame.

```
evolve best [OPTIONS] [EXPERIMENT]

Arguments:
  EXPERIMENT    Experiment name [optional, default: all]

Options:
  -k, --top-k INT     Number of strategies to show [default: 10]
  --metric TEXT       Sort metric: calmar|sharpe|cagr [default: calmar]
  --json              Output as JSON
  --with-code         Include strategy code in output
```

**Example Output**:
```
Top 10 Strategies (by Calmar)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Rank  ID        Gen   Calmar   Sharpe   MaxDD    CAGR
────────────────────────────────────────────────────
 1    abc123     15    2.34     1.56    -12.3%   28.8%
 2    def456     14    2.18     1.42    -13.1%   28.5%
 3    ghi789     13    2.05     1.38    -14.2%   29.1%
...
```

---

### `evolve export`

Export strategy code to file.

```
evolve export [OPTIONS] STRATEGY_ID

Arguments:
  STRATEGY_ID    Strategy UUID [required]

Options:
  -o, --output PATH   Output file path [default: ./<id>.py]
  --with-lineage      Include parent chain as comments
```

**Example**:
```bash
evolve export abc123 -o ./best_strategy.py --with-lineage
```

**Output File**:
```python
"""
Evolved Strategy: abc123
Generation: 15
Parent: def456
Fitness: Calmar=2.34, Sharpe=1.56

Lineage:
  <- def456 (gen 14, calmar=2.18)
  <- ghi789 (gen 13, calmar=2.05)
  <- seed_momentum (gen 0)
"""

# [Full strategy code here]
```

---

### `evolve stop`

Gracefully stop running evolution.

```
evolve stop [OPTIONS] [EXPERIMENT]

Arguments:
  EXPERIMENT    Experiment to stop [optional, default: active]

Options:
  --force       Immediate stop (don't wait for current iteration)
```

**Behavior**:
1. Sets status to PAUSED
2. Completes current iteration (unless --force)
3. Persists state for resume
4. Returns immediately

---

### `evolve list`

List all experiments with summary stats.

```
evolve list [OPTIONS]

Options:
  --json        Output as JSON
  --active      Show only active experiments
```

**Example Output**:
```
Experiments
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Name           Status      Iter   Best     Created
─────────────────────────────────────────────────
btc_v1         running     42/50  1.87     2025-12-27 10:30
btc_v0         completed   50/50  1.54     2025-12-26 15:20
eth_momentum   paused      20/100 0.92     2025-12-25 09:00
```

---

### `evolve resume`

Resume a paused evolution.

```
evolve resume [OPTIONS] EXPERIMENT

Arguments:
  EXPERIMENT    Experiment name to resume [required]

Options:
  --iterations INT    Additional iterations [optional, extends total]
```

**Example**:
```bash
# Resume from where it left off
evolve resume btc_v1

# Resume and add 50 more iterations
evolve resume btc_v1 --iterations 50
```

---

## Configuration File

Optional `config.yaml`:

```yaml
# Evolution parameters
population_size: 500
archive_size: 50
elite_ratio: 0.1
exploration_ratio: 0.2
max_concurrent: 2

# Backtest configuration
backtest:
  catalog_path: ./data/catalog
  instrument_id: BTCUSDT-PERP.BINANCE
  start_date: "2024-01-01"
  end_date: "2024-06-01"
  initial_capital: 100000
  venue: BINANCE

# Stop conditions
stop_conditions:
  max_iterations: 50
  target_fitness: 2.5
  max_time_seconds: 7200
```

---

## Python API

For programmatic usage:

```python
from scripts.alpha_evolve.controller import EvolutionController
from scripts.alpha_evolve.config import EvolutionConfig
from scripts.alpha_evolve.store import ProgramStore
from scripts.alpha_evolve.evaluator import StrategyEvaluator, BacktestConfig

# Initialize components
config = EvolutionConfig.load(Path("config.yaml"))
store = ProgramStore("evolve.db", population_size=config.population_size)
evaluator = StrategyEvaluator(backtest_config)

# Create controller
controller = EvolutionController(
    config=config,
    store=store,
    evaluator=evaluator,
)

# Run evolution
async def main():
    await controller.run(
        seed_strategy="momentum",
        experiment="btc_v1",
        iterations=50,
        on_progress=lambda e: print(e),
    )

asyncio.run(main())
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid configuration |
| 3 | Experiment not found |
| 4 | Strategy not found |
| 5 | Store error |
| 130 | User interrupt (SIGINT) |
