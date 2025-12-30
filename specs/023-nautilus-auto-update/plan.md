# Implementation Plan: NautilusTrader Auto-Update Pipeline

**Feature Branch**: `023-nautilus-auto-update`
**Created**: 2025-12-29
**Status**: Draft
**Spec Reference**: `specs/023-nautilus-auto-update/spec.md`

## Architecture Overview

Autonomous pipeline to detect NautilusTrader nightly changes, analyze impact on our codebase, update dependencies, and validate compatibility - preventing tech debt accumulation.

### System Context

The pipeline integrates three existing systems:
1. **N8N Workflow** (`/media/sam/1TB/devteam1`) - Existing scheduler infrastructure
2. **GitHub/PyPI APIs** - Source of release information
3. **Claude Code CLI** - Agent dispatch for complex fixes

The existing `docs/nautilus/nautilus-trader-changelog.json` is already being populated by an N8N workflow. This spec extends that foundation with impact analysis and automated remediation.

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    N8N Workflow (Existing)                      │
│  ┌─────────────────┐                                            │
│  │ nautilus-trader │──→ docs/nautilus/changelog.json (EXISTS)   │
│  │ changelog.json  │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              NEW: Auto-Update Pipeline (Python)                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Change Parser   │──│ Impact Analyzer │──│ Decision Gate   │  │
│  │ (parse_changes) │  │ (grep codebase) │  │ (simple/complex)│  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                    │            │
│                       ┌────────────────────────────┼────────┐   │
│                       ▼                            ▼        │   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐   │
│  │ Auto-Updater    │  │ Claude Dispatch │  │ Alert Human   │   │
│  │ (pyproject.toml)│  │ (complex fixes) │  │ (architectural)│   │
│  └─────────────────┘  └─────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Technical Context

### Dependencies (Status)
| Dependency | Status | Notes |
|------------|--------|-------|
| N8N Workflow | EXISTS | `/media/sam/1TB/devteam1` - already generates changelog |
| changelog.json | EXISTS | `docs/nautilus/nautilus-trader-changelog.json` |
| sync_research.py | EXISTS | Pattern for JSON sync scripts at `scripts/sync_research.py` |
| GitHub API | AVAILABLE | Via N8N or Python requests |
| Claude Code CLI | AVAILABLE | `claude` CLI installed |
| test-runner agent | EXISTS | For validation |

### Resolved (see research.md)
1. **GitHub Actions vs Local**: ✅ Hybrid - GH Actions for checks, local cron for heavy ops
2. **PR Approval Flow**: ✅ Confidence-gated HITL (Very High=auto, High=24h delay, Low=manual)
3. **N8N Extension**: ✅ Separate Python pipeline, consume N8N output
4. **Notification Channel**: ✅ Discord primary, email fallback for critical failures

---

## Constitution Check

### Principle Alignment

| Principle | Alignment | Notes |
|-----------|-----------|-------|
| Black Box Design | ✅ ALIGNED | Each module (parser, analyzer, updater) has clean API |
| KISS & YAGNI | ✅ ALIGNED | Minimal MVP: parse → analyze → alert, no complex ML |
| Native First | ✅ ALIGNED | Uses existing N8N, changelog format, sync patterns |
| Performance | ✅ ALIGNED | Daily cron, no real-time requirements |
| TDD Discipline | ✅ ALIGNED | Will test each module in isolation |

### Prohibited Actions Check

| Prohibited Action | Status | Notes |
|-------------------|--------|-------|
| `df.iterrows()` | ✅ N/A | No pandas DataFrames in this pipeline |
| Reimplement native | ✅ N/A | Using existing changelog generation |
| Create report files | ⚠️ RISK | Impact reports needed - justified by spec |
| Use `--no-verify` | ✅ N/A | All commits go through hooks |

### Gate Violations

**NONE** - Spec aligns with constitution.

---

## Technical Decisions

### Decision 1: Pipeline Architecture

**Options Considered**:
1. **N8N Extension**: Extend existing N8N workflow with new nodes
   - Pros: Consistent with existing infra, visual workflow
   - Cons: Limited Python capabilities, harder to test
2. **Pure Python Pipeline**: Standalone Python scripts triggered by cron
   - Pros: Full Python power, testable, version controlled
   - Cons: Separate from N8N ecosystem

**Selected**: Option 2 (Pure Python Pipeline)

**Rationale**: The impact analysis and Claude Code dispatch require complex Python logic that N8N handles poorly. The existing N8N workflow remains as-is for changelog generation; Python pipeline consumes its output.

