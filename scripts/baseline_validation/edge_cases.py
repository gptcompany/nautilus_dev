"""Edge case handlers for baseline validation.

This module provides utilities for handling edge cases that can occur
during walk-forward validation:
    - Zero trades in a window
    - NaN/Inf values in metrics
    - Extreme volatility periods
    - Negative Sharpe for all contenders

Philosophy:
    Fail fast on invalid states, graceful degradation for edge cases.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Sequence


class EdgeCaseType(Enum):
    """Types of edge cases that can be detected."""

    ZERO_TRADES = auto()
    NAN_VALUES = auto()
    INF_VALUES = auto()
    EXTREME_VOLATILITY = auto()
    ALL_NEGATIVE_SHARPE = auto()
    INSUFFICIENT_DATA = auto()
    ZERO_RETURNS = auto()


@dataclass
class EdgeCaseResult:
    """Result of edge case detection."""

    detected: bool
    case_type: EdgeCaseType | None
    message: str
    severity: str  # "warning" or "error"
    suggested_action: str


def check_for_nan_inf(values: Sequence[float]) -> EdgeCaseResult:
    """Check for NaN or Inf values in a sequence.

    Args:
        values: Sequence of numeric values.

    Returns:
        EdgeCaseResult with detection status.
    """
    nan_count = sum(1 for v in values if math.isnan(v))
    inf_count = sum(1 for v in values if math.isinf(v))

    if nan_count > 0:
        return EdgeCaseResult(
            detected=True,
            case_type=EdgeCaseType.NAN_VALUES,
            message=f"Found {nan_count} NaN values out of {len(values)} total",
            severity="error",
            suggested_action="Check data pipeline for missing values or division by zero",
        )

    if inf_count > 0:
        return EdgeCaseResult(
            detected=True,
            case_type=EdgeCaseType.INF_VALUES,
            message=f"Found {inf_count} Inf values out of {len(values)} total",
            severity="error",
            suggested_action="Check for overflow in calculations or extreme price movements",
        )

    return EdgeCaseResult(
        detected=False,
        case_type=None,
        message="No NaN or Inf values detected",
        severity="info",
        suggested_action="",
    )


def check_zero_trades(trade_counts: Sequence[int]) -> EdgeCaseResult:
    """Check for windows with zero trades.

    Args:
        trade_counts: Sequence of trade counts per window.

    Returns:
        EdgeCaseResult with detection status.
    """
    zero_count = sum(1 for c in trade_counts if c == 0)

    if zero_count > 0:
        pct = zero_count / len(trade_counts) * 100
        return EdgeCaseResult(
            detected=True,
            case_type=EdgeCaseType.ZERO_TRADES,
            message=f"{zero_count} windows ({pct:.1f}%) had zero trades",
            severity="warning" if pct < 25 else "error",
            suggested_action="Consider relaxing signal thresholds or checking data quality",
        )

    return EdgeCaseResult(
        detected=False,
        case_type=None,
        message="All windows had at least one trade",
        severity="info",
        suggested_action="",
    )


def check_extreme_volatility(
    returns: Sequence[float],
    threshold_std: float = 5.0,
) -> EdgeCaseResult:
    """Check for extreme volatility in returns.

    Args:
        returns: Sequence of return values.
        threshold_std: Number of standard deviations for extreme.

    Returns:
        EdgeCaseResult with detection status.
    """
    if len(returns) < 2:
        return EdgeCaseResult(
            detected=False,
            case_type=None,
            message="Insufficient data for volatility check",
            severity="warning",
            suggested_action="",
        )

    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    std_ret = math.sqrt(variance) if variance > 0 else 0

    if std_ret == 0:
        return EdgeCaseResult(
            detected=True,
            case_type=EdgeCaseType.ZERO_RETURNS,
            message="Zero volatility detected (all returns identical)",
            severity="warning",
            suggested_action="Check if strategy is generating varying position sizes",
        )

    # Count extreme values
    extreme_count = sum(1 for r in returns if abs(r - mean_ret) > threshold_std * std_ret)

    if extreme_count > 0:
        pct = extreme_count / len(returns) * 100
        return EdgeCaseResult(
            detected=True,
            case_type=EdgeCaseType.EXTREME_VOLATILITY,
            message=f"{extreme_count} returns ({pct:.1f}%) exceed {threshold_std} std devs",
            severity="warning",
            suggested_action="Review risk management; consider winsorizing extreme values",
        )

    return EdgeCaseResult(
        detected=False,
        case_type=None,
        message=f"No returns exceed {threshold_std} standard deviations",
        severity="info",
        suggested_action="",
    )


def check_all_negative_sharpe(sharpe_ratios: dict[str, float]) -> EdgeCaseResult:
    """Check if all contenders have negative Sharpe ratio.

    Args:
        sharpe_ratios: Dict mapping contender name to Sharpe ratio.

    Returns:
        EdgeCaseResult with detection status.
    """
    if not sharpe_ratios:
        return EdgeCaseResult(
            detected=False,
            case_type=None,
            message="No Sharpe ratios provided",
            severity="warning",
            suggested_action="",
        )

    all_negative = all(sr < 0 for sr in sharpe_ratios.values())

    if all_negative:
        min_sharpe = min(sharpe_ratios.values())
        worst_contender = min(sharpe_ratios, key=sharpe_ratios.get)  # type: ignore
        return EdgeCaseResult(
            detected=True,
            case_type=EdgeCaseType.ALL_NEGATIVE_SHARPE,
            message=f"All contenders have negative Sharpe. Worst: {worst_contender} ({min_sharpe:.2f})",
            severity="warning",
            suggested_action="Consider: 1) Market period analysis, 2) Signal quality review, 3) Transaction cost impact",
        )

    return EdgeCaseResult(
        detected=False,
        case_type=None,
        message="At least one contender has positive Sharpe ratio",
        severity="info",
        suggested_action="",
    )


def check_insufficient_data(
    window_count: int,
    min_windows: int,
) -> EdgeCaseResult:
    """Check if there are insufficient windows for statistical validity.

    Args:
        window_count: Number of windows generated.
        min_windows: Minimum required windows.

    Returns:
        EdgeCaseResult with detection status.
    """
    if window_count < min_windows:
        return EdgeCaseResult(
            detected=True,
            case_type=EdgeCaseType.INSUFFICIENT_DATA,
            message=f"Only {window_count} windows generated, {min_windows} required",
            severity="error",
            suggested_action="Extend data range or reduce window sizes",
        )

    return EdgeCaseResult(
        detected=False,
        case_type=None,
        message=f"{window_count} windows generated (>= {min_windows} required)",
        severity="info",
        suggested_action="",
    )


def sanitize_metric(value: float, default: float = 0.0) -> float:
    """Sanitize a metric value, replacing NaN/Inf with default.

    Args:
        value: Raw metric value.
        default: Default value for invalid inputs.

    Returns:
        Sanitized value.
    """
    if math.isnan(value) or math.isinf(value):
        return default
    return value


def sanitize_metrics(metrics: dict[str, float]) -> dict[str, float]:
    """Sanitize all metrics in a dict.

    Args:
        metrics: Dict of metric name to value.

    Returns:
        Dict with all values sanitized.
    """
    return {k: sanitize_metric(v) for k, v in metrics.items()}


def run_all_checks(
    sharpe_ratios: dict[str, float] | None = None,
    trade_counts: Sequence[int] | None = None,
    returns: Sequence[float] | None = None,
    window_count: int | None = None,
    min_windows: int = 12,
) -> list[EdgeCaseResult]:
    """Run all edge case checks.

    Args:
        sharpe_ratios: Contender Sharpe ratios.
        trade_counts: Trade counts per window.
        returns: Return values.
        window_count: Number of windows.
        min_windows: Minimum required windows.

    Returns:
        List of EdgeCaseResult for all detected issues.
    """
    results = []

    if sharpe_ratios:
        values = list(sharpe_ratios.values())
        results.append(check_for_nan_inf(values))
        results.append(check_all_negative_sharpe(sharpe_ratios))

    if trade_counts:
        results.append(check_zero_trades(trade_counts))

    if returns:
        results.append(check_for_nan_inf(returns))
        results.append(check_extreme_volatility(returns))

    if window_count is not None:
        results.append(check_insufficient_data(window_count, min_windows))

    # Filter to only detected issues
    return [r for r in results if r.detected]
