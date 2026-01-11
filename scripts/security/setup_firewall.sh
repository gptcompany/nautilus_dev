#!/bin/bash
# ============================================================================
# UFW Firewall Setup Script
# ============================================================================
#
# Configures UFW firewall with restrictive rules for trading system.
# IMPORTANT: Run with sudo
#
# Usage:
#   sudo ./setup_firewall.sh [apply|status|reset]
#
# ============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (sudo)"
    exit 1
fi

# ============================================================================
# Firewall Rules
# ============================================================================
apply_rules() {
    log_info "Applying UFW firewall rules..."

    # Reset to default (deny incoming, allow outgoing)
    ufw default deny incoming
    ufw default allow outgoing

    # SSH - REQUIRED for remote access
    log_info "Allowing SSH (port 22)..."
    ufw allow ssh

    # HTTP/HTTPS - Only if running public web services
    # Uncomment if needed:
    # ufw allow 80/tcp
    # ufw allow 443/tcp

    # Cloudflare Tunnel - No inbound rules needed (outbound only)
    # Tunnel connects outbound to Cloudflare

    # Docker internal network - Allow localhost only
    # Services should bind to 127.0.0.1, not 0.0.0.0

    # Rate limiting for SSH (brute force protection)
    log_info "Adding SSH rate limiting..."
    ufw limit ssh/tcp comment 'Rate limit SSH'

    # Block common attack ports
    log_info "Blocking common attack vectors..."

    # Block Telnet
    ufw deny 23/tcp comment 'Block Telnet'

    # Block SMB/NetBIOS (common ransomware vector)
    ufw deny 135/tcp comment 'Block RPC'
    ufw deny 137/udp comment 'Block NetBIOS'
    ufw deny 138/udp comment 'Block NetBIOS'
    ufw deny 139/tcp comment 'Block NetBIOS'
    ufw deny 445/tcp comment 'Block SMB'

    # Block common database ports from external access
    # (Should be localhost only anyway, but defense in depth)
    ufw deny 3306/tcp comment 'Block MySQL external'
    ufw deny 5432/tcp comment 'Block PostgreSQL external'
    ufw deny 27017/tcp comment 'Block MongoDB external'
    ufw deny 6379/tcp comment 'Block Redis external'
    ufw deny 7687/tcp comment 'Block Neo4j external'

    # Allow local Docker network
    # Docker creates its own iptables rules, but ensure localhost works
    ufw allow from 127.0.0.1 comment 'Allow localhost'
    ufw allow from 172.16.0.0/12 comment 'Allow Docker networks'

    # Logging
    log_info "Enabling logging..."
    ufw logging medium

    # Enable firewall
    log_info "Enabling UFW..."
    echo "y" | ufw enable

    log_info "Firewall rules applied successfully!"
    ufw status verbose
}

# ============================================================================
# Status
# ============================================================================
show_status() {
    log_info "Current UFW status:"
    ufw status verbose

    echo ""
    log_info "Numbered rules:"
    ufw status numbered
}

# ============================================================================
# Reset
# ============================================================================
reset_firewall() {
    log_warn "This will reset ALL firewall rules!"
    read -p "Are you sure? (y/N): " confirm

    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        ufw disable
        ufw reset
        log_info "Firewall reset complete"
    else
        log_info "Reset cancelled"
    fi
}

# ============================================================================
# Trading-specific rules (optional hardening)
# ============================================================================
apply_trading_rules() {
    log_info "Applying trading-specific hardening..."

    # Block outbound to known bad actors (example - customize as needed)
    # ufw deny out to 185.220.0.0/16 comment 'Block known bad range'

    # Rate limit outbound connections (prevent runaway bots)
    # This requires iptables directly, UFW doesn't support this well

    # Log all denied packets
    ufw logging high

    log_info "Trading hardening applied"
}

# ============================================================================
# Verification
# ============================================================================
verify_rules() {
    log_info "Verifying firewall configuration..."

    # Check UFW is active
    if ufw status | grep -q "Status: active"; then
        log_info "✓ UFW is active"
    else
        log_error "✗ UFW is not active"
        return 1
    fi

    # Check default policies
    if ufw status verbose | grep -q "Default: deny (incoming)"; then
        log_info "✓ Default incoming: deny"
    else
        log_warn "✗ Default incoming policy may be permissive"
    fi

    # Check SSH is allowed
    if ufw status | grep -q "22/tcp"; then
        log_info "✓ SSH (22) is allowed"
    else
        log_error "✗ SSH may be blocked - you could lose access!"
    fi

    # Check dangerous ports are blocked
    for port in 23 445 6379; do
        if ufw status | grep -q "${port}.*DENY"; then
            log_info "✓ Port ${port} is blocked"
        fi
    done

    log_info "Verification complete"
}

# ============================================================================
# Main
# ============================================================================
main() {
    case "${1:-help}" in
        apply)
            apply_rules
            verify_rules
            ;;
        status)
            show_status
            ;;
        reset)
            reset_firewall
            ;;
        verify)
            verify_rules
            ;;
        trading)
            apply_trading_rules
            ;;
        *)
            echo "Usage: sudo $0 {apply|status|reset|verify|trading}"
            echo ""
            echo "Commands:"
            echo "  apply    - Apply recommended firewall rules"
            echo "  status   - Show current firewall status"
            echo "  reset    - Reset all firewall rules (DANGEROUS)"
            echo "  verify   - Verify firewall configuration"
            echo "  trading  - Apply additional trading hardening"
            echo ""
            echo "WARNING: Always ensure SSH is allowed before enabling!"
            ;;
    esac
}

main "$@"
