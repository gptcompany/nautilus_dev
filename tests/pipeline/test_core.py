"""Tests for pipeline core components."""

import tempfile
from pathlib import Path

from pipeline.core.state import PipelineState
from pipeline.core.types import (
    Confidence,
    PipelineStatus,
    StageResult,
    StageType,
    ValidationResult,
)
from pipeline.hitl.confidence import ConfidenceScorer, ConfidenceThresholds


class TestPipelineStatus:
    """Test PipelineStatus enum."""

    def test_all_statuses_exist(self):
        """Verify all expected statuses."""
        assert PipelineStatus.IDLE
        assert PipelineStatus.RUNNING
        assert PipelineStatus.PAUSED
        assert PipelineStatus.PENDING_APPROVAL
        assert PipelineStatus.COMPLETED
        assert PipelineStatus.FAILED


class TestConfidence:
    """Test Confidence enum."""

    def test_all_confidence_levels_exist(self):
        """Verify all expected confidence levels."""
        assert Confidence.HIGH_CONFIDENCE
        assert Confidence.MEDIUM_CONFIDENCE
        assert Confidence.LOW_CONFIDENCE
        assert Confidence.CONFLICT
        assert Confidence.UNSOLVABLE


class TestStageType:
    """Test StageType enum."""

    def test_all_stage_types_exist(self):
        """Verify all expected stage types."""
        assert StageType.DATA.value == "data"
        assert StageType.ALPHA.value == "alpha"
        assert StageType.RISK.value == "risk"
        assert StageType.EXECUTION.value == "execution"
        assert StageType.MONITORING.value == "monitoring"


class TestStageResult:
    """Test StageResult dataclass."""

    def test_creation(self):
        """Test basic creation."""
        result = StageResult(
            stage=StageType.DATA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output={"data": "test"},
        )
        assert result.stage == StageType.DATA
        assert result.status == PipelineStatus.COMPLETED
        assert result.is_successful()

    def test_requires_approval_low_confidence(self):
        """Test approval required for low confidence."""
        result = StageResult(
            stage=StageType.ALPHA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.LOW_CONFIDENCE,
            output=None,
        )
        assert result.requires_approval()

    def test_requires_approval_explicit(self):
        """Test approval required when explicitly set."""
        result = StageResult(
            stage=StageType.ALPHA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output=None,
            needs_human_review=True,
        )
        assert result.requires_approval()

    def test_no_approval_needed_high_confidence(self):
        """Test no approval needed for high confidence."""
        result = StageResult(
            stage=StageType.DATA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output=None,
        )
        assert not result.requires_approval()


