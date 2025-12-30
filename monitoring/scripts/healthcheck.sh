#!/bin/bash
# monitoring/scripts/healthcheck.sh
# T070: Startup health check script for monitoring stack
#
# Verifies QuestDB and Grafana are running and accessible.
# Exit codes: 0 = healthy, 1 = unhealthy
#
# Usage:
#   ./healthcheck.sh [--verbose]

set -e

# Configuration
QUESTDB_HOST="${MONITORING_QUESTDB_HOST:-localhost}"
QUESTDB_HTTP_PORT="${MONITORING_QUESTDB_HTTP_PORT:-9000}"
GRAFANA_HOST="${GRAFANA_HOST:-localhost}"
GRAFANA_PORT="${GRAFANA_PORT:-3000}"
VERBOSE="${1:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    if [[ "$VERBOSE" == "--verbose" || "$VERBOSE" == "-v" ]]; then
        echo -e "$1"
    fi
}

log_always() {
    echo -e "$1"
}

check_questdb() {
    log "${YELLOW}Checking QuestDB...${NC}"

    # Check HTTP API
    HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://${QUESTDB_HOST}:${QUESTDB_HTTP_PORT}/exec?query=SELECT%201" 2>/dev/null || echo "000")

    if [[ "$HTTP_RESPONSE" == "200" ]]; then
        log "${GREEN}✓ QuestDB HTTP API is healthy${NC}"

        # Check if tables exist
        TABLES_RESPONSE=$(curl -s "http://${QUESTDB_HOST}:${QUESTDB_HTTP_PORT}/exec?query=SHOW%20TABLES" 2>/dev/null || echo "")

        if echo "$TABLES_RESPONSE" | grep -q "daemon_metrics"; then
            log "${GREEN}✓ daemon_metrics table exists${NC}"
        else
            log "${YELLOW}! daemon_metrics table not found (may need initialization)${NC}"
        fi

        if echo "$TABLES_RESPONSE" | grep -q "exchange_status"; then
            log "${GREEN}✓ exchange_status table exists${NC}"
        else
            log "${YELLOW}! exchange_status table not found (may need initialization)${NC}"
        fi

        if echo "$TABLES_RESPONSE" | grep -q "pipeline_metrics"; then
            log "${GREEN}✓ pipeline_metrics table exists${NC}"
        else
            log "${YELLOW}! pipeline_metrics table not found (may need initialization)${NC}"
        fi

        if echo "$TABLES_RESPONSE" | grep -q "trading_metrics"; then
            log "${GREEN}✓ trading_metrics table exists${NC}"
        else
            log "${YELLOW}! trading_metrics table not found (may need initialization)${NC}"
        fi

        return 0
    else
        log_always "${RED}✗ QuestDB HTTP API is not responding (HTTP $HTTP_RESPONSE)${NC}"
        return 1
    fi
}

check_grafana() {
    log "${YELLOW}Checking Grafana...${NC}"

    # Check health endpoint
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://${GRAFANA_HOST}:${GRAFANA_PORT}/api/health" 2>/dev/null || echo "000")

    if [[ "$HEALTH_RESPONSE" == "200" ]]; then
        log "${GREEN}✓ Grafana is healthy${NC}"

        # Check QuestDB datasource
        DS_RESPONSE=$(curl -s "http://admin:admin@${GRAFANA_HOST}:${GRAFANA_PORT}/api/datasources/name/QuestDB" 2>/dev/null || echo "")

        if echo "$DS_RESPONSE" | grep -q "questdb"; then
            log "${GREEN}✓ QuestDB datasource configured${NC}"
        else
            log "${YELLOW}! QuestDB datasource may not be configured${NC}"
        fi

        return 0
    else
        log_always "${RED}✗ Grafana is not responding (HTTP $HEALTH_RESPONSE)${NC}"
        return 1
    fi
}

check_docker_compose() {
    log "${YELLOW}Checking Docker containers...${NC}"

    # Check if docker-compose services are running
    if command -v docker-compose &> /dev/null; then
        MONITORING_DIR="$(dirname "$0")/.."

        if [[ -f "${MONITORING_DIR}/docker-compose.yml" ]]; then
            cd "$MONITORING_DIR"

            RUNNING=$(docker-compose ps --services --filter "status=running" 2>/dev/null || echo "")

            if echo "$RUNNING" | grep -q "questdb"; then
                log "${GREEN}✓ QuestDB container running${NC}"
            else
                log "${YELLOW}! QuestDB container not found via docker-compose${NC}"
            fi

            if echo "$RUNNING" | grep -q "grafana"; then
                log "${GREEN}✓ Grafana container running${NC}"
            else
                log "${YELLOW}! Grafana container not found via docker-compose${NC}"
            fi
        fi
    else
        log "${YELLOW}! docker-compose not available, skipping container check${NC}"
    fi
}

# Main health check
main() {
    log_always "${YELLOW}=== Nautilus Monitoring Health Check ===${NC}"

    HEALTHY=true

    # Check Docker containers (informational)
    check_docker_compose || true

    # Check QuestDB (required)
    if ! check_questdb; then
        HEALTHY=false
    fi

    # Check Grafana (required)
    if ! check_grafana; then
        HEALTHY=false
    fi

    echo ""

    if [[ "$HEALTHY" == "true" ]]; then
        log_always "${GREEN}=== All services healthy ===${NC}"
        exit 0
    else
        log_always "${RED}=== Some services unhealthy ===${NC}"
        exit 1
    fi
}

main
