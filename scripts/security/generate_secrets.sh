#!/bin/bash
# Security: Generate cryptographically secure secrets
# Usage: ./generate_secrets.sh [--output .env.secrets]

set -euo pipefail

OUTPUT_FILE="${1:-.env.secrets}"

echo "Generating secure secrets..."
echo ""

# Generate secrets
JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d '\n' | head -c 32)
WEBSOCKET_SECRET_KEY=$(openssl rand -base64 48 | tr -d '\n')
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d '\n' | head -c 32)
API_SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')

# Output to file
cat > "$OUTPUT_FILE" << EOF
# Generated secrets - $(date -Iseconds)
# NEVER commit this file to git!

# JWT Authentication
JWT_SECRET=$JWT_SECRET

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD

# WebSocket
WEBSOCKET_SECRET_KEY=$WEBSOCKET_SECRET_KEY

# Redis (if using password auth)
REDIS_PASSWORD=$REDIS_PASSWORD

# API
API_SECRET_KEY=$API_SECRET_KEY
EOF

chmod 600 "$OUTPUT_FILE"

echo "Secrets generated and saved to: $OUTPUT_FILE"
echo "File permissions set to 600 (owner read/write only)"
echo ""
echo "To use these secrets:"
echo "  1. Copy relevant values to your .env file"
echo "  2. Or source directly: source $OUTPUT_FILE"
echo ""
echo "IMPORTANT: Add '$OUTPUT_FILE' to .gitignore!"
