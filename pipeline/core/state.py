"""
Pipeline state management with checkpoint/resume capability.
"""

import json
import pickle
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pipeline.core.types import Confidence, PipelineStatus, StageResult, StageType


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


@dataclass
class PipelineState:
    """
    Holds the current state of a pipeline execution.

    Supports checkpoint/resume for long-running pipelines.

    Attributes:
        pipeline_id: Unique identifier for this pipeline run
        current_stage: Current or last executed stage
        status: Overall pipeline status
        stage_results: Results from each completed stage
        config: Pipeline configuration parameters
        checkpoint_path: Path where checkpoint was saved
        created_at: When pipeline was created
        updated_at: Last modification time
    """

    pipeline_id: str
    current_stage: StageType | None = None
    status: PipelineStatus = PipelineStatus.IDLE
    stage_results: dict[StageType, StageResult] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    checkpoint_path: Path | None = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(cls, config: dict[str, Any] | None = None) -> "PipelineState":
        """Create a new pipeline state with unique ID."""
        return cls(
            pipeline_id=str(uuid.uuid4())[:8],
            config=config or {},
        )

    def can_proceed(self) -> bool:
        """Check if pipeline can proceed to next stage."""
        return self.status not in (
            PipelineStatus.FAILED,
            PipelineStatus.PENDING_APPROVAL,
            PipelineStatus.COMPLETED,
        )

    def update_stage(self, stage: StageType, result: StageResult) -> None:
        """Update state with stage result."""
        self.current_stage = stage
        self.stage_results[stage] = result
        self.updated_at = _utc_now()

        if result.status == PipelineStatus.FAILED:
            self.status = PipelineStatus.FAILED
        elif result.requires_approval():
            self.status = PipelineStatus.PENDING_APPROVAL

    def get_next_stage(self) -> StageType | None:
        """Get the next stage to execute based on current state."""
        stage_order = [
            StageType.DATA,
            StageType.ALPHA,
            StageType.RISK,
            StageType.EXECUTION,
            StageType.MONITORING,
        ]

        if self.current_stage is None:
            return stage_order[0]

        try:
            current_idx = stage_order.index(self.current_stage)
            if current_idx < len(stage_order) - 1:
                return stage_order[current_idx + 1]
        except ValueError:
            pass

        return None

    def save_checkpoint(self, checkpoint_dir: Path) -> Path:
        """
        Persist state to disk for resume capability.

        Uses JSON for metadata, pickle for stage outputs.

        Args:
            checkpoint_dir: Directory to save checkpoint

        Returns:
            Path to the saved checkpoint
        """
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_path = checkpoint_dir / f"pipeline_{self.pipeline_id}.json"

        # Serialize state
        state_dict = {
            "pipeline_id": self.pipeline_id,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "status": self.status.name,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "stage_results": {},
        }

        # Serialize stage results (outputs go to pickle)
        outputs_path = checkpoint_dir / f"pipeline_{self.pipeline_id}_outputs.pkl"
        outputs = {}

        for stage_type, result in self.stage_results.items():
            state_dict["stage_results"][stage_type.value] = {
                "stage": result.stage.value,
                "status": result.status.name,
                "confidence": result.confidence.name,
                "metadata": result.metadata,
                "timestamp": result.timestamp.isoformat(),
                "needs_human_review": result.needs_human_review,
                "review_reason": result.review_reason,
            }
            outputs[stage_type.value] = result.output

        # Save JSON metadata
        with open(checkpoint_path, "w") as f:
            json.dump(state_dict, f, indent=2)

        # Save pickle outputs
        with open(outputs_path, "wb") as f:
            pickle.dump(outputs, f)

        self.checkpoint_path = checkpoint_path
        return checkpoint_path

    @classmethod
    def load_checkpoint(cls, checkpoint_path: Path) -> "PipelineState":
        """
        Resume from saved checkpoint.

        Args:
            checkpoint_path: Path to checkpoint JSON file

        Returns:
            Restored PipelineState
        """
        with open(checkpoint_path) as f:
            state_dict = json.load(f)

        # Load pickle outputs
        outputs_path = checkpoint_path.with_name(checkpoint_path.stem + "_outputs.pkl")
        outputs = {}
        if outputs_path.exists():
            with open(outputs_path, "rb") as f:
                outputs = pickle.load(f)

        # Reconstruct state
        state = cls(
            pipeline_id=state_dict["pipeline_id"],
            current_stage=(
                StageType(state_dict["current_stage"]) if state_dict["current_stage"] else None
            ),
            status=PipelineStatus[state_dict["status"]],
            config=state_dict.get("config", {}),
            checkpoint_path=checkpoint_path,
            created_at=datetime.fromisoformat(state_dict["created_at"]),
            updated_at=datetime.fromisoformat(state_dict["updated_at"]),
        )

        # Reconstruct stage results
        for stage_value, result_dict in state_dict.get("stage_results", {}).items():
            stage_type = StageType(stage_value)
            state.stage_results[stage_type] = StageResult(
                stage=StageType(result_dict["stage"]),
                status=PipelineStatus[result_dict["status"]],
                confidence=Confidence[result_dict["confidence"]],
                output=outputs.get(stage_value),
                metadata=result_dict.get("metadata", {}),
                timestamp=datetime.fromisoformat(result_dict["timestamp"]),
                needs_human_review=result_dict.get("needs_human_review", False),
                review_reason=result_dict.get("review_reason"),
            )

        return state

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "pipeline_id": self.pipeline_id,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "status": self.status.name,
            "config": self.config,
            "stages_completed": [s.value for s in self.stage_results.keys()],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
