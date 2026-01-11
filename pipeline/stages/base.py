"""
Abstract base class for pipeline stages.

All stage implementations must inherit from AbstractStage.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pipeline.core.types import Confidence, StageResult, StageType

if TYPE_CHECKING:
    from pipeline.core.state import PipelineState


class AbstractStage(ABC):
    """
    Base class for all pipeline stages.

    Subclasses must implement:
        - stage_type: Property returning the StageType
        - execute: Async method that runs stage logic
        - validate_input: Method to validate inputs before execution

    Example:
        ```python
        class DataStage(AbstractStage):
            @property
            def stage_type(self) -> StageType:
                return StageType.DATA

            async def execute(self, state: PipelineState) -> StageResult:
                # Load and validate data
                data = await self._load_data(state.config)
                return StageResult(
                    stage=self.stage_type,
                    status=PipelineStatus.COMPLETED,
                    confidence=Confidence.HIGH_CONFIDENCE,
                    output=data,
                )

            def validate_input(self, state: PipelineState) -> bool:
                return "data_path" in state.config
        ```
    """

    @property
    @abstractmethod
    def stage_type(self) -> StageType:
        """Return the stage type identifier."""
        ...

    @abstractmethod
    async def execute(self, state: "PipelineState") -> StageResult:
        """
        Execute stage logic.

        Args:
            state: Current pipeline state with results from previous stages

        Returns:
            StageResult with output and confidence level
        """
        ...

    @abstractmethod
    def validate_input(self, state: "PipelineState") -> bool:
        """
        Validate inputs before execution.

        Args:
            state: Current pipeline state

        Returns:
            True if inputs are valid, False otherwise
        """
        ...

    def get_confidence_requirement(self) -> Confidence:
        """
        Minimum confidence to auto-proceed without human review.

        Override in subclass to customize per stage.
        Default: MEDIUM_CONFIDENCE

        Returns:
            Minimum Confidence level for auto-proceed
        """
        return Confidence.MEDIUM_CONFIDENCE

    def get_dependencies(self) -> list[StageType]:
        """
        List of stages this stage depends on.

        Override in subclass if stage has dependencies.
        Default: Empty list (no dependencies)

        Returns:
            List of required StageType predecessors
        """
        return []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(stage_type={self.stage_type})"
