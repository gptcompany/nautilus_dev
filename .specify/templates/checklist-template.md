# Checklist: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Created**: [DATE]
**Spec Reference**: `specs/[###-feature-name]/spec.md`

## Pre-Implementation Checklist

### Requirements Clarity
- [ ] All user stories have clear acceptance criteria
- [ ] Edge cases identified and documented
- [ ] Dependencies identified and available
- [ ] No [NEEDS CLARIFICATION] items remaining in spec

### Technical Readiness
- [ ] Architecture decisions documented in plan.md
- [ ] File structure defined
- [ ] API surface defined
- [ ] Testing strategy outlined

---

## Implementation Checklist

### Code Quality
- [ ] Type hints on all public functions
- [ ] Docstrings on all public classes and methods
- [ ] No `df.iterrows()` usage (use vectorized operations)
- [ ] Native NautilusTrader indicators used (not reimplemented)
- [ ] No hardcoded values (use config)
- [ ] Error handling for edge cases

### NautilusTrader Best Practices
- [ ] Strategy inherits from `Strategy` base class
- [ ] Config uses Pydantic `BaseModel`
- [ ] Indicators initialized in `on_start()`
- [ ] Indicators registered with `self.register_indicator()`
- [ ] Position checks before order submission
- [ ] Proper instrument_id validation

### Testing
- [ ] Unit tests written BEFORE implementation (TDD)
- [ ] All tests passing
- [ ] Coverage > 80%
- [ ] Integration tests with BacktestNode
- [ ] Edge cases tested (empty data, gaps, extreme values)

### Documentation
- [ ] Strategy documentation in `docs/`
- [ ] Configuration options documented
- [ ] Usage examples provided
- [ ] CLAUDE.md updated if architecture changed

---

## Pre-Commit Checklist

### Code Standards
- [ ] `ruff check .` passes
- [ ] `ruff format .` applied
- [ ] No debug print statements
- [ ] No commented-out code blocks
- [ ] No TODO/FIXME without issue reference

### Git Hygiene
- [ ] Meaningful commit messages
- [ ] No secrets/API keys in code
- [ ] .gitignore updated if needed
- [ ] Branch up to date with main

### Final Verification
- [ ] `uv run pytest` passes
- [ ] Coverage report reviewed
- [ ] Alpha-debug run completed (if significant changes)
- [ ] PR description complete

---

## Post-Merge Checklist

- [ ] Feature branch deleted
- [ ] Related issues closed
- [ ] Documentation published
- [ ] Team notified of new feature

---

## Quick Reference Commands

```bash
# Run tests
uv run pytest tests/test_{feature_name}.py -v

# Check coverage
uv run pytest --cov=strategies/{feature_name} --cov-report=term-missing

# Lint and format
ruff check . && ruff format .

# Type check
uv run pyright strategies/{feature_name}/

# Run backtest
python -m strategies.{feature_name}.backtest
```
