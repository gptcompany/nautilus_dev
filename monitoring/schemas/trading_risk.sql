-- Trading Risk Metrics Schema
-- Real-time risk metrics for monitoring and alerting
--
-- Used by Grafana alert rules for:
-- - Drawdown alerts (>5% warning, >10% critical)
-- - Position exposure alerts
-- - Daily loss limit alerts

CREATE TABLE IF NOT EXISTS trading_risk (
    timestamp TIMESTAMP,
    trader_id SYMBOL,                    -- Trader identifier
    strategy_id SYMBOL,                  -- Strategy identifier

    -- Drawdown metrics
    drawdown_pct DOUBLE,                 -- Current drawdown % (0-100)
    max_drawdown_pct DOUBLE,             -- Maximum drawdown in session

    -- Position exposure
    position_exposure_pct DOUBLE,        -- Position as % of account
    gross_exposure DOUBLE,               -- Total gross exposure USD
    net_exposure DOUBLE,                 -- Net exposure USD

    -- Daily PnL
    daily_pnl_pct DOUBLE,                -- Daily PnL as % of account
    daily_pnl_usd DOUBLE,                -- Daily PnL in USD

    -- Risk limits
    leverage DOUBLE,                     -- Current leverage
    max_leverage_limit DOUBLE,           -- Configured max leverage

    env SYMBOL                           -- Environment (prod/staging/dev)
) TIMESTAMP(timestamp) PARTITION BY DAY WAL
DEDUP UPSERT KEYS(timestamp, trader_id, strategy_id);

-- Alert queries used by Grafana:
--
-- Drawdown > 10% Critical:
-- SELECT last(drawdown_pct) as value
-- FROM trading_risk
-- WHERE timestamp > now() - 5m;
--
-- Daily loss limit check:
-- SELECT last(daily_pnl_pct)
-- FROM trading_risk
-- WHERE timestamp > now() - 1d;
--
-- Position exposure warning:
-- SELECT max(position_exposure_pct)
-- FROM trading_risk
-- WHERE timestamp > now() - 1m;
