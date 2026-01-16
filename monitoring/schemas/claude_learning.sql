-- Claude Learning Patterns Schema
-- Syncs ClaudeFlow JSON data to QuestDB for time-series analysis
-- Created: 2026-01-16

-- Strategy performance tracking (from agents-profiles.json)
CREATE TABLE IF NOT EXISTS claude_strategy_metrics (
    timestamp TIMESTAMP,
    project SYMBOL INDEX,
    strategy SYMBOL INDEX,          -- conservative, balanced, aggressive
    success_rate DOUBLE,
    avg_score DOUBLE,
    avg_execution_time DOUBLE,
    uses LONG,
    real_executions LONG,
    improving BOOLEAN,
    improvement_rate DOUBLE
) TIMESTAMP(timestamp) PARTITION BY MONTH WAL;

-- Individual score snapshots (trend data from agents-profiles.json)
CREATE TABLE IF NOT EXISTS claude_strategy_trends (
    timestamp TIMESTAMP,
    project SYMBOL INDEX,
    strategy SYMBOL INDEX,
    score DOUBLE,
    is_real BOOLEAN                 -- true = actual execution, false = simulated
) TIMESTAMP(timestamp) PARTITION BY MONTH WAL;

-- Per-agent learning patterns (from models/*.json)
CREATE TABLE IF NOT EXISTS claude_agent_learning (
    timestamp TIMESTAMP,
    project SYMBOL INDEX,
    agent_type SYMBOL INDEX,        -- coder, verifier, architect, etc.
    score DOUBLE,
    passed BOOLEAN,
    pattern_type SYMBOL             -- success, failure, timeout
) TIMESTAMP(timestamp) PARTITION BY MONTH WAL;

-- Quality scores per block/responsibility
CREATE TABLE IF NOT EXISTS claude_quality_scores (
    timestamp TIMESTAMP,
    project SYMBOL INDEX,
    block SYMBOL INDEX,             -- validation, coding, github, general
    session_id SYMBOL,
    commit_hash STRING,
    score_total DOUBLE,
    score_code DOUBLE,
    score_test DOUBLE,
    score_data DOUBLE,
    score_framework DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;

-- Cross-repo learning aggregation
CREATE TABLE IF NOT EXISTS claude_cross_repo_patterns (
    timestamp TIMESTAMP,
    pattern_hash STRING,
    source_project SYMBOL INDEX,
    pattern_type SYMBOL,            -- error_fix, optimization, refactor
    confidence DOUBLE,
    usage_count LONG,
    success_rate DOUBLE
) TIMESTAMP(timestamp) PARTITION BY MONTH WAL;
