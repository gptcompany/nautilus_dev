"""Feature engineering for meta-model training.

This module provides feature extraction utilities for the meta-learning pipeline.
Features are designed to capture market conditions that predict primary model accuracy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def extract_meta_features(
    prices: NDArray[np.floating],
    atr_values: NDArray[np.floating] | None = None,
    volumes: NDArray[np.floating] | None = None,
    regime_states: NDArray[np.signedinteger] | None = None,
    lookback: int = 20,
) -> NDArray[np.floating]:
    """Extract features for meta-model training.

    Computes features that help predict whether the primary model's signal
    will be correct. Features focus on volatility, momentum, and market state.

    Args:
        prices: Close prices array.
        atr_values: ATR values for volatility normalization (optional).
        volumes: Volume data for volume-based features (optional).
        regime_states: HMM/GMM regime states if available (optional).
        lookback: Lookback period for rolling calculations.

    Returns:
        Feature matrix of shape (n_samples, n_features).
        Features include:
        - volatility: Rolling standard deviation of returns
        - normalized_atr: ATR / price ratio
        - momentum: Recent return over lookback period
        - vol_of_vol: Volatility of volatility
        - trend_strength: Absolute momentum normalized by volatility
        - mean_reversion: Distance from rolling mean normalized by volatility
    """
    n = len(prices)

    # Calculate returns
    returns = np.zeros(n)
    returns[1:] = np.diff(np.log(prices))

    # Feature 1: Rolling volatility (std of returns)
    volatility = _rolling_std(returns, lookback)

    # Feature 2: Normalized ATR (ATR / price)
    if atr_values is not None:
        normalized_atr = atr_values / prices
    else:
        # Approximate ATR from price range
        normalized_atr = volatility * np.sqrt(252)  # Annualized vol as proxy

    # Feature 3: Momentum (return over lookback period)
    momentum = _rolling_return(prices, lookback)

    # Feature 4: Volatility of volatility
    vol_of_vol = _rolling_std(volatility, lookback)

    # Feature 5: Trend strength (|momentum| / volatility)
    # Avoid division by zero
    safe_vol = np.where(volatility > 1e-10, volatility, 1e-10)
    trend_strength = np.abs(momentum) / safe_vol

    # Feature 6: Mean reversion indicator
    rolling_mean = _rolling_mean(prices, lookback)
    price_deviation = (prices - rolling_mean) / rolling_mean
    mean_reversion = price_deviation / safe_vol

    # Stack features
    features = np.column_stack(
        [
            volatility,
            normalized_atr,
            momentum,
            vol_of_vol,
            trend_strength,
            mean_reversion,
        ]
    )

    # Add volume features if available
    if volumes is not None:
        volume_ratio = _volume_ratio(volumes, lookback)
        features = np.column_stack([features, volume_ratio])

    # Add regime state if available
    if regime_states is not None:
        features = np.column_stack([features, regime_states.astype(np.float64)])

    # Replace NaN/Inf with 0 for warmup period
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    return features.astype(np.float64)


def _rolling_std(arr: NDArray[np.floating], window: int) -> NDArray[np.floating]:
    """Calculate rolling standard deviation.

    Uses vectorized approach for efficiency.
    """
    n = len(arr)
    result = np.zeros(n)

    if n < window:
        return result

    # Use cumsum trick for O(n) computation
    arr_sq = arr**2
    cumsum = np.cumsum(arr)
    cumsum_sq = np.cumsum(arr_sq)

    # Compute variance for each window
    for i in range(window - 1, n):
        start = i - window + 1
        if start == 0:
            window_sum = cumsum[i]
            window_sum_sq = cumsum_sq[i]
        else:
            window_sum = cumsum[i] - cumsum[start - 1]
            window_sum_sq = cumsum_sq[i] - cumsum_sq[start - 1]

        mean = window_sum / window
        variance = window_sum_sq / window - mean**2
        result[i] = np.sqrt(max(variance, 0))

    return result


def _rolling_mean(arr: NDArray[np.floating], window: int) -> NDArray[np.floating]:
    """Calculate rolling mean."""
    n = len(arr)
    result = np.zeros(n)

    if n < window:
        return arr.copy()

    cumsum = np.cumsum(arr)

    for i in range(n):
        if i < window - 1:
            result[i] = cumsum[i] / (i + 1)
        else:
            start = i - window + 1
            if start == 0:
                result[i] = cumsum[i] / window
            else:
                result[i] = (cumsum[i] - cumsum[start - 1]) / window

    return result


def _rolling_return(prices: NDArray[np.floating], window: int) -> NDArray[np.floating]:
    """Calculate rolling return over window."""
    n = len(prices)
    result = np.zeros(n)

    for i in range(window, n):
        result[i] = (prices[i] - prices[i - window]) / prices[i - window]

    return result


def _volume_ratio(volumes: NDArray[np.floating], window: int) -> NDArray[np.floating]:
    """Calculate volume relative to rolling average."""
    rolling_avg = _rolling_mean(volumes, window)
    # Avoid division by zero
    safe_avg = np.where(rolling_avg > 0, rolling_avg, 1.0)
    result = volumes / safe_avg
    from typing import cast

    return cast(NDArray[np.floating], result)


def get_feature_names(
    has_volumes: bool = False,
    has_regime: bool = False,
) -> list[str]:
    """Get list of feature names for interpretation.

    Args:
        has_volumes: Whether volume features are included.
        has_regime: Whether regime state is included.

    Returns:
        List of feature names in order.
    """
    names = [
        "volatility",
        "normalized_atr",
        "momentum",
        "vol_of_vol",
        "trend_strength",
        "mean_reversion",
    ]

    if has_volumes:
        names.append("volume_ratio")

    if has_regime:
        names.append("regime_state")

    return names
