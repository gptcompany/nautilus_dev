"""Tests for Alpha-Evolve Controller."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts.alpha_evolve.config import EvolutionConfig
from scripts.alpha_evolve.controller import (
    EvolutionController,
    EvolutionProgress,
    EvolutionStatus,
    ProgressEvent,
    ProgressEventType,
    StopCondition,
)
from scripts.alpha_evolve.mutator import MockMutator
from scripts.alpha_evolve.store import FitnessMetrics, ProgramStore


# === FIXTURES ===


@pytest.fixture
def evolution_config() -> EvolutionConfig:
    """Default evolution configuration."""
    return EvolutionConfig(
        population_size=100,
        archive_size=10,
        elite_ratio=0.1,
        exploration_ratio=0.2,
    )


@pytest.fixture
def temp_store(temp_db_path: Path) -> ProgramStore:
    """Temporary program store for testing."""
    return ProgramStore(temp_db_path, population_size=100, archive_size=10)


@pytest.fixture
def mock_evaluator() -> MagicMock:
    """Mock evaluator that returns successful results."""
    evaluator = MagicMock()
    evaluator.evaluate = AsyncMock(
        return_value=MagicMock(
            success=True,
            metrics=FitnessMetrics(
                sharpe_ratio=1.5,
                calmar_ratio=2.0,
                max_drawdown=0.15,
                cagr=0.30,
                total_return=0.45,
                trade_count=100,
                win_rate=0.55,
            ),
            error=None,
            error_type=None,
        )
    )
    return evaluator


@pytest.fixture
def mock_mutator() -> MockMutator:
    """Mock mutator that returns deterministic mutations."""
    return MockMutator()


@pytest.fixture
def controller(
    evolution_config: EvolutionConfig,
    temp_store: ProgramStore,
    mock_evaluator: MagicMock,
    mock_mutator: MockMutator,
) -> EvolutionController:
    """Evolution controller with mock dependencies."""
    return EvolutionController(
        config=evolution_config,
        store=temp_store,
        evaluator=mock_evaluator,
        mutator=mock_mutator,
    )


# === PHASE 3: USER STORY 1 - EVOLUTION LOOP TESTS (T011-T016) ===


class TestControllerInit:
    """T011: Test controller initialization."""

    def test_init_with_valid_config(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
        mock_evaluator: MagicMock,
    ):
        """Controller initializes with valid configuration."""
        controller = EvolutionController(
            config=evolution_config,
            store=temp_store,
            evaluator=mock_evaluator,
        )

        assert controller.config == evolution_config
        assert controller.store == temp_store
        assert controller.evaluator == mock_evaluator
        assert controller._status == EvolutionStatus.IDLE

    def test_init_with_optional_mutator(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
        mock_evaluator: MagicMock,
        mock_mutator: MockMutator,
    ):
        """Controller accepts optional custom mutator."""
        controller = EvolutionController(
            config=evolution_config,
            store=temp_store,
            evaluator=mock_evaluator,
            mutator=mock_mutator,
        )

        assert controller.mutator == mock_mutator

    def test_init_default_state(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
        mock_evaluator: MagicMock,
    ):
        """Controller starts in IDLE state with zeroed counters."""
        controller = EvolutionController(
            config=evolution_config,
            store=temp_store,
            evaluator=mock_evaluator,
        )

        assert controller._experiment is None
        assert controller._current_iteration == 0
        assert controller._best_fitness == float("-inf")
        assert controller._status == EvolutionStatus.IDLE
        assert controller._mutations_attempted == 0
        assert controller._evaluations_completed == 0


class TestRunSingleIteration:
    """T012: Test running single iteration."""

    @pytest.mark.asyncio
    async def test_run_single_iteration(self, controller: EvolutionController):
        """Single iteration completes seed -> mutate -> evaluate -> store cycle."""
        with patch.object(controller, "_load_seed_strategy", new_callable=AsyncMock):
            # Pre-populate store with a seed
            controller.store.insert(
                code=_sample_momentum_code(),
                metrics=FitnessMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

            result = await controller.run(
                seed_strategy="momentum",
                experiment="test_exp",
                iterations=1,
            )

        assert result.iterations_completed >= 1
        assert result.status in (EvolutionStatus.COMPLETED, EvolutionStatus.PAUSED)

    @pytest.mark.asyncio
    async def test_run_stores_mutated_strategy(self, controller: EvolutionController):
        """Mutated strategy is stored after successful evaluation."""
        with patch.object(controller, "_load_seed_strategy", new_callable=AsyncMock):
            # Pre-populate with seed
            controller.store.insert(
                code=_sample_momentum_code(),
                metrics=FitnessMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

            initial_count = controller.store.count("test_exp")

            await controller.run(
                seed_strategy="momentum",
                experiment="test_exp",
                iterations=1,
            )

            # Store should have more entries (seed + mutation)
            final_count = controller.store.count("test_exp")
            assert final_count >= initial_count


class TestIterationLimit:
    """T013: Test evolution stops at iteration limit."""

    @pytest.mark.asyncio
    async def test_run_stops_at_iteration_limit(self, controller: EvolutionController):
        """Evolution stops when iteration limit is reached."""
        with patch.object(controller, "_load_seed_strategy", new_callable=AsyncMock):
            # Pre-populate store
            controller.store.insert(
                code=_sample_momentum_code(),
                metrics=FitnessMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

            result = await controller.run(
                seed_strategy="momentum",
                experiment="test_exp",
                iterations=3,
            )

        assert result.iterations_completed <= 3
        assert result.stop_reason is not None


class TestContinueOnEvaluationFailure:
    """T014: Test controller continues on individual evaluation failures."""

    @pytest.mark.asyncio
    async def test_continues_on_evaluation_failure(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
    ):
        """Controller continues when individual evaluation fails."""
        # Create mock evaluator that fails first, succeeds second
        mock_evaluator = MagicMock()
        call_count = [0]

        async def flaky_evaluate(request):
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(
                    success=False,
                    error="Timeout",
                    error_type="timeout",
                    metrics=None,
                )
            return MagicMock(
                success=True,
                metrics=FitnessMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=0.15,
                    cagr=0.30,
                    total_return=0.45,
                    trade_count=100,
                    win_rate=0.55,
                ),
            )

        mock_evaluator.evaluate = flaky_evaluate

        controller = EvolutionController(
            config=evolution_config,
            store=temp_store,
            evaluator=mock_evaluator,
            mutator=MockMutator(),
        )

        with patch.object(controller, "_load_seed_strategy", new_callable=AsyncMock):
            # Pre-populate store
            temp_store.insert(
                code=_sample_momentum_code(),
                metrics=FitnessMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

            result = await controller.run(
                seed_strategy="momentum",
                experiment="test_exp",
                iterations=3,
            )

        # Should complete despite first failure
        assert result.iterations_completed >= 2
        assert result.status != EvolutionStatus.FAILED


class TestTargetFitnessStopCondition:
    """T015: Test stop condition - target fitness."""

    @pytest.mark.asyncio
    async def test_stop_condition_target_fitness(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
    ):
        """Evolution stops when target fitness is reached."""
        # Create evaluator that returns high fitness
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate = AsyncMock(
            return_value=MagicMock(
                success=True,
                metrics=FitnessMetrics(
                    sharpe_ratio=3.0,
                    calmar_ratio=5.0,  # Very high fitness
                    max_drawdown=0.05,
                    cagr=0.50,
                    total_return=0.80,
                    trade_count=200,
                    win_rate=0.65,
                ),
            )
        )

        controller = EvolutionController(
            config=evolution_config,
            store=temp_store,
            evaluator=mock_evaluator,
            mutator=MockMutator(),
        )

        with patch.object(controller, "_load_seed_strategy", new_callable=AsyncMock):
            temp_store.insert(
                code=_sample_momentum_code(),
                metrics=FitnessMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

            stop_condition = StopCondition(
                max_iterations=100,
                target_fitness=4.0,  # Target below what evaluator returns
            )

            result = await controller.run(
                seed_strategy="momentum",
                experiment="test_exp",
                iterations=100,
                stop_condition=stop_condition,
            )

        # Should stop early due to target fitness
        assert result.iterations_completed < 100
        assert "Target fitness" in (result.stop_reason or "")


class TestProgressEventEmission:
    """T016: Test progress event emission."""

    @pytest.mark.asyncio
    async def test_progress_event_emission(self, controller: EvolutionController):
        """Controller emits progress events during evolution."""
        events: list[ProgressEvent] = []

        def capture_progress(event: ProgressEvent):
            events.append(event)

        with patch.object(controller, "_load_seed_strategy", new_callable=AsyncMock):
            controller.store.insert(
                code=_sample_momentum_code(),
                metrics=FitnessMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

            await controller.run(
                seed_strategy="momentum",
                experiment="test_exp",
                iterations=2,
                on_progress=capture_progress,
            )

        # Should have multiple event types
        event_types = {e.event_type for e in events}
        assert ProgressEventType.ITERATION_START in event_types
        assert ProgressEventType.EVOLUTION_COMPLETE in event_types

    @pytest.mark.asyncio
    async def test_progress_events_have_correct_structure(self, controller: EvolutionController):
        """Progress events have expected fields."""
        events: list[ProgressEvent] = []

        def capture_progress(event: ProgressEvent):
            events.append(event)

        with patch.object(controller, "_load_seed_strategy", new_callable=AsyncMock):
            controller.store.insert(
                code=_sample_momentum_code(),
                metrics=FitnessMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

            await controller.run(
                seed_strategy="momentum",
                experiment="test_exp",
                iterations=1,
                on_progress=capture_progress,
            )

        assert len(events) > 0
        for event in events:
            assert isinstance(event.event_type, ProgressEventType)
            assert isinstance(event.iteration, int)
            assert event.timestamp is not None
            assert isinstance(event.data, dict)


# === PHASE 4: USER STORY 2 - PARENT SELECTION TESTS (T024-T028) ===


class TestParentSelectionModeDistribution:
    """T024: Test parent selection mode distribution."""

    def test_select_parent_mode_distribution(self, controller: EvolutionController):
        """Selection modes follow configured distribution (10/70/20)."""
        modes = {"elite": 0, "exploit": 0, "explore": 0}

        # Sample many times
        for _ in range(1000):
            mode = controller._select_parent_mode()
            modes[mode] += 1

        # Check distribution within tolerance
        total = sum(modes.values())
        elite_ratio = modes["elite"] / total
        exploit_ratio = modes["exploit"] / total
        explore_ratio = modes["explore"] / total

        # 10% elite (+/- 5%)
        assert 0.05 <= elite_ratio <= 0.15, f"Elite ratio: {elite_ratio}"
        # 70% exploit (+/- 10%)
        assert 0.60 <= exploit_ratio <= 0.80, f"Exploit ratio: {exploit_ratio}"
        # 20% explore (+/- 5%)
        assert 0.15 <= explore_ratio <= 0.25, f"Explore ratio: {explore_ratio}"


class TestSelectParentElite:
    """T025: Test elite parent selection."""

    def test_select_parent_elite(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
        mock_evaluator: MagicMock,
    ):
        """Elite selection picks from top 10% performers."""
        # Add strategies with varying fitness
        for i in range(100):
            temp_store.insert(
                code=f"# Strategy {i}",
                metrics=FitnessMetrics(
                    sharpe_ratio=float(i),
                    calmar_ratio=float(i),  # Higher = better
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

        # Controller for context (not used directly in sampling test)
        EvolutionController(
            config=evolution_config,
            store=temp_store,
            evaluator=mock_evaluator,
        )

        # Sample from elite multiple times
        elite_samples = []
        for _ in range(100):
            parent = temp_store.sample(strategy="elite", experiment="test_exp")
            if parent and parent.metrics:
                elite_samples.append(parent.metrics.calmar_ratio)

        # Elite should come from top 10 (fitness >= 90)
        avg_fitness = sum(elite_samples) / len(elite_samples)
        assert avg_fitness >= 85, f"Average elite fitness: {avg_fitness}"


class TestSelectParentExploit:
    """T026: Test exploit parent selection."""

    def test_select_parent_exploit(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
        mock_evaluator: MagicMock,
    ):
        """Exploit selection weights by fitness."""
        # Add strategies with varying fitness
        for i in range(10):
            temp_store.insert(
                code=f"# Strategy {i}",
                metrics=FitnessMetrics(
                    sharpe_ratio=float(i),
                    calmar_ratio=float(i),
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

        # Sample many times and count by fitness
        fitness_counts: dict[float, int] = {float(i): 0 for i in range(10)}
        for _ in range(1000):
            parent = temp_store.sample(strategy="exploit", experiment="test_exp")
            if parent and parent.metrics:
                fitness_counts[parent.metrics.calmar_ratio] += 1

        # Higher fitness should be selected more often
        high_fitness_count = sum(fitness_counts[f] for f in [7.0, 8.0, 9.0])
        low_fitness_count = sum(fitness_counts[f] for f in [0.0, 1.0, 2.0])

        # High fitness should be selected more than low
        assert high_fitness_count > low_fitness_count


class TestSelectParentExplore:
    """T027: Test explore parent selection."""

    def test_select_parent_explore(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
        mock_evaluator: MagicMock,
    ):
        """Explore selection is uniform random."""
        # Add strategies with varying fitness
        for i in range(10):
            temp_store.insert(
                code=f"# Strategy {i}",
                metrics=FitnessMetrics(
                    sharpe_ratio=float(i),
                    calmar_ratio=float(i),
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

        # Sample many times
        samples = []
        for _ in range(1000):
            parent = temp_store.sample(strategy="explore", experiment="test_exp")
            if parent and parent.metrics:
                samples.append(parent.metrics.calmar_ratio)

        # Should sample from full range (uniform)
        unique_samples = set(samples)
        assert len(unique_samples) >= 8, "Explore should sample from all strategies"


class TestSelectParentEmptyStore:
    """T028: Test parent selection with empty store."""

    def test_select_parent_empty_store(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
        mock_evaluator: MagicMock,
    ):
        """Parent selection raises error on empty store."""
        controller = EvolutionController(
            config=evolution_config,
            store=temp_store,
            evaluator=mock_evaluator,
        )

        controller._experiment = "empty_exp"

        with pytest.raises(RuntimeError, match="store is empty"):
            controller._select_parent("empty_exp")


# === STOP CONDITION TESTS ===


class TestStopConditionValidation:
    """Test StopCondition validation."""

    def test_valid_stop_condition(self):
        """Valid stop condition passes validation."""
        sc = StopCondition(
            max_iterations=50,
            target_fitness=2.0,
            max_time_seconds=3600,
            no_improvement_generations=10,
        )
        assert sc.max_iterations == 50

    def test_invalid_max_iterations(self):
        """Invalid max_iterations raises error."""
        with pytest.raises(ValueError, match="max_iterations"):
            StopCondition(max_iterations=0)

    def test_invalid_target_fitness(self):
        """Negative target_fitness raises error."""
        with pytest.raises(ValueError, match="target_fitness"):
            StopCondition(target_fitness=-1.0)


# === GET PROGRESS TESTS ===


class TestGetProgress:
    """Test get_progress method."""

    def test_get_progress_no_active_experiment(
        self,
        evolution_config: EvolutionConfig,
        temp_store: ProgramStore,
        mock_evaluator: MagicMock,
    ):
        """get_progress raises error when no experiment active."""
        controller = EvolutionController(
            config=evolution_config,
            store=temp_store,
            evaluator=mock_evaluator,
        )

        with pytest.raises(ValueError, match="No active experiment"):
            controller.get_progress()

    @pytest.mark.asyncio
    async def test_get_progress_during_run(self, controller: EvolutionController):
        """get_progress returns current state during evolution."""
        progress_snapshots: list[EvolutionProgress] = []

        def capture_progress(event: ProgressEvent):
            # Only capture during iteration events (while still running)
            if event.event_type == ProgressEventType.ITERATION_START:
                progress = controller.get_progress()
                progress_snapshots.append(progress)

        with patch.object(controller, "_load_seed_strategy", new_callable=AsyncMock):
            controller.store.insert(
                code=_sample_momentum_code(),
                metrics=FitnessMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=0.10,
                    cagr=0.15,
                    total_return=0.20,
                    trade_count=50,
                    win_rate=0.50,
                ),
                experiment="test_exp",
            )

            await controller.run(
                seed_strategy="momentum",
                experiment="test_exp",
                iterations=2,
                on_progress=capture_progress,
            )

        assert len(progress_snapshots) > 0
        for p in progress_snapshots:
            assert p.experiment == "test_exp"
            # During iteration start, status should be RUNNING
            assert p.status == EvolutionStatus.RUNNING


# === HELPER FUNCTIONS ===


def _sample_momentum_code() -> str:
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
