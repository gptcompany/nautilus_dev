# Post-Mortem: [INCIDENT TITLE]

**Incident ID**: INC-YYYY-NNN
**Post-Mortem Date**: YYYY-MM-DD
**Incident Date**: YYYY-MM-DD
**Author**: [Name]
**Attendees**: [Names]

## Executive Summary

[2-3 sentence summary for executives: what happened, impact, key actions]

## Incident Recap

### What Happened

[Detailed narrative of the incident from start to finish]

### Impact Assessment

| Metric | Value |
|--------|-------|
| Duration | X hours |
| Financial Loss | $X |
| Strategies Affected | N |
| Trades Missed | N |
| SLA Breach | Yes/No |

### Severity Justification

[Why this incident was classified at its severity level]

## Technical Analysis

### Root Cause

[Deep technical explanation of the root cause]

### Contributing Factors

1. **Factor 1**: [Description and why it contributed]
2. **Factor 2**: [Description and why it contributed]
3. **Factor 3**: [Description and why it contributed]

### Trigger

[What specific event or change triggered the incident]

## Timeline (Detailed)

```
YYYY-MM-DD HH:MM:SS UTC - Event description
YYYY-MM-DD HH:MM:SS UTC - Event description
...
```

## Response Analysis

### Detection

- **Time to Detect (TTD)**: X minutes
- **Detection Method**: [How was it detected]
- **Why wasn't it detected earlier**: [Explanation]

### Response

- **Time to Respond (TTR)**: X minutes
- **Time to Mitigate (TTM)**: X minutes
- **Time to Resolve (TTRES)**: X minutes

### Response Effectiveness

| Aspect | Rating | Notes |
|--------|--------|-------|
| Communication | Good/Fair/Poor | |
| Coordination | Good/Fair/Poor | |
| Technical Response | Good/Fair/Poor | |
| Decision Making | Good/Fair/Poor | |

## What Went Well

1. [Positive aspect of response]
2. [Positive aspect of response]
3. [Positive aspect of response]

## What Went Wrong

1. [Issue during response]
2. [Issue during response]
3. [Issue during response]

## Action Items

### Immediate (P0 - This Week)

| # | Action | Owner | Due Date | Status |
|---|--------|-------|----------|--------|
| 1 | [Action] | [Name] | YYYY-MM-DD | Open |
| 2 | [Action] | [Name] | YYYY-MM-DD | Open |

### Short-term (P1 - This Month)

| # | Action | Owner | Due Date | Status |
|---|--------|-------|----------|--------|
| 1 | [Action] | [Name] | YYYY-MM-DD | Open |
| 2 | [Action] | [Name] | YYYY-MM-DD | Open |

### Long-term (P2 - This Quarter)

| # | Action | Owner | Due Date | Status |
|---|--------|-------|----------|--------|
| 1 | [Action] | [Name] | YYYY-MM-DD | Open |
| 2 | [Action] | [Name] | YYYY-MM-DD | Open |

## Blameless Analysis

### System Failures (Not People Failures)

[Analysis of what systemic issues allowed this to happen]

### Process Gaps

[What processes were missing or inadequate]

### Knowledge Gaps

[What knowledge was missing that could have prevented or shortened the incident]

## Monitoring & Alerting Improvements

### New Alerts Needed

- [ ] [Alert description and threshold]
- [ ] [Alert description and threshold]

### Alert Tuning Needed

- [ ] [Alert to tune and why]
- [ ] [Alert to tune and why]

### Dashboard Updates

- [ ] [Dashboard change needed]
- [ ] [Dashboard change needed]

## Documentation Updates

- [ ] Runbook: [Which runbook needs updating]
- [ ] Architecture: [Which docs need updating]
- [ ] Training: [Training materials needed]

## Similar Past Incidents

| ID | Date | Similarity | Lessons Applied |
|----|------|------------|-----------------|
| INC-XXX | YYYY-MM-DD | [How similar] | Yes/No |

## Appendix

### Supporting Evidence

[Links to logs, screenshots, metrics]

### Related PRs/Commits

- [PR/Commit link]: [Description]
- [PR/Commit link]: [Description]

---

**Post-Mortem Status**: Draft | In Review | Approved | Closed
**Next Review Date**: YYYY-MM-DD
