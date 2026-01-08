-- Initialize All QuestDB Tables
-- Run this to create all monitoring tables
--
-- Usage:
--   curl -G "http://localhost:9000/exec" --data-urlencode "query=$(cat init_all.sql)"
--
-- Or via script:
--   ./scripts/init-questdb.sh

-- ============================================================================
-- Trading Metrics
-- ============================================================================

-- Core trading metrics (PnL, positions, orders)
-- Source: trading_metrics.sql

-- Daily PnL tracking
-- Source: daily_pnl.sql

-- Risk metrics for alerting (drawdown, exposure)
-- Source: trading_risk.sql

-- Order execution latency
-- Source: order_latency.sql

-- ============================================================================
-- System Health
-- ============================================================================

-- Component health status
-- Source: system_health.sql

-- Error events
-- Source: error_events.sql

-- Circuit breaker state
-- Source: circuit_breaker_state.sql

-- Exchange status
-- Source: exchange_status.sql

-- ============================================================================
-- Pipeline & Evolution
-- ============================================================================

-- Data pipeline metrics
-- Source: pipeline_metrics.sql

-- Strategy evolution metrics
-- Source: evolution_metrics.sql

-- Daemon metrics
-- Source: daemon_metrics.sql

-- ============================================================================
-- Claude Code Metrics
-- ============================================================================

-- Claude sessions, file edits, tests, agents
-- Source: claude_metrics.sql

-- ============================================================================
-- To initialize all tables, run each .sql file:
-- ============================================================================
-- for f in monitoring/schemas/*.sql; do
--   if [ "$f" != "monitoring/schemas/init_all.sql" ]; then
--     curl -s -G "http://localhost:9000/exec" --data-urlencode "query=$(cat $f)"
--   fi
-- done
