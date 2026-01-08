# ADR-002: Data Storage Strategy

## Status

**Accepted**

## Date

2025-01-08

## Context

Trading systems require efficient storage for:
- Historical OHLCV bars (billions of rows)
- Order book snapshots
- Trade executions
- Performance metrics

Need fast writes, fast time-range queries, reasonable compression.

## Decision

Use a **hybrid storage approach**:

| Data Type | Storage | Reason |
|-----------|---------|--------|
| Historical bars | Parquet files | Columnar, compressed, fast reads |
| Trade catalog | NautilusTrader ParquetCatalog | Native integration |
| Real-time metrics | QuestDB | Time-series optimized, SQL |
| Research/analysis | DuckDB | Fast analytics, in-process |
| Session state | Redis | Fast KV, pub/sub |

## Consequences

### Positive

- Each tool optimized for its use case
- Parquet: 10x compression, columnar queries
- QuestDB: Millions of writes/sec for metrics
- DuckDB: Zero-copy Parquet reads
- Redis: Microsecond latency for state

### Negative

- Multiple systems to manage
- Data sync complexity
- Learning curve for each tool

### Neutral

- Docker Compose manages services
- Most queries are simple time-range

## Alternatives Considered

### PostgreSQL for Everything

Simple but poor performance for time-series at scale.

### InfluxDB

Good for metrics but query language less flexible than SQL.

### TimescaleDB

Good but heavier resource usage than QuestDB.

## References

- [QuestDB Docs](https://questdb.io/docs/)
- [DuckDB Parquet](https://duckdb.org/docs/data/parquet)
- Spec 005: Grafana/QuestDB Monitoring
