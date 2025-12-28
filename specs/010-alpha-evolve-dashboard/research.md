# Research: Alpha-Evolve Dashboard Data Architecture

**Created**: 2025-12-28
**Status**: Resolved

## Research Questions

### 1. SQLite vs QuestDB: Which data source for Grafana?

**Decision**: Use QuestDB Sync

**Rationale**:
1. All existing dashboards (health.json, trading.json) use QuestDB
2. QuestDB provides `SAMPLE BY` and `LATEST BY` for efficient time-series queries
3. Existing `MetricsClient` provides battle-tested write path
4. No additional Docker volume mounts or plugins required
5. Consistent alerting capabilities across all dashboards

**Alternatives Considered**:

| Approach | Pros | Cons |
|----------|------|------|
| SQLite direct via `frser-sqlite-datasource` | No data duplication, simpler | Requires plugin, Docker mount, no time-series optimization |
| QuestDB Sync | Consistent stack, SAMPLE BY, no new plugins | Data duplication between SQLite and QuestDB |

### 2. QuestDB Table Schema

```sql
-- Evolution metrics time-series table
CREATE TABLE IF NOT EXISTS evolution_metrics (
    timestamp TIMESTAMP,
    program_id SYMBOL,         -- UUID, indexed for filtering
    experiment SYMBOL,         -- Low cardinality, filterable
    generation INT,
    parent_id SYMBOL,

    -- Fitness metrics (match SQLite store.py)
    sharpe DOUBLE,
    calmar DOUBLE,
    max_dd DOUBLE,
    cagr DOUBLE,
    total_return DOUBLE,
    trade_count INT,
    win_rate DOUBLE,

    -- Mutation tracking (for mutation success panel)
    mutation_outcome SYMBOL,   -- 'success', 'syntax_error', 'runtime_error', 'timeout'
    mutation_latency_ms DOUBLE
) TIMESTAMP(timestamp)
PARTITION BY DAY;
```

### 3. Sync Approach

**Decision**: Event-driven sync after evaluation

Sync metrics to QuestDB after each strategy evaluation completes. This:
- Minimizes latency (real-time dashboard updates)
- Is lightweight (only write when data changes)
- Reuses existing `MetricsClient` pattern

### 4. Sample Queries for Dashboard Panels

```sql
-- Fitness Progress (User Story 1)
SELECT timestamp, max(calmar) as best_fitness
FROM evolution_metrics
WHERE experiment = '${experiment}'
  AND timestamp > now() - interval '7d'
SAMPLE BY 1h;

-- Top Strategies (User Story 2)
SELECT program_id, generation, sharpe, calmar, max_dd, cagr
FROM evolution_metrics
WHERE experiment = '${experiment}'
  AND timestamp > now() - interval '1h'
LATEST BY program_id
ORDER BY calmar DESC
LIMIT 10;

-- Population Stats (User Story 3)
SELECT
    count() as population,
    max(generation) as max_generation,
    avg(calmar) as avg_fitness,
    min(calmar) as min_fitness,
    max(calmar) as max_fitness
FROM evolution_metrics
WHERE experiment = '${experiment}'
  AND timestamp > now() - interval '1h'
LATEST BY program_id;

-- Mutation Success Rate (User Story 4)
SELECT mutation_outcome, count() as count
FROM evolution_metrics
WHERE experiment = '${experiment}'
  AND timestamp > now() - interval '24h'
GROUP BY mutation_outcome;
```

## Edge Case Resolutions

| Edge Case | Resolution |
|-----------|------------|
| Empty dashboard (no evolution data) | Show "No data" with friendly message |
| Very large populations (10,000+) | QuestDB handles via DAY partitioning |
| QuestDB unavailable | Dashboard shows error; evolution continues (SQLite is primary) |
| Timezone differences | Use UTC timestamps, Grafana converts to user timezone |
| Dashboard refresh during write | QuestDB handles concurrent reads/writes |

## Implementation Files

| File | Purpose |
|------|---------|
| `monitoring/models.py` | Add `EvolutionMetrics` Pydantic model |
| `monitoring/schemas/evolution_metrics.sql` | QuestDB table definition |
| `scripts/alpha_evolve/metrics_publisher.py` | Sync hook for QuestDB writes |
| `monitoring/grafana/dashboards/evolution.json` | Dashboard JSON |
