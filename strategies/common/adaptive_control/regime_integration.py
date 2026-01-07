"""
Regime Integration - Combines parametric and non-parametric regime detection.

Integrates SpectralRegimeDetector with existing RegimeManager to provide
a more robust, less parametric regime signal.

Philosophy:
- HMM/GMM provide STRUCTURE (state transitions, clusters)
- Spectral provides FREEDOM (no distribution assumptions)
- Combine both for robust regime detection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from .spectral_regime import MarketRegime, SpectralRegimeDetector

if TYPE_CHECKING:
    from strategies.common.regime_detection.regime_manager import (
        RegimeManager,
        RegimeResult,
    )
    from strategies.common.regime_detection.types import RegimeState

logger = logging.getLogger(__name__)


class CombinedRegime(Enum):
    """Combined regime from spectral + HMM analysis."""

    STRONG_TREND = "strong_trend"  # Both agree: trending
    WEAK_TREND = "weak_trend"  # Spectral trending, HMM mixed
    MEAN_REVERT = "mean_revert"  # Both agree: mean reverting
    MIXED = "mixed"  # Disagreement
    VOLATILE = "volatile"  # High volatility detected
    UNKNOWN = "unknown"  # Insufficient data


@dataclass
class EnhancedRegimeResult:
    """Enhanced regime result with spectral information."""

    # From HMM/GMM
    hmm_regime: RegimeState
    hmm_confidence: float
    hmm_weight: float

    # From Spectral
    spectral_regime: MarketRegime
    spectral_alpha: float
    spectral_confidence: float

    # Combined
    combined_regime: CombinedRegime
    combined_weight: float
    agreement_score: float  # How much HMM and Spectral agree


class EnhancedRegimeManager:
    """
    Enhanced regime manager combining HMM and Spectral detection.

    Provides more robust regime signals by combining:
    - HMM: Captures state transitions and structure
    - Spectral: Non-parametric, data-driven

    Usage:
        enhanced = EnhancedRegimeManager(
            regime_manager=existing_manager,
            spectral_weight=0.3,  # How much to weight spectral
        )

        # Fit spectral detector with returns
        enhanced.fit_spectral(returns_history)

        # Update with each bar
        result = enhanced.update(bar, current_return)

        # Use combined weight for sizing
        size = base_size * result.combined_weight
    """

    def __init__(
        self,
        regime_manager: RegimeManager,
        spectral_weight: float = 0.3,
        spectral_window: int = 256,
        agreement_bonus: float = 0.2,
    ):
        """
        Args:
            regime_manager: Existing RegimeManager instance
            spectral_weight: Weight for spectral in combined signal (0-1)
            spectral_window: Window for spectral analysis
            agreement_bonus: Extra weight when both methods agree
        """
        self.regime_manager = regime_manager
        self.spectral_weight = spectral_weight
        self.agreement_bonus = agreement_bonus

        self.spectral = SpectralRegimeDetector(
            window_size=spectral_window,
            min_samples=64,
        )

        self._is_spectral_ready = False

    def fit_spectral(self, returns: list[float]) -> None:
        """Initialize spectral detector with historical returns."""
        self.spectral.update_batch(returns)
        self._is_spectral_ready = len(returns) >= self.spectral.min_samples
        logger.info(f"Spectral detector initialized with {len(returns)} returns")

    def update(self, bar: dict, current_return: float) -> EnhancedRegimeResult:
        """
        Update with new bar and return.

        Args:
            bar: Bar dict for HMM update
            current_return: Current return for spectral update

        Returns:
            EnhancedRegimeResult with combined regime information
        """
        # Update HMM
        hmm_result = self.regime_manager.update(bar)

        # Update Spectral
        self.spectral.update(current_return)
        spectral_analysis = self.spectral.analyze()

        # Calculate agreement
        agreement = self._calculate_agreement(hmm_result.regime, spectral_analysis.regime)

        # Calculate combined weight
        combined = self._combine_regimes(hmm_result, spectral_analysis, agreement)

        return EnhancedRegimeResult(
            hmm_regime=hmm_result.regime,
            hmm_confidence=hmm_result.confidence,
            hmm_weight=hmm_result.weight,
            spectral_regime=spectral_analysis.regime,
            spectral_alpha=spectral_analysis.alpha,
            spectral_confidence=spectral_analysis.confidence,
            combined_regime=combined[0],
            combined_weight=combined[1],
            agreement_score=agreement,
        )

    def _calculate_agreement(
        self,
        hmm_regime: RegimeState,
        spectral_regime: MarketRegime,
    ) -> float:
        """
        Calculate agreement score between HMM and Spectral.

        Returns 1.0 for full agreement, 0.0 for full disagreement.
        """
        # Import here to avoid circular dependency
        from strategies.common.regime_detection.types import RegimeState

        # Map HMM regime to trend/revert categories
        hmm_trending = hmm_regime in (
            RegimeState.TRENDING_UP,
            RegimeState.TRENDING_DOWN,
        )
        hmm_reverting = hmm_regime == RegimeState.RANGING

        # Map spectral regime
        spectral_trending = spectral_regime == MarketRegime.TRENDING
        spectral_reverting = spectral_regime == MarketRegime.MEAN_REVERTING

        # Full agreement
        if (hmm_trending and spectral_trending) or (hmm_reverting and spectral_reverting):
            return 1.0

        # Partial agreement (one neutral/normal)
        if spectral_regime == MarketRegime.NORMAL:
            return 0.5

        # Disagreement
        return 0.0

    def _combine_regimes(
        self,
        hmm_result: RegimeResult,
        spectral_analysis,
        agreement: float,
    ) -> tuple[CombinedRegime, float]:
        """
        Combine HMM and Spectral into single regime and weight.

        Returns:
            (combined_regime, combined_weight)
        """
        from strategies.common.regime_detection.types import RegimeState

        # Determine combined regime
        if spectral_analysis.regime == MarketRegime.UNKNOWN:
            combined_regime = CombinedRegime.UNKNOWN
        elif agreement >= 0.9:
            if spectral_analysis.regime == MarketRegime.TRENDING:
                combined_regime = CombinedRegime.STRONG_TREND
            else:
                combined_regime = CombinedRegime.MEAN_REVERT
        elif spectral_analysis.regime == MarketRegime.TRENDING:
            combined_regime = CombinedRegime.WEAK_TREND
        elif hmm_result.regime == RegimeState.VOLATILE:
            combined_regime = CombinedRegime.VOLATILE
        else:
            combined_regime = CombinedRegime.MIXED

        # Calculate combined weight
        # Base: weighted average of HMM and spectral confidence
        hmm_component = hmm_result.weight * (1 - self.spectral_weight)

        # Spectral weight based on regime type
        spectral_weights = {
            MarketRegime.TRENDING: 1.0,
            MarketRegime.NORMAL: 0.7,
            MarketRegime.MEAN_REVERTING: 0.5,
            MarketRegime.UNKNOWN: 0.3,
        }
        spectral_base = spectral_weights.get(spectral_analysis.regime, 0.5)
        spectral_component = spectral_base * self.spectral_weight * spectral_analysis.confidence

        combined_weight = hmm_component + spectral_component

        # Agreement bonus
        if agreement >= 0.9:
            combined_weight = min(1.0, combined_weight + self.agreement_bonus)

        # Clamp
        combined_weight = max(0.0, min(1.0, combined_weight))

        return combined_regime, combined_weight

    def get_combined_weight(self) -> float:
        """Get the current combined regime weight."""
        return self.regime_manager.get_regime_weight()

    @property
    def is_ready(self) -> bool:
        """Check if both HMM and Spectral are ready."""
        return self.regime_manager.is_fitted and self._is_spectral_ready
