"""Integration tests for Trading Pipeline Framework.

Tests the full pipeline flow including:
- State management and checkpointing
- Stage execution with HITL gates
- Confidence scoring
- Approval workflow (mocked)
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from pipeline.core.loop import PipelineLoop
from pipeline.core.state import PipelineState
from pipeline.core.types import (
    Confidence,
    PipelineStatus,
    StageResult,
    StageType,
)
from pipeline.hitl.approval import ApprovalGate, ApprovalResponse
from pipeline.hitl.confidence import ConfidenceScorer, ConfidenceThresholds, ValidationResult
from pipeline.stages.base import AbstractStage

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_checkpoint_dir():
    """Create temporary directory for checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_notification_service():
    """Mock notification service for testing."""
    service = MagicMock()
    service.send_approval_request = AsyncMock(return_value=None)
    service.send_progress = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_approval_gate(mock_notification_service):
    """Approval gate that auto-approves everything."""
    gate = ApprovalGate(mock_notification_service)
    gate.request_approval = AsyncMock(
        return_value=ApprovalResponse(approved=True, action="approve", reviewer="test")
    )
    return gate


class MockStage(AbstractStage):
    """Mock stage for testing."""

    def __init__(
        self,
        stage_type: StageType,
        should_pass: bool = True,
        confidence: Confidence = Confidence.HIGH_CONFIDENCE,
    ):
        self._stage_type = stage_type
        self._should_pass = should_pass
        self._confidence = confidence
        self.execute_count = 0

    @property
    def stage_type(self) -> StageType:
        return self._stage_type

    async def execute(self, state: PipelineState) -> StageResult:
        self.execute_count += 1
        return StageResult(
            stage=self._stage_type,
            status=PipelineStatus.COMPLETED if self._should_pass else PipelineStatus.FAILED,
            confidence=self._confidence,
            output={"mock": "data"},
            needs_human_review=self._confidence == Confidence.LOW_CONFIDENCE,
        )

    def validate_input(self, state: PipelineState) -> bool:
        return True


# =============================================================================
# State Management Tests
# =============================================================================


class TestPipelineState:
    """Tests for PipelineState."""

    def test_create_state(self):
        """Test basic state creation."""
        state = PipelineState(
            pipeline_id="test-123",
            current_stage=StageType.DATA,
            status=PipelineStatus.IDLE,
        )
        assert state.pipeline_id == "test-123"
        assert state.current_stage == StageType.DATA
        assert state.status == PipelineStatus.IDLE
        assert state.stage_results == {}

    def test_can_proceed_idle(self):
        """Test can_proceed for IDLE state."""
        state = PipelineState("test", StageType.DATA, PipelineStatus.IDLE)
        assert state.can_proceed() is True

    def test_can_proceed_failed(self):
        """Test can_proceed for FAILED state."""
        state = PipelineState("test", StageType.DATA, PipelineStatus.FAILED)
        assert state.can_proceed() is False

    def test_can_proceed_pending_approval(self):
        """Test can_proceed for PENDING_APPROVAL state."""
        state = PipelineState("test", StageType.DATA, PipelineStatus.PENDING_APPROVAL)
        assert state.can_proceed() is False

    def test_checkpoint_save_load(self, temp_checkpoint_dir):
        """Test state checkpoint save and load."""
        state = PipelineState(
            pipeline_id="checkpoint-test",
            current_stage=StageType.ALPHA,
            status=PipelineStatus.RUNNING,
        )
        state.stage_results[StageType.DATA] = StageResult(
            stage=StageType.DATA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output={"test": "data"},
        )

        # Save checkpoint (pass directory, method generates filename)
        checkpoint_path = state.save_checkpoint(temp_checkpoint_dir)
        assert checkpoint_path.exists()

        # Load checkpoint
        loaded = PipelineState.load_checkpoint(checkpoint_path)
        assert loaded.pipeline_id == "checkpoint-test"
        assert loaded.current_stage == StageType.ALPHA
        assert StageType.DATA in loaded.stage_results


# =============================================================================
# Confidence Scoring Tests
# =============================================================================


class TestConfidenceScorer:
    """Tests for confidence scoring."""

    def test_high_confidence(self):
        """Test high confidence scoring."""
        scorer = ConfidenceScorer(ConfidenceThresholds())
        validations = [
            ValidationResult(source="test1", score=0.95, passed=True),
            ValidationResult(source="test2", score=0.90, passed=True),
        ]
        result = scorer.score(validations)
        assert result == Confidence.HIGH_CONFIDENCE

    def test_medium_confidence(self):
        """Test medium confidence scoring."""
        scorer = ConfidenceScorer(ConfidenceThresholds())
        validations = [
            ValidationResult(source="test1", score=0.75, passed=True),
            ValidationResult(source="test2", score=0.70, passed=True),
        ]
        result = scorer.score(validations)
        assert result == Confidence.MEDIUM_CONFIDENCE

    def test_low_confidence(self):
        """Test low confidence scoring."""
        scorer = ConfidenceScorer(ConfidenceThresholds())
        validations = [
            ValidationResult(source="test1", score=0.50, passed=True),
            ValidationResult(source="test2", score=0.45, passed=False),
        ]
        result = scorer.score(validations)
        assert result == Confidence.LOW_CONFIDENCE

    def test_empty_validations(self):
        """Test with no validations."""
        scorer = ConfidenceScorer(ConfidenceThresholds())
        result = scorer.score([])
        assert result == Confidence.UNSOLVABLE


