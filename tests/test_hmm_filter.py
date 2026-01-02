"""Tests for HMM regime detection filter.

Tests cover:
- Fitting with sufficient data
- Rejection of insufficient data
- Regime prediction
- Latency requirements (<10ms)
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from strategies.common.regime_detection.hmm_filter import HMMRegimeFilter
from strategies.common.regime_detection.types import RegimeState


@pytest.fixture
def synthetic_trending_data() -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic data with clear trending regime."""
    np.random.seed(42)
    n_samples = 500

    # Trending up: positive drift, low volatility
    returns = np.random.normal(0.001, 0.01, n_samples)
    volatility = np.abs(np.random.normal(0.01, 0.002, n_samples))

    return returns, volatility


@pytest.fixture
def synthetic_multi_regime_data() -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic data with multiple regimes."""
    np.random.seed(42)

    # Regime 1: Trending up (low vol, positive returns)
    r1 = np.random.normal(0.002, 0.008, 150)
    v1 = np.abs(np.random.normal(0.008, 0.002, 150))

    # Regime 2: Volatile (high vol, mixed returns)
    r2 = np.random.normal(0.0, 0.025, 100)
    v2 = np.abs(np.random.normal(0.025, 0.005, 100))

    # Regime 3: Trending down (low vol, negative returns)
    r3 = np.random.normal(-0.002, 0.008, 150)
    v3 = np.abs(np.random.normal(0.008, 0.002, 150))

    # Regime 4: Ranging (low vol, near-zero returns)
    r4 = np.random.normal(0.0, 0.005, 100)
    v4 = np.abs(np.random.normal(0.005, 0.001, 100))

    returns = np.concatenate([r1, r2, r3, r4])
    volatility = np.concatenate([v1, v2, v3, v4])

    return returns, volatility


@pytest.fixture
def insufficient_data() -> tuple[np.ndarray, np.ndarray]:
    """Generate insufficient data for fitting."""
    np.random.seed(42)
    n_samples = 50  # Below minimum threshold

    returns = np.random.normal(0.0, 0.01, n_samples)
    volatility = np.abs(np.random.normal(0.01, 0.002, n_samples))

    return returns, volatility


class TestHMMFit:
    """Tests for HMM fitting behavior."""

    def test_hmm_fit_with_sufficient_data(
        self, synthetic_trending_data: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test that HMM fits successfully with sufficient data."""
        returns, volatility = synthetic_trending_data

        hmm_filter = HMMRegimeFilter(n_states=3, n_iter=100)
        hmm_filter.fit(returns, volatility)

        assert hmm_filter.is_fitted
        assert hmm_filter.model is not None

    def test_hmm_fit_fails_with_insufficient_data(
        self, insufficient_data: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test that HMM raises error with insufficient data."""
        returns, volatility = insufficient_data

        hmm_filter = HMMRegimeFilter(n_states=3, min_samples=100)

        with pytest.raises(ValueError, match="Insufficient data"):
            hmm_filter.fit(returns, volatility)

    def test_hmm_fit_with_multiple_initializations(
        self, synthetic_multi_regime_data: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test that multiple random inits improve convergence."""
        returns, volatility = synthetic_multi_regime_data

        hmm_filter = HMMRegimeFilter(n_states=3, n_iter=50, n_init=5)
        hmm_filter.fit(returns, volatility)

        assert hmm_filter.is_fitted
        # With multiple inits, should have tried to find best model
        assert hmm_filter.best_score is not None


class TestHMMPredict:
    """Tests for HMM prediction behavior."""

    def test_hmm_predict_returns_regime_label(
        self, synthetic_trending_data: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test that predict returns a valid RegimeState."""
        returns, volatility = synthetic_trending_data

        hmm_filter = HMMRegimeFilter(n_states=3, n_iter=100)
        hmm_filter.fit(returns, volatility)

        # Predict on single observation
        regime = hmm_filter.predict(returns[-1], volatility[-1])

        assert isinstance(regime, RegimeState)
        assert regime in list(RegimeState)

    def test_hmm_predict_without_fit_raises_error(self) -> None:
        """Test that predict raises error if not fitted."""
        hmm_filter = HMMRegimeFilter(n_states=3)

        with pytest.raises(RuntimeError, match="not fitted"):
            hmm_filter.predict(0.001, 0.01)

    def test_hmm_predict_latency_under_10ms(
        self, synthetic_trending_data: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test that single prediction completes in <10ms (FR-002)."""
        returns, volatility = synthetic_trending_data

        hmm_filter = HMMRegimeFilter(n_states=3, n_iter=100)
        hmm_filter.fit(returns, volatility)

        # Warm up
        _ = hmm_filter.predict(returns[-1], volatility[-1])

        # Time multiple predictions
        latencies = []
        for i in range(100):
            start = time.perf_counter()
            _ = hmm_filter.predict(
                returns[i % len(returns)], volatility[i % len(volatility)]
            )
            latencies.append((time.perf_counter() - start) * 1000)  # ms

        avg_latency = np.mean(latencies)
        max_latency = np.max(latencies)

        assert avg_latency < 10.0, f"Average latency {avg_latency:.2f}ms exceeds 10ms"
        # Allow some headroom for max due to GC/scheduling
        assert max_latency < 50.0, f"Max latency {max_latency:.2f}ms too high"


class TestHMMStateProbabilities:
    """Tests for state probability output."""

    def test_get_state_probabilities_returns_valid_distribution(
        self, synthetic_trending_data: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test that state probabilities sum to 1."""
        returns, volatility = synthetic_trending_data

        hmm_filter = HMMRegimeFilter(n_states=3, n_iter=100)
        hmm_filter.fit(returns, volatility)

        probs = hmm_filter.get_state_probabilities(returns[-1], volatility[-1])

        assert len(probs) == 3
        assert np.isclose(np.sum(probs), 1.0)
        assert all(p >= 0.0 for p in probs)


class TestHMMRegimeMapping:
    """Tests for regime label mapping."""

    def test_regime_mapping_identifies_volatile_state(
        self, synthetic_multi_regime_data: tuple[np.ndarray, np.ndarray]
    ) -> None:
        """Test that high volatility periods map to VOLATILE regime."""
        returns, volatility = synthetic_multi_regime_data

        hmm_filter = HMMRegimeFilter(n_states=4, n_iter=100)
        hmm_filter.fit(returns, volatility)

        # Predict on high-volatility segment (indices 150-250)
        volatile_predictions = [
            hmm_filter.predict(returns[i], volatility[i]) for i in range(160, 240)
        ]

        # Most predictions should be VOLATILE
        volatile_count = sum(
            1 for r in volatile_predictions if r == RegimeState.VOLATILE
        )
        assert volatile_count > len(volatile_predictions) * 0.5, (
            f"Only {volatile_count}/{len(volatile_predictions)} were VOLATILE"
        )
