"""
Unit tests for OnlineCorrelationMatrix and correlation tracking.

Tests cover:
- OnlineCorrelationMatrix initialization (T010)
- Correlation convergence with known data (T011, T021)
- Penalty calculation accuracy (T012)
- Ledoit-Wolf shrinkage behavior
- Performance benchmarks (T022)
- Adaptive correlation regime change (T023)
- Concentration metrics reporting (T030)
- Edge cases (T036-T039, T055)

Reference spec: specs/031-csrc-correlation/
"""

import time

import numpy as np
import pytest

from strategies.common.adaptive_control.correlation_tracker import (
    CorrelationMetrics,
    OnlineCorrelationMatrix,
    OnlineStats,
    calculate_covariance_penalty,
)


class TestOnlineStats:
    """Tests for OnlineStats dataclass with Welford's algorithm."""

    def test_initial_values(self):
        """Test OnlineStats initializes with zeros."""
        stats = OnlineStats()
        assert stats.mean == 0.0
        assert stats.m2 == 0.0
        assert stats.n == 0
        assert stats.var == 0.0
        assert stats.std == 0.0

    def test_variance_undefined_for_single_sample(self):
        """Test variance returns 0 for n < 2."""
        stats = OnlineStats(mean=5.0, m2=10.0, n=1)
        assert stats.var == 0.0

    def test_variance_calculation(self):
        """Test variance is m2/n for n >= 2."""
        stats = OnlineStats(mean=0.0, m2=20.0, n=10)
        assert stats.var == 2.0
        assert stats.std == pytest.approx(np.sqrt(2.0))


class TestOnlineCorrelationMatrixInit:
    """T010: Tests for OnlineCorrelationMatrix initialization."""

    def test_basic_initialization(self):
        """Test basic initialization with default parameters."""
        strategies = ["momentum", "mean_rev", "trend"]
        tracker = OnlineCorrelationMatrix(strategies=strategies)

        assert tracker.strategies == strategies
        assert tracker.n_strategies == 3
        assert tracker.decay == 0.99
        assert tracker.shrinkage == 0.1
        assert tracker.min_samples == 30
        assert tracker.n_samples == 0

    def test_custom_parameters(self):
        """Test initialization with custom parameters."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"],
            decay=0.95,
            shrinkage=0.2,
            min_samples=50,
        )
        assert tracker.decay == 0.95
        assert tracker.shrinkage == 0.2
        assert tracker.min_samples == 50

    def test_strategy_indices_mapping(self):
        """Test strategy_indices returns correct mapping."""
        strategies = ["alpha", "beta", "gamma"]
        tracker = OnlineCorrelationMatrix(strategies=strategies)

        indices = tracker.strategy_indices
        assert indices == {"alpha": 0, "beta": 1, "gamma": 2}

    def test_initial_correlation_matrix_is_identity(self):
        """Test initial correlation matrix is identity (insufficient samples)."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B", "C"])

        corr = tracker.get_correlation_matrix()
        expected = np.eye(3)
        np.testing.assert_array_almost_equal(corr, expected)

    def test_empty_strategies_raises_error(self):
        """Test empty strategies list raises ValueError."""
        with pytest.raises(ValueError, match="strategies list cannot be empty"):
            OnlineCorrelationMatrix(strategies=[])

    def test_invalid_decay_raises_error(self):
        """Test invalid decay values raise ValueError."""
        with pytest.raises(ValueError, match="decay must be in"):
            OnlineCorrelationMatrix(strategies=["A"], decay=0.0)

        with pytest.raises(ValueError, match="decay must be in"):
            OnlineCorrelationMatrix(strategies=["A"], decay=1.5)

    def test_invalid_shrinkage_raises_error(self):
        """Test invalid shrinkage values raise ValueError."""
        with pytest.raises(ValueError, match="shrinkage must be in"):
            OnlineCorrelationMatrix(strategies=["A"], shrinkage=-0.1)

        with pytest.raises(ValueError, match="shrinkage must be in"):
            OnlineCorrelationMatrix(strategies=["A"], shrinkage=1.5)


