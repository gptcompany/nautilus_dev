-- Error Events Schema
-- Tracks all system errors for monitoring and alerting
--
-- Used by Grafana alert rules for:
-- - High error rate detection
-- - Error pattern analysis

CREATE TABLE IF NOT EXISTS error_events (
    timestamp TIMESTAMP,
    trader_id SYMBOL,                    -- Trader identifier
    strategy_id SYMBOL,                  -- Strategy identifier
    component SYMBOL,                    -- Component: strategy, adapter, cache, etc.

    -- Error details
    severity SYMBOL,                     -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    error_type SYMBOL,                   -- Exception type
    error_code SYMBOL,                   -- Error code if applicable
    message STRING,                      -- Error message (truncated)

    -- Context
    venue SYMBOL,                        -- Exchange if relevant
    symbol SYMBOL,                       -- Trading symbol if relevant
    order_id SYMBOL,                     -- Order ID if relevant

    env SYMBOL                           -- Environment (prod/staging/dev)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Alert queries used by Grafana:
--
-- Error count in last 10 minutes:
-- SELECT count() as errors
-- FROM error_events
-- WHERE timestamp > now() - 10m
--   AND severity IN ('ERROR', 'CRITICAL');
--
-- Errors by component:
-- SELECT component, count() as errors
-- FROM error_events
-- WHERE timestamp > now() - 1h
--   AND severity IN ('ERROR', 'CRITICAL')
-- GROUP BY component
-- ORDER BY errors DESC;
--
-- Error rate per minute:
-- SELECT timestamp, count() as errors
-- FROM error_events
-- WHERE timestamp > now() - 1h
--   AND severity IN ('ERROR', 'CRITICAL')
-- SAMPLE BY 1m;
