---
allowed-tools: Bash, Read, mcp__langsmith__fetch_trace, mcp__langsmith__get_project_runs_stats, mcp__langsmith__list_datasets, mcp__langsmith__list_examples
---

# TDD Quality Score

Analyze test quality and coverage using LangSmith telemetry and test execution data.

## Usage
```
/tdd:quality-score <issue_number>
```

## Instructions

You are analyzing test quality for a specific issue using TDD Guard data and LangSmith telemetry.

### 1. Load Issue Context

Read the issue file: `.claude/epics/*/issues/<issue_number>.md`

Extract:
- Issue title and description
- Associated test files
- Implementation files

### 2. Analyze TDD Guard Data

Check `.claude/tdd-guard/data/modifications.json` for:
- RED→GREEN→REFACTOR cycle compliance
- Number of cycles executed
- Test failures before implementation
- Refactoring safety (tests maintained green)

### 3. Query LangSmith Telemetry

Use `mcp__langsmith__fetch_trace` to get recent test execution traces:
- Test execution count
- Token usage per test generation
- Error patterns
- Latency metrics

### 4. Calculate Quality Score

Generate composite score (0-100) based on:

**TDD Discipline (40 points)**
- RED phase executed first: 10 pts
- GREEN phase minimal implementation: 10 pts
- REFACTOR phase performed: 10 pts
- All cycles complete: 10 pts

**Test Coverage (30 points)**
- Critical paths covered: 15 pts
- Edge cases included: 10 pts
- Error scenarios tested: 5 pts

**Test Quality (20 points)**
- Descriptive test names: 5 pts
- Independent tests: 5 pts
- Fast execution (<1s): 5 pts
- No flaky tests: 5 pts

**Efficiency (10 points)**
- Minimal token usage: 5 pts
- Few iterations needed: 5 pts

### 5. Generate Report

Present findings in this format:

```
🎯 TDD Quality Score: XX/100

Issue #XX: [title]
Date: [analysis date]

📊 Score Breakdown
-----------------
TDD Discipline:  XX/40
Test Coverage:   XX/30
Test Quality:    XX/20
Efficiency:      XX/10

✅ Strengths
-----------
• [Key strength 1]
• [Key strength 2]

⚠️  Improvement Areas
--------------------
• [Improvement 1]: [specific recommendation]
• [Improvement 2]: [specific recommendation]

📈 Metrics
---------
Total Test Cycles: X
Avg Tokens/Cycle: XXX
Test Execution Time: XXXms
Failures Before GREEN: X

🎓 Recommendations
-----------------
1. [Specific actionable recommendation]
2. [Pattern to follow in future]
3. [Tool or technique to use]
```

### 6. Dataset Enhancement Suggestion

If quality score < 80, suggest adding this issue's tests to LangSmith dataset for future reference:

```
💡 Suggestion: Add to Learning Dataset

This issue shows good/poor patterns in [aspect]. Consider:
• Create dataset: /tdd:create-dataset issue-<number>
• Tag with: tdd-quality, [pattern-type]
• Use for: Future test generation guidance
```

## Example

```
/tdd:quality-score 42
```

Analyzes test quality for issue #42, provides score and recommendations.

## Notes

- Requires TDD Guard to be active during development
- Best used after issue completion
- Score is advisory, not blocking
- Helps identify patterns for improvement
