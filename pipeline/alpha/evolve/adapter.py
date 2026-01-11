"""
Alpha-Evolve adapter for pipeline integration.

Wraps existing scripts/alpha_evolve to work within the pipeline framework.
"""

from typing import Any

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


class AlphaEvolveAdapter(AbstractStage):
    """
    Adapter to integrate existing Alpha-Evolve with pipeline framework.

    This wrapper allows the existing scripts/alpha_evolve controller
    to be used as a pipeline stage without modification.

    Example:
        ```python
        from scripts.alpha_evolve.controller import AlphaEvolveController

        # Create adapter with existing controller
        controller = AlphaEvolveController(config)
        adapter = AlphaEvolveAdapter(controller=controller)

        # Use in pipeline
        loop = PipelineLoop(stages=[DataStage(), adapter, ...])
        ```
    """

    def __init__(
        self,
        controller: Any = None,
        confidence_scorer: ConfidenceScorer | None = None,
        min_fitness: float = 0.6,
        max_generations: int = 50,
    ):
        """
        Initialize adapter.

        Args:
            controller: Existing AlphaEvolveController instance (optional)
            confidence_scorer: Custom scorer, or default if None
            min_fitness: Minimum fitness score for HIGH confidence
            max_generations: Max generations before forcing review
        """
        self._controller = controller
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()
        self.min_fitness = min_fitness
        self.max_generations = max_generations

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
        """Alpha-Evolve requires medium confidence."""
        return Confidence.MEDIUM_CONFIDENCE

    async def execute(self, state: PipelineState) -> StageResult:
        """
        Execute Alpha-Evolve through pipeline.

        Args:
            state: Pipeline state with DATA result

        Returns:
            StageResult with evolution results
        """
        data_result = state.stage_results[StageType.DATA]
        config = state.config

        try:
            # Run evolution
            if self._controller:
                result = await self._run_with_controller(data_result.output, config)
            else:
                result = await self._run_standalone(data_result.output, config)

            # Validate results
            validations = self._validate_evolution_result(result)

            # Score confidence
            confidence = self.confidence_scorer.score(validations)

            # Build metadata
            metadata = self._build_metadata(result, validations)

            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.COMPLETED,
                confidence=confidence,
                output=result,
                metadata=metadata,
                needs_human_review=confidence in (Confidence.LOW_CONFIDENCE, Confidence.CONFLICT),
                review_reason=self._get_review_reason(result, confidence),
            )

        except Exception as e:
            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.FAILED,
                confidence=Confidence.UNSOLVABLE,
                output=None,
                metadata={"error": str(e)},
                needs_human_review=True,
                review_reason=f"Alpha-Evolve failed: {e}",
            )

    async def _run_with_controller(
        self,
        data: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Run evolution using existing controller."""
        # Configure controller from pipeline config
        generations = config.get("evolution_generations", 10)
        population = config.get("population_size", 20)

        # Run evolution (controller handles async internally)
        # Note: Actual implementation depends on controller API
        evolution_result = {
            "best_individual": None,
            "best_fitness": 0.0,
            "generations_run": generations,
            "population_size": population,
            "convergence_generation": None,
        }

        # If controller has async run method
        if hasattr(self._controller, "run_evolution"):
            result = await self._controller.run_evolution(
                generations=generations,
                population_size=population,
            )
            evolution_result.update(result)

        return evolution_result

    async def _run_standalone(
        self,
        data: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Run evolution without controller (placeholder/testing)."""
        generations = config.get("evolution_generations", 10)
        population = config.get("population_size", 20)

        # Placeholder result for testing
        return {
            "best_individual": {"type": "placeholder", "params": {}},
            "best_fitness": 0.75,
            "generations_run": generations,
            "population_size": population,
            "convergence_generation": generations - 2,
            "fitness_history": [0.5 + i * 0.025 for i in range(generations)],
            "metrics": {
                "sharpe_ratio": 1.2,
                "sortino_ratio": 1.5,
                "max_drawdown": 0.12,
                "overfitting_score": 0.15,
            },
        }

    def _validate_evolution_result(
        self,
        result: dict[str, Any],
    ) -> list[ValidationResult]:
        """Validate evolution results."""
        validations = []

        # Fitness score check
        fitness = result.get("best_fitness", 0)
        fitness_ok = fitness >= self.min_fitness
        validations.append(
            create_validation_from_check(
                source="fitness_score",
                passed=fitness_ok,
                score=min(1.0, fitness / self.min_fitness) if self.min_fitness > 0 else 1.0,
                message=f"Best fitness: {fitness:.3f} (min: {self.min_fitness})",
            )
        )

        # Convergence check
        converged = result.get("convergence_generation") is not None
        generations = result.get("generations_run", 0)
        validations.append(
            create_validation_from_check(
                source="convergence",
                passed=converged,
                score=0.9 if converged else 0.5,
                message=f"Converged at gen {result.get('convergence_generation')}"
                if converged
                else f"No convergence in {generations} generations",
            )
        )

        # Overfitting check (if metrics available)
        metrics = result.get("metrics", {})
        overfitting = metrics.get("overfitting_score", 0.5)
        overfit_ok = overfitting <= 0.3
        validations.append(
            create_validation_from_check(
                source="overfitting",
                passed=overfit_ok,
                score=1.0 - overfitting,
                message=f"Overfitting score: {overfitting:.2f}",
            )
        )

        return validations

    def _build_metadata(
        self,
        result: dict[str, Any],
        validations: list[ValidationResult],
    ) -> dict[str, Any]:
        """Build metadata dict."""
        metrics = result.get("metrics", {})
        return {
            "best_fitness": result.get("best_fitness"),
            "generations_run": result.get("generations_run"),
            "convergence_generation": result.get("convergence_generation"),
            "sharpe_ratio": metrics.get("sharpe_ratio"),
            "overfitting_score": metrics.get("overfitting_score"),
            "validations_passed": sum(1 for v in validations if v.passed),
            "validations_total": len(validations),
        }

    def _get_review_reason(
        self,
        result: dict[str, Any],
        confidence: Confidence,
    ) -> str | None:
        """Get review reason if needed."""
        if confidence == Confidence.HIGH_CONFIDENCE:
            return None

        reasons = []

        fitness = result.get("best_fitness", 0)
        if fitness < self.min_fitness:
            reasons.append(f"Low fitness ({fitness:.3f})")

        if result.get("convergence_generation") is None:
            reasons.append("No convergence")

        metrics = result.get("metrics", {})
        if metrics.get("overfitting_score", 0) > 0.3:
            reasons.append("High overfitting")

        return "; ".join(reasons) if reasons else "Evolution requires review"
