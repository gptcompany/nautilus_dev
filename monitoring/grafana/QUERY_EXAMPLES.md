# QuestDB Query Examples for Grafana

## Overview
These query examples can be used directly in Grafana dashboards with the QuestDB data source.

## Available Tables

All tables use `timestamp` as the designated timestamp column for time-series queries.

| Table | Purpose | Timestamp Column |
|-------|---------|------------------|
| trading_metrics | Trading performance data | timestamp |
| pipeline_metrics | Data pipeline statistics | timestamp |
| exchange_status | Exchange connection health | timestamp |
| daemon_metrics | Background daemon metrics | timestamp |

## Basic Query Patterns

### Time-Series Query
```sql
SELECT
    timestamp,
    metric_name,
    metric_value
FROM trading_metrics
WHERE timestamp > now() - 1h
ORDER BY timestamp DESC;
```

### Aggregated Metrics (1-minute intervals)
```sql
SELECT
    timestamp,
    avg(metric_value) as avg_value,
    max(metric_value) as max_value,
    min(metric_value) as min_value
FROM trading_metrics
WHERE timestamp > now() - 24h
SAMPLE BY 1m;
```

### Latest Values
```sql
SELECT
    metric_name,
    metric_value,
    timestamp
FROM trading_metrics
LATEST ON timestamp PARTITION BY metric_name;
```

## Grafana-Specific Queries

### Using Time Range Variables
Grafana provides `$__timeFrom` and `$__timeTo` variables:
```sql
SELECT
    timestamp,
    metric_value
FROM trading_metrics
WHERE timestamp BETWEEN $__timeFrom AND $__timeTo
ORDER BY timestamp;
```

### Using Dashboard Variables
If you create a variable `$metric` in Grafana:
```sql
SELECT
    timestamp,
    metric_value
FROM trading_metrics
WHERE metric_name = '$metric'
AND timestamp > now() - 1h;
```

## Example Dashboard Queries

### 1. Trading Performance Over Time
```sql
SELECT
    timestamp,
    sum(pnl) as total_pnl,
    avg(fill_price) as avg_price
FROM trading_metrics
WHERE timestamp > now() - 24h
SAMPLE BY 5m;
```

### 2. Exchange Health Status
```sql
SELECT
    timestamp,
    exchange_name,
    CASE
        WHEN status = 'connected' THEN 1
        ELSE 0
    END as is_connected
FROM exchange_status
WHERE timestamp > now() - 1h
LATEST ON timestamp PARTITION BY exchange_name;
```

### 3. Pipeline Throughput
```sql
SELECT
    timestamp,
    sum(messages_processed) as total_processed,
    avg(processing_time_ms) as avg_latency
FROM pipeline_metrics
WHERE timestamp > now() - 6h
SAMPLE BY 10m;
```

### 4. Daemon Memory Usage
```sql
SELECT
    timestamp,
    daemon_name,
    memory_mb
FROM daemon_metrics
WHERE timestamp > now() - 30m
ORDER BY timestamp DESC;
```

## Advanced Queries

### Moving Average
```sql
SELECT
    timestamp,
    metric_value,
    avg(metric_value) OVER (ORDER BY timestamp ROWS BETWEEN 10 PRECEDING AND CURRENT ROW) as moving_avg
FROM trading_metrics
WHERE metric_name = 'price'
AND timestamp > now() - 1h;
```

### Percentiles
```sql
SELECT
    timestamp,
    approx_percentile(latency_ms, 0.50) as p50,
    approx_percentile(latency_ms, 0.95) as p95,
    approx_percentile(latency_ms, 0.99) as p99
FROM pipeline_metrics
WHERE timestamp > now() - 1h
SAMPLE BY 1m;
```

### Count Events by Type
```sql
SELECT
    timestamp,
    event_type,
    count() as event_count
FROM trading_metrics
WHERE timestamp > now() - 24h
SAMPLE BY 1h
ALIGN TO CALENDAR;
```

## Grafana Panel Types

### Time Series Panel
Best for continuous metrics:
```sql
SELECT
    timestamp,
    metric_value
FROM trading_metrics
WHERE metric_name = 'pnl'
AND timestamp > now() - 1d;
```

### Stat Panel (Single Value)
For current/latest values:
```sql
SELECT
    metric_value
FROM trading_metrics
WHERE metric_name = 'total_pnl'
LATEST ON timestamp PARTITION BY metric_name;
```

### Table Panel
For multiple dimensions:
```sql
SELECT
    metric_name,
    avg(metric_value) as avg,
    max(metric_value) as max,
    min(metric_value) as min
FROM trading_metrics
WHERE timestamp > now() - 1h
GROUP BY metric_name;
```

### Bar Chart
For categorical comparisons:
```sql
SELECT
    exchange_name,
    sum(volume) as total_volume
FROM trading_metrics
WHERE timestamp > now() - 1h
GROUP BY exchange_name
ORDER BY total_volume DESC;
```

## Performance Tips

### 1. Use Designated Timestamp
Always filter on the `timestamp` column for optimal performance:
```sql
-- Good
WHERE timestamp > now() - 1h

-- Avoid
WHERE created_at > now() - 1h
```

### 2. Use SAMPLE BY for Aggregations
```sql
-- Efficient
SELECT timestamp, avg(value)
FROM metrics
WHERE timestamp > now() - 1d
SAMPLE BY 5m;

-- Less efficient
SELECT timestamp, avg(value)
FROM metrics
WHERE timestamp > now() - 1d
GROUP BY timestamp;
```

### 3. Limit Result Sets
```sql
SELECT * FROM trading_metrics
WHERE timestamp > now() - 1h
LIMIT 1000;
```

### 4. Use LATEST ON for Most Recent Values
```sql
-- Efficient
SELECT * FROM trading_metrics
LATEST ON timestamp PARTITION BY symbol;

-- Less efficient
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
    FROM trading_metrics
) WHERE rn = 1;
```

## Testing Queries

Before using in Grafana, test via HTTP API:
```bash
# Encode query
QUERY="SELECT timestamp, metric_value FROM trading_metrics WHERE timestamp > now() - 1h LIMIT 10"
ENCODED=$(echo "$QUERY" | jq -sRr @uri)

# Execute
curl -s "http://localhost:9000/exec?query=$ENCODED" | jq '.'
```

## References

- **QuestDB SQL**: https://questdb.io/docs/reference/sql/
- **Grafana Variables**: https://grafana.com/docs/grafana/latest/variables/
- **Time Functions**: https://questdb.io/docs/reference/function/date-time/
- **Aggregation**: https://questdb.io/docs/reference/function/aggregation/