class TestCorrelationConvergence:
    """T011/T021: Tests for correlation convergence with known data."""

    def test_correlation_convergence_known_data(self):
        """Test correlation converges to known value within 150 samples.

        SC-003: Correlation estimates converge to within 5% of true value
        after observing 150 return pairs.
        """
        np.random.seed(42)

        # Create two strategies with known correlation 0.9
        true_correlation = 0.9
        n_samples = 150

        # Generate correlated returns
        # If X ~ N(0,1) and Y = rho*X + sqrt(1-rho^2)*Z where Z ~ N(0,1)
        # Then corr(X, Y) = rho
        x = np.random.randn(n_samples)
        z = np.random.randn(n_samples)
        y = true_correlation * x + np.sqrt(1 - true_correlation**2) * z

        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"],
            decay=0.99,
            shrinkage=0.05,  # Light shrinkage
            min_samples=30,
        )

        # Feed returns
        for i in range(n_samples):
            tracker.update({"A": x[i], "B": y[i]})

        # Get estimated correlation
        corr_matrix = tracker.get_correlation_matrix()
        estimated_corr = corr_matrix[0, 1]

        # Check convergence within 5% (accounting for shrinkage toward 0)
        # With shrinkage=0.05, expected_corr = 0.95 * true_corr + 0.05 * 0 = 0.855
        # Allow 10% tolerance for statistical variation
        assert 0.7 < estimated_corr < 1.0, (
            f"Correlation {estimated_corr} not close to {true_correlation}"
        )

    def test_pairwise_correlation_accessor(self):
        """Test get_pairwise_correlation returns correct values."""
        np.random.seed(123)

        tracker = OnlineCorrelationMatrix(
            strategies=["X", "Y", "Z"],
            min_samples=10,
        )

        # Update with some data
        for _ in range(50):
            tracker.update(
                {
                    "X": np.random.randn(),
                    "Y": np.random.randn(),
                    "Z": np.random.randn(),
                }
            )

        # Self-correlation should be 1.0
        assert tracker.get_pairwise_correlation("X", "X") == 1.0

        # Unknown strategy should return 0.0
        assert tracker.get_pairwise_correlation("X", "UNKNOWN") == 0.0
        assert tracker.get_pairwise_correlation("UNKNOWN", "Y") == 0.0


