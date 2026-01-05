"""Integration tests for full pipeline.

Tests for:
    - End-to-end validation flow
    - Component interaction
    - Data flow integrity

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations

from datetime import datetime

import pytest


class TestEndToEndValidation:
    """Tests for complete validation flow."""

    def test_complete_validation_pipeline(self) -> None:
        """Test complete validation from config to report."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig
        from scripts.baseline_validation.report import (
            create_report_from_validation_run,
            export_to_json,
            generate_markdown_report,
        )

        # Setup
        config = BaselineValidationConfig.default()
        config.seed = 42

        # Run validation
        validator = ComparisonValidator(config)
        result = validator.run_mock()

        # Generate report
        report = create_report_from_validation_run(result)

        # Verify report content
        assert report.verdict is not None
        assert report.confidence >= 0
        assert len(report.contender_summaries) >= 2

        # Generate outputs
        markdown = generate_markdown_report(report)
        json_str = export_to_json(report)

        # Verify outputs
        assert "Baseline Validation" in markdown
        assert "verdict" in json_str.lower()

    def test_reproducibility(self) -> None:
        """Test that same config + seed produces same results."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig
        from scripts.baseline_validation.report import create_report_from_validation_run

        config1 = BaselineValidationConfig.default()
        config1.seed = 123

        config2 = BaselineValidationConfig.default()
        config2.seed = 123

        validator1 = ComparisonValidator(config1)
        validator2 = ComparisonValidator(config2)

        result1 = validator1.run_mock()
        result2 = validator2.run_mock()

        report1 = create_report_from_validation_run(result1)
        report2 = create_report_from_validation_run(result2)

        assert report1.verdict == report2.verdict
        assert report1.contender_summaries["adaptive"].avg_sharpe == pytest.approx(
            report2.contender_summaries["adaptive"].avg_sharpe
        )


class TestComponentInteraction:
    """Tests for component interaction."""

    def test_sizer_to_validator_integration(self) -> None:
        """Test sizers work correctly with validator."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig
        from scripts.baseline_validation.registry import ContenderRegistry

        config = BaselineValidationConfig.default()
        registry = ContenderRegistry.default()

        validator = ComparisonValidator(config, registry=registry)

        # Should have all contenders
        assert "adaptive" in validator.contenders
        assert "fixed" in validator.contenders
        assert "buyhold" in validator.contenders

    def test_validator_to_report_integration(self) -> None:
        """Test validation results work with report generation."""
        from scripts.baseline_validation.comparison_validator import (
            ComparisonValidator,
            ContenderResult,
            ValidationRun,
        )
        from scripts.baseline_validation.config_models import BaselineValidationConfig
        from scripts.baseline_validation.report import create_report_from_validation_run

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        result = validator.run_mock()

        # Verify result structure
        assert isinstance(result, ValidationRun)
        assert len(result.contender_results) > 0

        for name, cr in result.contender_results.items():
            assert isinstance(cr, ContenderResult)
            assert len(cr.window_sharpes) > 0

        # Generate report
        report = create_report_from_validation_run(result)

        # Verify report matches result
        assert len(report.contender_summaries) == len(result.contender_results)


class TestDataFlowIntegrity:
    """Tests for data flow integrity."""

    def test_metrics_flow_correctly(self) -> None:
        """Test that metrics flow correctly through pipeline."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig
        from scripts.baseline_validation.report import create_report_from_validation_run

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        result = validator.run_mock(seed=42)
        report = create_report_from_validation_run(result)

        # Check metrics consistency
        for name in result.contender_results:
            cr = result.contender_results[name]
            summary = report.contender_summaries[name]

            # Average Sharpe should match
            assert cr.avg_sharpe == pytest.approx(summary.avg_sharpe)
            # Max drawdown should match
            assert cr.max_drawdown == pytest.approx(summary.max_drawdown)

    def test_window_count_consistency(self) -> None:
        """Test window count is consistent across components."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig
        from scripts.baseline_validation.report import create_report_from_validation_run

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        result = validator.run_mock()
        report = create_report_from_validation_run(result)

        # Window count should match
        assert len(result.windows) == report.window_count

        # Each contender should have same number of window results
        for cr in result.contender_results.values():
            assert len(cr.window_sharpes) == len(result.windows)


class TestEdgeCases:
    """Tests for edge cases in integration."""

    def test_minimal_window_validation(self) -> None:
        """Test validation with minimal windows (at least 2 required)."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import (
            BaselineValidationConfig,
            ValidationConfig,
        )
        from scripts.baseline_validation.report import create_report_from_validation_run

        # Short data range = few windows
        config = BaselineValidationConfig.default()
        config.validation = ValidationConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2025, 1, 1),
            train_months=6,
            test_months=1,
            step_months=6,
            min_windows=2,  # Minimum allowed
        )

        validator = ComparisonValidator(config)
        result = validator.run_mock()

        # Should still produce valid report with few windows
        report = create_report_from_validation_run(result)
        assert report.verdict is not None
        assert report.window_count >= 2

    def test_disabled_contenders(self) -> None:
        """Test validation with some contenders disabled."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig
        from scripts.baseline_validation.report import create_report_from_validation_run

        config = BaselineValidationConfig.default()
        config.contenders["buyhold"].enabled = False

        validator = ComparisonValidator(config)
        result = validator.run_mock()

        # Should only have 2 contenders
        assert len(result.contender_results) == 2
        assert "buyhold" not in result.contender_results

        report = create_report_from_validation_run(result)
        assert len(report.contender_summaries) == 2
