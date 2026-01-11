"""
Alpha generation stage implementation.

Handles signal generation and model training/evaluation.
Integration point for Alpha-Evolve.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol

from pipeline.core.state import PipelineState
from pipeline.core.types import (
    Confidence,
    PipelineStatus,
    StageResult,
    StageType,
    ValidationResult,
)
from pipeline.hitl.confidence import ConfidenceScorer, create_validation_from_check
from pipeline.stages.base import AbstractStage


class AlphaGenerator(Protocol):
    """Protocol for alpha generation implementations."""

    async def generate(self, data: Any, config: dict[str, Any]) -> dict[str, Any]:
        """Generate alpha signals from data."""
        ...

    async def evaluate(self, alpha: dict[str, Any]) -> dict[str, float]:
        """Evaluate alpha quality metrics."""
        ...


@dataclass
class AlphaConfig:
    """Configuration for alpha stage."""

    model_type: str = "default"
    training_split: float = 0.7
    validation_split: float = 0.15
    test_split: float = 0.15
    min_sharpe: float = 0.5
    max_overfitting: float = 0.3
    evolution_generations: int = 10
    population_size: int = 20
    custom_params: dict[str, Any] = field(default_factory=dict)


class AlphaStage(AbstractStage):
    """
    Alpha generation stage with evolve integration.

    Responsibilities:
        - Generate alpha signals from data
        - Train and evaluate models
        - Detect overfitting
        - Support Alpha-Evolve integration

    Example:
        ```python
        stage = AlphaStage()
        state = PipelineState.create(config={
            "model_type": "momentum",
            "min_sharpe": 1.0,
        })
        # Requires DATA stage result
        state.stage_results[StageType.DATA] = data_result
        result = await stage.execute(state)
        ```
    """

    def __init__(
        self,
        generator: AlphaGenerator | None = None,
        confidence_scorer: ConfidenceScorer | None = None,
    ):
        """
        Initialize alpha stage.

        Args:
            generator: Custom alpha generator, or default if None
            confidence_scorer: Custom scorer, or default if None
        """
        self.generator = generator
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()

    @property
    def stage_type(self) -> StageType:
        """Return stage type."""
        return StageType.ALPHA

    def validate_input(self, state: PipelineState) -> bool:
        """Validate inputs before execution."""
        # Requires DATA stage output
        if StageType.DATA not in state.stage_results:
            return False
        data_result = state.stage_results[StageType.DATA]
        return data_result.is_successful() and data_result.output is not None

    def get_dependencies(self) -> list[StageType]:
        """Alpha depends on DATA stage."""
        return [StageType.DATA]

    def get_confidence_requirement(self) -> Confidence:
        """Alpha stage requires medium confidence to auto-proceed."""
        return Confidence.MEDIUM_CONFIDENCE

    async def execute(self, state: PipelineState) -> StageResult:
        """
        Execute alpha generation.

        Args:
            state: Pipeline state with DATA result

        Returns:
            StageResult with generated alpha
        """
        config = self._parse_config(state.config)
        data_result = state.stage_results[StageType.DATA]

        try:
            # Generate alpha
            alpha = await self._generate_alpha(data_result.output, config)

            # Evaluate
            metrics = await self._evaluate_alpha(alpha, config)

            # Validate
            validations = self._validate_metrics(metrics, config)

            # Score confidence
            confidence = self.confidence_scorer.score(validations)

            # Build metadata
            metadata = self._build_metadata(alpha, metrics, validations)

            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.COMPLETED,
                confidence=confidence,
                output={"alpha": alpha, "metrics": metrics},
                metadata=metadata,
                needs_human_review=confidence in (Confidence.LOW_CONFIDENCE, Confidence.CONFLICT),
                review_reason=self._get_review_reason(metrics, config, confidence),
            )

        except Exception as e:
            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.FAILED,
                confidence=Confidence.UNSOLVABLE,
                output=None,
                metadata={"error": str(e)},
                needs_human_review=True,
                review_reason=f"Alpha generation failed: {e}",
            )

    def _parse_config(self, config: dict[str, Any]) -> AlphaConfig:
        """Parse config dict into AlphaConfig."""
        return AlphaConfig(
            model_type=config.get("model_type", "default"),
            training_split=config.get("training_split", 0.7),
            validation_split=config.get("validation_split", 0.15),
            test_split=config.get("test_split", 0.15),
            min_sharpe=config.get("min_sharpe", 0.5),
            max_overfitting=config.get("max_overfitting", 0.3),
            evolution_generations=config.get("evolution_generations", 10),
            population_size=config.get("population_size", 20),
            custom_params=config.get("alpha_params", {}),
        )

    async def _generate_alpha(
        self,
        data: dict[str, Any],
        config: AlphaConfig,
    ) -> dict[str, Any]:
        """
        Generate alpha signals.

        Override or inject generator for custom logic.
        """
        if self.generator:
            return await self.generator.generate(data, config.custom_params)

        # Default placeholder implementation
        return {
            "model_type": config.model_type,
            "signals": [],
            "parameters": config.custom_params,
            "data_source": data.get("source"),
        }

    async def _evaluate_alpha(
        self,
        alpha: dict[str, Any],
        config: AlphaConfig,
    ) -> dict[str, float]:
        """
        Evaluate alpha quality metrics.

        Override or inject generator for custom logic.
        """
        if self.generator:
            return await self.generator.evaluate(alpha)

        # Default placeholder metrics
        return {
            "sharpe_ratio": 0.8,  # Placeholder
            "sortino_ratio": 1.2,
            "max_drawdown": 0.15,
            "win_rate": 0.55,
            "profit_factor": 1.3,
            "overfitting_score": 0.2,
            "training_score": 0.85,
            "validation_score": 0.75,
        }

    def _validate_metrics(
        self,
        metrics: dict[str, float],
        config: AlphaConfig,
    ) -> list[ValidationResult]:
        """Validate alpha metrics."""
        validations = []

        # Sharpe ratio check
        sharpe = metrics.get("sharpe_ratio", 0)
        sharpe_ok = sharpe >= config.min_sharpe
        validations.append(
            create_validation_from_check(
                source="sharpe_ratio",
                passed=sharpe_ok,
                score=min(1.0, sharpe / config.min_sharpe) if config.min_sharpe > 0 else 1.0,
                message=f"Sharpe ratio: {sharpe:.2f} (min: {config.min_sharpe})",
            )
        )

        # Overfitting check
        overfitting = metrics.get("overfitting_score", 1.0)
        overfit_ok = overfitting <= config.max_overfitting
        validations.append(
            create_validation_from_check(
                source="overfitting",
                passed=overfit_ok,
                score=1.0 - overfitting,
                message=f"Overfitting score: {overfitting:.2f} (max: {config.max_overfitting})",
            )
        )

        # Train/validation gap
        train_score = metrics.get("training_score", 0)
        val_score = metrics.get("validation_score", 0)
        gap = abs(train_score - val_score)
        gap_ok = gap <= 0.2  # Max 20% gap
        validations.append(
            create_validation_from_check(
                source="train_val_gap",
                passed=gap_ok,
                score=1.0 - min(1.0, gap / 0.2),
                message=f"Train/val gap: {gap:.2f}",
            )
        )

        return validations

    def _build_metadata(
        self,
        alpha: dict[str, Any],
        metrics: dict[str, float],
        validations: list[ValidationResult],
    ) -> dict[str, Any]:
        """Build metadata dict."""
        return {
            "model_type": alpha.get("model_type"),
            "sharpe_ratio": metrics.get("sharpe_ratio"),
            "overfitting_score": metrics.get("overfitting_score"),
            "max_drawdown": metrics.get("max_drawdown"),
            "validations_passed": sum(1 for v in validations if v.passed),
            "validations_total": len(validations),
        }

    def _get_review_reason(
        self,
        metrics: dict[str, float],
        config: AlphaConfig,
        confidence: Confidence,
    ) -> str | None:
        """Get review reason if needed."""
        if confidence == Confidence.HIGH_CONFIDENCE:
            return None

        reasons = []

        sharpe = metrics.get("sharpe_ratio", 0)
        if sharpe < config.min_sharpe:
            reasons.append(f"Low Sharpe ({sharpe:.2f})")

        overfitting = metrics.get("overfitting_score", 1.0)
        if overfitting > config.max_overfitting:
            reasons.append(f"High overfitting ({overfitting:.2f})")

        if reasons:
            return "; ".join(reasons)

        return "Alpha metrics below threshold"
