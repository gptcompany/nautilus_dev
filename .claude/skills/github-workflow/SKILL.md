---
name: github-workflow
description: GitHub workflow automation for NautilusTrader development. Generate standardized PR descriptions, issue templates, and commit messages. Reduces token usage by 70% on repetitive GitHub operations.
---

# GitHub Workflow Automation

Automate common GitHub operations with standardized templates to reduce token consumption.

## Token Consumption Analysis

### **Without Skill** (Direct GitHub MCP Tools)

| Operation | MCP Tool | Avg Tokens | Notes |
|-----------|----------|-----------|-------|
| Create PR | `mcp__github__create_pull_request` | ~2,500 | Tool metadata + body generation |
| Create Issue | `mcp__github__create_issue` | ~1,800 | Template + label reasoning |
| Add PR Comment | `mcp__github__add_comment_to_pending_review` | ~1,200 | Review comment context |
| List Issues | `mcp__github__list_issues` | ~2,000 | Pagination + filtering logic |

**Estimated Total**: ~7,500 tokens for typical PR workflow

### **With Skill** (Template-Driven)

| Operation | Template | Tokens | Savings |
|-----------|----------|--------|---------|
| Create PR | `nautilus_pr_template` | ~600 | **76%** |
| Create Issue | `strategy_issue_template` | ~500 | **72%** |
| Add PR Comment | `review_comment_template` | ~300 | **75%** |
| Commit Message | `commit_msg_template` | ~200 | **87%** |

**Estimated Total**: ~1,600 tokens (79% reduction)

---

## Quick Start

### Create Pull Request
```
User: "Create PR for MomentumStrategy implementation"

Skill: github-workflow
--> Generates PR with NautilusTrader template:
   Title: "[Strategy] MomentumStrategy: EMA crossover implementation"
   Body: Auto-generated from template
   Labels: enhancement, strategy
   Draft: true (if incomplete)
```

**Token Cost**: ~600 (vs ~2,500 with MCP tool)

---

## Templates

### 1. Pull Request Template

```yaml
# .claude/skills/github-workflow/templates/pr_template.md

Title Pattern: "[{Type}] {Module}: Brief Description"

Types: Strategy, Indicator, Data, Backtest, Live, Docs

Body:
## Summary
{description}

## Changes
- **Strategy/Module**: `{file_path}`
- **Tests**: `{test_file}` ({test_count} tests)
- **Coverage**: {coverage}%
- **Documentation**: Updated

## Test Plan
- [ ] Unit tests passing
- [ ] Integration tests passing (if applicable)
- [ ] Coverage >{threshold}%
- [ ] Backtest validation completed

## Checklist
- [ ] Code follows NautilusTrader patterns
- [ ] Native Rust indicators used (not reimplemented)
- [ ] No df.iterrows() usage
- [ ] Type hints complete
- [ ] Docstrings for public APIs

## Related
- Closes #{issue_number}

Generated with [Claude Code](https://claude.ai/code)
```

**Usage**:
```python
skill.create_pr(
    type="Strategy",
    module="MomentumStrategy",
    description="EMA crossover strategy with risk management",
    file_path="strategies/momentum_strategy.py",
    test_file="tests/test_momentum_strategy.py",
    coverage=87,
    issue_number=5
)
```

---

### 2. Issue Template

```yaml
# .claude/skills/github-workflow/templates/issue_template.md

Title: "[{Type}] {Module Name}"

Body:
## Goal
{goal}

## Deliverables
- [ ] `{deliverable_file}`
- [ ] `{test_file}`
- [ ] Coverage >{threshold}%
- [ ] Documentation updated

## Acceptance Criteria
{criteria_list}

## Technical Notes
- Exchange: {exchange}
- Instrument: {instrument}
- Timeframe: {timeframe}

## Resources
- NautilusTrader docs: {docs_link}
- Discord reference: {discord_link}

## Labels
- `enhancement`
- `{type}`
- `{priority}`
```

