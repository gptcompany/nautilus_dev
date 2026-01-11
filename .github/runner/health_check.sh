#!/bin/bash
# GitHub Runner Health Check
# Add to crontab: */5 * * * * /path/to/health_check.sh >> /tmp/runner_health.log 2>&1

CONTAINER_NAME="nautilus-github-runner"
COMPOSE_DIR="/media/sam/1TB/nautilus_dev/.github/runner"

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[$(date)] Runner container not running. Restarting..."
    cd "$COMPOSE_DIR" && docker compose up -d
    exit 1
fi

# Check if runner is idle (listening for jobs) or actively running
LAST_LOG=$(docker logs "$CONTAINER_NAME" --tail 1 2>/dev/null)
if echo "$LAST_LOG" | grep -q "Listening for Jobs"; then
    echo "[$(date)] Runner healthy - listening for jobs"
elif echo "$LAST_LOG" | grep -q "Running job"; then
    echo "[$(date)] Runner healthy - job in progress"
else
    echo "[$(date)] Runner status: $LAST_LOG"
fi
