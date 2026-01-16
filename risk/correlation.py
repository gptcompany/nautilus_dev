"""
Correlation Matrix Calculator for Trading Risk Analysis.

Provides rolling correlation calculations between strategies/symbols
to assess diversification and detect regime changes.

Reference: Modern Portfolio Theory, Risk Parity methodology.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd


def calculate_correlation_matrix(
    returns_df: pd.DataFrame,
    method: Literal["pearson", "spearman", "kendall"] = "pearson",
) -> pd.DataFrame:
    """
    Calculate correlation matrix between all columns.

    Args:
        returns_df: DataFrame with columns as assets/strategies and rows as time periods.
        method: Correlation method ('pearson', 'spearman', 'kendall').

    Returns:
        Correlation matrix as DataFrame.

    Example:
        >>> df = pd.DataFrame({
        ...     'strategy_a': [0.01, -0.02, 0.03],
        ...     'strategy_b': [0.02, -0.01, 0.02],
        ... })
        >>> corr = calculate_correlation_matrix(df)
    """
    return returns_df.corr(method=method)


def calculate_rolling_correlation(
    returns_df: pd.DataFrame,
    window: int = 30,
    method: Literal["pearson", "spearman", "kendall"] = "pearson",
) -> pd.DataFrame:
    """
    Calculate rolling correlation matrix over a specified window.

    Args:
        returns_df: DataFrame with columns as assets/strategies.
        window: Rolling window size in periods.
        method: Correlation method.

    Returns:
        DataFrame with rolling correlations (MultiIndex: timestamp, pair).

    Example:
        >>> rolling_corr = calculate_rolling_correlation(returns_df, window=20)
        >>> rolling_corr.loc['2024-01-15', ('strategy_a', 'strategy_b')]
    """
    rolling_corr = returns_df.rolling(window=window).corr()
    return rolling_corr


def calculate_pairwise_correlation(
    series_a: pd.Series,
    series_b: pd.Series,
    window: int = 30,
) -> pd.Series:
    """
    Calculate rolling correlation between two series.

    Args:
        series_a: First return series.
        series_b: Second return series.
        window: Rolling window size.

    Returns:
        Series of rolling correlations.
    """
    return series_a.rolling(window=window).corr(series_b)


def detect_correlation_regime_change(
    rolling_corr: pd.Series,
    threshold: float = 0.3,
    lookback: int = 5,
) -> pd.Series:
    """
    Detect significant correlation regime changes.

    Useful for identifying market stress or decorrelation events.

    Args:
        rolling_corr: Series of rolling correlations.
        threshold: Minimum absolute change to flag as regime change.
        lookback: Number of periods to look back for comparison.

    Returns:
        Boolean series indicating regime changes.
    """
    corr_change = rolling_corr.diff(lookback).abs()
    return corr_change > threshold


def calculate_average_correlation(
    corr_matrix: pd.DataFrame,
    exclude_diagonal: bool = True,
) -> float:
    """
    Calculate average pairwise correlation.

    Useful as a single metric for portfolio diversification.

    Args:
        corr_matrix: Correlation matrix.
        exclude_diagonal: Whether to exclude self-correlations (1.0).

    Returns:
        Average correlation value.
    """
    if exclude_diagonal:
        # Get upper triangle excluding diagonal
        mask = np.triu(np.ones(corr_matrix.shape, dtype=bool), k=1)
        upper_triangle = corr_matrix.where(mask)
        return upper_triangle.stack().mean()
    return corr_matrix.values.mean()


def calculate_max_correlation(
    corr_matrix: pd.DataFrame,
    exclude_diagonal: bool = True,
) -> tuple[float, tuple[str, str]]:
    """
    Find the maximum correlation pair.

    Identifies the most correlated assets (potential redundancy).

    Args:
        corr_matrix: Correlation matrix.
        exclude_diagonal: Whether to exclude self-correlations.

    Returns:
        Tuple of (max_correlation, (asset_a, asset_b)).
    """
    if exclude_diagonal:
        # Set diagonal to NaN
        np.fill_diagonal(corr_matrix.values, np.nan)

    max_corr = corr_matrix.stack().max()
    max_pair = corr_matrix.stack().idxmax()

    return max_corr, max_pair


def calculate_min_correlation(
    corr_matrix: pd.DataFrame,
    exclude_diagonal: bool = True,
) -> tuple[float, tuple[str, str]]:
    """
    Find the minimum correlation pair.

    Identifies the most diversifying pair.

    Args:
        corr_matrix: Correlation matrix.
        exclude_diagonal: Whether to exclude self-correlations.

    Returns:
        Tuple of (min_correlation, (asset_a, asset_b)).
    """
    if exclude_diagonal:
        np.fill_diagonal(corr_matrix.values, np.nan)

    min_corr = corr_matrix.stack().min()
    min_pair = corr_matrix.stack().idxmin()

    return min_corr, min_pair


def calculate_correlation_stability(
    rolling_corr: pd.Series,
    window: int = 20,
) -> float:
    """
    Calculate correlation stability as inverse of rolling std.

    High stability = consistent correlation = more predictable risk.

    Args:
        rolling_corr: Series of rolling correlations.
        window: Window for stability calculation.

    Returns:
        Stability score (higher = more stable).
    """
    rolling_std = rolling_corr.rolling(window=window).std()
    mean_std = rolling_std.mean()

    if mean_std == 0 or np.isnan(mean_std):
        return float("inf")

    return 1.0 / mean_std


def format_correlation_for_grafana(
    corr_matrix: pd.DataFrame,
    timestamp: pd.Timestamp,
) -> list[dict]:
    """
    Format correlation matrix for Grafana heatmap ingestion.

    Converts correlation matrix to row format suitable for QuestDB insert.

    Args:
        corr_matrix: Correlation matrix.
        timestamp: Timestamp for the correlation calculation.

    Returns:
        List of dicts ready for database insert.

    Example:
        >>> rows = format_correlation_for_grafana(corr_matrix, pd.Timestamp.now())
        >>> # Insert to QuestDB trading_correlation table
    """
    rows = []
    for asset_a in corr_matrix.index:
        for asset_b in corr_matrix.columns:
            if asset_a < asset_b:  # Upper triangle only to avoid duplicates
                rows.append(
                    {
                        "timestamp": timestamp,
                        "strategy_a": asset_a,
                        "strategy_b": asset_b,
                        "correlation": corr_matrix.loc[asset_a, asset_b],
                    }
                )
    return rows


class CorrelationAnalyzer:
    """
    Comprehensive correlation analyzer for portfolio risk assessment.

    Example:
        >>> analyzer = CorrelationAnalyzer(returns_df)
        >>> print(f"Average correlation: {analyzer.average_correlation:.2f}")
        >>> print(f"Max correlated pair: {analyzer.max_correlation_pair}")
    """

    def __init__(
        self,
        returns_df: pd.DataFrame,
        window: int = 30,
        method: Literal["pearson", "spearman", "kendall"] = "pearson",
    ):
        """
        Initialize correlation analyzer.

        Args:
            returns_df: DataFrame with columns as assets/strategies.
            window: Rolling window for correlation calculations.
            method: Correlation method.
        """
        self.returns_df = returns_df
        self.window = window
        self.method = method
        self._corr_matrix: pd.DataFrame | None = None
        self._rolling_corr: pd.DataFrame | None = None

    @property
    def correlation_matrix(self) -> pd.DataFrame:
        """Static correlation matrix (cached)."""
        if self._corr_matrix is None:
            self._corr_matrix = calculate_correlation_matrix(self.returns_df, self.method)
        return self._corr_matrix

    @property
    def rolling_correlation(self) -> pd.DataFrame:
        """Rolling correlation matrix (cached)."""
        if self._rolling_corr is None:
            self._rolling_corr = calculate_rolling_correlation(
                self.returns_df, self.window, self.method
            )
        return self._rolling_corr

    @property
    def average_correlation(self) -> float:
        """Average pairwise correlation."""
        return calculate_average_correlation(self.correlation_matrix.copy())

    @property
    def max_correlation_pair(self) -> tuple[float, tuple[str, str]]:
        """Most correlated pair."""
        return calculate_max_correlation(self.correlation_matrix.copy())

    @property
    def min_correlation_pair(self) -> tuple[float, tuple[str, str]]:
        """Least correlated pair (most diversifying)."""
        return calculate_min_correlation(self.correlation_matrix.copy())

    @property
    def diversification_score(self) -> float:
        """
        Diversification score (0-100).

        100 = perfectly uncorrelated portfolio
        0 = perfectly correlated portfolio
        """
        avg_corr = self.average_correlation
        # Map [-1, 1] to [100, 0]
        return (1 - avg_corr) * 50

    def summary(self) -> dict:
        """Return all correlation metrics as a dictionary."""
        max_corr, max_pair = self.max_correlation_pair
        min_corr, min_pair = self.min_correlation_pair

        return {
            "average_correlation": self.average_correlation,
            "max_correlation": max_corr,
            "max_correlation_pair": max_pair,
            "min_correlation": min_corr,
            "min_correlation_pair": min_pair,
            "diversification_score": self.diversification_score,
            "n_assets": len(self.returns_df.columns),
            "n_observations": len(self.returns_df),
        }
