# Incident Management

This directory contains incident reports and post-mortems for the trading system.

## Severity Levels

| Level | Name | Description | Response Time |
|-------|------|-------------|---------------|
| P1 | Critical | Trading halted, significant financial loss | Immediate |
| P2 | High | Degraded trading, potential loss | < 15 min |
| P3 | Medium | Minor impact, workaround available | < 1 hour |
| P4 | Low | No trading impact | Next business day |

## Templates

- [TEMPLATE-incident.md](TEMPLATE-incident.md) - Initial incident report
- [TEMPLATE-postmortem.md](TEMPLATE-postmortem.md) - Detailed post-mortem analysis

## Creating a New Incident

1. Copy `TEMPLATE-incident.md` to `INC-YYYY-NNN.md`
2. Fill in initial details as incident unfolds
3. Update status as situation changes
4. After resolution, create post-mortem using `TEMPLATE-postmortem.md`

## Incident Log

| ID | Date | Severity | Title | Status |
|----|------|----------|-------|--------|
| - | - | - | No incidents recorded yet | - |

## Metrics Targets

| Metric | Target | Description |
|--------|--------|-------------|
| MTTR | < 30 min | Mean Time To Resolve (P1/P2) |
| TTD | < 5 min | Time To Detect |
| Incident Rate | < 2/month | P1+P2 incidents per month |
| Post-mortem Rate | 100% | All P1/P2 have post-mortem |

## Quick Response Guide

### P1 - Critical

1. **Alert** team via Discord @everyone
2. **Stop** trading if necessary (`./scripts/emergency-stop.sh`)
3. **Assess** impact and root cause
4. **Mitigate** - apply quickest fix
5. **Communicate** updates every 15 min
6. **Resolve** and restore service
7. **Document** in incident report

### P2 - High

1. **Alert** team via Discord
2. **Assess** impact scope
3. **Decide** whether to halt affected strategies
4. **Investigate** root cause
5. **Fix** and verify
6. **Document** in incident report

## Contact

- **Primary On-Call**: [Configure in PagerDuty/OpsGenie]
- **Escalation**: See [runbooks/incident-response.md](../runbooks/incident-response.md)
