#!/bin/bash
# Health Check Script
# Verifies all services are running correctly

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0

check() {
    local name=$1
    local cmd=$2

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}[OK]${NC} $name"
    else
        echo -e "${RED}[FAIL]${NC} $name"
        FAILED=$((FAILED + 1))
    fi
}

echo "=== Health Check ==="
echo ""

# Core services
check "Redis" "redis-cli ping"
check "QuestDB" "curl -s http://localhost:9000/status"
check "Grafana" "curl -s http://localhost:3000/api/health"

# Python environment
check "Python" "python3 --version"
check "NautilusTrader" "python3 -c 'import nautilus_trader'"

# Git status
check "Git clean" "[ -z \"\$(git status --porcelain)\" ]"

# Disk space (warn if < 10GB)
DISK_FREE=$(df -BG . | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$DISK_FREE" -lt 10 ]; then
    echo -e "${YELLOW}[WARN]${NC} Disk space low: ${DISK_FREE}GB"
fi

echo ""
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}All checks passed${NC}"
    exit 0
else
    echo -e "${RED}$FAILED check(s) failed${NC}"
    exit 1
fi
