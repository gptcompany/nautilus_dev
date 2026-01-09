# Recovery Runbook

> Emergency procedures for trading system recovery

## Quick Reference

| Situation | Action | Time |
|-----------|--------|------|
| Strategy crash | Restart strategy container | < 1 min |
| Database connection lost | Reconnect or restart | < 2 min |
| Exchange disconnection | Auto-reconnect (3x) | < 30 sec |
| Full system failure | Execute full rollback | < 5 min |
| Max drawdown breach | Kill switch activates | Immediate |

## Emergency Contacts

| Role | Contact | When |
|------|---------|------|
| On-call | [Your contact] | Any incident |
| Exchange support | [Exchange contact] | API issues |
| Infrastructure | [Infra contact] | Server issues |

---

## 1. Strategy Crash Recovery

### Symptoms
- Strategy container stopped
- No new orders being placed
- Position not being managed

### Steps

```bash
# 1. Check container status
docker-compose -f docker-compose.staging.yml ps

# 2. Check logs for error
docker-compose -f docker-compose.staging.yml logs --tail=100 strategy

# 3. Restart strategy
docker-compose -f docker-compose.staging.yml restart strategy

# 4. Verify positions reconciled
# Check Grafana positions dashboard
```

### Post-Recovery
- [ ] Review error logs
- [ ] Check if positions reconciled correctly
- [ ] Verify no duplicate orders created
- [ ] Create incident report if significant

---

## 2. Database Connection Lost

### Symptoms
- "Connection refused" errors in logs
- No new data in dashboards
- Metrics not updating

### Steps

```bash
# 1. Check QuestDB status
docker-compose -f docker-compose.staging.yml ps questdb
curl http://localhost:9000/health

# 2. If down, restart
docker-compose -f docker-compose.staging.yml restart questdb

# 3. Verify data flow
curl "http://localhost:9000/exec?query=SELECT%20count()%20FROM%20trading_pnl"

# 4. If data lost, check backups
ls -la /var/lib/questdb/db/
```

### Data Recovery
```bash
# QuestDB WAL recovery (if needed)
docker exec questdb-staging questdb repair
```

---

## 3. Exchange Disconnection

### Symptoms
- WebSocket connection errors
- Order submissions failing
- Price data stale

### Steps

```bash
# 1. Check exchange status page
# Binance: https://www.binance.com/en/trade/BTC_USDT (check status)
# Bybit: https://www.bybit.com/en-US/ (check status)

# 2. Strategy should auto-reconnect (3 attempts)
# Check logs for reconnection attempts
docker-compose logs --tail=50 strategy | grep -i "reconnect\|connection"

# 3. If auto-reconnect fails, manual restart
docker-compose restart strategy

# 4. Verify connection restored
# Check for new price data in dashboards
```

### If Exchange is Down
1. Wait for exchange recovery
2. Do NOT force orders through backup exchange
3. Close positions manually via exchange UI if critical
4. Document all manual actions

---

## 4. Full System Rollback

### When to Use
- Major bug deployed to production
- System unstable after update
- Data corruption detected

### Steps

```bash
# 1. Stop all trading immediately
docker-compose -f docker-compose.staging.yml stop strategy

# 2. Execute rollback script
./scripts/rollback.sh --to <TIMESTAMP>

# 3. Verify rollback
git log -1  # Should show previous commit
docker-compose ps  # Should show healthy containers

# 4. Restart with previous version
docker-compose -f docker-compose.staging.yml up -d

# 5. Verify system health
curl http://localhost:9000/health
curl http://localhost:3001/api/health
```

### Post-Rollback
- [ ] Verify positions are correct
- [ ] Check no orphaned orders
- [ ] Review what caused the issue
- [ ] Plan fix before next deployment

---

## 5. Kill Switch Activated

### What Happened
- Drawdown exceeded 15% (KILL_SWITCH_DRAWDOWN)
- System automatically stopped trading
- All positions should remain (not auto-closed)

### Steps

```bash
# 1. Verify kill switch state
docker-compose logs strategy | grep -i "kill switch\|drawdown"

# 2. Review current positions
# Check Grafana positions dashboard

# 3. Decide: close positions or wait?
# If closing manually:
# - Use exchange UI
# - Document all manual trades

# 4. Reset kill switch (requires manual confirmation)
# Edit strategy config to reset, then restart
```

### Recovery Criteria
- [ ] Understand why drawdown occurred
- [ ] Market conditions normalized
- [ ] Risk parameters reviewed
- [ ] Management approval (if applicable)

---

## 6. Position State Mismatch

### Symptoms
- Dashboard shows different position than exchange
- Reconciliation errors in logs
- P&L doesn't match expected

### Steps

```bash
# 1. Get exchange position (via API or UI)
# Document: instrument, quantity, side, avg_price

# 2. Get system position
curl "http://localhost:9000/exec?query=SELECT%20*%20FROM%20positions%20WHERE%20quantity%20!=%200"

# 3. If mismatch:
# a. Trust exchange as source of truth
# b. Update system state manually if needed
# c. Restart strategy with reconciliation enabled

# 4. Verify reconciliation
docker-compose logs strategy | grep -i "reconcil"
```

---

## Incident Report Template

After any significant incident:

```markdown
## Incident Report: [TITLE]

**Date**: YYYY-MM-DD HH:MM UTC
**Duration**: X minutes
**Severity**: Critical/High/Medium/Low

### Summary
Brief description of what happened.

### Timeline
- HH:MM - First alert
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Recovery action taken
- HH:MM - System restored

### Root Cause
What caused the incident.

### Impact
- Trading: X minutes of downtime
- Financial: $X impact (if any)
- Data: Any data loss

### Resolution
What was done to fix it.

### Prevention
What changes to prevent recurrence:
- [ ] Action item 1
- [ ] Action item 2

### Lessons Learned
What we learned from this incident.
```

---

## Useful Commands

```bash
# Check all container health
docker-compose ps

# View recent logs
docker-compose logs --tail=100 --follow

# Check resource usage
docker stats

# Emergency stop all trading
docker-compose stop strategy

# Full restart
docker-compose down && docker-compose up -d

# Check Grafana alerts
curl http://localhost:3001/api/v1/alerts

# Manual QuestDB query
curl "http://localhost:9000/exec?query=SELECT%20*%20FROM%20trading_pnl%20LIMIT%2010"
```
