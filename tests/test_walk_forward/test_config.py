"""Tests for WalkForwardConfig validation."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from scripts.alpha_evolve.walk_forward.config import WalkForwardConfig


class TestWalkForwardConfigCreation:
    """Test valid config creation."""

    def test_valid_config_with_defaults(self) -> None:
        """Test creating config with default values."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
        )
        assert config.train_months == 6
        assert config.test_months == 3
        assert config.step_months == 3
        assert config.embargo_before_days == 5
        assert config.embargo_after_days == 3
        assert config.min_windows == 4
        assert config.min_profitable_windows_pct == 0.75
        assert config.min_test_sharpe == 0.5
        assert config.max_drawdown_threshold == 0.30
        assert config.min_robustness_score == 60.0
        assert config.seed is None

    def test_valid_config_with_custom_values(self) -> None:
        """Test creating config with all custom values."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=8,
            test_months=4,
            step_months=2,
            embargo_before_days=7,
            embargo_after_days=5,
            min_windows=3,
            min_profitable_windows_pct=0.80,
            min_test_sharpe=0.7,
            max_drawdown_threshold=0.25,
            min_robustness_score=70.0,
            seed=42,
        )
        assert config.train_months == 8
        assert config.test_months == 4
        assert config.step_months == 2
        assert config.embargo_before_days == 7
        assert config.embargo_after_days == 5
        assert config.min_windows == 3
        assert config.min_profitable_windows_pct == 0.80
        assert config.min_test_sharpe == 0.7
        assert config.max_drawdown_threshold == 0.25
        assert config.min_robustness_score == 70.0
        assert config.seed == 42

    def test_minimal_config(self) -> None:
        """Test config with minimal data range."""
        # 2 windows with 3-month train, 2-month test, 2-month step
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2023, 10, 1),
            train_months=3,
            test_months=2,
            step_months=2,
            embargo_before_days=0,
            embargo_after_days=0,
            min_windows=2,
        )
        assert config.min_windows == 2


class TestWalkForwardConfigValidationErrors:
    """Test validation error cases."""

    def test_error_start_after_end(self) -> None:
        """Test error when data_start >= data_end."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2024, 1, 1),
                data_end=datetime(2023, 1, 1),
            )
        assert "data_end must be after data_start" in str(exc_info.value)

    def test_error_start_equals_end(self) -> None:
        """Test error when data_start == data_end."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2023, 1, 1),
            )
        assert "data_end must be after data_start" in str(exc_info.value)

    def test_error_negative_train_months(self) -> None:
        """Test error with negative train_months."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2024, 12, 1),
                train_months=-1,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_error_zero_train_months(self) -> None:
        """Test error with zero train_months."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2024, 12, 1),
                train_months=0,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_error_negative_embargo(self) -> None:
        """Test error with negative embargo days."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2024, 12, 1),
                embargo_before_days=-1,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_error_min_windows_too_low(self) -> None:
        """Test error when min_windows < 2."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2024, 12, 1),
                min_windows=1,
            )
        assert "greater than or equal to 2" in str(exc_info.value)

    def test_error_profitable_pct_too_high(self) -> None:
        """Test error when min_profitable_windows_pct > 1.0."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2024, 12, 1),
                min_profitable_windows_pct=1.5,
            )
        assert "less than or equal to 1" in str(exc_info.value)

    def test_error_profitable_pct_zero(self) -> None:
        """Test error when min_profitable_windows_pct <= 0."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2024, 12, 1),
                min_profitable_windows_pct=0,
            )
        assert "greater than 0" in str(exc_info.value)

    def test_error_max_drawdown_too_high(self) -> None:
        """Test error when max_drawdown_threshold > 1.0."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2024, 12, 1),
                max_drawdown_threshold=1.5,
            )
        assert "less than or equal to 1" in str(exc_info.value)

    def test_error_robustness_score_over_100(self) -> None:
        """Test error when min_robustness_score > 100."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2024, 12, 1),
                min_robustness_score=150,
            )
        assert "less than or equal to 100" in str(exc_info.value)

    def test_error_insufficient_data(self) -> None:
        """Test error when data range too short for min_windows."""
        with pytest.raises(ValidationError) as exc_info:
            WalkForwardConfig(
                data_start=datetime(2023, 1, 1),
                data_end=datetime(2023, 6, 1),  # Only 5 months
                train_months=6,
                test_months=3,
                min_windows=4,
            )
        assert "Insufficient data" in str(exc_info.value)


class TestWalkForwardConfigDefaults:
    """Test default values match spec."""

    def test_defaults_match_spec(self) -> None:
        """Verify defaults match spec.md requirements."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
        )
        # From spec.md FR-002
        assert config.train_months == 6
        assert config.test_months == 3
        assert config.step_months == 3
        # From plan.md Decision 4
        assert config.embargo_before_days == 5
        assert config.embargo_after_days == 3
        # From spec.md FR-005
        assert config.min_robustness_score == 60.0
        assert config.min_profitable_windows_pct == 0.75
        assert config.min_test_sharpe == 0.5
        assert config.max_drawdown_threshold == 0.30