class TestPipelineState:
    """Test PipelineState management."""

    def test_create_state(self):
        """Test state creation."""
        state = PipelineState.create(config={"key": "value"})
        assert state.pipeline_id
        assert state.status == PipelineStatus.IDLE
        assert state.config == {"key": "value"}

    def test_can_proceed_idle(self):
        """Test can proceed from idle."""
        state = PipelineState.create()
        state.status = PipelineStatus.RUNNING
        assert state.can_proceed()

    def test_cannot_proceed_failed(self):
        """Test cannot proceed when failed."""
        state = PipelineState.create()
        state.status = PipelineStatus.FAILED
        assert not state.can_proceed()

    def test_cannot_proceed_pending_approval(self):
        """Test cannot proceed when pending approval."""
        state = PipelineState.create()
        state.status = PipelineStatus.PENDING_APPROVAL
        assert not state.can_proceed()

    def test_get_next_stage_from_start(self):
        """Test getting first stage."""
        state = PipelineState.create()
        assert state.get_next_stage() == StageType.DATA

    def test_get_next_stage_after_data(self):
        """Test getting stage after DATA."""
        state = PipelineState.create()
        state.current_stage = StageType.DATA
        assert state.get_next_stage() == StageType.ALPHA

    def test_get_next_stage_at_end(self):
        """Test no next stage at end."""
        state = PipelineState.create()
        state.current_stage = StageType.MONITORING
        assert state.get_next_stage() is None

    def test_checkpoint_save_load(self):
        """Test checkpoint save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir)

            # Create state with result
            state = PipelineState.create(config={"test": True})
            state.current_stage = StageType.DATA
            state.status = PipelineStatus.RUNNING
            state.stage_results[StageType.DATA] = StageResult(
                stage=StageType.DATA,
                status=PipelineStatus.COMPLETED,
                confidence=Confidence.HIGH_CONFIDENCE,
                output={"loaded": True},
            )

            # Save checkpoint
            checkpoint_path = state.save_checkpoint(checkpoint_dir)
            assert checkpoint_path.exists()

            # Load checkpoint
            loaded_state = PipelineState.load_checkpoint(checkpoint_path)
            assert loaded_state.pipeline_id == state.pipeline_id
            assert loaded_state.current_stage == StageType.DATA
            assert loaded_state.config == {"test": True}
            assert StageType.DATA in loaded_state.stage_results
            assert loaded_state.stage_results[StageType.DATA].output == {"loaded": True}


class TestConfidenceScorer:
    """Test ConfidenceScorer."""

    def test_empty_validations(self):
        """Test empty input returns UNSOLVABLE."""
        scorer = ConfidenceScorer()
        assert scorer.score([]) == Confidence.UNSOLVABLE

    def test_high_confidence(self):
        """Test high confidence scoring."""
        scorer = ConfidenceScorer()
        validations = [
            ValidationResult(source="a", score=0.9, passed=True),
            ValidationResult(source="b", score=0.95, passed=True),
            ValidationResult(source="c", score=0.88, passed=True),
        ]
        assert scorer.score(validations) == Confidence.HIGH_CONFIDENCE

    def test_medium_confidence(self):
        """Test medium confidence scoring."""
        scorer = ConfidenceScorer()
        validations = [
            ValidationResult(source="a", score=0.7, passed=True),
            ValidationResult(source="b", score=0.75, passed=True),
            ValidationResult(source="c", score=0.72, passed=True),
        ]
        assert scorer.score(validations) == Confidence.MEDIUM_CONFIDENCE

    def test_low_confidence(self):
        """Test low confidence scoring."""
        scorer = ConfidenceScorer()
        validations = [
            ValidationResult(source="a", score=0.5, passed=True),
            ValidationResult(source="b", score=0.45, passed=False),
        ]
        assert scorer.score(validations) == Confidence.LOW_CONFIDENCE

    def test_conflict_detection(self):
        """Test conflict detection."""
        scorer = ConfidenceScorer()
        validations = [
            ValidationResult(source="a", score=0.9, passed=True),
            ValidationResult(source="b", score=0.85, passed=False),
        ]
        assert scorer.score(validations) == Confidence.CONFLICT

    def test_custom_thresholds(self):
        """Test custom thresholds."""
        thresholds = ConfidenceThresholds(high=0.95, medium=0.8)
        scorer = ConfidenceScorer(thresholds=thresholds)

        validations = [
            ValidationResult(source="a", score=0.9, passed=True),
            ValidationResult(source="b", score=0.88, passed=True),
        ]
        # With higher thresholds, this should be MEDIUM not HIGH
        assert scorer.score(validations) == Confidence.MEDIUM_CONFIDENCE

    def test_score_with_details(self):
        """Test detailed scoring."""
        scorer = ConfidenceScorer()
        validations = [
            ValidationResult(source="a", score=0.9, passed=True),
            ValidationResult(source="b", score=0.85, passed=True),
        ]
        confidence, details = scorer.score_with_details(validations)

        assert confidence == Confidence.HIGH_CONFIDENCE
        assert details["avg_score"] == 0.875
        assert details["num_validations"] == 2
        assert details["agreement_rate"] == 1.0
        assert not details["conflict"]
