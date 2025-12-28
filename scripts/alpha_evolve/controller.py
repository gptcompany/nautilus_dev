"""
Alpha-Evolve Controller - Orchestrates the evolutionary loop.

Coordinates parent selection, LLM-guided mutations, backtest evaluation,
and population management for strategy optimization.

Part of spec-009: Alpha-Evolve Controller & CLI
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from monitoring.client import MetricsClient
    from scripts.alpha_evolve.config import EvolutionConfig
    from scripts.alpha_evolve.evaluator import StrategyEvaluator
    from scripts.alpha_evolve.mutator import Mutator, MutationResponse
    from scripts.alpha_evolve.store import Program, ProgramStore

logger = logging.getLogger("alpha_evolve.controller")


class EvolutionStatus(Enum):
    """Controller state machine states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressEventType(Enum):
    """Types of progress events emitted during evolution."""

    ITERATION_START = "iteration_start"
    PARENT_SELECTED = "parent_selected"
    MUTATION_REQUESTED = "mutation_requested"
    MUTATION_COMPLETE = "mutation_complete"
    EVALUATION_START = "evaluation_start"
    EVALUATION_COMPLETE = "evaluation_complete"
    ITERATION_COMPLETE = "iteration_complete"
    EVOLUTION_COMPLETE = "evolution_complete"
    ERROR = "error"


@dataclass
class StopCondition:
    """Conditions for early evolution termination."""

    max_iterations: int = 50
    target_fitness: float | None = None
    max_time_seconds: int | None = None
    no_improvement_generations: int | None = None

    def __post_init__(self) -> None:
        """Validate stop condition parameters."""
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        if self.target_fitness is not None and self.target_fitness < 0:
            raise ValueError("target_fitness must be >= 0 if set")
        if self.max_time_seconds is not None and self.max_time_seconds < 1:
            raise ValueError("max_time_seconds must be >= 1 if set")
        if (
            self.no_improvement_generations is not None
            and self.no_improvement_generations < 1
        ):
            raise ValueError("no_improvement_generations must be >= 1 if set")


@dataclass
class ProgressEvent:
    """Progress event for callbacks/monitoring."""

    event_type: ProgressEventType
    iteration: int
    timestamp: datetime
    data: dict = field(default_factory=dict)


@dataclass
class EvolutionProgress:
    """Current evolution state for monitoring."""

    experiment: str
    iteration: int
    generation: int
    best_fitness: float
    best_strategy_id: str | None
    population_size: int
    elapsed_seconds: float
    status: EvolutionStatus

    mutations_attempted: int = 0
    mutations_successful: int = 0
    evaluations_completed: int = 0
    evaluations_failed: int = 0


@dataclass
class EvolutionResult:
    """Final result from evolution run."""

    experiment: str
    status: EvolutionStatus
    iterations_completed: int
    best_strategy: Program | None
    final_population_size: int
    elapsed_seconds: float

    total_mutations: int
    successful_mutations: int
    total_evaluations: int
    successful_evaluations: int

    stop_reason: str | None = None


