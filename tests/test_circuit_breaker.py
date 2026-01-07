"""
Unit tests for CircuitBreaker.

Tests cover:
- T004: CircuitBreakerState enum
- T005: CircuitBreakerConfig validation (see test_circuit_breaker_config.py)
- T006: Drawdown calculation
- T007: State transitions (ACTIVE→WARNING→REDUCING→HALTED)
- T008: Recovery transitions
- T009: can_open_position() logic
- T010: position_size_multiplier() logic
- T011: Manual reset()
- T011b: Edge cases (startup, rapid drawdown, oscillation, division by zero)
"""

from decimal import Decimal

import pytest

from risk import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState


# --- Fixtures ---


@pytest.fixture
def default_config() -> CircuitBreakerConfig:
    """Default circuit breaker config for tests."""
    return CircuitBreakerConfig(
        level1_drawdown_pct=Decimal("0.10"),  # 10% - WARNING
        level2_drawdown_pct=Decimal("0.15"),  # 15% - REDUCING
        level3_drawdown_pct=Decimal("0.20"),  # 20% - HALTED
        recovery_drawdown_pct=Decimal("0.05"),  # 5% - recover to ACTIVE
        auto_recovery=False,
    )


@pytest.fixture
def auto_recovery_config() -> CircuitBreakerConfig:
    """Circuit breaker config with auto_recovery enabled."""
    return CircuitBreakerConfig(
        level1_drawdown_pct=Decimal("0.10"),
        level2_drawdown_pct=Decimal("0.15"),
        level3_drawdown_pct=Decimal("0.20"),
        recovery_drawdown_pct=Decimal("0.05"),
        auto_recovery=True,
    )


@pytest.fixture
def circuit_breaker(default_config: CircuitBreakerConfig) -> CircuitBreaker:
    """Create circuit breaker with default config and no portfolio."""
    return CircuitBreaker(config=default_config, portfolio=None)


# --- T004: CircuitBreakerState Enum Tests ---


class TestCircuitBreakerState:
    """T004: Unit test for CircuitBreakerState enum."""

    def test_state_values(self) -> None:
        """Verify all state values are correct."""
        assert CircuitBreakerState.ACTIVE.value == "active"
        assert CircuitBreakerState.WARNING.value == "warning"
        assert CircuitBreakerState.REDUCING.value == "reducing"
        assert CircuitBreakerState.HALTED.value == "halted"

    def test_state_count(self) -> None:
        """Verify exactly 4 states exist."""
        assert len(CircuitBreakerState) == 4


# --- T006: Drawdown Calculation Tests ---


