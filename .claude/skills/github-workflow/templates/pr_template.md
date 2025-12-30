# Pull Request: [{{TYPE}}] {{MODULE_NAME}}

## Summary
{{DESCRIPTION}}

## Changes
- **Strategy/Module**: `{{FILE_PATH}}`
- **Tests**: `{{TEST_FILE}}` ({{TEST_COUNT}} tests)
- **Coverage**: {{COVERAGE}}%
- **Documentation**: Updated

## Test Plan
- [ ] Unit tests passing
- [ ] Integration tests passing (if applicable)
- [ ] Coverage >{{THRESHOLD}}%
- [ ] Backtest validation completed

## Implementation Details
{{IMPLEMENTATION_NOTES}}

## Checklist
- [ ] Code follows NautilusTrader patterns
- [ ] Native Rust indicators used (not reimplemented)
- [ ] No df.iterrows() usage
- [ ] Type hints complete
- [ ] Docstrings for public APIs
- [ ] TDD cycle completed (RED-GREEN-REFACTOR)

## Related
- Closes #{{ISSUE_NUMBER}}
- Depends on: #{{DEPENDS_ON}}

## Screenshots (if applicable)
{{SCREENSHOTS}}

---

Generated with [Claude Code](https://claude.ai/code)

**Agent**: {{AGENT_NAME}}
