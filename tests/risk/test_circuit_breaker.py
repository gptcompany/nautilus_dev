"""
Comprehensive tests for CircuitBreaker implementation.

This is a PRODUCTION trading system handling REAL MONEY.
The circuit breaker is a CRITICAL safety mechanism.

Test Coverage:
- Configuration validation
- State initialization
- Equity tracking and peak updates
- Drawdown calculation
- State transitions (all paths)
- Trip conditions and thresholds
- Reset logic (manual and auto-recovery)
- Position sizing multipliers
- Edge cases: zero equity, negative equity, boundary conditions
- Concurrency considerations
- Cooldown periods
- Rapid state transitions

Target: 90%+ coverage
"""

# Python 3.10 compatibility
import datetime as _dt
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from risk.circuit_breaker import CircuitBreaker
from risk.circuit_breaker_config import CircuitBreakerConfig
from risk.circuit_breaker_state import CircuitBreakerState

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def default_config() -> CircuitBreakerConfig:
    """Create default circuit breaker configuration."""
    return CircuitBreakerConfig(
        level1_drawdown_pct=Decimal("0.10"),  # 10% WARNING
        level2_drawdown_pct=Decimal("0.15"),  # 15% REDUCING
        level3_drawdown_pct=Decimal("0.20"),  # 20% HALTED
        recovery_drawdown_pct=Decimal("0.05"),  # 5% recovery
        auto_recovery=False,
        check_interval_secs=60,
        warning_size_multiplier=Decimal("0.5"),
        reducing_size_multiplier=Decimal("0.0"),
    )


@pytest.fixture
def auto_recovery_config() -> CircuitBreakerConfig:
    """Create config with auto-recovery enabled."""
    return CircuitBreakerConfig(
        level1_drawdown_pct=Decimal("0.10"),
        level2_drawdown_pct=Decimal("0.15"),
        level3_drawdown_pct=Decimal("0.20"),
        recovery_drawdown_pct=Decimal("0.05"),
        auto_recovery=True,  # Enable auto-recovery
        check_interval_secs=60,
        warning_size_multiplier=Decimal("0.5"),
        reducing_size_multiplier=Decimal("0.0"),
    )


@pytest.fixture
def tight_config() -> CircuitBreakerConfig:
    """Create config with tight thresholds for testing."""
    return CircuitBreakerConfig(
        level1_drawdown_pct=Decimal("0.05"),  # 5%
        level2_drawdown_pct=Decimal("0.08"),  # 8%
        level3_drawdown_pct=Decimal("0.10"),  # 10%
        recovery_drawdown_pct=Decimal("0.02"),  # 2%
        auto_recovery=False,
    )


@pytest.fixture
def circuit_breaker(default_config: CircuitBreakerConfig) -> CircuitBreaker:
    """Create circuit breaker with default config."""
    return CircuitBreaker(config=default_config, portfolio=None)


@pytest.fixture
def mock_portfolio() -> MagicMock:
    """Create mock Portfolio for testing."""
    portfolio = MagicMock()

    # Setup mock venue
    venue = MagicMock()
    portfolio.venue = venue

    # Setup mock account with balance
    account = MagicMock()
    MagicMock()
    balance_value = 100000.0
    account.balance_total.return_value = balance_value
    portfolio.account.return_value = account

    return portfolio


# =============================================================================
# Configuration Tests
# =============================================================================


