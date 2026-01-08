#!/bin/bash
# Setup Discord Webhook for Grafana Alerts
#
# Usage: ./scripts/setup-discord-alerts.sh
#
# Prerequisites:
# 1. Discord server with admin permissions
# 2. Channel for alerts

set -e

echo "=== Discord Alert Webhook Setup ==="
echo ""

# Check if already configured
if [ -n "$DISCORD_WEBHOOK_URL" ]; then
    echo "Discord already configured:"
    echo "  Webhook: ${DISCORD_WEBHOOK_URL:0:50}..."
    echo ""
    read -p "Reconfigure? (y/N): " RECONFIG
    if [ "$RECONFIG" != "y" ] && [ "$RECONFIG" != "Y" ]; then
        echo "Keeping existing configuration."
        exit 0
    fi
fi

echo "Step 1: Create Discord Webhook"
echo "  - Open Discord and go to your server"
echo "  - Server Settings > Integrations > Webhooks"
echo "  - Click 'New Webhook'"
echo "  - Name it 'Trading Alerts'"
echo "  - Select the alerts channel"
echo "  - Copy the webhook URL"
echo ""
read -p "Enter webhook URL: " WEBHOOK_URL

if [ -z "$WEBHOOK_URL" ]; then
    echo "Error: Webhook URL is required"
    exit 1
fi

# Validate URL format
if [[ ! "$WEBHOOK_URL" =~ ^https://discord\.com/api/webhooks/ ]] && [[ ! "$WEBHOOK_URL" =~ ^https://discordapp\.com/api/webhooks/ ]]; then
    echo "Warning: URL doesn't look like a Discord webhook"
    read -p "Continue anyway? (y/N): " CONT
    if [ "$CONT" != "y" ] && [ "$CONT" != "Y" ]; then
        exit 1
    fi
fi

# Test webhook
echo ""
echo "Step 2: Testing webhook..."
TEST_RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{
        "content": null,
        "embeds": [{
            "title": "Trading Alerts Connected",
            "description": "This is a test message from your trading system.\n\nIf you see this, Discord alerts are working!",
            "color": 5763719,
            "fields": [
                {"name": "System", "value": "nautilus-dev", "inline": true},
                {"name": "Status", "value": "OK", "inline": true}
            ],
            "footer": {"text": "Grafana Alert System"}
        }]
    }')

if [ "$TEST_RESULT" = "204" ] || [ "$TEST_RESULT" = "200" ]; then
    echo "Test message sent successfully!"
else
    echo "Warning: Webhook returned HTTP $TEST_RESULT"
    echo "Check your Discord channel for the message"
fi

# Save configuration
echo ""
echo "Step 3: Saving configuration..."

ENV_FILE="${HOME}/.env.trading"

# Backup existing
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "${ENV_FILE}.bak"
fi

# Update or add vars
if [ -f "$ENV_FILE" ]; then
    # Remove old entries
    sed -i '/DISCORD_WEBHOOK_URL/d' "$ENV_FILE"
    sed -i '/TELEGRAM_/d' "$ENV_FILE"  # Clean up old Telegram config
fi

# Add new entries
echo "" >> "$ENV_FILE"
echo "# Discord Alert Webhook (configured $(date +%Y-%m-%d))" >> "$ENV_FILE"
echo "DISCORD_WEBHOOK_URL=$WEBHOOK_URL" >> "$ENV_FILE"

echo "Configuration saved to $ENV_FILE"

# Export for current session
export DISCORD_WEBHOOK_URL="$WEBHOOK_URL"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To use in Grafana:"
echo "  1. Add to docker-compose.yml environment:"
echo "     DISCORD_WEBHOOK_URL: \${DISCORD_WEBHOOK_URL}"
echo ""
echo "  2. Or source the env file:"
echo "     source $ENV_FILE"
echo ""
echo "  3. Restart Grafana to pick up contact points"
echo ""
echo "Your trading alerts will now be sent to Discord!"
