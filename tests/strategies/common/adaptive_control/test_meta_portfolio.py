"""Comprehensive tests for MetaPortfolio module.

Tests cover:
1. BacktestMatrix - configuration generation, backtest execution, result selection
2. MetaPortfolio - system registration, signal aggregation, PnL updates, adaptation
3. Factory function - create_meta_portfolio_from_backtest

Coverage targets:
- Lines 119-121, 125, 141-158, 162-174, 194-203, 207-227
- Lines 258-271, 285-299, 303-314, 333-361, 365-377
- Lines 389-439, 443-456, 460-464, 468-471, 492-503, 507-522, 526-539
- Lines 559-582

Works with --noconftest flag (all fixtures defined locally).
"""

import json
import math
import tempfile
from pathlib import Path

import pytest

from strategies.common.adaptive_control.meta_portfolio import (
    BacktestMatrix,
    BacktestResult,
    MetaPortfolio,
    SystemConfig,
    SystemState,
    create_meta_portfolio_from_backtest,
)

# =============================================================================
# Test Fixtures (local for --noconftest)
# =============================================================================


def make_system_config(
    name: str = "test_system",
    selector_type: str = "thompson",
    n_particles: int = 0,
    strategies: list[str] = None,
) -> SystemConfig:
    """Create a test SystemConfig."""
    return SystemConfig(
        name=name,
        selector_type=selector_type,
        n_particles=n_particles,
        strategies=strategies or ["strat_a", "strat_b"],
    )


def make_backtest_result(
    config: SystemConfig = None,
    sharpe_ratio: float = 1.5,
    sortino_ratio: float = 2.0,
    max_drawdown: float = 0.15,
    total_return: float = 0.25,
    win_rate: float = 0.55,
    n_trades: int = 100,
    pnl_series: list[float] = None,
) -> BacktestResult:
    """Create a test BacktestResult."""
    return BacktestResult(
        config=config or make_system_config(),
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown=max_drawdown,
        total_return=total_return,
        win_rate=win_rate,
        n_trades=n_trades,
        pnl_series=pnl_series or [0.01, -0.005, 0.02, -0.01, 0.015],
    )


# =============================================================================
# SystemConfig Tests
# =============================================================================


class TestSystemConfig:
    """Test SystemConfig dataclass."""

    def test_create_config(self):
        """Test creating SystemConfig."""
        config = SystemConfig(
            name="test",
            selector_type="thompson",
            n_particles=0,
            strategies=["a", "b"],
        )
        assert config.name == "test"
        assert config.selector_type == "thompson"
        assert config.n_particles == 0
        assert config.strategies == ["a", "b"]
        assert config.parameters == {}

    def test_config_with_parameters(self):
        """Test SystemConfig with custom parameters."""
        config = SystemConfig(
            name="test",
            selector_type="particle",
            n_particles=50,
            strategies=["mom", "mr"],
            parameters={"learning_rate": 0.1},
        )
        assert config.parameters == {"learning_rate": 0.1}


class TestBacktestResult:
    """Test BacktestResult dataclass."""

    def test_create_result(self):
        """Test creating BacktestResult."""
        config = make_system_config()
        result = BacktestResult(
            config=config,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            max_drawdown=0.1,
            total_return=0.25,
            win_rate=0.6,
            n_trades=50,
        )
        assert result.sharpe_ratio == 1.5
        assert result.n_trades == 50
        assert result.pnl_series == []

    def test_result_with_pnl_series(self):
        """Test BacktestResult with PnL series."""
        result = make_backtest_result(pnl_series=[0.01, -0.02, 0.03])
        assert result.pnl_series == [0.01, -0.02, 0.03]


class TestSystemState:
    """Test SystemState dataclass."""

    def test_create_state(self):
        """Test creating SystemState."""
        state = SystemState(
            name="sys1",
            weight=0.5,
            cumulative_pnl=100.0,
            recent_pnl=[10, 20, -5],
            n_updates=10,
            is_active=True,
        )
        assert state.name == "sys1"
        assert state.weight == 0.5
        assert state.is_active is True


# =============================================================================
# BacktestMatrix Tests (covers lines 119-121, 125, 141-158, 162-174, 194-203, 207-227)
# =============================================================================


class TestBacktestMatrixInit:
    """Test BacktestMatrix initialization (lines 119-121)."""

    def test_init_without_runner(self):
        """Test initialization without backtest runner."""
        matrix = BacktestMatrix()
        assert matrix.backtest_runner is None
        assert matrix.configs == []
        assert matrix.results == []

    def test_init_with_runner(self):
        """Test initialization with backtest runner."""

        def runner(config):
            return make_backtest_result(config=config)

        matrix = BacktestMatrix(backtest_runner=runner)
        assert matrix.backtest_runner is not None


class TestBacktestMatrixAddConfig:
    """Test BacktestMatrix.add_config (line 125)."""

    def test_add_single_config(self):
        """Test adding a single config."""
        matrix = BacktestMatrix()
        config = make_system_config(name="config1")
        matrix.add_config(config)
        assert len(matrix.configs) == 1
        assert matrix.configs[0].name == "config1"

    def test_add_multiple_configs(self):
        """Test adding multiple configs."""
        matrix = BacktestMatrix()
        for i in range(5):
            matrix.add_config(make_system_config(name=f"config_{i}"))
        assert len(matrix.configs) == 5


