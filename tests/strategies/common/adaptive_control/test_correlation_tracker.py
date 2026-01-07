"""Comprehensive tests for CorrelationTracker module.

Coverage targets:
- OnlineStats: var, std properties (lines 90-92, 97)
- OnlineCorrelationMatrix: initialization, update, correlation methods
- CorrelationMetrics: portfolio metrics calculation
- calculate_covariance_penalty: penalty function

Test categories:
1. Unit tests for each class/function
2. Edge cases: empty data, single asset, extreme correlations
3. Numerical accuracy tests
4. Rolling window behavior tests
"""

import math

import numpy as np
import pytest

from strategies.common.adaptive_control.correlation_tracker import (
    CorrelationMetrics,
    OnlineCorrelationMatrix,
    OnlineStats,
    calculate_covariance_penalty,
)


# =============================================================================
# OnlineStats Tests
# =============================================================================


class TestOnlineStats:
    """Test OnlineStats dataclass and properties."""

    def test_default_initialization(self):
        """Test default OnlineStats values."""
        stats = OnlineStats()
        assert stats.mean == 0.0
        assert stats.m2 == 0.0
        assert stats.n == 0

    def test_var_with_no_samples(self):
        """Test variance with zero samples returns 0.0."""
        stats = OnlineStats(mean=0.0, m2=0.0, n=0)
        assert stats.var == 0.0

    def test_var_with_one_sample(self):
        """Test variance with one sample returns 0.0."""
        stats = OnlineStats(mean=5.0, m2=0.0, n=1)
        assert stats.var == 0.0

    def test_var_with_two_samples(self):
        """Test variance with two samples."""
        # For values [1, 3], mean=2, m2=2
        # var = m2/n = 2/2 = 1.0
        stats = OnlineStats(mean=2.0, m2=2.0, n=2)
        assert stats.var == 1.0

    def test_var_calculation(self):
        """Test variance calculation correctness."""
        # For values [1, 2, 3, 4, 5], mean=3, population var=2.0
        # m2 = sum((x-mean)^2) = 4+1+0+1+4 = 10
        stats = OnlineStats(mean=3.0, m2=10.0, n=5)
        assert stats.var == 2.0

    def test_std_with_no_samples(self):
        """Test standard deviation with zero samples returns 0.0."""
        stats = OnlineStats(mean=0.0, m2=0.0, n=0)
        assert stats.std == 0.0

    def test_std_with_one_sample(self):
        """Test standard deviation with one sample returns 0.0."""
        stats = OnlineStats(mean=5.0, m2=0.0, n=1)
        assert stats.std == 0.0

    def test_std_calculation(self):
        """Test standard deviation calculation correctness."""
        # var = 4.0, std = 2.0
        stats = OnlineStats(mean=0.0, m2=16.0, n=4)
        assert stats.std == 2.0

    def test_std_is_sqrt_of_var(self):
        """Test std is square root of var."""
        stats = OnlineStats(mean=0.0, m2=50.0, n=10)
        assert stats.std == math.sqrt(stats.var)


# =============================================================================
# CorrelationMetrics Tests
# =============================================================================


class TestCorrelationMetrics:
    """Test CorrelationMetrics dataclass."""

    def test_default_initialization(self):
        """Test default CorrelationMetrics values."""
        metrics = CorrelationMetrics()
        assert metrics.herfindahl_index == 0.0
        assert metrics.effective_n_strategies == 0.0
        assert metrics.max_pairwise_correlation == 0.0
        assert metrics.avg_correlation == 0.0

    def test_custom_initialization(self):
        """Test custom CorrelationMetrics values."""
        metrics = CorrelationMetrics(
            herfindahl_index=0.25,
            effective_n_strategies=4.0,
            max_pairwise_correlation=0.8,
            avg_correlation=0.3,
        )
        assert metrics.herfindahl_index == 0.25
        assert metrics.effective_n_strategies == 4.0
        assert metrics.max_pairwise_correlation == 0.8
        assert metrics.avg_correlation == 0.3


# =============================================================================
# OnlineCorrelationMatrix Initialization Tests
# =============================================================================


