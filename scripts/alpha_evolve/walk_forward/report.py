"""Report generation for walk-forward validation results."""

import json
from datetime import datetime
from typing import Any

from scripts.alpha_evolve.walk_forward.models import WalkForwardResult


def generate_report(result: WalkForwardResult) -> str:
    """Generate markdown report from walk-forward validation results.

    Args:
        result: Complete walk-forward validation result.

    Returns:
        Markdown formatted report string.

    Example:
        >>> report = generate_report(result)
        >>> print(report)
    """
    lines: list[str] = []

    # Header
    lines.append("# Walk-Forward Validation Report\n")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Summary section
    lines.append("## Summary\n")
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    lines.append(f"**Status**: {status}")
    lines.append(f"**Robustness Score**: {result.robustness_score:.1f}/100")
    lines.append(f"**Windows Evaluated**: {len(result.windows)}")
    lines.append(f"**Validation Time**: {result.validation_time_seconds:.2f}s\n")

    # Advanced metrics
    if (
        result.deflated_sharpe_ratio is not None
        or result.probability_backtest_overfitting is not None
    ):
        lines.append("## Advanced Overfitting Metrics\n")
        lines.append(
            "*Based on Lopez de Prado (2018) - Advances in Financial Machine Learning*\n"
        )

        if result.deflated_sharpe_ratio is not None:
            lines.append(
                f"**Deflated Sharpe Ratio (DSR)**: {result.deflated_sharpe_ratio:.3f}"
            )
            lines.append("  - Adjusted for multiple testing (Ch. 14)")

        if result.probability_backtest_overfitting is not None:
            pbo = result.probability_backtest_overfitting
            pbo_status = "⚠️ HIGH RISK" if pbo > 0.5 else "✓ Low risk"
            lines.append(
                f"**Probability of Backtest Overfitting (PBO)**: {pbo:.1%} {pbo_status}"
            )
            lines.append("  - Probability best strategy is false positive (Ch. 11)\n")

    # Key metrics summary
    lines.append("## Key Metrics\n")
    lines.append("| Metric | Value | Threshold | Status |")
    lines.append("|--------|-------|-----------|--------|")

    # Robustness score
    rob_status = (
        "✓" if result.robustness_score >= result.config.min_robustness_score else "✗"
    )
    lines.append(
        f"| Robustness Score | {result.robustness_score:.1f} | "
        f"≥ {result.config.min_robustness_score:.1f} | {rob_status} |"
    )

    # Profitable windows
    prof_status = (
        "✓"
        if result.profitable_windows_pct >= result.config.min_profitable_windows_pct
        else "✗"
    )
    lines.append(
        f"| Profitable Windows | {result.profitable_windows_pct:.1%} | "
        f"≥ {result.config.min_profitable_windows_pct:.1%} | {prof_status} |"
    )

    # Worst drawdown
    dd_status = (
        "✓" if result.worst_drawdown <= result.config.max_drawdown_threshold else "✗"
    )
    lines.append(
        f"| Worst Drawdown | {result.worst_drawdown:.1%} | "
        f"≤ {result.config.max_drawdown_threshold:.1%} | {dd_status} |"
    )

    # Average test Sharpe
    lines.append(f"| Avg Test Sharpe | {result.avg_test_sharpe:.2f} | - | - |")
    lines.append(f"| Avg Degradation | {result.avg_degradation:.2f} | - | - |\n")

    # Window results table
    lines.append("## Window Results\n")
    lines.append(
        "| Window | Period | Train Sharpe | Test Sharpe | Test Return | Test DD | Degradation |"
    )
    lines.append(
        "|--------|--------|--------------|-------------|-------------|---------|-------------|"
    )

    for w in result.windows:
        period = f"{w.window.test_start.strftime('%Y-%m')} to {w.window.test_end.strftime('%Y-%m')}"
        degradation_pct = (
            f"{w.degradation_ratio:.0%}" if w.degradation_ratio <= 2 else ">200%"
        )
        lines.append(
            f"| {w.window.window_id} | {period} | "
            f"{w.train_metrics.sharpe_ratio:.2f} | "
            f"{w.test_metrics.sharpe_ratio:.2f} | "
            f"{w.test_metrics.total_return:+.1%} | "
            f"{w.test_metrics.max_drawdown:.1%} | "
            f"{degradation_pct} |"
        )

    lines.append("")

    # Configuration section
    lines.append("## Configuration\n")
    lines.append(
        f"- **Data Range**: {result.config.data_start.strftime('%Y-%m-%d')} to {result.config.data_end.strftime('%Y-%m-%d')}"
    )
    lines.append(f"- **Train Window**: {result.config.train_months} months")
    lines.append(f"- **Test Window**: {result.config.test_months} months")
    lines.append(f"- **Step Size**: {result.config.step_months} months")
    lines.append(f"- **Embargo Before**: {result.config.embargo_before_days} days")
    lines.append(f"- **Embargo After**: {result.config.embargo_after_days} days\n")

    # Interpretation section
    lines.append("## Interpretation Guide\n")
    lines.append("### Robustness Score (0-100)")
    lines.append("- **80-100**: Excellent - robust strategy, likely to perform live")
    lines.append("- **60-80**: Good - acceptable for cautious deployment")
    lines.append("- **40-60**: Fair - possible overfitting, needs review")
    lines.append("- **0-40**: Poor - significant overfitting, do not deploy\n")

    lines.append("### Degradation Ratio")
    lines.append("- **>80%**: Minimal degradation - strategy generalizes well")
    lines.append("- **50-80%**: Moderate degradation - typical for real strategies")
    lines.append("- **<50%**: Significant degradation - likely overfitting\n")

    # Footer
    lines.append("---")
    lines.append("*Report generated by Walk-Forward Validator (Spec 020)*")

    return "\n".join(lines)


