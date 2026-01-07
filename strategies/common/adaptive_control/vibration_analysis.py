"""
Vibration Analysis - The Mathematical Core of Gann's "Law of Vibration"

Gann's "Law of Vibration" stripped of mysticism:
- Everything oscillates (price, volume, sentiment)
- Multiple frequencies combine (like music)
- Resonance occurs when frequencies align
- This is just Fourier analysis + harmonic theory

What's real:
- Price series contain multiple overlapping cycles
- Cycles can be detected via spectral analysis
- When cycles align, volatility increases (resonance)
- This is the same math used in electrical engineering

What's NOT real:
- Numerology (digital roots, "sacred" numbers)
- Mystical vibrations from the universe
- Predetermined price targets from "natural law"

This module implements the REAL mathematics behind Gann's intuitions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class VibrationMode:
    """A detected vibration (cycle) in the price series."""

    frequency: float  # Cycles per sample
    period: float  # Samples per cycle
    amplitude: float  # Strength of this vibration
    phase: float  # Phase offset (radians)


@dataclass
class ResonanceEvent:
    """When multiple vibrations align."""

    timestamp: int  # Sample index
    strength: float  # How strong the alignment
    participating_modes: list[VibrationMode]


class VibrationAnalyzer:
    """
    Analyzes price "vibrations" (oscillations/cycles).

    This is the mathematical reality behind Gann's mysticism.
    Uses standard DSP techniques to find cycles in price data.

    Key insight: Markets oscillate at multiple frequencies simultaneously.
    When these frequencies align (like musical harmony), big moves happen.

    Usage:
        va = VibrationAnalyzer()

        # Add price data
        for price in prices:
            va.update(price)

        # Get dominant vibrations
        modes = va.get_dominant_modes(n_modes=3)

        # Check for resonance (cycle alignment)
        resonance = va.check_resonance()
    """

    def __init__(
        self,
        window_size: int = 128,
        min_period: int = 5,
        max_period: int = 64,
    ):
        """
        Args:
            window_size: Analysis window (power of 2 for FFT efficiency)
            min_period: Minimum cycle length to detect
            max_period: Maximum cycle length to detect
        """
        self.window_size = window_size
        self.min_period = min_period
        self.max_period = max_period

        self._buffer: list[float] = []
        self._modes: list[VibrationMode] = []
        self._last_price: float | None = None

    def update(self, price: float) -> None:
        """Add new price observation."""
        self._buffer.append(price)
        if len(self._buffer) > self.window_size * 2:
            self._buffer = self._buffer[-self.window_size * 2 :]
        self._last_price = price

    def get_dominant_modes(self, n_modes: int = 3) -> list[VibrationMode]:
        """
        Extract dominant vibration modes using FFT.

        Returns the n strongest frequency components.

        Args:
            n_modes: Number of modes to return

        Returns:
            List of VibrationMode sorted by amplitude
        """
        if len(self._buffer) < self.window_size:
            return []

        # Use last window_size samples
        data = np.array(self._buffer[-self.window_size :])

        # Remove trend (detrend)
        data = data - np.linspace(data[0], data[-1], len(data))

        # Apply Hanning window to reduce spectral leakage
        window = np.hanning(len(data))
        data_windowed = data * window

        # FFT
        fft_result = np.fft.rfft(data_windowed)
        freqs = np.fft.rfftfreq(len(data))
        amplitudes = np.abs(fft_result) / len(data)
        phases = np.angle(fft_result)

        # Convert to periods and filter
        modes = []
        for _i, (freq, amp, phase) in enumerate(zip(freqs, amplitudes, phases, strict=False)):
            if freq == 0:
                continue
            period = 1.0 / freq
            if self.min_period <= period <= self.max_period:
                modes.append(
                    VibrationMode(
                        frequency=freq,
                        period=period,
                        amplitude=amp,
                        phase=phase,
                    )
                )

        # Sort by amplitude and return top n
        modes.sort(key=lambda m: m.amplitude, reverse=True)
        self._modes = modes[:n_modes]
        return self._modes

    def check_resonance(self, tolerance: float = 0.1) -> ResonanceEvent | None:
        """
        Check if current vibration modes are in resonance.

        Resonance = multiple cycles aligning at similar phase.
        This often precedes large price moves.

        Args:
            tolerance: Phase alignment tolerance (radians)

        Returns:
            ResonanceEvent if resonance detected, None otherwise
        """
        if len(self._modes) < 2:
            return None

        # Check phase alignment
        phases = [m.phase for m in self._modes]

        # Calculate phase coherence (how aligned are the phases?)
        # Using circular mean for phases
        cos_sum = sum(math.cos(p) for p in phases)
        sin_sum = sum(math.sin(p) for p in phases)
        coherence = math.sqrt(cos_sum**2 + sin_sum**2) / len(phases)

        # High coherence = resonance
        if coherence > 0.7:
            return ResonanceEvent(
                timestamp=len(self._buffer),
                strength=coherence,
                participating_modes=self._modes,
            )

        return None

    def predict_next_extreme(self) -> tuple[int, str] | None:
        """
        Predict when next local extreme might occur.

        Uses dominant cycle to estimate time to next peak/trough.

        Returns:
            (bars_until_extreme, "peak" or "trough") or None
        """
        if not self._modes:
            self.get_dominant_modes()

        if not self._modes:
            return None

        dominant = self._modes[0]

        # Current phase position
        current_phase = dominant.phase

        # Bars until next peak (phase = 0) or trough (phase = π)
        period_bars = int(dominant.period)

        # Estimate bars to next extreme
        phase_to_peak = (2 * math.pi - current_phase) % (2 * math.pi)
        phase_to_trough = (math.pi - current_phase) % (2 * math.pi)

        bars_to_peak = int((phase_to_peak / (2 * math.pi)) * period_bars)
        bars_to_trough = int((phase_to_trough / (2 * math.pi)) * period_bars)

        if bars_to_peak < bars_to_trough:
            return (bars_to_peak, "peak")
        else:
            return (bars_to_trough, "trough")


class HarmonicRatioAnalyzer:
    """
    Analyzes harmonic ratios between price levels.

    Musical consonance applied to price:
    - Octave (2:1) - Price doubles
    - Fifth (3:2) - 50% move
    - Fourth (4:3) - 33% move
    - Third (5:4) - 25% move

    Gann intuited that "harmonic" price levels act as support/resistance.
    This is the mathematical expression of that idea.
    """

    # Harmonic ratios from music theory
    CONSONANT_RATIOS = {
        "unison": 1.0,
        "octave": 2.0,
        "fifth": 1.5,  # 3:2
        "fourth": 1.333,  # 4:3
        "major_third": 1.25,  # 5:4
        "minor_third": 1.2,  # 6:5
    }

    def __init__(self, tolerance: float = 0.02):
        """
        Args:
            tolerance: Allowed deviation from perfect ratio
        """
        self.tolerance = tolerance

    def find_harmonic_relationship(
        self,
        price_a: float,
        price_b: float,
    ) -> str | None:
        """
        Check if two prices are in a harmonic relationship.

        Args:
            price_a: First price
            price_b: Second price

        Returns:
            Name of harmonic relationship, or None
        """
        if price_a <= 0 or price_b <= 0:
            return None

        ratio = max(price_a, price_b) / min(price_a, price_b)

        for name, target_ratio in self.CONSONANT_RATIOS.items():
            if abs(ratio - target_ratio) < self.tolerance:
                return name

        return None

    def get_harmonic_levels(
        self,
        base_price: float,
        direction: str = "both",
    ) -> dict[str, float]:
        """
        Get harmonic price levels from a base price.

        Args:
            base_price: Reference price
            direction: "up", "down", or "both"

        Returns:
            Dict of harmonic_name -> price_level
        """
        levels = {}

        for name, ratio in self.CONSONANT_RATIOS.items():
            if direction in ("up", "both"):
                levels[f"{name}_up"] = base_price * ratio
            if direction in ("down", "both"):
                levels[f"{name}_down"] = base_price / ratio

        return levels

    def calculate_consonance_score(
        self,
        prices: list[float],
    ) -> float:
        """
        Calculate how "harmonic" a set of prices are.

        High score = prices are in harmonic relationships.
        This might indicate stable support/resistance structure.

        Args:
            prices: List of significant price levels

        Returns:
            Consonance score (0 to 1)
        """
        if len(prices) < 2:
            return 0.0

        harmonic_pairs = 0
        total_pairs = 0

        for i in range(len(prices)):
            for j in range(i + 1, len(prices)):
                total_pairs += 1
                if self.find_harmonic_relationship(prices[i], prices[j]):
                    harmonic_pairs += 1

        return harmonic_pairs / total_pairs if total_pairs > 0 else 0.0


class DigitalRootAnalyzer:
    """
    Digital root analysis - what Vortex Math actually is.

    Digital root = repeatedly sum digits until single digit.
    Example: 256 → 2+5+6 = 13 → 1+3 = 4

    The patterns:
    - Powers of 2: 1,2,4,8,7,5,1,2,4,8,7,5... (never 3,6,9)
    - Multiples of 3: 3,6,9,3,6,9... (separate cycle)
    - 9: Always stays 9 (fixed point)

    This is NOT mystical - it's modular arithmetic (mod 9).
    The pattern emerges because 10 ≡ 1 (mod 9).

    Can this help trading? Probably not.
    But we implement it for completeness.
    """

    @staticmethod
    def digital_root(n: int) -> int:
        """
        Calculate digital root (repeated digit sum until single digit).

        Mathematically: dr(n) = 1 + ((n - 1) mod 9)

        Args:
            n: Positive integer

        Returns:
            Digital root (1-9)
        """
        if n <= 0:
            return 0
        root = 1 + ((n - 1) % 9)
        return root if root != 0 else 9

    @staticmethod
    def vortex_sequence(n: int = 24) -> list[int]:
        """
        Generate the Vortex Math doubling sequence.

        1 → 2 → 4 → 8 → 16(7) → 32(5) → 64(1) → ...

        Args:
            n: How many terms

        Returns:
            List of digital roots
        """
        sequence = []
        value = 1
        for _ in range(n):
            sequence.append(DigitalRootAnalyzer.digital_root(value))
            value *= 2
        return sequence

    def analyze_price_pattern(self, prices: list[float]) -> dict:
        """
        Analyze digital root patterns in price movements.

        This is mostly for exploration - unlikely to have predictive value.

        Args:
            prices: List of prices

        Returns:
            Analysis results
        """
        # Convert prices to integers for digital root
        int_prices = [int(p) for p in prices if p > 0]
        roots = [self.digital_root(p) for p in int_prices]

        # Count distribution
        distribution = {i: roots.count(i) for i in range(1, 10)}

        # Check for patterns
        vortex_cycle = [1, 2, 4, 8, 7, 5]
        trinity_cycle = [3, 6, 9]

        vortex_count = sum(1 for r in roots if r in vortex_cycle)
        trinity_count = sum(1 for r in roots if r in trinity_cycle)

        return {
            "distribution": distribution,
            "vortex_ratio": vortex_count / len(roots) if roots else 0,
            "trinity_ratio": trinity_count / len(roots) if roots else 0,
            "most_common": max(distribution, key=distribution.get) if distribution else None,
        }
