"""Event dataclasses for regime detection ensemble.

Provides dataclasses for regime change events and detector votes
used by the ensemble voting system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from strategies.common.regime_detection.types import RegimeState


@dataclass(frozen=True)
class RegimeVote:
    """Single detector's regime assessment.

    Used in ensemble aggregation logic to collect votes
    from multiple detectors.

    Attributes:
        detector_id: Unique identifier for the detector.
        regime: The regime classification from this detector.
        confidence: Confidence score (0.0-1.0) for the classification.
        timestamp: When this vote was cast.
    """

    detector_id: str
    regime: RegimeState
    confidence: float
    timestamp: datetime


@dataclass(frozen=True)
class RegimeChangeEvent:
    """Event emitted when ensemble confirms regime transition.

    Contains full audit trail including old regime, new regime,
    confidence, and per-detector votes.

    Attributes:
        old_regime: Previous regime state.
        new_regime: New regime state.
        confidence: Aggregate confidence in the transition.
        timestamp: When the transition was detected.
        votes: Per-detector votes that led to this decision.
    """

    old_regime: RegimeState
    new_regime: RegimeState
    confidence: float
    timestamp: datetime
    votes: list[RegimeVote] = field(default_factory=list)

    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"RegimeChangeEvent({self.old_regime.name} -> {self.new_regime.name}, "
            f"confidence={self.confidence:.2f}, votes={len(self.votes)})"
        )
