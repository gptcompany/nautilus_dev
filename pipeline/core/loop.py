"""
Main pipeline loop with HITL gates.

Executes stages sequentially with checkpointing and human approval gates.
"""

import logging
from collections.abc import Callable
from pathlib import Path

from pipeline.core.state import PipelineState
from pipeline.core.types import (
    Confidence,
    PipelineStatus,
    ProgressEvent,
    StageResult,
    StageType,
)
from pipeline.hitl.approval import ApprovalGate, ApprovalResponse
from pipeline.stages.base import AbstractStage

logger = logging.getLogger(__name__)


ProgressCallback = Callable[[ProgressEvent], None]


class PipelineLoop:
    """
    Main pipeline execution loop with HITL integration.

    Features:
        - Sequential stage execution with dependencies
        - Human approval gates for low-confidence results
        - Auto-checkpoint after each stage
        - Progress callbacks for monitoring
        - Resume from checkpoint

    Example:
        ```python
        stages = [DataStage(), AlphaStage(), RiskStage()]
        approval_gate = ApprovalGate(approval_dir=Path("./approvals"))

        loop = PipelineLoop(
            stages=stages,
            approval_gate=approval_gate,
            checkpoint_dir=Path("./checkpoints"),
        )

        state = PipelineState.create(config={"data_path": "./data"})
        result = await loop.run(state)
        ```
    """

    # Default stage execution order
    STAGE_ORDER = [
        StageType.DATA,
        StageType.ALPHA,
        StageType.RISK,
        StageType.EXECUTION,
        StageType.MONITORING,
    ]

    def __init__(
        self,
        stages: list[AbstractStage],
        approval_gate: ApprovalGate,
        checkpoint_dir: Path,
        auto_checkpoint: bool = True,
    ):
        """
        Initialize pipeline loop.

        Args:
            stages: List of stage implementations
            approval_gate: HITL approval gate
            checkpoint_dir: Directory for checkpoints
            auto_checkpoint: Save checkpoint after each stage
        """
        self.stages = {s.stage_type: s for s in stages}
        self.approval_gate = approval_gate
        self.checkpoint_dir = checkpoint_dir
        self.auto_checkpoint = auto_checkpoint
        self._callbacks: list[ProgressCallback] = []

        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def add_callback(self, callback: ProgressCallback) -> None:
        """Add progress callback."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: ProgressCallback) -> None:
        """Remove progress callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _emit_progress(
        self,
        state: PipelineState,
        progress_pct: float = 0.0,
        message: str = "",
    ) -> None:
        """Emit progress event to all callbacks."""
        event = ProgressEvent(
            pipeline_id=state.pipeline_id,
            stage=state.current_stage or StageType.DATA,
            status=state.status,
            progress_pct=progress_pct,
            message=message,
        )

        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    async def run(self, state: PipelineState) -> PipelineState:
        """
        Execute pipeline with HITL gates.

        Args:
            state: Initial or resumed pipeline state

        Returns:
            Final pipeline state
        """
        state.status = PipelineStatus.RUNNING
        self._emit_progress(state, message="Pipeline started")

        # Determine which stages to run
        stages_to_run = self._get_stages_to_run(state)
        total_stages = len(stages_to_run)

        for i, stage_type in enumerate(stages_to_run):
            if not state.can_proceed():
                logger.warning(f"Pipeline cannot proceed: {state.status}")
                break

            stage = self.stages.get(stage_type)
            if not stage:
                logger.debug(f"Skipping unregistered stage: {stage_type}")
                continue

            # Update state
            state.current_stage = stage_type
            progress_pct = (i / total_stages) * 100
            self._emit_progress(state, progress_pct, f"Running {stage_type.value}")

            # Validate inputs
            if not stage.validate_input(state):
                logger.error(f"Stage {stage_type} input validation failed")
                state.status = PipelineStatus.FAILED
                break

            # Execute stage
            try:
                result = await stage.execute(state)
            except Exception as e:
                logger.exception(f"Stage {stage_type} execution failed")
                result = StageResult(
                    stage=stage_type,
                    status=PipelineStatus.FAILED,
                    confidence=Confidence.UNSOLVABLE,
                    output=None,
                    review_reason=f"Exception: {e}",
                    needs_human_review=True,
                )

            state.update_stage(stage_type, result)

            # HITL gate check
            if result.requires_approval():
                state.status = PipelineStatus.PENDING_APPROVAL
                self._emit_progress(state, progress_pct, "Awaiting human approval")

                approval = await self._handle_approval(state, result)

                if not approval.approved:
                    logger.info(f"Approval rejected: {approval.feedback}")
                    state.status = PipelineStatus.FAILED
                    break

                # Apply modifications if any
                if approval.modifications:
                    state.config.update(approval.modifications)

                state.status = PipelineStatus.RUNNING

            # Auto-checkpoint
            if self.auto_checkpoint:
                checkpoint_path = state.save_checkpoint(self.checkpoint_dir)
                logger.debug(f"Checkpoint saved: {checkpoint_path}")

        # Finalize
        if state.status == PipelineStatus.RUNNING:
            state.status = PipelineStatus.COMPLETED
            self._emit_progress(state, 100.0, "Pipeline completed")
        else:
            self._emit_progress(state, message=f"Pipeline ended: {state.status.name}")

        return state

    def _get_stages_to_run(self, state: PipelineState) -> list[StageType]:
        """Get stages to run based on current state."""
        if state.current_stage is None:
            return self.STAGE_ORDER

        # Resume from after current stage
        try:
            current_idx = self.STAGE_ORDER.index(state.current_stage)
            # If current stage completed, start from next
            if state.current_stage in state.stage_results:
                result = state.stage_results[state.current_stage]
                if result.is_successful():
                    return self.STAGE_ORDER[current_idx + 1 :]
            return self.STAGE_ORDER[current_idx:]
        except ValueError:
            return self.STAGE_ORDER

    async def _handle_approval(
        self,
        state: PipelineState,
        result: StageResult,
    ) -> ApprovalResponse:
        """Handle HITL approval request."""
        logger.info(
            f"Requesting approval for {result.stage.value} (confidence: {result.confidence.name})"
        )

        return await self.approval_gate.request_approval(
            pipeline_id=state.pipeline_id,
            result=result,
        )

    async def run_single_stage(
        self,
        state: PipelineState,
        stage_type: StageType,
    ) -> StageResult:
        """
        Run a single stage for testing/debugging.

        Args:
            state: Pipeline state
            stage_type: Stage to run

        Returns:
            Stage result
        """
        stage = self.stages.get(stage_type)
        if not stage:
            raise ValueError(f"Stage not registered: {stage_type}")

        if not stage.validate_input(state):
            raise ValueError(f"Stage {stage_type} input validation failed")

        return await stage.execute(state)

    @classmethod
    def resume(
        cls,
        checkpoint_path: Path,
        stages: list[AbstractStage],
        approval_gate: ApprovalGate,
    ) -> tuple["PipelineLoop", PipelineState]:
        """
        Create loop and restore state from checkpoint.

        Args:
            checkpoint_path: Path to checkpoint file
            stages: Stage implementations
            approval_gate: HITL approval gate

        Returns:
            Tuple of (PipelineLoop, restored PipelineState)
        """
        state = PipelineState.load_checkpoint(checkpoint_path)
        checkpoint_dir = checkpoint_path.parent

        loop = cls(
            stages=stages,
            approval_gate=approval_gate,
            checkpoint_dir=checkpoint_dir,
        )

        return loop, state
