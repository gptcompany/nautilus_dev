# Data Model: NautilusTrader Auto-Update Pipeline

**Feature**: 023-nautilus-auto-update
**Date**: 2025-12-29

## Entity Relationship

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            DATA FLOW                                         │
└──────────────────────────────────────────────────────────────────────────────┘

                    [N8N Workflow]
                         │
                         ▼
┌─────────────────────────────────────────────┐
│ ChangelogData (existing JSON)               │
│   docs/nautilus/nautilus-trader-changelog.json │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ ChangelogEntry (parsed)                     │
│   - version, stable_version                 │
│   - breaking_changes[], bug_list[]          │
│   - timestamp                               │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│ ImpactReport                                │
│   - affected_files[]                        │
│   - can_auto_update (bool)                  │
│   - recommendation (enum)                   │
│   - confidence_score (0-100)                │
└──────────────────┬──────────────────────────┘
                   │
          ┌───────┴───────┐
          ▼               ▼
┌──────────────────┐ ┌──────────────────┐
│ UpdateResult     │ │ DispatchResult   │
│ (auto-update)    │ │ (Claude dispatch)│
│ - branch_name    │ │ - task_prompt    │
│ - pr_url         │ │ - agent_id       │
│ - test_results   │ │ - pr_url         │
└──────────────────┘ └──────────────────┘
```

---

## Pydantic Models

### Core Enums

```python
# scripts/auto_update/models.py

from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import datetime

class Severity(str, Enum):
    """Severity of a breaking change."""
    CRITICAL = "critical"  # Compilation breaks, import errors
    HIGH = "high"          # Tests fail, runtime errors
    MEDIUM = "medium"      # Deprecation warnings, API changes
    LOW = "low"            # Minor signature changes, type hints

class Recommendation(str, Enum):
    """Action recommendation based on impact analysis."""
    AUTO = "auto"          # Safe to auto-update (confidence >= 85)
    DELAYED = "delayed"    # Auto-merge after 24h review window (confidence 65-84)
    MANUAL = "manual"      # Requires human review (confidence < 65)
    BLOCKED = "blocked"    # Critical breaking changes, do not proceed

class ConfidenceLevel(str, Enum):
    """Confidence level for update safety."""
    VERY_HIGH = "very_high"  # >= 85
    HIGH = "high"            # 65-84
    NEUTRAL = "neutral"      # 40-64
    LOW = "low"              # < 40
```

### Input Models (from changelog.json)

```python
class OpenIssue(BaseModel):
    """GitHub issue from changelog."""
    number: int
    title: str
    state: str
    labels: list[str]
    created_at: datetime
    updated_at: datetime
    author: str
    url: str
    comments: int

class ChangelogData(BaseModel):
    """Raw changelog data from N8N-generated JSON."""
    timestamp: datetime
    stable_version: str
    nightly_commits: int
    breaking_changes: list[str]  # May be empty
    open_issues: dict  # Contains issues_list, bug_list, feature_list

class BreakingChange(BaseModel):
    """Parsed breaking change with impact analysis."""
    description: str
    affected_pattern: str = Field(
        description="Regex pattern to grep in codebase"
    )
    severity: Severity
    migration_guide: str | None = None
```

### Analysis Models

```python
class AffectedFile(BaseModel):
    """File impacted by a breaking change."""
    path: Path
    line_numbers: list[int]
    breaking_change: BreakingChange
    can_auto_fix: bool = False
    fix_type: str | None = None  # "import_rename" | "method_rename" | None

class ImpactReport(BaseModel):
    """Complete impact analysis for a version update."""
    version: str
    previous_version: str | None
    breaking_changes: list[BreakingChange]
    affected_files: list[AffectedFile]
    total_affected_lines: int
    confidence_score: float = Field(ge=0, le=100)
    confidence_level: ConfidenceLevel
    can_auto_update: bool
    recommendation: Recommendation
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def should_dispatch_claude(self) -> bool:
        """Check if Claude Code should handle this update."""
        return (
            self.recommendation == Recommendation.MANUAL
            and not any(bc.severity == Severity.CRITICAL for bc in self.breaking_changes)
        )
```

### Operation Models

```python
class TestResult(BaseModel):
    """Result of running test suite."""
    passed: bool
    total_tests: int
    failed_tests: int
    skipped_tests: int
    failed_test_names: list[str]
    duration_seconds: float
    coverage_percent: float | None = None

class UpdateResult(BaseModel):
    """Result of auto-update operation."""
    success: bool
    version: str
    branch_name: str
    pr_url: str | None
    test_result: TestResult | None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DispatchResult(BaseModel):
    """Result of Claude Code dispatch."""
    dispatched: bool
    task_prompt: str
    agent_id: str | None = None
    pr_url: str | None = None
    error_message: str | None = None
    timeout_reached: bool = False
