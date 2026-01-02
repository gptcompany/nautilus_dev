"""Data transformation utilities for regime detection.

Provides vectorized calculations for returns and volatility.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def calculate_returns(prices: NDArray[np.float64]) -> NDArray[np.float64]:
    """Calculate log returns from price series.

    Args:
        prices: Array of prices (OHLC close or similar).

    Returns:
        Array of log returns, length = len(prices) - 1.

    Raises:
        ValueError: If prices contains zeros or negative values.
    """
    if len(prices) < 2:
        return np.array([], dtype=np.float64)

    if np.any(prices <= 0):
        raise ValueError("Prices must be positive")

    return np.diff(np.log(prices))


def calculate_volatility(
    returns: NDArray[np.float64],
    window: int = 20,
) -> NDArray[np.float64]:
    """Calculate rolling volatility (standard deviation of returns).

    Args:
        returns: Array of returns.
        window: Rolling window size.

    Returns:
        Array of rolling volatility values. First (window-1) values are NaN.
    """
    if len(returns) < window:
        return np.full(len(returns), np.nan, dtype=np.float64)

    # Efficient rolling std using stride tricks
    result = np.full(len(returns), np.nan, dtype=np.float64)
    for i in range(window - 1, len(returns)):
        result[i] = np.std(returns[i - window + 1 : i + 1], ddof=1)

    return result


def calculate_atr(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int = 14,
) -> NDArray[np.float64]:
    """Calculate Average True Range (ATR).

    Args:
        high: Array of high prices.
        low: Array of low prices.
        close: Array of close prices.
        period: ATR period.

    Returns:
        Array of ATR values. First (period) values are NaN.
    """
    if len(high) < period + 1:
        return np.full(len(high), np.nan, dtype=np.float64)

    # True Range components
    tr1 = high[1:] - low[1:]  # High - Low
    tr2 = np.abs(high[1:] - close[:-1])  # |High - Previous Close|
    tr3 = np.abs(low[1:] - close[:-1])  # |Low - Previous Close|

    tr = np.maximum(tr1, np.maximum(tr2, tr3))

    # Prepend NaN for first bar (no previous close)
    tr = np.concatenate([[np.nan], tr])

    # Calculate ATR using EMA-style smoothing
    result = np.full(len(high), np.nan, dtype=np.float64)
    result[period] = np.nanmean(tr[1 : period + 1])

    alpha = 1.0 / period
    for i in range(period + 1, len(high)):
        result[i] = alpha * tr[i] + (1 - alpha) * result[i - 1]

    return result


def normalize_features(
    features: NDArray[np.float64],
) -> tuple[NDArray[np.float64], float, float]:
    """Normalize features to zero mean and unit variance.

    Args:
        features: Array of feature values.

    Returns:
        Tuple of (normalized_features, mean, std).
    """
    mean = np.nanmean(features)
    std = np.nanstd(features)
    if std == 0 or np.isnan(std):
        std = 1.0
    normalized = (features - mean) / std
    return normalized, mean, std
