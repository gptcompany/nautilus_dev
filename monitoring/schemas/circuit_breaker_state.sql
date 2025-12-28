-- Circuit Breaker State Metrics Schema
-- T029: QuestDB schema for circuit breaker state changes
--
-- Tracks circuit breaker state transitions, drawdown levels, and equity values.
-- Used for real-time monitoring and alerting on portfolio-level risk.

CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    timestamp TIMESTAMP,
    trader_id SYMBOL,                    -- Trader identifier
    state SYMBOL INDEX,                  -- CircuitBreakerState (active/warning/reducing/halted)
    current_drawdown DOUBLE,             -- Current drawdown as decimal (0.15 = 15%)
    peak_equity DOUBLE,                  -- High water mark
    current_equity DOUBLE,               -- Current equity value
    env SYMBOL                           -- Environment (prod/staging/dev)
) TIMESTAMP(timestamp) PARTITION BY DAY
WAL
DEDUP UPSERT KEYS(timestamp, trader_id);

-- Useful queries:
--
-- Current state per trader:
-- SELECT trader_id, state, current_drawdown, peak_equity, current_equity
-- FROM circuit_breaker_state
-- WHERE timestamp > now() - '5m'
-- LATEST BY trader_id;
--
-- State history for a trader:
-- SELECT timestamp, state, current_drawdown
-- FROM circuit_breaker_state
-- WHERE trader_id = 'TRADER-001'
--   AND timestamp > now() - '24h'
-- ORDER BY timestamp;
--
-- Count of HALTED events in last 7 days:
-- SELECT count() as halted_count
-- FROM circuit_breaker_state
-- WHERE state = 'halted'
--   AND timestamp > now() - '7d';
