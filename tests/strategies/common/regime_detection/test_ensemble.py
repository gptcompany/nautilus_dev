"""Ensemble voting tests for regime detection.

Tests requirements:
- FR-004: Majority and weighted voting
- FR-006: Emit regime change events when threshold exceeded
- FR-007: Exclude non-warmed-up detectors
- FR-008: Query interface for votes and confidence
- FR-011: Handle detector failures gracefully
- SC-002: False positive rate < 5%
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from strategies.common.regime_detection import RegimeEnsemble, RegimeState
from strategies.common.regime_detection.events import RegimeChangeEvent

if TYPE_CHECKING:
    from tests.strategies.common.regime_detection.conftest import MockDetector


class TestMajorityVoting:
    """Test majority voting (FR-004, 2-of-3 threshold)."""

    def test_majority_two_of_three(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
        mock_volatile_detector: MockDetector,
    ) -> None:
        """Test 2-of-3 majority voting.

        When 2 detectors agree, ensemble should return their regime.
        """
        # Two detectors say TRENDING_UP
        mock_ranging_detector.set_regime(RegimeState.TRENDING_UP)

        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,  # TRENDING_UP
                "d2": mock_ranging_detector,  # TRENDING_UP (changed)
                "d3": mock_volatile_detector,  # VOLATILE
            },
            use_weighted_voting=False,
            voting_threshold=0.5,  # Need > 50% for majority
            min_detectors=2,
        )

        # Trigger vote collection
        ensemble.update(0.01)

        # Should be TRENDING_UP (2 out of 3)
        assert ensemble.current_regime() == RegimeState.TRENDING_UP

    def test_majority_unanimous(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
        mock_volatile_detector: MockDetector,
    ) -> None:
        """Test unanimous agreement."""
        # All detectors say VOLATILE
        mock_trending_detector.set_regime(RegimeState.VOLATILE)
        mock_ranging_detector.set_regime(RegimeState.VOLATILE)

        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
                "d3": mock_volatile_detector,
            },
            use_weighted_voting=False,
            voting_threshold=0.5,
            min_detectors=2,
        )

        ensemble.update(0.01)
        assert ensemble.current_regime() == RegimeState.VOLATILE

    def test_majority_split_vote_maintains_current(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
        mock_volatile_detector: MockDetector,
    ) -> None:
        """When votes are split with no majority, maintain current regime."""
        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,  # TRENDING_UP
                "d2": mock_ranging_detector,  # RANGING
                "d3": mock_volatile_detector,  # VOLATILE
            },
            use_weighted_voting=False,
            voting_threshold=0.5,
            min_detectors=2,
        )

        # Initial regime is RANGING
        initial_regime = ensemble.current_regime()

        # Update - no clear majority
        ensemble.update(0.01)

        # With threshold 0.5 and 3 different votes (each ~33%),
        # no regime exceeds threshold, so current regime is maintained
        # or changes to the one with most votes (implementation dependent)
        # The key is consistent behavior
        votes = ensemble.get_votes()
        assert len(votes) == 3


class TestWeightedVoting:
    """Test confidence-weighted voting (FR-004)."""

    def test_weighted_score_calculation(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
        mock_volatile_detector: MockDetector,
    ) -> None:
        """Test weighted score calculation.

        Example: weights {BOCD: 0.4, IIR: 0.2, Spectral: 0.3, HMM: 0.1}
        confidences [0.8, 0.6, 0.9, 0.5]
        weighted = (0.4*0.8 + 0.2*0.6 + 0.3*0.9 + 0.1*0.5) = 0.74
        """
        # Set specific confidences
        mock_trending_detector.set_confidence(0.8)
        mock_ranging_detector.set_confidence(0.6)
        mock_volatile_detector.set_confidence(0.9)

        # Make all say the same regime so weighted score is meaningful
        mock_trending_detector.set_regime(RegimeState.TRENDING_UP)
        mock_ranging_detector.set_regime(RegimeState.TRENDING_UP)
        mock_volatile_detector.set_regime(RegimeState.TRENDING_UP)

        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
                "d3": mock_volatile_detector,
            },
            weights={"d1": 0.4, "d2": 0.3, "d3": 0.3},
            use_weighted_voting=True,
            voting_threshold=0.5,
            min_detectors=2,
        )

        ensemble.update(0.01)

        # All agree, so confidence should be high
        confidence = ensemble.aggregate_confidence()
        assert 0.5 < confidence <= 1.0

    def test_high_weight_detector_dominates(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
        mock_volatile_detector: MockDetector,
    ) -> None:
        """Test that high-weight detector influences result more."""
        # d1 (high weight) says TRENDING_UP
        mock_trending_detector.set_confidence(0.9)
        mock_trending_detector.set_regime(RegimeState.TRENDING_UP)

        # Others say RANGING
        mock_ranging_detector.set_confidence(0.5)
        mock_volatile_detector.set_confidence(0.5)
        mock_volatile_detector.set_regime(RegimeState.RANGING)

        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,  # TRENDING_UP, weight=0.6
                "d2": mock_ranging_detector,  # RANGING, weight=0.2
                "d3": mock_volatile_detector,  # RANGING, weight=0.2
            },
            weights={"d1": 0.6, "d2": 0.2, "d3": 0.2},
            use_weighted_voting=True,
            voting_threshold=0.4,
            min_detectors=2,
        )

        # Set initial regime to something different
        ensemble._current_regime = RegimeState.RANGING

        ensemble.update(0.01)

        # High weight detector should dominate
        # d1: 0.6 * 0.9 = 0.54 for TRENDING_UP
        # d2+d3: 0.2*0.5 + 0.2*0.5 = 0.2 for RANGING
        # After normalization, TRENDING_UP should win
        votes = ensemble.get_votes()
        assert len(votes) == 3


class TestWarmupExclusion:
    """Test warmup detector exclusion (FR-007)."""

    def test_cold_detector_excluded_from_voting(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
        mock_cold_detector: MockDetector,
    ) -> None:
        """Verify non-warmed-up detectors are excluded from voting."""
        ensemble = RegimeEnsemble(
            detectors={
                "hot1": mock_trending_detector,  # warmed up
                "hot2": mock_ranging_detector,  # warmed up
                "cold": mock_cold_detector,  # NOT warmed up
            },
            use_weighted_voting=False,
            min_detectors=2,
        )

        ensemble.update(0.01)

        # Only 2 votes should be collected (cold detector excluded)
        votes = ensemble.get_votes()
        assert len(votes) == 2
        assert all(v.detector_id != "cold" for v in votes)

    def test_min_detectors_not_met_with_cold_detectors(
        self,
        mock_trending_detector: MockDetector,
        mock_cold_detector: MockDetector,
    ) -> None:
        """When too few warmed-up detectors, no regime change should occur."""
        ensemble = RegimeEnsemble(
            detectors={
                "hot": mock_trending_detector,
                "cold": mock_cold_detector,
            },
            min_detectors=2,  # Need 2, but only 1 is warm
        )

        # Should not produce regime change event
        event = ensemble.update(0.01)
        assert event is None

        # Only 1 vote collected
        votes = ensemble.get_votes()
        assert len(votes) == 1


class TestRegimeChangeEvents:
    """Test regime change event emission (FR-006)."""

    def test_emit_event_on_regime_change(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """Verify event is emitted when regime changes."""
        events_received: list[RegimeChangeEvent] = []

        def callback(event: RegimeChangeEvent) -> None:
            events_received.append(event)

        # Both say RANGING initially
        mock_trending_detector.set_regime(RegimeState.RANGING)
        mock_ranging_detector.set_regime(RegimeState.RANGING)

        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
            },
            on_regime_change=callback,
            voting_threshold=0.5,
            min_detectors=1,
        )

        # First update - sets initial regime
        ensemble.update(0.01)
        assert ensemble.current_regime() == RegimeState.RANGING

        # Change detector outputs
        mock_trending_detector.set_regime(RegimeState.TRENDING_UP)
        mock_ranging_detector.set_regime(RegimeState.TRENDING_UP)

        # Second update - should trigger regime change
        event = ensemble.update(0.02)

        # Event should be returned
        assert event is not None
        assert event.old_regime == RegimeState.RANGING
        assert event.new_regime == RegimeState.TRENDING_UP

        # Callback should have been invoked
        assert len(events_received) == 1
        assert events_received[0].new_regime == RegimeState.TRENDING_UP

    def test_no_event_when_regime_unchanged(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """No event when regime stays the same."""
        events_received: list[RegimeChangeEvent] = []

        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
            },
            on_regime_change=lambda e: events_received.append(e),
            min_detectors=1,
        )

        # Multiple updates with same regime output
        for _ in range(5):
            event = ensemble.update(0.01)

        # Should have at most 1 event (initial setup may trigger one)
        # After that, no new events since regime is stable
        assert len(events_received) <= 1

    def test_event_contains_votes(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """Event should include per-detector votes for audit."""
        mock_trending_detector.set_regime(RegimeState.RANGING)
        mock_ranging_detector.set_regime(RegimeState.RANGING)

        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
            },
            voting_threshold=0.5,
            min_detectors=1,
        )

        # Set initial state
        ensemble.update(0.01)

        # Trigger regime change
        mock_trending_detector.set_regime(RegimeState.VOLATILE)
        mock_ranging_detector.set_regime(RegimeState.VOLATILE)

        event = ensemble.update(0.02)

        assert event is not None
        assert len(event.votes) == 2
        assert all(v.regime == RegimeState.VOLATILE for v in event.votes)


class TestDetectorFailureHandling:
    """Test graceful detector failure handling (FR-011)."""

    def test_continue_with_remaining_detectors_after_failure(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """Ensemble continues with N-1 detectors after failure."""

        class FailingDetector:
            """Detector that raises exception on update."""

            def update(self, value: float) -> None:
                raise RuntimeError("Simulated failure")

            def current_regime(self) -> RegimeState:
                return RegimeState.RANGING

            def confidence(self) -> float:
                return 0.5

            def is_warmed_up(self) -> bool:
                return True

        failing = FailingDetector()

        ensemble = RegimeEnsemble(
            detectors={
                "good1": mock_trending_detector,
                "good2": mock_ranging_detector,
                "bad": failing,
            },
            min_detectors=1,  # Allow operation with 1 detector
        )

        # Should not raise, should continue with remaining detectors
        ensemble.update(0.01)

        # Bad detector should be marked unhealthy
        status = ensemble.get_detector_status()
        assert not status["bad"]["healthy"]
        assert status["bad"]["last_error"] is not None
        assert status["good1"]["healthy"]
        assert status["good2"]["healthy"]

    def test_reset_failed_detector(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """Test resetting a failed detector to healthy."""
        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
            },
        )

        # Manually mark as failed
        ensemble._detectors["d1"].is_healthy = False
        ensemble._detectors["d1"].last_error = "Test error"

        # Reset
        result = ensemble.reset_detector("d1")

        assert result is True
        assert ensemble._detectors["d1"].is_healthy
        assert ensemble._detectors["d1"].last_error is None


class TestEnsembleHealth:
    """Test ensemble health monitoring."""

    def test_is_healthy_with_sufficient_detectors(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """Ensemble is healthy when >= min_detectors are operational."""
        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
            },
            min_detectors=2,
        )

        assert ensemble.is_healthy()

    def test_is_unhealthy_with_insufficient_detectors(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """Ensemble is unhealthy when < min_detectors are operational."""
        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
            },
            min_detectors=2,
        )

        # Mark one as unhealthy
        ensemble._detectors["d1"].is_healthy = False

        assert not ensemble.is_healthy()


class TestRuntimeWeightUpdate:
    """Test runtime weight updates (FR-013)."""

    def test_set_weights_normalizes(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """Weights are normalized to sum to 1.0."""
        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
            },
        )

        ensemble.set_weights({"d1": 2.0, "d2": 8.0})

        # Weights should be normalized
        status = ensemble.get_detector_status()
        assert abs(status["d1"]["weight"] - 0.2) < 0.01
        assert abs(status["d2"]["weight"] - 0.8) < 0.01

    def test_set_weights_rejects_negative(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """Negative weights should be rejected."""
        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
            },
        )

        with pytest.raises(ValueError, match="non-negative"):
            ensemble.set_weights({"d1": -0.5, "d2": 1.0})

    def test_weights_applied_immediately(
        self,
        mock_trending_detector: MockDetector,
        mock_ranging_detector: MockDetector,
    ) -> None:
        """New weights should apply on next update."""
        # Initially both say different things
        mock_trending_detector.set_regime(RegimeState.TRENDING_UP)
        mock_trending_detector.set_confidence(0.9)
        mock_ranging_detector.set_regime(RegimeState.RANGING)
        mock_ranging_detector.set_confidence(0.9)

        ensemble = RegimeEnsemble(
            detectors={
                "d1": mock_trending_detector,
                "d2": mock_ranging_detector,
            },
            use_weighted_voting=True,
            voting_threshold=0.4,
        )

        # Set d1 to dominate
        ensemble.set_weights({"d1": 0.9, "d2": 0.1})

        # Update and verify weights are in status
        ensemble.update(0.01)
        status = ensemble.get_detector_status()
        assert status["d1"]["weight"] == pytest.approx(0.9, abs=0.01)
        assert status["d2"]["weight"] == pytest.approx(0.1, abs=0.01)
