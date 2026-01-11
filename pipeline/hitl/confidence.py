"""
Confidence scoring with multi-CAS (multi-source agreement) pattern.

Aggregates validation results from multiple sources to determine
overall confidence level for HITL gating.
"""

from dataclasses import dataclass, field

from pipeline.core.types import Confidence, ValidationResult


@dataclass
class ConfidenceThresholds:
    """
    Thresholds for confidence level determination.

    Attributes:
        high: Score threshold for HIGH_CONFIDENCE (0.85)
        medium: Score threshold for MEDIUM_CONFIDENCE (0.65)
        low: Score threshold for LOW_CONFIDENCE (0.4)
        agreement_high: Agreement rate for HIGH (0.9)
        agreement_medium: Agreement rate for MEDIUM (0.7)
    """

    high: float = 0.85
    medium: float = 0.65
    low: float = 0.4
    agreement_high: float = 0.9
    agreement_medium: float = 0.7


@dataclass
class AgreementResult:
    """Result of agreement analysis across validation sources."""

    rate: float  # 0.0 to 1.0
    conflict: bool  # Direct contradiction detected
    sources_agree: list[str] = field(default_factory=list)
    sources_disagree: list[str] = field(default_factory=list)


class ConfidenceScorer:
    """
    Score confidence based on multiple validation sources.

    Implements multi-CAS (Cascading Approval System) pattern from N8N specs.

    Confidence Levels:
        - HIGH_CONFIDENCE: All sources agree, scores > high_threshold
        - MEDIUM_CONFIDENCE: Most sources agree, scores > medium_threshold
        - LOW_CONFIDENCE: Disagreement or low scores
        - CONFLICT: Sources directly contradict each other
        - UNSOLVABLE: Cannot determine (missing data, errors)

    Example:
        ```python
        scorer = ConfidenceScorer()

        validations = [
            ValidationResult(source="backtest", score=0.9, passed=True),
            ValidationResult(source="risk_check", score=0.85, passed=True),
            ValidationResult(source="overfitting", score=0.7, passed=True),
        ]

        confidence = scorer.score(validations)
        # Returns Confidence.HIGH_CONFIDENCE
        ```
    """

    def __init__(self, thresholds: ConfidenceThresholds | None = None):
        """
        Initialize scorer with thresholds.

        Args:
            thresholds: Custom thresholds, or defaults if None
        """
        self.thresholds = thresholds or ConfidenceThresholds()

    def score(self, validations: list[ValidationResult]) -> Confidence:
        """
        Aggregate multiple validation sources into confidence level.

        Args:
            validations: List of validation results from different sources

        Returns:
            Overall Confidence level
        """
        if not validations:
            return Confidence.UNSOLVABLE

        # Extract scores (filter None)
        scores = [v.score for v in validations if v.score is not None]
        if not scores:
            return Confidence.UNSOLVABLE

        # Check agreement
        agreement = self._check_agreement(validations)

        if agreement.conflict:
            return Confidence.CONFLICT

        avg_score = sum(scores) / len(scores)

        # Determine confidence based on score and agreement
        if avg_score >= self.thresholds.high and agreement.rate >= self.thresholds.agreement_high:
            return Confidence.HIGH_CONFIDENCE
        elif (
            avg_score >= self.thresholds.medium
            and agreement.rate >= self.thresholds.agreement_medium
        ):
            return Confidence.MEDIUM_CONFIDENCE
        elif avg_score >= self.thresholds.low:
            return Confidence.LOW_CONFIDENCE
        else:
            return Confidence.UNSOLVABLE

    def _check_agreement(self, validations: list[ValidationResult]) -> AgreementResult:
        """
        Check agreement across validation sources.

        Args:
            validations: List of validation results

        Returns:
            AgreementResult with agreement rate and conflict flag
        """
        if len(validations) <= 1:
            return AgreementResult(
                rate=1.0,
                conflict=False,
                sources_agree=[v.source for v in validations],
            )

        # Count pass/fail
        passed = [v for v in validations if v.passed]
        failed = [v for v in validations if not v.passed]

        # Check for direct contradiction (some pass, some fail with high confidence)
        conflict = False
        if passed and failed:
            passed_scores = [v.score for v in passed if v.score is not None]
            failed_scores = [v.score for v in failed if v.score is not None]

            # Conflict if both sides have high scores
            if passed_scores and failed_scores:
                avg_passed = sum(passed_scores) / len(passed_scores)
                avg_failed = sum(failed_scores) / len(failed_scores)

                if avg_passed >= self.thresholds.medium and avg_failed >= self.thresholds.medium:
                    conflict = True

        # Calculate agreement rate
        majority = max(len(passed), len(failed))
        agreement_rate = majority / len(validations)

        return AgreementResult(
            rate=agreement_rate,
            conflict=conflict,
            sources_agree=[v.source for v in (passed if len(passed) >= len(failed) else failed)],
            sources_disagree=[v.source for v in (failed if len(passed) >= len(failed) else passed)],
        )

    def score_with_details(
        self,
        validations: list[ValidationResult],
    ) -> tuple[Confidence, dict]:
        """
        Score with detailed breakdown.

        Args:
            validations: List of validation results

        Returns:
            Tuple of (Confidence, details dict)
        """
        confidence = self.score(validations)
        agreement = self._check_agreement(validations)
        scores = [v.score for v in validations if v.score is not None]

        details = {
            "confidence": confidence.name,
            "avg_score": sum(scores) / len(scores) if scores else None,
            "num_validations": len(validations),
            "agreement_rate": agreement.rate,
            "conflict": agreement.conflict,
            "sources_agree": agreement.sources_agree,
            "sources_disagree": agreement.sources_disagree,
            "thresholds": {
                "high": self.thresholds.high,
                "medium": self.thresholds.medium,
                "agreement_high": self.thresholds.agreement_high,
                "agreement_medium": self.thresholds.agreement_medium,
            },
        }

        return confidence, details


def create_validation_from_check(
    source: str,
    passed: bool,
    score: float | None = None,
    message: str = "",
) -> ValidationResult:
    """
    Helper to create ValidationResult from simple check.

    Args:
        source: Name of validation source
        passed: Whether check passed
        score: Optional score (0.0-1.0), defaults to 1.0 if passed else 0.0
        message: Optional message

    Returns:
        ValidationResult
    """
    if score is None:
        score = 1.0 if passed else 0.0

    return ValidationResult(
        source=source,
        score=score,
        passed=passed,
        message=message,
    )