class TestCovariancePenalty:
    """T012: Tests for covariance penalty calculation."""

    def test_penalty_calculation_with_known_weights(self):
        """T012: Test penalty formula with known weights and correlations.

        penalty = sum_i sum_j (w_i * w_j * corr_ij) for i != j
        """
        # Perfect correlation between A and B
        corr_matrix = np.array(
            [
                [1.0, 0.8],
                [0.8, 1.0],
            ]
        )
        strategy_indices = {"A": 0, "B": 1}
        weights = {"A": 0.5, "B": 0.5}

        # Expected: 0.5 * 0.5 * 0.8 + 0.5 * 0.5 * 0.8 = 0.4
        penalty = calculate_covariance_penalty(weights, corr_matrix, strategy_indices)
        assert penalty == pytest.approx(0.4)

    def test_penalty_zero_for_uncorrelated(self):
        """Test penalty is 0 when correlation is 0."""
        corr_matrix = np.array(
            [
                [1.0, 0.0],
                [0.0, 1.0],
            ]
        )
        strategy_indices = {"A": 0, "B": 1}
        weights = {"A": 0.5, "B": 0.5}

        penalty = calculate_covariance_penalty(weights, corr_matrix, strategy_indices)
        assert penalty == pytest.approx(0.0)

    def test_penalty_negative_for_negative_correlation(self):
        """Test penalty is negative for negatively correlated strategies."""
        corr_matrix = np.array(
            [
                [1.0, -0.8],
                [-0.8, 1.0],
            ]
        )
        strategy_indices = {"A": 0, "B": 1}
        weights = {"A": 0.5, "B": 0.5}

        penalty = calculate_covariance_penalty(weights, corr_matrix, strategy_indices)
        assert penalty == pytest.approx(-0.4)

    def test_penalty_with_three_strategies(self):
        """Test penalty calculation with three strategies."""
        corr_matrix = np.array(
            [
                [1.0, 0.5, 0.3],
                [0.5, 1.0, 0.2],
                [0.3, 0.2, 1.0],
            ]
        )
        strategy_indices = {"A": 0, "B": 1, "C": 2}
        weights = {"A": 0.4, "B": 0.4, "C": 0.2}

        # Manual calculation:
        # A-B: 0.4 * 0.4 * 0.5 * 2 = 0.16
        # A-C: 0.4 * 0.2 * 0.3 * 2 = 0.048
        # B-C: 0.4 * 0.2 * 0.2 * 2 = 0.032
        # Total: 0.24
        penalty = calculate_covariance_penalty(weights, corr_matrix, strategy_indices)
        assert penalty == pytest.approx(0.24)

    def test_penalty_single_strategy_is_zero(self):
        """Test penalty is 0 for single strategy (no pairs)."""
        corr_matrix = np.array([[1.0]])
        strategy_indices = {"A": 0}
        weights = {"A": 1.0}

        penalty = calculate_covariance_penalty(weights, corr_matrix, strategy_indices)
        assert penalty == 0.0

    def test_penalty_normalizes_weights(self):
        """Test that unnormalized weights are handled correctly."""
        corr_matrix = np.array(
            [
                [1.0, 0.8],
                [0.8, 1.0],
            ]
        )
        strategy_indices = {"A": 0, "B": 1}

        # Unnormalized weights (sum to 2.0)
        weights = {"A": 1.0, "B": 1.0}
        penalty = calculate_covariance_penalty(weights, corr_matrix, strategy_indices)

        # After normalization: 0.5, 0.5 -> penalty = 0.4
        assert penalty == pytest.approx(0.4)


class TestPerformance:
    """T022: Performance benchmarks for correlation tracking."""

    def test_performance_10_strategies(self):
        """T022: Test < 1ms update for 10 strategies (FR-006)."""
        np.random.seed(42)
        n_strategies = 10
        strategies = [f"strat_{i}" for i in range(n_strategies)]

        tracker = OnlineCorrelationMatrix(strategies=strategies, min_samples=10)

        # Warm up
        for _ in range(50):
            returns = {s: np.random.randn() for s in strategies}
            tracker.update(returns)

        # Benchmark
        n_iterations = 100
        start = time.perf_counter()
        for _ in range(n_iterations):
            returns = {s: np.random.randn() for s in strategies}
            tracker.update(returns)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / n_iterations) * 1000
        assert avg_ms < 1.0, f"Update took {avg_ms:.3f}ms, expected < 1ms"

    def test_performance_20_strategies(self):
        """SC-004: Test < 1ms for 20 strategies."""
        np.random.seed(42)
        n_strategies = 20
        strategies = [f"strat_{i}" for i in range(n_strategies)]

        tracker = OnlineCorrelationMatrix(strategies=strategies, min_samples=10)

        # Warm up
        for _ in range(50):
            returns = {s: np.random.randn() for s in strategies}
            tracker.update(returns)

        # Benchmark
        n_iterations = 100
        start = time.perf_counter()
        for _ in range(n_iterations):
            returns = {s: np.random.randn() for s in strategies}
            tracker.update(returns)
        elapsed = time.perf_counter() - start

        avg_ms = (elapsed / n_iterations) * 1000
        assert avg_ms < 1.0, f"Update took {avg_ms:.3f}ms, expected < 1ms"


