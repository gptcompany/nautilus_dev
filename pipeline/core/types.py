"""
Core types for the Pipeline Framework.

Defines enums, dataclasses, and type aliases used across the pipeline.
"""

# Python 3.10 compatibility
import datetime as _dt
from dataclasses import dataclass, field
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from enum import Enum, auto
from typing import Any


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


class PipelineStatus(Enum):
    """Pipeline execution status."""

    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    PENDING_APPROVAL = auto()
    COMPLETED = auto()
    FAILED = auto()


class Confidence(Enum):
    """
    Confidence level for stage results.

    Used by HITL to determine if human review is needed.
    """

    HIGH_CONFIDENCE = auto()  # Auto-proceed
    MEDIUM_CONFIDENCE = auto()  # Log, proceed with caution
    LOW_CONFIDENCE = auto()  # Require human review
    CONFLICT = auto()  # Multiple sources disagree
    UNSOLVABLE = auto()  # Cannot determine, escalate


class StageType(Enum):
    """Pipeline stage types following ML4Trading flow."""

    DATA = "data"
    ALPHA = "alpha"
    RISK = "risk"
    EXECUTION = "execution"
    MONITORING = "monitoring"


@dataclass
class StageResult:
    """
    Result from a pipeline stage execution.

    Attributes:
        stage: The stage type that produced this result
        status: Execution status
        confidence: Confidence level for HITL gating
        output: Stage output data (Any type for flexibility)
        metadata: Additional metadata dict
        timestamp: When the result was produced
        needs_human_review: Flag for explicit human review requirement
        review_reason: Explanation if human review is needed
    """

    stage: StageType
    status: PipelineStatus
    confidence: Confidence
    output: Any
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_utc_now)
    needs_human_review: bool = False
    review_reason: str | None = None

    def is_successful(self) -> bool:
        """Check if stage completed successfully."""
        return self.status == PipelineStatus.COMPLETED

    def requires_approval(self) -> bool:
        """Check if this result requires human approval."""
        return self.needs_human_review or self.confidence in (
            Confidence.LOW_CONFIDENCE,
            Confidence.CONFLICT,
            Confidence.UNSOLVABLE,
        )


@dataclass
class ValidationResult:
    """
    Result from a single validation source.

    Used by ConfidenceScorer to aggregate multiple validation results.
    """

    source: str
    score: float | None
    passed: bool
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressEvent:
    """Event emitted during pipeline execution for monitoring."""

    pipeline_id: str
    stage: StageType
    status: PipelineStatus
    progress_pct: float = 0.0
    message: str = ""
    timestamp: datetime = field(default_factory=_utc_now)
