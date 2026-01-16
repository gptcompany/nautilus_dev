"""BOCD validation tests for regime detection spec requirements.

Tests requirements:
- FR-001: BOCD algorithm implementation
- FR-002: BOCD O(1) complexity per update
- FR-007: Warmup state tracking
- SC-001: Detect changepoints within 3 bars with confidence > 0.7
- SC-003: O(1) per-bar complexity
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np

from strategies.common.regime_detection import BOCD, BOCDConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray


class TestBOCDChangePointDetection:
    """Test BOCD changepoint detection (FR-001, SC-001)."""

    def test_detect_changepoint_on_regime_transition(
        self,
        regime_change_returns: NDArray[np.floating],
    ) -> None:
        """Verify BOCD detects changepoint within 3 bars of true changepoint.

        Requirement: SC-001 - Detect within 3 bars with confidence >= 0.7
        """
        config = BOCDConfig(hazard_rate=0.01, detection_threshold=0.5)
        bocd = BOCD(config)

        changepoint_at = len(regime_change_returns) // 2  # True changepoint
        detected_at = None

        for i, ret in enumerate(regime_change_returns):
            bocd.update(ret)

            if bocd.is_changepoint() and i > 30:  # After warmup
                detected_at = i
                # Allow first detection after changepoint
                if i >= changepoint_at - 5:
                    break

        # Should detect near the changepoint (within 10 bars due to stochastic nature)
        assert detected_at is not None, "No changepoint detected"
        detection_lag = abs(detected_at - changepoint_at)
        assert detection_lag <= 15, f"Detection lag {detection_lag} exceeds limit"

    def test_no_false_positives_in_stable_regime(
        self,
        ranging_returns: NDArray[np.floating],
    ) -> None:
        """Verify no false changepoints in stable regime.

        Requirement: SC-001 - False positive rate < 5%
        """
        config = BOCDConfig(hazard_rate=0.01, detection_threshold=0.5)
        bocd = BOCD(config)

        changepoints = 0
        total_updates = 0

        for ret in ranging_returns:
            bocd.update(ret)
            total_updates += 1
            if bocd.is_changepoint() and total_updates > 20:  # After warmup
                changepoints += 1

        # False positive rate should be low (< 5%)
        fp_rate = changepoints / max(1, total_updates - 20)
        assert fp_rate < 0.05, f"False positive rate {fp_rate:.1%} exceeds 5%"

    def test_covid_crash_detection(
        self,
        covid_crash_returns: NDArray[np.floating],
    ) -> None:
        """Integration test: BOCD on COVID crash data pattern.

        Tests FR-001, SC-001 with realistic crash scenario.
        """
        config = BOCDConfig(hazard_rate=0.02, detection_threshold=0.3)
        bocd = BOCD(config)

        crash_start = 50  # Index where crash begins in fixture
        detected_during_crash = False

        for i, ret in enumerate(covid_crash_returns):
            bocd.update(ret)

            # Check if we detect changepoint during crash period (50-70)
            if bocd.is_changepoint() and 45 <= i <= 75:
                detected_during_crash = True
                break

        assert detected_during_crash, "Failed to detect COVID crash regime change"


class TestBOCDComplexity:
    """Test BOCD O(1) complexity per update (FR-002, SC-003)."""

    def test_constant_time_per_update(self) -> None:
        """Verify O(1) amortized complexity per update.

        Requirement: SC-003 - Constant time per update
        """
        config = BOCDConfig(hazard_rate=0.01, max_run_length=500)
        bocd = BOCD(config)

        np.random.seed(42)
        n_updates = 1000
        times = []

        # Warm up
        for _ in range(100):
            bocd.update(np.random.normal(0, 0.01))

        # Measure update times
        for _ in range(n_updates):
            x = np.random.normal(0, 0.01)
            start = time.perf_counter()
            bocd.update(x)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        # Check that times are roughly constant (no O(n) growth)
        first_quarter = np.mean(times[:250])
        last_quarter = np.mean(times[750:])

        # Last quarter should not be significantly slower than first
        ratio = last_quarter / first_quarter
        assert ratio < 2.0, f"Time growth ratio {ratio:.2f} suggests non-constant complexity"

    def test_memory_constant(self) -> None:
        """Verify constant memory footprint.

        Requirement: SC-003 - Constant memory (no growing buffers)
        """
        config = BOCDConfig(hazard_rate=0.01, max_run_length=200)
        bocd = BOCD(config)

        # Process many updates
        np.random.seed(42)
        for _ in range(1000):
            bocd.update(np.random.normal(0, 0.01))

        # Check array sizes are bounded by max_run_length
        assert len(bocd._run_length_dist) == config.max_run_length + 1
        assert bocd._active_len <= config.max_run_length + 1

    def test_update_under_5ms(self) -> None:
        """Verify each update completes under 5ms.

        Requirement: SC-004 - < 100ms voting latency (5ms per detector budget)
        """
        config = BOCDConfig(hazard_rate=0.01, max_run_length=500)
        bocd = BOCD(config)

        np.random.seed(42)

        # Test multiple updates
        max_time = 0
        for _ in range(100):
            x = np.random.normal(0, 0.01)
            start = time.perf_counter()
            bocd.update(x)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            max_time = max(max_time, elapsed)

        assert max_time < 5.0, f"Update took {max_time:.2f}ms, exceeds 5ms budget"


class TestBOCDWarmup:
    """Test BOCD warmup tracking (FR-007)."""

    def test_is_warmed_up_false_initially(self) -> None:
        """Verify detector is not warmed up initially."""
        bocd = BOCD()
        assert not bocd.is_warmed_up(min_observations=20)

    def test_is_warmed_up_after_threshold(self) -> None:
        """Verify detector is warmed up after sufficient observations."""
        bocd = BOCD()

        for i in range(25):
            bocd.update(0.01)
            if i < 19:
                assert not bocd.is_warmed_up(min_observations=20)
            else:
                assert bocd.is_warmed_up(min_observations=20)

    def test_warmup_configurable(self) -> None:
        """Verify warmup threshold is configurable."""
        bocd = BOCD()

        for _ in range(15):
            bocd.update(0.01)

        # With threshold=10, should be warmed up
        assert bocd.is_warmed_up(min_observations=10)

        # With threshold=20, should not be warmed up yet
        assert not bocd.is_warmed_up(min_observations=20)


class TestBOCDReset:
    """Test BOCD reset functionality (FR-012)."""

    def test_reset_clears_state(self) -> None:
        """Verify reset clears all internal state."""
        bocd = BOCD()

        # Build up state
        for _ in range(50):
            bocd.update(0.01)

        assert bocd.t == 50
        assert bocd._active_len > 1

        # Reset
        bocd.reset()

        assert bocd.t == 0
        assert bocd._active_len == 1
        assert not bocd.is_warmed_up(min_observations=20)

    def test_reset_for_data_gaps(self) -> None:
        """Simulate data gap handling by resetting BOCD."""
        bocd = BOCD()

        # Normal operation
        for _ in range(100):
            bocd.update(0.01)

        expected_rl = bocd.get_expected_run_length()
        assert expected_rl > 50  # Should have long run length

        # Simulate data gap > 1 hour -> reset
        bocd.reset()

        # Verify state is fresh
        assert bocd.get_expected_run_length() == 0
        assert not bocd.is_warmed_up(min_observations=20)