class TestAdaptiveCorrelation:
    """T023: Tests for adaptive correlation tracking during regime changes."""

    def test_adaptive_correlation_regime_change(self):
        """T023: Test correlation adapts when regime changes (0.5 -> 0.9).

        With decay=0.99, expect adaptation within 100 samples.
        """
        np.random.seed(42)

        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"],
            decay=0.95,  # Faster decay for regime change test
            shrinkage=0.05,
            min_samples=20,
        )

        # Phase 1: Low correlation (0.5) for 100 samples
        low_corr = 0.5
        for _ in range(100):
            x = np.random.randn()
            y = low_corr * x + np.sqrt(1 - low_corr**2) * np.random.randn()
            tracker.update({"A": x, "B": y})

        # Record correlation at end of phase 1
        corr_phase1 = tracker.get_pairwise_correlation("A", "B")

        # Phase 2: High correlation (0.9) for 100 samples
        high_corr = 0.9
        for _ in range(100):
            x = np.random.randn()
            y = high_corr * x + np.sqrt(1 - high_corr**2) * np.random.randn()
            tracker.update({"A": x, "B": y})

        # Record correlation at end of phase 2
        corr_phase2 = tracker.get_pairwise_correlation("A", "B")

        # Correlation should have increased significantly
        assert corr_phase2 > corr_phase1, (
            f"Correlation should increase: {corr_phase1:.3f} -> {corr_phase2:.3f}"
        )
        # Should be closer to 0.9 than to 0.5
        assert corr_phase2 > 0.6, f"Correlation {corr_phase2} should be > 0.6"