class TestOnlineCorrelationMatrixInit:
    """Test OnlineCorrelationMatrix initialization and validation."""

    def test_valid_initialization(self):
        """Test valid initialization."""
        strategies = ["A", "B", "C"]
        tracker = OnlineCorrelationMatrix(strategies=strategies)

        assert tracker.strategies == strategies
        assert tracker.n_strategies == 3
        assert tracker.decay == 0.99
        assert tracker.shrinkage == 0.1
        assert tracker.min_samples == 30
        assert tracker.epsilon == 1e-6
        assert tracker.n_samples == 0

    def test_custom_parameters(self):
        """Test initialization with custom parameters."""
        tracker = OnlineCorrelationMatrix(
            strategies=["X", "Y"],
            decay=0.95,
            shrinkage=0.2,
            min_samples=50,
            epsilon=1e-8,
        )
        assert tracker.decay == 0.95
        assert tracker.shrinkage == 0.2
        assert tracker.min_samples == 50
        assert tracker.epsilon == 1e-8

    def test_empty_strategies_raises_error(self):
        """Test empty strategies list raises ValueError."""
        with pytest.raises(ValueError, match="strategies list cannot be empty"):
            OnlineCorrelationMatrix(strategies=[])

    def test_decay_zero_raises_error(self):
        """Test decay=0 raises ValueError."""
        with pytest.raises(ValueError, match="decay must be in"):
            OnlineCorrelationMatrix(strategies=["A"], decay=0.0)

    def test_decay_negative_raises_error(self):
        """Test negative decay raises ValueError."""
        with pytest.raises(ValueError, match="decay must be in"):
            OnlineCorrelationMatrix(strategies=["A"], decay=-0.5)

    def test_decay_greater_than_one_raises_error(self):
        """Test decay > 1 raises ValueError."""
        with pytest.raises(ValueError, match="decay must be in"):
            OnlineCorrelationMatrix(strategies=["A"], decay=1.5)

    def test_decay_one_is_valid(self):
        """Test decay=1.0 is valid (no decay)."""
        tracker = OnlineCorrelationMatrix(strategies=["A"], decay=1.0)
        assert tracker.decay == 1.0

    def test_shrinkage_negative_raises_error(self):
        """Test negative shrinkage raises ValueError."""
        with pytest.raises(ValueError, match="shrinkage must be in"):
            OnlineCorrelationMatrix(strategies=["A"], shrinkage=-0.1)

    def test_shrinkage_greater_than_one_raises_error(self):
        """Test shrinkage > 1 raises ValueError."""
        with pytest.raises(ValueError, match="shrinkage must be in"):
            OnlineCorrelationMatrix(strategies=["A"], shrinkage=1.5)

    def test_shrinkage_zero_is_valid(self):
        """Test shrinkage=0 is valid (no shrinkage)."""
        tracker = OnlineCorrelationMatrix(strategies=["A"], shrinkage=0.0)
        assert tracker.shrinkage == 0.0

    def test_shrinkage_one_is_valid(self):
        """Test shrinkage=1.0 is valid (full shrinkage)."""
        tracker = OnlineCorrelationMatrix(strategies=["A"], shrinkage=1.0)
        assert tracker.shrinkage == 1.0

    def test_min_samples_zero_raises_error(self):
        """Test min_samples=0 raises ValueError."""
        with pytest.raises(ValueError, match="min_samples must be >= 1"):
            OnlineCorrelationMatrix(strategies=["A"], min_samples=0)

    def test_min_samples_negative_raises_error(self):
        """Test negative min_samples raises ValueError."""
        with pytest.raises(ValueError, match="min_samples must be >= 1"):
            OnlineCorrelationMatrix(strategies=["A"], min_samples=-5)

    def test_epsilon_zero_raises_error(self):
        """Test epsilon=0 raises ValueError."""
        with pytest.raises(ValueError, match="epsilon must be > 0"):
            OnlineCorrelationMatrix(strategies=["A"], epsilon=0.0)

    def test_epsilon_negative_raises_error(self):
        """Test negative epsilon raises ValueError."""
        with pytest.raises(ValueError, match="epsilon must be > 0"):
            OnlineCorrelationMatrix(strategies=["A"], epsilon=-1e-6)

    def test_strategy_indices_mapping(self):
        """Test strategy_indices property returns correct mapping."""
        strategies = ["alpha", "beta", "gamma"]
        tracker = OnlineCorrelationMatrix(strategies=strategies)

        indices = tracker.strategy_indices
        assert indices == {"alpha": 0, "beta": 1, "gamma": 2}

    def test_strategy_indices_is_copy(self):
        """Test strategy_indices returns a copy."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"])
        indices1 = tracker.strategy_indices
        indices2 = tracker.strategy_indices

        # Should be equal but not same object
        assert indices1 == indices2
        assert indices1 is not indices2

        # Modifying returned copy should not affect internal state
        indices1["C"] = 99
        assert "C" not in tracker.strategy_indices


# =============================================================================
# OnlineCorrelationMatrix Update Tests
# =============================================================================


class TestOnlineCorrelationMatrixUpdate:
    """Test OnlineCorrelationMatrix update method."""

    def test_first_update_initializes(self):
        """Test first update initializes EMA values."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"])

        tracker.update({"A": 0.01, "B": 0.02})

        assert tracker.n_samples == 1
        np.testing.assert_array_almost_equal(
            tracker._ema_means, np.array([0.01, 0.02])
        )

    def test_missing_strategy_uses_zero(self):
        """Test missing strategy in returns uses 0.0."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B", "C"])

        tracker.update({"A": 0.05})  # B and C missing

        assert tracker.n_samples == 1
        # B and C should be 0.0
        assert tracker._ema_means[1] == 0.0
        assert tracker._ema_means[2] == 0.0

    def test_sample_counter_increments(self):
        """Test n_samples increments with each update."""
        tracker = OnlineCorrelationMatrix(strategies=["A"])

        for i in range(10):
            tracker.update({"A": 0.01 * i})
            assert tracker.n_samples == i + 1

    def test_welford_stats_update(self):
        """Test Welford statistics are updated correctly."""
        tracker = OnlineCorrelationMatrix(strategies=["A"])

        values = [2.0, 4.0, 6.0]
        for v in values:
            tracker.update({"A": v})

        # Mean should be 4.0
        assert tracker._stats[0].n == 3
        assert abs(tracker._stats[0].mean - 4.0) < 1e-10

    def test_ema_update_formula(self):
        """Test EMA update follows correct formula."""
        decay = 0.9
        tracker = OnlineCorrelationMatrix(strategies=["A"], decay=decay)

        tracker.update({"A": 1.0})
        tracker.update({"A": 2.0})

        # After second update:
        # ema_mean = 0.9 * 1.0 + 0.1 * 2.0 = 1.1
        expected_mean = decay * 1.0 + (1 - decay) * 2.0
        assert abs(tracker._ema_means[0] - expected_mean) < 1e-10

    def test_multiple_strategies_update(self):
        """Test update with multiple strategies."""
        tracker = OnlineCorrelationMatrix(
            strategies=["mom", "rev", "trend"], min_samples=1
        )

        # Feed correlated returns
        for _ in range(50):
            tracker.update({"mom": 0.01, "rev": -0.01, "trend": 0.01})

        assert tracker.n_samples == 50


# =============================================================================
# OnlineCorrelationMatrix Correlation Matrix Tests
# =============================================================================


class TestGetCorrelationMatrix:
    """Test get_correlation_matrix method."""

    def test_returns_identity_before_min_samples(self):
        """Test returns identity matrix before min_samples reached."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"], min_samples=30)

        for _ in range(10):
            tracker.update({"A": 0.01, "B": 0.02})

        corr = tracker.get_correlation_matrix()
        expected = np.eye(2)
        np.testing.assert_array_almost_equal(corr, expected)

    def test_returns_identity_at_min_samples_minus_one(self):
        """Test returns identity at exactly min_samples - 1."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"], min_samples=30)

        for _ in range(29):
            tracker.update({"A": 0.01, "B": 0.02})

        corr = tracker.get_correlation_matrix()
        expected = np.eye(2)
        np.testing.assert_array_almost_equal(corr, expected)

    def test_computes_correlation_at_min_samples(self):
        """Test computes correlation at exactly min_samples."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=30, shrinkage=0.0
        )

        np.random.seed(42)
        for _ in range(30):
            r = np.random.normal(0, 0.01)
            tracker.update({"A": r, "B": r})  # Perfectly correlated

        corr = tracker.get_correlation_matrix()
        # Diagonal should be 1.0
        assert abs(corr[0, 0] - 1.0) < 1e-6
        assert abs(corr[1, 1] - 1.0) < 1e-6

    def test_diagonal_is_one(self):
        """Test diagonal is always 1.0."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B", "C"], min_samples=10
        )

        np.random.seed(42)
        for _ in range(20):
            tracker.update({
                "A": np.random.normal(0, 0.01),
                "B": np.random.normal(0, 0.02),
                "C": np.random.normal(0, 0.03),
            })

        corr = tracker.get_correlation_matrix()
        for i in range(3):
            assert abs(corr[i, i] - 1.0) < 1e-10

    def test_symmetric_matrix(self):
        """Test correlation matrix is symmetric."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B", "C"], min_samples=10
        )

        np.random.seed(42)
        for _ in range(20):
            tracker.update({
                "A": np.random.normal(0, 0.01),
                "B": np.random.normal(0, 0.02),
                "C": np.random.normal(0, 0.03),
            })

        corr = tracker.get_correlation_matrix()
        np.testing.assert_array_almost_equal(corr, corr.T)

    def test_values_in_valid_range(self):
        """Test all correlation values are in [-1, 1]."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B", "C"], min_samples=10
        )

        np.random.seed(42)
        for _ in range(50):
            tracker.update({
                "A": np.random.normal(0, 0.01),
                "B": np.random.normal(0, 0.02),
                "C": np.random.normal(0, 0.03),
            })

        corr = tracker.get_correlation_matrix()
        assert np.all(corr >= -1.0)
        assert np.all(corr <= 1.0)

    def test_positive_correlation_detected(self):
        """Test positive correlation is detected."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5, shrinkage=0.0
        )

        np.random.seed(42)
        for _ in range(50):
            r = np.random.normal(0, 0.01)
            tracker.update({"A": r, "B": r + np.random.normal(0, 0.001)})

        corr = tracker.get_correlation_matrix()
        assert corr[0, 1] > 0.8  # High positive correlation

    def test_negative_correlation_detected(self):
        """Test negative correlation is detected."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5, shrinkage=0.0
        )

        np.random.seed(42)
        for _ in range(50):
            r = np.random.normal(0, 0.01)
            tracker.update({"A": r, "B": -r + np.random.normal(0, 0.001)})

        corr = tracker.get_correlation_matrix()
        assert corr[0, 1] < -0.8  # High negative correlation

    def test_zero_variance_handled(self):
        """Test zero variance strategy is handled gracefully."""
        tracker = OnlineCorrelationMatrix(
            strategies=["constant", "variable"], min_samples=5
        )

        for _ in range(10):
            tracker.update({"constant": 0.0, "variable": np.random.normal(0, 0.01)})

        # Should not raise, should handle zero variance
        corr = tracker.get_correlation_matrix()
        assert corr.shape == (2, 2)
        assert abs(corr[0, 0] - 1.0) < 1e-10
        assert abs(corr[1, 1] - 1.0) < 1e-10


# =============================================================================
# Shrinkage Tests
# =============================================================================


class TestApplyShrinkage:
    """Test _apply_shrinkage method."""

    def test_no_shrinkage(self):
        """Test shrinkage=0 leaves matrix unchanged (except regularization)."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], shrinkage=0.0, min_samples=5
        )

        np.random.seed(42)
        for _ in range(20):
            r = np.random.normal(0, 0.01)
            tracker.update({"A": r, "B": r})

        corr = tracker.get_correlation_matrix()
        # With shrinkage=0, off-diagonal should be high
        assert corr[0, 1] > 0.9

    def test_full_shrinkage(self):
        """Test shrinkage=1.0 returns near-identity matrix."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], shrinkage=1.0, min_samples=5
        )

        np.random.seed(42)
        for _ in range(20):
            r = np.random.normal(0, 0.01)
            tracker.update({"A": r, "B": r})

        corr = tracker.get_correlation_matrix()
        # With full shrinkage, off-diagonal should be near zero
        assert abs(corr[0, 1]) < 0.01

    def test_partial_shrinkage(self):
        """Test partial shrinkage reduces correlation estimates."""
        tracker_no_shrink = OnlineCorrelationMatrix(
            strategies=["A", "B"], shrinkage=0.0, min_samples=5
        )
        tracker_shrink = OnlineCorrelationMatrix(
            strategies=["A", "B"], shrinkage=0.5, min_samples=5
        )

        np.random.seed(42)
        for _ in range(20):
            r = np.random.normal(0, 0.01)
            tracker_no_shrink.update({"A": r, "B": r})

        np.random.seed(42)
        for _ in range(20):
            r = np.random.normal(0, 0.01)
            tracker_shrink.update({"A": r, "B": r})

        corr_no = tracker_no_shrink.get_correlation_matrix()
        corr_yes = tracker_shrink.get_correlation_matrix()

        # Shrunk off-diagonal should be smaller
        assert abs(corr_yes[0, 1]) < abs(corr_no[0, 1])


# =============================================================================
# Pairwise Correlation Tests
# =============================================================================


class TestGetPairwiseCorrelation:
    """Test get_pairwise_correlation method."""

    def test_self_correlation_is_one(self):
        """Test self-correlation returns 1.0."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"])
        tracker.update({"A": 0.01, "B": 0.02})

        assert tracker.get_pairwise_correlation("A", "A") == 1.0
        assert tracker.get_pairwise_correlation("B", "B") == 1.0

    def test_unknown_strategy_returns_zero(self):
        """Test unknown strategy returns 0.0."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"])
        tracker.update({"A": 0.01, "B": 0.02})

        assert tracker.get_pairwise_correlation("A", "UNKNOWN") == 0.0
        assert tracker.get_pairwise_correlation("UNKNOWN", "B") == 0.0
        assert tracker.get_pairwise_correlation("X", "Y") == 0.0

    def test_pairwise_matches_matrix(self):
        """Test pairwise correlation matches matrix value."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B", "C"], min_samples=5
        )

        np.random.seed(42)
        for _ in range(20):
            tracker.update({
                "A": np.random.normal(0, 0.01),
                "B": np.random.normal(0, 0.02),
                "C": np.random.normal(0, 0.03),
            })

        corr = tracker.get_correlation_matrix()
        assert tracker.get_pairwise_correlation("A", "B") == corr[0, 1]
        assert tracker.get_pairwise_correlation("B", "C") == corr[1, 2]
        assert tracker.get_pairwise_correlation("A", "C") == corr[0, 2]

    def test_symmetric_pairwise(self):
        """Test pairwise correlation is symmetric."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5
        )

        np.random.seed(42)
        for _ in range(20):
            tracker.update({
                "A": np.random.normal(0, 0.01),
                "B": np.random.normal(0, 0.02),
            })

        assert tracker.get_pairwise_correlation("A", "B") == tracker.get_pairwise_correlation("B", "A")


# =============================================================================
# Metrics Tests
# =============================================================================


class TestGetMetrics:
    """Test get_metrics method."""

    def test_equal_weights_herfindahl(self):
        """Test Herfindahl with equal weights."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B", "C", "D"])

        metrics = tracker.get_metrics()

        # Equal weights: 1/4 = 0.25
        assert metrics.herfindahl_index == 0.25
        assert metrics.effective_n_strategies == 4.0

    def test_custom_weights_herfindahl(self):
        """Test Herfindahl with custom weights."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"])

        # Concentrated in A
        metrics = tracker.get_metrics({"A": 0.9, "B": 0.1})

        # HHI = 0.9^2 + 0.1^2 = 0.81 + 0.01 = 0.82
        expected_hhi = 0.9**2 + 0.1**2
        assert abs(metrics.herfindahl_index - expected_hhi) < 1e-10

    def test_weights_normalized(self):
        """Test weights are normalized if they don't sum to 1."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"])

        # Weights sum to 2.0
        metrics = tracker.get_metrics({"A": 1.0, "B": 1.0})

        # After normalization: [0.5, 0.5]
        # HHI = 0.5^2 + 0.5^2 = 0.5
        assert abs(metrics.herfindahl_index - 0.5) < 1e-10

    def test_zero_total_weight_uses_equal(self):
        """Test zero total weight uses equal weights."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B"])

        metrics = tracker.get_metrics({"A": 0.0, "B": 0.0})

        # Falls back to equal weights
        assert metrics.herfindahl_index == 0.5

    def test_missing_strategies_in_weights(self):
        """Test missing strategies in weights dict treated as 0."""
        tracker = OnlineCorrelationMatrix(strategies=["A", "B", "C"])

        # Only A specified
        metrics = tracker.get_metrics({"A": 1.0})

        # After normalization: [1.0, 0.0, 0.0]
        # HHI = 1.0
        assert metrics.herfindahl_index == 1.0
        assert metrics.effective_n_strategies == 1.0

    def test_max_pairwise_correlation(self):
        """Test max pairwise correlation."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B", "C"], min_samples=5, shrinkage=0.0
        )

        np.random.seed(42)
        for _ in range(20):
            r = np.random.normal(0, 0.01)
            tracker.update({
                "A": r,
                "B": r,  # Perfectly correlated with A
                "C": np.random.normal(0, 0.01),  # Independent
            })

        metrics = tracker.get_metrics()
        # A-B correlation should be close to 1.0
        assert metrics.max_pairwise_correlation > 0.8

    def test_avg_correlation(self):
        """Test average correlation calculation."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5, shrinkage=0.0
        )

        np.random.seed(42)
        for _ in range(20):
            r = np.random.normal(0, 0.01)
            tracker.update({"A": r, "B": r})

        metrics = tracker.get_metrics()
        # Average of off-diagonal (which is just [0,1] and [1,0])
        corr = tracker.get_correlation_matrix()
        expected_avg = (corr[0, 1] + corr[1, 0]) / 2
        assert abs(metrics.avg_correlation - expected_avg) < 1e-10

    def test_single_strategy_metrics(self):
        """Test metrics with single strategy."""
        tracker = OnlineCorrelationMatrix(strategies=["A"])

        metrics = tracker.get_metrics()

        assert metrics.herfindahl_index == 1.0
        assert metrics.effective_n_strategies == 1.0
        assert metrics.max_pairwise_correlation == 0.0
        assert metrics.avg_correlation == 0.0


# =============================================================================
# Properties Tests
# =============================================================================


class TestProperties:
    """Test property accessors."""

    def test_n_samples_property(self):
        """Test n_samples property."""
        tracker = OnlineCorrelationMatrix(strategies=["A"])

        assert tracker.n_samples == 0

        tracker.update({"A": 0.01})
        assert tracker.n_samples == 1

        tracker.update({"A": 0.02})
        assert tracker.n_samples == 2

    def test_strategy_indices_property(self):
        """Test strategy_indices property."""
        tracker = OnlineCorrelationMatrix(strategies=["X", "Y", "Z"])

        indices = tracker.strategy_indices
        assert indices == {"X": 0, "Y": 1, "Z": 2}


# =============================================================================
# calculate_covariance_penalty Tests
# =============================================================================


class TestCalculateCovariancePenalty:
    """Test calculate_covariance_penalty function."""

    def test_single_strategy_returns_zero(self):
        """Test single strategy returns zero penalty."""
        weights = {"A": 1.0}
        corr = np.array([[1.0]])
        indices = {"A": 0}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        assert penalty == 0.0

    def test_empty_strategies_returns_zero(self):
        """Test empty strategies returns zero penalty."""
        weights = {}
        corr = np.array([]).reshape(0, 0)
        indices = {}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        assert penalty == 0.0

    def test_uncorrelated_strategies(self):
        """Test uncorrelated strategies have zero penalty."""
        weights = {"A": 0.5, "B": 0.5}
        corr = np.array([[1.0, 0.0], [0.0, 1.0]])
        indices = {"A": 0, "B": 1}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        assert abs(penalty) < 1e-10

    def test_perfectly_correlated_strategies(self):
        """Test perfectly correlated strategies have high penalty."""
        weights = {"A": 0.5, "B": 0.5}
        corr = np.array([[1.0, 1.0], [1.0, 1.0]])
        indices = {"A": 0, "B": 1}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        # penalty = 0.5 * 0.5 * 1.0 * 2 (for both off-diagonals) = 0.5
        assert abs(penalty - 0.5) < 1e-10

    def test_high_correlation_penalty(self):
        """Test high correlation example from docstring."""
        weights = {"A": 0.5, "B": 0.5}
        corr = np.array([[1.0, 0.8], [0.8, 1.0]])
        indices = {"A": 0, "B": 1}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        # penalty = 2 * 0.5 * 0.5 * 0.8 = 0.4
        assert abs(penalty - 0.4) < 1e-10

    def test_negative_correlation_penalty(self):
        """Test negative correlation gives negative penalty (hedge)."""
        weights = {"A": 0.5, "B": 0.5}
        corr = np.array([[1.0, -0.8], [-0.8, 1.0]])
        indices = {"A": 0, "B": 1}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        # penalty = 2 * 0.5 * 0.5 * (-0.8) = -0.4
        assert abs(penalty - (-0.4)) < 1e-10

    def test_weights_normalized(self):
        """Test weights are normalized if they don't sum to 1."""
        weights = {"A": 1.0, "B": 1.0}  # Sum = 2.0
        corr = np.array([[1.0, 0.8], [0.8, 1.0]])
        indices = {"A": 0, "B": 1}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        # After normalization: [0.5, 0.5]
        # penalty = 2 * 0.5 * 0.5 * 0.8 = 0.4
        assert abs(penalty - 0.4) < 1e-10

    def test_zero_weight_strategy(self):
        """Test zero weight strategy contributes nothing."""
        weights = {"A": 1.0, "B": 0.0}
        corr = np.array([[1.0, 0.8], [0.8, 1.0]])
        indices = {"A": 0, "B": 1}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        # Only A has weight, no off-diagonal contribution
        assert abs(penalty) < 1e-10

    def test_missing_strategy_in_weights(self):
        """Test missing strategy in weights treated as zero."""
        weights = {"A": 1.0}  # B missing
        corr = np.array([[1.0, 0.8], [0.8, 1.0]])
        indices = {"A": 0, "B": 1}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        assert abs(penalty) < 1e-10

    def test_three_strategies(self):
        """Test penalty with three strategies."""
        weights = {"A": 1/3, "B": 1/3, "C": 1/3}
        # All pairwise correlations = 0.5
        corr = np.array([
            [1.0, 0.5, 0.5],
            [0.5, 1.0, 0.5],
            [0.5, 0.5, 1.0],
        ])
        indices = {"A": 0, "B": 1, "C": 2}

        penalty = calculate_covariance_penalty(weights, corr, indices)
        # 6 off-diagonal pairs, each contributes (1/3)^2 * 0.5 = 0.5/9
        # Total = 6 * 0.5/9 = 3/9 = 1/3
        expected = 6 * (1/3) * (1/3) * 0.5
        assert abs(penalty - expected) < 1e-10

    def test_integration_with_tracker(self):
        """Test penalty calculation with actual tracker output."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5, shrinkage=0.0
        )

        np.random.seed(42)
        for _ in range(20):
            r = np.random.normal(0, 0.01)
            tracker.update({"A": r, "B": r})

        weights = {"A": 0.5, "B": 0.5}
        corr = tracker.get_correlation_matrix()
        indices = tracker.strategy_indices

        penalty = calculate_covariance_penalty(weights, corr, indices)
        # Should be positive (correlated strategies)
        assert penalty > 0.3


# =============================================================================
# Rolling Window Behavior Tests
# =============================================================================


class TestRollingWindowBehavior:
    """Test EMA-based rolling window behavior."""

    def test_ema_adapts_to_regime_change(self):
        """Test EMA adapts when correlation regime changes."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5, decay=0.9, shrinkage=0.0
        )

        # First regime: positive correlation
        np.random.seed(42)
        for _ in range(50):
            r = np.random.normal(0, 0.01)
            tracker.update({"A": r, "B": r})

        corr_before = tracker.get_correlation_matrix()
        assert corr_before[0, 1] > 0.5

        # Second regime: negative correlation
        for _ in range(100):
            r = np.random.normal(0, 0.01)
            tracker.update({"A": r, "B": -r})

        corr_after = tracker.get_correlation_matrix()
        # Should have adapted to negative correlation
        assert corr_after[0, 1] < corr_before[0, 1]

    def test_slow_decay_maintains_history(self):
        """Test slow decay (0.99) maintains more history."""
        tracker_fast = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5, decay=0.9, shrinkage=0.0
        )
        tracker_slow = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5, decay=0.99, shrinkage=0.0
        )

        # Positive correlation phase
        np.random.seed(42)
        for _ in range(50):
            r = np.random.normal(0, 0.01)
            tracker_fast.update({"A": r, "B": r})
            tracker_slow.update({"A": r, "B": r})

        # Negative correlation phase
        for _ in range(20):
            r = np.random.normal(0, 0.01)
            tracker_fast.update({"A": r, "B": -r})
            tracker_slow.update({"A": r, "B": -r})

        corr_fast = tracker_fast.get_correlation_matrix()
        corr_slow = tracker_slow.get_correlation_matrix()

        # Slow decay should show higher correlation (more history)
        assert corr_slow[0, 1] > corr_fast[0, 1]


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_returns(self):
        """Test with very small return values."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5
        )

        for _ in range(20):
            tracker.update({"A": 1e-12, "B": 1e-12})

        corr = tracker.get_correlation_matrix()
        assert corr.shape == (2, 2)
        assert not np.any(np.isnan(corr))

    def test_very_large_returns(self):
        """Test with very large return values."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5
        )

        for _ in range(20):
            tracker.update({"A": 1e6, "B": 1e6})

        corr = tracker.get_correlation_matrix()
        assert corr.shape == (2, 2)
        assert not np.any(np.isnan(corr))

    def test_mixed_positive_negative_returns(self):
        """Test with mixed positive and negative returns."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5
        )

        np.random.seed(42)
        for _ in range(20):
            tracker.update({
                "A": np.random.uniform(-0.1, 0.1),
                "B": np.random.uniform(-0.1, 0.1),
            })

        corr = tracker.get_correlation_matrix()
        assert np.all(corr >= -1.0)
        assert np.all(corr <= 1.0)

    def test_many_strategies(self):
        """Test with many strategies (N=20)."""
        strategies = [f"strat_{i}" for i in range(20)]
        tracker = OnlineCorrelationMatrix(
            strategies=strategies, min_samples=5
        )

        np.random.seed(42)
        for _ in range(30):
            returns = {s: np.random.normal(0, 0.01) for s in strategies}
            tracker.update(returns)

        corr = tracker.get_correlation_matrix()
        assert corr.shape == (20, 20)
        assert np.all(np.abs(np.diag(corr) - 1.0) < 1e-10)

    def test_constant_returns_handled(self):
        """Test constant returns (zero variance) are handled."""
        tracker = OnlineCorrelationMatrix(
            strategies=["A", "B"], min_samples=5
        )

        for _ in range(20):
            tracker.update({"A": 0.01, "B": 0.02})  # Constant

        corr = tracker.get_correlation_matrix()
        # Should not have NaN or inf
        assert not np.any(np.isnan(corr))
        assert not np.any(np.isinf(corr))
