# Skills Manifest

Quick reference for all available Claude Code skills in this project.

## Trading Domain

| Skill | Description | Token Savings | Triggers |
|-------|-------------|---------------|----------|
| `paper-to-strategy` | Academic paper → NautilusTrader spec | 70% (2500→750) | "convert paper", "paper to strategy" |
| `pinescript-converter` | PineScript → NautilusTrader Python | ~65% | `/pinescript <url>` |
| `research-pipeline` | Automated research (semantic + papers) | ~60% | `/research <topic>` |

## Code Generation

| Skill | Description | Token Savings | Triggers |
|-------|-------------|---------------|----------|
| `pytest-test-generator` | TDD test templates with RED phase | 83% | "generate tests", "create test" |
| `pydantic-model-generator` | Type-safe Pydantic models | 75% (2000→500) | "create model", "pydantic for" |
| `formula-to-code` | LaTeX/math → Python code | 70% (2000→600) | "convert formula", "implement equation" |

## Workflow Automation

| Skill | Description | Token Savings | Triggers |
|-------|-------------|---------------|----------|
| `github-workflow` | PR descriptions, issues, commits | 79% (7000→1600) | "create PR", "create issue" |

## Usage Examples

### Convert Paper to Strategy
```
User: "Convert this paper on momentum strategies to a NautilusTrader spec"
→ Skill: paper-to-strategy
```

### Generate Tests
```
User: "Generate TDD tests for MomentumStrategy"
→ Skill: pytest-test-generator (creates RED phase tests)
```

### Create PR
```
User: "Create PR for the momentum strategy implementation"
→ Skill: github-workflow (uses templates, 79% token savings)
```

## Skill Locations

```
.claude/skills/
├── formula-to-code/SKILL.md
├── github-workflow/SKILL.md
├── paper-to-strategy/SKILL.md
├── pinescript-converter/SKILL.md
├── pydantic-model-generator/SKILL.md
├── pytest-test-generator/SKILL.md
└── research-pipeline/SKILL.md
```

## Token Savings Summary

| Category | Average Savings |
|----------|-----------------|
| Code Generation | 76% |
| Trading Domain | 65% |
| Workflow | 79% |
| **Overall** | **73%** |
