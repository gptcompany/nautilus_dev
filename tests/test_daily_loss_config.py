"""Tests for DailyLossConfig (Spec 013)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from risk.daily_loss_config import DailyLossConfig


class TestDailyLossConfigValidation:
    """Test DailyLossConfig validation rules."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DailyLossConfig()
        assert config.daily_loss_limit == Decimal("1000")
        assert config.daily_loss_pct is None
        assert config.reset_time_utc == "00:00"
        assert config.per_strategy is False
        assert config.close_positions_on_limit is True
        assert config.warning_threshold_pct == Decimal("0.5")

    def test_custom_absolute_limit(self):
        """Test custom absolute loss limit."""
        config = DailyLossConfig(daily_loss_limit=Decimal("500"))
        assert config.daily_loss_limit == Decimal("500")

    def test_percentage_limit(self):
        """Test percentage-based loss limit."""
        config = DailyLossConfig(daily_loss_pct=Decimal("0.02"))
        assert config.daily_loss_pct == Decimal("0.02")

    def test_daily_loss_limit_must_be_positive(self):
        """Test that daily_loss_limit must be > 0."""
        with pytest.raises(ValidationError) as exc_info:
            DailyLossConfig(daily_loss_limit=Decimal("-100"))
        assert "greater than 0" in str(exc_info.value)

    def test_daily_loss_limit_zero_rejected(self):
        """Test that daily_loss_limit cannot be 0."""
        with pytest.raises(ValidationError) as exc_info:
            DailyLossConfig(daily_loss_limit=Decimal("0"))
        assert "greater than 0" in str(exc_info.value)

    def test_daily_loss_pct_must_be_between_0_and_1(self):
        """Test that daily_loss_pct must be in (0, 1) range."""
        with pytest.raises(ValidationError):
            DailyLossConfig(daily_loss_pct=Decimal("1.5"))

        with pytest.raises(ValidationError):
            DailyLossConfig(daily_loss_pct=Decimal("-0.1"))

    def test_daily_loss_pct_boundary_rejected(self):
        """Test that daily_loss_pct cannot be 0 or 1."""
        with pytest.raises(ValidationError):
            DailyLossConfig(daily_loss_pct=Decimal("0"))

        with pytest.raises(ValidationError):
            DailyLossConfig(daily_loss_pct=Decimal("1"))

    def test_warning_threshold_pct_must_be_between_0_and_1(self):
        """Test warning_threshold_pct validation."""
        with pytest.raises(ValidationError):
            DailyLossConfig(warning_threshold_pct=Decimal("1.5"))


class TestResetTimeValidation:
    """Test reset_time_utc format validation."""

    def test_valid_reset_times(self):
        """Test valid HH:MM formats."""
        valid_times = ["00:00", "12:30", "23:59", "09:00"]
        for time in valid_times:
            config = DailyLossConfig(reset_time_utc=time)
            assert config.reset_time_utc == time

    def test_invalid_reset_time_format(self):
        """Test that invalid formats are rejected."""
        invalid_times = ["24:00", "12:60", "1:30", "12:3", "invalid", "12-30", ""]
        for time in invalid_times:
            with pytest.raises(ValidationError) as exc_info:
                DailyLossConfig(reset_time_utc=time)
            assert "HH:MM format" in str(exc_info.value)

    def test_reset_time_24_hour_rejected(self):
        """Test that 24:00 is not valid."""
        with pytest.raises(ValidationError):
            DailyLossConfig(reset_time_utc="24:00")


class TestGetEffectiveLimit:
    """Test get_effective_limit() method."""

    def test_absolute_limit_returned_when_no_pct(self):
        """Test that absolute limit is used when percentage not set."""
        config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
        starting_equity = Decimal("50000")
        assert config.get_effective_limit(starting_equity) == Decimal("1000")

    def test_percentage_limit_takes_precedence(self):
        """Test that percentage limit is used when set."""
        config = DailyLossConfig(
            daily_loss_limit=Decimal("1000"),
            daily_loss_pct=Decimal("0.02"),
        )
        starting_equity = Decimal("50000")
        # 2% of 50000 = 1000
        assert config.get_effective_limit(starting_equity) == Decimal("1000")

    def test_percentage_calculation(self):
        """Test correct percentage calculation."""
        config = DailyLossConfig(daily_loss_pct=Decimal("0.05"))
        starting_equity = Decimal("100000")
        # 5% of 100000 = 5000
        assert config.get_effective_limit(starting_equity) == Decimal("5000")


class TestConfigImmutability:
    """Test config assignment validation."""

    def test_assignment_validation_enabled(self):
        """Test that assignment triggers validation."""
        config = DailyLossConfig()
        # Valid assignment should work
        config.daily_loss_limit = Decimal("500")
        assert config.daily_loss_limit == Decimal("500")

        # Invalid assignment should fail
        with pytest.raises(ValidationError):
            config.daily_loss_limit = Decimal("-100")
