# Runbook: Emergency Rollback

## Overview

Procedure for reverting to a previous known-good state.

**Target Time**: < 5 minutes from decision to rollback complete.

## When to Rollback

- Unexpected errors in production logs
- P&L anomalies
- API connection failures after deploy
- Any doubt about system stability

**Rule**: When in doubt, rollback first, investigate later.

## Quick Rollback (< 5 min)

### Step 1: Stop Trading (30 sec)

```bash
# Emergency stop - closes all positions immediately
./scripts/emergency_stop.sh

# Verify stopped
pgrep -f trading_node && echo "STILL RUNNING" || echo "Stopped"
```

### Step 2: Rollback Code (1 min)

```bash
# Find last known-good tag
git tag -l "deploy-*" | tail -5

# Rollback to previous deploy
./scripts/rollback.sh

# Or manually:
git checkout deploy-YYYYMMDD-HHMMSS
```

### Step 3: Restart Services (2 min)

```bash
# Start with previous version
./scripts/start.sh

# Health check
./scripts/health_check.sh
```

### Step 4: Verify (1 min)

```bash
# Check version
git log -1 --oneline

# Check logs
tail -20 logs/trading.log

# Check metrics
curl http://localhost:9000/status
```

## Detailed Rollback Script

The `scripts/rollback.sh` script automates these steps:

```bash
#!/bin/bash
# Usage: ./scripts/rollback.sh [TAG]
# If no TAG provided, rolls back to previous deploy tag

set -e

TAG=${1:-$(git tag -l "deploy-*" | sort -r | sed -n '2p')}

if [ -z "$TAG" ]; then
    echo "ERROR: No rollback target found"
    exit 1
fi

echo "Rolling back to: $TAG"

# Stop services
./scripts/shutdown.sh force

# Checkout previous version
git checkout "$TAG"

# Restore config if backed up
if [ -d "/backup/config-${TAG#deploy-}" ]; then
    cp -r "/backup/config-${TAG#deploy-}/" config/
fi

# Start services
./scripts/start.sh

echo "Rollback complete to $TAG"
```

## Database Rollback

If database changes need reverting:

```bash
# Stop services first
./scripts/shutdown.sh force

# Restore database backup
docker exec questdb psql -f /backup/pre-deploy.sql

# Start services
./scripts/start.sh
```

## Post-Rollback

1. **Document**: Create incident report
2. **Investigate**: What went wrong?
3. **Fix**: Address root cause
4. **Test**: Verify fix in staging
5. **Redeploy**: Follow normal deploy process

## Rollback Decision Tree

```
Error detected
     │
     ▼
Is trading active?
     │
   Yes ──► Emergency stop first
     │
     ▼
Is data at risk?
     │
   Yes ──► Backup current state
     │
     ▼
Rollback to previous version
     │
     ▼
Verify system health
     │
     ▼
Create incident report
```

## Contact During Incident

- Pause all non-essential work
- Focus on recovery
- Document everything
- Post-mortem within 24 hours
