-- monitoring/schemas/trading_metrics.sql
-- T053: Trading metrics table schema for QuestDB
--
-- Run via QuestDB HTTP API or Web Console:
--   curl -G "http://localhost:9000/exec" --data-urlencode "query=$(cat trading_metrics.sql)"

CREATE TABLE IF NOT EXISTS trading_metrics (
    -- Designated timestamp (partition key)
    timestamp TIMESTAMP NOT NULL,

    -- Dimensions (SYMBOL for efficient storage)
    strategy SYMBOL CAPACITY 256,        -- Strategy identifier
    symbol SYMBOL CAPACITY 1000,         -- Trading symbol e.g. BTC/USDT:USDT
    venue SYMBOL CAPACITY 256,           -- Exchange: binance, bybit, okx
    env SYMBOL CAPACITY 256,             -- Environment: prod, staging, dev

    -- PnL metrics
    pnl DOUBLE,                          -- Realized PnL
    unrealized_pnl DOUBLE,               -- Unrealized PnL
    drawdown DOUBLE,                     -- Current drawdown %

    -- Position metrics
    position_size DOUBLE,                -- Current position size
    exposure DOUBLE,                     -- Total exposure value

    -- Order metrics
    orders_placed LONG,                  -- Cumulative orders placed
    orders_filled LONG,                  -- Cumulative orders filled
    fill_rate DOUBLE                     -- Fill rate (0.0 to 1.0)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL
DEDUP UPSERT KEYS(timestamp, strategy, symbol, venue);

-- Sample query: Current PnL by strategy
-- SELECT
--     strategy,
--     symbol,
--     pnl,
--     unrealized_pnl,
--     pnl + unrealized_pnl as total_pnl
-- FROM trading_metrics
-- WHERE timestamp > now() - interval '1m'
-- LATEST BY strategy, symbol;

-- Sample query: Orders per hour by strategy
-- SELECT
--     timestamp,
--     strategy,
--     max(orders_placed) - min(orders_placed) as orders_delta
-- FROM trading_metrics
-- WHERE timestamp > now() - interval '24h'
-- AND env = 'prod'
-- SAMPLE BY 1h ALIGN TO CALENDAR;

-- Sample query: Position exposure by symbol
-- SELECT
--     symbol,
--     venue,
--     sum(exposure) as total_exposure,
--     sum(position_size) as total_size
-- FROM trading_metrics
-- WHERE timestamp > now() - interval '1m'
-- AND env = 'prod'
-- LATEST BY symbol, venue;

-- Sample query: Drawdown history
-- SELECT
--     timestamp,
--     strategy,
--     drawdown
-- FROM trading_metrics
-- WHERE timestamp > now() - interval '7d'
-- AND env = 'prod'
-- AND drawdown > 0
-- ORDER BY timestamp DESC;

-- Sample query: Fill rate analysis
-- SELECT
--     strategy,
--     avg(fill_rate) as avg_fill_rate,
--     min(fill_rate) as min_fill_rate,
--     max(fill_rate) as max_fill_rate
-- FROM trading_metrics
-- WHERE timestamp > now() - interval '24h'
-- AND env = 'prod'
-- GROUP BY strategy;