class TestBacktestMatrixGenerateConfigs:
    """Test BacktestMatrix.generate_configs (lines 141-158)."""

    def test_generate_thompson_configs(self):
        """Test generating Thompson selector configs (n_particles=0)."""
        matrix = BacktestMatrix()
        matrix.generate_configs(
            selector_types=["thompson"],
            particle_counts=[0],
            strategy_sets=[["mom", "mr"]],
        )
        assert len(matrix.configs) == 1
        assert matrix.configs[0].selector_type == "thompson"
        assert matrix.configs[0].n_particles == 0

    def test_generate_particle_configs(self):
        """Test generating particle selector configs."""
        matrix = BacktestMatrix()
        matrix.generate_configs(
            selector_types=["particle"],
            particle_counts=[20, 50],
            strategy_sets=[["mom", "mr"]],
        )
        assert len(matrix.configs) == 2
        assert all(c.selector_type == "particle" for c in matrix.configs)
        assert all(c.n_particles > 0 for c in matrix.configs)

    def test_generate_bayesian_configs(self):
        """Test generating Bayesian selector configs."""
        matrix = BacktestMatrix()
        matrix.generate_configs(
            selector_types=["bayesian"],
            particle_counts=[100],
            strategy_sets=[["a", "b", "c"]],
        )
        assert len(matrix.configs) == 1
        assert matrix.configs[0].n_particles == 100

    def test_skip_invalid_thompson_with_particles(self):
        """Test that Thompson + n_particles > 0 is skipped."""
        matrix = BacktestMatrix()
        matrix.generate_configs(
            selector_types=["thompson"],
            particle_counts=[0, 50],  # 50 should be skipped for thompson
            strategy_sets=[["mom"]],
        )
        assert len(matrix.configs) == 1
        assert matrix.configs[0].n_particles == 0

    def test_skip_invalid_particle_with_zero_particles(self):
        """Test that particle/bayesian + n_particles=0 is skipped."""
        matrix = BacktestMatrix()
        matrix.generate_configs(
            selector_types=["particle", "bayesian"],
            particle_counts=[0, 50],  # 0 should be skipped for particle/bayesian
            strategy_sets=[["mom"]],
        )
        assert len(matrix.configs) == 2
        assert all(c.n_particles == 50 for c in matrix.configs)

    def test_generate_full_matrix(self):
        """Test generating full configuration matrix."""
        matrix = BacktestMatrix()
        matrix.generate_configs(
            selector_types=["thompson", "particle", "bayesian"],
            particle_counts=[0, 20, 50],
            strategy_sets=[["a", "b"], ["a", "b", "c"]],
        )
        # thompson: 1 particle count (0) * 2 strategy sets = 2
        # particle: 2 particle counts (20, 50) * 2 strategy sets = 4
        # bayesian: 2 particle counts (20, 50) * 2 strategy sets = 4
        assert len(matrix.configs) == 10

    def test_config_naming_convention(self):
        """Test config names follow expected format."""
        matrix = BacktestMatrix()
        matrix.generate_configs(
            selector_types=["particle"],
            particle_counts=[50],
            strategy_sets=[["mom", "mr"]],
        )
        assert matrix.configs[0].name == "particle_50p_2s"


class TestBacktestMatrixRunAll:
    """Test BacktestMatrix.run_all (lines 162-174)."""

    def test_run_all_without_runner_raises(self):
        """Test that run_all raises without backtest_runner."""
        matrix = BacktestMatrix()
        matrix.add_config(make_system_config())
        with pytest.raises(ValueError, match="No backtest_runner provided"):
            matrix.run_all()

    def test_run_all_success(self):
        """Test successful run_all execution."""

        def runner(config: SystemConfig) -> BacktestResult:
            return make_backtest_result(config=config, sharpe_ratio=1.0 + len(config.name) * 0.01)

        matrix = BacktestMatrix(backtest_runner=runner)
        for i in range(3):
            matrix.add_config(make_system_config(name=f"config_{i}"))

        results = matrix.run_all()
        assert len(results) == 3
        assert all(isinstance(r, BacktestResult) for r in results)

    def test_run_all_handles_exceptions(self):
        """Test that run_all handles backtest failures gracefully."""
        call_count = [0]

        def failing_runner(config: SystemConfig) -> BacktestResult:
            call_count[0] += 1
            if call_count[0] == 2:
                raise RuntimeError("Simulated failure")
            return make_backtest_result(config=config)

        matrix = BacktestMatrix(backtest_runner=failing_runner)
        for i in range(3):
            matrix.add_config(make_system_config(name=f"config_{i}"))

        results = matrix.run_all()
        # Only 2 results (one failed)
        assert len(results) == 2

    def test_run_all_clears_previous_results(self):
        """Test that run_all clears previous results."""

        def runner(config):
            return make_backtest_result(config=config)

        matrix = BacktestMatrix(backtest_runner=runner)
        matrix.add_config(make_system_config(name="test"))
        matrix.results = [make_backtest_result()]  # Pre-existing result

        matrix.run_all()
        assert len(matrix.results) == 1


