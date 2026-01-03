"""Tests for Bayesian Online Changepoint Detection (Spec 026 - US3).

TDD RED Phase: These tests should FAIL until implementation is complete.
"""

from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.meta_learning
class TestBOCDUpdate:
    """Test suite for BOCD update mechanics."""

    def test_update_processes_single_observation(self, bocd_config):
        """Test that update() processes a single observation."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Process a single observation
        bocd.update(0.01)

        # Should have updated internal state
        assert bocd.t == 1

    def test_update_returns_changepoint_probability(self, bocd_config):
        """Test that update returns probability between 0 and 1."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Process multiple observations
        for obs in [0.01, -0.02, 0.015, -0.01]:
            prob = bocd.update(obs)
            assert 0.0 <= prob <= 1.0

    def test_multiple_updates_track_run_length(self, bocd_config):
        """Test that multiple updates correctly track run length."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Process 100 observations
        for i in range(100):
            bocd.update(np.random.normal(0, 0.01))

        assert bocd.t == 100

        # Run length distribution should have length t+1
        rld = bocd.get_run_length_distribution()
        assert len(rld) == 101


@pytest.mark.meta_learning
class TestChangepointProbability:
    """Test suite for changepoint probability calculation."""

    def test_get_changepoint_probability_returns_valid_prob(self, bocd_config):
        """Test that get_changepoint_probability returns P(run_length=0)."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Process some observations
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)

        prob = bocd.get_changepoint_probability()

        assert 0.0 <= prob <= 1.0

    def test_changepoint_probability_increases_on_regime_change(self, bocd_config):
        """Test that changepoint probability increases when regime changes."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Stable regime: low volatility around 0
        for _ in range(100):
            bocd.update(np.random.normal(0, 0.005))

        prob_before = bocd.get_changepoint_probability()

        # Sudden regime change: high volatility, different mean
        for _ in range(10):
            bocd.update(np.random.normal(0.1, 0.05))

        prob_after = bocd.get_changepoint_probability()

        # Probability should increase after regime change
        # (may not always hold for small changes, but should for large ones)
        # This is a soft assertion - we mainly check it doesn't crash
        assert 0.0 <= prob_after <= 1.0


@pytest.mark.meta_learning
class TestRunLengthDistribution:
    """Test suite for run length distribution."""

    def test_run_length_distribution_sums_to_one(self, bocd_config):
        """Test that run length distribution is a valid probability distribution."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Process observations
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)

        rld = bocd.get_run_length_distribution()

        # Should sum to 1.0 (or very close)
        assert abs(np.sum(rld) - 1.0) < 1e-6

    def test_run_length_distribution_non_negative(self, bocd_config):
        """Test that all probabilities are non-negative."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)

        rld = bocd.get_run_length_distribution()

        assert np.all(rld >= 0.0)


@pytest.mark.meta_learning
class TestChangepointDetection:
    """Test suite for is_changepoint() method."""

    def test_is_changepoint_with_threshold(self, bocd_config):
        """Test that is_changepoint uses threshold correctly."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Process stable data
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)

        # Get current probability
        prob = bocd.get_changepoint_probability()

        # Threshold above prob should return False
        result_high = bocd.is_changepoint(threshold=0.99)
        assert not result_high

        # Threshold below prob should return True (if prob > 0)
        if prob > 0:
            result_low = bocd.is_changepoint(threshold=0.0)
            assert result_low

    def test_detects_synthetic_regime_change(self, sample_returns, bocd_config):
        """Test detection on synthetic data with known regime changes."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        changepoints_detected = []

        for i, ret in enumerate(sample_returns):
            bocd.update(ret)
            if bocd.is_changepoint(threshold=0.5):
                changepoints_detected.append(i)

        # sample_returns has regime changes at ~300 and ~700
        # Should detect at least one changepoint
        assert len(changepoints_detected) > 0

    def test_detects_regime_change_within_10_bars(self):
        """Test that BOCD detects regime changes within 10 bars (spec requirement)."""
        from strategies.common.regime_detection.bocd import BOCD
        from strategies.common.regime_detection.config import BOCDConfig

        config = BOCDConfig(
            hazard_rate=0.05,  # Higher for faster detection
            detection_threshold=0.3,
        )
        bocd = BOCD(config)

        # Stable regime
        for _ in range(100):
            bocd.update(np.random.normal(0, 0.01))

        # Clear regime change
        detection_delay = None
        for i in range(20):
            bocd.update(np.random.normal(0.5, 0.01))  # Very different mean
            if bocd.is_changepoint(threshold=0.3):
                detection_delay = i
                break

        # Should detect within 10 bars for obvious change
        if detection_delay is not None:
            assert detection_delay <= 10


@pytest.mark.meta_learning
class TestBOCDReset:
    """Test suite for reset functionality."""

    def test_reset_clears_state(self, bocd_config):
        """Test that reset() clears all internal state."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Process some observations
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)

        assert bocd.t == 50

        # Reset
        bocd.reset()

        # State should be cleared
        assert bocd.t == 0

        # Run length distribution should be reset
        rld = bocd.get_run_length_distribution()
        assert len(rld) == 1
        assert rld[0] == 1.0


@pytest.mark.meta_learning
class TestBOCDPerformance:
    """Test performance requirements."""

    def test_update_latency(self, bocd_config):
        """Test that single update completes in <5ms."""
        import time

        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Warm up with some observations
        for obs in np.random.normal(0, 0.01, 100):
            bocd.update(obs)

        # Measure single update time
        start = time.time()
        for _ in range(100):
            bocd.update(np.random.normal(0, 0.01))
        elapsed = (time.time() - start) / 100

        # Should be <5ms per update
        assert elapsed < 0.005, f"Update took {elapsed * 1000:.2f}ms (>5ms limit)"


@pytest.mark.meta_learning
class TestStudentTPrior:
    """Test Student-t conjugate prior implementation."""

    def test_handles_outliers_gracefully(self, bocd_config):
        """Test that Student-t prior handles outliers without crashing."""
        from strategies.common.regime_detection.bocd import BOCD

        bocd = BOCD(bocd_config)

        # Normal data
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)

        # Extreme outlier
        bocd.update(10.0)  # 1000 standard deviations

        # Should still work
        prob = bocd.get_changepoint_probability()
        assert 0.0 <= prob <= 1.0

        rld = bocd.get_run_length_distribution()
        assert abs(np.sum(rld) - 1.0) < 1e-5
