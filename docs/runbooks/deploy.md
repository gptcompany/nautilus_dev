# Runbook: Production Deployment

## Overview

Step-by-step procedure for deploying changes to production trading system.

**CRITICAL**: This system handles REAL MONEY. Follow every step.

## Pre-Deployment Checklist

- [ ] CI/CD pipeline passed (all 6 stages green)
- [ ] Code review completed
- [ ] No CRITICAL/HIGH security issues
- [ ] Test coverage > 90% for critical modules
- [ ] Changelog updated
- [ ] ADR written for major changes

## Deployment Steps

### 1. Create Checkpoint

```bash
# Capture current state
./scripts/checkpoint.sh "pre-deploy-$(date +%Y%m%d-%H%M%S)"
```

### 2. Verify Trading State

```bash
# Check no open positions (or document them)
python scripts/check_positions.py

# If positions open:
# - Document in deployment notes
# - Consider waiting for flat state
```

### 3. Stop Trading Services

```bash
# Graceful shutdown (completes pending orders)
./scripts/shutdown.sh graceful

# Wait for confirmation
# Expected: "All positions closed, shutdown complete"
```

### 4. Backup Current State

```bash
# Database backup
docker exec questdb /bin/bash -c "pg_dump > /backup/pre-deploy.sql"

# Config backup
cp -r config/ /backup/config-$(date +%Y%m%d)/
```

### 5. Deploy New Version

```bash
# Pull latest (already passed CI/CD)
git fetch origin main
git checkout main
git pull

# Verify version
git log -1 --oneline
```

### 6. Run Migrations (if any)

```bash
# Check for migrations
ls migrations/pending/

# Run if present
python scripts/run_migrations.py
```

### 7. Start Services

```bash
# Start in paper mode first
PAPER_MODE=true ./scripts/start.sh

# Verify health
./scripts/health_check.sh

# If healthy, switch to live
PAPER_MODE=false ./scripts/start.sh
```

### 8. Post-Deployment Verification

```bash
# Check logs for errors
tail -f logs/trading.log | grep -i error

# Verify metrics flowing
curl http://localhost:9000/status

# Verify Grafana dashboards
# Open: http://localhost:3000/d/trading
```

## Rollback Procedure

If anything goes wrong:

```bash
# Immediate rollback
./scripts/rollback.sh

# See: docs/runbooks/rollback.md
```

## Emergency Contacts

| Role | Contact | When |
|------|---------|------|
| Primary | [Your contact] | First escalation |
| Exchange Support | [Exchange contact] | API issues |

## Post-Deployment

- [ ] Monitor for 30 minutes
- [x] Check error rates in Sentry (auto: GitHub release tracking)
- [ ] Verify P&L tracking
- [ ] Update deployment log