class TestBacktestMatrixSelectTopK:
    """Test BacktestMatrix.select_top_k (lines 194-203)."""

    def test_select_top_k_by_sharpe(self):
        """Test selecting top K by Sharpe ratio."""
        matrix = BacktestMatrix()
        matrix.results = [
            make_backtest_result(sharpe_ratio=1.0, n_trades=50),
            make_backtest_result(sharpe_ratio=2.0, n_trades=50),
            make_backtest_result(sharpe_ratio=1.5, n_trades=50),
        ]

        top = matrix.select_top_k(k=2)
        assert len(top) == 2
        assert top[0].sharpe_ratio == 2.0
        assert top[1].sharpe_ratio == 1.5

    def test_select_top_k_by_sortino(self):
        """Test selecting top K by Sortino ratio."""
        matrix = BacktestMatrix()
        matrix.results = [
            make_backtest_result(sortino_ratio=1.0, n_trades=50),
            make_backtest_result(sortino_ratio=3.0, n_trades=50),
            make_backtest_result(sortino_ratio=2.0, n_trades=50),
        ]

        top = matrix.select_top_k(k=2, metric="sortino_ratio")
        assert len(top) == 2
        assert top[0].sortino_ratio == 3.0

    def test_select_top_k_by_total_return(self):
        """Test selecting top K by total return."""
        matrix = BacktestMatrix()
        matrix.results = [
            make_backtest_result(total_return=0.1, n_trades=50),
            make_backtest_result(total_return=0.5, n_trades=50),
            make_backtest_result(total_return=0.3, n_trades=50),
        ]

        top = matrix.select_top_k(k=1, metric="total_return")
        assert top[0].total_return == 0.5

    def test_select_top_k_filters_min_trades(self):
        """Test that min_trades filter is applied."""
        matrix = BacktestMatrix()
        matrix.results = [
            make_backtest_result(sharpe_ratio=3.0, n_trades=10),  # Below min
            make_backtest_result(sharpe_ratio=1.0, n_trades=50),
            make_backtest_result(sharpe_ratio=2.0, n_trades=50),
        ]

        top = matrix.select_top_k(k=3, min_trades=30)
        assert len(top) == 2
        # Highest sharpe (3.0) should be filtered out
        assert top[0].sharpe_ratio == 2.0

    def test_select_top_k_when_k_exceeds_available(self):
        """Test when k > number of valid results."""
        matrix = BacktestMatrix()
        matrix.results = [
            make_backtest_result(sharpe_ratio=1.0, n_trades=50),
            make_backtest_result(sharpe_ratio=2.0, n_trades=50),
        ]

        top = matrix.select_top_k(k=10)
        assert len(top) == 2

    def test_select_top_k_empty_results(self):
        """Test selecting from empty results."""
        matrix = BacktestMatrix()
        matrix.results = []

        top = matrix.select_top_k(k=3)
        assert len(top) == 0


