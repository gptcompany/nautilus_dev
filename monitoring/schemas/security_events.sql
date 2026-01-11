-- ============================================================================
-- Security Events Schema for QuestDB
-- ============================================================================
-- This schema supports the security dashboard and audit logging.
-- Run against QuestDB using HTTP API or SQL console.
-- ============================================================================

-- Security Events Table
-- Tracks all security-related events (login attempts, blocked IPs, alerts)
CREATE TABLE IF NOT EXISTS security_events (
    timestamp TIMESTAMP,
    event_type SYMBOL,           -- login_failed, login_success, ip_blocked, rate_limited, etc.
    severity SYMBOL,             -- critical, high, medium, low
    source_ip STRING,
    user_agent STRING,
    user_id STRING,
    endpoint STRING,
    message STRING,
    metadata STRING,             -- JSON for additional context
    resolved BOOLEAN
) TIMESTAMP(timestamp) PARTITION BY DAY
WITH maxUncommittedRows=10000, commitLag=1s;

-- API Access Log
-- Tracks all API requests for audit and anomaly detection
CREATE TABLE IF NOT EXISTS api_access_log (
    timestamp TIMESTAMP,
    client_ip STRING,
    endpoint STRING,
    method SYMBOL,               -- GET, POST, PUT, DELETE
    status_code INT,
    response_time_ms DOUBLE,
    user_id STRING,
    user_agent STRING,
    request_size INT,
    response_size INT,
    error_message STRING
) TIMESTAMP(timestamp) PARTITION BY DAY
WITH maxUncommittedRows=50000, commitLag=500ms;

-- Order Audit Log
-- Tracks all trading orders for compliance and security
CREATE TABLE IF NOT EXISTS order_audit_log (
    timestamp TIMESTAMP,
    order_id STRING,
    symbol SYMBOL,
    side SYMBOL,                 -- buy, sell
    order_type SYMBOL,           -- market, limit, stop
    quantity DOUBLE,
    price DOUBLE,
    status SYMBOL,               -- submitted, filled, rejected, cancelled
    rejection_reason STRING,
    exchange STRING,
    strategy_id STRING,
    user_id STRING,
    client_order_id STRING,
    execution_id STRING,
    fill_price DOUBLE,
    fill_quantity DOUBLE,
    fees DOUBLE,
    metadata STRING              -- JSON for additional context
) TIMESTAMP(timestamp) PARTITION BY DAY
WITH maxUncommittedRows=10000, commitLag=1s;

-- Trading Risk Metrics
-- Real-time risk monitoring data
CREATE TABLE IF NOT EXISTS trading_risk_metrics (
    timestamp TIMESTAMP,
    account_id STRING,
    equity DOUBLE,
    position_value DOUBLE,
    position_size_pct DOUBLE,    -- Position as % of equity
    daily_pnl DOUBLE,
    daily_pnl_pct DOUBLE,        -- P&L as % of equity
    leverage DOUBLE,
    margin_used DOUBLE,
    margin_available DOUBLE,
    open_orders INT,
    open_positions INT,
    max_drawdown DOUBLE,
    trading_halted BOOLEAN,
    halt_reason STRING
) TIMESTAMP(timestamp) PARTITION BY DAY
WITH maxUncommittedRows=10000, commitLag=1s;

-- Withdrawal Log
-- Tracks all withdrawal requests for security
CREATE TABLE IF NOT EXISTS withdrawal_log (
    timestamp TIMESTAMP,
    withdrawal_id STRING,
    account_id STRING,
    amount DOUBLE,
    currency SYMBOL,
    destination_address STRING,
    status SYMBOL,               -- pending, approved, rejected, completed
    approval_timestamp TIMESTAMP,
    approved_by STRING,
    rejection_reason STRING,
    is_whitelisted BOOLEAN,
    delay_hours INT
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- Model Access Log (ML Security)
-- Tracks all ML model loads and predictions
CREATE TABLE IF NOT EXISTS model_access_log (
    timestamp TIMESTAMP,
    model_path STRING,
    model_hash STRING,           -- SHA-256 of model file
    signature_valid BOOLEAN,
    action SYMBOL,               -- load, predict, validate
    success BOOLEAN,
    error_message STRING,
    load_time_ms DOUBLE,
    inference_time_ms DOUBLE,
    user_id STRING,
    source_ip STRING
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- Sample Data for Testing (DELETE IN PRODUCTION)
-- ============================================================================

-- Insert sample security event
-- INSERT INTO security_events VALUES(
--     now(),
--     'login_failed',
--     'medium',
--     '192.168.1.100',
--     'Mozilla/5.0',
--     'test_user',
--     '/api/login',
--     'Invalid credentials',
--     '{"attempts": 3}',
--     false
-- );

-- ============================================================================
-- Useful Queries
-- ============================================================================

-- Failed logins in last hour
-- SELECT count() FROM security_events WHERE event_type = 'login_failed' AND timestamp > dateadd('h', -1, now());

-- API requests by endpoint (last 6h)
-- SELECT endpoint, count() as requests FROM api_access_log WHERE timestamp > dateadd('h', -6, now()) GROUP BY endpoint ORDER BY requests DESC;

-- Orders by status (last 24h)
-- SELECT status, count() as orders FROM order_audit_log WHERE timestamp > dateadd('h', -24, now()) GROUP BY status;

-- Current risk metrics
-- SELECT * FROM trading_risk_metrics ORDER BY timestamp DESC LIMIT 1;

-- Model loads with invalid signatures
-- SELECT * FROM model_access_log WHERE signature_valid = false ORDER BY timestamp DESC;