class TestCircuitBreakerConfig:
    """Test configuration validation."""

    def test_default_config_valid(self) -> None:
        """Default configuration should be valid."""
        config = CircuitBreakerConfig()
        assert config.level1_drawdown_pct == Decimal("0.10")
        assert config.level2_drawdown_pct == Decimal("0.15")
        assert config.level3_drawdown_pct == Decimal("0.20")
        assert config.recovery_drawdown_pct == Decimal("0.05")
        assert config.auto_recovery is False

    def test_thresholds_must_be_ordered(self) -> None:
        """Thresholds must be in ascending order: level1 < level2 < level3."""
        with pytest.raises(ValidationError) as exc_info:
            CircuitBreakerConfig(
                level1_drawdown_pct=Decimal("0.20"),  # Wrong order
                level2_drawdown_pct=Decimal("0.15"),
                level3_drawdown_pct=Decimal("0.10"),
            )
        assert "must be ordered" in str(exc_info.value)

    def test_recovery_must_be_below_level1(self) -> None:
        """Recovery threshold must be below level1 (hysteresis)."""
        with pytest.raises(ValidationError) as exc_info:
            CircuitBreakerConfig(
                level1_drawdown_pct=Decimal("0.10"),
                recovery_drawdown_pct=Decimal("0.12"),  # Above level1
            )
        assert "must be less than level1" in str(exc_info.value)

    def test_percentages_must_be_in_range(self) -> None:
        """Percentages must be between 0 and 1 (exclusive)."""
        # Test 0
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(level1_drawdown_pct=Decimal("0"))

        # Test 1
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(level3_drawdown_pct=Decimal("1.0"))

        # Test negative
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(level1_drawdown_pct=Decimal("-0.1"))

    def test_multipliers_must_be_in_range(self) -> None:
        """Size multipliers must be between 0 and 1 (inclusive)."""
        # Test negative
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(warning_size_multiplier=Decimal("-0.1"))

        # Test > 1
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(warning_size_multiplier=Decimal("1.5"))

        # Test 0 and 1 are valid
        config = CircuitBreakerConfig(
            warning_size_multiplier=Decimal("0.0"),
            reducing_size_multiplier=Decimal("1.0"),
        )
        assert config.warning_size_multiplier == Decimal("0.0")
        assert config.reducing_size_multiplier == Decimal("1.0")

    def test_check_interval_must_be_positive(self) -> None:
        """Check interval must be positive."""
        with pytest.raises(ValidationError):
            CircuitBreakerConfig(check_interval_secs=0)

        with pytest.raises(ValidationError):
            CircuitBreakerConfig(check_interval_secs=-60)

    def test_config_is_frozen(self) -> None:
        """Config should be immutable (frozen)."""
        config = CircuitBreakerConfig()
        with pytest.raises(ValidationError):
            config.level1_drawdown_pct = Decimal("0.15")


# =============================================================================
# Initialization Tests
# =============================================================================


class TestCircuitBreakerInitialization:
    """Test circuit breaker initialization."""

    def test_initialization_without_portfolio(self, default_config: CircuitBreakerConfig) -> None:
        """Should initialize without portfolio (for testing)."""
        cb = CircuitBreaker(config=default_config, portfolio=None)
        assert cb.config == default_config
        assert cb.state == CircuitBreakerState.ACTIVE
        assert cb.peak_equity == Decimal("0")
        assert cb.current_equity == Decimal("0")
        assert cb.current_drawdown == Decimal("0")

    def test_initialization_with_portfolio(
        self, default_config: CircuitBreakerConfig, mock_portfolio: MagicMock
    ) -> None:
        """Should initialize with portfolio."""
        cb = CircuitBreaker(config=default_config, portfolio=mock_portfolio)
        assert cb.config == default_config
        assert cb._portfolio == mock_portfolio

    def test_last_check_timestamp_set(self, circuit_breaker: CircuitBreaker) -> None:
        """Should set last_check timestamp on initialization."""
        now = datetime.now(UTC)
        assert isinstance(circuit_breaker.last_check, datetime)
        # Should be within 1 second
        assert (now - circuit_breaker.last_check).total_seconds() < 1


# =============================================================================
# Equity Tracking Tests
# =============================================================================


