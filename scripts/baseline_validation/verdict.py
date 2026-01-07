"""Verdict determination logic for baseline validation.

Implements GO/WAIT/STOP decision logic based on:
    - Sharpe ratio edge threshold
    - Maximum drawdown comparison
    - Statistical significance

Reference:
    - DeMiguel (2009): "Optimal Versus Naive Diversification"
    - Lopez de Prado (2018): "Advances in Financial Machine Learning"
"""

from __future__ import annotations

from scripts.baseline_validation.report_models import Verdict


def determine_verdict(
    adaptive_sharpe: float,
    fixed_sharpe: float,
    adaptive_max_dd: float,
    fixed_max_dd: float,
    sharpe_edge_threshold: float = 0.2,
    drawdown_tolerance: float = 1.5,
) -> Verdict:
    """Determine GO/WAIT/STOP verdict.

    Decision logic:
        GO: Adaptive beats Fixed by sharpe_edge AND drawdown is acceptable
        STOP: Fixed beats Adaptive OR Fixed has much better risk profile
        WAIT: Insufficient evidence to decide

    Args:
        adaptive_sharpe: Average Sharpe ratio of adaptive strategy.
        fixed_sharpe: Average Sharpe ratio of fixed baseline.
        adaptive_max_dd: Maximum drawdown of adaptive strategy.
        fixed_max_dd: Maximum drawdown of fixed baseline.
        sharpe_edge_threshold: Minimum Sharpe edge required for GO (default: 0.2).
        drawdown_tolerance: Max ratio of adaptive/fixed drawdown (default: 1.5).

    Returns:
        Verdict enum (GO, WAIT, or STOP).
    """
    import math

    # B4 fix: Handle NaN values - cannot make decision with invalid data
    if math.isnan(adaptive_sharpe) or math.isnan(fixed_sharpe):
        return Verdict.WAIT

    sharpe_edge = adaptive_sharpe - fixed_sharpe

    # Fixed wins - STOP
    if fixed_sharpe > adaptive_sharpe:
        return Verdict.STOP

    # Adaptive wins but edge is insufficient - WAIT
    if sharpe_edge < sharpe_edge_threshold:
        return Verdict.WAIT

    # Adaptive has acceptable drawdown - GO
    # Allow adaptive to have up to drawdown_tolerance times fixed drawdown
    if fixed_max_dd > 0:
        dd_ratio = adaptive_max_dd / fixed_max_dd
        if dd_ratio > drawdown_tolerance:
            return Verdict.WAIT

    return Verdict.GO


def calculate_confidence(
    window_sharpes: list[float],
    p_value: float,
    min_windows: int = 5,
) -> float:
    """Calculate confidence level in the verdict.

    Confidence is based on:
        - Number of windows (more = higher confidence)
        - P-value significance (lower = higher confidence)
        - Consistency of window results (lower variance = higher confidence)

    Args:
        window_sharpes: Sharpe ratios from each window.
        p_value: P-value from significance test.
        min_windows: Minimum windows for base confidence.

    Returns:
        Confidence level between 0 and 1.
    """
    n_windows = len(window_sharpes)

    if n_windows < 2:
        return 0.1  # Very low confidence with insufficient data

    # B3 fix: Clamp p_value to valid range [0, 1]
    p_value = max(0.0, min(1.0, p_value))

    # Window count contribution (0.0 to 0.4)
    window_factor = min(n_windows / 20, 1.0) * 0.4

    # P-value contribution (0.0 to 0.4)
    # Lower p-value = higher confidence
    p_value_factor = max(0, (1 - p_value * 2)) * 0.4

    # Consistency contribution (0.0 to 0.2)
    if window_sharpes:
        mean = sum(window_sharpes) / len(window_sharpes)
        if len(window_sharpes) > 1:
            variance = sum((s - mean) ** 2 for s in window_sharpes) / (len(window_sharpes) - 1)
            std = variance**0.5
            # Lower std relative to mean = higher consistency
            cv = abs(std / mean) if mean != 0 else 1.0
            consistency_factor = max(0, (1 - cv)) * 0.2
        else:
            consistency_factor = 0.1
    else:
        consistency_factor = 0.0

    confidence = window_factor + p_value_factor + consistency_factor

    return min(max(confidence, 0.0), 1.0)


def generate_recommendation(
    verdict: Verdict,
    adaptive_sharpe: float,
    fixed_sharpe: float,
    sharpe_edge: float,
) -> str:
    """Generate human-readable recommendation.

    Args:
        verdict: The determined verdict.
        adaptive_sharpe: Average Sharpe of adaptive strategy.
        fixed_sharpe: Average Sharpe of fixed baseline.
        sharpe_edge: Difference in Sharpe ratios.

    Returns:
        Human-readable recommendation string.
    """
    if verdict == Verdict.GO:
        return (
            f"Deploy adaptive sizing. Adaptive outperforms Fixed by "
            f"Sharpe edge of {sharpe_edge:.2f} ({adaptive_sharpe:.2f} vs {fixed_sharpe:.2f}). "
            f"Complexity is justified by out-of-sample performance."
        )

    if verdict == Verdict.STOP:
        return (
            f"Use Fixed 2% sizing. Fixed baseline outperforms Adaptive "
            f"({fixed_sharpe:.2f} vs {adaptive_sharpe:.2f}). "
            f"Complexity is NOT justified - use simpler approach."
        )

    # WAIT
    return (
        f"Further investigation needed. Sharpe edge ({sharpe_edge:.2f}) is insufficient "
        f"to justify complexity. Adaptive: {adaptive_sharpe:.2f}, Fixed: {fixed_sharpe:.2f}. "
        f"Consider more data, different parameters, or regime analysis."
    )
