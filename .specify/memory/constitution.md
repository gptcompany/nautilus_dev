# Project Constitution: NautilusTrader Development

**Project**: nautilus_dev
**Created**: 2025-12-10
**Version**: 1.1
**Updated**: 2026-01-06

## Trading Philosophy: I Quattro Pilastri

> "La gabbia la creiamo noi, non il sistema" - EXCEPT for safety parameters

### P1. Probabilistico
- Not predictions, but probability distributions
- Confidence intervals, not point estimates
- Bayesian updating over fixed beliefs

### P2. Non Lineare
- Power laws, not linear scaling (Giller, Mandelbrot)
- Signal^0.5 scaling for position sizing
- Fractals and fat tails are real

### P3. Non Parametrico
- Adaptive to data, not fixed parameters
- Online/recursive algorithms (O(1) per sample)
- Signal thresholds adapt; safety limits are FIXED

### P4. Scalare
- Works at any frequency, any asset, any market condition
- Ratios over absolutes (invariant to scale)
- Ensemble/consensus over single truth

> **P5 "Leggi Naturali" REMOVED** (2026-01-05): PMW validation found ZERO academic
> evidence for Fibonacci/wave physics in trading. Fractals remain valid under P2.

### Safety Parameters (NON-NEGOTIABLE)
```python
MAX_LEVERAGE = 3              # NEVER adaptive
MAX_POSITION_PCT = 10         # NEVER adaptive
STOP_LOSS_PCT = 5             # NEVER adaptive
DAILY_LOSS_LIMIT_PCT = 2      # NEVER adaptive
KILL_SWITCH_DRAWDOWN = 15     # NEVER adaptive
```

---

## Core Principles

### 1. Black Box Design (Eskil Steenberg)
- **Black Box Interfaces**: Strategy modules with clean APIs, hidden implementation
- **Everything Replaceable**: If you don't understand a module, rewrite it easily
- **Constant Velocity**: Write 5 complete lines today > edit 1 line tomorrow
- **Single Responsibility**: One strategy = one clear trading logic
- **Reusable Components**: Extract common patterns into utilities

### 2. KISS & YAGNI
- **Keep It Simple**: Choose boring technology (Python, not Rust until needed)
- **You Ain't Gonna Need It**: Don't build for hypothetical future requirements
- **One module, one purpose**: Each file does ONE thing well
- **Delete dead code**: If unused for 2 weeks, remove it

### 3. Native First
- **Use NautilusTrader native indicators**: Never reimplement EMA, RSI, etc.
- **Use NautilusTrader test kit**: TestDataStubs, TestIdStubs for testing
- **Follow NautilusTrader patterns**: Event-driven architecture, Strategy base class

### 4. Performance Constraints
- **NO `df.iterrows()`**: Use vectorized operations or Rust wranglers
- **Streaming data**: Use ParquetDataCatalog, not in-memory DataFrames
- **Async where needed**: Use async/await for I/O operations

---

## Pipeline Execution Rules

### Subagent Sequential Execution (MANDATORY)

**NEVER run subagents in background during spec-pipeline phases.**

```python
# CORRECT: Sequential, blocking execution
Task(
    subagent_type="nautilus-docs-specialist",
    run_in_background=False,  # EXPLICIT blocking
    prompt="..."
)
# Wait for result before proceeding

# WRONG: Background execution breaks pipeline
Task(
    subagent_type="nautilus-docs-specialist",
    run_in_background=True,  # NEVER in spec-pipeline
    prompt="..."
)
```

### Spec-Pipeline Phase Order (STRICT)

```
1. /speckit.specify     → WAIT for spec.md
2. Research Decision    → BLOCKING evaluation
3. /research (if needed)→ WAIT for research.md
4. /speckit.plan        → WAIT for plan.md
5. NT Validation 1      → BLOCKING, handle results
6. /speckit.tasks       → WAIT for tasks.md
7. /speckit.analyze     → BLOCKING, handle results
8. NT Validation 2      → BLOCKING, handle results
9. Final Report         → Generate summary
```

