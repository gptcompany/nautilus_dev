"""Unit tests for report generation.

Tests for:
    - Markdown report generation
    - Comparison table formatting
    - JSON export

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations

from datetime import datetime


class TestMarkdownReportGeneration:
    """Tests for Markdown report generation."""

    def test_generates_markdown_report(self) -> None:
        """Test that report generator produces markdown output."""
        from scripts.baseline_validation.report import generate_markdown_report
        from scripts.baseline_validation.report_models import (
            ValidationReport,
            ContenderSummary,
            Verdict,
        )

        report = ValidationReport(
            run_id="test-001",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            verdict=Verdict.GO,
            confidence=0.85,
            recommendation="Deploy adaptive sizing",
            contender_summaries={
                "adaptive": ContenderSummary(
                    name="adaptive",
                    avg_sharpe=1.5,
                    std_sharpe=0.3,
                    max_drawdown=0.15,
                    win_rate=0.65,
                    total_trades=150,
                ),
                "fixed": ContenderSummary(
                    name="fixed",
                    avg_sharpe=1.2,
                    std_sharpe=0.25,
                    max_drawdown=0.18,
                    win_rate=0.60,
                    total_trades=145,
                ),
            },
            window_count=12,
            data_start=datetime(2015, 1, 1),
            data_end=datetime(2025, 1, 1),
        )

        markdown = generate_markdown_report(report)

        assert "# Baseline Validation Report" in markdown
        assert "GO" in markdown
        assert "adaptive" in markdown

    def test_markdown_contains_comparison_table(self) -> None:
        """Test that markdown contains comparison table."""
        from scripts.baseline_validation.report import generate_markdown_report
        from scripts.baseline_validation.report_models import (
            ValidationReport,
            ContenderSummary,
            Verdict,
        )

        report = ValidationReport(
            run_id="test-002",
            timestamp=datetime.now(),
            verdict=Verdict.WAIT,
            confidence=0.50,
            recommendation="Further investigation",
            contender_summaries={
                "adaptive": ContenderSummary(
                    name="adaptive",
                    avg_sharpe=1.3,
                    std_sharpe=0.3,
                    max_drawdown=0.15,
                    win_rate=0.60,
                    total_trades=100,
                ),
                "fixed": ContenderSummary(
                    name="fixed",
                    avg_sharpe=1.2,
                    std_sharpe=0.25,
                    max_drawdown=0.16,
                    win_rate=0.58,
                    total_trades=95,
                ),
            },
            window_count=8,
            data_start=datetime(2015, 1, 1),
            data_end=datetime(2023, 1, 1),
        )

        markdown = generate_markdown_report(report)

        # Should contain markdown table separators
        assert "|" in markdown
        assert "Sharpe" in markdown or "sharpe" in markdown


class TestComparisonTableFormatting:
    """Tests for comparison table formatting."""

    def test_formats_comparison_table(self) -> None:
        """Test comparison table formatting."""
        from scripts.baseline_validation.report import format_comparison_table
        from scripts.baseline_validation.report_models import ContenderSummary

        summaries = {
            "adaptive": ContenderSummary(
                name="adaptive",
                avg_sharpe=1.5,
                std_sharpe=0.3,
                max_drawdown=0.15,
                win_rate=0.65,
                total_trades=150,
            ),
            "fixed": ContenderSummary(
                name="fixed",
                avg_sharpe=1.2,
                std_sharpe=0.25,
                max_drawdown=0.18,
                win_rate=0.60,
                total_trades=145,
            ),
            "buyhold": ContenderSummary(
                name="buyhold",
                avg_sharpe=0.7,
                std_sharpe=0.4,
                max_drawdown=0.25,
                win_rate=0.50,
                total_trades=1,
            ),
        }

        table = format_comparison_table(summaries)

        # Should be a list of formatted rows
        assert isinstance(table, str)
        assert "adaptive" in table
        assert "fixed" in table

    def test_highlights_winner(self) -> None:
        """Test that table highlights the winner."""
        from scripts.baseline_validation.report import format_comparison_table
        from scripts.baseline_validation.report_models import ContenderSummary

        summaries = {
            "adaptive": ContenderSummary(
                name="adaptive",
                avg_sharpe=1.5,
                std_sharpe=0.3,
                max_drawdown=0.15,
                win_rate=0.65,
                total_trades=150,
            ),
            "fixed": ContenderSummary(
                name="fixed",
                avg_sharpe=1.2,
                std_sharpe=0.25,
                max_drawdown=0.18,
                win_rate=0.60,
                total_trades=145,
            ),
        }

        table = format_comparison_table(summaries, highlight_winner=True)

        # Winner should be marked (adaptive has higher Sharpe)
        assert "**" in table or "winner" in table.lower() or "✓" in table


class TestJSONExport:
    """Tests for JSON export."""

    def test_exports_to_json(self) -> None:
        """Test report can be exported to JSON."""
        from scripts.baseline_validation.report import export_to_json
        from scripts.baseline_validation.report_models import (
            ValidationReport,
            ContenderSummary,
            Verdict,
        )
        import json

        report = ValidationReport(
            run_id="test-003",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            verdict=Verdict.STOP,
            confidence=0.70,
            recommendation="Use fixed 2% sizing",
            contender_summaries={
                "adaptive": ContenderSummary(
                    name="adaptive",
                    avg_sharpe=1.0,
                    std_sharpe=0.4,
                    max_drawdown=0.25,
                    win_rate=0.55,
                    total_trades=120,
                ),
                "fixed": ContenderSummary(
                    name="fixed",
                    avg_sharpe=1.3,
                    std_sharpe=0.2,
                    max_drawdown=0.15,
                    win_rate=0.62,
                    total_trades=118,
                ),
            },
            window_count=10,
            data_start=datetime(2015, 1, 1),
            data_end=datetime(2024, 1, 1),
        )

        json_str = export_to_json(report)

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["verdict"] == "STOP"
        assert "contender_summaries" in data

    def test_json_is_reproducible(self) -> None:
        """Test that JSON export is deterministic."""
        from scripts.baseline_validation.report import export_to_json
        from scripts.baseline_validation.report_models import (
            ValidationReport,
            ContenderSummary,
            Verdict,
        )

        report = ValidationReport(
            run_id="test-004",
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            verdict=Verdict.GO,
            confidence=0.80,
            recommendation="Deploy",
            contender_summaries={
                "adaptive": ContenderSummary(
                    name="adaptive",
                    avg_sharpe=1.5,
                    std_sharpe=0.3,
                    max_drawdown=0.15,
                    win_rate=0.65,
                    total_trades=150,
                ),
            },
            window_count=12,
            data_start=datetime(2015, 1, 1),
            data_end=datetime(2025, 1, 1),
        )

        json1 = export_to_json(report)
        json2 = export_to_json(report)

        assert json1 == json2


class TestReportFromValidationRun:
    """Tests for generating report from ValidationRun."""

    def test_creates_report_from_validation_run(self) -> None:
        """Test creating report from ValidationRun result."""
        from scripts.baseline_validation.comparison_validator import (
            ComparisonValidator,
        )
        from scripts.baseline_validation.config_models import BaselineValidationConfig
        from scripts.baseline_validation.report import create_report_from_validation_run
        from scripts.baseline_validation.report_models import ValidationReport

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)
        validation_run = validator.run_mock()

        report = create_report_from_validation_run(validation_run)

        assert isinstance(report, ValidationReport)
        assert report.verdict is not None
        assert len(report.contender_summaries) == 3
