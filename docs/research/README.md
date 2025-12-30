# Research Documentation

This directory contains documentation and synced data from the academic research pipeline.

## Contents

### Mapping Tables

- **[indicator_mapping.md](indicator_mapping.md)** - Maps academic paper indicator terminology to NautilusTrader Rust implementations
- **[order_mapping.md](order_mapping.md)** - Maps academic paper order types to NautilusTrader order enums

### Synced Data

- **strategies.json** - Strategy entities synced from `academic_research/memory.json`

## Usage

### Finding NautilusTrader Indicators

When converting a paper's indicator to NautilusTrader:

1. Look up the indicator in `indicator_mapping.md`
2. Use the NautilusTrader class name and module
3. If not found, check the "Custom Indicators Needed" section

Example:
```
Paper says: "20-day exponential moving average"
Mapping: ExponentialMovingAverage from nautilus_trader.indicators.average.ema
Usage: self.ema = ExponentialMovingAverage(period=20)
```

### Finding Order Types

When converting a paper's order description to NautilusTrader:

1. Look up the order type in `order_mapping.md`
2. Use the appropriate `OrderType` enum
3. Check the exchange support matrix for availability

Example:
```
Paper says: "stop loss at 2%"
Mapping: OrderType.STOP_MARKET with reduce_only=True
```

### Syncing Strategy Data

To sync strategy entities from academic_research:

```bash
# Normal sync (skips if fresh)
python scripts/sync_research.py

# Preview changes
python scripts/sync_research.py --dry-run

# Force sync
python scripts/sync_research.py --force
```

The sync script:
- Extracts `strategy__` entities from `memory.json`
- Writes to `docs/research/strategies.json`
- Includes staleness detection (24-hour threshold)
- Preserves sync timestamps

## Related Resources

### In nautilus_dev

- `.claude/agents/strategy-researcher.md` - Agent for paper analysis
- `.claude/skills/paper-to-strategy/` - Skill for spec generation
- `scripts/sync_research.py` - Sync script

### In academic_research

- `memory.json` - Knowledge graph with strategy entities
- `docs/entity_schemas.md` - Entity schema definitions
- `.claude/skills/research-query-workflow/` - Research workflow

## Workflow

```
1. Research paper in academic_research
   └─> Creates source__ and strategy__ entities in memory.json

2. Run sync_research.py
   └─> Copies strategy__ entities to strategies.json

3. Use strategy-researcher agent
   └─> Reads strategies.json for existing research
   └─> Generates spec.md using paper-to-strategy skill

4. Implement with alpha-evolve
   └─> Multiple implementation variants
   └─> Backtest evaluation
   └─> Best implementation selection
```

## Version Info

- **Created**: 2025-12-29
- **Spec**: 022-academic-research-pipeline
- **NautilusTrader**: nightly >= 1.222.0
