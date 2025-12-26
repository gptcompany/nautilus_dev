"""
Validation helpers for NautilusTrader tearsheet data.

This module provides validation functions to verify that equity curves,
drawdowns, and trade metrics are correctly extracted from backtest results.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from nautilus_trader.backtest.engine import BacktestEngine

_logger = logging.getLogger(__name__)


def validate_equity_curve(engine: "BacktestEngine") -> tuple[bool, str]:
    """
    Validate equity curve data from engine.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    tuple[bool, str]
        (is_valid, message) tuple.
    """
    try:
        returns = engine.portfolio.analyzer.returns()

        if returns is None:
            return False, "Returns series is None"

        if len(returns) == 0:
            return False, "Returns series is empty"

        if not isinstance(returns.index, pd.DatetimeIndex):
            return False, "Returns index is not DatetimeIndex"

        # Check for NaN values
        nan_count = returns.isna().sum()
        if nan_count > 0:
            _logger.warning(f"Returns contains {nan_count} NaN values")

        # Check for extreme values (likely data errors)
        extreme_threshold = 0.5  # 50% daily return is suspicious
        extreme_count = (returns.abs() > extreme_threshold).sum()
        if extreme_count > 0:
            _logger.warning(
                f"Returns contains {extreme_count} extreme values (>50% daily)"
            )

        return True, f"Valid equity curve with {len(returns)} data points"

    except Exception as e:
        return False, f"Error validating equity curve: {e}"


def validate_drawdown(engine: "BacktestEngine") -> tuple[bool, str]:
    """
    Validate drawdown data from engine.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    tuple[bool, str]
        (is_valid, message) tuple.
    """
    try:
        returns = engine.portfolio.analyzer.returns()

        if len(returns) == 0:
            return False, "Cannot calculate drawdown from empty returns"

        # Calculate drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max

        # Verify drawdown properties
        if drawdown.max() > 0:
            return False, f"Drawdown has positive values (max={drawdown.max():.4f})"

        # Get max drawdown from stats
        stats = engine.portfolio.analyzer.get_performance_stats_returns()
        reported_max_dd = stats.get("Max Drawdown", 0.0)
        calculated_max_dd = drawdown.min()

        # Allow small tolerance for floating point
        if abs(reported_max_dd - calculated_max_dd) > 0.001:
            _logger.debug(
                f"Max drawdown mismatch: reported={reported_max_dd:.4f}, "
                f"calculated={calculated_max_dd:.4f}"
            )

        return True, f"Valid drawdown (max={calculated_max_dd:.2%})"

    except Exception as e:
        return False, f"Error validating drawdown: {e}"


def validate_returns_data(engine: "BacktestEngine") -> tuple[bool, str]:
    """
    Validate returns data for heatmap generation.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    tuple[bool, str]
        (is_valid, message) tuple.
    """
    try:
        returns = engine.portfolio.analyzer.returns()

        if len(returns) == 0:
            return False, "Returns series is empty"

        # Check date range
        start_date = returns.index.min()
        end_date = returns.index.max()
        date_range = (end_date - start_date).days

        if date_range < 30:
            return False, f"Returns span only {date_range} days (need 30+ for heatmap)"

        # Check for monthly aggregation capability
        monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        if len(monthly) == 0:
            return False, "Cannot aggregate to monthly returns"

        return True, f"Valid returns data: {start_date.date()} to {end_date.date()}"

    except Exception as e:
        return False, f"Error validating returns data: {e}"


def validate_trade_metrics(engine: "BacktestEngine") -> tuple[bool, str]:
    """
    Validate trade metrics from engine.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    tuple[bool, str]
        (is_valid, message) tuple.
    """
    try:
        stats = engine.portfolio.analyzer.get_performance_stats_general()

        required_fields = ["Win Rate", "Profit Factor", "Total Trades"]
        missing = [f for f in required_fields if f not in stats]

        if missing:
            return False, f"Missing required fields: {missing}"

        total_trades = stats.get("Total Trades", 0)
        if total_trades == 0:
            return False, "No trades to analyze"

        win_rate = stats.get("Win Rate", 0.0)
        if not 0 <= win_rate <= 1:
            return False, f"Invalid win rate: {win_rate}"

        profit_factor = stats.get("Profit Factor", 0.0)
        if profit_factor < 0:
            return False, f"Invalid profit factor: {profit_factor}"

        return (
            True,
            f"Valid trade metrics: {total_trades} trades, {win_rate:.1%} win rate",
        )

    except Exception as e:
        return False, f"Error validating trade metrics: {e}"


def run_all_validations(engine: "BacktestEngine") -> dict[str, tuple[bool, str]]:
    """
    Run all validation checks on engine data.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    dict[str, tuple[bool, str]]
        Validation name to (is_valid, message) mapping.
    """
    return {
        "equity_curve": validate_equity_curve(engine),
        "drawdown": validate_drawdown(engine),
        "returns_data": validate_returns_data(engine),
        "trade_metrics": validate_trade_metrics(engine),
    }
