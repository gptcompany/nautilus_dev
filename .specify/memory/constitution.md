# Project Constitution: NautilusTrader Development

**Project**: nautilus_dev
**Created**: 2025-12-10
**Version**: 1.0

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

## Agent Guidelines

### When to Use Subagents
- `nautilus-coder`: Strategy implementation
- `nautilus-docs-specialist`: Documentation lookup
- `test-runner`: ALWAYS use for running tests
- `alpha-debug`: After implementation, before commits
- `alpha-evolve`: Complex algorithmic tasks with [E] marker
- `tdd-guard`: When writing production code

### When to Use Skills
- `pytest-test-generator`: Test boilerplate (83% token savings)
- `github-workflow`: PR/Issue/Commit templates (79% savings)
- `pydantic-model-generator`: Config models (75% savings)

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

## Prohibited Actions

### NEVER
- Use `--no-verify` to bypass hooks
- Disable tests instead of fixing them
- Commit without testing locally
- Hardcode secrets/API keys
- Use `df.iterrows()`
- Reimplement native indicators
- Create report files unless requested

### ALWAYS
- Run tests before committing
- Use `uv` for dependencies (not `pip`)
- Format code before commit
- Update docs when architecture changes
- Use test-runner agent for tests
