# Code Review Checklist

> For NautilusTrader strategy development. Use this checklist for all PRs.

## Trading-Specific Checks

### Position Management
- [ ] Position sizes respect `MAX_POSITION_PCT` (10%)
- [ ] Leverage within `MAX_LEVERAGE` (3x)
- [ ] Stop losses implemented and tested
- [ ] No position accumulation bugs (check for duplicate signals)

### Risk Management
- [ ] Daily loss limit respected (`DAILY_LOSS_LIMIT_PCT`)
- [ ] Kill switch implemented for max drawdown (15%)
- [ ] No adaptive safety limits (must be FIXED)
- [ ] Emergency shutdown path exists

### Order Execution
- [ ] Order types appropriate for instrument
- [ ] Slippage tolerance configured
- [ ] Rate limiting respected (exchange limits)
- [ ] Retry logic for transient failures (max 3x)

### Data Handling
- [ ] No `df.iterrows()` - use vectorized operations
- [ ] Streaming data processing (no full dataset in memory)
- [ ] Proper timezone handling (UTC)
- [ ] No lookahead bias in indicators

## Security Checks

### Secrets & Credentials
- [ ] No hardcoded API keys
- [ ] No credentials in logs
- [ ] `.env` files in `.gitignore`
- [ ] Secrets accessed via environment variables

### Input Validation
- [ ] User inputs validated
- [ ] External data sanitized
- [ ] SQL injection prevention (parameterized queries)
- [ ] No `eval()` or `exec()` on user input

### API Security
- [ ] API keys have minimal permissions
- [ ] Rate limiting implemented
- [ ] Error messages don't leak sensitive info
- [ ] HTTPS for all external calls

## Performance Checks

### Latency
- [ ] Hot path optimized (no unnecessary allocations)
- [ ] Native Rust indicators used (not Python reimplementations)
- [ ] Async where appropriate
- [ ] No blocking calls in event handlers

### Memory
- [ ] No memory leaks (check long-running processes)
- [ ] Large datasets streamed, not loaded
- [ ] Proper cleanup in `on_stop()`
- [ ] Connection pools used for databases

### Concurrency
- [ ] Thread safety for shared state
- [ ] No race conditions
- [ ] Proper locking where needed
- [ ] Async/await used correctly

## NautilusTrader Best Practices

### Strategy Structure
- [ ] Single responsibility (one strategy = one logic)
- [ ] Proper inheritance from `Strategy` base
- [ ] `on_start()`, `on_stop()` implemented
- [ ] State properly initialized

### Indicators
- [ ] Using native Rust indicators from NT
- [ ] Not reimplementing existing indicators
- [ ] Proper warmup period handling
- [ ] Indicator state reset on restart

### Events & Messages
- [ ] Proper event handling (`on_order`, `on_position`, etc.)
- [ ] No blocking in event handlers
- [ ] Error handling for all events
- [ ] Logging at appropriate levels

### Testing
- [ ] Unit tests for signal logic
- [ ] Backtest with real market data
- [ ] Edge cases covered (empty data, extreme values)
- [ ] 80%+ coverage for critical paths

## General Code Quality

### Documentation
- [ ] Public methods have docstrings
- [ ] Complex logic explained in comments
- [ ] README updated if needed
- [ ] ADR created for architectural decisions

### Style
- [ ] PEP 8 compliant (ruff check passes)
- [ ] Type hints on public APIs
- [ ] Consistent naming conventions
- [ ] Functions <= 50 lines

### Error Handling
- [ ] Fail fast on invalid config
- [ ] Retry transient errors (3x max)
- [ ] No silent failures
- [ ] Proper exception types

---

## Review Workflow

1. **Author**: Run pre-commit hooks before pushing
2. **Reviewer**: Use this checklist systematically
3. **Opus Reviewer**: Automated review via GitHub Actions
4. **Approval**: Requires at least one human approval

## Quick Commands

```bash
# Run all checks locally
uv run ruff check . && uv run ruff format --check .
uv run mypy strategies/
uv run pytest tests/ -x --tb=short
uv run bandit -r strategies/ -ll
```