# =============================================================================
# Pipeline Loop Tests
# =============================================================================


class TestPipelineLoop:
    """Tests for the main pipeline loop."""

    @pytest.mark.asyncio
    async def test_single_stage_execution(self, mock_approval_gate, temp_checkpoint_dir):
        """Test single stage execution."""
        data_stage = MockStage(StageType.DATA)

        loop = PipelineLoop(
            stages=[data_stage],
            approval_gate=mock_approval_gate,
            checkpoint_dir=temp_checkpoint_dir,
            auto_checkpoint=False,
        )

        state = PipelineState("single-stage", StageType.DATA, PipelineStatus.IDLE)
        result = await loop.run(state)

        assert data_stage.execute_count == 1
        assert StageType.DATA in result.stage_results
        assert result.stage_results[StageType.DATA].status == PipelineStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_multi_stage_execution(self, mock_approval_gate, temp_checkpoint_dir):
        """Test multiple stage execution in order."""
        stages = [
            MockStage(StageType.DATA),
            MockStage(StageType.ALPHA),
            MockStage(StageType.RISK),
        ]

        loop = PipelineLoop(
            stages=stages,
            approval_gate=mock_approval_gate,
            checkpoint_dir=temp_checkpoint_dir,
            auto_checkpoint=False,
        )

        state = PipelineState("multi-stage", StageType.DATA, PipelineStatus.IDLE)
        result = await loop.run(state)

        for stage in stages:
            assert stage.execute_count == 1

        assert result.status == PipelineStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_stage_failure_stops_pipeline(self, mock_approval_gate, temp_checkpoint_dir):
        """Test that stage failure stops the pipeline."""
        stages = [
            MockStage(StageType.DATA),
            MockStage(StageType.ALPHA, should_pass=False),  # This will fail
            MockStage(StageType.RISK),
        ]

        loop = PipelineLoop(
            stages=stages,
            approval_gate=mock_approval_gate,
            checkpoint_dir=temp_checkpoint_dir,
            auto_checkpoint=False,
        )

        state = PipelineState("fail-test", StageType.DATA, PipelineStatus.IDLE)
        result = await loop.run(state)

        assert stages[0].execute_count == 1  # DATA ran
        assert stages[1].execute_count == 1  # ALPHA ran and failed
        assert stages[2].execute_count == 0  # RISK never ran
        assert result.status == PipelineStatus.FAILED

    @pytest.mark.asyncio
    async def test_low_confidence_triggers_approval(
        self, mock_notification_service, temp_checkpoint_dir
    ):
        """Test that low confidence triggers approval request."""
        gate = ApprovalGate(mock_notification_service)
        gate.request_approval = AsyncMock(
            return_value=ApprovalResponse(approved=True, action="approve", reviewer="human")
        )

        stages = [
            MockStage(StageType.DATA, confidence=Confidence.LOW_CONFIDENCE),
        ]

        loop = PipelineLoop(
            stages=stages,
            approval_gate=gate,
            checkpoint_dir=temp_checkpoint_dir,
            auto_checkpoint=False,
        )

        state = PipelineState("approval-test", StageType.DATA, PipelineStatus.IDLE)
        result = await loop.run(state)

        # Approval was requested for low confidence
        gate.request_approval.assert_called_once()
        assert result.status == PipelineStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_approval_rejection_stops_pipeline(
        self, mock_notification_service, temp_checkpoint_dir
    ):
        """Test that approval rejection stops pipeline."""
        gate = ApprovalGate(mock_notification_service)
        gate.request_approval = AsyncMock(
            return_value=ApprovalResponse(approved=False, action="reject", reviewer="human")
        )

        stages = [
            MockStage(StageType.DATA, confidence=Confidence.LOW_CONFIDENCE),
            MockStage(StageType.ALPHA),
        ]

        loop = PipelineLoop(
            stages=stages,
            approval_gate=gate,
            checkpoint_dir=temp_checkpoint_dir,
            auto_checkpoint=False,
        )

        state = PipelineState("reject-test", StageType.DATA, PipelineStatus.IDLE)
        result = await loop.run(state)

        assert stages[0].execute_count == 1
        assert stages[1].execute_count == 0  # Never reached
        assert result.status == PipelineStatus.FAILED

    @pytest.mark.asyncio
    async def test_auto_checkpoint(self, mock_approval_gate, temp_checkpoint_dir):
        """Test automatic checkpointing after each stage."""
        stages = [
            MockStage(StageType.DATA),
            MockStage(StageType.ALPHA),
        ]

        loop = PipelineLoop(
            stages=stages,
            approval_gate=mock_approval_gate,
            checkpoint_dir=temp_checkpoint_dir,
            auto_checkpoint=True,
        )

        state = PipelineState("checkpoint-test", StageType.DATA, PipelineStatus.IDLE)
        result = await loop.run(state)

        # Checkpoint file should exist
        checkpoint_files = list(temp_checkpoint_dir.glob("*.json"))
        assert len(checkpoint_files) > 0