---

### Decision 2: Update Branch Strategy

**Options Considered**:
1. **Single Update Branch**: All updates go to `nautilus-update` branch
   - Pros: Simple, one PR to review
   - Cons: Harder to track individual releases
2. **Version-Specific Branches**: `update/v1.222.0` for each version
   - Pros: Clean history, easy rollback
   - Cons: More branches to manage

**Selected**: Option 2 (Version-Specific Branches)

**Rationale**: Easier to identify which changes came from which NautilusTrader version. Enables selective cherry-picking if needed.

---

### Decision 3: Claude Code Integration

**Options Considered**:
1. **Subprocess Dispatch**: Use `subprocess.run(["claude", "--task", ...])`
   - Pros: Simple, uses installed CLI
   - Cons: No programmatic control, harder to capture output
2. **Claude Code SDK**: Use Python SDK for agent dispatch
   - Pros: Better control, async support
   - Cons: Additional dependency

**Selected**: Option 1 (Subprocess Dispatch)

**Rationale**: KISS principle. CLI dispatch is sufficient for this use case. The agent receives task prompt, creates PR, done.

---

## Implementation Strategy

### Phase 1: Foundation (MVP)

**Goal**: Parse changelog, detect breaking changes, generate impact report

**Deliverables**:
- [ ] `scripts/auto_update/__init__.py` - Module structure
- [ ] `scripts/auto_update/parser.py` - Parse changelog.json
- [ ] `scripts/auto_update/analyzer.py` - Grep codebase for impact
- [ ] `scripts/auto_update/models.py` - Pydantic models
- [ ] Unit tests for parser and analyzer

**Dependencies**: Existing `docs/nautilus/nautilus-trader-changelog.json`

---

### Phase 2: Auto-Update & Validation

**Goal**: Update pyproject.toml, run tests, create branch

**Deliverables**:
- [ ] `scripts/auto_update/updater.py` - Update pyproject.toml
- [ ] `scripts/auto_update/validator.py` - Run tests via test-runner
- [ ] `scripts/auto_update/git_ops.py` - Git operations
- [ ] Integration tests with mock pyproject.toml

**Dependencies**: Phase 1

---

### Phase 3: Agent Dispatch & Alerting

**Goal**: Dispatch Claude Code for complex fixes, alert on failures

**Deliverables**:
- [ ] `scripts/auto_update/dispatcher.py` - Claude Code subprocess
- [ ] `scripts/auto_update/notifier.py` - Notification system
- [ ] `scripts/auto_update/cli.py` - CLI interface
- [ ] End-to-end integration tests

**Dependencies**: Phase 2

---

## File Structure

```
scripts/
├── auto_update/
│   ├── __init__.py           # Module exports
│   ├── models.py             # Pydantic: ChangelogEntry, ImpactReport
│   ├── parser.py             # Parse changelog.json
│   ├── analyzer.py           # Grep codebase for impact
│   ├── updater.py            # Update pyproject.toml
│   ├── validator.py          # Run tests
│   ├── git_ops.py            # Git branch/commit/push
│   ├── dispatcher.py         # Claude Code dispatch
│   ├── notifier.py           # Notifications
│   └── cli.py                # CLI entry point
tests/
└── scripts/
    └── auto_update/
        ├── test_parser.py
        ├── test_analyzer.py
        ├── test_updater.py
        └── test_integration.py
```

## API Design

### Public Interface

```python
# CLI entry point
$ python -m scripts.auto_update check          # Parse changelog, show impact
$ python -m scripts.auto_update update         # Auto-update if safe
$ python -m scripts.auto_update update --force # Update even with breaking changes
$ python -m scripts.auto_update dispatch       # Dispatch Claude Code
```

### Core Models

```python
from pydantic import BaseModel
from enum import Enum

class Severity(str, Enum):
    CRITICAL = "critical"  # Breaks compilation
    HIGH = "high"          # Breaks tests
    MEDIUM = "medium"      # Deprecation warnings
    LOW = "low"            # Minor API changes

class BreakingChange(BaseModel):
    description: str
    affected_pattern: str  # Regex pattern to grep
    severity: Severity

class ImpactReport(BaseModel):
    version: str
    breaking_changes: list[BreakingChange]
    affected_files: list[str]
    can_auto_update: bool
    recommendation: str  # "auto" | "claude" | "human"
```

### Configuration

