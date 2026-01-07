"""Barrier calculation helpers for triple barrier labeling.

Provides vectorized helper functions for calculating vertical (timeout)
and horizontal (TP/SL) barriers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def get_vertical_barriers(
    n: int,
    max_holding_bars: int,
) -> NDArray[np.signedinteger]:
    """Calculate vertical barrier (timeout) indices.

    For each entry index i, the vertical barrier is at i + max_holding_bars,
    capped at n-1 (the last valid index).

    Args:
        n: Length of price series.
        max_holding_bars: Maximum holding period in bars.

    Returns:
        Array of timeout indices for each entry point.

    Example:
        >>> barriers = get_vertical_barriers(100, 10)
        >>> barriers[0]  # Entry at 0, timeout at 10
        10
        >>> barriers[95]  # Entry at 95, timeout capped at 99
        99
    """
    if n == 0:
        return np.array([], dtype=np.int64)

    indices = np.arange(n, dtype=np.int64)
    barriers_raw = indices + max_holding_bars

    # Cap at last valid index
    from typing import cast

    result = np.minimum(barriers_raw, n - 1).astype(np.int64)
    return cast(NDArray[np.signedinteger], result)


def get_horizontal_barriers(
    prices: NDArray[np.floating],
    atr_values: NDArray[np.floating],
    pt_multiplier: float,
    sl_multiplier: float,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """Calculate horizontal barriers (take-profit and stop-loss) for each entry.

    Args:
        prices: Close prices at entry points.
        atr_values: ATR values at entry points.
        pt_multiplier: Take-profit distance as multiple of ATR.
        sl_multiplier: Stop-loss distance as multiple of ATR.

    Returns:
        Tuple of (tp_barriers, sl_barriers) arrays.

    Example:
        >>> prices = np.array([100.0, 105.0])
        >>> atr = np.array([2.0, 2.5])
        >>> tp, sl = get_horizontal_barriers(prices, atr, 2.0, 1.0)
        >>> tp[0]  # 100 + 2*2 = 104
        104.0
        >>> sl[0]  # 100 - 1*2 = 98
        98.0
    """
    tp_barriers = prices + (pt_multiplier * atr_values)
    sl_barriers = prices - (sl_multiplier * atr_values)

    return tp_barriers, sl_barriers


def check_barrier_hit(
    prices: NDArray[np.floating],
    entry_idx: int,
    timeout_idx: int,
    tp_barrier: float,
    sl_barrier: float,
) -> tuple[int, int]:
    """Check which barrier is hit first for a single entry.

    Scans from entry_idx+1 to timeout_idx to find first barrier touch.

    Args:
        prices: Full price series.
        entry_idx: Entry bar index.
        timeout_idx: Timeout bar index (vertical barrier).
        tp_barrier: Take-profit price level.
        sl_barrier: Stop-loss price level.

    Returns:
        Tuple of (exit_idx, label):
        - label = +1 if TP hit first
        - label = -1 if SL hit first
        - label = 0 if timeout (no barrier hit)
    """
    for j in range(entry_idx + 1, timeout_idx + 1):
        if j >= len(prices):
            break

        price = prices[j]

        # Check TP first (could also check SL first, doesn't matter much)
        if price >= tp_barrier:
            return j, 1
        if price <= sl_barrier:
            return j, -1

    # Timeout - use sign of final return
    if timeout_idx < len(prices):
        final_return = prices[timeout_idx] - prices[entry_idx]
        if final_return > 0:
            return timeout_idx, 1
        elif final_return < 0:
            return timeout_idx, -1
    return timeout_idx, 0
