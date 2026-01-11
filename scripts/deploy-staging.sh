#!/bin/bash
# Deploy to Staging Environment
#
# Usage: ./scripts/deploy-staging.sh [--skip-tests] [--force]
#
# Prerequisites:
# - Docker and docker-compose installed
# - .env.staging configured with testnet credentials
# - QuestDB and Grafana containers available

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
STAGING_COMPOSE="$PROJECT_DIR/docker-compose.staging.yml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
SKIP_TESTS=false
FORCE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests) SKIP_TESTS=true; shift ;;
        --force) FORCE=true; shift ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

echo "=========================================="
echo "  Staging Deployment - $TIMESTAMP"
echo "=========================================="

# Step 1: Pre-flight checks
log_info "Step 1: Pre-flight checks..."

if [ ! -f "$STAGING_COMPOSE" ]; then
    log_error "Staging compose file not found: $STAGING_COMPOSE"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker not installed"
    exit 1
fi

if ! docker info &> /dev/null; then
    log_error "Docker daemon not running"
    exit 1
fi

# Step 2: Run tests (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    log_info "Step 2: Running tests..."
    cd "$PROJECT_DIR"

    if ! uv run pytest tests/ -x --tb=short -q; then
        if [ "$FORCE" = false ]; then
            log_error "Tests failed! Use --force to deploy anyway (not recommended)"
            exit 1
        else
            log_warn "Tests failed but --force specified, continuing..."
        fi
    else
        log_info "Tests passed!"
    fi
else
    log_warn "Step 2: Skipping tests (--skip-tests)"
fi

# Step 3: Lint check
log_info "Step 3: Running lint checks..."
cd "$PROJECT_DIR"
if ! uv run ruff check . --quiet; then
    log_warn "Lint issues found (non-blocking)"
fi

# Step 4: Create state snapshot
log_info "Step 4: Creating pre-deploy snapshot..."
SNAPSHOT_DIR="$PROJECT_DIR/.staging-snapshots"
mkdir -p "$SNAPSHOT_DIR"

# Save current git state
git rev-parse HEAD > "$SNAPSHOT_DIR/pre-deploy-$TIMESTAMP.git"

# Save current container state (if any)
if docker-compose -f "$STAGING_COMPOSE" ps -q 2>/dev/null | grep -q .; then
    docker-compose -f "$STAGING_COMPOSE" ps > "$SNAPSHOT_DIR/pre-deploy-$TIMESTAMP.containers"
fi

log_info "Snapshot saved to $SNAPSHOT_DIR/pre-deploy-$TIMESTAMP.*"

# Step 5: Build Docker images
log_info "Step 5: Building Docker images..."
cd "$PROJECT_DIR"
docker-compose -f "$STAGING_COMPOSE" build --parallel

# Step 6: Stop existing containers
log_info "Step 6: Stopping existing containers..."
docker-compose -f "$STAGING_COMPOSE" down --remove-orphans || true

# Step 7: Start new containers
log_info "Step 7: Starting new containers..."
docker-compose -f "$STAGING_COMPOSE" up -d

# Step 8: Wait for health checks
log_info "Step 8: Waiting for services to be healthy..."
HEALTH_TIMEOUT=60
HEALTH_INTERVAL=5
ELAPSED=0

while [ $ELAPSED -lt $HEALTH_TIMEOUT ]; do
    # Check if questdb is responding
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/health 2>/dev/null | grep -q "200"; then
        log_info "QuestDB healthy"
        break
    fi
    sleep $HEALTH_INTERVAL
    ELAPSED=$((ELAPSED + HEALTH_INTERVAL))
    echo -n "."
done
echo ""

if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
    log_warn "Health check timeout - services may still be starting"
fi

# Step 9: Run smoke tests
log_info "Step 9: Running smoke tests..."

# Check QuestDB
if curl -s "http://localhost:9000/exec?query=SELECT%201" | grep -q "dataset"; then
    log_info "QuestDB: OK"
else
    log_warn "QuestDB: Not responding"
fi

# Check Grafana
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/api/health 2>/dev/null | grep -q "200"; then
    log_info "Grafana: OK"
else
    log_warn "Grafana: Not responding (may need more time)"
fi

# Step 10: Summary
echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
log_info "Staging services:"
docker-compose -f "$STAGING_COMPOSE" ps
echo ""
log_info "Access points:"
echo "  - QuestDB Console: http://localhost:9000"
echo "  - Grafana:         http://localhost:3001"
echo ""
log_info "Rollback command:"
echo "  ./scripts/rollback.sh --to $TIMESTAMP"
echo ""