def export_json(result: WalkForwardResult) -> str:
    """Export walk-forward validation results to JSON.

    Args:
        result: Complete walk-forward validation result.

    Returns:
        JSON string with all metrics.

    Example:
        >>> json_str = export_json(result)
        >>> data = json.loads(json_str)
    """
    data: dict[str, Any] = {
        "summary": {
            "passed": result.passed,
            "robustness_score": result.robustness_score,
            "profitable_windows_pct": result.profitable_windows_pct,
            "avg_test_sharpe": result.avg_test_sharpe,
            "avg_test_return": result.avg_test_return,
            "worst_drawdown": result.worst_drawdown,
            "avg_degradation": result.avg_degradation,
            "validation_time_seconds": result.validation_time_seconds,
        },
        "advanced_metrics": {
            "deflated_sharpe_ratio": result.deflated_sharpe_ratio,
            "probability_backtest_overfitting": result.probability_backtest_overfitting,
        },
        "config": {
            "data_start": result.config.data_start.isoformat(),
            "data_end": result.config.data_end.isoformat(),
            "train_months": result.config.train_months,
            "test_months": result.config.test_months,
            "step_months": result.config.step_months,
            "embargo_before_days": result.config.embargo_before_days,
            "embargo_after_days": result.config.embargo_after_days,
            "min_windows": result.config.min_windows,
            "min_profitable_windows_pct": result.config.min_profitable_windows_pct,
            "min_test_sharpe": result.config.min_test_sharpe,
            "max_drawdown_threshold": result.config.max_drawdown_threshold,
            "min_robustness_score": result.config.min_robustness_score,
        },
        "windows": [
            {
                "window_id": w.window.window_id,
                "train_start": w.window.train_start.isoformat(),
                "train_end": w.window.train_end.isoformat(),
                "test_start": w.window.test_start.isoformat(),
                "test_end": w.window.test_end.isoformat(),
                "train_metrics": {
                    "sharpe_ratio": w.train_metrics.sharpe_ratio,
                    "calmar_ratio": w.train_metrics.calmar_ratio,
                    "max_drawdown": w.train_metrics.max_drawdown,
                    "total_return": w.train_metrics.total_return,
                    "win_rate": w.train_metrics.win_rate,
                    "trade_count": w.train_metrics.trade_count,
                },
                "test_metrics": {
                    "sharpe_ratio": w.test_metrics.sharpe_ratio,
                    "calmar_ratio": w.test_metrics.calmar_ratio,
                    "max_drawdown": w.test_metrics.max_drawdown,
                    "total_return": w.test_metrics.total_return,
                    "win_rate": w.test_metrics.win_rate,
                    "trade_count": w.test_metrics.trade_count,
                },
                "degradation_ratio": w.degradation_ratio,
            }
            for w in result.windows
        ],
        "generated_at": datetime.now().isoformat(),
    }

    return json.dumps(data, indent=2)