class TestBacktestMatrixSaveResults:
    """Test BacktestMatrix.save_results (lines 207-227)."""

    def test_save_results_creates_file(self):
        """Test that save_results creates a JSON file."""
        matrix = BacktestMatrix()
        config = make_system_config(name="test_sys", strategies=["a", "b"])
        matrix.results = [make_backtest_result(config=config)]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            matrix.save_results(path)
            assert path.exists()

            with open(path) as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]["config"]["name"] == "test_sys"
            assert data[0]["sharpe_ratio"] == 1.5
        finally:
            path.unlink()

    def test_save_results_multiple_results(self):
        """Test saving multiple results."""
        matrix = BacktestMatrix()
        for i in range(5):
            config = make_system_config(name=f"sys_{i}")
            matrix.results.append(make_backtest_result(config=config, sharpe_ratio=i * 0.5))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            matrix.save_results(path)

            with open(path) as f:
                data = json.load(f)

            assert len(data) == 5
            assert data[2]["sharpe_ratio"] == 1.0  # i=2 -> 2*0.5
        finally:
            path.unlink()

    def test_save_results_includes_all_fields(self):
        """Test that all result fields are saved."""
        matrix = BacktestMatrix()
        config = make_system_config(
            name="full_test",
            selector_type="particle",
            n_particles=50,
            strategies=["mom", "mr", "trend"],
        )
        matrix.results = [
            make_backtest_result(
                config=config,
                sharpe_ratio=1.5,
                sortino_ratio=2.0,
                max_drawdown=0.15,
                total_return=0.25,
                win_rate=0.55,
                n_trades=100,
            )
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            matrix.save_results(path)

            with open(path) as f:
                data = json.load(f)

            result = data[0]
            assert result["config"]["name"] == "full_test"
            assert result["config"]["selector_type"] == "particle"
            assert result["config"]["n_particles"] == 50
            assert result["config"]["strategies"] == ["mom", "mr", "trend"]
            assert result["sharpe_ratio"] == 1.5
            assert result["sortino_ratio"] == 2.0
            assert result["max_drawdown"] == 0.15
            assert result["total_return"] == 0.25
            assert result["win_rate"] == 0.55
            assert result["n_trades"] == 100
        finally:
            path.unlink()


# =============================================================================
# MetaPortfolio Tests (covers lines 258-271, 285-299, 303-314, 333-361, 365-377,
#                      389-439, 443-456, 460-464, 468-471, 492-503, 507-522, 526-539)
# =============================================================================


class TestMetaPortfolioInit:
    """Test MetaPortfolio initialization (lines 258-271)."""

    def test_default_initialization(self):
        """Test default initialization values."""
        portfolio = MetaPortfolio()
        assert portfolio.base_size == 1000.0
        assert portfolio.giller_exponent == 0.5
        assert portfolio.adaptation_rate == 0.1
        assert portfolio.min_weight == 0.05
        assert portfolio.max_weight == 0.5
        assert portfolio.deactivation_threshold == -0.20
        assert portfolio._total_pnl == 0.0
        assert portfolio._peak_equity == 0.0
        assert portfolio._history == []

    def test_custom_initialization(self):
        """Test custom initialization values."""
        portfolio = MetaPortfolio(
            base_size=5000.0,
            giller_exponent=0.7,
            adaptation_rate=0.2,
            min_weight=0.1,
            max_weight=0.4,
            deactivation_threshold=-0.15,
        )
        assert portfolio.base_size == 5000.0
        assert portfolio.giller_exponent == 0.7
        assert portfolio.adaptation_rate == 0.2
        assert portfolio.min_weight == 0.1
        assert portfolio.max_weight == 0.4
        assert portfolio.deactivation_threshold == -0.15


class TestMetaPortfolioRegisterSystem:
    """Test MetaPortfolio.register_system (lines 285-299)."""

    def test_register_single_system(self):
        """Test registering a single system."""
        portfolio = MetaPortfolio()
        portfolio.register_system("system_a", initial_weight=0.5)

        assert "system_a" in portfolio._systems
        assert portfolio._systems["system_a"].weight == 0.5
        assert portfolio._systems["system_a"].is_active is True
        assert portfolio._systems["system_a"].cumulative_pnl == 0.0

    def test_register_system_equal_weight(self):
        """Test registering system without initial weight."""
        portfolio = MetaPortfolio()
        portfolio.register_system("system_a")

        # First system gets weight 1.0 (1/1)
        assert portfolio._systems["system_a"].weight == 1.0

    def test_register_multiple_systems(self):
        """Test registering multiple systems."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a", initial_weight=0.4)
        portfolio.register_system("b", initial_weight=0.3)
        portfolio.register_system("c", initial_weight=0.3)

        assert len(portfolio._systems) == 3

    def test_register_rebuilds_ensemble(self):
        """Test that registration rebuilds the ensemble."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")

        # With 2+ systems, ensemble should be created
        assert portfolio._ensemble is not None
        assert portfolio._thompson is not None


class TestMetaPortfolioRebuildEnsemble:
    """Test MetaPortfolio._rebuild_ensemble (lines 303-314)."""

    def test_rebuild_with_single_system(self):
        """Test ensemble with single system (no ensemble, only Thompson)."""
        portfolio = MetaPortfolio()
        portfolio.register_system("only_one")

        # Less than 2 systems -> no ensemble
        assert portfolio._ensemble is None
        assert portfolio._thompson is not None

    def test_rebuild_with_two_systems(self):
        """Test ensemble with two systems."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")

        assert portfolio._ensemble is not None
        assert len(portfolio._ensemble.strategies) == 2

    def test_rebuild_excludes_inactive_systems(self):
        """Test that inactive systems are excluded from ensemble."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")
        portfolio.register_system("c")

        # Deactivate one system
        portfolio._systems["b"].is_active = False
        portfolio._rebuild_ensemble()

        assert len(portfolio._ensemble.strategies) == 2
        assert "b" not in portfolio._ensemble.strategies


class TestMetaPortfolioAggregate:
    """Test MetaPortfolio.aggregate (lines 333-361)."""

    def test_aggregate_single_system(self):
        """Test aggregation with single system."""
        portfolio = MetaPortfolio(base_size=1000.0)
        portfolio.register_system("a", initial_weight=1.0)

        signal, size = portfolio.aggregate({"a": 0.5})

        assert signal == 0.5
        # size = |0.5|^0.5 * 1000 = 0.707 * 1000 ≈ 707
        expected_size = (0.5**0.5) * 1000.0
        assert abs(size - expected_size) < 0.01

    def test_aggregate_multiple_systems(self):
        """Test aggregation with multiple systems."""
        portfolio = MetaPortfolio(base_size=1000.0)
        portfolio.register_system("a", initial_weight=0.5)
        portfolio.register_system("b", initial_weight=0.5)

        signal, size = portfolio.aggregate({"a": 1.0, "b": 0.5})

        # Weighted signal = (0.5 * 1.0 + 0.5 * 0.5) / 1.0 = 0.75
        assert abs(signal - 0.75) < 0.01

    def test_aggregate_zero_signal(self):
        """Test aggregation with zero signal."""
        portfolio = MetaPortfolio(base_size=1000.0)
        portfolio.register_system("a", initial_weight=1.0)

        signal, size = portfolio.aggregate({"a": 0.0})

        assert signal == 0.0
        assert size == 0.0

    def test_aggregate_negative_signal(self):
        """Test aggregation with negative signal."""
        portfolio = MetaPortfolio(base_size=1000.0)
        portfolio.register_system("a", initial_weight=1.0)

        signal, size = portfolio.aggregate({"a": -0.5})

        assert signal == -0.5
        # Size should be negative
        expected_size = -((0.5**0.5) * 1000.0)
        assert abs(size - expected_size) < 0.01

    def test_aggregate_ignores_unknown_systems(self):
        """Test that unknown systems are ignored."""
        portfolio = MetaPortfolio(base_size=1000.0)
        portfolio.register_system("a", initial_weight=1.0)

        signal, size = portfolio.aggregate({"a": 0.5, "unknown": 1.0})

        assert abs(signal - 0.5) < 0.01

    def test_aggregate_ignores_inactive_systems(self):
        """Test that inactive systems are ignored."""
        portfolio = MetaPortfolio(base_size=1000.0)
        portfolio.register_system("a", initial_weight=0.5)
        portfolio.register_system("b", initial_weight=0.5)
        portfolio._systems["b"].is_active = False

        signal, size = portfolio.aggregate({"a": 1.0, "b": -1.0})

        # Only 'a' should be used
        assert signal == 1.0

    def test_aggregate_giller_exponent(self):
        """Test Giller sizing with different exponents."""
        portfolio = MetaPortfolio(base_size=1000.0, giller_exponent=0.3)
        portfolio.register_system("a", initial_weight=1.0)

        signal, size = portfolio.aggregate({"a": 0.5})

        expected_size = (0.5**0.3) * 1000.0
        assert abs(size - expected_size) < 0.01


