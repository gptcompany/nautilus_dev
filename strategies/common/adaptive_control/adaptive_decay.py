"""Adaptive Decay Calculator for Discounted Thompson Sampling (Spec 032).

This module implements adaptive discounting for Thompson Sampling in non-stationary
environments. The decay factor adjusts automatically based on market volatility,
allowing faster adaptation during volatile regimes and more stable estimates during
calm periods.

Academic Foundation:
- Qi et al. (2023): Discounted Thompson Sampling for Non-Stationary Bandit Problems
- de Freitas Fonseca et al. (2024): RF-DSW TS - Relaxed f-Discounted-Sliding-Window

Key Formula:
    decay = 0.99 - 0.04 * normalized_volatility
    where normalized_volatility = clip((variance_ratio - 0.7) / 0.8, 0, 1)

Range:
- Low volatility (variance_ratio < 0.7): decay = 0.99 (stable estimates)
- High volatility (variance_ratio > 1.5): decay = 0.95 (faster adaptation)
- Normal volatility: Interpolated linearly

Reference: specs/032-adts-discounting/
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategies.common.adaptive_control.dsp_filters import IIRRegimeDetector


@dataclass(frozen=True)
class VolatilityContext:
    """Context for volatility-based decay calculation.

    Attributes:
        variance_ratio: Ratio of fast/slow variance from IIRRegimeDetector.
                       < 0.7 = mean-reverting/stable
                       0.7-1.5 = normal
                       > 1.5 = trending/volatile
    """

    variance_ratio: float

    @property
    def normalized_volatility(self) -> float:
        """Normalize variance_ratio to [0, 1] for decay calculation.

        Mapping:
        - variance_ratio <= 0.7 -> 0.0 (low volatility)
        - variance_ratio >= 1.5 -> 1.0 (high volatility)
        - variance_ratio in (0.7, 1.5) -> linear interpolation

        Handles edge cases:
        - Negative variance_ratio: Clamped to 0.0
        - Zero variance_ratio: Returns 0.0
        """
        if self.variance_ratio <= 0.0:
            return 0.0

        # Thresholds from IIRRegimeDetector defaults
        low_threshold = 0.7
        high_threshold = 1.5

        if self.variance_ratio <= low_threshold:
            return 0.0
        elif self.variance_ratio >= high_threshold:
            return 1.0
        else:
            # Linear interpolation
            return (self.variance_ratio - low_threshold) / (
                high_threshold - low_threshold
            )


class AdaptiveDecayCalculator:
    """Calculates adaptive decay factor based on market volatility.

    The decay factor controls how much old observations are discounted
    in Thompson Sampling updates. Higher decay (closer to 1.0) means
    slower forgetting; lower decay means faster adaptation.

    Formula:
        decay = decay_high - decay_range * normalized_volatility

    Where:
        - decay_high = 0.99 (maximum decay for stable regimes)
        - decay_low = 0.95 (minimum decay for volatile regimes)
        - decay_range = decay_high - decay_low = 0.04

    This implements passive adaptive discounting as described in:
    - Qi et al. (2023): DS-TS for non-stationary bandits
    - de Freitas Fonseca et al. (2024): RF-DSW TS

    Attributes:
        decay_low: Minimum decay factor (volatile regime).
        decay_high: Maximum decay factor (stable regime).
    """

    # Fixed parameters per spec (SC-005: No new hyperparameters)
    decay_low: float = 0.95
    decay_high: float = 0.99

    def calculate(self, context: VolatilityContext) -> float:
        """Calculate adaptive decay from volatility context.

        Args:
            context: VolatilityContext with variance_ratio.

        Returns:
            Decay factor in [decay_low, decay_high] range.
        """
        normalized = context.normalized_volatility
        decay = self.decay_high - (self.decay_high - self.decay_low) * normalized
        # Clamp to ensure valid range (defensive)
        return max(self.decay_low, min(self.decay_high, decay))

    def calculate_from_ratio(self, variance_ratio: float) -> float:
        """Convenience method to calculate decay directly from variance_ratio.

        Args:
            variance_ratio: Raw variance ratio from IIRRegimeDetector.

        Returns:
            Decay factor in [decay_low, decay_high] range.
        """
        context = VolatilityContext(variance_ratio=variance_ratio)
        return self.calculate(context)

    def calculate_from_detector(self, detector: "IIRRegimeDetector") -> float:
        """Calculate decay directly from IIRRegimeDetector.

        Args:
            detector: IIRRegimeDetector instance with current variance_ratio.

        Returns:
            Decay factor in [decay_low, decay_high] range.
        """
        return self.calculate_from_ratio(detector.variance_ratio)
