-- Daily PnL Metrics Schema (Spec 013)
-- T036: QuestDB schema for daily PnL tracking
--
-- Tracks daily realized/unrealized PnL and limit triggers.
-- Used for real-time monitoring and alerting on daily loss limits.

CREATE TABLE IF NOT EXISTS daily_pnl (
    timestamp TIMESTAMP,
    trader_id SYMBOL,                    -- Trader identifier
    strategy_id SYMBOL,                  -- Strategy identifier (if per_strategy=True)
    realized_pnl DOUBLE,                 -- Realized PnL for the day
    unrealized_pnl DOUBLE,               -- Current unrealized PnL
    total_pnl DOUBLE,                    -- realized + unrealized
    limit_value DOUBLE,                  -- Configured daily loss limit
    limit_triggered BOOLEAN,             -- Whether limit was hit
    env SYMBOL                           -- Environment (prod/staging/dev)
) TIMESTAMP(timestamp) PARTITION BY DAY
WAL
DEDUP UPSERT KEYS(timestamp, trader_id, strategy_id);

-- Useful queries:
--
-- Current PnL per trader:
-- SELECT trader_id, strategy_id, total_pnl, limit_triggered
-- FROM daily_pnl
-- WHERE timestamp > now() - '5m'
-- LATEST BY trader_id, strategy_id;
--
-- Daily PnL history for a trader:
-- SELECT timestamp, total_pnl, limit_triggered
-- FROM daily_pnl
-- WHERE trader_id = 'TRADER-001'
--   AND timestamp > now() - '24h'
-- ORDER BY timestamp;
--
-- Count of limit triggers in last 7 days:
-- SELECT count() as limit_triggers
-- FROM daily_pnl
-- WHERE limit_triggered = true
--   AND timestamp > now() - '7d';
--
-- Max daily loss per trader:
-- SELECT trader_id, min(total_pnl) as max_loss
-- FROM daily_pnl
-- WHERE timestamp > now() - '30d'
-- GROUP BY trader_id;
