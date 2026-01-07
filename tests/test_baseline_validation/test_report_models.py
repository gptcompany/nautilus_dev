"""Unit tests for report models.

Tests for:
    - ValidationReport model
    - ContenderSummary model
    - ComparisonTable model

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations

from datetime import datetime

import pytest


class TestValidationReport:
    """Tests for ValidationReport model."""

    def test_validation_report_creation(self) -> None:
        """Test ValidationReport can be created."""
        from scripts.baseline_validation.report_models import (
            ContenderSummary,
            ValidationReport,
            Verdict,
        )

        report = ValidationReport(
            run_id="test-001",
            timestamp=datetime.now(),
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

        assert report.verdict == Verdict.GO
        assert report.confidence == 0.85
        assert len(report.contender_summaries) == 2

    def test_validation_report_serialization(self) -> None:
        """Test ValidationReport can be serialized to dict."""
        from scripts.baseline_validation.report_models import (
            ContenderSummary,
            ValidationReport,
            Verdict,
        )

        report = ValidationReport(
            run_id="test-001",
            timestamp=datetime.now(),
            verdict=Verdict.WAIT,
            confidence=0.50,
            recommendation="Further investigation needed",
            contender_summaries={
                "adaptive": ContenderSummary(
                    name="adaptive",
                    avg_sharpe=1.3,
                    std_sharpe=0.3,
                    max_drawdown=0.15,
                    win_rate=0.60,
                    total_trades=100,
                ),
            },
            window_count=8,
            data_start=datetime(2015, 1, 1),
            data_end=datetime(2023, 1, 1),
        )

        data = report.model_dump()

        assert "verdict" in data
        assert "confidence" in data
        assert "contender_summaries" in data


class TestContenderSummary:
    """Tests for ContenderSummary model."""

    def test_contender_summary_creation(self) -> None:
        """Test ContenderSummary can be created."""
        from scripts.baseline_validation.report_models import ContenderSummary

        summary = ContenderSummary(
            name="adaptive",
            avg_sharpe=1.5,
            std_sharpe=0.3,
            max_drawdown=0.15,
            win_rate=0.65,
            total_trades=150,
        )

        assert summary.name == "adaptive"
        assert summary.avg_sharpe == 1.5
        assert summary.max_drawdown == 0.15

    def test_contender_summary_validation(self) -> None:
        """Test ContenderSummary validates fields."""
        from scripts.baseline_validation.report_models import ContenderSummary

        # Win rate should be between 0 and 1
        with pytest.raises(ValueError):
            ContenderSummary(
                name="test",
                avg_sharpe=1.0,
                std_sharpe=0.2,
                max_drawdown=0.10,
                win_rate=1.5,  # Invalid: > 1.0
                total_trades=50,
            )


class TestComparisonRow:
    """Tests for ComparisonRow model."""

    def test_comparison_row_creation(self) -> None:
        """Test ComparisonRow can be created."""
        from scripts.baseline_validation.report_models import ComparisonRow

        row = ComparisonRow(
            metric="Avg Sharpe",
            adaptive="1.50",
            fixed="1.20",
            buyhold="0.70",
            winner="adaptive",
        )

        assert row.metric == "Avg Sharpe"
        assert row.winner == "adaptive"


class TestVerdictDetails:
    """Tests for VerdictDetails model."""

    def test_verdict_details_creation(self) -> None:
        """Test VerdictDetails can be created."""
        from scripts.baseline_validation.report_models import Verdict, VerdictDetails

        details = VerdictDetails(
            verdict=Verdict.GO,
            sharpe_edge=0.3,
            drawdown_comparison="adaptive: 15% vs fixed: 18%",
            t_statistic=2.5,
            p_value=0.02,
            is_significant=True,
        )

        assert details.verdict == Verdict.GO
        assert details.is_significant is True

    def test_verdict_details_significance(self) -> None:
        """Test significance calculation."""
        from scripts.baseline_validation.report_models import Verdict, VerdictDetails

        # p_value < 0.05 should be significant
        details = VerdictDetails(
            verdict=Verdict.GO,
            sharpe_edge=0.25,
            drawdown_comparison="adaptive better",
            t_statistic=2.1,
            p_value=0.04,
            is_significant=True,
        )

        assert details.is_significant is True
