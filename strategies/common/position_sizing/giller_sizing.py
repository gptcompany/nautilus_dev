"""Giller sub-linear position sizing.

Implements position sizing based on Graham Giller research,
using sub-linear scaling (signal^exponent) to avoid over-betting.
"""

from __future__ import annotations

import math

from strategies.common.position_sizing.config import GillerConfig


class GillerSizer:
    """Sub-linear position sizer based on Graham Giller research.

    Uses the formula: size = sign(signal) * |signal|^exponent * base_size * regime_weight * (1 - toxicity)

    The sub-linear scaling (default exponent=0.5, i.e., sqrt) prevents
    over-betting on strong signals while maintaining directional exposure.

    Attributes:
        config: GillerConfig with sizing parameters.
    """

    def __init__(self, config: GillerConfig) -> None:
        """Initialize Giller sizer.

        Args:
            config: Configuration with base_size, exponent, min/max limits.
        """
        self.config = config

    def calculate(
        self,
        signal: float,
        regime_weight: float = 1.0,
        toxicity: float = 0.0,
    ) -> float:
        """Calculate position size using sub-linear scaling.

        Formula: sign(signal) * |signal|^exponent * base_size * regime_weight * (1 - toxicity)

        Args:
            signal: Trading signal magnitude (can be positive or negative).
            regime_weight: Regime-based weight multiplier (0.0 to 1.0).
            toxicity: VPIN toxicity penalty (0.0 to 1.0).

        Returns:
            Position size with sign preserved, clamped to min/max limits.
            Returns 0.0 for NaN/inf signals.
        """
        # Handle NaN/inf signals
        if not math.isfinite(signal):
            return 0.0

        # Handle zero signal
        if signal == 0.0:
            return 0.0

        # Clamp inputs to valid ranges
        regime_weight = max(0.0, min(1.0, regime_weight))
        toxicity = max(0.0, min(1.0, toxicity))

        # Extract sign and magnitude
        sign = 1.0 if signal > 0 else -1.0
        magnitude = abs(signal)

        # Sub-linear scaling: |signal|^exponent
        scaled = magnitude**self.config.exponent

        # Apply base size, regime weight, and toxicity penalty
        size = scaled * self.config.base_size * regime_weight * (1.0 - toxicity)

        # If raw size is zero (e.g., regime_weight=0 or toxicity=1), return 0
        # This means "don't trade" takes precedence over min_size
        if size == 0.0:
            return 0.0

        # Apply min/max limits (on absolute value)
        if size < self.config.min_size:
            size = self.config.min_size
        elif size > self.config.max_size:
            size = self.config.max_size

        # Restore sign
        return float(sign * size)
