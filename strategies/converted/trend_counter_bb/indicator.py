"""
Trend Counter Indicator - BigBeluga Style.

Converted from Pine Script pattern:
    float mid = math.avg(ta.highest(length), ta.lowest(length))
    for offset = 0 to length - 1
        switch
            hl2 > mid[offset] => counter += 1.0
            => counter := 0.0
    counter := math.round(ta.ema(counter > 400 ? 400 : counter, smooth))

This indicator counts consecutive bars above/below the midline,
providing a trend strength measure with smoothing.
"""

from __future__ import annotations

from collections import deque
from enum import IntEnum
from typing import TYPE_CHECKING

from nautilus_trader.indicators import ExponentialMovingAverage, Indicator

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar


class Trend(IntEnum):
    """Trend direction enum (replaces Pine Script color coding)."""

    STRONG_DOWN = -2
    DOWN = -1
    NEUTRAL = 0
    UP = 1
    STRONG_UP = 2


class TrendCounterIndicator(Indicator):
    """
    Trend Counter indicator based on BigBeluga pattern.

    Counts consecutive bars where hl2 is above/below the midpoint
    of highest/lowest over the lookback period. Applies EMA smoothing.

    Parameters
    ----------
    length : int
        Lookback period for highest/lowest calculation.
    smooth : int
        EMA smoothing period for the counter.

    Outputs
    -------
    value : float
        Smoothed trend counter (0-100 normalized).
    trend : Trend
        Current trend direction.
    strength : float
        Trend strength (0-1 normalized).
    """

    def __init__(self, length: int = 20, smooth: int = 5) -> None:
        """Initialize the Trend Counter indicator."""
        super().__init__([length, smooth])

        if length < 2:
            raise ValueError(f"length must be >= 2, got {length}")
        if smooth < 1:
            raise ValueError(f"smooth must be >= 1, got {smooth}")

        self.length = length
        self.smooth = smooth

        # Buffers for highest/lowest calculation
        self._highs: deque[float] = deque(maxlen=length)
        self._lows: deque[float] = deque(maxlen=length)
        self._mids: deque[float] = deque(maxlen=length)
        self._hl2_buffer: deque[float] = deque(maxlen=length)

        # EMA for smoothing counter
        self._counter_ema = ExponentialMovingAverage(smooth)

        # Raw counter before smoothing
        self._raw_counter: float = 0.0

        # Outputs
        self.value: float = 0.0
        self.trend: Trend = Trend.NEUTRAL
        self.strength: float = 0.0

        # Average for comparison
        self._counter_avg: float = 0.0
        self._counter_history: deque[float] = deque(maxlen=50)

    @property
    def name(self) -> str:
        """Return indicator name."""
        return f"TrendCounter({self.length},{self.smooth})"

    def handle_bar(self, bar: Bar) -> None:
        """
        Handle incoming bar data.

        Parameters
        ----------
        bar : Bar
            The bar to process.
        """
        high = float(bar.high)
        low = float(bar.low)
        hl2 = (high + low) / 2.0

        # Add to buffers
        self._highs.append(high)
        self._lows.append(low)
        self._hl2_buffer.append(hl2)

        # Need full buffer for calculation
        if len(self._highs) < self.length:
            return

        # Calculate midpoint: avg(highest, lowest)
        highest = max(self._highs)
        lowest = min(self._lows)
        mid = (highest + lowest) / 2.0
        self._mids.append(mid)

        # Count consecutive bars where hl2 > mid[offset]
        # Pine: for offset = 0 to length - 1
        counter = 0.0
        mids_list = list(self._mids)
        hl2_list = list(self._hl2_buffer)

        for offset in range(min(len(mids_list), self.length)):
            # Compare current hl2 with historical mid values
            if len(hl2_list) > offset and len(mids_list) > offset:
                if hl2_list[-(offset + 1)] > mids_list[-(offset + 1)]:
                    counter += 1.0
                else:
                    # Pine: => counter := 0.0 (resets on any fail)
                    break

        # Cap at 400 (Pine: counter > 400 ? 400 : counter)
        self._raw_counter = min(counter, 400.0)

        # Apply EMA smoothing
        self._counter_ema.update_raw(self._raw_counter)

        if not self._counter_ema.initialized:
            return

        # Store smoothed value
        smoothed = round(self._counter_ema.value)
        self.value = smoothed

        # Track history for average
        self._counter_history.append(smoothed)
        if len(self._counter_history) > 0:
            self._counter_avg = sum(self._counter_history) / len(self._counter_history)

        # Determine trend (replaces Pine color logic)
        self._calculate_trend()

        # Mark as initialized
        self._set_initialized(True)

    def _calculate_trend(self) -> None:
        """Calculate trend direction and strength from counter value."""
        # Normalize to 0-1 (assuming max meaningful counter is 100)
        max_expected = min(self.length, 100)
        self.strength = min(1.0, self.value / max_expected)

        # Trend based on value vs average
        if self.value > self._counter_avg * 1.5:
            self.trend = Trend.STRONG_UP
        elif self.value > self._counter_avg:
            self.trend = Trend.UP
        elif self.value < self._counter_avg * 0.5:
            self.trend = Trend.STRONG_DOWN if self.value < 2 else Trend.DOWN
        elif self.value < self._counter_avg:
            self.trend = Trend.DOWN
        else:
            self.trend = Trend.NEUTRAL

    def reset(self) -> None:
        """Reset the indicator state."""
        self._highs.clear()
        self._lows.clear()
        self._mids.clear()
        self._hl2_buffer.clear()
        self._counter_history.clear()
        self._counter_ema.reset()
        self._raw_counter = 0.0
        self.value = 0.0
        self.trend = Trend.NEUTRAL
        self.strength = 0.0
        self._counter_avg = 0.0
        self._set_initialized(False)
