#!/bin/bash
# GitHub Actions Runner Entrypoint Script
# Configures and starts the self-hosted runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Validate required environment variables
if [[ -z "$RUNNER_TOKEN" ]]; then
    log_error "RUNNER_TOKEN is required"
    log_info "Get token from: Settings > Actions > Runners > New self-hosted runner"
    exit 1
fi

if [[ -z "$RUNNER_REPOSITORY" ]]; then
    log_error "RUNNER_REPOSITORY is required (format: owner/repo)"
    exit 1
fi

# Set defaults
RUNNER_NAME="${RUNNER_NAME:-nautilus-runner-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-self-hosted,linux,x64,nautilus}"
RUNNER_WORKDIR="${RUNNER_WORKDIR:-/home/runner/work}"

log_info "Starting GitHub Actions Runner"
log_info "Runner Name: $RUNNER_NAME"
log_info "Repository: $RUNNER_REPOSITORY"
log_info "Labels: $RUNNER_LABELS"
log_info "Work Directory: $RUNNER_WORKDIR"

# Configure runner if not already configured
if [[ ! -f ".runner" ]]; then
    log_info "Configuring runner..."

    ./config.sh \
        --url "https://github.com/${RUNNER_REPOSITORY}" \
        --token "${RUNNER_TOKEN}" \
        --name "${RUNNER_NAME}" \
        --labels "${RUNNER_LABELS}" \
        --work "${RUNNER_WORKDIR}" \
        --unattended \
        --replace

    log_info "Runner configured successfully"
else
    log_info "Runner already configured"
fi

# Verify service connectivity
log_info "Checking service connectivity..."

# Redis check
if redis-cli -h "${REDIS_HOST:-localhost}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; then
    log_info "Redis: OK"
else
    log_warn "Redis: NOT AVAILABLE (tests requiring Redis may fail)"
fi

# Neo4j check (bolt protocol)
if timeout 5 bash -c "echo > /dev/tcp/${NEO4J_URI#bolt://}/7687" 2>/dev/null; then
    log_info "Neo4j: OK"
else
    log_warn "Neo4j: NOT AVAILABLE"
fi

# QuestDB check
if curl -s "http://${QUESTDB_HOST:-localhost}:${QUESTDB_HTTP_PORT:-9000}/status" > /dev/null 2>&1; then
    log_info "QuestDB: OK"
else
    log_warn "QuestDB: NOT AVAILABLE"
fi

# DuckDB check (file exists)
if [[ -f "${DUCKDB_PATH:-/data/research.duckdb}" ]]; then
    log_info "DuckDB: OK (file exists)"
else
    log_warn "DuckDB: File not found at ${DUCKDB_PATH}"
fi

# Install Python dependencies from workspace if pyproject.toml exists
if [[ -f "/workspace/pyproject.toml" ]]; then
    log_info "Installing Python dependencies..."
    cd /workspace
    uv sync --frozen 2>/dev/null || uv sync || log_warn "Could not sync dependencies"
    cd /home/runner
fi

log_info "Starting runner..."

# Handle graceful shutdown
cleanup() {
    log_info "Received shutdown signal"
    ./config.sh remove --token "${RUNNER_TOKEN}" 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# Run the runner
./run.sh &

# Wait for runner process
wait $!
