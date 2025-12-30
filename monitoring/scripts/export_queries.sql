-- monitoring/scripts/export_queries.sql
-- T064: CSV export query examples for historical analysis
--
-- Usage: Copy queries to QuestDB Web Console or use HTTP API:
--   curl -G "http://localhost:9000/exec" --data-urlencode "query=<QUERY>" > output.csv

-- ============================================
-- Open Interest (OI) Data Export
-- ============================================

-- Export 30 days of OI data (aggregated hourly)
-- Optimized with SAMPLE BY for large time ranges
SELECT
    timestamp,
    exchange,
    symbol,
    sum(records_count) as oi_count,
    avg(latency_ms) as avg_latency
FROM pipeline_metrics
WHERE data_type = 'oi'
  AND timestamp > now() - interval '30d'
  AND env = 'prod'
SAMPLE BY 1h ALIGN TO CALENDAR;

-- Export raw OI data for specific symbol
SELECT
    timestamp,
    exchange,
    symbol,
    records_count,
    bytes_written,
    latency_ms,
    gap_detected
FROM pipeline_metrics
WHERE data_type = 'oi'
  AND symbol = 'BTC/USDT:USDT'
  AND timestamp > now() - interval '7d'
  AND env = 'prod'
ORDER BY timestamp;

-- ============================================
-- Funding Rate Data Export
-- ============================================

-- Export funding rate fetches (aggregated daily)
SELECT
    timestamp,
    exchange,
    sum(records_count) as funding_count,
    count(*) as fetch_count
FROM pipeline_metrics
WHERE data_type = 'funding'
  AND timestamp > now() - interval '90d'
  AND env = 'prod'
SAMPLE BY 1d ALIGN TO CALENDAR;

-- ============================================
-- Exchange Connectivity Export
-- ============================================

-- Export exchange downtime events
SELECT
    timestamp,
    exchange,
    connected,
    latency_ms,
    reconnect_count,
    last_message_at
FROM exchange_status
WHERE connected = false
  AND timestamp > now() - interval '30d'
  AND env = 'prod'
ORDER BY timestamp DESC;

-- Export latency percentiles by exchange (daily)
SELECT
    timestamp,
    exchange,
    avg(latency_ms) as avg_latency,
    max(latency_ms) as max_latency,
    min(latency_ms) as min_latency
FROM exchange_status
WHERE timestamp > now() - interval '30d'
  AND env = 'prod'
  AND connected = true
SAMPLE BY 1d ALIGN TO CALENDAR;

-- ============================================
-- Trading Performance Export
-- ============================================

-- Export daily PnL summary by strategy
SELECT
    timestamp,
    strategy,
    symbol,
    venue,
    max(pnl) as realized_pnl,
    max(unrealized_pnl) as unrealized_pnl,
    max(drawdown) as max_drawdown,
    sum(orders_placed) as total_orders
FROM trading_metrics
WHERE timestamp > now() - interval '30d'
  AND env = 'prod'
SAMPLE BY 1d ALIGN TO CALENDAR;

-- Export detailed trading activity
SELECT
    timestamp,
    strategy,
    symbol,
    venue,
    pnl,
    unrealized_pnl,
    position_size,
    exposure,
    orders_placed,
    orders_filled,
    fill_rate,
    drawdown
FROM trading_metrics
WHERE timestamp > now() - interval '7d'
  AND env = 'prod'
ORDER BY timestamp;

-- ============================================
-- Daemon Health Export
-- ============================================

-- Export daemon uptime and error summary
SELECT
    timestamp,
    host,
    max(uptime_seconds) as uptime,
    max(error_count) as errors,
    max(fetch_count) as fetches,
    max(liquidation_count) as liquidations
FROM daemon_metrics
WHERE timestamp > now() - interval '30d'
  AND env = 'prod'
SAMPLE BY 1d ALIGN TO CALENDAR;

-- Export error events
SELECT
    timestamp,
    host,
    error_count,
    last_error
FROM daemon_metrics
WHERE last_error IS NOT NULL
  AND timestamp > now() - interval '7d'
  AND env = 'prod'
ORDER BY timestamp DESC;

-- ============================================
-- Data Quality Analysis
-- ============================================

-- Export data gaps summary
SELECT
    timestamp,
    exchange,
    symbol,
    data_type,
    gap_duration_seconds
FROM pipeline_metrics
WHERE gap_detected = true
  AND timestamp > now() - interval '30d'
  AND env = 'prod'
ORDER BY gap_duration_seconds DESC;

-- Gap frequency by exchange
SELECT
    exchange,
    data_type,
    count(*) as gap_count,
    avg(gap_duration_seconds) as avg_gap_duration,
    max(gap_duration_seconds) as max_gap_duration,
    sum(gap_duration_seconds) as total_gap_time
FROM pipeline_metrics
WHERE gap_detected = true
  AND timestamp > now() - interval '30d'
  AND env = 'prod'
GROUP BY exchange, data_type
ORDER BY gap_count DESC;

-- ============================================
-- Performance Optimization Tips
-- ============================================

-- Use SAMPLE BY for aggregations over large time ranges
-- SAMPLE BY 1h = hourly buckets
-- SAMPLE BY 1d = daily buckets
-- SAMPLE BY 1w = weekly buckets

-- Use LATEST BY for current values
-- SELECT * FROM table WHERE timestamp > now() - interval '1m' LATEST BY key;

-- Use LIMIT for pagination
-- SELECT * FROM table ORDER BY timestamp DESC LIMIT 1000 OFFSET 0;

-- For CSV export via HTTP API with headers:
-- curl -G "http://localhost:9000/exec" \
--   --data-urlencode "query=SELECT * FROM table" \
--   -H "Accept: text/csv" > output.csv