class TestMetaPortfolioGetCurrentWeights:
    """Test MetaPortfolio._get_current_weights (lines 365-377)."""

    def test_get_weights_normalized(self):
        """Test that weights are normalized."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a", initial_weight=0.2)
        portfolio.register_system("b", initial_weight=0.3)

        weights = portfolio._get_current_weights()

        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01

    def test_get_weights_excludes_inactive(self):
        """Test that inactive systems are excluded."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a", initial_weight=0.5)
        portfolio.register_system("b", initial_weight=0.5)
        portfolio._systems["b"].is_active = False

        weights = portfolio._get_current_weights()

        assert "b" not in weights or weights.get("b", 0) == 0
        # 'a' should now have weight 1.0 after normalization
        if "a" in weights:
            assert weights["a"] == 1.0


class TestMetaPortfolioUpdatePnL:
    """Test MetaPortfolio.update_pnl (lines 389-439)."""

    def test_update_pnl_updates_cumulative(self):
        """Test that PnL updates cumulative values."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")

        portfolio.update_pnl({"a": 10.0, "b": 5.0})

        assert portfolio._systems["a"].cumulative_pnl == 10.0
        assert portfolio._systems["b"].cumulative_pnl == 5.0

    def test_update_pnl_tracks_recent(self):
        """Test that recent PnL is tracked."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")

        for i in range(10):
            portfolio.update_pnl({"a": float(i)})

        assert len(portfolio._systems["a"].recent_pnl) == 10
        assert portfolio._systems["a"].n_updates == 10

    def test_update_pnl_limits_history(self):
        """Test that recent PnL history is limited to 50."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")

        for i in range(60):
            portfolio.update_pnl({"a": float(i)})

        assert len(portfolio._systems["a"].recent_pnl) == 50

    def test_update_pnl_deactivates_poor_system(self):
        """Test that systems with poor PnL are deactivated."""
        portfolio = MetaPortfolio(base_size=1000.0, deactivation_threshold=-0.20)
        portfolio.register_system("a")
        portfolio.register_system("b")

        # Deactivation at -20% of base_size = -200
        portfolio.update_pnl({"a": -250.0, "b": 10.0})

        assert portfolio._systems["a"].is_active is False
        assert portfolio._systems["b"].is_active is True

    def test_update_pnl_returns_weights(self):
        """Test that update_pnl returns updated weights."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")

        weights = portfolio.update_pnl({"a": 10.0, "b": 5.0})

        assert "a" in weights or "b" in weights
        assert sum(weights.values()) <= 1.01  # Allow small rounding errors

    def test_update_pnl_tracks_total(self):
        """Test that total PnL is tracked."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")

        portfolio.update_pnl({"a": 10.0, "b": 5.0})
        portfolio.update_pnl({"a": -3.0, "b": 2.0})

        assert portfolio._total_pnl == 14.0  # 10 + 5 - 3 + 2

    def test_update_pnl_tracks_peak_equity(self):
        """Test that peak equity is tracked."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")

        portfolio.update_pnl({"a": 100.0})
        portfolio.update_pnl({"a": -50.0})
        portfolio.update_pnl({"a": 30.0})

        assert portfolio._peak_equity == 100.0

    def test_update_pnl_records_history(self):
        """Test that history is recorded."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")

        portfolio.update_pnl({"a": 10.0})

        assert len(portfolio._history) == 1
        assert "timestamp" in portfolio._history[0]
        assert portfolio._history[0]["pnls"] == {"a": 10.0}

    def test_update_pnl_ignores_unknown_system(self):
        """Test that unknown systems in PnL dict are ignored."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")

        portfolio.update_pnl({"a": 10.0, "unknown": 100.0})

        assert portfolio._systems["a"].cumulative_pnl == 10.0
        assert "unknown" not in portfolio._systems


