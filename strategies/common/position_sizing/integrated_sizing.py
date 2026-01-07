"""Integrated position sizing for meta-learning pipeline (Spec 026 - US4).

This module provides the IntegratedSizer class that combines all sizing factors
into a unified position size calculation.

Formula:
    size = direction * |signal|^giller_exponent * meta_confidence *
           regime_weight * (1 - toxicity) * fractional_kelly

Factor Breakdown:
    - direction: Sign of the signal (+1 long, -1 short, 0 flat)
    - |signal|^exponent: Sub-linear scaling (Giller 2015)
    - meta_confidence: P(primary_model_correct) from MetaModel
    - regime_weight: Regime-based weight adjustment
    - (1 - toxicity): VPIN penalty for informed flow
    - fractional_kelly: Conservative Kelly fraction
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from strategies.common.position_sizing.config import IntegratedSizingConfig

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class IntegratedSize:
    """Result of integrated position sizing calculation.

    Attributes:
        final_size: Final position size (signed, clamped to bounds).
        direction: Signal direction (+1, -1, or 0).
        factors: Factor contribution breakdown for debugging.
    """

    final_size: float
    direction: int
    factors: dict[str, float] = field(default_factory=dict)


class IntegratedSizer:
    """Integrated position sizing combining all pipeline factors.

    Calculates position size using the unified formula that combines
    signal magnitude, meta-model confidence, regime weight, and toxicity.

    Attributes:
        config: IntegratedSizingConfig with sizing parameters.

    Example:
        >>> from strategies.common.position_sizing import IntegratedSizer
        >>> config = IntegratedSizingConfig(
        ...     giller_exponent=0.5,
        ...     fractional_kelly=0.5,
        ... )
        >>> sizer = IntegratedSizer(config)
        >>> result = sizer.calculate(
        ...     signal=1.0,
        ...     meta_confidence=0.8,
        ...     regime_weight=1.0,
        ...     toxicity=0.1,
        ... )
        >>> print(f"Size: {result.final_size}, Direction: {result.direction}")
    """

    def __init__(self, config: IntegratedSizingConfig | None = None) -> None:
        """Initialize IntegratedSizer.

        Args:
            config: Sizing configuration. Uses defaults if None.
        """
        self._config = config or IntegratedSizingConfig()

    @property
    def config(self) -> IntegratedSizingConfig:
        """Get configuration."""
        return self._config

    def calculate(
        self,
        signal: float,
        meta_confidence: float | None = None,
        regime_weight: float | None = None,
        toxicity: float | None = None,
    ) -> IntegratedSize:
        """Calculate integrated position size.

        Args:
            signal: Primary signal strength (positive = long, negative = short).
            meta_confidence: P(primary_model_correct) from MetaModel.
                            Uses default if None.
            regime_weight: Regime-based weight (0.4-1.2 typical).
                          Uses default if None.
            toxicity: VPIN toxicity (0 = clean, 1 = toxic).
                     Uses default if None.

        Returns:
            IntegratedSize with final_size, direction, and factor breakdown.
        """
        # Handle zero signal case
        if signal == 0:
            return IntegratedSize(
                final_size=0.0,
                direction=0,
                factors={
                    "signal": 0.0,
                    "meta_confidence": 0.0,
                    "regime_weight": 0.0,
                    "toxicity_penalty": 0.0,
                    "kelly_fraction": 0.0,
                },
            )

        # Apply defaults for missing values
        meta_conf = (
            meta_confidence if meta_confidence is not None else self._config.default_meta_confidence
        )
        regime_wt = (
            regime_weight if regime_weight is not None else self._config.default_regime_weight
        )
        tox = toxicity if toxicity is not None else self._config.default_toxicity

        # Calculate direction
        direction = 1 if signal > 0 else -1

        # Calculate factor contributions
        signal_factor = abs(signal) ** self._config.giller_exponent
        toxicity_penalty = 1 - tox

        # Compute raw size (unsigned)
        raw_size = (
            signal_factor * meta_conf * regime_wt * toxicity_penalty * self._config.fractional_kelly
        )

        # Apply clamping
        if raw_size < self._config.min_size:
            # If too small, clamp to 0 (don't trade)
            final_size = 0.0
            direction = 0
        elif raw_size > self._config.max_size:
            final_size = direction * self._config.max_size
        else:
            final_size = direction * raw_size

        # Build factor breakdown for debugging
        factors = {
            "signal": signal_factor,
            "meta_confidence": meta_conf,
            "regime_weight": regime_wt,
            "toxicity_penalty": toxicity_penalty,
            "kelly_fraction": self._config.fractional_kelly,
        }

        # Log at DEBUG level per FR-008
        logger.debug(
            "IntegratedSizer: signal=%.4f, meta=%.4f, regime=%.4f, "
            "toxicity=%.4f, raw=%.4f, final=%.4f",
            signal,
            meta_conf,
            regime_wt,
            tox,
            raw_size,
            final_size,
        )

        return IntegratedSize(
            final_size=final_size,
            direction=direction if final_size != 0 else 0,
            factors=factors,
        )
