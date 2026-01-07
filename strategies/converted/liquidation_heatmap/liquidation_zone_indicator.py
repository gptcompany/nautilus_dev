"""
Liquidation Zone Indicator for NautilusTrader.

Converted from: Liquidation HeatMap [BigBeluga]
Source: https://www.tradingview.com/script/tMtleB1G-Liqudation-HeatMap-BigBeluga/
License: CC BY-NC-SA 4.0

This indicator identifies potential liquidation zones based on:
- Pivot highs and lows with elevated volume
- ATR-based zone width
- Zone "consumption" when price crosses through midpoint
"""

from collections import deque
from dataclasses import dataclass

from nautilus_trader.indicators import AverageTrueRange, Indicator
from nautilus_trader.model.data import Bar


@dataclass
class LiquidationZone:
    """Represents a liquidation zone (potential stop-loss cluster)."""

    start_bar_idx: int
    top: float
    bottom: float
    volume_intensity: float  # 0.0 to 1.0, higher = more volume
    is_above_price: bool  # True if zone is above current price (from pivot high)
    consumed: bool = False

    @property
    def midpoint(self) -> float:
        """Get zone midpoint for consumption detection."""
        return (self.top + self.bottom) / 2.0

    def is_price_through(self, high: float, low: float) -> bool:
        """Check if price bar has crossed through zone midpoint."""
        mid = self.midpoint
        return high > mid and low < mid


