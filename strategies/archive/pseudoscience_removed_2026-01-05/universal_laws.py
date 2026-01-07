"""
Universal Laws - The Hidden Mathematics Behind Gann's Methods

W.D. Gann discovered that markets follow the same laws as nature:
- Logarithmic spirals (galaxies, shells, markets)
- Fibonacci/Golden ratio (plants, DNA, price retracements)
- Self-similarity/Fractals (coastlines, mountains, market charts)
- Natural cycles (seasons, moon phases, planetary alignments)

This module implements these universal patterns computationally,
without the mysticism - pure mathematics that appears everywhere.

References:
- Mandelbrot (1963): "The Variation of Certain Speculative Prices"
- Peters (1991): "Chaos and Order in the Capital Markets" (Fractal Market Hypothesis)
- Prechter & Frost: "Elliott Wave Principle" (Fibonacci in markets)
- D'Arcy Thompson (1917): "On Growth and Form" (Universal growth patterns)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# The Golden Ratio - φ (phi)
# Found in: DNA, galaxies, plants, markets, music, architecture
PHI = (1 + math.sqrt(5)) / 2  # 1.6180339887...

# Fibonacci sequence ratios (converge to phi)
FIBONACCI_RATIOS = [
    0.236,  # 1/φ^3
    0.382,  # 1/φ^2
    0.500,  # 1/2
    0.618,  # 1/φ (golden ratio inverse)
    0.786,  # sqrt(0.618)
    1.000,  # 1
    1.272,  # sqrt(φ)
    1.618,  # φ
    2.618,  # φ^2
    4.236,  # φ^3
]


@dataclass
class SpiralPoint:
    """Point on logarithmic spiral (Gann Square of 9)."""

    price: float
    angle_degrees: float
    radius: float
    harmonic_level: int  # Which "ring" of the spiral


@dataclass
class CycleInfo:
    """Detected natural cycle."""

    period: float  # In bars/samples
    amplitude: float
    phase: float
    confidence: float


class LogarithmicSpiral:
    """
    Logarithmic spiral - the shape of nature.

    Found in: Nautilus shells, galaxies, hurricanes, DNA helix,
              sunflower seeds, pine cones, AND Gann's Square of 9.

    The spiral equation: r = a * e^(b*θ)

    Where b = cot(α), and α ≈ 17.03° for the golden spiral.

    Gann's Square of 9:
    - Center = √price
    - Angles = 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°
    - Each full revolution = next "ring"

    Usage:
        spiral = LogarithmicSpiral()
        point = spiral.price_to_spiral(100.0)
        # Returns position on spiral

        # Find harmonic price levels
        levels = spiral.get_harmonic_levels(100.0)
    """

    def __init__(self, base: float = 1.0, growth_rate: float = 0.306349):
        """
        Args:
            base: Starting radius (a in r = a*e^(b*θ))
            growth_rate: Growth rate (b) - 0.306349 for golden spiral
        """
        self.base = base
        # Golden spiral growth rate: b = ln(φ) / (π/2)
        self.growth_rate = growth_rate

    def price_to_spiral(self, price: float) -> SpiralPoint:
        """
        Convert price to position on logarithmic spiral.

        This is the core of Gann's Square of 9.

        Args:
            price: Market price

        Returns:
            SpiralPoint with angle, radius, harmonic level
        """
        if price <= 0:
            return SpiralPoint(price=price, angle_degrees=0, radius=0, harmonic_level=0)

        # Gann's method: work with √price
        sqrt_price = math.sqrt(price)

        # Calculate angle (0-360 degrees per revolution)
        # Full revolution = 360°, but price increases each revolution
        angle_rad = sqrt_price * 2 * math.pi / 10  # Scale factor
        angle_deg = math.degrees(angle_rad) % 360

        # Calculate radius (distance from center)
        radius = self.base * math.exp(self.growth_rate * angle_rad)

        # Harmonic level (which "ring" of the spiral)
        harmonic_level = int(sqrt_price / 10)

        return SpiralPoint(
            price=price,
            angle_degrees=angle_deg,
            radius=radius,
            harmonic_level=harmonic_level,
        )

    def get_harmonic_levels(
        self,
        price: float,
        angles: list[float] | None = None,
    ) -> list[float]:
        """
        Get harmonic price levels from current price.

        Gann's key angles: 45°, 90°, 120°, 135°, 180°, 225°, 270°, 315°

        Args:
            price: Current price
            angles: List of angles in degrees (default: Gann's key angles)

        Returns:
            List of harmonic price levels
        """
        if angles is None:
            angles = [45, 90, 120, 135, 180, 225, 270, 315, 360]

        sqrt_price = math.sqrt(price)
        levels = []

        for angle in angles:
            # Add angle offset to find harmonic prices
            for direction in [-1, 1]:  # Both up and down
                offset = direction * angle / 360
                harmonic_sqrt = sqrt_price + offset
                if harmonic_sqrt > 0:
                    levels.append(harmonic_sqrt**2)

        return sorted(set(levels))


class FibonacciAnalyzer:
    """
    Fibonacci analysis - the growth pattern of life.

    Fibonacci appears in:
    - Plant leaf arrangements (phyllotaxis)
    - Shell spirals
    - DNA molecule dimensions
    - Musical harmonics
    - Market retracements (allegedly)

    The key insight: Fibonacci ratios converge to φ (golden ratio).

    Usage:
        fib = FibonacciAnalyzer()
        levels = fib.get_retracement_levels(high=100, low=80)
        # Returns key Fibonacci price levels
    """

    def __init__(self, ratios: list[float] | None = None):
        """
        Args:
            ratios: Custom Fibonacci ratios (default: standard set)
        """
        self.ratios = ratios or FIBONACCI_RATIOS

    def get_retracement_levels(
        self,
        high: float,
        low: float,
    ) -> dict[str, float]:
        """
        Calculate Fibonacci retracement levels.

        Args:
            high: Swing high price
            low: Swing low price

        Returns:
            Dict of ratio -> price level
        """
        range_size = high - low
        levels = {}

        for ratio in self.ratios:
            # Retracement from high
            levels[f"ret_{ratio}"] = high - (range_size * ratio)

        return levels

    def get_extension_levels(
        self,
        high: float,
        low: float,
        direction: int = 1,
    ) -> dict[str, float]:
        """
        Calculate Fibonacci extension levels.

        Args:
            high: Swing high price
            low: Swing low price
            direction: 1 for upward extensions, -1 for downward

        Returns:
            Dict of ratio -> price level
        """
        range_size = high - low
        levels = {}

        for ratio in self.ratios:
            if direction > 0:
                levels[f"ext_{ratio}"] = high + (range_size * ratio)
            else:
                levels[f"ext_{ratio}"] = low - (range_size * ratio)

        return levels

    def check_golden_ratio(
        self,
        a: float,
        b: float,
        tolerance: float = 0.05,
    ) -> bool:
        """
        Check if two values are in golden ratio.

        (a + b) / a = a / b = φ

        Args:
            a: Larger value
            b: Smaller value
            tolerance: Acceptable deviation from φ

        Returns:
            True if in golden ratio
        """
        if b == 0 or a == 0:
            return False

        ratio = a / b
        return abs(ratio - PHI) < tolerance


class FractalDimensionEstimator:
    """
    Fractal dimension - measuring self-similarity.

    If markets are fractal:
    - Same patterns appear at all timeframes
    - 1-minute chart looks like daily chart (scaled)
    - Dimension D ≈ 1.5 for random walk, higher for trending

    Methods:
    - Box-counting dimension
    - Hurst exponent (related: D = 2 - H)

    Usage:
        fde = FractalDimensionEstimator()
        dim = fde.estimate_box_counting(prices)
        hurst = fde.estimate_hurst(returns)
    """

    def estimate_hurst(self, returns: list[float], min_lag: int = 2) -> float:
        """
        Estimate Hurst exponent using R/S analysis.

        H = 0.5: Random walk (Brownian motion)
        H > 0.5: Persistent (trending)
        H < 0.5: Anti-persistent (mean reverting)

        Fractal dimension D = 2 - H

        Args:
            returns: List of returns
            min_lag: Minimum lag for analysis

        Returns:
            Hurst exponent (0 to 1)
        """
        import numpy as np

        n = len(returns)
        if n < min_lag * 2:
            return 0.5  # Default to random walk

        returns_arr = np.array(returns)

        # R/S analysis at different scales
        lags = []
        rs_values = []

        for lag in range(min_lag, n // 4):
            # Number of sub-series
            n_sub = n // lag

            rs_list = []
            for i in range(n_sub):
                sub = returns_arr[i * lag : (i + 1) * lag]
                if len(sub) < 2:
                    continue

                # Mean-adjusted cumulative deviation
                mean = np.mean(sub)
                cumdev = np.cumsum(sub - mean)

                # Range
                R = np.max(cumdev) - np.min(cumdev)

                # Standard deviation
                S = np.std(sub, ddof=1)

                if S > 0:
                    rs_list.append(R / S)

            if rs_list:
                lags.append(lag)
                rs_values.append(np.mean(rs_list))

        if len(lags) < 2:
            return 0.5

        # Linear regression in log-log space: log(R/S) = H * log(n)
        log_lags = np.log(lags)
        log_rs = np.log(rs_values)

        # Simple linear regression
        slope = float(np.polyfit(log_lags, log_rs, 1)[0])

        # Clamp to valid range
        return max(0.0, min(1.0, slope))

    def get_fractal_dimension(self, returns: list[float]) -> float:
        """
        Get fractal dimension from Hurst exponent.

        D = 2 - H

        D ≈ 1.5: Random (efficient market)
        D > 1.5: Mean reverting (rougher)
        D < 1.5: Trending (smoother)

        Args:
            returns: List of returns

        Returns:
            Fractal dimension (1 to 2)
        """
        H = self.estimate_hurst(returns)
        return 2 - H


class NaturalCycleDetector:
    """
    Natural cycle detection - rhythms of the universe.

    Natural cycles that Gann tracked:
    - Solar cycle: ~11 years
    - Lunar cycle: 29.5 days
    - Seasonal: 365.25 days
    - Weekly: 7 days (human/religious origin)
    - Daily: 24 hours

    Market cycles often align with:
    - Quarterly earnings (90 days)
    - Options expiration (monthly, weekly)
    - Economic data releases

    Usage:
        ncd = NaturalCycleDetector()
        cycles = ncd.detect_cycles(prices, max_period=365)
    """

    # Natural periods in days
    NATURAL_PERIODS = {
        "lunar": 29.5,
        "quarter": 90,
        "seasonal": 365.25,
        "solar_cycle": 4018,  # ~11 years
    }

    def detect_dominant_cycle(
        self,
        data: list[float],
        min_period: int = 5,
        max_period: int = 100,
    ) -> CycleInfo | None:
        """
        Detect the dominant cycle using autocorrelation.

        Simple O(n*m) method, no FFT needed.

        Args:
            data: Price or return series
            min_period: Minimum cycle length to detect
            max_period: Maximum cycle length to detect

        Returns:
            CycleInfo for dominant cycle, or None
        """
        import numpy as np

        n = len(data)
        if n < max_period * 2:
            max_period = n // 2

        if max_period < min_period:
            return None

        data_arr = np.array(data)
        mean = np.mean(data_arr)
        data_centered = data_arr - mean
        var = np.var(data_centered)

        if var == 0:
            return None

        best_period = min_period
        best_correlation = 0

        for period in range(min_period, max_period + 1):
            # Calculate autocorrelation at this lag
            autocorr = np.sum(data_centered[:-period] * data_centered[period:])
            autocorr /= (n - period) * var

            if autocorr > best_correlation:
                best_correlation = autocorr
                best_period = period

        if best_correlation < 0.1:  # Weak cycle
            return None

        return CycleInfo(
            period=float(best_period),
            amplitude=float(np.std(data_arr)),
            phase=0.0,  # Would need more complex analysis
            confidence=float(best_correlation),
        )

    def check_natural_alignment(
        self,
        detected_period: float,
        tolerance: float = 0.1,
    ) -> str | None:
        """
        Check if detected cycle aligns with known natural cycles.

        Args:
            detected_period: Detected cycle period in days
            tolerance: Acceptable deviation (as fraction)

        Returns:
            Name of matching natural cycle, or None
        """
        for name, natural_period in self.NATURAL_PERIODS.items():
            ratio = detected_period / natural_period
            # Check for harmonics (1x, 2x, 0.5x, etc.)
            for harmonic in [0.25, 0.5, 1, 2, 4]:
                if abs(ratio - harmonic) < tolerance:
                    return f"{name}_x{harmonic}"
        return None


class UniversalLawsAnalyzer:
    """
    Complete analyzer combining all universal patterns.

    This is what Gann knew but expressed through simple tools:
    - Square of 9 = Logarithmic spiral
    - Gann angles = Fibonacci ratios
    - Natural squares = Self-similarity
    - Time/price squaring = Fractal dimension

    Usage:
        ula = UniversalLawsAnalyzer()

        # Analyze current price
        analysis = ula.analyze(
            current_price=100.0,
            swing_high=120.0,
            swing_low=80.0,
            price_history=[...],
        )

        # Get key levels
        print(analysis["spiral_harmonics"])
        print(analysis["fibonacci_levels"])
        print(analysis["fractal_dimension"])
        print(analysis["dominant_cycle"])
    """

    def __init__(self):
        self.spiral = LogarithmicSpiral()
        self.fibonacci = FibonacciAnalyzer()
        self.fractal = FractalDimensionEstimator()
        self.cycles = NaturalCycleDetector()

    def analyze(
        self,
        current_price: float,
        swing_high: float,
        swing_low: float,
        price_history: list[float],
    ) -> dict:
        """
        Complete analysis using universal laws.

        Args:
            current_price: Current market price
            swing_high: Recent swing high
            swing_low: Recent swing low
            price_history: Historical prices

        Returns:
            Dict with all analysis results
        """
        # Calculate returns for some analyses
        returns = []
        for i in range(1, len(price_history)):
            if price_history[i - 1] > 0:
                returns.append((price_history[i] - price_history[i - 1]) / price_history[i - 1])

        result = {
            # Spiral analysis (Gann Square of 9)
            "spiral_position": self.spiral.price_to_spiral(current_price),
            "spiral_harmonics": self.spiral.get_harmonic_levels(current_price),
            # Fibonacci levels
            "fibonacci_retracements": self.fibonacci.get_retracement_levels(swing_high, swing_low),
            "fibonacci_extensions": self.fibonacci.get_extension_levels(swing_high, swing_low),
            # Fractal analysis
            "hurst_exponent": self.fractal.estimate_hurst(returns) if returns else 0.5,
            "fractal_dimension": self.fractal.get_fractal_dimension(returns) if returns else 1.5,
            # Cycle analysis
            "dominant_cycle": self.cycles.detect_dominant_cycle(price_history),
        }

        # Market character interpretation
        H = result["hurst_exponent"]
        if H > 0.55:
            result["market_character"] = "TRENDING"
        elif H < 0.45:
            result["market_character"] = "MEAN_REVERTING"
        else:
            result["market_character"] = "RANDOM"

        return result

    def get_support_resistance_levels(
        self,
        current_price: float,
        swing_high: float,
        swing_low: float,
        n_levels: int = 5,
    ) -> tuple[list[float], list[float]]:
        """
        Get combined support and resistance levels.

        Combines spiral harmonics and Fibonacci levels.

        Args:
            current_price: Current price
            swing_high: Recent high
            swing_low: Recent low
            n_levels: Number of levels each direction

        Returns:
            (support_levels, resistance_levels)
        """
        all_levels = []

        # Add spiral harmonics
        all_levels.extend(self.spiral.get_harmonic_levels(current_price))

        # Add Fibonacci levels
        fib_ret = self.fibonacci.get_retracement_levels(swing_high, swing_low)
        all_levels.extend(fib_ret.values())

        fib_ext = self.fibonacci.get_extension_levels(swing_high, swing_low)
        all_levels.extend(fib_ext.values())

        # Filter and sort
        all_levels = sorted(set(all_levels))

        # Separate support (below) and resistance (above)
        supports = [l for l in all_levels if l < current_price][-n_levels:]
        resistances = [l for l in all_levels if l > current_price][:n_levels]

        return supports, resistances