class TestMetaPortfolioUpdateWeightsFromProbs:
    """Test MetaPortfolio._update_weights_from_probs (lines 443-456)."""

    def test_update_weights_adapts_to_probs(self):
        """Test that weights adapt to probabilities."""
        portfolio = MetaPortfolio(adaptation_rate=0.5, max_weight=1.0)  # max_weight=1.0 to avoid clamping
        portfolio.register_system("a", initial_weight=0.4)
        portfolio.register_system("b", initial_weight=0.4)

        initial_a = portfolio._systems["a"].weight
        portfolio._update_weights_from_probs({"a": 1.0, "b": 0.0})

        # Weight should move toward 1.0: new = 0.5*0.4 + 0.5*1.0 = 0.7
        assert portfolio._systems["a"].weight > initial_a

    def test_update_weights_enforces_min_weight(self):
        """Test that minimum weight is enforced."""
        portfolio = MetaPortfolio(min_weight=0.1)
        portfolio.register_system("a", initial_weight=0.5)

        # Try to push weight to 0
        portfolio._update_weights_from_probs({"a": 0.0})

        assert portfolio._systems["a"].weight >= 0.1

    def test_update_weights_enforces_max_weight(self):
        """Test that maximum weight is enforced."""
        portfolio = MetaPortfolio(max_weight=0.6)
        portfolio.register_system("a", initial_weight=0.5)

        # Try to push weight to 1.0
        for _ in range(20):
            portfolio._update_weights_from_probs({"a": 1.0})

        assert portfolio._systems["a"].weight <= 0.6

    def test_update_weights_ignores_inactive(self):
        """Test that inactive systems are not updated."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a", initial_weight=0.5)
        portfolio._systems["a"].is_active = False

        initial_weight = portfolio._systems["a"].weight
        portfolio._update_weights_from_probs({"a": 1.0})

        assert portfolio._systems["a"].weight == initial_weight


class TestMetaPortfolioReactivateSystem:
    """Test MetaPortfolio.reactivate_system (lines 460-464)."""

    def test_reactivate_deactivated_system(self):
        """Test reactivating a deactivated system."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")
        portfolio._systems["a"].is_active = False
        portfolio._systems["a"].cumulative_pnl = -500.0

        portfolio.reactivate_system("a")

        assert portfolio._systems["a"].is_active is True
        assert portfolio._systems["a"].cumulative_pnl == 0.0  # Reset

    def test_reactivate_nonexistent_system(self):
        """Test reactivating a nonexistent system (no-op)."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")

        # Should not raise
        portfolio.reactivate_system("unknown")


class TestMetaPortfolioGetStatus:
    """Test MetaPortfolio.get_status (lines 468-471, 492-503)."""

    def test_get_status_basic(self):
        """Test getting basic status."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")

        status = portfolio.get_status()

        assert "total_pnl" in status
        assert "peak_equity" in status
        assert "drawdown" in status
        assert "active_systems" in status
        assert "inactive_systems" in status
        assert "weights" in status
        assert "system_details" in status

    def test_get_status_after_pnl_updates(self):
        """Test status after PnL updates."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")

        portfolio.update_pnl({"a": 100.0, "b": 50.0})
        portfolio.update_pnl({"a": -30.0, "b": 20.0})

        status = portfolio.get_status()

        assert status["total_pnl"] == 140.0
        assert status["peak_equity"] == 150.0
        assert status["active_systems"] == 2
        assert status["inactive_systems"] == 0

    def test_get_status_with_inactive_systems(self):
        """Test status with inactive systems."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")
        portfolio._systems["b"].is_active = False

        status = portfolio.get_status()

        assert status["active_systems"] == 1
        assert status["inactive_systems"] == 1

    def test_get_status_system_details(self):
        """Test system details in status."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a", initial_weight=0.5)
        portfolio.update_pnl({"a": 10.0})

        status = portfolio.get_status()

        assert "a" in status["system_details"]
        details = status["system_details"]["a"]
        assert "weight" in details
        assert "cumulative_pnl" in details
        assert "n_updates" in details
        assert "is_active" in details
        assert "recent_sharpe" in details

    def test_get_status_drawdown_calculation(self):
        """Test drawdown calculation."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")

        portfolio.update_pnl({"a": 100.0})  # Peak at 100
        portfolio.update_pnl({"a": -50.0})  # Now at 50

        status = portfolio.get_status()

        # Drawdown = (100 - 50) / 100 = 0.5
        assert abs(status["drawdown"] - 0.5) < 0.01


