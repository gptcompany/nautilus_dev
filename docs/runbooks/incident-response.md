# Runbook: Incident Response

## Severity Levels

| Level | Description | Response Time | Examples |
|-------|-------------|---------------|----------|
| **SEV1** | Trading halted, money at risk | < 5 min | Kill switch triggered, positions stuck |
| **SEV2** | Degraded performance | < 30 min | High latency, partial failures |
| **SEV3** | Minor issues | < 4 hours | Non-critical errors, cosmetic bugs |

## Incident Response Steps

### 1. Detect & Triage (2 min)

- Acknowledge alert
- Determine severity
- Start incident timer

```bash
# Quick status check
./scripts/health_check.sh
tail -50 logs/trading.log | grep -E "(ERROR|CRITICAL)"
```

### 2. Communicate (1 min)

For SEV1/SEV2:
- Update status page (if any)
- Notify stakeholders

### 3. Mitigate (varies)

**SEV1**: Stop the bleeding first

```bash
# Option A: Emergency stop all trading
./scripts/emergency_stop.sh

# Option B: Kill switch specific strategy
./scripts/kill_strategy.sh <strategy_id>

# Option C: Full rollback
./scripts/rollback.sh
```

**SEV2**: Targeted fix

```bash
# Identify affected component
grep -r "ERROR" logs/ | cut -d: -f1 | sort | uniq -c

# Restart specific service
docker restart <service_name>
```

### 4. Investigate (ongoing)

- Collect logs
- Check metrics
- Identify root cause

```bash
# Export logs for analysis
./scripts/export_logs.sh incident-$(date +%Y%m%d)

# Check recent changes
git log --oneline -20

# Check external factors
# - Exchange status
# - Network issues
# - Market events
```

### 5. Resolve

- Apply fix
- Verify fix works
- Resume normal operations

### 6. Document

Create post-mortem in `docs/incidents/`:

```markdown
# Incident: YYYY-MM-DD - Brief Description

## Summary
One-line summary of what happened.

## Timeline
- HH:MM - Alert triggered
- HH:MM - Incident acknowledged
- HH:MM - Root cause identified
- HH:MM - Fix applied
- HH:MM - Normal operations resumed

## Root Cause
What actually caused the incident.

## Impact
- Duration: X minutes
- Financial impact: $X
- Positions affected: X

## Resolution
What was done to fix it.

## Lessons Learned
- What went well
- What could be improved
- Action items

## Action Items
- [ ] Item 1 (Owner, Due date)
- [ ] Item 2 (Owner, Due date)
```

## Common Incidents

### Kill Switch Triggered

1. Stop and assess - don't rush to restart
2. Check what triggered it (drawdown, error rate, manual)
3. Review recent trades
4. Fix root cause before restarting
5. Restart with reduced position sizes

### Exchange Connection Lost

1. Check exchange status page
2. Check network connectivity
3. Check API credentials still valid
4. Restart adapter
5. Monitor for reconnection

### Position Mismatch

1. Stop new orders immediately
2. Query exchange for actual positions
3. Reconcile with local state
4. Close any orphaned positions
5. Investigate cause

### Memory Exhaustion

1. Identify leaking process
2. Restart with memory limits
3. Add monitoring for early warning
4. Fix memory leak in code

## Post-Incident

- [ ] Post-mortem written within 24 hours
- [ ] Action items assigned
- [ ] Monitoring improved
- [ ] Runbook updated if needed