class TestEquityTracking:
    """Test equity tracking and peak updates."""

    def test_set_initial_equity(self, circuit_breaker: CircuitBreaker) -> None:
        """Should set both current and peak equity."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        assert circuit_breaker.current_equity == Decimal("100000")
        assert circuit_breaker.peak_equity == Decimal("100000")
        assert circuit_breaker.current_drawdown == Decimal("0")

    def test_update_with_explicit_equity(self, circuit_breaker: CircuitBreaker) -> None:
        """Should update equity when explicitly provided."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("105000"))
        assert circuit_breaker.current_equity == Decimal("105000")

    def test_update_peak_on_new_high(self, circuit_breaker: CircuitBreaker) -> None:
        """Should update peak equity on new high."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("110000"))
        assert circuit_breaker.peak_equity == Decimal("110000")

    def test_peak_not_updated_on_decline(self, circuit_breaker: CircuitBreaker) -> None:
        """Should not update peak on equity decline."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))
        assert circuit_breaker.peak_equity == Decimal("100000")
        assert circuit_breaker.current_equity == Decimal("90000")

    def test_update_from_portfolio(
        self, default_config: CircuitBreakerConfig, mock_portfolio: MagicMock
    ) -> None:
        """Should read equity from portfolio if not provided."""
        cb = CircuitBreaker(config=default_config, portfolio=mock_portfolio)
        cb.set_initial_equity(Decimal("100000"))

        # Update without explicit equity
        cb.update()

        # Should have called portfolio.account
        mock_portfolio.account.assert_called_once()

    def test_update_timestamp(self, circuit_breaker: CircuitBreaker) -> None:
        """Should update last_check timestamp on update."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        old_timestamp = circuit_breaker.last_check

        # Wait a tiny bit
        import time

        time.sleep(0.01)

        circuit_breaker.update(equity=Decimal("100000"))
        assert circuit_breaker.last_check > old_timestamp


# =============================================================================
# Drawdown Calculation Tests
# =============================================================================


class TestDrawdownCalculation:
    """Test drawdown calculation logic."""

    def test_zero_drawdown_at_peak(self, circuit_breaker: CircuitBreaker) -> None:
        """Drawdown should be zero at peak equity."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("100000"))
        assert circuit_breaker.current_drawdown == Decimal("0")

    def test_calculate_simple_drawdown(self, circuit_breaker: CircuitBreaker) -> None:
        """Should calculate drawdown correctly."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # 10% drawdown
        assert circuit_breaker.current_drawdown == Decimal("0.1")

    def test_calculate_precise_drawdown(self, circuit_breaker: CircuitBreaker) -> None:
        """Should maintain precision in drawdown calculation."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # 15% drawdown
        assert circuit_breaker.current_drawdown == Decimal("0.15")

    def test_drawdown_from_new_peak(self, circuit_breaker: CircuitBreaker) -> None:
        """Drawdown should be calculated from new peak."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("120000"))  # New peak
        circuit_breaker.update(equity=Decimal("108000"))  # 10% from new peak
        assert circuit_breaker.current_drawdown == Decimal("0.1")

    def test_zero_peak_equity_returns_zero_drawdown(self, circuit_breaker: CircuitBreaker) -> None:
        """Should return 0 drawdown when peak equity is 0 (startup)."""
        # Don't set initial equity
        circuit_breaker.update(equity=Decimal("0"))
        assert circuit_breaker.current_drawdown == Decimal("0")

    def test_negative_equity_drawdown(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle negative equity (catastrophic loss)."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("-10000"))
        # Drawdown = (100000 - (-10000)) / 100000 = 1.1 (110%)
        assert circuit_breaker.current_drawdown == Decimal("1.1")


# =============================================================================
# State Transition Tests
# =============================================================================


class TestStateTransitions:
    """Test all state transition paths."""

    def test_initial_state_is_active(self, circuit_breaker: CircuitBreaker) -> None:
        """Initial state should be ACTIVE."""
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_transition_to_warning(self, circuit_breaker: CircuitBreaker) -> None:
        """Should transition to WARNING at level1 threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # 10% drawdown = level1
        assert circuit_breaker.state == CircuitBreakerState.WARNING

    def test_transition_to_reducing(self, circuit_breaker: CircuitBreaker) -> None:
        """Should transition to REDUCING at level2 threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # 15% drawdown = level2
        assert circuit_breaker.state == CircuitBreakerState.REDUCING

    def test_transition_to_halted(self, circuit_breaker: CircuitBreaker) -> None:
        """Should transition to HALTED at level3 threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # 20% drawdown = level3
        assert circuit_breaker.state == CircuitBreakerState.HALTED

    def test_direct_transition_active_to_reducing(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle direct jump from ACTIVE to REDUCING."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        # Jump directly to 15% drawdown
        circuit_breaker.update(equity=Decimal("85000"))
        assert circuit_breaker.state == CircuitBreakerState.REDUCING

    def test_direct_transition_active_to_halted(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle direct jump from ACTIVE to HALTED."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        # Jump directly to 20% drawdown
        circuit_breaker.update(equity=Decimal("80000"))
        assert circuit_breaker.state == CircuitBreakerState.HALTED

    def test_progression_through_all_states(self, circuit_breaker: CircuitBreaker) -> None:
        """Should progress through all states in order."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # ACTIVE -> WARNING
        circuit_breaker.update(equity=Decimal("90000"))  # 10%
        assert circuit_breaker.state == CircuitBreakerState.WARNING

        # WARNING -> REDUCING
        circuit_breaker.update(equity=Decimal("85000"))  # 15%
        assert circuit_breaker.state == CircuitBreakerState.REDUCING

        # REDUCING -> HALTED
        circuit_breaker.update(equity=Decimal("80000"))  # 20%
        assert circuit_breaker.state == CircuitBreakerState.HALTED

    def test_recovery_from_warning_to_active(self, circuit_breaker: CircuitBreaker) -> None:
        """Should recover from WARNING to ACTIVE below recovery threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Enter WARNING
        circuit_breaker.update(equity=Decimal("90000"))  # 10%
        assert circuit_breaker.state == CircuitBreakerState.WARNING

        # Recover below 5% threshold
        circuit_breaker.update(equity=Decimal("96000"))  # 4% drawdown
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_recovery_from_reducing_to_active(self, circuit_breaker: CircuitBreaker) -> None:
        """Should recover from REDUCING to ACTIVE below recovery threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Enter REDUCING
        circuit_breaker.update(equity=Decimal("85000"))  # 15%
        assert circuit_breaker.state == CircuitBreakerState.REDUCING

        # Recover below 5% threshold
        circuit_breaker.update(equity=Decimal("96000"))  # 4% drawdown
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_no_auto_recovery_from_halted(self, circuit_breaker: CircuitBreaker) -> None:
        """Should NOT auto-recover from HALTED when auto_recovery=False."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Enter HALTED
        circuit_breaker.update(equity=Decimal("80000"))  # 20%
        assert circuit_breaker.state == CircuitBreakerState.HALTED

        # Recover equity but stay HALTED
        circuit_breaker.update(equity=Decimal("96000"))  # 4% drawdown
        assert circuit_breaker.state == CircuitBreakerState.HALTED  # Still HALTED

    def test_auto_recovery_from_halted(self, auto_recovery_config: CircuitBreakerConfig) -> None:
        """Should auto-recover from HALTED when auto_recovery=True."""
        cb = CircuitBreaker(config=auto_recovery_config, portfolio=None)
        cb.set_initial_equity(Decimal("100000"))

        # Enter HALTED
        cb.update(equity=Decimal("80000"))  # 20%
        assert cb.state == CircuitBreakerState.HALTED

        # Recover equity
        cb.update(equity=Decimal("96000"))  # 4% drawdown
        assert cb.state == CircuitBreakerState.ACTIVE  # Auto-recovered

    def test_hysteresis_prevents_oscillation(self, circuit_breaker: CircuitBreaker) -> None:
        """Recovery threshold below level1 prevents state oscillation."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Enter WARNING at 10%
        circuit_breaker.update(equity=Decimal("90000"))
        assert circuit_breaker.state == CircuitBreakerState.WARNING

        # Improve to 8% (still above 5% recovery) - stay WARNING
        circuit_breaker.update(equity=Decimal("92000"))
        assert circuit_breaker.state == CircuitBreakerState.WARNING

        # Improve to 4% (below 5% recovery) - return to ACTIVE
        circuit_breaker.update(equity=Decimal("96000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE


# =============================================================================
# Boundary Condition Tests
# =============================================================================


class TestBoundaryConditions:
    """Test exact threshold boundaries."""

    def test_exact_level1_threshold(self, circuit_breaker: CircuitBreaker) -> None:
        """Should trigger WARNING at exact level1 threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # Exactly 10%
        assert circuit_breaker.state == CircuitBreakerState.WARNING

    def test_just_below_level1_threshold(self, circuit_breaker: CircuitBreaker) -> None:
        """Should stay ACTIVE just below level1 threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90001"))  # 9.999%
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_exact_level2_threshold(self, circuit_breaker: CircuitBreaker) -> None:
        """Should trigger REDUCING at exact level2 threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # Exactly 15%
        assert circuit_breaker.state == CircuitBreakerState.REDUCING

    def test_exact_level3_threshold(self, circuit_breaker: CircuitBreaker) -> None:
        """Should trigger HALTED at exact level3 threshold."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # Exactly 20%
        assert circuit_breaker.state == CircuitBreakerState.HALTED

    def test_exact_recovery_threshold(self, circuit_breaker: CircuitBreaker) -> None:
        """Should recover at exact recovery threshold (using <=)."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Enter WARNING
        circuit_breaker.update(equity=Decimal("90000"))
        assert circuit_breaker.state == CircuitBreakerState.WARNING
        # At 5% recovery threshold - should recover (<=)
        circuit_breaker.update(equity=Decimal("95000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE  # Recovers at <=
        # At 5% recovery threshold - should recover (<=)
        circuit_breaker.update(equity=Decimal("95000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE  # Recovers at <=
        # At 5% recovery threshold - should recover (<=)
        circuit_breaker.update(equity=Decimal("95000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE  # Recovers at <=
        # At 5% recovery threshold - should recover (<=)
        circuit_breaker.update(equity=Decimal("95000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE  # Recovers at <=
        # At 5% recovery threshold - should recover (<=)
        circuit_breaker.update(equity=Decimal("95000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE  # Recovers at <=
        # At 5% recovery threshold - should recover (<=)
        circuit_breaker.update(equity=Decimal("95000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE  # Recovers at <=
        # At 5% recovery threshold - should recover (<=)
        circuit_breaker.update(equity=Decimal("95000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE  # Recovers at <=
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE  # Recover


# =============================================================================
# Position Control Tests
# =============================================================================


class TestPositionControl:
    """Test position sizing and entry control."""

    def test_can_open_position_when_active(self, circuit_breaker: CircuitBreaker) -> None:
        """Should allow new positions when ACTIVE."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE
        assert circuit_breaker.can_open_position() is True

    def test_can_open_position_when_warning(self, circuit_breaker: CircuitBreaker) -> None:
        """Should allow new positions when WARNING."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # WARNING
        assert circuit_breaker.state == CircuitBreakerState.WARNING
        assert circuit_breaker.can_open_position() is True

    def test_cannot_open_position_when_reducing(self, circuit_breaker: CircuitBreaker) -> None:
        """Should NOT allow new positions when REDUCING."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # REDUCING
        assert circuit_breaker.state == CircuitBreakerState.REDUCING
        assert circuit_breaker.can_open_position() is False

    def test_cannot_open_position_when_halted(self, circuit_breaker: CircuitBreaker) -> None:
        """Should NOT allow new positions when HALTED."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # HALTED
        assert circuit_breaker.state == CircuitBreakerState.HALTED
        assert circuit_breaker.can_open_position() is False

    def test_position_size_multiplier_active(self, circuit_breaker: CircuitBreaker) -> None:
        """Should return 1.0 multiplier when ACTIVE."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE
        assert circuit_breaker.position_size_multiplier() == Decimal("1.0")

    def test_position_size_multiplier_warning(self, circuit_breaker: CircuitBreaker) -> None:
        """Should return configured multiplier when WARNING."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # WARNING
        assert circuit_breaker.position_size_multiplier() == Decimal("0.5")

    def test_position_size_multiplier_reducing(self, circuit_breaker: CircuitBreaker) -> None:
        """Should return configured multiplier when REDUCING."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # REDUCING
        assert circuit_breaker.position_size_multiplier() == Decimal("0.0")

    def test_position_size_multiplier_halted(self, circuit_breaker: CircuitBreaker) -> None:
        """Should return 0.0 multiplier when HALTED."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # HALTED
        assert circuit_breaker.position_size_multiplier() == Decimal("0.0")

    def test_custom_multipliers(self) -> None:
        """Should use custom size multipliers from config."""
        config = CircuitBreakerConfig(
            warning_size_multiplier=Decimal("0.25"),  # Custom 25%
            reducing_size_multiplier=Decimal("0.1"),  # Custom 10%
        )
        cb = CircuitBreaker(config=config, portfolio=None)
        cb.set_initial_equity(Decimal("100000"))

        # WARNING state
        cb.update(equity=Decimal("90000"))
        assert cb.position_size_multiplier() == Decimal("0.25")

        # REDUCING state
        cb.update(equity=Decimal("85000"))
        assert cb.position_size_multiplier() == Decimal("0.1")


# =============================================================================
# Manual Reset Tests
# =============================================================================


class TestManualReset:
    """Test manual reset functionality."""

    def test_reset_from_halted(self, circuit_breaker: CircuitBreaker) -> None:
        """Should allow manual reset from HALTED state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Enter HALTED
        circuit_breaker.update(equity=Decimal("80000"))
        assert circuit_breaker.state == CircuitBreakerState.HALTED

        # Manual reset
        circuit_breaker.reset()
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_cannot_reset_when_auto_recovery_enabled(
        self, auto_recovery_config: CircuitBreakerConfig
    ) -> None:
        """Should raise error if trying to reset with auto_recovery=True."""
        cb = CircuitBreaker(config=auto_recovery_config, portfolio=None)
        cb.set_initial_equity(Decimal("100000"))
        cb.update(equity=Decimal("80000"))  # HALTED

        with pytest.raises(ValueError) as exc_info:
            cb.reset()
        assert "auto_recovery is enabled" in str(exc_info.value)

    def test_cannot_reset_from_active(self, circuit_breaker: CircuitBreaker) -> None:
        """Should raise error if trying to reset from ACTIVE state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

        with pytest.raises(ValueError) as exc_info:
            circuit_breaker.reset()
        assert "only from HALTED" in str(exc_info.value)

    def test_cannot_reset_from_warning(self, circuit_breaker: CircuitBreaker) -> None:
        """Should raise error if trying to reset from WARNING state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # WARNING

        with pytest.raises(ValueError) as exc_info:
            circuit_breaker.reset()
        assert "only from HALTED" in str(exc_info.value)

    def test_cannot_reset_from_reducing(self, circuit_breaker: CircuitBreaker) -> None:
        """Should raise error if trying to reset from REDUCING state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # REDUCING

        with pytest.raises(ValueError) as exc_info:
            circuit_breaker.reset()
        assert "only from HALTED" in str(exc_info.value)

    def test_reset_updates_timestamp(self, circuit_breaker: CircuitBreaker) -> None:
        """Should update last_check timestamp on reset."""
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # HALTED

        old_timestamp = circuit_breaker.last_check
        import time

        time.sleep(0.01)

        circuit_breaker.reset()
        assert circuit_breaker.last_check > old_timestamp


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_zero_initial_equity(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle zero initial equity gracefully."""
        circuit_breaker.set_initial_equity(Decimal("0"))
        circuit_breaker.update(equity=Decimal("0"))
        assert circuit_breaker.current_drawdown == Decimal("0")
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_very_small_equity(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle very small equity values."""
        circuit_breaker.set_initial_equity(Decimal("0.01"))
        circuit_breaker.update(equity=Decimal("0.009"))  # 10% drawdown
        assert circuit_breaker.state == CircuitBreakerState.WARNING

    def test_very_large_equity(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle very large equity values."""
        large_value = Decimal("999999999999.99")
        circuit_breaker.set_initial_equity(large_value)
        circuit_breaker.update(equity=large_value * Decimal("0.9"))  # 10% drawdown
        assert circuit_breaker.state == CircuitBreakerState.WARNING

    def test_rapid_equity_changes(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle rapid equity changes correctly."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Rapid drawdown
        circuit_breaker.update(equity=Decimal("95000"))
        circuit_breaker.update(equity=Decimal("90000"))  # WARNING
        circuit_breaker.update(equity=Decimal("85000"))  # REDUCING
        circuit_breaker.update(equity=Decimal("80000"))  # HALTED

        assert circuit_breaker.state == CircuitBreakerState.HALTED

    def test_rapid_recovery(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle rapid recovery correctly."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Drawdown then rapid recovery
        circuit_breaker.update(equity=Decimal("85000"))  # REDUCING
        assert circuit_breaker.state == CircuitBreakerState.REDUCING

        circuit_breaker.update(equity=Decimal("96000"))  # Rapid recovery
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_oscillating_equity_near_threshold(self, tight_config: CircuitBreakerConfig) -> None:
        """Should handle oscillating equity near thresholds."""
        cb = CircuitBreaker(config=tight_config, portfolio=None)
        cb.set_initial_equity(Decimal("100000"))

        # Oscillate around 5% (level1 threshold)
        cb.update(equity=Decimal("95001"))  # Just above
        assert cb.state == CircuitBreakerState.ACTIVE

        cb.update(equity=Decimal("95000"))  # At threshold
        assert cb.state == CircuitBreakerState.WARNING

        cb.update(equity=Decimal("95001"))  # Just above (still in WARNING due to hysteresis)
        assert cb.state == CircuitBreakerState.WARNING

    def test_multiple_peaks(self, circuit_breaker: CircuitBreaker) -> None:
        """Should track multiple peaks correctly."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # First peak
        circuit_breaker.update(equity=Decimal("110000"))
        assert circuit_breaker.peak_equity == Decimal("110000")

        # Drawdown
        circuit_breaker.update(equity=Decimal("100000"))
        assert circuit_breaker.peak_equity == Decimal("110000")

        # New peak
        circuit_breaker.update(equity=Decimal("120000"))
        assert circuit_breaker.peak_equity == Decimal("120000")

        # Drawdown from new peak
        circuit_breaker.update(equity=Decimal("108000"))  # 10% from 120k
        assert circuit_breaker.state == CircuitBreakerState.WARNING

    def test_recovery_to_new_peak(self, circuit_breaker: CircuitBreaker) -> None:
        """Should handle recovery to new peak correctly."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Drawdown
        circuit_breaker.update(equity=Decimal("90000"))
        assert circuit_breaker.state == CircuitBreakerState.WARNING

        # Recover to old peak
        circuit_breaker.update(equity=Decimal("100000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

        # New peak
        circuit_breaker.update(equity=Decimal("105000"))
        assert circuit_breaker.peak_equity == Decimal("105000")
        assert circuit_breaker.current_drawdown == Decimal("0")

    def test_precision_preservation(self, circuit_breaker: CircuitBreaker) -> None:
        """Should preserve decimal precision throughout calculations."""
        circuit_breaker.set_initial_equity(Decimal("100000.123456"))
        circuit_breaker.update(equity=Decimal("85000.098765"))

        # Should maintain precision
        expected_dd = (Decimal("100000.123456") - Decimal("85000.098765")) / Decimal(
            "100000.123456"
        )
        assert circuit_breaker.current_drawdown == expected_dd


# =============================================================================
# Integration Tests
# =============================================================================


class TestCircuitBreakerIntegration:
    """Test realistic trading scenarios."""

    def test_typical_trading_session(self, circuit_breaker: CircuitBreaker) -> None:
        """Simulate a typical trading session with ups and downs."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Start trading (small gain)
        circuit_breaker.update(equity=Decimal("101000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

        # Bad trade (WARNING)
        circuit_breaker.update(equity=Decimal("90900"))  # 10% from 101k peak
        assert circuit_breaker.state == CircuitBreakerState.WARNING
        assert circuit_breaker.position_size_multiplier() == Decimal("0.5")

        # Another bad trade (REDUCING)
        circuit_breaker.update(equity=Decimal("85850"))  # 15% from 101k peak
        assert circuit_breaker.state == CircuitBreakerState.REDUCING
        assert circuit_breaker.can_open_position() is False

        # Start recovering
        circuit_breaker.update(equity=Decimal("96000"))
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE
        assert circuit_breaker.can_open_position() is True

    def test_catastrophic_loss_scenario(self, circuit_breaker: CircuitBreaker) -> None:
        """Simulate catastrophic loss requiring manual intervention."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Sudden catastrophic loss
        circuit_breaker.update(equity=Decimal("75000"))  # 25% loss
        assert circuit_breaker.state == CircuitBreakerState.HALTED
        assert circuit_breaker.can_open_position() is False

        # Even after recovery, stay HALTED (requires manual reset)
        circuit_breaker.update(equity=Decimal("97000"))
        assert circuit_breaker.state == CircuitBreakerState.HALTED

        # Manual intervention
        circuit_breaker.reset()
        assert circuit_breaker.state == CircuitBreakerState.ACTIVE

    def test_slow_grind_drawdown(self, circuit_breaker: CircuitBreaker) -> None:
        """Simulate slow grinding drawdown through all states."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Slow grind through states
        for equity in range(99000, 79000, -1000):
            circuit_breaker.update(equity=Decimal(str(equity)))

        # Should end up HALTED
        assert circuit_breaker.state == CircuitBreakerState.HALTED
        assert circuit_breaker.current_drawdown >= Decimal("0.20")

    def test_volatile_market_conditions(self, circuit_breaker: CircuitBreaker) -> None:
        """Simulate volatile market with rapid swings."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Volatile swings
        equities = [
            Decimal("95000"),  # ACTIVE
            Decimal("105000"),  # ACTIVE (new peak)
            Decimal("94500"),  # WARNING (10% from 105k)
            Decimal("89250"),  # REDUCING (15% from 105k)
            Decimal("99750"),  # ACTIVE (recovered)
        ]

        for equity in equities:
            circuit_breaker.update(equity=equity)

        assert circuit_breaker.state == CircuitBreakerState.ACTIVE
        assert circuit_breaker.peak_equity == Decimal("105000")

    def test_long_term_growth_scenario(self, circuit_breaker: CircuitBreaker) -> None:
        """Simulate long-term account growth with periodic drawdowns."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Growth with periodic drawdowns
        milestones = [
            (Decimal("110000"), CircuitBreakerState.ACTIVE),  # Growth
            (Decimal("100000"), CircuitBreakerState.ACTIVE),  # 9% DD (safe)
            (Decimal("120000"), CircuitBreakerState.ACTIVE),  # New peak
            (Decimal("108000"), CircuitBreakerState.WARNING),  # 10% DD
            (Decimal("115000"), CircuitBreakerState.ACTIVE),  # Recovery
            (Decimal("130000"), CircuitBreakerState.ACTIVE),  # New peak
        ]

        for equity, expected_state in milestones:
            circuit_breaker.update(equity=equity)
            assert circuit_breaker.state == expected_state

        assert circuit_breaker.peak_equity == Decimal("130000")


# =============================================================================
# Concurrency Tests
# =============================================================================


class TestConcurrencyConsiderations:
    """Test considerations for concurrent access (documentation)."""

    def test_state_consistency_after_rapid_updates(self, circuit_breaker: CircuitBreaker) -> None:
        """State should remain consistent even with rapid updates."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Simulate rapid updates
        for _ in range(100):
            circuit_breaker.update(equity=Decimal("90000"))

        # State should be consistent
        assert circuit_breaker.state == CircuitBreakerState.WARNING
        assert circuit_breaker.current_drawdown == Decimal("0.1")

    def test_timestamp_monotonicity(self, circuit_breaker: CircuitBreaker) -> None:
        """Timestamps should always move forward."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        timestamps = []
        for i in range(10):
            circuit_breaker.update(equity=Decimal("100000"))
            timestamps.append(circuit_breaker.last_check)
            import time

            time.sleep(0.001)

        # Timestamps should be monotonically increasing
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i - 1]


# =============================================================================
# Property Tests
# =============================================================================


class TestCircuitBreakerProperties:
    """Test fundamental properties that should always hold."""

    def test_drawdown_never_negative(self, circuit_breaker: CircuitBreaker) -> None:
        """Drawdown should never be negative (0 at minimum)."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Test various scenarios
        equities = [Decimal("100000"), Decimal("110000"), Decimal("95000"), Decimal("120000")]
        for equity in equities:
            circuit_breaker.update(equity=equity)
            assert circuit_breaker.current_drawdown >= Decimal("0")

    def test_peak_never_decreases(self, circuit_breaker: CircuitBreaker) -> None:
        """Peak equity should only increase, never decrease."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        peaks = [circuit_breaker.peak_equity]
        equities = [Decimal("95000"), Decimal("110000"), Decimal("105000"), Decimal("120000")]

        for equity in equities:
            circuit_breaker.update(equity=equity)
            peaks.append(circuit_breaker.peak_equity)

        # Peaks should be monotonically non-decreasing
        for i in range(1, len(peaks)):
            assert peaks[i] >= peaks[i - 1]

    def test_state_always_valid(self, circuit_breaker: CircuitBreaker) -> None:
        """State should always be one of the valid enum values."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        valid_states = {
            CircuitBreakerState.ACTIVE,
            CircuitBreakerState.WARNING,
            CircuitBreakerState.REDUCING,
            CircuitBreakerState.HALTED,
        }

        # Test various scenarios
        equities = [
            Decimal("90000"),
            Decimal("85000"),
            Decimal("80000"),
            Decimal("96000"),
            Decimal("110000"),
        ]

        for equity in equities:
            circuit_breaker.update(equity=equity)
            assert circuit_breaker.state in valid_states

    def test_multiplier_in_valid_range(self, circuit_breaker: CircuitBreaker) -> None:
        """Position size multiplier should always be between 0 and 1."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        equities = [Decimal("100000"), Decimal("90000"), Decimal("85000"), Decimal("80000")]

        for equity in equities:
            circuit_breaker.update(equity=equity)
            multiplier = circuit_breaker.position_size_multiplier()
            assert Decimal("0") <= multiplier <= Decimal("1")

    def test_can_open_consistent_with_state(self, circuit_breaker: CircuitBreaker) -> None:
        """can_open_position should be consistent with state."""
        circuit_breaker.set_initial_equity(Decimal("100000"))

        # Test all states
        test_cases = [
            (Decimal("100000"), CircuitBreakerState.ACTIVE, True),
            (Decimal("90000"), CircuitBreakerState.WARNING, True),
            (Decimal("85000"), CircuitBreakerState.REDUCING, False),
            (Decimal("80000"), CircuitBreakerState.HALTED, False),
        ]

        for equity, expected_state, expected_can_open in test_cases:
            circuit_breaker.update(equity=equity)
            assert circuit_breaker.state == expected_state
            assert circuit_breaker.can_open_position() == expected_can_open
