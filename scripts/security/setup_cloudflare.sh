#!/bin/bash
# ============================================================================
# Cloudflare Tunnel & Access Setup Script
# ============================================================================
#
# This script helps configure Cloudflare Tunnel and Access for secure
# remote access to monitoring services.
#
# Prerequisites:
#   - cloudflared CLI installed
#   - Cloudflare account with princyx.xyz domain
#   - Tunnel already created (n8n-tunnel)
#
# Usage:
#   ./setup_cloudflare.sh [dns|access|validate|restart]
#
# ============================================================================

set -euo pipefail

# Configuration
DOMAIN="princyx.xyz"
TUNNEL_NAME="n8n-tunnel"
TUNNEL_ID="4362fe6d-ea1a-4260-941e-609d69d2456f"

# Services to expose
declare -A SERVICES=(
    ["grafana"]="3000"
    ["questdb"]="9000"
    ["prometheus"]="9090"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================================
# DNS Record Setup
# ============================================================================
setup_dns() {
    log_info "Setting up DNS records for Cloudflare Tunnel..."

    for service in "${!SERVICES[@]}"; do
        hostname="${service}.${DOMAIN}"
        log_info "Creating CNAME for ${hostname} -> ${TUNNEL_ID}.cfargotunnel.com"

        # Note: This requires cloudflared tunnel route dns command
        # or manual setup in Cloudflare dashboard
        cloudflared tunnel route dns "${TUNNEL_NAME}" "${hostname}" 2>/dev/null || {
            log_warn "DNS record for ${hostname} may already exist or requires manual setup"
            log_info "Manual: Add CNAME ${hostname} -> ${TUNNEL_ID}.cfargotunnel.com"
        }
    done

    log_info "DNS setup complete. Records may take up to 5 minutes to propagate."
}

# ============================================================================
# Cloudflare Access Policies (Manual Instructions)
# ============================================================================
setup_access() {
    log_info "Cloudflare Access Setup Instructions"
    echo ""
    echo "=============================================="
    echo "  CLOUDFLARE ACCESS POLICY SETUP (MANUAL)    "
    echo "=============================================="
    echo ""
    echo "Go to: https://one.dash.cloudflare.com/"
    echo "Navigate to: Access > Applications"
    echo ""
    echo "Create a new Self-hosted Application for each service:"
    echo ""

    for service in "${!SERVICES[@]}"; do
        hostname="${service}.${DOMAIN}"
        echo "  ${service^} Dashboard:"
        echo "    - Application name: ${service^} Monitoring"
        echo "    - Application domain: ${hostname}"
        echo "    - Session duration: 24 hours"
        echo "    - Policy name: Allow Owner"
        echo "    - Policy action: Allow"
        echo "    - Include: Emails ending in @princyx.xyz OR specific email"
        echo ""
    done

    echo "Recommended Access Policy:"
    echo "  - Require: Email (your email address)"
    echo "  - OR: Identity Provider (Google/GitHub)"
    echo "  - Enable: Purpose justification (optional)"
    echo ""
    echo "=============================================="
}

# ============================================================================
# Validate Configuration
# ============================================================================
validate() {
    log_info "Validating Cloudflare Tunnel configuration..."

    # Check config file
    if [[ -f ~/.cloudflared/config.yml ]]; then
        log_info "Config file exists: ~/.cloudflared/config.yml"

        # Validate YAML
        if command -v yq &> /dev/null; then
            yq eval '.' ~/.cloudflared/config.yml > /dev/null 2>&1 && \
                log_info "Config YAML is valid" || \
                log_error "Config YAML is invalid"
        fi
    else
        log_error "Config file not found: ~/.cloudflared/config.yml"
        return 1
    fi

    # Check credentials
    if [[ -f ~/.cloudflared/${TUNNEL_ID}.json ]]; then
        log_info "Credentials file exists"
    else
        log_error "Credentials file not found"
        return 1
    fi

    # Check tunnel status
    log_info "Checking tunnel status..."
    cloudflared tunnel info "${TUNNEL_NAME}" 2>/dev/null || {
        log_warn "Could not get tunnel info (may require login)"
    }

    # Test local services
    log_info "Testing local service availability..."
    for service in "${!SERVICES[@]}"; do
        port="${SERVICES[$service]}"
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}" | grep -q "200\|302\|401"; then
            log_info "  ${service} (port ${port}): RUNNING"
        else
            log_warn "  ${service} (port ${port}): NOT RESPONDING"
        fi
    done

    log_info "Validation complete"
}

# ============================================================================
# Restart Tunnel
# ============================================================================
restart_tunnel() {
    log_info "Restarting Cloudflare Tunnel..."

    # Check if running as systemd service
    if systemctl is-active --quiet cloudflared 2>/dev/null; then
        log_info "Restarting cloudflared systemd service..."
        sudo systemctl restart cloudflared
        sleep 3
        systemctl status cloudflared --no-pager
    else
        # Manual restart
        log_info "Stopping any existing tunnel processes..."
        pkill -f "cloudflared tunnel" 2>/dev/null || true

        log_info "Starting tunnel in background..."
        nohup cloudflared tunnel run "${TUNNEL_NAME}" > /tmp/cloudflared.log 2>&1 &

        sleep 3
        if pgrep -f "cloudflared tunnel" > /dev/null; then
            log_info "Tunnel started successfully (PID: $(pgrep -f 'cloudflared tunnel'))"
        else
            log_error "Failed to start tunnel. Check /tmp/cloudflared.log"
            return 1
        fi
    fi
}

# ============================================================================
# Install as systemd service
# ============================================================================
install_service() {
    log_info "Installing cloudflared as systemd service..."

    sudo cloudflared service install 2>/dev/null || {
        log_warn "Service may already be installed"
    }

    # Copy config to system location
    sudo cp ~/.cloudflared/config.yml /etc/cloudflared/config.yml 2>/dev/null || {
        log_info "Creating /etc/cloudflared directory..."
        sudo mkdir -p /etc/cloudflared
        sudo cp ~/.cloudflared/config.yml /etc/cloudflared/config.yml
        sudo cp ~/.cloudflared/${TUNNEL_ID}.json /etc/cloudflared/${TUNNEL_ID}.json
    }

    # Update credentials path in system config
    sudo sed -i "s|/home/sam/.cloudflared|/etc/cloudflared|g" /etc/cloudflared/config.yml

    sudo systemctl enable cloudflared
    sudo systemctl start cloudflared

    log_info "Service installed and started"
}

# ============================================================================
# Main
# ============================================================================
main() {
    case "${1:-help}" in
        dns)
            setup_dns
            ;;
        access)
            setup_access
            ;;
        validate)
            validate
            ;;
        restart)
            restart_tunnel
            ;;
        install)
            install_service
            ;;
        all)
            validate
            setup_dns
            restart_tunnel
            setup_access
            ;;
        *)
            echo "Usage: $0 {dns|access|validate|restart|install|all}"
            echo ""
            echo "Commands:"
            echo "  dns       - Setup DNS records for tunnel"
            echo "  access    - Show Cloudflare Access setup instructions"
            echo "  validate  - Validate current configuration"
            echo "  restart   - Restart the tunnel"
            echo "  install   - Install as systemd service"
            echo "  all       - Run all setup steps"
            ;;
    esac
}

main "$@"