class TestDrawdownCalculation:
    """T006: Unit test for drawdown calculation."""

    def test_drawdown_zero_at_peak(self, circuit_breaker: CircuitBreaker) -> None:
        """Drawdown should be 0 when at peak."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("100000"))

        assert circuit_breaker.current_drawdown == Decimal("0")

    def test_drawdown_10_percent(self, circuit_breaker: CircuitBreaker) -> None:
        """Drawdown should be 0.10 when 10% below peak."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))

        assert circuit_breaker.current_drawdown == Decimal("0.10")

    def test_drawdown_20_percent(self, circuit_breaker: CircuitBreaker) -> None:
        """Drawdown should be 0.20 when 20% below peak."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))

        assert circuit_breaker.current_drawdown == Decimal("0.20")

    def test_drawdown_tracks_peak(self, circuit_breaker: CircuitBreaker) -> None:
        """Peak should update when equity increases."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("110000"))

        assert circuit_breaker.peak_equity == Decimal("110000")
        assert circuit_breaker.current_drawdown == Decimal("0")

    def test_peak_never_decreases(self, circuit_breaker: CircuitBreaker) -> None:
        """Peak should not decrease when equity drops."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("110000"))
        circuit_breaker.update(equity=Decimal("90000"))

        assert circuit_breaker.peak_equity == Decimal("110000")


# --- T007: State Transitions Tests ---


class TestStateTransitions:
    """T007: Unit test for state transitions (ACTIVE→WARNING→REDUCING→HALTED)."""

    def test_starts_in_active_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Circuit breaker should start in ACTIVE state."""
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_transition_to_warning_at_10_percent(self, circuit_breaker: CircuitBreaker) -> None:
        """Should transition to WARNING at 10% drawdown."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # 10% drawdown

        assert circuit_breaker.state == CircuitBreakerState.WARNING

    def test_transition_to_reducing_at_15_percent(self, circuit_breaker: CircuitBreaker) -> None:
        """Should transition to REDUCING at 15% drawdown."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # 15% drawdown

        assert circuit_breaker.state == CircuitBreakerState.REDUCING

    def test_transition_to_halted_at_20_percent(self, circuit_breaker: CircuitBreaker) -> None:
        """Should transition to HALTED at 20% drawdown."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # 20% drawdown

        assert circuit_breaker.state == CircuitBreakerState.HALTED

    def test_graduated_transitions(self, circuit_breaker: CircuitBreaker) -> None:
        """Should transition through all states as drawdown increases."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # ACTIVE at 5% drawdown
        circuit_breaker.update(equity=Decimal("95000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

        # WARNING at 10% drawdown
        circuit_breaker.update(equity=Decimal("90000"))
        assert circuit_breaker.state == CircuitBreakerState.WARNING

        # REDUCING at 15% drawdown
        circuit_breaker.update(equity=Decimal("85000"))
        assert circuit_breaker.state == CircuitBreakerState.REDUCING

        # HALTED at 20% drawdown
        circuit_breaker.update(equity=Decimal("80000"))
        assert circuit_breaker.state == CircuitBreakerState.HALTED


# --- T008: Recovery Transitions Tests ---


class TestRecoveryTransitions:
    """T008: Unit test for recovery transitions."""

    def test_recovery_from_warning_to_active(self, circuit_breaker: CircuitBreaker) -> None:
        """Should recover from WARNING to ACTIVE when below recovery threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Go to WARNING
        circuit_breaker.update(equity=Decimal("90000"))
        assert circuit_breaker.state == CircuitBreakerState.WARNING

        # Recover to ACTIVE (below 5% recovery threshold)
        circuit_breaker.update(equity=Decimal("96000"))  # 4% drawdown
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_recovery_from_reducing_to_active(self, circuit_breaker: CircuitBreaker) -> None:
        """Should recover from REDUCING to ACTIVE when below recovery threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Go to REDUCING
        circuit_breaker.update(equity=Decimal("85000"))
        assert circuit_breaker.state == CircuitBreakerState.REDUCING

        # Recover to ACTIVE (below 5% recovery threshold)
        circuit_breaker.update(equity=Decimal("96000"))  # 4% drawdown
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_halted_requires_manual_reset(self, circuit_breaker: CircuitBreaker) -> None:
        """HALTED state should NOT auto-recover when auto_recovery=False."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Go to HALTED
        circuit_breaker.update(equity=Decimal("80000"))
        assert circuit_breaker.state == CircuitBreakerState.HALTED

        # Try to recover - should stay HALTED
        circuit_breaker.update(equity=Decimal("96000"))  # 4% drawdown
        assert circuit_breaker.state == CircuitBreakerState.HALTED

    def test_halted_auto_recovery_when_enabled(
        self, auto_recovery_config: CircuitBreakerConfig
    ) -> None:
        """HALTED state should auto-recover when auto_recovery=True."""
        cb = CircuitBreaker(config=auto_recovery_config, portfolio=None)
        cb.set_initial_equity(Decimal("100000"))

        # Go to HALTED
        cb.update(equity=Decimal("80000"))
        assert cb.state == CircuitBreakerState.HALTED

        # Recover to ACTIVE (below 5% recovery threshold)
        cb.update(equity=Decimal("96000"))  # 4% drawdown
        assert cb.state == CircuitBreakerState.ACTIVE


# --- T009: can_open_position() Tests ---


class TestCanOpenPosition:
    """T009: Unit test for can_open_position() logic."""

    def test_can_open_in_active_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Should allow positions in ACTIVE state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("100000"))

        assert circuit_breaker.can_open_position() is True

    def test_can_open_in_warning_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Should allow positions in WARNING state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # 10% drawdown

        assert circuit_breaker.state == CircuitBreakerState.WARNING
        assert circuit_breaker.can_open_position() is True

    def test_cannot_open_in_reducing_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Should NOT allow positions in REDUCING state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # 15% drawdown

        assert circuit_breaker.state == CircuitBreakerState.REDUCING
        assert circuit_breaker.can_open_position() is False

    def test_cannot_open_in_halted_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Should NOT allow positions in HALTED state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # 20% drawdown

        assert circuit_breaker.state == CircuitBreakerState.HALTED
        assert circuit_breaker.can_open_position() is False


# --- T010: position_size_multiplier() Tests ---


class TestPositionSizeMultiplier:
    """T010: Unit test for position_size_multiplier() logic."""

    def test_full_size_in_active_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Should return 1.0 (100%) in ACTIVE state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("100000"))

        assert circuit_breaker.position_size_multiplier() == Decimal("1.0")

    def test_reduced_size_in_warning_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Should return 0.5 (50%) in WARNING state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # 10% drawdown

        assert circuit_breaker.position_size_multiplier() == Decimal("0.5")

    def test_zero_size_in_reducing_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Should return 0.0 in REDUCING state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # 15% drawdown

        assert circuit_breaker.position_size_multiplier() == Decimal("0.0")

    def test_zero_size_in_halted_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Should return 0.0 in HALTED state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # 20% drawdown

        assert circuit_breaker.position_size_multiplier() == Decimal("0.0")

    def test_custom_warning_multiplier(self, default_config: CircuitBreakerConfig) -> None:
        """Should respect custom warning_size_multiplier."""
        config = CircuitBreakerConfig(
            level1_drawdown_pct=Decimal("0.10"),
            level2_drawdown_pct=Decimal("0.15"),
            level3_drawdown_pct=Decimal("0.20"),
            recovery_drawdown_pct=Decimal("0.05"),
            warning_size_multiplier=Decimal("0.75"),  # 75%
        )
        cb = CircuitBreaker(config=config, portfolio=None)
        cb.set_initial_equity(Decimal("100000"))
        cb.update(equity=Decimal("90000"))  # 10% drawdown

        assert cb.position_size_multiplier() == Decimal("0.75")


# --- T011: Manual reset() Tests ---


class TestManualReset:
    """T011: Unit test for manual reset()."""

    def test_reset_from_halted_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Should reset to ACTIVE from HALTED state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # 20% drawdown

        assert circuit_breaker.state == CircuitBreakerState.HALTED

        circuit_breaker.reset()

        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_reset_fails_when_auto_recovery_enabled(
        self, auto_recovery_config: CircuitBreakerConfig
    ) -> None:
        """Should raise ValueError when auto_recovery is enabled."""
        cb = CircuitBreaker(config=auto_recovery_config, portfolio=None)
        cb.set_initial_equity(Decimal("100000"))
        cb.update(equity=Decimal("80000"))

        with pytest.raises(ValueError, match="auto_recovery"):
            cb.reset()

    def test_reset_fails_when_not_halted(self, circuit_breaker: CircuitBreaker) -> None:
        """Should raise ValueError when state is not HALTED."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # WARNING state

        assert circuit_breaker.state == CircuitBreakerState.WARNING

        with pytest.raises(ValueError, match="HALTED"):
            circuit_breaker.reset()


# --- T011b: Edge Cases Tests ---


class TestEdgeCases:
    """T011b: Unit test for edge cases."""

    def test_initial_equity_zero_startup(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle initial equity = 0 at startup."""
        # Don't set initial equity - should stay at 0
        assert circuit_breaker.peak_equity == Decimal("0")
        assert circuit_breaker.current_drawdown == Decimal("0")
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_rapid_drawdown_skips_intermediate_states(
        self, circuit_breaker: CircuitBreaker
    ) -> None:
        """Should handle rapid drawdown that skips intermediate states."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Jump directly to 25% drawdown (should be HALTED, not WARNING/REDUCING)
        circuit_breaker.update(equity=Decimal("75000"))

        assert circuit_breaker.state == CircuitBreakerState.HALTED

    def test_recovery_oscillation_near_threshold(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle oscillation near threshold (hysteresis test)."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Go to WARNING at 10%
        circuit_breaker.update(equity=Decimal("90000"))
        assert circuit_breaker.state == CircuitBreakerState.WARNING

        # Recovery to 6% (above recovery threshold of 5%)
        circuit_breaker.update(equity=Decimal("94000"))
        assert circuit_breaker.state == CircuitBreakerState.WARNING  # Still WARNING

        # Recovery to 4% (below recovery threshold)
        circuit_breaker.update(equity=Decimal("96000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

        # Back to exactly 10%
        circuit_breaker.update(equity=Decimal("90000"))
        assert circuit_breaker.state == CircuitBreakerState.WARNING

    def test_division_by_zero_protection(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle peak_equity = 0 without division by zero."""
        # Peak is 0, should not crash
        circuit_breaker.update(equity=Decimal("0"))

        assert circuit_breaker.current_drawdown == Decimal("0")
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_negative_equity_handling(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle negative equity (margin call scenario)."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Negative equity (margin call)
        circuit_breaker.update(equity=Decimal("-10000"))

        # Drawdown should be > 100%
        assert circuit_breaker.current_drawdown > Decimal("1.0")
        assert circuit_breaker.state == CircuitBreakerState.HALTED


# --- Additional Tests for Properties ---


class TestProperties:
    """Tests for property accessors."""

    def test_config_property(
        self, circuit_breaker: CircuitBreaker, default_config: CircuitBreakerConfig
    ) -> None:
        """Config property should return the configuration."""
        assert circuit_breaker.config == default_config

    def test_current_equity_property(self, circuit_breaker: CircuitBreaker) -> None:
        """current_equity property should return last known equity."""
        circuit_breaker.set_initial_equity(Decimal("50000"))
        circuit_breaker.update(equity=Decimal("45000"))

        assert circuit_breaker.current_equity == Decimal("45000")

    def test_last_check_property(self, circuit_breaker: CircuitBreaker) -> None:
        """last_check property should return timestamp of last update."""
        from datetime import datetime, timezone

        circuit_breaker.update(equity=Decimal("100000"))

        assert isinstance(circuit_breaker.last_check, datetime)
        assert circuit_breaker.last_check.tzinfo == timezone.utc


# --- T016-T018: CircuitBreakerActor Tests ---


class TestCircuitBreakerActorInitialization:
    """T016: Unit test for CircuitBreakerActor initialization."""

    def test_actor_initializes_with_config(self, default_config: CircuitBreakerConfig) -> None:
        """Actor should initialize with config and circuit breaker."""
        from risk.circuit_breaker_actor import CircuitBreakerActor

        actor = CircuitBreakerActor(config=default_config)

        assert actor.circuit_breaker is not None
        assert actor.circuit_breaker.config == default_config

    def test_actor_starts_in_active_state(self, default_config: CircuitBreakerConfig) -> None:
        """Actor should start with circuit breaker in ACTIVE state."""
        from risk.circuit_breaker_actor import CircuitBreakerActor

        actor = CircuitBreakerActor(config=default_config)

        assert actor.circuit_breaker.state == CircuitBreakerState.ACTIVE


class TestCircuitBreakerActorAccountHandler:
    """T017: Unit test for on_account_state handler."""

    def test_updates_equity_on_account_state(self, default_config: CircuitBreakerConfig) -> None:
        """Should update circuit breaker equity when account state received."""
        from unittest.mock import MagicMock

        from risk.circuit_breaker_actor import CircuitBreakerActor

        actor = CircuitBreakerActor(config=default_config)
        actor.circuit_breaker.set_initial_equity(Decimal("100000"))

        # Create mock account state event
        mock_event = MagicMock()
        mock_event.balances = [MagicMock()]
        mock_event.balances[0].total = MagicMock()
        mock_event.balances[0].total.as_decimal.return_value = Decimal("90000")

        actor.handle_account_state(mock_event)

        assert actor.circuit_breaker.current_equity == Decimal("90000")
        assert actor.circuit_breaker.state == CircuitBreakerState.WARNING

    def test_transitions_state_on_drawdown(self, default_config: CircuitBreakerConfig) -> None:
        """Should transition state based on drawdown from account updates."""
        from unittest.mock import MagicMock

        from risk.circuit_breaker_actor import CircuitBreakerActor

        actor = CircuitBreakerActor(config=default_config)
        actor.circuit_breaker.set_initial_equity(Decimal("100000"))

        # Simulate 20% drawdown
        mock_event = MagicMock()
        mock_event.balances = [MagicMock()]
        mock_event.balances[0].total = MagicMock()
        mock_event.balances[0].total.as_decimal.return_value = Decimal("80000")

        actor.handle_account_state(mock_event)

        assert actor.circuit_breaker.state == CircuitBreakerState.HALTED


class TestCircuitBreakerActorTimerCheck:
    """T018: Unit test for periodic timer check."""

    def test_timer_check_updates_state(self, default_config: CircuitBreakerConfig) -> None:
        """Periodic timer check should update circuit breaker state."""
        from risk.circuit_breaker_actor import CircuitBreakerActor

        actor = CircuitBreakerActor(config=default_config)
        actor.circuit_breaker.set_initial_equity(Decimal("100000"))

        # Manually update equity to simulate drawdown
        actor.circuit_breaker._current_equity = Decimal("85000")

        # Timer check should recalculate
        actor.on_timer_check()

        assert actor.circuit_breaker.state == CircuitBreakerState.REDUCING

    def test_config_check_interval(self, default_config: CircuitBreakerConfig) -> None:
        """Actor should use config check_interval_secs."""
        from risk.circuit_breaker_actor import CircuitBreakerActor

        actor = CircuitBreakerActor(config=default_config)

        assert actor.check_interval_secs == default_config.check_interval_secs
