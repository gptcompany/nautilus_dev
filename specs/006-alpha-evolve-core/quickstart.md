# Quickstart: Alpha-Evolve Core Infrastructure

## Installation

```bash
# No additional dependencies required beyond project base
# Uses: sqlite3, re, ast, pydantic, pyyaml (all available)
```

## Basic Usage

### 1. Patching System

```python
from scripts.alpha_evolve.patching import apply_patch, validate_syntax

# Strategy code with EVOLVE-BLOCK markers
parent_code = '''
from nautilus_trader.trading.strategy import Strategy

class MyStrategy(Strategy):
    def on_bar(self, bar):
        # === EVOLVE-BLOCK: decision_logic ===
        if bar.close > bar.open:
            self.buy()
        # === END EVOLVE-BLOCK ===
'''

# Apply mutation
mutation = {"blocks": {"decision_logic": "if self.ema.value > bar.close:\n    self.sell()"}}
child_code = apply_patch(parent_code, mutation)

# Validate before saving
valid, error = validate_syntax(child_code)
if valid:
    print("Mutation successful!")
```

### 2. Hall-of-Fame Store

```python
from scripts.alpha_evolve.store import ProgramStore, FitnessMetrics

# Initialize store
store = ProgramStore(
    db_path="./alpha_evolve.db",
    population_size=500,
    archive_size=50,
)

# Insert seed strategy
seed_id = store.insert(
    code=parent_code,
    experiment="btc_momentum_v1",
)

# After evaluation, update metrics
store.update_metrics(seed_id, FitnessMetrics(
    sharpe_ratio=1.5,
    calmar_ratio=2.1,
    max_drawdown=-0.15,
    cagr=0.35,
    total_return=0.42,
    trade_count=150,
))

# Insert child with lineage
child_id = store.insert(
    code=child_code,
    parent_id=seed_id,
    experiment="btc_momentum_v1",
)

# Get top performers
top_10 = store.top_k(k=10, metric="calmar")
for p in top_10:
    print(f"{p.id}: Calmar={p.metrics.calmar_ratio:.2f}")

# Sample parent for next mutation
parent = store.sample(strategy="exploit")
print(f"Selected parent: {parent.id}")
```

### 3. Configuration

```python
from scripts.alpha_evolve.config import EvolutionConfig

# Load from YAML (with env var overrides)
config = EvolutionConfig.load(Path("scripts/alpha_evolve/config.yaml"))

print(f"Population size: {config.population_size}")
print(f"Archive size: {config.archive_size}")
print(f"Elite ratio: {config.elite_ratio}")

# Override via environment
# export EVOLVE_POPULATION_SIZE=1000
# export EVOLVE_ELITE_RATIO=0.15
```

### 4. config.yaml Example

```yaml
# scripts/alpha_evolve/config.yaml
evolution:
  population_size: 500
  archive_size: 50
  elite_ratio: 0.1
  exploration_ratio: 0.2
  max_concurrent: 2
```

## Directory Structure

```
scripts/alpha_evolve/
├── __init__.py
├── patching.py      # EVOLVE-BLOCK mutation
├── store.py         # SQLite persistence
├── config.py        # Configuration loading
└── config.yaml      # Default parameters

tests/alpha_evolve/
├── test_patching.py
├── test_store.py
└── test_config.py
```

## Quick Verification

```bash
# Run tests
cd /media/sam/1TB/nautilus_dev
uv run pytest tests/alpha_evolve/ -v

# Expected output:
# tests/alpha_evolve/test_patching.py::test_block_replacement PASSED
# tests/alpha_evolve/test_patching.py::test_indent_preservation PASSED
# tests/alpha_evolve/test_store.py::test_insert_and_get PASSED
# tests/alpha_evolve/test_store.py::test_top_k PASSED
# tests/alpha_evolve/test_store.py::test_sample_strategies PASSED
# tests/alpha_evolve/test_store.py::test_prune PASSED
# tests/alpha_evolve/test_config.py::test_load_defaults PASSED
# tests/alpha_evolve/test_config.py::test_validation PASSED
```
