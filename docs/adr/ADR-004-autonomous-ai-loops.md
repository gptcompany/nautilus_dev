# ADR-004: Autonomous AI Coding Loop Strategy

**Status**: Proposed
**Date**: 2026-01-08
**Decision Makers**: Development Team

## Context

Emerging patterns for autonomous AI coding show two main approaches:
1. **Ralph Wiggum** - Bash loop with exit interception, running Claude for hours
2. **AlphaEvolve** - Multi-implementation evolutionary approach with fitness selection

We need to decide which patterns to adopt for our NautilusTrader development system.

## Comparative Analysis

### Ralph Wiggum Approach

**Core Pattern:**
```bash
while :; do cat PROMPT.md | claude-code ; done
```

**Key Features:**
- Stop hook intercepts exit (exit code 2)
- State persisted via git history + modified files
- Progress tracked in `progress.txt` / `@fix_plan.md`
- Circuit breaker: consecutive errors, no-progress detection
- Rate limiting: 100 calls/hour default
- 5-hour API limit handling

**Strengths:**
- Simple conceptual model
- Excels at mechanical refactors, migrations
- Continuous refinement toward clear goals
- Well-tested (97 tests, 100% pass rate)
- Built-in monitoring dashboard

**Weaknesses:**
- Requires precise completion criteria
- Can diverge on ambiguous tasks
- High token cost ($50-100+ for long loops)
- Single-threaded execution
- "Faith-based" - requires belief in eventual convergence

**Best For:**
- Large refactors (framework migrations)
- Test coverage expansion
- Documentation generation
- Greenfield scaffolding
- Mechanical, objective tasks

### AlphaEvolve Approach (Ours)

**Core Pattern:**
```
Generate N implementations → Evaluate fitness → Select best/ensemble
```

**Key Features:**
- Multiple parallel implementations
- Fitness function evaluation
- Best selection or ensemble creation
- TDD integration (Red-Green-Refactor)
- Context from SpecKit artifacts

**Strengths:**
- Explores solution space breadth
- Quality through competition
- Works with uncertain requirements
- Parallelizable (git worktrees)
- Produces diverse options for human review

**Weaknesses:**
- Higher resource usage (N implementations)
- Requires fitness function design
- More complex orchestration
- May produce similar solutions

**Best For:**
- Complex algorithmic tasks ([E] marker)
- Architectural decisions
- Strategy development
- Tasks with multiple valid approaches

### Our Current Architecture

**Components:**
| Component | Purpose |
|-----------|---------|
| Specialized Agents | Domain expertise (nautilus-coder, test-runner, etc.) |
| SpecKit Pipeline | spec.md → plan.md → tasks.md |
| TDD Guard | Red-Green-Refactor enforcement |
| Alpha-Debug | Iterative bug hunting (2-10 rounds) |
| Hooks System | Quality gates, metrics collection |

**Strengths:**
- Domain-specialized agents
- Strong TDD discipline
- Comprehensive metrics/monitoring
- CI/CD integration
- Human-in-the-loop checkpoints

**Gaps Compared to Ralph:**
| Gap | Ralph Has | We Have |
|-----|-----------|---------|
| Continuous loops | Yes (hours) | No (session-based) |
| Exit interception | Stop hook | Session summary only |
| Progress persistence | @fix_plan.md | TodoWrite (session) |
| Circuit breakers | Built-in | Limited |
| Rate limiting | Configurable | None |

## Decision Options

### Option A: Adopt Ralph Pattern
Create `ralph-mode` for long-running autonomous tasks.

**Implementation:**
```bash
# New hook: hooks/control/ralph-loop.py
# Stop hook that re-injects prompt on exit
# Circuit breaker: MAX_CONSECUTIVE_ERRORS=3
# Progress file: .ralph/progress.md
```

**Pros:** Proven pattern, enables hours-long sessions
**Cons:** High token cost, requires prompt engineering

### Option B: Enhance AlphaEvolve
Add continuous refinement to AlphaEvolve.

**Implementation:**
```python
# alpha-evolve with iterations
for round in range(MAX_ROUNDS):
    implementations = generate_implementations(N)
    best = evaluate_fitness(implementations)
    if fitness(best) > THRESHOLD:
        break
    refine_prompt(best)
```

**Pros:** Builds on existing system, quality-focused
**Cons:** More complex, still bounded

### Option C: Hybrid Approach (Recommended)
Use Ralph for mechanical tasks, AlphaEvolve for creative tasks.

**Implementation:**
```
Task Classification:
├── Mechanical (refactor, migrate, docs) → Ralph Loop
├── Creative (new features, architecture) → AlphaEvolve
└── Bug Fixes → Alpha-Debug (existing)
```

**New Components:**
1. `ralph-loop` hook for continuous execution
2. Task classifier in prompt submission
3. Progress persistence across sessions
4. Enhanced circuit breakers

## Proposed Implementation

### Phase 1: Ralph-Lite Mode
```yaml
# .claude/settings.json
{
  "hooks": {
    "Stop": [{
      "command": "python3 hooks/control/ralph-loop.py",
      "timeout": 5000
    }]
  }
}
```

**ralph-loop.py features:**
- Check for `RALPH_MODE=true` env var
- Read `PROMPT.md` for re-injection
- Track iterations in `.ralph/state.json`
- Circuit breaker: 3 consecutive errors, 5 no-progress
- Max iterations: 20 (configurable)

### Phase 2: Progress Persistence
```markdown
# .ralph/progress.md
## Iteration 1 (2026-01-08 10:00)
- [x] Created base structure
- [x] Added unit tests
- [ ] Integration tests pending

## Iteration 2 (2026-01-08 10:15)
- [x] Fixed import errors
- [x] Integration tests passing
```

### Phase 3: Task Classifier
```python
def classify_task(prompt: str) -> str:
    """Classify task for appropriate execution mode."""
    mechanical_keywords = ['refactor', 'migrate', 'rename', 'update all', 'generate docs']
    creative_keywords = ['design', 'implement new', 'create strategy', 'architect']

    if any(kw in prompt.lower() for kw in mechanical_keywords):
        return 'ralph'
    elif any(kw in prompt.lower() for kw in creative_keywords):
        return 'alpha-evolve'
    else:
        return 'standard'
```

## Consequences

### Positive
- Enables hours-long autonomous development
- Appropriate tool for task type
- Built-in safety (circuit breakers)
- Progress visibility

### Negative
- Increased token costs for Ralph mode
- More complex system to maintain
- Requires prompt discipline

### Risks
- Runaway loops (mitigated by circuit breakers)
- Token budget overruns (mitigated by iteration limits)
- Divergent outputs (mitigated by clear completion criteria)

## References

- [Ralph Wiggum Official](https://ghuntley.com/ralph/)
- [Ralph Implementation](https://github.com/frankbria/ralph-claude-code)
- [Autonomous Loops Guide](https://paddo.dev/blog/ralph-wiggum-autonomous-loops/)
- [AlphaEvolve Pattern](specs/alpha-evolve/)
