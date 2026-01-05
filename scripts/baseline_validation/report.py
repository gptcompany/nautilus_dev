"""Report generation for baseline validation.

Provides:
    - Markdown report generation
    - Comparison table formatting
    - JSON export for persistence
    - Report creation from ValidationRun

Reference:
    - DeMiguel (2009): "Optimal Versus Naive Diversification"
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from scripts.baseline_validation.report_models import (
    ContenderSummary,
    ValidationReport,
    Verdict,
    VerdictDetails,
)
from scripts.baseline_validation.verdict import (
    calculate_confidence,
    determine_verdict,
    generate_recommendation,
)

if TYPE_CHECKING:
    from scripts.baseline_validation.comparison_validator import ValidationRun


def create_report_from_validation_run(
    validation_run: "ValidationRun",
    sharpe_edge_threshold: float = 0.2,
) -> ValidationReport:
    """Create ValidationReport from ValidationRun result.

    Args:
        validation_run: Result from ComparisonValidator.run() or run_mock().
        sharpe_edge_threshold: Minimum Sharpe edge for GO verdict.

    Returns:
        ValidationReport with verdict and recommendations.
    """
    # Build ContenderSummary from ContenderResult
    contender_summaries: dict[str, ContenderSummary] = {}

    for name, result in validation_run.contender_results.items():
        contender_summaries[name] = ContenderSummary(
            name=result.name,
            avg_sharpe=result.avg_sharpe,
            std_sharpe=result.std_sharpe,
            max_drawdown=result.max_drawdown,
            win_rate=result.win_rate,
            total_trades=result.total_trades,
        )

    # Get adaptive and fixed for verdict
    adaptive = contender_summaries.get("adaptive")
    fixed = contender_summaries.get("fixed")

    if adaptive and fixed:
        verdict = determine_verdict(
            adaptive_sharpe=adaptive.avg_sharpe,
            fixed_sharpe=fixed.avg_sharpe,
            adaptive_max_dd=adaptive.max_drawdown,
            fixed_max_dd=fixed.max_drawdown,
            sharpe_edge_threshold=sharpe_edge_threshold,
        )

        sharpe_edge = adaptive.avg_sharpe - fixed.avg_sharpe

        # Get p-value from comparison if available
        p_value = 0.05  # Default
        if validation_run.comparison:
            # Use pairwise comparison p-value
            for pw in validation_run.comparison.pairwise_comparisons:
                if "adaptive" in pw.contender_a and "fixed" in pw.contender_b:
                    p_value = pw.p_value
                    break

        # Calculate confidence
        adaptive_result = validation_run.contender_results.get("adaptive")
        window_sharpes = adaptive_result.window_sharpes if adaptive_result else []
        confidence = calculate_confidence(window_sharpes, p_value)

        recommendation = generate_recommendation(
            verdict=verdict,
            adaptive_sharpe=adaptive.avg_sharpe,
            fixed_sharpe=fixed.avg_sharpe,
            sharpe_edge=sharpe_edge,
        )

        # Build verdict details
        verdict_details = VerdictDetails(
            verdict=verdict,
            sharpe_edge=sharpe_edge,
            drawdown_comparison=f"adaptive: {adaptive.max_drawdown:.1%} vs fixed: {fixed.max_drawdown:.1%}",
            t_statistic=0.0,  # Would come from comparison
            p_value=p_value,
            is_significant=p_value < 0.05,
        )
    else:
        # Fallback if not all contenders present
        verdict = Verdict.WAIT
        confidence = 0.0
        recommendation = "Missing required contenders for verdict"
        verdict_details = None

    # Get data range from windows
    windows = validation_run.windows
    data_start = windows[0].train_start if windows else datetime(2015, 1, 1)
    data_end = windows[-1].test_end if windows else datetime(2025, 1, 1)

    return ValidationReport(
        run_id=validation_run.config_hash[:8],
        timestamp=validation_run.run_timestamp,
        verdict=verdict,
        confidence=confidence,
        recommendation=recommendation,
        contender_summaries=contender_summaries,
        window_count=len(windows),
        data_start=data_start,
        data_end=data_end,
        verdict_details=verdict_details,
    )


def generate_markdown_report(report: ValidationReport) -> str:
    """Generate Markdown report from ValidationReport.

    Args:
        report: ValidationReport to format.

    Returns:
        Markdown-formatted report string.
    """
    lines = [
        "# Baseline Validation Report",
        "",
        f"**Run ID**: {report.run_id}",
        f"**Timestamp**: {report.timestamp.isoformat()}",
        f"**Data Range**: {report.data_start.date()} to {report.data_end.date()}",
        f"**Walk-Forward Windows**: {report.window_count}",
        "",
        "---",
        "",
        "## Verdict",
        "",
        f"### {report.verdict.value}",
        "",
        f"**Confidence**: {report.confidence:.0%}",
        "",
        f"**Recommendation**: {report.recommendation}",
        "",
    ]

    # Add verdict details if present
    if report.verdict_details:
        lines.extend(
            [
                "### Statistical Details",
                "",
                f"- Sharpe Edge: {report.verdict_details.sharpe_edge:.3f}",
                f"- Drawdown: {report.verdict_details.drawdown_comparison}",
                f"- P-value: {report.verdict_details.p_value:.4f}",
                f"- Significant: {'Yes' if report.verdict_details.is_significant else 'No'}",
                "",
            ]
        )

    # Add comparison table
    lines.extend(
        [
            "---",
            "",
            "## Contender Comparison",
            "",
            format_comparison_table(report.contender_summaries, highlight_winner=True),
            "",
        ]
    )

    return "\n".join(lines)


def format_comparison_table(
    summaries: dict[str, ContenderSummary],
    highlight_winner: bool = False,
) -> str:
    """Format comparison table in Markdown.

    Args:
        summaries: Dict of contender name to ContenderSummary.
        highlight_winner: Whether to highlight the winner with **.

    Returns:
        Markdown table string.
    """
    # Determine columns
    contenders = list(summaries.keys())

    # Find winner (highest avg_sharpe)
    winner = (
        max(contenders, key=lambda c: summaries[c].avg_sharpe) if contenders else ""
    )

    # Build header
    header = "| Metric |"
    separator = "|--------|"
    for c in contenders:
        name = f"**{c}** ✓" if highlight_winner and c == winner else c
        header += f" {name} |"
        separator += "--------|"

    lines = [header, separator]

    # Metrics to display
    metrics = [
        ("Avg Sharpe", lambda s: f"{s.avg_sharpe:.3f}"),
        ("Std Sharpe", lambda s: f"{s.std_sharpe:.3f}"),
        ("Max Drawdown", lambda s: f"{s.max_drawdown:.1%}"),
        ("Win Rate", lambda s: f"{s.win_rate:.1%}"),
        ("Total Trades", lambda s: str(s.total_trades)),
    ]

    for metric_name, formatter in metrics:
        row = f"| {metric_name} |"
        for c in contenders:
            value = formatter(summaries[c])
            row += f" {value} |"
        lines.append(row)

    return "\n".join(lines)


def export_to_json(report: ValidationReport, indent: int = 2) -> str:
    """Export report to JSON string.

    Args:
        report: ValidationReport to export.
        indent: JSON indentation level.

    Returns:
        JSON string representation.
    """
    # Use model_dump with mode='json' for proper serialization
    data = report.model_dump(mode="json")
    return json.dumps(data, indent=indent, default=str, sort_keys=True)
