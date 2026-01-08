# ADR-006: Agent Deprecation Plan

**Status**: Approved
**Date**: 2026-01-08
**Supersedes**: Individual agent configurations

## Summary

With the introduction of the Ralph Loop pattern and Task Classifier, several specialized agents become redundant. This ADR documents which agents to deprecate, which to keep, and the migration path.

## Agent Classification

### DEPRECATE (Replace with Ralph Loop)

| Agent | Reason | Ralph Equivalent |
|-------|--------|------------------|
| `alpha-debug` | Iterative bug hunting = Ralph loop | Loop until tests pass |
| `test-runner` | Mechanical test execution | Part of Ralph exit criteria |
| `tdd-guard` | TDD enforcement | Ralph exit condition (tests must pass) |

**Token Savings**: ~30-50% on mechanical tasks

### KEEP (Domain Expertise Required)

| Agent | Reason | When to Use |
|-------|--------|-------------|
| `nautilus-coder` | NT-specific knowledge (Context7, Discord) | Strategy implementation |
| `nautilus-docs-specialist` | Curated NT documentation | Documentation search |
| `nautilus-data-pipeline-operator` | Data pipeline expertise | Data ingestion |
| `nautilus-live-operator` | Live trading operations | Deployment |
| `strategy-researcher` | Paper search APIs | Research tasks |
| `grafana-expert` | Visual validation | Dashboard creation |
| `backtest-analyzer` | Log chunking strategy | Large backtest analysis |

### KEEP (Different Paradigm)

| Agent | Reason | When to Use |
|-------|--------|-------------|
| `alpha-evolve` | Parallel generation (N implementations) | Creative/architectural tasks |
| `alpha-visual` | Screenshot-based validation | UI/visualization refinement |

### CONDITIONAL (May Deprecate Later)

| Agent | Current Status | Decision Criteria |
|-------|----------------|-------------------|
| `pinescript-converter` | Keep for now | Deprecate if Ralph handles conversions well |
| `mathematician` | Keep for Wolfram API | Deprecate if rarely used |

## Migration Path

### Phase 1: Add New Hooks (Immediate)

```bash
# Add to settings.json
hooks:
  UserPromptSubmit:
    - task-classifier.py  # Routes to appropriate mode
  Stop:
    - ralph-loop.py       # Handles continuation
```

### Phase 2: Soft Deprecation (1 week)

- Keep deprecated agents functional
- Log usage to track adoption
- Show warning when deprecated agent spawned manually

```python
# In deprecated agent configs
if agent_type in DEPRECATED_AGENTS:
    log_warning(f"{agent_type} is deprecated, use Ralph mode instead")
    suggest_ralph_mode()
```

### Phase 3: Hard Deprecation (1 month)

- Remove deprecated agents from available list
- Update CLAUDE.md documentation
- Archive old agent configurations

## Updated Agent Configuration

### agents.json (After Deprecation)

```json
{
  "available_agents": {
    "ralph": {
      "description": "Autonomous loop for mechanical tasks",
      "triggers": ["fix", "refactor", "test coverage", "migrate"],
      "exit_criteria": ["tests pass", "no lint errors"]
    },
    "nautilus-coder": {
      "description": "NT strategy implementation",
      "triggers": ["strategy", "indicator", "backtest"],
      "tools": ["Context7", "Discord search"]
    },
    "alpha-evolve": {
      "description": "Multi-implementation generator",
      "triggers": ["design", "architect", "multiple approaches"],
      "generates": "N implementations with fitness evaluation"
    },
    "strategy-researcher": {
      "description": "Academic paper research",
      "triggers": ["research", "paper", "academic"],
      "apis": ["arXiv", "Google Scholar", "Semantic Scholar"]
    },
    "grafana-expert": {
      "description": "Dashboard creation and validation",
      "triggers": ["dashboard", "grafana", "visualization"],
      "tools": ["Playwright", "Chrome DevTools"]
    }
  },
  "deprecated_agents": [
    "alpha-debug",
    "test-runner",
    "tdd-guard"
  ]
}
```

## CLAUDE.md Updates

### Before (Current)

```markdown
| Agent | Use For |
|-------|---------|
| alpha-debug | Bug hunting (2-10 rounds) |
| test-runner | Test execution |
| tdd-guard | TDD enforcement |
| nautilus-coder | Strategy implementation |
...
```

### After (Post-Deprecation)

```markdown
## Execution Modes

| Mode | Triggers | Description |
|------|----------|-------------|
| Ralph Loop | fix, refactor, test coverage | Autonomous iteration until criteria met |
| Specialist | strategy, research, dashboard | Domain-specific agent delegation |
| Alpha-Evolve | design, architect, multiple | N implementations with selection |

## Specialist Agents

| Agent | Domain | When to Use |
|-------|--------|-------------|
| nautilus-coder | NautilusTrader | Strategy/indicator implementation |
| strategy-researcher | Academic | Paper search and analysis |
| grafana-expert | Monitoring | Dashboard creation |
| backtest-analyzer | Logs | Large log file analysis |
```

## Rollback Plan

If Ralph mode causes issues:

1. **Immediate**: Set `RALPH_MODE_ENABLED=false` in environment
2. **Short-term**: Re-enable deprecated agents in settings
3. **Long-term**: Revert this ADR and restore original architecture

## Success Metrics

Track over 30 days:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Token reduction | 30% | Compare before/after |
| Task completion rate | 95% | Ralph vs manual |
| Circuit breaker trips | < 10% | Iterations that hit limit |
| User satisfaction | Maintain | Survey/feedback |

## Implementation Checklist

- [x] Create task-classifier.py hook
- [x] Create ralph-loop.py stop hook
- [x] Document deprecation plan (this ADR)
- [ ] Update settings.json with new hooks
- [ ] Update CLAUDE.md with new execution modes
- [ ] Add deprecation warnings to old agents
- [ ] Monitor metrics for 1 week
- [ ] Hard deprecation after validation

## References

- ADR-004: Autonomous AI Loops Strategy
- ADR-005: Agent Architecture Analysis
- Ralph Wiggum: https://ghuntley.com/ralph/
