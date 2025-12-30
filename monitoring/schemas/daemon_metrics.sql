-- T013: daemon_metrics table schema for QuestDB
-- Health Dashboard: Infrastructure health metrics from CCXT DaemonRunner

CREATE TABLE IF NOT EXISTS daemon_metrics (
    -- Designated timestamp (partition key)
    timestamp TIMESTAMP NOT NULL,

    -- Dimensions (SYMBOL for efficient storage)
    host SYMBOL CAPACITY 1000,           -- Hostname running daemon
    env SYMBOL CAPACITY 256,             -- Environment: prod, staging, dev

    -- Counters (monotonically increasing)
    fetch_count LONG,                    -- Cumulative OI/Funding fetches
    error_count LONG,                    -- Cumulative errors
    liquidation_count LONG,              -- Cumulative liquidations streamed

    -- Gauges (current state)
    uptime_seconds DOUBLE,               -- Time since daemon start
    running BOOLEAN,                     -- Daemon running state

    -- Status
    last_error VARCHAR                   -- Last error message (if any)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL
DEDUP UPSERT KEYS(timestamp, host, env);

-- Query examples for Health Dashboard panels:

-- Panel 1: Current daemon status (uptime)
-- SELECT
--     timestamp,
--     uptime_seconds / 3600 as uptime_hours,
--     running
-- FROM daemon_metrics
-- WHERE host = '${host}' AND env = '${env}'
-- ORDER BY timestamp DESC
-- LIMIT 1;

-- Panel 2: Fetch rate per hour (counter diff)
-- SELECT
--     timestamp,
--     fetch_count - lag(fetch_count) OVER (ORDER BY timestamp) as fetches_per_interval
-- FROM daemon_metrics
-- WHERE timestamp > now() - interval '24h'
--   AND host = '${host}'
-- SAMPLE BY 1h;

-- Panel 3: Error rate trend
-- SELECT
--     timestamp,
--     error_count - lag(error_count) OVER (ORDER BY timestamp) as errors_per_interval
-- FROM daemon_metrics
-- WHERE timestamp > now() - interval '7d'
--   AND host = '${host}'
-- SAMPLE BY 1h;

-- Panel 4: Last error timestamp
-- SELECT
--     timestamp,
--     last_error
-- FROM daemon_metrics
-- WHERE last_error IS NOT NULL
--   AND host = '${host}'
-- ORDER BY timestamp DESC
-- LIMIT 5;
