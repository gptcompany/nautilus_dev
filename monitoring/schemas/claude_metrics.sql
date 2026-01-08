-- QuestDB Schema for Claude Code Metrics
-- Migrated from InfluxDB to consolidate on single time-series DB

-- ============================================================================
-- Session Metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS claude_sessions (
    timestamp TIMESTAMP,
    project SYMBOL,
    session_id SYMBOL,
    duration_seconds DOUBLE,
    tool_calls LONG,
    errors LONG,
    error_rate DOUBLE,
    tasks_completed LONG
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- File Edit Metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS claude_file_edits (
    timestamp TIMESTAMP,
    project SYMBOL,
    session_id SYMBOL,
    is_rework BOOLEAN
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- Test Run Metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS claude_test_runs (
    timestamp TIMESTAMP,
    project SYMBOL,
    session_id SYMBOL,
    passed BOOLEAN
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- Agent Spawn Metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS claude_agents (
    timestamp TIMESTAMP,
    project SYMBOL,
    session_id SYMBOL,
    agent_type SYMBOL,
    success BOOLEAN
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- Cycle Time Metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS claude_cycle_times (
    timestamp TIMESTAMP,
    project SYMBOL,
    session_id SYMBOL,
    seconds DOUBLE,
    minutes DOUBLE,
    iterations LONG
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- TDD Compliance Metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS claude_tdd (
    timestamp TIMESTAMP,
    project SYMBOL,
    event_type SYMBOL,
    file_name SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY;

-- ============================================================================
-- Prompt Optimization Metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS claude_prompts (
    timestamp TIMESTAMP,
    event_type SYMBOL,
    target_model SYMBOL,
    optimizer_model SYMBOL,
    style SYMBOL,
    ambiguity DOUBLE,
    confidence DOUBLE,
    expansion_ratio DOUBLE,
    accepted BOOLEAN,
    similarity DOUBLE,
    reason SYMBOL
) TIMESTAMP(timestamp) PARTITION BY DAY;