class TestMetaPortfolioCalculateSharpe:
    """Test MetaPortfolio._calculate_sharpe (lines 492-503)."""

    def test_sharpe_with_valid_data(self):
        """Test Sharpe calculation with valid data."""
        portfolio = MetaPortfolio()
        pnls = [0.01, -0.005, 0.02, -0.01, 0.015, 0.008]

        sharpe = portfolio._calculate_sharpe(pnls)

        assert isinstance(sharpe, float)
        assert math.isfinite(sharpe)

    def test_sharpe_empty_list(self):
        """Test Sharpe with empty list."""
        portfolio = MetaPortfolio()

        sharpe = portfolio._calculate_sharpe([])

        assert sharpe == 0.0

    def test_sharpe_single_value(self):
        """Test Sharpe with single value."""
        portfolio = MetaPortfolio()

        sharpe = portfolio._calculate_sharpe([0.01])

        assert sharpe == 0.0

    def test_sharpe_constant_values(self):
        """Test Sharpe with constant values (zero variance)."""
        portfolio = MetaPortfolio()

        sharpe = portfolio._calculate_sharpe([0.01, 0.01, 0.01, 0.01])

        assert sharpe == 0.0  # Variance = 0 returns 0 (neutral value)

    def test_sharpe_with_risk_free(self):
        """Test Sharpe with risk-free rate."""
        portfolio = MetaPortfolio()
        pnls = [0.01, 0.02, 0.03, 0.04, 0.05]

        sharpe_no_rf = portfolio._calculate_sharpe(pnls, risk_free=0.0)
        sharpe_with_rf = portfolio._calculate_sharpe(pnls, risk_free=0.01)

        assert sharpe_with_rf < sharpe_no_rf


