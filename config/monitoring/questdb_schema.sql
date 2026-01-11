-- QuestDB Schema for Trading Metrics
-- Run: curl -G --data-urlencode "query@questdb_schema.sql" http://localhost:9000/exec

-- ============================================================================
-- PnL Metrics (real-time profit/loss tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_pnl (
    timestamp TIMESTAMP,
    strategy_id SYMBOL,
    symbol SYMBOL,
    realized_pnl DOUBLE,
    unrealized_pnl DOUBLE,
    total_pnl DOUBLE,
    cumulative_pnl DOUBLE,
    trade_count LONG,
    win_count LONG,
    loss_count LONG
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- Position Metrics (current positions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_positions (
    timestamp TIMESTAMP,
    strategy_id SYMBOL,
    symbol SYMBOL,
    side SYMBOL,           -- LONG, SHORT, FLAT
    quantity DOUBLE,
    avg_entry_price DOUBLE,
    current_price DOUBLE,
    unrealized_pnl DOUBLE,
    margin_used DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- Order Metrics (execution quality)
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_orders (
    timestamp TIMESTAMP,
    strategy_id SYMBOL,
    symbol SYMBOL,
    order_id STRING,
    order_type SYMBOL,     -- MARKET, LIMIT, STOP
    side SYMBOL,           -- BUY, SELL
    quantity DOUBLE,
    price DOUBLE,
    filled_quantity DOUBLE,
    avg_fill_price DOUBLE,
    slippage_bps DOUBLE,
    latency_ms DOUBLE,
    status SYMBOL          -- FILLED, PARTIAL, REJECTED, CANCELLED
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- Risk Metrics (safety monitoring)
-- ============================================================================
CREATE TABLE IF NOT EXISTS trading_risk (
    timestamp TIMESTAMP,
    strategy_id SYMBOL,
    drawdown_pct DOUBLE,
    daily_pnl_pct DOUBLE,
    position_exposure_pct DOUBLE,
    leverage_used DOUBLE,
    margin_ratio DOUBLE,
    risk_score DOUBLE,     -- 0-100, higher = more risk
    alert_level SYMBOL     -- NORMAL, WARNING, CRITICAL
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- System Metrics (health monitoring)
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_health (
    timestamp TIMESTAMP,
    component SYMBOL,      -- TRADING_NODE, ADAPTER, CACHE
    status SYMBOL,         -- HEALTHY, DEGRADED, DOWN
    latency_ms DOUBLE,
    error_count LONG,
    memory_mb DOUBLE,
    cpu_pct DOUBLE
) TIMESTAMP(timestamp) PARTITION BY HOUR;

-- ============================================================================
-- Error Events (for alerting)
-- ============================================================================
CREATE TABLE IF NOT EXISTS error_events (
    timestamp TIMESTAMP,
    severity SYMBOL,       -- INFO, WARNING, ERROR, CRITICAL
    component SYMBOL,
    strategy_id SYMBOL,
    error_code STRING,
    message STRING
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- Alert History (for tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS alert_history (
    timestamp TIMESTAMP,
    alert_type SYMBOL,     -- DRAWDOWN, ERROR_RATE, POSITION, SYSTEM
    severity SYMBOL,
    message STRING,
    value DOUBLE,
    threshold DOUBLE,
    notified BOOLEAN
) TIMESTAMP(timestamp) PARTITION BY DAY;