```python
class AutoUpdateConfig(BaseModel):
    changelog_path: Path = Path("docs/nautilus/nautilus-trader-changelog.json")
    source_dirs: list[Path] = [Path("strategies"), Path("scripts")]
    branch_prefix: str = "update/v"
    dry_run: bool = False
    dispatch_threshold: Severity = Severity.MEDIUM  # Dispatch Claude for MEDIUM+
```

## Testing Strategy

### Unit Tests
- [ ] Test parser extracts breaking changes correctly
- [ ] Test analyzer greps patterns in source files
- [ ] Test updater modifies pyproject.toml correctly
- [ ] Test git_ops creates branches/commits

### Integration Tests
- [ ] Test full pipeline with mock changelog
- [ ] Test dispatcher subprocess with mock Claude response
- [ ] Test notification hooks

### Manual Testing
- [ ] Run against real changelog
- [ ] Verify impact report accuracy
- [ ] Test Claude Code dispatch

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| False positive detection | Unnecessary work | Medium | Review impact reports before action |
| Claude dispatch fails | Update stuck | Low | Fallback to human notification |
| Broken auto-update | Can't sync | Medium | Always create PR, never merge auto |
| Missing breaking change | Runtime errors | Low | Comprehensive grep patterns |

## Dependencies

### External Dependencies
- NautilusTrader (obviously)
- pydantic >= 2.0 (data models)
- click (CLI interface)
- requests (GitHub API if needed)

### Internal Dependencies
- Existing N8N workflow (changelog generation)
- test-runner agent (validation)
- github-workflow skill (PR creation)

## Acceptance Criteria

- [ ] Daily changelog parsing works (< 6 hour detection latency)
- [ ] Impact analysis identifies 90%+ of affected files
- [ ] Auto-update works for simple version bumps
- [ ] Claude dispatch creates valid PRs
- [ ] All unit tests passing (coverage > 80%)
- [ ] Documentation updated

---

## Post-Design Constitution Re-Evaluation

**Date**: 2025-12-29
**Artifacts Reviewed**: plan.md, research.md, data-model.md, contracts/cli-interface.md, quickstart.md

### Principle Alignment (Post-Design)

| Principle | Status | Evidence |
|-----------|--------|----------|
| Black Box Design | ✅ PASS | Modules (parser, analyzer, updater, dispatcher) have clean interfaces per data-model.md |
| KISS & YAGNI | ✅ PASS | Minimal models, no ML, reuses existing N8N + changelog.json |
| Native First | ✅ PASS | Uses existing test-runner, github-workflow skill, N8N infrastructure |
| Performance | ✅ PASS | Daily cron, no real-time; streaming not needed (JSON files) |
| TDD Discipline | ✅ PASS | Test strategy defined in plan.md Phase structure |

### Agent Guidelines Alignment

| Guideline | Status | Evidence |
|-----------|--------|----------|
| Use test-runner for tests | ✅ PASS | validator.py uses test-runner agent per plan.md |
| Use github-workflow for PRs | ✅ PASS | Listed as internal dependency |
| Alpha-debug after implementation | ✅ WILL TRIGGER | Part of Phase 3 validation |

### Prohibited Actions Check (Post-Design)

| Action | Status | Notes |
|--------|--------|-------|
| `df.iterrows()` | ✅ N/A | No pandas in design |
| Reimplement native | ✅ N/A | Uses existing changelog generation |
| Create report files | ⚠️ JUSTIFIED | Impact reports are core feature per spec US2 |
| `--no-verify` | ✅ N/A | git_ops.py will respect hooks |

### Quality Gates Verification

**Pre-Commit** (will enforce during implementation):
- [ ] All tests pass → validator.py
- [ ] Code formatted → ruff in CI
- [ ] Linting clean → ruff check
- [ ] Coverage maintained → pytest-cov

**Pre-Merge**:
- [ ] PR description → github-workflow skill
- [ ] Alpha-debug verification → Phase 3
- [ ] Documentation updated → quickstart.md exists

### Final Verdict

**✅ APPROVED FOR IMPLEMENTATION**

No constitution violations. All clarifications resolved in research.md. Design follows KISS principles and reuses existing infrastructure.

### Implementation Priority

1. **Phase 1** (MVP): parser.py, analyzer.py, models.py - Enables manual `check` command
2. **Phase 2**: updater.py, git_ops.py, validator.py - Enables `update` command
3. **Phase 3**: dispatcher.py, notifier.py, cli.py - Full autonomy