# =============================================================================
# Full Pipeline Integration Test
# =============================================================================


class TestFullPipelineIntegration:
    """Full end-to-end pipeline tests."""

    @pytest.mark.asyncio
    async def test_data_to_monitoring_flow(self, mock_approval_gate, temp_checkpoint_dir):
        """Test complete pipeline flow from DATA to MONITORING."""
        stages = [
            MockStage(StageType.DATA),
            MockStage(StageType.ALPHA),
            MockStage(StageType.RISK),
            MockStage(StageType.EXECUTION),
            MockStage(StageType.MONITORING),
        ]

        loop = PipelineLoop(
            stages=stages,
            approval_gate=mock_approval_gate,
            checkpoint_dir=temp_checkpoint_dir,
            auto_checkpoint=True,
        )

        state = PipelineState("full-flow", StageType.DATA, PipelineStatus.IDLE)
        result = await loop.run(state)

        # All stages executed
        for stage in stages:
            assert stage.execute_count == 1, f"{stage.stage_type} not executed"

        # All results recorded
        for stage_type in [
            StageType.DATA,
            StageType.ALPHA,
            StageType.RISK,
            StageType.EXECUTION,
            StageType.MONITORING,
        ]:
            assert stage_type in result.stage_results

        # Pipeline completed successfully
        assert result.status == PipelineStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_resume_from_checkpoint(self, mock_approval_gate, temp_checkpoint_dir):
        """Test resuming pipeline from checkpoint."""
        # Create initial state with DATA completed
        initial_state = PipelineState("resume-test", StageType.ALPHA, PipelineStatus.RUNNING)
        initial_state.stage_results[StageType.DATA] = StageResult(
            stage=StageType.DATA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output={"data": "loaded"},
        )

        # Save checkpoint (pass directory, method generates filename)
        checkpoint_path = initial_state.save_checkpoint(temp_checkpoint_dir)

        # Load and resume
        resumed_state = PipelineState.load_checkpoint(checkpoint_path)

        stages = [
            MockStage(StageType.DATA),  # Should be skipped
            MockStage(StageType.ALPHA),
            MockStage(StageType.RISK),
        ]

        loop = PipelineLoop(
            stages=stages,
            approval_gate=mock_approval_gate,
            checkpoint_dir=temp_checkpoint_dir,
            auto_checkpoint=False,
        )

        # Resume from ALPHA (DATA already done)
        result = await loop.run(resumed_state)

        # DATA stage should have been skipped (already in results)
        assert StageType.DATA in result.stage_results
        assert result.stage_results[StageType.DATA].output == {"data": "loaded"}


# =============================================================================
# Edge Cases
# =============================================================================


class TestPipelineEdgeCases:
    """Edge case tests."""

    def test_empty_pipeline_id(self):
        """Test state with empty pipeline ID."""
        state = PipelineState("", StageType.DATA, PipelineStatus.IDLE)
        assert state.pipeline_id == ""

    @pytest.mark.asyncio
    async def test_no_stages(self, mock_approval_gate, temp_checkpoint_dir):
        """Test pipeline with no stages."""
        loop = PipelineLoop(
            stages=[],
            approval_gate=mock_approval_gate,
            checkpoint_dir=temp_checkpoint_dir,
        )

        state = PipelineState("empty", StageType.DATA, PipelineStatus.IDLE)
        result = await loop.run(state)

        assert result.status == PipelineStatus.COMPLETED
        assert len(result.stage_results) == 0

    def test_confidence_thresholds_custom(self):
        """Test custom confidence thresholds."""
        thresholds = ConfidenceThresholds(high=0.95, medium=0.80, low=0.50)
        scorer = ConfidenceScorer(thresholds)

        # Score that would be HIGH with defaults is now MEDIUM
        validations = [ValidationResult(source="test", score=0.88, passed=True)]
        result = scorer.score(validations)
        assert result == Confidence.MEDIUM_CONFIDENCE
