# Data Model: Alpha-Evolve Dashboard

**Created**: 2025-12-28
**Spec Reference**: `specs/010-alpha-evolve-dashboard/spec.md`

## Entities

### EvolutionMetrics

Time-series record of strategy evolution metrics, stored in QuestDB for Grafana visualization.

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| timestamp | TIMESTAMP | When metric was recorded | 2025-12-28T10:30:00Z |
| program_id | SYMBOL | Unique strategy ID (UUID) | "a1b2c3d4-..." |
| experiment | SYMBOL | Experiment name for filtering | "btc_momentum_v1" |
| generation | INT | Generation number (0 = seed) | 5 |
| parent_id | SYMBOL | Parent strategy ID (null for seeds) | "e5f6g7h8-..." |
| sharpe | DOUBLE | Sharpe ratio | 1.85 |
| calmar | DOUBLE | Calmar ratio (primary fitness) | 2.34 |
| max_dd | DOUBLE | Maximum drawdown (percentage) | 15.2 |
| cagr | DOUBLE | Compound annual growth rate | 0.45 |
| total_return | DOUBLE | Total return percentage | 0.82 |
| trade_count | INT | Number of trades executed | 127 |
| win_rate | DOUBLE | Win rate (0-1) | 0.58 |
| mutation_outcome | SYMBOL | Mutation result category | "success" |
| mutation_latency_ms | DOUBLE | Mutation API call duration | 2340.5 |

**Mutation Outcome Values**:
- `success`: Mutation produced valid, evaluated code
- `syntax_error`: Mutation produced code with syntax errors
- `runtime_error`: Mutation produced code that crashed during evaluation
- `timeout`: Mutation API call timed out
- `seed`: Initial seed strategy (no mutation)

### Relationships

```
┌──────────────────────────┐
│     EvolutionMetrics     │
├──────────────────────────┤
│ timestamp (PK)           │
│ program_id (index)       │──────┐
│ experiment (index)       │      │
│ generation               │      │
│ parent_id (FK)           │──────┤ self-reference (lineage)
│ ...fitness metrics...    │      │
│ ...mutation tracking...  │      │
└──────────────────────────┘      │
           ▲                      │
           └──────────────────────┘
```

## State Transitions

### Program Lifecycle

```
                        ┌─────────────────────┐
                        │      SEED           │
                        │  generation = 0     │
                        │  parent_id = null   │
                        └─────────┬───────────┘
                                  │
                                  ▼ mutation
              ┌───────────────────────────────────────┐
              │                                       │
              ▼                                       ▼
    ┌─────────────────────┐               ┌─────────────────────┐
    │   MUTATION_SUCCESS  │               │   MUTATION_FAILED   │
    │  outcome = success  │               │  outcome = error    │
    └─────────┬───────────┘               │  no fitness metrics │
              │                           └─────────────────────┘
              ▼ evaluation
              │
    ┌─────────┴───────────┐
    │                     │
    ▼                     ▼
┌────────────┐    ┌────────────────┐
│  EVALUATED │    │  EVAL_FAILED   │
│ has metrics│    │  runtime_error │
└────────────┘    └────────────────┘
```

### Mutation Outcome State Machine

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │ request mutation
       ▼
┌──────────────────┐
│ MUTATION_PENDING │
└────────┬─────────┘
         │
    ┌────┼────┬────────┐
    │    │    │        │
    ▼    │    ▼        ▼
success  │  syntax   timeout
    │    │  error      │
    │    │    │        │
    │    ▼    │        │
    │ runtime │        │
    │  error  │        │
    │    │    │        │
    ▼    ▼    ▼        ▼
┌──────────────────────────┐
│    OUTCOME_RECORDED      │
│  (written to QuestDB)    │
└──────────────────────────┘
```

## Validation Rules

### EvolutionMetrics

| Field | Validation |
|-------|------------|
| timestamp | Required, must be UTC |
| program_id | Required, valid UUID format |
| experiment | Required, alphanumeric with underscores |
| generation | >= 0 |
| parent_id | Optional, valid UUID if present |
| sharpe | Can be negative |
| calmar | Can be negative |
| max_dd | 0-100 (percentage) |
| cagr | Can be negative |
| total_return | Can be negative |
| trade_count | >= 0 |
| win_rate | 0-1 (ratio) |
| mutation_outcome | One of: success, syntax_error, runtime_error, timeout, seed |
| mutation_latency_ms | >= 0 |

## Query Patterns

### 1. Fitness Progress (User Story 1)

```sql
-- Best fitness per generation over time
SELECT timestamp, max(calmar) as best_fitness
FROM evolution_metrics
WHERE experiment = '${experiment}'
  AND mutation_outcome = 'success'
  AND timestamp > now() - interval '7d'
SAMPLE BY 1h;
```

### 2. Top Strategies (User Story 2)

```sql
-- Top 10 strategies by calmar ratio
SELECT program_id, generation, sharpe, calmar, max_dd, cagr
FROM evolution_metrics
WHERE experiment = '${experiment}'
  AND mutation_outcome = 'success'
  AND timestamp > now() - interval '1h'
LATEST BY program_id
ORDER BY calmar DESC
LIMIT 10;
```

### 3. Population Stats (User Story 3)

```sql
-- Population-level statistics
SELECT
    count() as population,
    max(generation) as max_generation,
    avg(calmar) as avg_fitness,
    min(calmar) as min_fitness,
    max(calmar) as max_fitness,
    stddev(calmar) as std_fitness
FROM evolution_metrics
WHERE experiment = '${experiment}'
  AND mutation_outcome = 'success'
  AND timestamp > now() - interval '1h'
LATEST BY program_id;
```

### 4. Mutation Success Rate (User Story 4)

```sql
-- Mutation outcome distribution
SELECT mutation_outcome, count() as count
FROM evolution_metrics
WHERE experiment = '${experiment}'
  AND timestamp > now() - interval '24h'
GROUP BY mutation_outcome;
```

### 5. Fitness Distribution (Histogram)

```sql
-- Fitness distribution for histogram
SELECT calmar
FROM evolution_metrics
WHERE experiment = '${experiment}'
  AND mutation_outcome = 'success'
  AND timestamp > now() - interval '1h'
LATEST BY program_id;
```
