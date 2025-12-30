# Data Model: Alpha-Evolve Core Infrastructure

**Created**: 2025-12-27
**Status**: Complete

## Entities

### Program

Represents an evolved trading strategy with code, lineage, and fitness metrics.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| code | TEXT | NOT NULL | Full strategy Python code |
| parent_id | UUID | FK → programs.id, nullable | Parent strategy (null for seeds) |
| generation | INT | DEFAULT 0 | Evolution generation number |
| experiment | TEXT | nullable | Experiment name for grouping |
| sharpe | FLOAT | nullable | Sharpe ratio |
| calmar | FLOAT | nullable | Calmar ratio (primary fitness) |
| max_dd | FLOAT | nullable | Maximum drawdown (negative) |
| cagr | FLOAT | nullable | Compound annual growth rate |
| total_return | FLOAT | nullable | Total return percentage |
| trade_count | INT | nullable | Number of trades executed |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp (Unix) |

**Relationships**:
- Self-referential: `parent_id` → `programs.id`
- Lineage chain can be traversed via recursive query

**Indexes**:
- `idx_calmar`: DESC on calmar for top_k queries
- `idx_sharpe`: DESC on sharpe for alternative ranking
- `idx_experiment`: For experiment filtering

---

### FitnessMetrics

Value object containing strategy performance measurements.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| sharpe_ratio | FLOAT | required | Risk-adjusted return |
| calmar_ratio | FLOAT | required | Return / Max Drawdown |
| max_drawdown | FLOAT | required | Worst peak-to-trough (negative) |
| cagr | FLOAT | required | Annualized return |
| total_return | FLOAT | required | Cumulative return |
| trade_count | INT | optional | Number of trades |
| win_rate | FLOAT | optional | Winning trade percentage |

**Note**: This is a Python dataclass, not a database table. Metrics are stored flat in Program table.

---

### EvolutionConfig

Configuration parameters for evolution process.

| Field | Type | Constraints | Default | Description |
|-------|------|-------------|---------|-------------|
| population_size | INT | ≥ 10 | 500 | Max strategies in population |
| archive_size | INT | ≥ 1 | 50 | Protected top performers |
| elite_ratio | FLOAT | 0.0-1.0 | 0.1 | Elite selection probability |
| exploration_ratio | FLOAT | 0.0-1.0 | 0.2 | Random selection probability |
| max_concurrent | INT | ≥ 1 | 2 | Max parallel evaluations |

**Validation Rules**:
- `elite_ratio + exploration_ratio ≤ 1.0`
- `archive_size < population_size`

---

## State Transitions

### Program Lifecycle

```
                    ┌─────────────┐
                    │   CREATED   │
                    │ (no metrics)│
                    └──────┬──────┘
                           │
                    evaluate()
                           │
                           ▼
              ┌────────────────────────┐
              │       EVALUATED        │
              │ (metrics populated)    │
              └────────────┬───────────┘
                           │
                    prune() if excess
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        ┌─────────┐             ┌────────────┐
        │ PRUNED  │             │  ARCHIVED  │
        │(deleted)│             │ (protected)│
        └─────────┘             └────────────┘
```

---

## Query Patterns

### top_k(k, metric)

```sql
SELECT * FROM programs
WHERE calmar IS NOT NULL
ORDER BY calmar DESC
LIMIT ?
```

### sample(strategy)

**Elite (10%)**:
```sql
SELECT * FROM programs
WHERE calmar IS NOT NULL
ORDER BY calmar DESC
LIMIT (SELECT COUNT(*) * 0.1 FROM programs)
-- Then random.choice() in Python
```

**Explore (random)**:
```sql
SELECT * FROM programs
ORDER BY RANDOM()
LIMIT 1
```

**Exploit (weighted)**:
```python
# In Python: fitness-proportional selection
programs = get_all_evaluated()
weights = [max(0, p.calmar) for p in programs]
return random.choices(programs, weights=weights)[0]
```

### get_lineage(id)

```sql
WITH RECURSIVE lineage AS (
    SELECT * FROM programs WHERE id = ?
    UNION ALL
    SELECT p.* FROM programs p
    INNER JOIN lineage l ON p.id = l.parent_id
)
SELECT * FROM lineage
```
