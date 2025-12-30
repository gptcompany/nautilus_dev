-- monitoring/schemas/exchange_status.sql
-- T033: Exchange status table schema for QuestDB
--
-- Run via QuestDB HTTP API or Web Console:
--   curl -G "http://localhost:9000/exec" --data-urlencode "query=$(cat exchange_status.sql)"

CREATE TABLE IF NOT EXISTS exchange_status (
    -- Designated timestamp (partition key)
    timestamp TIMESTAMP NOT NULL,

    -- Dimensions (SYMBOL for efficient storage)
    exchange SYMBOL CAPACITY 256,        -- Exchange: binance, bybit, okx
    host SYMBOL CAPACITY 1000,           -- Hostname running collector
    env SYMBOL CAPACITY 256,             -- Environment: prod, staging, dev

    -- Status
    connected BOOLEAN,                   -- WebSocket connected
    latency_ms DOUBLE,                   -- Round-trip latency
    reconnect_count LONG,                -- Cumulative reconnections

    -- Timestamps
    last_message_at TIMESTAMP,           -- Last message received
    disconnected_at TIMESTAMP            -- Last disconnect time (null if connected)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL
DEDUP UPSERT KEYS(timestamp, exchange, host);

-- Sample query: Current exchange status
-- SELECT
--     exchange,
--     connected,
--     latency_ms,
--     last_message_at
-- FROM exchange_status
-- WHERE timestamp > now() - interval '1m'
-- LATEST BY exchange;

-- Sample query: Reconnection events (last 24h)
-- SELECT
--     timestamp,
--     exchange,
--     reconnect_count
-- FROM exchange_status
-- WHERE reconnect_count > 0
-- AND timestamp > now() - interval '24h'
-- ORDER BY timestamp DESC;

-- Sample query: Downtime events
-- SELECT
--     timestamp,
--     exchange,
--     disconnected_at
-- FROM exchange_status
-- WHERE connected = false
-- AND timestamp > now() - interval '7d'
-- ORDER BY timestamp DESC;