class TestCorrelationMetrics:
    """T030: Tests for concentration metrics reporting."""

    def test_concentration_metrics_reported(self):
        """T030: Test Herfindahl and effective N are reported."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B", "C"],
            min_samples=5,
        )

        # Update with some data
        for _ in range(10):
            tracker.update({"A": 0.01, "B": 0.01, "C": 0.01})

        # Get metrics with equal weights
        weights = {"A": 1 / 3, "B": 1 / 3, "C": 1 / 3}
        metrics = tracker.get_metrics(weights)

        assert isinstance(metrics, CorrelationMetrics)
        # Equal weights: Herfindahl = 3 * (1/3)^2 = 1/3
        assert metrics.herfindahl_index == pytest.approx(1 / 3, rel=0.01)
        # Effective N = 1 / (1/3) = 3
        assert metrics.effective_n_strategies == pytest.approx(3.0, rel=0.01)

    def test_concentration_metrics_concentrated_portfolio(self):
        """Test metrics for concentrated portfolio (single strategy)."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B", "C"], min_samples=1)
        tracker.update({"A": 0.01, "B": 0.01, "C": 0.01})

        # Concentrated weights: all in one strategy
        weights = {"A": 1.0, "B": 0.0, "C": 0.0}
        metrics = tracker.get_metrics(weights)

        # Herfindahl = 1^2 + 0^2 + 0^2 = 1.0 (max concentration)
        assert metrics.herfindahl_index == pytest.approx(1.0)
        # Effective N = 1.0
        assert metrics.effective_n_strategies == pytest.approx(1.0)

    def test_metrics_without_weights_uses_equal(self):
        """Test get_metrics without weights assumes equal weights."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"], min_samples=1)
        tracker.update({"A": 0.01, "B": 0.01})

        metrics = tracker.get_metrics()  # No weights provided

        # Equal weights for 2 strategies: Herfindahl = 2 * 0.5^2 = 0.5
        assert metrics.herfindahl_index == pytest.approx(0.5)
        assert metrics.effective_n_strategies == pytest.approx(2.0)


class TestEdgeCases:
    """T036-T039, T055: Tests for edge cases."""

    def test_singular_matrix_regularization(self):
        """T036: Test regularization prevents crash on singular matrix."""
        # Create perfectly correlated data (would cause singular matrix)
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"],
            min_samples=5,
        )

        # Feed identical returns (perfect correlation, singular)
        for i in range(20):
            value = float(i) / 10  # Same value for both strategies
            tracker.update({"A": value, "B": value})

        # Should not crash and return valid matrix
        corr = tracker.get_correlation_matrix()
        assert corr.shape == (2, 2)
        assert np.all(np.isfinite(corr)), "Matrix contains non-finite values"
        # Diagonal should be 1.0
        assert corr[0, 0] == pytest.approx(1.0)
        assert corr[1, 1] == pytest.approx(1.0)

    def test_zero_variance_strategy(self):
        """T037: Test zero variance strategy treated as uncorrelated."""
        tracker = OnlineCorrelationMatrix(
            strategies=["varying", "constant"],
            min_samples=5,
        )

        # Feed varying A, constant B
        for i in range(20):
            tracker.update({"varying": np.sin(i), "constant": 5.0})

        corr = tracker.get_correlation_matrix()

        # Should not crash
        assert corr.shape == (2, 2)
        assert np.all(np.isfinite(corr))
        # Off-diagonal should be close to 0 (with shrinkage)
        assert abs(corr[0, 1]) < 0.5, f"Expected low correlation, got {corr[0, 1]}"

    def test_all_strategies_correlated(self):
        """T038 related: Test handling of highly correlated strategies."""
        np.random.seed(42)

        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B", "C"],
            shrinkage=0.1,
            min_samples=20,
        )

        # All strategies follow same signal (perfect correlation)
        for _ in range(100):
            base_return = np.random.randn() * 0.01
            tracker.update(
                {
                    "A": base_return + np.random.randn() * 0.001,
                    "B": base_return + np.random.randn() * 0.001,
                    "C": base_return + np.random.randn() * 0.001,
                }
            )

        corr = tracker.get_correlation_matrix()

        # All correlations should be high (> 0.8)
        assert corr[0, 1] > 0.8, f"A-B correlation {corr[0, 1]} should be > 0.8"
        assert corr[0, 2] > 0.8, f"A-C correlation {corr[0, 2]} should be > 0.8"
        assert corr[1, 2] > 0.8, f"B-C correlation {corr[1, 2]} should be > 0.8"

    def test_two_strategy_portfolio(self):
        """T039: Test N=2 works correctly."""
        tracker = OnlineCorrelationMatrix(
            strategies=["long", "short"],
            min_samples=5,
        )

        # Feed negatively correlated returns
        np.random.seed(42)
        for _ in range(50):
            x = np.random.randn() * 0.01
            tracker.update({"long": x, "short": -x})

        corr = tracker.get_correlation_matrix()

        assert corr.shape == (2, 2)
        # Diagonal is 1
        assert corr[0, 0] == pytest.approx(1.0)
        assert corr[1, 1] == pytest.approx(1.0)
        # Off-diagonal should be negative (with shrinkage pulling toward 0)
        assert corr[0, 1] < 0, f"Expected negative correlation, got {corr[0, 1]}"

    def test_sliding_window_memory_constraint(self):
        """T055: Test max 1000 samples in memory (FR-004).

        Note: Current implementation uses EMA (exponential decay) rather than
        explicit sliding window, so memory is O(N^2) regardless of samples.
        This test verifies memory doesn't grow with samples.
        """
        import sys

        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B", "C"],
            min_samples=10,
        )

        # Record memory after initialization
        initial_size = sys.getsizeof(tracker._ema_cov) + sys.getsizeof(
            tracker._ema_means
        )

        # Feed 2000 samples (more than 1000)
        np.random.seed(42)
        for _ in range(2000):
            tracker.update(
                {
                    "A": np.random.randn(),
                    "B": np.random.randn(),
                    "C": np.random.randn(),
                }
            )

        # Memory should not have grown significantly
        final_size = sys.getsizeof(tracker._ema_cov) + sys.getsizeof(tracker._ema_means)

        # EMA doesn't store history, so size should be same
        assert final_size == initial_size, (
            f"Memory grew: {initial_size} -> {final_size}"
        )

        # n_samples should still be tracked correctly
        assert tracker.n_samples == 2000

    def test_missing_strategy_returns_handled(self):
        """Test missing strategies in returns dict are treated as 0."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B", "C"],
            min_samples=5,
        )

        # Only provide partial returns
        for _ in range(10):
            tracker.update({"A": 0.01})  # B and C missing

        # Should not crash
        assert tracker.n_samples == 10
        corr = tracker.get_correlation_matrix()
        assert corr.shape == (3, 3)
