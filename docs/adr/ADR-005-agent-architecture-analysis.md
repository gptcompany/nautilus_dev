# ADR-005: Agent Architecture Analysis - Ralph vs Specialized Agents

**Status**: Analysis
**Date**: 2026-01-08

## Question

Should we replace specialized sub-agents with a single Ralph Wiggum loop + prompt optimizer?

## Token Cost Analysis

### Current Architecture (Specialized Agents)

```
Session Start
├── Main Context Load: ~5K tokens
├── Agent Spawn #1 (nautilus-coder): +8K tokens (new context)
├── Agent Spawn #2 (test-runner): +8K tokens (new context)
├── Agent Spawn #3 (alpha-debug round 1): +8K tokens
├── Agent Spawn #4 (alpha-debug round 2): +8K tokens
└── Total: ~37K tokens for moderate task
```

**Cost per session**: ~$0.50-1.50 (depending on model)

### Ralph Loop Architecture

```
Session Start
├── Initial Context Load: ~5K tokens
├── Iteration 1: +2K tokens (incremental)
├── Iteration 2: +2K tokens (git diff only)
├── Iteration 3: +2K tokens
├── ...
├── Iteration 20: +2K tokens
└── Total: ~45K tokens for 20 iterations
```

**Cost per session**: ~$0.60-1.80 (but more iterations)

### Token Efficiency Comparison

| Scenario | Specialized | Ralph | Winner |
|----------|-------------|-------|--------|
| Simple bug fix | 15K (2 agents) | 9K (3 iter) | Ralph |
| Complex refactor | 45K (5 agents) | 30K (10 iter) | Ralph |
| New strategy | 60K (7 agents) | 80K (25 iter) | Specialized |
| Test coverage | 30K (3 agents) | 20K (8 iter) | Ralph |
| Architecture decision | 25K (3 agents) | 60K (20 iter, diverges) | Specialized |

**Key Insight**: Ralph wins on **mechanical tasks**, Specialized wins on **creative/complex tasks**.

## Agent Classification

### Can Be Replaced by Ralph ✓

| Agent | Why Replaceable | Ralph Equivalent |
|-------|-----------------|------------------|
| alpha-debug | Iterative refinement | Loop until tests pass |
| test-runner | Mechanical execution | Part of loop (CI gate) |
| backtest-analyzer | Pattern matching | Prompt with log chunks |
| tdd-guard | Rule enforcement | Loop exit condition |

### Cannot Be Replaced by Ralph ✗

| Agent | Why Not Replaceable |
|-------|---------------------|
| nautilus-coder | Domain expertise (Context7, Discord knowledge) |
| alpha-evolve | Parallel generation paradigm (N implementations) |
| strategy-researcher | External API calls (papers, analysis) |
| grafana-expert | Visual validation + tool integration |
| nautilus-docs-specialist | Curated knowledge base |

### Hybrid (Partial Replacement)

| Agent | Ralph Component | Specialist Component |
|-------|-----------------|---------------------|
| pinescript-converter | Iteration on conversion | Initial analysis |
| nautilus-visualization | Render loop | Design decisions |

## Proposed Hybrid Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROMPT CLASSIFIER                            │
│  (Analyzes task → routes to appropriate execution mode)          │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   RALPH MODE    │  │  SPECIALIST     │  │  ALPHA-EVOLVE   │
│                 │  │     MODE        │  │     MODE        │
│ • Bug fixes     │  │                 │  │                 │
│ • Refactors     │  │ • NT strategy   │  │ • New features  │
│ • Test coverage │  │ • Research      │  │ • Architecture  │
│ • Migrations    │  │ • Visualization │  │ • Algorithms    │
│ • Docs gen      │  │ • API calls     │  │                 │
│                 │  │                 │  │                 │
│ Exit: tests pass│  │ Exit: task done │  │ Exit: N impls   │
│ or max iter     │  │                 │  │ + fitness eval  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Implementation Recommendation

### Phase 1: Ralph-Lite for Mechanical Tasks

