# NautilusTrader Auto-Update Pipeline
#
# Autonomous pipeline to detect NautilusTrader nightly changes,
# analyze impact on codebase, update dependencies, and validate compatibility.
#
# Usage:
#   python -m scripts.auto_update check          # Parse changelog, show impact
#   python -m scripts.auto_update update         # Auto-update if safe
#   python -m scripts.auto_update update --force # Update even with breaking changes
#   python -m scripts.auto_update dispatch       # Dispatch Claude Code

"""NautilusTrader Auto-Update Pipeline module."""

from scripts.auto_update.models import (
    AutoUpdateConfig,
    Severity,
    Recommendation,
    ConfidenceLevel,
    ChangelogData,
    BreakingChange,
    AffectedFile,
    ImpactReport,
    TestResult,
    UpdateResult,
    DispatchResult,
    OpenIssue,
)

__all__ = [
    # Config
    "AutoUpdateConfig",
    # Enums
    "Severity",
    "Recommendation",
    "ConfidenceLevel",
    # Models
    "ChangelogData",
    "BreakingChange",
    "AffectedFile",
    "ImpactReport",
    "TestResult",
    "UpdateResult",
    "DispatchResult",
    "OpenIssue",
]

__version__ = "0.1.0"