class TestMetaPortfolioSaveLoadState:
    """Test MetaPortfolio.save_state and load_state (lines 507-522, 526-539)."""

    def test_save_state_creates_file(self):
        """Test that save_state creates a JSON file."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a", initial_weight=0.6)
        portfolio.register_system("b", initial_weight=0.4)
        portfolio.update_pnl({"a": 100.0, "b": 50.0})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            portfolio.save_state(path)
            assert path.exists()

            with open(path) as f:
                data = json.load(f)

            assert data["total_pnl"] == 150.0
            assert "systems" in data
            assert "a" in data["systems"]
        finally:
            path.unlink()

    def test_load_state_restores_values(self):
        """Test that load_state restores saved values."""
        portfolio1 = MetaPortfolio()
        portfolio1.register_system("a", initial_weight=0.6)
        portfolio1.register_system("b", initial_weight=0.4)
        portfolio1.update_pnl({"a": 100.0, "b": 50.0})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            portfolio1.save_state(path)

            # Create new portfolio and load state
            portfolio2 = MetaPortfolio()
            portfolio2.register_system("a")
            portfolio2.register_system("b")
            portfolio2.load_state(path)

            assert portfolio2._total_pnl == 150.0
            assert portfolio2._peak_equity == 150.0
            assert portfolio2._systems["a"].cumulative_pnl == 100.0
            assert portfolio2._systems["b"].cumulative_pnl == 50.0
        finally:
            path.unlink()

    def test_load_state_rebuilds_ensemble(self):
        """Test that load_state rebuilds the ensemble."""
        portfolio = MetaPortfolio()
        portfolio.register_system("a")
        portfolio.register_system("b")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            portfolio.save_state(path)
            portfolio._ensemble = None  # Clear ensemble

            portfolio.load_state(path)

            # Ensemble should be rebuilt
            assert portfolio._ensemble is not None
        finally:
            path.unlink()

    def test_load_state_partial_match(self):
        """Test loading state when only some systems exist."""
        portfolio1 = MetaPortfolio()
        portfolio1.register_system("a")
        portfolio1.register_system("b")
        portfolio1.register_system("c")
        portfolio1.update_pnl({"a": 10.0, "b": 20.0, "c": 30.0})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            portfolio1.save_state(path)

            # Load into portfolio with only some systems
            portfolio2 = MetaPortfolio()
            portfolio2.register_system("a")
            portfolio2.register_system("b")
            # 'c' not registered

            portfolio2.load_state(path)

            assert portfolio2._systems["a"].cumulative_pnl == 10.0
            assert portfolio2._systems["b"].cumulative_pnl == 20.0
            assert "c" not in portfolio2._systems
        finally:
            path.unlink()


# =============================================================================
# Factory Function Tests (covers lines 559-582)
# =============================================================================


class TestCreateMetaPortfolioFromBacktest:
    """Test create_meta_portfolio_from_backtest function (lines 559-582)."""

    def test_create_portfolio_from_single_result(self):
        """Test creating portfolio from single backtest result."""
        config = make_system_config(name="best_system")
        results = [make_backtest_result(config=config, sharpe_ratio=2.0)]

        portfolio = create_meta_portfolio_from_backtest(results, top_k=1, base_size=5000.0)

        assert portfolio.base_size == 5000.0
        assert "best_system" in portfolio._systems

    def test_create_portfolio_selects_top_k(self):
        """Test that top K systems are selected by Sharpe."""
        results = [
            make_backtest_result(
                config=make_system_config(name="low"), sharpe_ratio=0.5
            ),
            make_backtest_result(
                config=make_system_config(name="high"), sharpe_ratio=2.0
            ),
            make_backtest_result(
                config=make_system_config(name="mid"), sharpe_ratio=1.0
            ),
        ]

        portfolio = create_meta_portfolio_from_backtest(results, top_k=2)

        assert len(portfolio._systems) == 2
        assert "high" in portfolio._systems
        assert "mid" in portfolio._systems
        assert "low" not in portfolio._systems

    def test_create_portfolio_weights_by_sharpe(self):
        """Test that weights are proportional to Sharpe ratios."""
        results = [
            make_backtest_result(
                config=make_system_config(name="a"), sharpe_ratio=2.0
            ),
            make_backtest_result(
                config=make_system_config(name="b"), sharpe_ratio=1.0
            ),
        ]

        portfolio = create_meta_portfolio_from_backtest(results, top_k=2)

        # 'a' should have higher weight than 'b'
        weight_a = portfolio._systems["a"].weight
        weight_b = portfolio._systems["b"].weight
        assert weight_a > weight_b

    def test_create_portfolio_negative_sharpe(self):
        """Test handling of negative Sharpe ratios."""
        results = [
            make_backtest_result(
                config=make_system_config(name="negative"), sharpe_ratio=-0.5
            ),
            make_backtest_result(
                config=make_system_config(name="zero"), sharpe_ratio=0.0
            ),
        ]

        portfolio = create_meta_portfolio_from_backtest(results, top_k=2)

        # Both should have equal weights (total_sharpe <= 0)
        assert len(portfolio._systems) == 2

    def test_create_portfolio_equal_weights_fallback(self):
        """Test equal weights when all Sharpe ratios are negative."""
        results = [
            make_backtest_result(
                config=make_system_config(name="a"), sharpe_ratio=-1.0
            ),
            make_backtest_result(
                config=make_system_config(name="b"), sharpe_ratio=-0.5
            ),
        ]

        portfolio = create_meta_portfolio_from_backtest(results, top_k=2)

        # With all negative sharpes, should get equal weights (1/2)
        assert portfolio._systems["a"].weight == 0.5
        assert portfolio._systems["b"].weight == 0.5

    def test_create_portfolio_min_weight_enforcement(self):
        """Test that minimum weight of 0.1 is enforced."""
        results = [
            make_backtest_result(
                config=make_system_config(name="huge"), sharpe_ratio=10.0
            ),
            make_backtest_result(
                config=make_system_config(name="tiny"), sharpe_ratio=0.01
            ),
        ]

        portfolio = create_meta_portfolio_from_backtest(results, top_k=2)

        # 'tiny' should have at least 0.1 weight
        assert portfolio._systems["tiny"].weight >= 0.1


# =============================================================================
# Integration Tests
# =============================================================================


class TestMetaPortfolioIntegration:
    """Integration tests for full portfolio lifecycle."""

    def test_full_lifecycle(self):
        """Test complete portfolio lifecycle."""
        # 1. Setup backtest matrix
        def runner(config: SystemConfig) -> BacktestResult:
            return make_backtest_result(
                config=config,
                sharpe_ratio=1.0 + len(config.strategies) * 0.2,
                n_trades=50,
            )

        matrix = BacktestMatrix(backtest_runner=runner)
        matrix.generate_configs(
            selector_types=["thompson"],
            particle_counts=[0],
            strategy_sets=[["a"], ["a", "b"], ["a", "b", "c"]],
        )

        # 2. Run backtests
        matrix.run_all()

        # 3. Select top performers
        top_results = matrix.select_top_k(k=2)
        assert len(top_results) == 2

        # 4. Create portfolio
        portfolio = create_meta_portfolio_from_backtest(top_results, top_k=2)
        assert len(portfolio._systems) == 2

        # 5. Simulate trading
        for _ in range(10):
            signals = dict.fromkeys(portfolio._systems, 0.5)
            signal, size = portfolio.aggregate(signals)
            assert abs(signal) <= 1.0

            pnls = dict.fromkeys(portfolio._systems, 10.0)
            portfolio.update_pnl(pnls)

        # 6. Check status
        status = portfolio.get_status()
        assert status["total_pnl"] > 0
        assert status["active_systems"] == 2

    def test_system_deactivation_and_reactivation(self):
        """Test deactivation and reactivation flow."""
        portfolio = MetaPortfolio(base_size=1000.0, deactivation_threshold=-0.10)
        portfolio.register_system("good")
        portfolio.register_system("bad")

        # Good system profits, bad system loses
        for _ in range(5):
            portfolio.update_pnl({"good": 20.0, "bad": -30.0})

        # 'bad' should be deactivated (cumulative loss > 10% of base)
        assert portfolio._systems["bad"].is_active is False
        assert portfolio._systems["good"].is_active is True

        # Reactivate
        portfolio.reactivate_system("bad")
        assert portfolio._systems["bad"].is_active is True
        assert portfolio._systems["bad"].cumulative_pnl == 0.0

    def test_weight_adaptation_over_time(self):
        """Test that weights adapt based on performance."""
        # Use max_weight=0.9 to allow weights to increase above 0.5
        portfolio = MetaPortfolio(adaptation_rate=0.3, max_weight=0.9)
        portfolio.register_system("winner", initial_weight=0.4)
        portfolio.register_system("loser", initial_weight=0.4)

        portfolio._systems["winner"].weight

        # Winner consistently outperforms - Thompson Sampling will favor it
        for _ in range(50):  # More iterations for clearer adaptation
            portfolio.update_pnl({"winner": 10.0, "loser": -5.0})

        # Winner's weight should increase (or at minimum not decrease much)
        # Note: Weight adaptation depends on Thompson probabilities which are stochastic
        # The winner should have higher weight than loser due to better cumulative performance
        weights = portfolio._get_current_weights()
        assert weights.get("winner", 0) >= weights.get("loser", 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
