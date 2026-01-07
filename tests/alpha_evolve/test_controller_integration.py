"""Integration tests for Alpha-Evolve Controller.

These tests verify the complete evolution workflow end-to-end.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from scripts.alpha_evolve.config import EvolutionConfig
from scripts.alpha_evolve.controller import (
    EvolutionController,
    EvolutionStatus,
    ProgressEvent,
    ProgressEventType,
    StopCondition,
)
from scripts.alpha_evolve.mutator import MockMutator
from scripts.alpha_evolve.store import FitnessMetrics, ProgramStore

# === FIXTURES ===


@pytest.fixture
def integration_config() -> EvolutionConfig:
    """Configuration for integration tests."""
    return EvolutionConfig(
        population_size=50,
        archive_size=5,
        elite_ratio=0.1,
        exploration_ratio=0.2,
    )


@pytest.fixture
def integration_store(temp_db_path: Path) -> ProgramStore:
    """Store for integration tests."""
    return ProgramStore(temp_db_path, population_size=50, archive_size=5)


@pytest.fixture
def mock_evaluator_success() -> MagicMock:
    """Mock evaluator that always succeeds with improving fitness."""
    evaluator = MagicMock()
    call_count = [0]

    async def evaluate(request):
        call_count[0] += 1
        # Fitness improves with each evaluation
        fitness = 1.0 + call_count[0] * 0.1
        return MagicMock(
            success=True,
            metrics=FitnessMetrics(
                sharpe_ratio=fitness,
                calmar_ratio=fitness,
                max_drawdown=0.10,
                cagr=0.15,
                total_return=0.20,
                trade_count=50 + call_count[0],
                win_rate=0.50,
            ),
            error=None,
        )

    evaluator.evaluate = evaluate
    return evaluator


# === PHASE 8: INTEGRATION TESTS (T065-T067) ===


class TestEvolutionLoopFullCycle:
    """T065: Test full evolution loop cycle."""

    @pytest.mark.asyncio
    async def test_evolution_loop_full_cycle(
        self,
        integration_config: EvolutionConfig,
        integration_store: ProgramStore,
        mock_evaluator_success: MagicMock,
    ):
        """Full evolution cycle: seed -> mutate -> evaluate -> store -> repeat."""
        # Pre-populate with seed
        seed_code = _sample_seed_code()
        seed_id = integration_store.insert(
            code=seed_code,
            metrics=FitnessMetrics(
                sharpe_ratio=1.0,
                calmar_ratio=1.0,
                max_drawdown=0.15,
                cagr=0.12,
                total_return=0.18,
                trade_count=40,
                win_rate=0.48,
            ),
            experiment="full_cycle_test",
        )

        controller = EvolutionController(
            config=integration_config,
            store=integration_store,
            evaluator=mock_evaluator_success,
            mutator=MockMutator(),
        )

        # Track events
        events: list[ProgressEvent] = []

        def capture_events(event: ProgressEvent):
            events.append(event)

        # Patch _load_seed_strategy to skip actual loading
        async def mock_load_seed(*args, **kwargs):
            return seed_id

        controller._load_seed_strategy = mock_load_seed

        # Run 5 iterations
        result = await controller.run(
            seed_strategy="momentum",
            experiment="full_cycle_test",
            iterations=5,
            on_progress=capture_events,
        )

        # Verify result
        assert result.status == EvolutionStatus.COMPLETED
        assert result.iterations_completed == 5
        assert result.experiment == "full_cycle_test"

        # Verify population grew
        population_count = integration_store.count("full_cycle_test")
        assert population_count > 1

        # Verify events were emitted
        event_types = {e.event_type for e in events}
        assert ProgressEventType.ITERATION_START in event_types
        assert ProgressEventType.EVOLUTION_COMPLETE in event_types

        # Verify best strategy tracked
        assert result.best_strategy is not None
        assert result.best_strategy.metrics is not None
        assert result.best_strategy.metrics.calmar_ratio > 1.0


class TestEvolutionStopAndResume:
    """T066: Test evolution stop and resume."""

    @pytest.mark.asyncio
    async def test_evolution_stop_graceful(
        self,
        integration_config: EvolutionConfig,
        integration_store: ProgramStore,
        mock_evaluator_success: MagicMock,
    ):
        """Evolution stops gracefully when stop() is called."""
        # Pre-populate with seed
        seed_id = integration_store.insert(
            code=_sample_seed_code(),
            metrics=FitnessMetrics(
                sharpe_ratio=1.0,
                calmar_ratio=1.0,
                max_drawdown=0.15,
                cagr=0.12,
                total_return=0.18,
                trade_count=40,
                win_rate=0.48,
            ),
            experiment="stop_test",
        )

        controller = EvolutionController(
            config=integration_config,
            store=integration_store,
            evaluator=mock_evaluator_success,
            mutator=MockMutator(),
        )

        async def mock_load_seed(*args, **kwargs):
            return seed_id

        controller._load_seed_strategy = mock_load_seed

        # Request stop after 2nd iteration
        iterations_seen = [0]

        def stop_after_two(event: ProgressEvent):
            if event.event_type == ProgressEventType.ITERATION_COMPLETE:
                iterations_seen[0] += 1
                if iterations_seen[0] >= 2:
                    controller.stop()

        result = await controller.run(
            seed_strategy="momentum",
            experiment="stop_test",
            iterations=10,  # Would run 10 if not stopped
            on_progress=stop_after_two,
        )

        # Should have stopped early
        assert result.status == EvolutionStatus.PAUSED
        assert result.iterations_completed <= 3  # At most 2-3 iterations
        assert "stop" in result.stop_reason.lower()

    @pytest.mark.asyncio
    async def test_checkpoint_persistence(
        self,
        integration_config: EvolutionConfig,
        integration_store: ProgramStore,
        mock_evaluator_success: MagicMock,
    ):
        """Checkpoint data is persisted for resume."""
        # Pre-populate with seed
        seed_id = integration_store.insert(
            code=_sample_seed_code(),
            metrics=FitnessMetrics(
                sharpe_ratio=1.0,
                calmar_ratio=1.0,
                max_drawdown=0.15,
                cagr=0.12,
                total_return=0.18,
                trade_count=40,
                win_rate=0.48,
            ),
            experiment="checkpoint_test",
        )

        controller = EvolutionController(
            config=integration_config,
            store=integration_store,
            evaluator=mock_evaluator_success,
            mutator=MockMutator(),
        )

        async def mock_load_seed(*args, **kwargs):
            return seed_id

        controller._load_seed_strategy = mock_load_seed

        # Run 3 iterations
        await controller.run(
            seed_strategy="momentum",
            experiment="checkpoint_test",
            iterations=3,
        )

        # Verify checkpoint data can be loaded
        checkpoint = controller._load_checkpoint("checkpoint_test")
        assert checkpoint is not None
        assert checkpoint["experiment"] == "checkpoint_test"
        assert checkpoint["best_fitness"] >= 1.0


class TestCLIFullWorkflow:
    """T067: Test CLI full workflow (via controller)."""

    @pytest.mark.asyncio
    async def test_workflow_start_to_export(
        self,
        integration_config: EvolutionConfig,
        integration_store: ProgramStore,
        mock_evaluator_success: MagicMock,
    ):
        """Full workflow: start evolution, check status, export best."""
        # Pre-populate with seed
        seed_id = integration_store.insert(
            code=_sample_seed_code(),
            metrics=FitnessMetrics(
                sharpe_ratio=1.0,
                calmar_ratio=1.0,
                max_drawdown=0.15,
                cagr=0.12,
                total_return=0.18,
                trade_count=40,
                win_rate=0.48,
            ),
            experiment="workflow_test",
        )

        controller = EvolutionController(
            config=integration_config,
            store=integration_store,
            evaluator=mock_evaluator_success,
            mutator=MockMutator(),
        )

        async def mock_load_seed(*args, **kwargs):
            return seed_id

        controller._load_seed_strategy = mock_load_seed

        # Step 1: Run evolution
        result = await controller.run(
            seed_strategy="momentum",
            experiment="workflow_test",
            iterations=3,
        )

        assert result.status == EvolutionStatus.COMPLETED

        # Step 2: Check status via get_progress
        progress = controller.get_progress("workflow_test")
        assert progress.experiment == "workflow_test"
        assert progress.population_size > 0

        # Step 3: Get best strategies
        best_strategies = integration_store.top_k(k=5, experiment="workflow_test")
        assert len(best_strategies) > 0

        # Step 4: Verify lineage
        best = best_strategies[0]
        lineage = integration_store.get_lineage(best.id)
        assert len(lineage) >= 1  # At least the strategy itself


# === ADDITIONAL INTEGRATION TESTS ===


class TestEvolutionWithStopConditions:
    """Test evolution with various stop conditions."""

    @pytest.mark.asyncio
    async def test_stop_on_target_fitness(
        self,
        integration_config: EvolutionConfig,
        integration_store: ProgramStore,
    ):
        """Evolution stops when target fitness reached."""
        # Mock evaluator that returns high fitness
        evaluator = MagicMock()
        evaluator.evaluate = AsyncMock(
            return_value=MagicMock(
                success=True,
                metrics=FitnessMetrics(
                    sharpe_ratio=5.0,
                    calmar_ratio=5.0,  # High fitness
                    max_drawdown=0.05,
                    cagr=0.25,
                    total_return=0.50,
                    trade_count=100,
                    win_rate=0.65,
                ),
            )
        )

        seed_id = integration_store.insert(
            code=_sample_seed_code(),
            metrics=FitnessMetrics(
                sharpe_ratio=1.0,
                calmar_ratio=1.0,
                max_drawdown=0.15,
                cagr=0.12,
                total_return=0.18,
                trade_count=40,
                win_rate=0.48,
            ),
            experiment="target_test",
        )

        controller = EvolutionController(
            config=integration_config,
            store=integration_store,
            evaluator=evaluator,
            mutator=MockMutator(),
        )

        async def mock_load_seed(*args, **kwargs):
            return seed_id

        controller._load_seed_strategy = mock_load_seed

        stop_condition = StopCondition(
            max_iterations=100,
            target_fitness=4.0,  # Stop when fitness >= 4.0
        )

        result = await controller.run(
            seed_strategy="momentum",
            experiment="target_test",
            iterations=100,
            stop_condition=stop_condition,
        )

        # Should stop early
        assert result.iterations_completed < 100
        assert "Target fitness" in result.stop_reason


class TestEvolutionErrorRecovery:
    """Test evolution error handling."""

    @pytest.mark.asyncio
    async def test_continues_on_partial_failures(
        self,
        integration_config: EvolutionConfig,
        integration_store: ProgramStore,
    ):
        """Evolution continues despite some evaluation failures."""
        evaluator = MagicMock()
        call_count = [0]

        async def flaky_evaluate(request):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                # Fail every other evaluation
                return MagicMock(
                    success=False,
                    error="Random failure",
                    error_type="runtime",
                    metrics=None,
                )
            return MagicMock(
                success=True,
                metrics=FitnessMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=1.5,
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
            )

        evaluator.evaluate = flaky_evaluate

        seed_id = integration_store.insert(
            code=_sample_seed_code(),
            metrics=FitnessMetrics(
                sharpe_ratio=1.0,
                calmar_ratio=1.0,
                max_drawdown=0.15,
                cagr=0.12,
                total_return=0.18,
                trade_count=40,
                win_rate=0.48,
            ),
            experiment="flaky_test",
        )

        controller = EvolutionController(
            config=integration_config,
            store=integration_store,
            evaluator=evaluator,
            mutator=MockMutator(),
        )

        async def mock_load_seed(*args, **kwargs):
            return seed_id

        controller._load_seed_strategy = mock_load_seed

        result = await controller.run(
            seed_strategy="momentum",
            experiment="flaky_test",
            iterations=5,
        )

        # Should complete despite failures
        assert result.status == EvolutionStatus.COMPLETED
        assert result.iterations_completed == 5
        # Should have some successful evaluations
        assert result.successful_evaluations > 0


# === HELPER FUNCTIONS ===


def _sample_seed_code() -> str:
    """Sample strategy code with EVOLVE-BLOCK."""
    return '''"""Sample momentum strategy."""

from nautilus_trader.trading.strategy import Strategy


class MomentumEvolveStrategy(Strategy):
    """Momentum strategy."""

    def on_start(self):
        """Initialize."""
        pass

    def on_bar(self, bar):
        """Handle bar."""
        # === EVOLVE-BLOCK: decision_logic ===
        if bar.close > bar.open:
            self.buy()
        # === END EVOLVE-BLOCK ===
'''
