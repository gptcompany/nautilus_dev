"""
Sample backtest data fixtures for tearsheet testing.

This module provides sample data for testing tearsheet generation
without requiring full NautilusTrader backtest execution.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def generate_sample_returns(
    start_date: str = "2023-01-01",
    periods: int = 252,
    freq: str = "D",
    mean_return: float = 0.0005,
    volatility: float = 0.015,
    seed: int = 42,
) -> pd.Series:
    """
    Generate sample returns series for testing.

    Parameters
    ----------
    start_date : str
        Start date for the series.
    periods : int
        Number of periods to generate.
    freq : str
        Frequency (D for daily, h for hourly).
    mean_return : float
        Mean return per period.
    volatility : float
        Standard deviation of returns.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.Series
        Returns series with DatetimeIndex.
    """
    np.random.seed(seed)
    dates = pd.date_range(start_date, periods=periods, freq=freq)
    returns = np.random.normal(mean_return, volatility, periods)
    return pd.Series(returns, index=dates, name="returns")


def generate_sample_pnl_stats(
    total_pnl: float = 1500.50,
    currency: str = "USDT",
) -> dict[str, dict[str, Any]]:
    """
    Generate sample PnL statistics.

    Parameters
    ----------
    total_pnl : float
        Total profit/loss.
    currency : str
        Base currency.

    Returns
    -------
    dict
        PnL statistics in NautilusTrader format.
    """
    return {
        currency: {
            "PnL (total)": total_pnl,
            "PnL (realized)": total_pnl,
            "PnL (unrealized)": 0.0,
            "Commission (total)": -50.0,
        }
    }


def generate_sample_returns_stats(
    sharpe: float = 1.25,
    sortino: float = 1.85,
    calmar: float = 2.1,
    max_drawdown: float = -0.12,
) -> dict[str, Any]:
    """
    Generate sample returns statistics.

    Parameters
    ----------
    sharpe : float
        Sharpe ratio.
    sortino : float
        Sortino ratio.
    calmar : float
        Calmar ratio.
    max_drawdown : float
        Maximum drawdown (negative).

    Returns
    -------
    dict
        Returns statistics in NautilusTrader format.
    """
    return {
        "Sharpe Ratio (252 days)": sharpe,
        "Sortino Ratio (252 days)": sortino,
        "Calmar Ratio": calmar,
        "Max Drawdown": max_drawdown,
        "Avg Drawdown": max_drawdown / 2,
        "Daily Avg Return": 0.0005,
        "Daily Std Return": 0.015,
        "Annualized Return": 0.126,
        "Annualized Volatility": 0.238,
    }


def generate_sample_general_stats(
    total_trades: int = 150,
    win_rate: float = 0.55,
    profit_factor: float = 1.8,
) -> dict[str, Any]:
    """
    Generate sample general statistics.

    Parameters
    ----------
    total_trades : int
        Total number of trades.
    win_rate : float
        Win rate (0-1).
    profit_factor : float
        Profit factor.

    Returns
    -------
    dict
        General statistics in NautilusTrader format.
    """
    return {
        "Total Trades": total_trades,
        "Win Rate": win_rate,
        "Profit Factor": profit_factor,
        "Avg Trade Duration": "2h 30m",
        "Avg Winner": 50.0,
        "Avg Loser": -30.0,
        "Largest Winner": 500.0,
        "Largest Loser": -200.0,
        "Expectancy": 15.0,
        "Long Trades": int(total_trades * 0.6),
        "Short Trades": int(total_trades * 0.4),
    }


def generate_sample_ohlc(
    start_date: str = "2023-01-01",
    periods: int = 252,
    initial_price: float = 30000.0,
    volatility: float = 0.02,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate sample OHLC data for BTCUSDT.

    Parameters
    ----------
    start_date : str
        Start date for the series.
    periods : int
        Number of periods (days).
    initial_price : float
        Starting price.
    volatility : float
        Daily volatility.
    seed : int
        Random seed.

    Returns
    -------
    pd.DataFrame
        OHLC DataFrame with DatetimeIndex.
    """
    np.random.seed(seed)
    dates = pd.date_range(start_date, periods=periods, freq="D")

    # Generate price path
    returns = np.random.normal(0.0, volatility, periods)
    close_prices = initial_price * np.cumprod(1 + returns)

    # Generate OHLC from close prices
    ohlc = pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.uniform(-0.005, 0.005, periods)),
            "high": close_prices * (1 + np.abs(np.random.normal(0, 0.01, periods))),
            "low": close_prices * (1 - np.abs(np.random.normal(0, 0.01, periods))),
            "close": close_prices,
            "volume": np.random.uniform(1000, 10000, periods),
        },
        index=dates,
    )

    # Ensure high >= max(open, close) and low <= min(open, close)
    ohlc["high"] = ohlc[["open", "high", "close"]].max(axis=1)
    ohlc["low"] = ohlc[["open", "low", "close"]].min(axis=1)

    return ohlc


# =============================================================================
# Pre-generated Sample Data (for consistent testing)
# =============================================================================

# 1-year daily BTCUSDT sample data
SAMPLE_RETURNS_1Y = generate_sample_returns(periods=252)
SAMPLE_PNL_STATS = generate_sample_pnl_stats()
SAMPLE_RETURNS_STATS = generate_sample_returns_stats()
SAMPLE_GENERAL_STATS = generate_sample_general_stats()
SAMPLE_OHLC_1Y = generate_sample_ohlc(periods=252)

# 2-year data for heatmap testing
SAMPLE_RETURNS_2Y = generate_sample_returns(
    start_date="2022-01-01",
    periods=504,  # ~2 years
    seed=43,
)

# 10-year data for long backtest testing
SAMPLE_RETURNS_10Y = generate_sample_returns(
    start_date="2013-01-01",
    periods=2520,  # ~10 years
    seed=44,
)

# High-frequency data (hourly for 1 month)
SAMPLE_RETURNS_HF = generate_sample_returns(
    start_date="2023-01-01",
    periods=24 * 30,  # 30 days of hourly
    freq="h",
    mean_return=0.00005,
    volatility=0.002,
    seed=45,
)
