#!/bin/bash
# NautilusTrader Auto-Update Cron Script
# Runs daily at 07:00 local time

set -e

cd /media/sam/1TB/nautilus_dev
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
export PYTHONPATH="/media/sam/1TB/nautilus_dev:$PYTHONPATH"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/1432322262949695508/v0-mhd2qIdpPY0rfoheN_EGrjRKAiXZUoJgR_9FAZimW9atKHpSPjtHxx8l0bSd4c5-A"

LOG_FILE="/var/log/nautilus-auto-update.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting auto-update check..." >> "$LOG_FILE"

# Check for updates
CHECK_OUTPUT=$(python -m scripts.auto_update check --format json 2>&1 || true)
echo "[$TIMESTAMP] Check: $CHECK_OUTPUT" >> "$LOG_FILE"

# Parse result and notify
VERSION=$(echo "$CHECK_OUTPUT" | grep -o '"latest_version": "[^"]*"' | cut -d'"' -f4)
COMMITS=$(echo "$CHECK_OUTPUT" | grep -o '"nightly_commits": [0-9]*' | cut -d: -f2 | tr -d ' ')
BREAKING=$(echo "$CHECK_OUTPUT" | grep -o '"breaking_changes": \[\]' || echo "[]")

if [ -n "$VERSION" ]; then
    if [ "$BREAKING" = '"breaking_changes": []' ]; then
        python -m scripts.auto_update notify "📦 NautilusTrader v$VERSION - $COMMITS nightly commits - No breaking changes" --channel discord >> "$LOG_FILE" 2>&1 || true
    else
        python -m scripts.auto_update notify "⚠️ NautilusTrader v$VERSION - Breaking changes detected!" --channel discord >> "$LOG_FILE" 2>&1 || true
    fi
fi

echo "[$TIMESTAMP] Completed" >> "$LOG_FILE"
