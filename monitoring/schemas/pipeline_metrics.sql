-- monitoring/schemas/pipeline_metrics.sql
-- T022: Pipeline metrics table schema for QuestDB
--
-- Run via QuestDB HTTP API or Web Console:
--   curl -G "http://localhost:9000/exec" --data-urlencode "query=$(cat pipeline_metrics.sql)"

CREATE TABLE IF NOT EXISTS pipeline_metrics (
    -- Designated timestamp (partition key)
    timestamp TIMESTAMP NOT NULL,

    -- Dimensions (SYMBOL for efficient storage)
    exchange SYMBOL CAPACITY 256,        -- Exchange: binance, bybit, okx
    symbol SYMBOL CAPACITY 10000,        -- e.g., BTC/USDT:USDT
    data_type SYMBOL CAPACITY 256,       -- oi, funding, liquidation
    host SYMBOL CAPACITY 1000,           -- Hostname running collector
    env SYMBOL CAPACITY 256,             -- Environment: prod, staging, dev

    -- Metrics
    records_count LONG,                  -- Records in this interval
    bytes_written LONG,                  -- Bytes written to storage
    latency_ms DOUBLE,                   -- Processing latency

    -- Quality
    gap_detected BOOLEAN,                -- Data gap detected
    gap_duration_seconds DOUBLE          -- Gap duration (if detected)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Sample query: Throughput by exchange (last hour)
-- SELECT
--     exchange,
--     sum(records_count) as total_records,
--     sum(bytes_written) as total_bytes
-- FROM pipeline_metrics
-- WHERE timestamp > now() - interval '1h'
-- GROUP BY exchange;

-- Sample query: Detect data gaps
-- SELECT
--     timestamp,
--     exchange,
--     symbol,
--     gap_duration_seconds
-- FROM pipeline_metrics
-- WHERE gap_detected = true
-- AND timestamp > now() - interval '24h'
-- ORDER BY timestamp DESC;