class EvolutionController:
    """
    Main orchestrator for the evolution loop.

    Coordinates parent selection, LLM-guided mutations, backtest evaluation,
    and population management for strategy optimization.
    """

    def __init__(
        self,
        config: EvolutionConfig,
        store: ProgramStore,
        evaluator: StrategyEvaluator,
        mutator: Mutator | None = None,
        metrics_client: MetricsClient | None = None,
    ) -> None:
        """
        Initialize evolution controller.

        Args:
            config: Evolution configuration (population, selection ratios)
            store: Strategy persistence store (spec-006)
            evaluator: Backtest evaluator (spec-007)
            mutator: Code mutation provider (defaults to LLMMutator)
            metrics_client: Optional QuestDB client for dashboard metrics (spec-010)

        Raises:
            ValueError: If config is invalid
        """
        self.config = config
        self.store = store
        self.evaluator = evaluator
        self.mutator = mutator

        # Metrics publisher for Grafana dashboard (spec-010)
        self._metrics_publisher: EvolutionMetricsPublisher | None = None
        if metrics_client is not None:
            from scripts.alpha_evolve.metrics_publisher import EvolutionMetricsPublisher

            self._metrics_publisher = EvolutionMetricsPublisher(metrics_client)

        # Runtime state
        self._experiment: str | None = None
        self._current_iteration: int = 0
        self._best_fitness: float = float("-inf")
        self._best_strategy_id: str | None = None
        self._status: EvolutionStatus = EvolutionStatus.IDLE
        self._stop_requested: bool = False
        self._start_time: float = 0.0

        # Statistics
        self._mutations_attempted: int = 0
        self._mutations_successful: int = 0
        self._evaluations_completed: int = 0
        self._evaluations_failed: int = 0
        self._generations_without_improvement: int = 0
        self._last_best_fitness: float = float("-inf")

        # Progress callback
        self._on_progress: Callable[[ProgressEvent], None] | None = None

    async def run(
        self,
        seed_strategy: str,
        experiment: str,
        iterations: int,
        stop_condition: StopCondition | None = None,
        on_progress: Callable[[ProgressEvent], None] | None = None,
        *,
        _skip_seed: bool = False,
    ) -> EvolutionResult:
        """
        Execute evolution loop.

        Args:
            seed_strategy: Name of seed strategy ("momentum")
            experiment: Unique experiment name
            iterations: Number of iterations to run
            stop_condition: Optional early termination conditions
            on_progress: Callback for progress events
            _skip_seed: Internal flag to skip seed loading (for resume)

        Returns:
            EvolutionResult with final statistics

        Raises:
            ValueError: If seed strategy not found
            RuntimeError: If evolution fails unrecoverably
        """
        # Initialize state (skip resets for resume to preserve checkpoint state)
        self._experiment = experiment
        self._status = EvolutionStatus.RUNNING
        self._stop_requested = False
        self._on_progress = on_progress

        if not _skip_seed:
            # Fresh run: reset all state
            self._current_iteration = 0
            self._best_fitness = float("-inf")
            self._best_strategy_id = None
            self._start_time = time.time()

            # Reset statistics
            self._mutations_attempted = 0
            self._mutations_successful = 0
            self._evaluations_completed = 0
            self._evaluations_failed = 0
            self._generations_without_improvement = 0
        # else: resume() has already restored checkpoint state

        # Create stop condition if not provided
        if stop_condition is None:
            stop_condition = StopCondition(max_iterations=iterations)
        else:
            # Use provided iterations as max if not set
            if stop_condition.max_iterations < iterations:
                stop_condition.max_iterations = iterations

        # Load seed strategy (skip for resume)
        if not _skip_seed:
            await self._load_seed_strategy(seed_strategy, experiment)

        logger.info(f"Starting evolution: {experiment}, iterations={iterations}")

        stop_reason = None

        # Main evolution loop
        for iteration in range(iterations):
            if self._stop_requested:
                self._status = EvolutionStatus.PAUSED
                stop_reason = "User requested stop"
                break

            self._current_iteration = iteration

            # Emit iteration start event
            self._emit_progress(
                ProgressEventType.ITERATION_START,
                {"iteration": iteration, "max_iterations": iterations},
            )

            # Run single iteration
            try:
                await self._run_iteration(experiment)
            except Exception as e:
                logger.error(f"Iteration {iteration} failed: {e}")
                self._emit_progress(
                    ProgressEventType.ERROR,
                    {"error": str(e), "iteration": iteration},
                )
                # Continue on individual failures (FR-003)
                continue

            # Emit iteration complete event
            self._emit_progress(
                ProgressEventType.ITERATION_COMPLETE,
                {
                    "iteration": iteration,
                    "best_fitness": self._best_fitness,
                    "population_size": self.store.count(experiment),
                },
            )

            # Check stop conditions
            should_stop, reason = self._check_stop_conditions(stop_condition)
            if should_stop:
                stop_reason = reason
                break

        # Finalize
        if not stop_reason:
            self._status = EvolutionStatus.COMPLETED
            stop_reason = "Completed all iterations"

        # Get best strategy
        best_strategy = None
        if self._best_strategy_id:
            best_strategy = self.store.get(self._best_strategy_id)

        elapsed = time.time() - self._start_time

        # Emit completion event
        self._emit_progress(
            ProgressEventType.EVOLUTION_COMPLETE,
            {
                "status": self._status.value,
                "stop_reason": stop_reason,
                "elapsed_seconds": elapsed,
            },
        )

        logger.info(f"Evolution complete: {stop_reason}")

        return EvolutionResult(
            experiment=experiment,
            status=self._status,
            iterations_completed=self._current_iteration + 1,
            best_strategy=best_strategy,
            final_population_size=self.store.count(experiment),
            elapsed_seconds=elapsed,
            total_mutations=self._mutations_attempted,
            successful_mutations=self._mutations_successful,
            total_evaluations=self._evaluations_completed + self._evaluations_failed,
            successful_evaluations=self._evaluations_completed,
            stop_reason=stop_reason,
        )

    def stop(self, force: bool = False) -> None:
        """
        Request graceful stop.

        Args:
            force: If True, interrupt immediately
                   If False, complete current iteration
        """
        self._stop_requested = True
        logger.info(f"Stop requested (force={force})")
        if force:
            self._status = EvolutionStatus.PAUSED

    async def resume(
        self,
        experiment: str,
        additional_iterations: int = 0,
        on_progress: Callable[[ProgressEvent], None] | None = None,
    ) -> EvolutionResult:
        """
        Resume paused evolution.

        Args:
            experiment: Experiment name to resume
            additional_iterations: Extra iterations beyond original target
            on_progress: Callback for progress events

        Returns:
            EvolutionResult with final statistics

        Raises:
            ValueError: If experiment not found or not resumable
        """
        # Load checkpoint
        checkpoint = self._load_checkpoint(experiment)
        if checkpoint is None:
            raise ValueError(f"Experiment not found: {experiment}")

        # Calculate remaining iterations
        remaining = checkpoint.get("remaining_iterations", 0)
        iterations = remaining + additional_iterations

        if iterations <= 0:
            raise ValueError("No iterations remaining to resume")

        logger.info(f"Resuming {experiment}: {iterations} iterations remaining")

        # Resume from checkpoint state
        self._experiment = experiment
        self._current_iteration = checkpoint.get("iteration", 0)
        self._best_fitness = checkpoint.get("best_fitness", float("-inf"))
        self._best_strategy_id = checkpoint.get("best_strategy_id")
        self._start_time = time.time() - checkpoint.get("elapsed_seconds", 0)

        # Continue evolution (skip seed loading since we're resuming)
        return await self.run(
            seed_strategy="",
            experiment=experiment,
            iterations=iterations,
            on_progress=on_progress,
            _skip_seed=True,
        )

    def get_progress(self, experiment: str | None = None) -> EvolutionProgress:
        """
        Get current evolution progress.

        Args:
            experiment: Experiment name (None for active experiment)

        Returns:
            EvolutionProgress snapshot

        Raises:
            ValueError: If experiment not found
        """
        exp_name = experiment or self._experiment
        if not exp_name:
            raise ValueError("No active experiment")

        # Get max generation from store
        top_strategies = self.store.top_k(k=1, metric="calmar", experiment=exp_name)
        generation = top_strategies[0].generation if top_strategies else 0

        return EvolutionProgress(
            experiment=exp_name,
            iteration=self._current_iteration,
            generation=generation,
            best_fitness=self._best_fitness,
            best_strategy_id=self._best_strategy_id,
            population_size=self.store.count(exp_name),
            elapsed_seconds=time.time() - self._start_time if self._start_time else 0,
            status=self._status,
            mutations_attempted=self._mutations_attempted,
            mutations_successful=self._mutations_successful,
            evaluations_completed=self._evaluations_completed,
            evaluations_failed=self._evaluations_failed,
        )

    async def _load_seed_strategy(self, seed_name: str, experiment: str) -> str:
        """
        Load and store seed strategy.

        Args:
            seed_name: Name of seed strategy ("momentum")
            experiment: Experiment name

        Returns:
            ID of stored seed strategy

        Raises:
            ValueError: If seed not found
        """
        from scripts.alpha_evolve.templates import MomentumEvolveStrategy
        import inspect

        # Map seed names to strategy classes
        seeds = {
            "momentum": MomentumEvolveStrategy,
        }

        if seed_name not in seeds:
            raise ValueError(
                f"Unknown seed strategy: {seed_name}. Available: {list(seeds.keys())}"
            )

        # Get source code
        strategy_class = seeds[seed_name]
        code = inspect.getsource(inspect.getmodule(strategy_class))

        # Store as generation 0
        seed_id = self.store.insert(
            code=code,
            metrics=None,  # Will be evaluated in first iteration
            parent_id=None,
            experiment=experiment,
        )

        logger.info(f"Loaded seed strategy: {seed_name} (id={seed_id[:8]}...)")
        return seed_id

    def _select_parent_mode(self) -> str:
        """
        Select parent selection mode based on configured ratios.

        Returns:
            Selection mode: "elite", "exploit", or "explore"
        """
        r = random.random()

        elite_threshold = self.config.elite_ratio
        exploit_threshold = 1.0 - self.config.exploration_ratio

        if r < elite_threshold:
            return "elite"
        elif r < exploit_threshold:
            return "exploit"
        else:
            return "explore"

    def _select_parent(self, experiment: str) -> Program:
        """
        Select parent strategy for mutation.

        Args:
            experiment: Experiment name for filtering

        Returns:
            Selected parent Program

        Raises:
            RuntimeError: If store is empty
        """

        mode = self._select_parent_mode()
        parent = self.store.sample(strategy=mode, experiment=experiment)

        if parent is None:
            raise RuntimeError("Cannot select parent: store is empty")

        logger.debug(f"Selected parent via {mode}: {parent.id[:8]}...")
        return parent

    async def _request_mutation(
        self,
        parent: Program,
        retry_count: int = 0,
    ) -> MutationResponse:
        """
        Request code mutation from LLM.

        Args:
            parent: Parent strategy to mutate
            retry_count: Current retry attempt (max 3)

        Returns:
            MutationResponse with mutated code or error
        """
        from scripts.alpha_evolve.mutator import LLMMutator, MutationRequest

        # Use default mutator if not provided
        if self.mutator is None:
            self.mutator = LLMMutator()

        request = MutationRequest(
            parent_code=parent.code,
            parent_metrics=parent.metrics,
            block_name="decision_logic",
            guidance="",
            previous_error=None,
            retry_count=retry_count,
        )

        return await self.mutator.mutate(request)

    async def _run_iteration(self, experiment: str) -> None:
        """
        Execute single evolution iteration.

        Args:
            experiment: Experiment name
        """
        # 1. Select parent
        parent = self._select_parent(experiment)

        self._emit_progress(
            ProgressEventType.PARENT_SELECTED,
            {
                "parent_id": parent.id,
                "parent_fitness": parent.metrics.calmar_ratio if parent.metrics else 0,
            },
        )

        # 2. Request mutation
        self._emit_progress(ProgressEventType.MUTATION_REQUESTED, {})
        self._mutations_attempted += 1

        response = await self._request_mutation(parent)

        if not response.success:
            logger.warning(f"Mutation failed: {response.error}")
            self._emit_progress(
                ProgressEventType.MUTATION_COMPLETE,
                {"success": False, "error": response.error},
            )
            # Publish mutation failure to dashboard (spec-010)
            if self._metrics_publisher:
                outcome = (
                    "syntax_error"
                    if "syntax" in str(response.error).lower()
                    else "runtime_error"
                )
                await self._metrics_publisher.publish_mutation_failure(
                    experiment=experiment,
                    outcome=outcome,
                    latency_ms=response.latency_ms
                    if hasattr(response, "latency_ms")
                    else 0.0,
                )
            return

        self._mutations_successful += 1
        self._emit_progress(
            ProgressEventType.MUTATION_COMPLETE,
            {"success": True},
        )

        # 3. Evaluate mutated strategy
        self._emit_progress(ProgressEventType.EVALUATION_START, {})

        from scripts.alpha_evolve.evaluator import EvaluationRequest

        eval_request = EvaluationRequest(
            strategy_code=response.mutated_code,
            strategy_class_name="MomentumEvolveStrategy",
            config_class_name="MomentumEvolveConfig",
        )

        eval_result = await self.evaluator.evaluate(eval_request)

        if not eval_result.success:
            logger.warning(f"Evaluation failed: {eval_result.error}")
            self._evaluations_failed += 1
            self._emit_progress(
                ProgressEventType.EVALUATION_COMPLETE,
                {"success": False, "error": eval_result.error},
            )
            return

        self._evaluations_completed += 1
        metrics = eval_result.metrics

        self._emit_progress(
            ProgressEventType.EVALUATION_COMPLETE,
            {
                "success": True,
                "calmar": metrics.calmar_ratio if metrics else 0,
                "sharpe": metrics.sharpe_ratio if metrics else 0,
            },
        )

        # 4. Store result
        child_id = self.store.insert(
            code=response.mutated_code,
            metrics=metrics,
            parent_id=parent.id,
            experiment=experiment,
        )

        # 4.5. Publish to dashboard (spec-010)
        if self._metrics_publisher:
            child = self.store.get(child_id)
            if child:
                await self._metrics_publisher.publish_evaluation(
                    program=child,
                    mutation_outcome="success",
                    mutation_latency_ms=response.latency_ms
                    if hasattr(response, "latency_ms")
                    else 0.0,
                )

        # 5. Update best if improved
        if metrics and metrics.calmar_ratio > self._best_fitness:
            old_best = self._best_fitness
            self._best_fitness = metrics.calmar_ratio
            self._best_strategy_id = child_id
            self._generations_without_improvement = 0
            logger.info(
                f"New best: calmar={metrics.calmar_ratio:.4f} (was {old_best:.4f})"
            )
        else:
            self._generations_without_improvement += 1

        # 6. Prune if needed
        pruned = self.store.prune()
        if pruned > 0:
            logger.debug(f"Pruned {pruned} strategies")

    def _check_stop_conditions(
        self, condition: StopCondition
    ) -> tuple[bool, str | None]:
        """
        Check if any stop condition is met.

        Args:
            condition: Stop condition configuration

        Returns:
            Tuple of (should_stop, reason)
        """
        # 1. Max iterations (checked by loop)

        # 2. Target fitness
        if (
            condition.target_fitness is not None
            and self._best_fitness >= condition.target_fitness
        ):
            return True, f"Target fitness reached: {self._best_fitness:.4f}"

        # 3. Max time
        if condition.max_time_seconds is not None:
            elapsed = time.time() - self._start_time
            if elapsed >= condition.max_time_seconds:
                return True, f"Time limit reached: {elapsed:.0f}s"

        # 4. Stagnation
        if condition.no_improvement_generations is not None:
            if (
                self._generations_without_improvement
                >= condition.no_improvement_generations
            ):
                return (
                    True,
                    f"No improvement for {self._generations_without_improvement} generations",
                )

        return False, None

    def _emit_progress(self, event_type: ProgressEventType, data: dict) -> None:
        """
        Emit progress event to callback.

        Args:
            event_type: Type of progress event
            data: Event-specific payload
        """
        if self._on_progress is None:
            return

        event = ProgressEvent(
            event_type=event_type,
            iteration=self._current_iteration,
            timestamp=datetime.now(),
            data=data,
        )

        try:
            self._on_progress(event)
        except Exception as e:
            logger.warning(f"Progress callback error: {e}")

    def _load_checkpoint(self, experiment: str) -> dict | None:
        """
        Load checkpoint data for resuming.

        Args:
            experiment: Experiment name

        Returns:
            Checkpoint dict or None if not found
        """
        # Get experiment stats from store
        count = self.store.count(experiment)
        if count == 0:
            return None

        # Get best strategy
        top = self.store.top_k(k=1, metric="calmar", experiment=experiment)
        if not top:
            return None

        best = top[0]

        return {
            "experiment": experiment,
            "iteration": best.generation,
            "best_fitness": best.metrics.calmar_ratio if best.metrics else 0,
            "best_strategy_id": best.id,
            "elapsed_seconds": 0,  # Cannot recover elapsed time
            "remaining_iterations": 0,  # Needs to be set by caller
        }
