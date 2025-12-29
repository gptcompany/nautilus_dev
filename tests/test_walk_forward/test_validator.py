"""Tests for WalkForwardValidator."""

from datetime import datetime

import pytest

from scripts.alpha_evolve.walk_forward.config import WalkForwardConfig
from scripts.alpha_evolve.walk_forward.validator import WalkForwardValidator


class TestValidatorIntegration:
    """Integration tests with mock evaluator."""

    @pytest.mark.asyncio
    async def test_validate_returns_correct_window_count(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test validate() returns correct number of WindowResults."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        assert len(result.windows) >= sample_config.min_windows

    @pytest.mark.asyncio
    async def test_validate_tracks_timing(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test validation_time_seconds is tracked."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        assert result.validation_time_seconds > 0

    @pytest.mark.asyncio
    async def test_validate_calculates_robustness_score(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test robustness score is calculated."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        assert 0 <= result.robustness_score <= 100

    @pytest.mark.asyncio
    async def test_validate_calculates_advanced_metrics(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test advanced metrics (DSR, PBO) are calculated."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        assert result.deflated_sharpe_ratio is not None
        assert result.probability_backtest_overfitting is not None
        assert 0 <= result.probability_backtest_overfitting <= 1


class TestPassFailCriteria:
    """Test pass/fail criteria logic."""

    @pytest.mark.asyncio
    async def test_passing_scenario(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test passing scenario with all criteria met."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        # Mock evaluator returns good metrics
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_failing_low_robustness_score(self, mock_evaluator) -> None:
        """Test failure when robustness score is too low."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=3,
            min_windows=4,
            min_robustness_score=99.0,  # Impossibly high threshold
        )

        validator = WalkForwardValidator(config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_failing_excessive_drawdown(self, failing_evaluator) -> None:
        """Test failure when drawdown exceeds threshold."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=3,
            min_windows=4,
            max_drawdown_threshold=0.30,  # Failing evaluator returns 0.35
        )

        validator = WalkForwardValidator(config, failing_evaluator)
        result = await validator.validate("test_strategy_code")

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_failing_too_few_profitable_windows(self, failing_evaluator) -> None:
        """Test failure when too few windows are profitable."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=3,
            min_windows=4,
            min_profitable_windows_pct=0.75,  # Failing evaluator has negative returns
            max_drawdown_threshold=1.0,  # Disable DD check
        )

        validator = WalkForwardValidator(config, failing_evaluator)
        result = await validator.validate("test_strategy_code")

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_failing_low_test_sharpe(self, failing_evaluator) -> None:
        """Test failure when test Sharpe is too low."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=3,
            min_windows=4,
            min_test_sharpe=0.5,  # Failing evaluator returns 0.2
            max_drawdown_threshold=1.0,  # Disable DD check
            min_profitable_windows_pct=0.01,  # Disable profit check
        )

        validator = WalkForwardValidator(config, failing_evaluator)
        result = await validator.validate("test_strategy_code")

        # Should fail on Sharpe criterion (majority need >= 0.5)
        assert result.passed is False


class TestWindowResultProperties:
    """Test WindowResult computed properties."""

    @pytest.mark.asyncio
    async def test_degradation_ratio_calculated(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test degradation_ratio is calculated for each window."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        for window_result in result.windows:
            # degradation = test_sharpe / train_sharpe
            expected = (
                window_result.test_metrics.sharpe_ratio
                / window_result.train_metrics.sharpe_ratio
            )
            assert abs(window_result.degradation_ratio - expected) < 0.01


class TestWalkForwardResultProperties:
    """Test WalkForwardResult computed properties."""

    @pytest.mark.asyncio
    async def test_profitable_windows_pct(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test profitable_windows_pct property."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        # Mock evaluator returns positive returns
        assert result.profitable_windows_pct == 1.0

    @pytest.mark.asyncio
    async def test_avg_test_sharpe(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test avg_test_sharpe property."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        # Mock evaluator returns 0.75 test sharpe
        assert abs(result.avg_test_sharpe - 0.75) < 0.01

    @pytest.mark.asyncio
    async def test_worst_drawdown(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test worst_drawdown property."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        # Mock evaluator returns 0.15 drawdown
        assert abs(result.worst_drawdown - 0.15) < 0.01

    @pytest.mark.asyncio
    async def test_avg_degradation(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test avg_degradation property."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        # Should be test_sharpe (0.75) / train_sharpe (1.3)
        expected = 0.75 / 1.3
        assert abs(result.avg_degradation - expected) < 0.1
