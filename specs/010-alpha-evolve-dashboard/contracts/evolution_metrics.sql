-- QuestDB Table Definition: evolution_metrics
-- Purpose: Time-series storage for Alpha-Evolve strategy evolution data
-- Used by: Grafana Evolution Dashboard (spec-010)
-- Created: 2025-12-28

-- Drop table if exists (development only)
-- DROP TABLE IF EXISTS evolution_metrics;

CREATE TABLE IF NOT EXISTS evolution_metrics (
    -- Timestamp (required for time-series)
    timestamp TIMESTAMP,

    -- Strategy identification
    program_id SYMBOL CAPACITY 100000,  -- UUID, high cardinality
    experiment SYMBOL CAPACITY 256,      -- Experiment name, low cardinality
    generation INT,                      -- Generation number (0 = seed)
    parent_id SYMBOL CAPACITY 100000,   -- Parent strategy UUID (null for seeds)

    -- Fitness metrics (match SQLite store.py schema)
    sharpe DOUBLE,                       -- Sharpe ratio
    calmar DOUBLE,                       -- Calmar ratio (primary fitness metric)
    max_dd DOUBLE,                       -- Maximum drawdown (percentage)
    cagr DOUBLE,                         -- Compound annual growth rate
    total_return DOUBLE,                 -- Total return percentage
    trade_count INT,                     -- Number of trades executed
    win_rate DOUBLE,                     -- Win rate (0-1)

    -- Mutation tracking (for dashboard panel 4)
    mutation_outcome SYMBOL CAPACITY 8,  -- success, syntax_error, runtime_error, timeout, seed
    mutation_latency_ms DOUBLE           -- Mutation API call duration in milliseconds
)
TIMESTAMP(timestamp)
PARTITION BY DAY;

-- Indexes are automatic for SYMBOL columns in QuestDB
-- Additional indexes can be created for frequently queried INT columns:
-- CREATE INDEX ON evolution_metrics (generation);

-- Sample data for testing (uncomment to insert)
-- INSERT INTO evolution_metrics (timestamp, program_id, experiment, generation, parent_id, sharpe, calmar, max_dd, cagr, total_return, trade_count, win_rate, mutation_outcome, mutation_latency_ms)
-- VALUES
-- (now(), 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'btc_momentum_v1', 0, NULL, 1.5, 2.0, 10.5, 0.35, 0.65, 100, 0.55, 'seed', 0.0),
-- (now(), 'b2c3d4e5-f6a7-8901-bcde-f2345678901a', 'btc_momentum_v1', 1, 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 1.8, 2.5, 8.2, 0.42, 0.78, 120, 0.58, 'success', 2340.5);