**Between each phase**: Verify previous phase completed successfully before proceeding.

### Research Validation Rules (Prevent Regressions)

**Purpose**: Ensure /research IMPROVES implementation, never DEGRADES it.

#### Pre-Research Snapshot
Before invoking /research, capture:
1. Current spec.md content (hash or key sections)
2. Existing implementation decisions
3. Performance baselines (if applicable)

#### Post-Research Validation
After /research completes, verify:
1. **No removal of working features** - Research adds, doesn't subtract
2. **No contradiction with P1-P4** - Academic findings must align with pillars
3. **No over-engineering** - Simple > complex (KISS principle)
4. **PMW check** - Search for counter-evidence before adopting findings

#### Research Integration Checklist
- [ ] Finding has academic citation (not just blog/opinion)
- [ ] Finding aligns with at least one pillar (P1-P4)
- [ ] Finding has been PMW-validated (counter-evidence searched)
- [ ] Integration maintains existing functionality
- [ ] Integration doesn't violate safety parameters

#### Rollback Trigger
If research integration causes:
- Test failures → Rollback, investigate
- Performance regression > 10% → Rollback, investigate
- Violation of P1-P4 → Reject finding
- Contradiction with proven code → Prefer proven code

---

## Development Workflow

### TDD Discipline
1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Improve without breaking tests

### Code Review Standards
- Type hints on all public functions
- Docstrings on all public classes/methods
- Coverage > 80%
- No hardcoded values

### Documentation Requirements
- Update `docs/` for new features
- Keep `CLAUDE.md` under 400 lines
- Update architecture docs when structure changes

---

## Agent Guidelines

### When to Use Subagents
- `nautilus-coder`: Strategy implementation
- `nautilus-docs-specialist`: Documentation lookup (BLOCKING)
- `test-runner`: ALWAYS use for running tests
- `alpha-debug`: After implementation, before commits
- `alpha-evolve`: Complex algorithmic tasks with [E] marker
- `tdd-guard`: When writing production code

### Subagent Execution Mode
| Agent | Default Mode | In Pipeline |
|-------|--------------|-------------|
| nautilus-docs-specialist | blocking | BLOCKING |
| test-runner | blocking | BLOCKING |
| alpha-debug | blocking | BLOCKING |
| alpha-evolve | blocking | BLOCKING |
| Explore | can be background | BLOCKING in pipeline |

### When to Use Skills
- `pytest-test-generator`: Test boilerplate (83% token savings)
- `github-workflow`: PR/Issue/Commit templates (79% savings)
- `pydantic-model-generator`: Config models (75% savings)

---

## Quality Gates

### Pre-Commit
- [ ] All tests pass (`uv run pytest`)
- [ ] Code formatted (`ruff format .`)
- [ ] Linting clean (`ruff check .`)
- [ ] No debug statements
- [ ] Coverage maintained

### Pre-Merge
- [ ] PR description complete
- [ ] Alpha-debug verification (for significant changes)
- [ ] Documentation updated
- [ ] No [NEEDS CLARIFICATION] items

### Post-Research (NEW)
- [ ] No test regressions
- [ ] No performance regressions > 10%
- [ ] Findings align with P1-P4
- [ ] PMW validation completed

---

## Prohibited Actions

### NEVER
- Use `--no-verify` to bypass hooks
- Disable tests instead of fixing them
- Commit without testing locally
- Hardcode secrets/API keys
- Use `df.iterrows()`
- Reimplement native indicators
- Create report files unless requested
- **Run spec-pipeline subagents in background**
- **Adopt research findings that contradict P1-P4**
- **Make safety parameters adaptive**

### ALWAYS
- Run tests before committing
- Use `uv` for dependencies (not `pip`)
- Format code before commit
- Update docs when architecture changes
- Use test-runner agent for tests
- **Execute spec-pipeline phases sequentially**
- **Validate research findings against pillars**
- **Keep safety parameters fixed**
