# On-Call Procedures

## Overview

This runbook defines on-call responsibilities and escalation procedures for the NautilusTrader trading system.

## Shift Schedule

| Shift | Hours (UTC) | Coverage |
|-------|-------------|----------|
| Day | 08:00-16:00 | Primary |
| Evening | 16:00-00:00 | Primary |
| Night | 00:00-08:00 | On-call (pager) |
| Weekend | All day | On-call rotation |

## Alert Severity Levels

### P1 - Critical (Immediate Response)
- **Response Time**: < 5 minutes
- **Examples**:
  - Kill switch triggered (drawdown > 15%)
  - Position reconciliation failure
  - Complete system outage
  - Exchange connection lost during open positions
- **Actions**:
  1. Acknowledge alert
  2. Check Grafana dashboards
  3. Execute emergency stop if needed
  4. Escalate to team lead

### P2 - High (15 min Response)
- **Response Time**: < 15 minutes
- **Examples**:
  - Drawdown > 10% warning
  - Order execution latency > 5s
  - Error rate > 1%
  - Failed strategy restart
- **Actions**:
  1. Acknowledge alert
  2. Review Sentry errors
  3. Check strategy logs
  4. Determine if trading should pause

### P3 - Medium (1 hour Response)
- **Response Time**: < 1 hour
- **Examples**:
  - Drawdown > 5% warning
  - Data feed delays
  - Memory usage > 80%
  - Disk space warnings
- **Actions**:
  1. Acknowledge alert
  2. Monitor trend
  3. Plan remediation

### P4 - Low (Next Business Day)
- **Response Time**: Next business day
- **Examples**:
  - Non-critical test failures
  - Documentation drift
  - Dependency updates available
- **Actions**:
  1. Create ticket
  2. Schedule for next sprint

## Quick Commands

### Check System Status
```bash
# System health
docker-compose ps
curl localhost:9000/exec?query=SELECT%201  # QuestDB
curl localhost:3001/api/health              # Grafana

# Trading status
tail -100 /var/log/nautilus/trading.log
redis-cli INFO replication
```

### Emergency Stop
```bash
# Graceful shutdown (preferred)
./scripts/graceful_shutdown.sh

# Hard stop (if graceful fails)
docker-compose down --timeout 30

# Kill all positions (LAST RESORT)
python scripts/emergency_close_positions.py
```

### Restart Services
```bash
# Single service
docker-compose restart trading-node

# Full stack
docker-compose down && docker-compose up -d

# With clean state
docker-compose down -v && docker-compose up -d
```

## Escalation Matrix

| Severity | First | Escalate After | To |
|----------|-------|----------------|-----|
| P1 | On-call | 5 min | Team Lead |
| P2 | On-call | 30 min | Team Lead |
| P3 | On-call | 4 hours | Team |
| P4 | Ticket | N/A | Sprint Planning |

## Communication Channels

| Channel | Use For |
|---------|---------|
| Discord #alerts | Automated alerts |
| Discord #trading-ops | Incident discussion |
| Phone | P1 escalation |
| Email | Post-incident reports |

## Handoff Checklist

When handing off to next on-call:

- [ ] Review open incidents
- [ ] Check pending alerts
- [ ] Verify all systems green
- [ ] Note any unusual patterns
- [ ] Update on-call calendar

## Post-Incident

After any P1/P2 incident:

1. Create incident report in `docs/incidents/`
2. Schedule post-mortem (within 48h)
3. Update runbooks with lessons learned
4. Create tickets for preventive measures

## Contacts

| Role | Contact | Backup |
|------|---------|--------|
| Team Lead | [TBD] | [TBD] |
| Platform | [TBD] | [TBD] |
| Exchange Issues | Exchange support | N/A |

---

*Last Updated: 2026-01-08*
*Spec: 040-dev-excellence*
