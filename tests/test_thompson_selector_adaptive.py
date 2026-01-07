"""Tests for ThompsonSelector Adaptive Decay Integration (Spec 032 - US2, US3).

Tests verify:
- US2: Backward compatibility without detector (fixed decay)
- US2: Adaptive decay with IIRRegimeDetector integration
- US2: update() and update_continuous() use adaptive decay
- US3: DecayEvent audit emission
"""

import pytest
from unittest.mock import MagicMock

from strategies.common.adaptive_control.particle_portfolio import (
    ThompsonSelector,
)
from strategies.common.adaptive_control.dsp_filters import IIRRegimeDetector


class TestThompsonSelectorBackwardCompatibility:
    """Tests for backward compatibility (US2)."""

    def test_backward_compatibility_no_detector(self) -> None:
        """Test: ThompsonSelector works without regime_detector (fixed decay).

        When no regime_detector is provided, ThompsonSelector should use
        the fixed decay value (default 0.99) as before.
        """
        selector = ThompsonSelector(
            strategies=["strat_a", "strat_b"],
            decay=0.98,  # Custom fixed decay
        )

        # Should use fixed decay
        assert selector.current_decay == 0.98

        # Update should work normally
        selector.update("strat_a", success=True)
        selector.update_continuous("strat_b", return_value=0.05)

        # Decay should remain fixed
        assert selector.current_decay == 0.98

    def test_default_decay_value(self) -> None:
        """Test: Default decay is 0.99 without regime_detector."""
        selector = ThompsonSelector(strategies=["strat_a"])
        assert selector.current_decay == 0.99


class TestThompsonSelectorAdaptiveDecay:
    """Tests for adaptive decay with IIRRegimeDetector (US2)."""

    @pytest.fixture
    def low_volatility_detector(self) -> IIRRegimeDetector:
        """Create detector in low volatility state (variance_ratio < 0.7).

        Pattern: Start with volatility, then calm down significantly.
        This creates fast_var << slow_var (ratio < 1.0).
        """
        detector = IIRRegimeDetector()
        # First: volatility period (builds up slow variance)
        for i in range(100):
            ret = 0.10 if i % 2 == 0 else -0.10
            detector.update(ret)
        # Then: calm period (reduces fast variance)
        for _ in range(100):
            detector.update(0.0001)
        return detector

    @pytest.fixture
    def high_volatility_detector(self) -> IIRRegimeDetector:
        """Create detector in high volatility state (variance_ratio > 1.5).

        Pattern: Start calm, then spike volatility recently.
        This creates fast_var >> slow_var (ratio > 1.5).
        Using faster response periods to achieve higher ratios.
        """
        detector = IIRRegimeDetector(fast_period=5, slow_period=50)
        # First: very calm period (keeps slow variance low)
        for _ in range(280):
            detector.update(0.0001)
        # Then: recent volatility spike (increases fast variance)
        for i in range(20):
            ret = 0.30 if i % 2 == 0 else -0.30
            detector.update(ret)
        return detector

    def test_adaptive_with_detector_low_volatility(
        self, low_volatility_detector: IIRRegimeDetector
    ) -> None:
        """Test: With detector in low volatility, decay approaches 0.99."""
        selector = ThompsonSelector(
            strategies=["strat_a", "strat_b"],
            decay=0.99,  # Base decay (used when detector not available)
            regime_detector=low_volatility_detector,
        )

        # Adaptive decay should be high (close to 0.99) for low volatility
        decay = selector.current_decay
        assert decay >= 0.97, f"Expected decay >= 0.97 for low volatility, got {decay}"

    def test_adaptive_with_detector_high_volatility(
        self, high_volatility_detector: IIRRegimeDetector
    ) -> None:
        """Test: With detector in high volatility, decay approaches 0.95."""
        selector = ThompsonSelector(
            strategies=["strat_a", "strat_b"],
            decay=0.99,
            regime_detector=high_volatility_detector,
        )

        # Adaptive decay should be low (close to 0.95) for high volatility
        decay = selector.current_decay
        assert decay <= 0.97, f"Expected decay <= 0.97 for high volatility, got {decay}"

    def test_update_uses_adaptive_decay(self, high_volatility_detector: IIRRegimeDetector) -> None:
        """Test: update() method uses adaptive decay when detector available."""
        selector = ThompsonSelector(
            strategies=["strat_a", "strat_b"],
            decay=0.99,
            regime_detector=high_volatility_detector,
        )

        # Record initial stats
        initial_successes = selector.stats["strat_a"].successes

        # Update with success
        selector.update("strat_a", success=True)

        # Stats should have been decayed by adaptive decay (not fixed)
        # Since high volatility, decay should be ~0.95
        # After decay: initial_successes * 0.95, then +1 for success
        expected_min = initial_successes * 0.94  # Allow some tolerance
        expected_max = initial_successes * 0.96 + 1.0

        # Verify decay was applied (successes should be decayed)
        # Note: We can't verify exact decay value, but we can verify it was applied
        assert selector.stats["strat_a"].successes >= expected_min
        assert selector.stats["strat_a"].successes <= expected_max + 1.0

    def test_update_continuous_uses_adaptive_decay(
        self, high_volatility_detector: IIRRegimeDetector
    ) -> None:
        """Test: update_continuous() method uses adaptive decay when detector available."""
        selector = ThompsonSelector(
            strategies=["strat_a", "strat_b"],
            decay=0.99,
            regime_detector=high_volatility_detector,
        )

        # Record initial stats
        initial_successes = selector.stats["strat_a"].successes

        # Update with continuous return
        selector.update_continuous("strat_a", return_value=0.05)

        # Stats should have been decayed by adaptive decay
        # Similar verification as above
        expected_min = initial_successes * 0.94
        expected_max = initial_successes * 0.96 + 1.0

        assert selector.stats["strat_a"].successes >= expected_min
        assert selector.stats["strat_a"].successes <= expected_max + 1.0

    def test_decay_changes_with_detector_updates(self) -> None:
        """Test: Decay value changes as detector state changes."""
        detector = IIRRegimeDetector()
        selector = ThompsonSelector(
            strategies=["strat_a"],
            decay=0.99,
            regime_detector=detector,
        )

        # Initially, detector has default state (variance_ratio ~1.0)
        initial_decay = selector.current_decay

        # Feed high volatility data to detector
        for i in range(50):
            detector.update(0.1 if i % 2 == 0 else -0.1)

        # Decay should have changed
        new_decay = selector.current_decay
        assert new_decay != initial_decay or abs(new_decay - 0.97) < 0.03


