"""
Unit tests for CircuitBreakerConfig.

Tests cover:
- T005: CircuitBreakerConfig validation
  - Threshold ordering (level1 < level2 < level3)
  - Recovery hysteresis (recovery < level1)
  - Percentage range validation
  - Multiplier range validation
  - Interval validation
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from risk import CircuitBreakerConfig


class TestCircuitBreakerConfigDefaults:
    """Test default configuration values."""

    def test_default_values(self) -> None:
        """Default config should have sensible defaults."""
        config = CircuitBreakerConfig()

        assert config.level1_drawdown_pct == Decimal("0.10")  # 10%
        assert config.level2_drawdown_pct == Decimal("0.15")  # 15%
        assert config.level3_drawdown_pct == Decimal("0.20")  # 20%
        assert config.recovery_drawdown_pct == Decimal("0.05")  # 5%
        assert config.auto_recovery is False
        assert config.check_interval_secs == 60
        assert config.warning_size_multiplier == Decimal("0.5")
        assert config.reducing_size_multiplier == Decimal("0.0")

    def test_config_is_frozen(self) -> None:
        """Config should be immutable."""
        config = CircuitBreakerConfig()

        with pytest.raises(ValidationError):
            config.level1_drawdown_pct = Decimal("0.05")


class TestThresholdOrdering:
    """Test threshold ordering validation."""

    def test_valid_threshold_ordering(self) -> None:
        """Should accept valid threshold ordering."""
        config = CircuitBreakerConfig(
            level1_drawdown_pct=Decimal("0.10"),
            level2_drawdown_pct=Decimal("0.15"),
            level3_drawdown_pct=Decimal("0.20"),
        )
        assert config.level1_drawdown_pct < config.level2_drawdown_pct
        assert config.level2_drawdown_pct < config.level3_drawdown_pct

    def test_rejects_level1_equal_level2(self) -> None:
        """Should reject level1 == level2."""
        with pytest.raises(ValidationError, match="ordered"):
            CircuitBreakerConfig(
                level1_drawdown_pct=Decimal("0.15"),
                level2_drawdown_pct=Decimal("0.15"),
                level3_drawdown_pct=Decimal("0.20"),
            )

    def test_rejects_level1_greater_level2(self) -> None:
        """Should reject level1 > level2."""
        with pytest.raises(ValidationError, match="ordered"):
            CircuitBreakerConfig(
                level1_drawdown_pct=Decimal("0.20"),
                level2_drawdown_pct=Decimal("0.15"),
                level3_drawdown_pct=Decimal("0.25"),
            )

    def test_rejects_level2_greater_level3(self) -> None:
        """Should reject level2 > level3."""
        with pytest.raises(ValidationError, match="ordered"):
            CircuitBreakerConfig(
                level1_drawdown_pct=Decimal("0.10"),
                level2_drawdown_pct=Decimal("0.30"),
                level3_drawdown_pct=Decimal("0.20"),
            )


class TestRecoveryHysteresis:
    """Test recovery threshold hysteresis validation."""

    def test_valid_recovery_below_level1(self) -> None:
        """Should accept recovery < level1."""
        config = CircuitBreakerConfig(
            level1_drawdown_pct=Decimal("0.10"),
            recovery_drawdown_pct=Decimal("0.05"),
        )
        assert config.recovery_drawdown_pct < config.level1_drawdown_pct

    def test_rejects_recovery_equal_level1(self) -> None:
        """Should reject recovery == level1."""
        with pytest.raises(ValidationError, match="hysteresis"):
            CircuitBreakerConfig(
                level1_drawdown_pct=Decimal("0.10"),
                recovery_drawdown_pct=Decimal("0.10"),
            )

    def test_rejects_recovery_greater_level1(self) -> None:
        """Should reject recovery > level1."""
        with pytest.raises(ValidationError, match="hysteresis"):
            CircuitBreakerConfig(
                level1_drawdown_pct=Decimal("0.10"),
                recovery_drawdown_pct=Decimal("0.15"),
            )


class TestPercentageValidation:
    """Test percentage range validation."""

    def test_rejects_percentage_zero(self) -> None:
        """Should reject percentage = 0."""
        with pytest.raises(ValidationError, match="between 0 and 1"):
            CircuitBreakerConfig(level1_drawdown_pct=Decimal("0"))

    def test_rejects_percentage_one(self) -> None:
        """Should reject percentage = 1."""
        with pytest.raises(ValidationError, match="between 0 and 1"):
            CircuitBreakerConfig(level3_drawdown_pct=Decimal("1.0"))

    def test_rejects_negative_percentage(self) -> None:
        """Should reject negative percentage."""
        with pytest.raises(ValidationError, match="between 0 and 1"):
            CircuitBreakerConfig(level1_drawdown_pct=Decimal("-0.10"))

    def test_rejects_percentage_greater_than_one(self) -> None:
        """Should reject percentage > 1."""
        with pytest.raises(ValidationError, match="between 0 and 1"):
            CircuitBreakerConfig(level3_drawdown_pct=Decimal("1.5"))


class TestMultiplierValidation:
    """Test multiplier range validation."""

    def test_accepts_multiplier_zero(self) -> None:
        """Should accept multiplier = 0."""
        config = CircuitBreakerConfig(reducing_size_multiplier=Decimal("0"))
        assert config.reducing_size_multiplier == Decimal("0")

    def test_accepts_multiplier_one(self) -> None:
        """Should accept multiplier = 1."""
        config = CircuitBreakerConfig(warning_size_multiplier=Decimal("1.0"))
        assert config.warning_size_multiplier == Decimal("1.0")

    def test_rejects_multiplier_negative(self) -> None:
        """Should reject negative multiplier."""
        with pytest.raises(ValidationError, match="between 0 and 1"):
            CircuitBreakerConfig(warning_size_multiplier=Decimal("-0.5"))

    def test_rejects_multiplier_greater_than_one(self) -> None:
        """Should reject multiplier > 1."""
        with pytest.raises(ValidationError, match="between 0 and 1"):
            CircuitBreakerConfig(warning_size_multiplier=Decimal("1.5"))


class TestIntervalValidation:
    """Test check interval validation."""

    def test_accepts_positive_interval(self) -> None:
        """Should accept positive interval."""
        config = CircuitBreakerConfig(check_interval_secs=30)
        assert config.check_interval_secs == 30

    def test_rejects_zero_interval(self) -> None:
        """Should reject zero interval."""
        with pytest.raises(ValidationError, match="positive"):
            CircuitBreakerConfig(check_interval_secs=0)

    def test_rejects_negative_interval(self) -> None:
        """Should reject negative interval."""
        with pytest.raises(ValidationError, match="positive"):
            CircuitBreakerConfig(check_interval_secs=-10)