```

### Configuration Model

```python
class AutoUpdateConfig(BaseModel):
    """Configuration for auto-update pipeline."""

    # Paths
    changelog_path: Path = Path("docs/nautilus/nautilus-trader-changelog.json")
    source_dirs: list[Path] = [
        Path("strategies"),
        Path("scripts"),
        Path("tests"),
    ]
    pyproject_path: Path = Path("pyproject.toml")

    # Git settings
    branch_prefix: str = "update/v"
    remote: str = "origin"
    base_branch: str = "master"

    # Confidence thresholds
    auto_merge_threshold: int = 85  # Confidence score for auto-merge
    delayed_merge_threshold: int = 65  # Confidence score for delayed merge

    # Timeouts
    test_timeout_seconds: int = 600  # 10 minutes
    claude_timeout_seconds: int = 1800  # 30 minutes

    # Behavior
    dry_run: bool = False
    skip_tests: bool = False

    # Notifications
    discord_webhook_url: str | None = None
    email_recipient: str | None = None
```

---

## State Transitions

```
                     ┌──────────────────────────────────────────────────┐
                     │              PIPELINE STATES                     │
                     └──────────────────────────────────────────────────┘

    [idle]
       │
       ▼ (changelog updated)
  ┌─────────┐
  │ parsing │──────────────────────────────────────────┐
  └────┬────┘                                          │
       │                                               │
       ▼                                               │ (parse error)
  ┌───────────┐                                        │
  │ analyzing │────────────────────────────────────────┤
  └─────┬─────┘                                        │
        │                                              │
        ├──────────────────────────┐                   │
        │                          │                   │
        ▼                          ▼                   │
   ┌──────────┐            ┌───────────────┐           │
   │ updating │            │ dispatching   │           │
   │ (auto)   │            │ (Claude Code) │           │
   └────┬─────┘            └───────┬───────┘           │
        │                          │                   │
        ▼                          ▼                   │
   ┌──────────┐            ┌───────────────┐           │
   │ testing  │            │ monitoring    │           │
   └────┬─────┘            │ (wait for PR) │           │
        │                  └───────┬───────┘           │
        │                          │                   │
        ├─────────────────────────────────────────────►│
        │                          │                   │
        ▼                          ▼                   ▼
   ┌──────────┐            ┌───────────────┐     ┌─────────┐
   │ pr_ready │            │ pr_created    │     │ failed  │
   └────┬─────┘            └───────┬───────┘     └────┬────┘
        │                          │                   │
        ├─────────────────────────►│                   │
        │                          │                   │
        ▼                          ▼                   ▼
   ┌──────────────────────────────────────────────────────┐
   │                      notifying                        │
   └──────────────────────────────────────────────────────┘
        │
        ▼
     [idle]
```

---

## Validation Rules

### ImpactReport Validation

```python
# Invariants
- confidence_score in [0, 100]
- confidence_level matches score:
  - VERY_HIGH if score >= 85
  - HIGH if score >= 65
  - NEUTRAL if score >= 40
  - LOW otherwise
- can_auto_update is True only if:
  - No CRITICAL severity breaking changes
  - confidence_score >= 65
- recommendation follows confidence_level:
  - VERY_HIGH → AUTO
  - HIGH → DELAYED
  - NEUTRAL/LOW → MANUAL
  - CRITICAL breaking change → BLOCKED
```

### UpdateResult Validation

```python
# Invariants
- If success is True:
  - branch_name must be non-empty
  - pr_url must be non-empty (PR was created)
- If success is False:
  - error_message must be non-empty
```

---

## Example Data

### Input: changelog.json

```json
{
  "timestamp": "2025-12-29T00:00:29.251Z",
  "stable_version": "v1.221.0",
  "nightly_commits": 50,
  "breaking_changes": [
    "Removed deprecated `Strategy.on_tick` method, use `on_quote_tick` instead",
    "Changed `BarType.from_str` signature to require venue parameter"
  ],
  "open_issues": {
    "total": 15500,
    "bugs": 500,
    "features": 15250,
    "bug_list": [...]
  }
}
```

### Output: ImpactReport

```json
{
  "version": "1.222.0",
  "previous_version": "1.221.0",
  "breaking_changes": [
    {
      "description": "Removed deprecated `Strategy.on_tick` method",
      "affected_pattern": "def on_tick\\(",
      "severity": "high",
      "migration_guide": "Replace on_tick with on_quote_tick"
    }
  ],
  "affected_files": [
    {
      "path": "strategies/production/btc_momentum.py",
      "line_numbers": [45, 78],
      "breaking_change": {...},
      "can_auto_fix": true,
      "fix_type": "method_rename"
    }
  ],
  "total_affected_lines": 12,
  "confidence_score": 72.5,
  "confidence_level": "high",
  "can_auto_update": false,
  "recommendation": "delayed",
  "generated_at": "2025-12-29T05:00:00Z"
}
```