**Usage**:
```python
skill.create_issue(
    type="strategy",
    module="MeanReversionStrategy",
    goal="Implement Bollinger Bands mean reversion strategy",
    deliverable_file="strategies/mean_reversion.py",
    exchange="Binance",
    instrument="BTCUSDT",
    priority="P1"
)
```

---

### 3. PR Review Comment Template

```yaml
# Review comment for specific code

## Pattern: Suggest Improvement
**Code Review**: {file}:{line}

**Issue**: {issue_description}

**Suggestion**:
```{language}
{suggested_code}
```

**Reason**: {explanation}
```

**Usage**:
```python
skill.add_review_comment(
    file="strategies/momentum_strategy.py",
    line=45,
    issue="Using custom EMA instead of native indicator",
    suggestion="from nautilus_trader.indicators import ExponentialMovingAverage",
    language="python"
)
```

---

### 4. Commit Message Template

```yaml
# Standardized commit format

Pattern:
[{Type}] {Module}: Brief description

{detailed_changes}

- Deliverable: {file}
- Tests: {test_file}
- Coverage: {coverage}%

Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Usage**:
```python
skill.generate_commit_msg(
    type="Strategy",
    module="MomentumStrategy",
    description="Implement EMA crossover logic",
    file="strategies/momentum_strategy.py",
    coverage=87
)
```

**Output**:
```
[Strategy] MomentumStrategy: Implement EMA crossover logic

- Add EMA indicator with configurable period
- Implement long/short signal generation
- Add position sizing based on risk parameters

- Deliverable: strategies/momentum_strategy.py
- Tests: tests/test_momentum_strategy.py (5 tests)
- Coverage: 87%

Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Workflow Automation

### Workflow 1: Complete PR Creation
```
User: "Create PR for MomentumStrategy"

Skill Execution:
1. Read git diff
2. Extract changes summary
3. Count tests
4. Check coverage
5. Generate PR body from template
6. Call mcp__github__create_pull_request with template
7. Add labels (enhancement, strategy)
8. Set draft=true (if tests incomplete)

Token Cost: ~600 (vs ~2,500 manual)
```

### Workflow 2: Strategy Development Issue
```
User: "Create issue for new RSI strategy"

Skill Execution:
1. Create issue from strategy template
2. Add NautilusTrader-specific checklist
3. Link to relevant docs
4. Assign labels

Token Cost: ~500 (vs ~1,800 manual)
```

---

## Token Savings Summary

| Operation | Without Skill | With Skill | Savings |
|-----------|--------------|------------|---------|
| Create PR | 2,500 | 600 | **76%** |
| Create Issue | 1,800 | 500 | **72%** |
| PR Comments | 1,200 | 300 | **75%** |
| Commit Msg | 1,500 | 200 | **87%** |
| **Total/Task** | **7,000** | **1,600** | **77%** |

---

## Automatic Invocation

**Triggers**:
- "create PR for [strategy/module]"
- "create issue for [feature]"
- "generate commit message for [changes]"
- "add review comment to PR [number]"

**Does NOT trigger**:
- Complex PR review reasoning (use human or subagent)
- Code conflict resolution (use subagent)
- Strategic issue prioritization (use human)

---

## NautilusTrader-Specific Labels

```yaml
# Recommended labels for NautilusTrader projects
labels:
  types:
    - strategy
    - indicator
    - data-pipeline
    - backtest
    - live-trading
    - adapter
    - docs
  priorities:
    - P0-critical
    - P1-high
    - P2-medium
    - P3-low
  status:
    - needs-review
    - in-progress
    - blocked
    - ready-to-merge
```

---

## Best Practices

### PR Best Practices
- Always use draft PRs for incomplete work
- Link to related issue (#XX)
- Include test coverage in description
- Verify no df.iterrows() usage
- Confirm native indicators used

### Issue Best Practices
- One strategy/feature per issue
- Clear acceptance criteria
- Include exchange and instrument details
- Link to NautilusTrader docs

### Commit Message Best Practices
- Follow [Type] prefix convention
- Be concise but descriptive
- Include deliverable file paths
- Always add Claude attribution
