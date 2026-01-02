"""Tests for GMM volatility clustering filter.

Tests cover:
- Fitting and cluster identification
- Volatility cluster prediction
- Probability output
"""

from __future__ import annotations

import numpy as np
import pytest

from strategies.common.regime_detection.gmm_filter import GMMVolatilityFilter
from strategies.common.regime_detection.types import VolatilityCluster


@pytest.fixture
def synthetic_volatility_data() -> np.ndarray:
    """Generate synthetic volatility data with 3 distinct clusters."""
    np.random.seed(42)

    # Low volatility cluster (tight range)
    low_vol = np.abs(np.random.normal(0.005, 0.001, 200))

    # Medium volatility cluster
    med_vol = np.abs(np.random.normal(0.015, 0.003, 200))

    # High volatility cluster (wide range)
    high_vol = np.abs(np.random.normal(0.035, 0.007, 200))

    volatility = np.concatenate([low_vol, med_vol, high_vol])
    np.random.shuffle(volatility)  # Shuffle to avoid sequence bias

    return volatility


@pytest.fixture
def two_cluster_volatility() -> np.ndarray:
    """Generate volatility data with 2 distinct clusters."""
    np.random.seed(42)

    low_vol = np.abs(np.random.normal(0.005, 0.001, 300))
    high_vol = np.abs(np.random.normal(0.030, 0.006, 300))

    volatility = np.concatenate([low_vol, high_vol])
    np.random.shuffle(volatility)

    return volatility


class TestGMMFit:
    """Tests for GMM fitting behavior."""

    def test_gmm_fit_identifies_three_clusters(
        self, synthetic_volatility_data: np.ndarray
    ) -> None:
        """Test that GMM identifies 3 volatility clusters."""
        gmm_filter = GMMVolatilityFilter(n_clusters=3)
        gmm_filter.fit(synthetic_volatility_data)

        assert gmm_filter.is_fitted
        assert gmm_filter.model is not None
        assert len(gmm_filter.cluster_means) == 3

        # Cluster means should be different
        means = sorted(gmm_filter.cluster_means)
        assert means[0] < means[1] < means[2]

    def test_gmm_fit_with_two_clusters(
        self, two_cluster_volatility: np.ndarray
    ) -> None:
        """Test that GMM works with 2 clusters."""
        gmm_filter = GMMVolatilityFilter(n_clusters=2)
        gmm_filter.fit(two_cluster_volatility)

        assert gmm_filter.is_fitted
        assert len(gmm_filter.cluster_means) == 2

    def test_gmm_fit_fails_with_insufficient_data(self) -> None:
        """Test that GMM raises error with insufficient data."""
        volatility = np.array([0.01, 0.02, 0.03])  # Too few samples

        gmm_filter = GMMVolatilityFilter(n_clusters=3, min_samples=50)

        with pytest.raises(ValueError, match="Insufficient data"):
            gmm_filter.fit(volatility)


class TestGMMPredict:
    """Tests for GMM prediction behavior."""

    def test_gmm_predict_returns_volatility_cluster(
        self, synthetic_volatility_data: np.ndarray
    ) -> None:
        """Test that predict returns a valid VolatilityCluster."""
        gmm_filter = GMMVolatilityFilter(n_clusters=3)
        gmm_filter.fit(synthetic_volatility_data)

        # Predict on single observation
        cluster = gmm_filter.predict(0.005)  # Low volatility

        assert isinstance(cluster, VolatilityCluster)
        assert cluster in list(VolatilityCluster)

    def test_gmm_predict_without_fit_raises_error(self) -> None:
        """Test that predict raises error if not fitted."""
        gmm_filter = GMMVolatilityFilter(n_clusters=3)

        with pytest.raises(RuntimeError, match="not fitted"):
            gmm_filter.predict(0.01)

    def test_gmm_predict_low_volatility_correctly(
        self, synthetic_volatility_data: np.ndarray
    ) -> None:
        """Test that low volatility values predict LOW cluster."""
        gmm_filter = GMMVolatilityFilter(n_clusters=3)
        gmm_filter.fit(synthetic_volatility_data)

        # Very low volatility should be LOW
        cluster = gmm_filter.predict(0.003)
        assert cluster == VolatilityCluster.LOW

    def test_gmm_predict_high_volatility_correctly(
        self, synthetic_volatility_data: np.ndarray
    ) -> None:
        """Test that high volatility values predict HIGH cluster."""
        gmm_filter = GMMVolatilityFilter(n_clusters=3)
        gmm_filter.fit(synthetic_volatility_data)

        # Very high volatility should be HIGH
        cluster = gmm_filter.predict(0.05)
        assert cluster == VolatilityCluster.HIGH


class TestGMMProbabilities:
    """Tests for GMM probability output."""

    def test_gmm_predict_probabilities_sum_to_one(
        self, synthetic_volatility_data: np.ndarray
    ) -> None:
        """Test that cluster probabilities sum to 1."""
        gmm_filter = GMMVolatilityFilter(n_clusters=3)
        gmm_filter.fit(synthetic_volatility_data)

        probs = gmm_filter.get_cluster_probabilities(0.015)

        assert len(probs) == 3
        assert np.isclose(np.sum(probs), 1.0)
        assert all(p >= 0.0 for p in probs)

    def test_gmm_predict_probabilities_high_confidence_at_extremes(
        self, synthetic_volatility_data: np.ndarray
    ) -> None:
        """Test that extreme values have high confidence."""
        gmm_filter = GMMVolatilityFilter(n_clusters=3)
        gmm_filter.fit(synthetic_volatility_data)

        # Very low volatility should have high prob for LOW cluster
        low_probs = gmm_filter.get_cluster_probabilities(0.003)

        # Very high volatility should have high prob for HIGH cluster
        high_probs = gmm_filter.get_cluster_probabilities(0.05)

        # Get the LOW and HIGH cluster indices
        sorted_indices = sorted(range(3), key=lambda i: gmm_filter.cluster_means[i])
        low_idx = sorted_indices[0]
        high_idx = sorted_indices[2]

        # Expect >50% probability for correct cluster at extremes
        assert low_probs[low_idx] > 0.5, f"Low vol prob: {low_probs}"
        assert high_probs[high_idx] > 0.5, f"High vol prob: {high_probs}"


class TestVolatilityClusterMapping:
    """Tests for volatility cluster label mapping."""

    def test_volatility_cluster_from_gmm_cluster_three_clusters(self) -> None:
        """Test mapping for 3 clusters."""
        cluster_means = [0.005, 0.015, 0.030]  # low, medium, high

        assert (
            VolatilityCluster.from_gmm_cluster(0, cluster_means)
            == VolatilityCluster.LOW
        )
        assert (
            VolatilityCluster.from_gmm_cluster(1, cluster_means)
            == VolatilityCluster.MEDIUM
        )
        assert (
            VolatilityCluster.from_gmm_cluster(2, cluster_means)
            == VolatilityCluster.HIGH
        )

    def test_volatility_cluster_from_gmm_cluster_two_clusters(self) -> None:
        """Test mapping for 2 clusters."""
        cluster_means = [0.005, 0.030]  # low, high

        assert (
            VolatilityCluster.from_gmm_cluster(0, cluster_means)
            == VolatilityCluster.LOW
        )
        assert (
            VolatilityCluster.from_gmm_cluster(1, cluster_means)
            == VolatilityCluster.HIGH
        )
