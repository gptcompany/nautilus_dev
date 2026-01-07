"""Comparison metrics for baseline validation.

This module provides metrics for comparing contender performance:
    - Relative Sharpe difference
    - Win/loss ratio between contenders
    - Statistical significance (t-test)
    - Aggregate metrics across windows

All metrics use only standard library (no numpy/scipy).

Reference:
    - Lopez de Prado (2018): "Advances in Financial Machine Learning"
    - Bailey & Lopez de Prado (2014): "The Deflated Sharpe Ratio"
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class ContenderMetrics:
    """Aggregated metrics for a single contender."""

    name: str
    avg_sharpe: float
    std_sharpe: float
    avg_return: float
    std_return: float
    avg_drawdown: float
    max_drawdown: float
    win_rate: float  # % of profitable windows
    total_trades: int
    window_count: int


@dataclass
class ComparisonResult:
    """Result of comparing two contenders."""

    contender_a: str
    contender_b: str
    sharpe_difference: float  # A - B
    sharpe_difference_pct: float  # % improvement
    relative_drawdown: float  # A_dd / B_dd (< 1 is better for A)
    win_loss_ratio: float  # Windows where A > B / Windows where B > A
    t_statistic: float
    p_value: float
    is_significant: bool  # p < 0.05
    a_beats_b: bool  # Whether A is significantly better


@dataclass
class MultiContenderComparison:
    """Comparison results for multiple contenders."""

    contender_metrics: dict[str, ContenderMetrics]
    pairwise_comparisons: list[ComparisonResult]
    best_contender: str
    best_sharpe: float
    ranking: list[str]  # Ordered by Sharpe descending


def calculate_contender_metrics(
    name: str,
    sharpe_ratios: Sequence[float],
    returns: Sequence[float],
    drawdowns: Sequence[float],
    trade_counts: Sequence[int],
) -> ContenderMetrics:
    """Calculate aggregated metrics for a contender.

    Args:
        name: Contender name.
        sharpe_ratios: Sharpe ratio per window.
        returns: Total return per window.
        drawdowns: Max drawdown per window.
        trade_counts: Trade count per window.

    Returns:
        ContenderMetrics with aggregated statistics.
    """
    n = len(sharpe_ratios)

    if n == 0:
        return ContenderMetrics(
            name=name,
            avg_sharpe=0.0,
            std_sharpe=0.0,
            avg_return=0.0,
            std_return=0.0,
            avg_drawdown=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            total_trades=0,
            window_count=0,
        )

    # Calculate means
    avg_sharpe = sum(sharpe_ratios) / n
    avg_return = sum(returns) / n
    avg_drawdown = sum(drawdowns) / n

    # Calculate standard deviations
    if n > 1:
        var_sharpe = sum((s - avg_sharpe) ** 2 for s in sharpe_ratios) / (n - 1)
        var_return = sum((r - avg_return) ** 2 for r in returns) / (n - 1)
        std_sharpe = math.sqrt(var_sharpe)
        std_return = math.sqrt(var_return)
    else:
        std_sharpe = 0.0
        std_return = 0.0

    # Win rate: % of windows with positive return
    profitable_windows = sum(1 for r in returns if r > 0)
    win_rate = profitable_windows / n

    return ContenderMetrics(
        name=name,
        avg_sharpe=avg_sharpe,
        std_sharpe=std_sharpe,
        avg_return=avg_return,
        std_return=std_return,
        avg_drawdown=avg_drawdown,
        max_drawdown=max(drawdowns) if drawdowns else 0.0,
        win_rate=win_rate,
        total_trades=sum(trade_counts),
        window_count=n,
    )


def calculate_sharpe_difference(
    sharpe_a: float,
    sharpe_b: float,
) -> tuple[float, float]:
    """Calculate Sharpe ratio difference.

    Args:
        sharpe_a: Sharpe ratio of contender A.
        sharpe_b: Sharpe ratio of contender B.

    Returns:
        Tuple of (absolute_difference, percentage_difference).
        Percentage is relative to B.
    """
    absolute_diff = sharpe_a - sharpe_b

    if abs(sharpe_b) < 1e-10:
        # Avoid division by zero
        pct_diff = float("inf") if sharpe_a > 0 else float("-inf") if sharpe_a < 0 else 0.0
    else:
        pct_diff = (sharpe_a - sharpe_b) / abs(sharpe_b) * 100

    return absolute_diff, pct_diff


def calculate_win_loss_ratio(
    returns_a: Sequence[float],
    returns_b: Sequence[float],
) -> float:
    """Calculate win/loss ratio between contenders.

    Counts windows where A outperforms B vs B outperforms A.

    Args:
        returns_a: Returns per window for contender A.
        returns_b: Returns per window for contender B.

    Returns:
        Ratio of windows where A > B / windows where B > A.
        Returns inf if B never wins, 0 if A never wins.
    """
    if len(returns_a) != len(returns_b):
        raise ValueError(
            f"Return sequences must have same length: {len(returns_a)} vs {len(returns_b)}"
        )

    a_wins = 0
    b_wins = 0

    for r_a, r_b in zip(returns_a, returns_b, strict=False):
        if r_a > r_b:
            a_wins += 1
        elif r_b > r_a:
            b_wins += 1
        # Ties don't count

    if b_wins == 0:
        return float("inf") if a_wins > 0 else 1.0
    return a_wins / b_wins


def calculate_t_statistic(
    returns_a: Sequence[float],
    returns_b: Sequence[float],
) -> tuple[float, float]:
    """Calculate paired t-test statistic and p-value.

    Tests whether the mean difference is significantly different from zero.

    Args:
        returns_a: Returns per window for contender A.
        returns_b: Returns per window for contender B.

    Returns:
        Tuple of (t_statistic, p_value).
        Positive t means A > B on average.
    """
    if len(returns_a) != len(returns_b):
        raise ValueError(
            f"Return sequences must have same length: {len(returns_a)} vs {len(returns_b)}"
        )

    n = len(returns_a)

    if n < 2:
        return 0.0, 1.0

    # Calculate differences
    differences = [a - b for a, b in zip(returns_a, returns_b, strict=False)]

    # Mean difference
    mean_diff = sum(differences) / n

    # Standard error of the mean difference
    if n > 1:
        variance = sum((d - mean_diff) ** 2 for d in differences) / (n - 1)
        std_err = math.sqrt(variance / n)
    else:
        std_err = 0.0

    if std_err < 1e-10:
        # All differences are identical
        if abs(mean_diff) < 1e-10:
            return 0.0, 1.0
        else:
            return float("inf") if mean_diff > 0 else float("-inf"), 0.0

    # t-statistic
    t_stat = mean_diff / std_err

    # Approximate p-value using Student's t-distribution
    # Using two-tailed test
    p_value = _t_distribution_p_value(t_stat, n - 1)

    return t_stat, p_value


def _t_distribution_p_value(t: float, df: int) -> float:
    """Approximate p-value from t-distribution.

    Uses approximation for large df (normal approximation).
    For small df, uses a simple approximation.

    Args:
        t: t-statistic.
        df: Degrees of freedom.

    Returns:
        Two-tailed p-value.
    """
    # B5 fix: Guard against invalid degrees of freedom
    if df <= 0:
        return 1.0

    # For large df, use normal approximation
    # For small df, use rough approximation

    t_abs = abs(t)

    if df >= 30:
        # Normal approximation
        # P(|Z| > t) = 2 * (1 - Phi(t))
        p = 2 * (1 - _norm_cdf(t_abs))
    else:
        # Simple approximation for small df
        # This is rough but adequate for our comparison purposes
        # Uses the relationship: as df -> inf, t -> N(0,1)
        adjustment = 1 + 3 / df  # Inflate t for small df
        p = 2 * (1 - _norm_cdf(t_abs / adjustment))

    return max(0.0, min(1.0, p))


def _norm_cdf(x: float) -> float:
    """Standard normal CDF using erfc.

    Args:
        x: Value to evaluate.

    Returns:
        P(Z <= x) where Z ~ N(0,1).
    """
    return 0.5 * math.erfc(-x / math.sqrt(2.0))


def compare_contenders(
    name_a: str,
    name_b: str,
    sharpes_a: Sequence[float],
    sharpes_b: Sequence[float],
    returns_a: Sequence[float],
    returns_b: Sequence[float],
    drawdowns_a: Sequence[float],
    drawdowns_b: Sequence[float],
    significance_threshold: float = 0.05,
    sharpe_edge_threshold: float = 0.2,
) -> ComparisonResult:
    """Compare two contenders statistically.

    Args:
        name_a: Name of contender A.
        name_b: Name of contender B.
        sharpes_a: Sharpe ratios per window for A.
        sharpes_b: Sharpe ratios per window for B.
        returns_a: Returns per window for A.
        returns_b: Returns per window for B.
        drawdowns_a: Drawdowns per window for A.
        drawdowns_b: Drawdowns per window for B.
        significance_threshold: p-value threshold for significance.
        sharpe_edge_threshold: Sharpe difference required for "beats" (default 0.2).

    Returns:
        ComparisonResult with statistical comparison.
    """
    n = len(sharpes_a)
    if n == 0:
        return ComparisonResult(
            contender_a=name_a,
            contender_b=name_b,
            sharpe_difference=0.0,
            sharpe_difference_pct=0.0,
            relative_drawdown=1.0,
            win_loss_ratio=1.0,
            t_statistic=0.0,
            p_value=1.0,
            is_significant=False,
            a_beats_b=False,
        )

    # Average metrics
    avg_sharpe_a = sum(sharpes_a) / n
    avg_sharpe_b = sum(sharpes_b) / n
    avg_dd_a = sum(drawdowns_a) / n if drawdowns_a else 0.0
    avg_dd_b = sum(drawdowns_b) / n if drawdowns_b else 0.0

    # Calculate metrics
    sharpe_diff, sharpe_diff_pct = calculate_sharpe_difference(avg_sharpe_a, avg_sharpe_b)
    win_loss = calculate_win_loss_ratio(returns_a, returns_b)
    t_stat, p_value = calculate_t_statistic(returns_a, returns_b)

    # Relative drawdown (< 1 means A has lower drawdown)
    if avg_dd_b > 1e-10:
        relative_dd = avg_dd_a / avg_dd_b
    else:
        relative_dd = 1.0 if avg_dd_a < 1e-10 else float("inf")

    # Determine if A beats B
    is_significant = p_value < significance_threshold
    a_beats_b = (
        is_significant
        and sharpe_diff > sharpe_edge_threshold
        and t_stat > 0  # A has higher returns
    )

    return ComparisonResult(
        contender_a=name_a,
        contender_b=name_b,
        sharpe_difference=sharpe_diff,
        sharpe_difference_pct=sharpe_diff_pct,
        relative_drawdown=relative_dd,
        win_loss_ratio=win_loss,
        t_statistic=t_stat,
        p_value=p_value,
        is_significant=is_significant,
        a_beats_b=a_beats_b,
    )


def compare_all_contenders(
    contender_results: dict[str, dict[str, list[float]]],
    sharpe_edge_threshold: float = 0.2,
) -> MultiContenderComparison:
    """Compare all contenders against each other.

    Args:
        contender_results: Dict mapping contender name to results dict:
            {
                "adaptive": {
                    "sharpes": [1.2, 0.8, ...],
                    "returns": [0.05, -0.02, ...],
                    "drawdowns": [0.10, 0.15, ...],
                    "trade_counts": [50, 45, ...],
                },
                ...
            }
        sharpe_edge_threshold: Sharpe difference for "beats".

    Returns:
        MultiContenderComparison with all results.
    """
    names = list(contender_results.keys())

    # Calculate individual metrics
    contender_metrics = {}
    for name, results in contender_results.items():
        # Ensure trade_counts is a list of ints
        trade_counts_raw = results.get("trade_counts", [])
        trade_counts: list[int] = [int(x) for x in trade_counts_raw] if trade_counts_raw else []

        metrics = calculate_contender_metrics(
            name=name,
            sharpe_ratios=results.get("sharpes", []),
            returns=results.get("returns", []),
            drawdowns=results.get("drawdowns", []),
            trade_counts=trade_counts,
        )
        contender_metrics[name] = metrics

    # Pairwise comparisons
    pairwise = []
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            res_a = contender_results[name_a]
            res_b = contender_results[name_b]

            comparison = compare_contenders(
                name_a=name_a,
                name_b=name_b,
                sharpes_a=res_a.get("sharpes", []),
                sharpes_b=res_b.get("sharpes", []),
                returns_a=res_a.get("returns", []),
                returns_b=res_b.get("returns", []),
                drawdowns_a=res_a.get("drawdowns", []),
                drawdowns_b=res_b.get("drawdowns", []),
                sharpe_edge_threshold=sharpe_edge_threshold,
            )
            pairwise.append(comparison)

    # Find best contender (highest Sharpe)
    ranking = sorted(
        contender_metrics.keys(),
        key=lambda n: contender_metrics[n].avg_sharpe,
        reverse=True,
    )

    best = ranking[0] if ranking else ""
    best_sharpe = contender_metrics[best].avg_sharpe if best else 0.0

    return MultiContenderComparison(
        contender_metrics=contender_metrics,
        pairwise_comparisons=pairwise,
        best_contender=best,
        best_sharpe=best_sharpe,
        ranking=ranking,
    )