Replace these with Ralph loop:
```yaml
ralph_tasks:
  - "fix all lint errors"
  - "add tests for uncovered functions"
  - "update imports across codebase"
  - "migrate from X to Y"
  - "generate docstrings"
```

Keep specialists for:
```yaml
specialist_tasks:
  - "implement new trading strategy"  # nautilus-coder
  - "research paper X and convert"    # strategy-researcher
  - "create dashboard for Y"          # grafana-expert
```

### Phase 2: Smart Prompt Optimizer

```python
def optimize_prompt(raw_prompt: str) -> tuple[str, str]:
    """
    Returns (optimized_prompt, execution_mode).

    execution_mode: 'ralph' | 'specialist' | 'alpha-evolve'
    """
    # Mechanical keywords → Ralph
    if any(kw in raw_prompt.lower() for kw in [
        'fix', 'refactor', 'update all', 'migrate',
        'rename', 'add tests', 'generate docs'
    ]):
        return enhance_for_ralph(raw_prompt), 'ralph'

    # Domain-specific → Specialist
    if any(kw in raw_prompt.lower() for kw in [
        'strategy', 'nautilus', 'backtest', 'indicator',
        'research', 'paper', 'dashboard'
    ]):
        return raw_prompt, 'specialist'

    # Creative/complex → AlphaEvolve
    if any(kw in raw_prompt.lower() for kw in [
        'design', 'architect', 'implement new', 'create',
        'optimize algorithm', 'multiple approaches'
    ]):
        return raw_prompt, 'alpha-evolve'

    return raw_prompt, 'standard'

def enhance_for_ralph(prompt: str) -> str:
    """Add Ralph-specific instructions."""
    return f"""
{prompt}

## Completion Criteria
- All tests pass
- No lint errors (ruff check .)
- No type errors (mypy)

## Progress Tracking
Update @progress.md after each iteration.

## Exit Conditions
Stop when ALL criteria met or after 15 iterations.
"""
```

### Phase 3: Unified Command

```bash
# Instead of remembering which agent to use:
claude "fix all type errors in strategies/"
# Auto-routes to Ralph mode

claude "implement new momentum strategy based on paper X"
# Auto-routes to nautilus-coder + strategy-researcher

claude "create 3 different approaches for position sizing"
# Auto-routes to alpha-evolve
```

## Token Savings Estimate

| Current | Proposed | Savings |
|---------|----------|---------|
| 5 agent spawns × 8K = 40K | Ralph 10 iter × 2K = 20K | 50% |
| Context reload each spawn | Incremental context | ~30% |
| Manual agent selection | Auto-routing | Time saved |

**Estimated monthly savings**: 30-50% token reduction for mechanical tasks.

## Decision Matrix

| Factor | Keep Specialized | Go Full Ralph | Hybrid (Recommended) |
|--------|------------------|---------------|----------------------|
| Token cost | High | Medium | Low |
| Domain expertise | Excellent | Poor | Good |
| Mechanical tasks | Slow | Fast | Fast |
| Creative tasks | Good | Poor | Good |
| Complexity | Medium | Low | Medium |
| Maintenance | High (many agents) | Low | Medium |

## Recommendation

**HYBRID APPROACH** with:

1. **Ralph-Lite** for mechanical tasks (replaces alpha-debug, test-runner, tdd-guard)
2. **Specialist agents** for domain expertise (nautilus-coder, strategy-researcher)
3. **Alpha-Evolve** for creative/architectural tasks
4. **Prompt Optimizer** for auto-routing

This gives us:
- 30-50% token savings on mechanical tasks
- Preserved domain expertise where needed
- Simpler mental model (one command)
- Best of both worlds

## Next Steps

1. Implement prompt classifier hook
2. Create Ralph-Lite mode (Phase 8.2 from tasks.md)
3. Keep 4 specialist agents (nautilus-*, strategy-researcher)
4. Deprecate redundant agents (alpha-debug → Ralph, tdd-guard → Ralph exit condition)
