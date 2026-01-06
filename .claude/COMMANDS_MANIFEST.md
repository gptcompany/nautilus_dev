# Commands Manifest

Quick reference for all available slash commands in this project.

## TDD Workflow (`/tdd:*`)

| Command | Description | Use Case |
|---------|-------------|----------|
| `/tdd:cycle` | Full Red-Green-Refactor cycle | Complete TDD iteration |
| `/tdd:cycle-safe` | TDD cycle with auto-rollback | Safe iteration with undo |
| `/tdd:red` | Write failing tests only | RED phase |
| `/tdd:green` | Implement minimal solution | GREEN phase |
| `/tdd:refactor` | Clean up code | REFACTOR phase |
| `/tdd:spec-to-test` | Convert spec to test cases | Spec → Tests |
| `/tdd:rollback-red` | Rollback to RED phase | Undo GREEN/REFACTOR |
| `/tdd:quality-score` | Calculate TDD quality metrics | Quality check |

### TDD Flow
```
/tdd:spec-to-test → /tdd:red → /tdd:green → /tdd:refactor
         OR
/tdd:cycle-safe (all-in-one with rollback)
```

## SpecKit Pipeline (`/speckit:*`)

| Command | Description | Output |
|---------|-------------|--------|
| `/speckit:constitution` | Project principles | `constitution.md` |
| `/speckit:specify` | Feature specification | `spec.md` |
| `/speckit:clarify` | Clarify requirements | Updated `spec.md` |
| `/speckit:plan` | Implementation plan | `plan.md` |
| `/speckit:tasks` | Task breakdown | `tasks.md` |
| `/speckit:taskstoissues` | Convert to GitHub issues | GitHub issues |
| `/speckit:implement` | Execute tasks | Code implementation |
| `/speckit:analyze` | Cross-artifact analysis | Consistency report |
| `/speckit:checklist` | Custom checklist | `checklist.md` |

### SpecKit Flow
```
/speckit:constitution → /speckit:specify → /speckit:clarify
                                ↓
                        /speckit:plan → /speckit:tasks
                                              ↓
                                     /speckit:implement
```

## Undo System (`/undo:*`)

| Command | Description | Use Case |
|---------|-------------|----------|
| `/undo:checkpoint` | Create named restore point | Before risky changes |
| `/undo:list` | List all checkpoints | View history |
| `/undo:preview` | Preview rollback changes | Before rollback |
| `/undo:rollback` | Rollback to checkpoint | Undo changes |
| `/undo:redo` | Redo after rollback | Redo changes |

## Other Commands

| Command | Description |
|---------|-------------|
| `/research` | Academic research pipeline |
| `/pinescript` | Convert PineScript to NautilusTrader |
| `/spec-pipeline` | Automated spec orchestration |
| `/verify-tasks` | Verify tasks.md consistency |

## Command Locations

```
.claude/commands/
├── research.md
├── pinescript.md
├── spec-pipeline.md
├── verify-tasks.md
├── speckit/
│   ├── constitution.md
│   ├── specify.md
│   ├── clarify.md
│   ├── plan.md
│   ├── tasks.md
│   ├── taskstoissues.md
│   ├── implement.md
│   ├── analyze.md
│   └── checklist.md
├── tdd/
│   ├── cycle.md
│   ├── cycle-safe.md
│   ├── red.md
│   ├── green.md
│   ├── refactor.md
│   ├── spec-to-test.md
│   ├── rollback-red.md
│   └── quality-score.md
└── undo/
    ├── checkpoint.md
    ├── list.md
    ├── preview.md
    ├── rollback.md
    └── redo.md
```

## Recommended Workflows

### New Feature Development
```
1. /speckit:specify "feature description"
2. /speckit:clarify (if ambiguous)
3. /speckit:plan
4. /speckit:tasks
5. /undo:checkpoint "before implementation"
6. /tdd:cycle-safe (for each task)
7. /speckit:analyze (verify consistency)
```

### Bug Fix with Safety
```
1. /undo:checkpoint "before bugfix"
2. /tdd:red (write failing test)
3. /tdd:green (fix bug)
4. /tdd:refactor (cleanup)
```

### Research to Implementation
```
1. /research "topic"
2. /speckit:specify (from research)
3. /speckit:plan
4. /tdd:spec-to-test
5. /tdd:cycle
```
