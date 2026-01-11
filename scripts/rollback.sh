#!/bin/bash
# Rollback Script - Target: < 5 minutes
# Usage: ./scripts/rollback.sh [TAG]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[ROLLBACK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Find rollback target
TAG=${1:-$(git tag -l "deploy-*" 2>/dev/null | sort -r | sed -n '2p')}

if [ -z "$TAG" ]; then
    warn "No deploy tag found, using HEAD~1"
    TAG="HEAD~1"
fi

log "Starting rollback to: $TAG"
START_TIME=$(date +%s)

# Step 1: Stop trading (if running)
log "Step 1/4: Stopping services..."
if pgrep -f "trading_node" > /dev/null 2>&1; then
    pkill -SIGTERM -f "trading_node" || true
    sleep 2
    pkill -SIGKILL -f "trading_node" 2>/dev/null || true
fi
log "Services stopped"

# Step 2: Backup current state
log "Step 2/4: Backing up current state..."
BACKUP_DIR="/tmp/rollback-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r config/ "$BACKUP_DIR/" 2>/dev/null || true
git rev-parse HEAD > "$BACKUP_DIR/previous_commit"
log "Backup saved to $BACKUP_DIR"

# Step 3: Checkout target version
log "Step 3/4: Checking out $TAG..."
git fetch --tags 2>/dev/null || true
git checkout "$TAG" --force

# Step 4: Verify
log "Step 4/4: Verifying..."
CURRENT=$(git log -1 --oneline)
log "Now at: $CURRENT"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
log "=========================================="
log "ROLLBACK COMPLETE in ${DURATION}s"
log "=========================================="
log "Rolled back to: $TAG"
log "Backup at: $BACKUP_DIR"
echo ""
warn "Next steps:"
echo "  1. Start services: ./scripts/start.sh"
echo "  2. Verify health: ./scripts/health_check.sh"
echo "  3. Create incident report"