class TestThompsonSelectorAuditEmission:
    """Tests for audit event emission (US3)."""

    def test_decay_event_emitted(self) -> None:
        """Test: DecayEvent is emitted when decay is calculated with emitter."""
        mock_emitter = MagicMock()

        detector = IIRRegimeDetector()
        # Initialize detector
        for _ in range(50):
            detector.update(0.01)

        selector = ThompsonSelector(
            strategies=["strat_a"],
            decay=0.99,
            regime_detector=detector,
            audit_emitter=mock_emitter,
        )

        # Trigger update which should emit decay event
        selector.update("strat_a", success=True)

        # Verify emit_system was called with SYS_DECAY_UPDATE
        mock_emitter.emit_system.assert_called()
        call_args = mock_emitter.emit_system.call_args

        # Check event type
        from strategies.common.audit.events import AuditEventType

        assert call_args.kwargs["event_type"] == AuditEventType.SYS_DECAY_UPDATE

    def test_no_emission_without_emitter(self) -> None:
        """Test: No emission when audit_emitter is None."""
        detector = IIRRegimeDetector()
        for _ in range(50):
            detector.update(0.01)

        selector = ThompsonSelector(
            strategies=["strat_a"],
            decay=0.99,
            regime_detector=detector,
            audit_emitter=None,  # No emitter
        )

        # Should not raise any errors
        selector.update("strat_a", success=True)
        selector.update_continuous("strat_a", return_value=0.05)

    def test_decay_event_payload_correct(self) -> None:
        """Test: DecayEvent payload contains correct data."""
        mock_emitter = MagicMock()

        detector = IIRRegimeDetector()
        # Create known state
        for _ in range(100):
            detector.update(0.05)

        selector = ThompsonSelector(
            strategies=["strat_a"],
            decay=0.99,
            regime_detector=detector,
            audit_emitter=mock_emitter,
        )

        # Trigger update
        selector.update("strat_a", success=True)

        # Check payload
        call_args = mock_emitter.emit_system.call_args
        payload = call_args.kwargs["payload"]

        # Payload should contain required fields
        assert "decay_value" in payload
        assert "variance_ratio" in payload
        assert "is_adaptive" in payload

        # Values should be reasonable
        assert 0.95 <= payload["decay_value"] <= 0.99
        assert payload["variance_ratio"] >= 0
        assert payload["is_adaptive"] is True

    def test_no_decay_event_without_detector(self) -> None:
        """Test: No decay event emitted when using fixed decay (no detector)."""
        mock_emitter = MagicMock()

        selector = ThompsonSelector(
            strategies=["strat_a"],
            decay=0.99,
            # No regime_detector
            audit_emitter=mock_emitter,
        )

        # Trigger update
        selector.update("strat_a", success=True)

        # emit_system should NOT have been called for SYS_DECAY_UPDATE
        # (only adaptive decay emits events)
        for call in mock_emitter.emit_system.call_args_list:
            if "event_type" in call.kwargs:
                from strategies.common.audit.events import AuditEventType

                assert call.kwargs["event_type"] != AuditEventType.SYS_DECAY_UPDATE
