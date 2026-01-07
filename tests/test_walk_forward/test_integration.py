"""Integration tests for walk-forward validation pipeline."""

import json
from datetime import datetime

import pytest

from scripts.alpha_evolve.walk_forward.config import WalkForwardConfig
from scripts.alpha_evolve.walk_forward.report import export_json, generate_report
from scripts.alpha_evolve.walk_forward.validator import WalkForwardValidator


class TestFullPipeline:
    """Test complete validation pipeline."""

    @pytest.mark.asyncio
    async def test_full_validation_pipeline(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test complete pipeline from config to result."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        # Verify result has all expected fields
        assert result.config == sample_config
        assert len(result.windows) >= 4
        assert 0 <= result.robustness_score <= 100
        assert isinstance(result.passed, bool)
        assert result.validation_time_seconds > 0

    @pytest.mark.asyncio
    async def test_report_generation(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test markdown report generation."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        report = generate_report(result)

        # Verify report structure
        assert "# Walk-Forward Validation Report" in report
        assert "## Summary" in report
        assert "## Key Metrics" in report
        assert "## Window Results" in report
        assert "## Configuration" in report
        assert "Robustness Score" in report

        # Verify status indicator
        if result.passed:
            assert "✅ PASSED" in report
        else:
            assert "❌ FAILED" in report

    @pytest.mark.asyncio
    async def test_json_export(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test JSON export is valid and contains expected data."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        json_str = export_json(result)
        data = json.loads(json_str)

        # Verify structure
        assert "summary" in data
        assert "advanced_metrics" in data
        assert "config" in data
        assert "windows" in data
        assert "generated_at" in data

        # Verify summary
        assert "passed" in data["summary"]
        assert "robustness_score" in data["summary"]
        assert "profitable_windows_pct" in data["summary"]

        # Verify windows
        assert len(data["windows"]) >= 4
        for window in data["windows"]:
            assert "window_id" in window
            assert "train_metrics" in window
            assert "test_metrics" in window
            assert "degradation_ratio" in window

    @pytest.mark.asyncio
    async def test_pipeline_with_failing_strategy(
        self,
        failing_evaluator,
    ) -> None:
        """Test pipeline correctly identifies failing strategy."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=3,
            min_windows=4,
            max_drawdown_threshold=0.30,  # Failing evaluator exceeds this
        )

        validator = WalkForwardValidator(config, failing_evaluator)
        result = await validator.validate("test_strategy_code")

        assert result.passed is False

        # Verify report shows failure
        report = generate_report(result)
        assert "❌ FAILED" in report


class TestEdgeCases:
    """Test edge cases in the pipeline."""

    @pytest.mark.asyncio
    async def test_minimal_windows(
        self,
        minimal_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test with minimal number of windows."""
        validator = WalkForwardValidator(minimal_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        assert len(result.windows) >= 2

    @pytest.mark.asyncio
    async def test_zero_embargo(self, mock_evaluator) -> None:
        """Test with zero embargo periods."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=0,
            embargo_after_days=0,
            min_windows=4,
        )

        validator = WalkForwardValidator(config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        # Verify no gap between train and test
        for window_result in result.windows:
            gap = (window_result.window.test_start - window_result.window.train_end).days
            assert gap == 0

    @pytest.mark.asyncio
    async def test_large_embargo(self, mock_evaluator) -> None:
        """Test with large embargo periods."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=30,  # Large embargo
            embargo_after_days=14,
            min_windows=2,  # Fewer windows due to data loss
        )

        validator = WalkForwardValidator(config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        # Verify embargo applied
        for window_result in result.windows:
            gap = (window_result.window.test_start - window_result.window.train_end).days
            assert gap == 30


class TestAdvancedMetrics:
    """Test advanced overfitting metrics."""

    @pytest.mark.asyncio
    async def test_deflated_sharpe_less_than_raw(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test DSR is always <= raw Sharpe."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        # DSR should be less than average test Sharpe
        if result.deflated_sharpe_ratio is not None:
            assert result.deflated_sharpe_ratio <= result.avg_test_sharpe + 0.01

    @pytest.mark.asyncio
    async def test_pbo_bounds(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test PBO is between 0 and 1."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        if result.probability_backtest_overfitting is not None:
            assert 0 <= result.probability_backtest_overfitting <= 1

    @pytest.mark.asyncio
    async def test_advanced_metrics_in_report(
        self,
        sample_config: WalkForwardConfig,
        mock_evaluator,
    ) -> None:
        """Test advanced metrics appear in report."""
        validator = WalkForwardValidator(sample_config, mock_evaluator)
        result = await validator.validate("test_strategy_code")

        report = generate_report(result)

        assert "Deflated Sharpe Ratio" in report
        assert "Probability of Backtest Overfitting" in report
        assert "Lopez de Prado" in report
