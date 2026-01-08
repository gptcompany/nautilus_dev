-- System Health Schema
-- Tracks component health status for monitoring
--
-- Used by Grafana alert rules for:
-- - System component down detection
-- - Connection status monitoring

CREATE TABLE IF NOT EXISTS system_health (
    timestamp TIMESTAMP,
    component SYMBOL,                    -- Component name
    component_type SYMBOL,               -- Type: adapter, cache, database, strategy

    -- Health status
    status SYMBOL,                       -- UP, DOWN, DEGRADED, UNKNOWN
    latency_ms DOUBLE,                   -- Response latency if applicable
    last_heartbeat TIMESTAMP,            -- Last successful heartbeat

    -- Details
    message STRING,                      -- Status message
    error_count LONG,                    -- Error count since last UP

    -- Connection details (for adapters)
    venue SYMBOL,                        -- Exchange for adapters
    connected BOOLEAN,                   -- Connection status

    env SYMBOL                           -- Environment (prod/staging/dev)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL
DEDUP UPSERT KEYS(timestamp, component, env);

-- Alert queries used by Grafana:
--
-- Components currently DOWN:
-- SELECT count()
-- FROM system_health
-- WHERE timestamp > now() - 5m
--   AND status = 'DOWN';
--
-- Current status of all components:
-- SELECT component, component_type, status, latency_ms
-- FROM system_health
-- WHERE timestamp > now() - 1m
-- LATEST BY component;
--
-- Connection status by venue:
-- SELECT venue, connected, status
-- FROM system_health
-- WHERE timestamp > now() - 1m
--   AND component_type = 'adapter'
-- LATEST BY venue;