class LiquidationZoneIndicator(Indicator):
    """
    Liquidation Zone Indicator.

    Identifies potential liquidation/stop-loss clusters based on:
    - Pivot high/low detection
    - Volume intensity at pivot points
    - ATR-based zone width

    Zones are "consumed" (removed) when price crosses through their midpoint.

    Parameters
    ----------
    atr_period : int
        Period for ATR calculation (default 200).
    pivot_lookback : int
        Bars to look back for pivot detection (default 2).
    max_zones : int
        Maximum number of active zones to track (default 500).
    atr_multiplier_minutes : float
        ATR multiplier for minute timeframes (default 0.25).
    atr_multiplier_hourly : float
        ATR multiplier for hourly+ timeframes (default 0.2).
    atr_multiplier_daily : float
        ATR multiplier for daily timeframes (default 0.2).
    """

    def __init__(
        self,
        atr_period: int = 200,
        pivot_lookback: int = 2,
        max_zones: int = 500,
        atr_multiplier: float = 0.25,
    ) -> None:
        super().__init__([])

        self.atr_period = atr_period
        self.pivot_lookback = pivot_lookback
        self.max_zones = max_zones
        self.atr_multiplier = atr_multiplier

        # Native Rust ATR indicator
        self._atr = AverageTrueRange(period=atr_period)

        # Bar history for pivot detection
        self._bar_history: deque[Bar] = deque(maxlen=pivot_lookback * 2 + 1)

        # Volume history for intensity calculation
        self._volume_history: deque[float] = deque(maxlen=max_zones)

        # Active liquidation zones
        self._zones: list[LiquidationZone] = []

        # Bar counter
        self._bar_count: int = 0

        # Cached values
        self._last_zone_above: LiquidationZone | None = None
        self._last_zone_below: LiquidationZone | None = None

    @property
    def name(self) -> str:
        return f"LiquidationZone({self.atr_period},{self.pivot_lookback})"

    @property
    def has_inputs(self) -> bool:
        return len(self._bar_history) > 0

    @property
    def initialized(self) -> bool:
        return self._atr.initialized and len(self._bar_history) >= self.pivot_lookback * 2 + 1

    @property
    def zones(self) -> list[LiquidationZone]:
        """Get active (non-consumed) liquidation zones."""
        return [z for z in self._zones if not z.consumed]

    @property
    def zones_above_price(self) -> list[LiquidationZone]:
        """Get zones above current price (from pivot highs)."""
        return [z for z in self.zones if z.is_above_price]

    @property
    def zones_below_price(self) -> list[LiquidationZone]:
        """Get zones below current price (from pivot lows)."""
        return [z for z in self.zones if not z.is_above_price]

    @property
    def nearest_zone_above(self) -> LiquidationZone | None:
        """Get nearest unconsumed zone above current price."""
        if not self._bar_history:
            return None
        current_close = float(self._bar_history[-1].close)
        above = [z for z in self.zones if z.bottom > current_close]
        if not above:
            return None
        return min(above, key=lambda z: z.bottom)

    @property
    def nearest_zone_below(self) -> LiquidationZone | None:
        """Get nearest unconsumed zone below current price."""
        if not self._bar_history:
            return None
        current_close = float(self._bar_history[-1].close)
        below = [z for z in self.zones if z.top < current_close]
        if not below:
            return None
        return max(below, key=lambda z: z.top)

    def handle_bar(self, bar: Bar) -> None:
        """Process a bar and update zones."""
        # Update ATR
        self._atr.handle_bar(bar)

        # Store bar
        self._bar_history.append(bar)
        self._bar_count += 1

        # Get volume (or use candle range as proxy)
        volume = float(bar.volume) if float(bar.volume) > 0 else float(bar.high - bar.low) * 100
        self._volume_history.append(volume)

        if not self.initialized:
            return

        # Detect pivot points and create zones
        self._detect_pivots(bar)

        # Check for zone consumption
        self._check_zone_consumption(bar)

        # Clean up old zones
        self._cleanup_zones()

    def _detect_pivots(self, bar: Bar) -> None:
        """Detect pivot highs and lows, create zones."""
        if len(self._bar_history) < self.pivot_lookback * 2 + 1:
            return

        idx = self.pivot_lookback  # Middle bar in history
        bars = list(self._bar_history)

        # Get the middle bar (potential pivot)
        pivot_bar = bars[idx]
        pivot_high = float(pivot_bar.high)
        pivot_low = float(pivot_bar.low)

        # Check for pivot high
        is_pivot_high = True
        for i in range(len(bars)):
            if i != idx:
                if float(bars[i].high) >= pivot_high:
                    is_pivot_high = False
                    break

        # Check for pivot low
        is_pivot_low = True
        for i in range(len(bars)):
            if i != idx:
                if float(bars[i].low) <= pivot_low:
                    is_pivot_low = False
                    break

        if not (is_pivot_high or is_pivot_low):
            return

        # Calculate zone width using ATR
        atr_value = self._atr.value * self.atr_multiplier

        # Calculate volume intensity (0.0 to 1.0)
        if len(self._volume_history) > 0:
            volume = (
                self._volume_history[-self.pivot_lookback - 1]
                if len(self._volume_history) > self.pivot_lookback
                else self._volume_history[-1]
            )
            vol_avg = sum(self._volume_history) / len(self._volume_history)
            vol_max = max(self._volume_history)
            if vol_max > 0:
                intensity = (
                    min(1.0, volume / vol_max)
                    if volume > vol_avg
                    else volume / (vol_avg * 2)
                    if vol_avg > 0
                    else 0.5
                )
            else:
                intensity = 0.5
        else:
            intensity = 0.5

        # Create zones
        if is_pivot_high:
            zone = LiquidationZone(
                start_bar_idx=self._bar_count - self.pivot_lookback,
                top=pivot_high + atr_value,
                bottom=pivot_high,
                volume_intensity=intensity,
                is_above_price=True,
            )
            self._zones.append(zone)

        if is_pivot_low:
            zone = LiquidationZone(
                start_bar_idx=self._bar_count - self.pivot_lookback,
                top=pivot_low,
                bottom=pivot_low - atr_value,
                volume_intensity=intensity,
                is_above_price=False,
            )
            self._zones.append(zone)

    def _check_zone_consumption(self, bar: Bar) -> None:
        """Mark zones as consumed when price crosses through midpoint."""
        high = float(bar.high)
        low = float(bar.low)

        for zone in self._zones:
            if not zone.consumed and zone.is_price_through(high, low):
                zone.consumed = True

    def _cleanup_zones(self) -> None:
        """Remove excess zones to stay under max_zones."""
        active_zones = [z for z in self._zones if not z.consumed]
        if len(active_zones) > self.max_zones:
            # Remove oldest zones first
            active_zones.sort(key=lambda z: z.start_bar_idx)
            for zone in active_zones[: len(active_zones) - self.max_zones]:
                zone.consumed = True

        # Actually remove consumed zones periodically
        if self._bar_count % 100 == 0:
            self._zones = [z for z in self._zones if not z.consumed]

    def reset(self) -> None:
        """Reset the indicator."""
        self._atr.reset()
        self._bar_history.clear()
        self._volume_history.clear()
        self._zones.clear()
        self._bar_count = 0
        self._last_zone_above = None
        self._last_zone_below = None
