"""Unit tests for comparison validator.

Tests for:
    - ComparisonValidator
    - Multi-contender window execution
    - ContenderResult aggregation

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations


import pytest


class TestComparisonValidatorInit:
    """Tests for ComparisonValidator initialization."""

    def test_init_with_config(self) -> None:
        """Test initialization with config."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        assert validator.config is config

    def test_init_with_registry(self) -> None:
        """Test initialization with custom registry."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig
        from scripts.baseline_validation.registry import ContenderRegistry

        config = BaselineValidationConfig.default()
        registry = ContenderRegistry.default()
        validator = ComparisonValidator(config, registry=registry)

        assert len(validator.contenders) == 3


class TestComparisonValidatorWindowGeneration:
    """Tests for walk-forward window generation."""

    def test_generates_windows(self) -> None:
        """Test that validator generates walk-forward windows."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        windows = validator.generate_windows()

        assert len(windows) >= config.validation.min_windows

    def test_windows_have_no_overlap(self) -> None:
        """Test that train and test periods don't overlap."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        windows = validator.generate_windows()

        for window in windows:
            # Train must end before test starts
            assert window.train_end <= window.test_start


class TestComparisonValidatorExecution:
    """Tests for multi-contender execution."""

    def test_run_returns_results_for_all_contenders(self) -> None:
        """Test that run returns results for all contenders."""
        from scripts.baseline_validation.comparison_validator import (
            ComparisonValidator,
            ValidationRun,
        )
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        # Run with mock data (won't actually run backtests)
        result = validator.run_mock()

        assert isinstance(result, ValidationRun)
        assert len(result.contender_results) == 3

    def test_contender_results_have_metrics(self) -> None:
        """Test that each contender result has required metrics."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        result = validator.run_mock()

        for name, contender_result in result.contender_results.items():
            assert hasattr(contender_result, "avg_sharpe")
            assert hasattr(contender_result, "max_drawdown")
            assert hasattr(contender_result, "window_results")


class TestContenderResultAggregation:
    """Tests for ContenderResult aggregation across windows."""

    def test_aggregates_sharpe_across_windows(self) -> None:
        """Test Sharpe ratio aggregation."""
        from scripts.baseline_validation.comparison_validator import ContenderResult

        # Create mock window results
        sharpes = [1.0, 1.5, 0.8, 1.2]

        result = ContenderResult(
            name="test",
            window_sharpes=sharpes,
            window_returns=[0.1, 0.15, 0.08, 0.12],
            window_drawdowns=[0.1, 0.12, 0.15, 0.11],
            window_trade_counts=[50, 45, 55, 48],
        )

        expected_avg = sum(sharpes) / len(sharpes)
        assert result.avg_sharpe == pytest.approx(expected_avg)

    def test_calculates_max_drawdown(self) -> None:
        """Test max drawdown calculation."""
        from scripts.baseline_validation.comparison_validator import ContenderResult

        drawdowns = [0.10, 0.15, 0.12, 0.18]

        result = ContenderResult(
            name="test",
            window_sharpes=[1.0] * 4,
            window_returns=[0.1] * 4,
            window_drawdowns=drawdowns,
            window_trade_counts=[50] * 4,
        )

        assert result.max_drawdown == pytest.approx(0.18)

    def test_handles_empty_windows(self) -> None:
        """Test handling of empty window list."""
        from scripts.baseline_validation.comparison_validator import ContenderResult

        result = ContenderResult(
            name="test",
            window_sharpes=[],
            window_returns=[],
            window_drawdowns=[],
            window_trade_counts=[],
        )

        assert result.avg_sharpe == 0.0
        assert result.max_drawdown == 0.0


class TestValidationRun:
    """Tests for ValidationRun result container."""

    def test_has_comparison_metrics(self) -> None:
        """Test that ValidationRun includes comparison metrics."""
        from scripts.baseline_validation.comparison_validator import (
            ComparisonValidator,
        )
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        result = validator.run_mock()

        assert hasattr(result, "comparison")
        assert result.comparison is not None

    def test_determines_winner(self) -> None:
        """Test that ValidationRun determines a winner."""
        from scripts.baseline_validation.comparison_validator import (
            ComparisonValidator,
        )
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        result = validator.run_mock()

        assert result.best_contender in ["adaptive", "fixed", "buyhold"]
