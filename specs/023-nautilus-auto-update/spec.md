# Spec 023: NautilusTrader Auto-Update Pipeline

## Overview

Autonomous pipeline to detect NautilusTrader nightly changes, update local infrastructure, and validate compatibility - preventing tech debt accumulation.

## Problem Statement

NautilusTrader nightly releases frequently with:
- Breaking API changes
- New adapter features
- Bug fixes we depend on
- Schema changes

Manual updates lead to:
- Stale code incompatible with latest features
- Missed bug fixes
- Accumulated tech debt
- "Mega mess infrastrutturale"

## Goals

1. **Auto-Detection**: Monitor nightly releases and changelog
2. **Impact Analysis**: Identify breaking changes affecting our codebase
3. **Auto-Update**: Update dependencies and adapt code where possible
4. **Validation**: Run tests to verify compatibility
5. **Alerting**: Notify when manual intervention required

## User Stories

### US1: Changelog Monitoring (P1 - MVP)
**As a** developer,
**I want** automatic monitoring of NautilusTrader releases,
**So that** I'm aware of changes immediately.

**Acceptance Criteria**:
- [ ] Daily check of GitHub releases/nightly wheels
- [ ] Parse changelog for breaking changes
- [ ] Store changes in `docs/nautilus/nautilus-trader-changelog.json`
- [ ] Update `docs/nautilus/nautilus-trader-changelog.md`

### US2: Breaking Change Detection (P1 - MVP)
**As a** developer,
**I want** automatic detection of breaking changes affecting my code,
**So that** I can prioritize fixes.

**Acceptance Criteria**:
- [ ] Grep codebase for deprecated/changed APIs
- [ ] Cross-reference with our imports and usage patterns
- [ ] Generate impact report with affected files
- [ ] Severity classification (CRITICAL, HIGH, MEDIUM, LOW)

### US3: Dependency Update (P2)
**As a** developer,
**I want** automatic dependency updates,
**So that** I stay current without manual work.

**Acceptance Criteria**:
- [ ] Update `pyproject.toml` with new nightly version
- [ ] Run `uv sync` to update lock file
- [ ] Commit changes to update branch
- [ ] Create PR for review

### US4: Compatibility Validation (P2)
**As a** developer,
**I want** automatic test runs after updates,
**So that** I know if updates break anything.

**Acceptance Criteria**:
- [ ] Run `uv run pytest` on update branch
- [ ] Capture test results and failures
- [ ] Annotate PR with test status
- [ ] Block merge if tests fail

### US5: Auto-Fix Simple Changes (P3)
**As a** developer,
**I want** automatic fixes for simple API changes,
**So that** I spend less time on boilerplate updates.

**Acceptance Criteria**:
- [ ] Regex-based import path updates
- [ ] Simple rename operations (sed/awk)
- [ ] Type hint updates for changed signatures
- [ ] Commit fixes to update branch

### US6: Claude Code Integration (P3)
**As a** developer,
**I want** Claude Code to autonomously handle complex updates,
**So that** I only intervene for architectural decisions.

**Acceptance Criteria**:
- [ ] Spawn Claude Code agent for complex fixes
- [ ] Agent reads impact report and attempts fixes
- [ ] Agent runs tests and iterates
- [ ] Agent creates PR with detailed description

## Requirements

### Functional Requirements

#### FR-001: GitHub Release Monitor
```python
# Cron job or N8N workflow
def check_nautilus_releases() -> list[Release]:
    """Check for new NautilusTrader releases since last check."""
    # Uses GitHub API or PyPI API
    # Returns list of new releases with changelogs
```

#### FR-002: Changelog Parser
```python
def parse_changelog(release: Release) -> ChangelogEntry:
    """Parse release notes for breaking changes."""
    return ChangelogEntry(
        version=release.version,
        breaking_changes=[...],
        new_features=[...],
        bug_fixes=[...],
        deprecations=[...],
    )
```

#### FR-003: Impact Analyzer
```python
def analyze_impact(changes: ChangelogEntry) -> ImpactReport:
    """Analyze impact of changes on our codebase."""
    # Grep for affected imports, classes, functions
    # Return report with affected files and severity
```

#### FR-004: Auto-Updater
```python
def auto_update(version: str) -> UpdateResult:
    """Update NautilusTrader to specified version."""
    # Update pyproject.toml
    # Run uv sync
    # Commit to branch
```

#### FR-005: Test Runner
```python
def validate_update() -> TestResult:
    """Run tests to validate update compatibility."""
    # Use test-runner agent
    # Capture results
    # Return pass/fail with details
```

#### FR-006: Claude Code Agent Dispatch
```python
def dispatch_claude_fix(impact_report: ImpactReport) -> FixResult:
    """Dispatch Claude Code to fix complex issues."""
    # Create task with impact report context
    # Claude Code attempts fixes
    # Returns result with PR link
```

### Non-Functional Requirements

#### NFR-001: Frequency
- Daily check at 06:00 UTC (after nightly builds)
- Immediate processing of detected changes

#### NFR-002: Autonomy
- Fully autonomous for simple updates (import paths, renames)
- Human approval required for:
  - Architectural changes
  - New dependencies
  - Test failures requiring logic changes

#### NFR-003: Traceability
- All changes tracked in git
- Each update creates separate branch
- Full audit trail of automated changes

## Technical Design

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  N8N Workflow (Scheduler)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ GitHub API  │  │ Changelog   │  │ Impact Analyzer     │  │
│  │ Monitor     │──│ Parser      │──│ (Grep codebase)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│        │                │                    │              │
│        ▼                ▼                    ▼              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Decision Gate                          │    │
│  │  Simple change? → Auto-update + Test               │    │
│  │  Complex change? → Dispatch Claude Code            │    │
│  │  Architectural? → Alert human                      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Claude Code Agent                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Read Impact │  │ Apply Fixes │  │ Run Tests           │  │
│  │ Report      │──│ (Edit tool) │──│ (test-runner agent) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Create PR with Results                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
nautilus_dev/
├── scripts/
│   └── auto_update/
│       ├── __init__.py
│       ├── monitor.py          # GitHub release monitor
│       ├── parser.py           # Changelog parser
│       ├── analyzer.py         # Impact analyzer
│       ├── updater.py          # Dependency updater
│       └── dispatcher.py       # Claude Code dispatcher
├── .github/
│   └── workflows/
│       └── nautilus-update.yml # GitHub Actions workflow
└── docs/
    └── nautilus/
        ├── nautilus-trader-changelog.json  # Machine-readable
        └── nautilus-trader-changelog.md    # Human-readable
```

### Integration Points

- **N8N Workflow**: Existing at `/media/sam/1TB/devteam1` for scheduling
- **Claude Code**: CLI invocation with task prompt
- **GitHub Actions**: For PR creation and test runs
- **test-runner agent**: For validation

## Dependencies

### External Dependencies
- GitHub API access
- PyPI API access (for version checking)
- N8N instance (existing)
- Claude Code CLI

### Internal Dependencies
- Spec 022 (Academic Research Pipeline) - similar autonomous pattern
- test-runner agent - for validation
- github-workflow skill - for PR creation

## Success Metrics

- **Detection latency**: < 6 hours from release to detection
- **Auto-fix rate**: > 70% of simple changes fixed automatically
- **Test pass rate**: > 95% after auto-updates
- **Human intervention**: < 30% of updates require manual work

## Priority Justification

CRITICAL for long-term maintainability:
1. NautilusTrader releases frequently (weekly nightly)
2. Manual updates accumulate tech debt
3. Breaking changes can break live trading
4. Autonomous pipeline reduces developer burden
