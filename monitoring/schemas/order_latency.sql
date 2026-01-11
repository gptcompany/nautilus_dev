-- Order Latency Schema
-- Tracks order execution latency for performance monitoring
--
-- Used by Grafana dashboards for:
-- - Order execution latency analysis
-- - Fill time distribution
-- - Venue performance comparison

CREATE TABLE IF NOT EXISTS order_latency (
    timestamp TIMESTAMP,
    trader_id SYMBOL,                    -- Trader identifier
    strategy_id SYMBOL,                  -- Strategy identifier
    order_id SYMBOL,                     -- Order identifier

    -- Order details
    venue SYMBOL,                        -- Exchange
    symbol SYMBOL,                       -- Trading symbol
    side SYMBOL,                         -- BUY, SELL
    order_type SYMBOL,                   -- MARKET, LIMIT, STOP, etc.

    -- Latency metrics (all in milliseconds)
    submit_latency_ms DOUBLE,            -- Time to submit order
    ack_latency_ms DOUBLE,               -- Time to receive acknowledgement
    fill_latency_ms DOUBLE,              -- Time to fill (for filled orders)
    total_latency_ms DOUBLE,             -- Total round-trip time

    -- Fill details
    fill_status SYMBOL,                  -- FILLED, PARTIAL, REJECTED, CANCELLED
    fill_pct DOUBLE,                     -- Fill percentage (0-100)
    slippage_bps DOUBLE,                 -- Slippage in basis points

    env SYMBOL                           -- Environment (prod/staging/dev)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Dashboard queries:
--
-- Average latency by venue (last hour):
-- SELECT venue, avg(total_latency_ms) as avg_latency
-- FROM order_latency
-- WHERE timestamp > now() - 1h
--   AND env = 'prod'
-- GROUP BY venue;
--
-- Latency percentiles:
-- SELECT
--     venue,
--     percentile_cont(total_latency_ms, 0.5) as p50,
--     percentile_cont(total_latency_ms, 0.95) as p95,
--     percentile_cont(total_latency_ms, 0.99) as p99
-- FROM order_latency
-- WHERE timestamp > now() - 1h
-- GROUP BY venue;
--
-- Latency over time:
-- SELECT timestamp, avg(total_latency_ms) as latency
-- FROM order_latency
-- WHERE timestamp > now() - 24h
-- SAMPLE BY 5m;
--
-- Slippage analysis:
-- SELECT venue, symbol, avg(slippage_bps) as avg_slippage
-- FROM order_latency
-- WHERE timestamp > now() - 24h
--   AND fill_status = 'FILLED'
-- GROUP BY venue, symbol;
