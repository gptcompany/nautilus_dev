# Ralph Mode - Autonomous Development Prompt Template

## Quick Start

To enable Ralph mode for autonomous development loops, structure your prompt like this:

```
[RALPH MODE]

## Task
<Clear description of what needs to be done>

## Exit Criteria
- [ ] All tests pass
- [ ] Lint clean (ruff check)
- [ ] <Your specific criteria>

## Constraints
- Max iterations: 10
- Budget: $15
- <Any other limits>

## Context
<Relevant files, specs, or background>
```

## Example Prompts

### Bug Fix (Mechanical)
```
[RALPH MODE]

## Task
Fix the failing test in tests/strategies/test_position_sizing.py

## Exit Criteria
- [ ] test_position_sizing.py passes
- [ ] No new test failures introduced
- [ ] Coverage maintained > 80%

## Constraints
- Only modify position_sizing/ directory
- Don't change public API
```

### Feature Implementation
```
[RALPH MODE]

## Task
Implement WebSocket reconnection logic per Spec 021

## Exit Criteria
- [ ] All tests pass
- [ ] Reconnection works after disconnect
- [ ] Max 3 retry attempts before failure
- [ ] Backoff delay between retries

## Constraints
- Follow existing patterns in adapters/
- Add unit tests for new code
```

### Refactoring
```
[RALPH MODE]

## Task
Refactor MetricsCollector to use async I/O

## Exit Criteria
- [ ] All existing tests pass
- [ ] Performance benchmark shows improvement
- [ ] No blocking calls in hot path

## Constraints
- Maintain backward compatibility
- Keep public API unchanged
```

## Control Commands

During Ralph execution, you can use:

| Command | Effect |
|---------|--------|
| `STOP RALPH` | Immediately stop the loop |
| `RALPH STATUS` | Show current iteration and progress |
| `RALPH PAUSE` | Pause for manual review |
| `RALPH RESUME` | Continue after pause |

## How It Works

1. **Task Classifier** analyzes your prompt
2. If mechanical task → Ralph mode (autonomous loops)
3. If creative task → AlphaEvolve mode (multi-approach)
4. If standard → Normal Claude workflow

## Circuit Breakers

Ralph automatically stops when:

- Max iterations reached (default: 15)
- Budget limit hit (default: $20)
- 3 consecutive errors
- 5 iterations with no progress
- 3 consecutive CI failures

## Best Practices

### DO
- Provide clear, measurable exit criteria
- Set reasonable iteration limits
- Include test requirements
- Specify which files/directories to modify

### DON'T
- Use for exploratory/research tasks
- Leave exit criteria vague
- Skip test requirements
- Allow unlimited iterations

## Progress Tracking

Progress is saved to:
- `~/.claude/ralph/state.json` - Current state
- `~/.claude/ralph/progress.md` - History log
- Git commits after each iteration

## Related

- [ADR-004: Ralph vs AlphaEvolve](docs/adr/ADR-004-autonomous-ai-loops.md)
- [Ralph Loop Hook](hooks/control/ralph-loop.py)
- [Task Classifier](hooks/submit/task-classifier.py)
