"""Unified RegimeManager facade for regime detection.

Combines HMM regime detection and GMM volatility clustering
into a single interface for strategy use.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from strategies.common.regime_detection.config import RegimeConfig
from strategies.common.regime_detection.gmm_filter import GMMVolatilityFilter
from strategies.common.regime_detection.hmm_filter import HMMRegimeFilter
from strategies.common.regime_detection.types import RegimeState, VolatilityCluster
from strategies.common.utils.data_transforms import (
    calculate_returns,
    calculate_volatility,
)

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegimeResult:
    """Result of regime detection update.

    Attributes:
        regime: The detected market regime state.
        volatility: The detected volatility cluster.
        weight: Regime-based position weight (0.0 to 1.0).
        confidence: Confidence in the regime prediction (0.0 to 1.0).
    """

    regime: RegimeState
    volatility: VolatilityCluster
    weight: float
    confidence: float


class RegimeManager:
    """Unified facade for regime detection.

    Combines HMM regime detection and GMM volatility clustering
    into a single interface. Updates internal state on each bar
    and provides regime weight for position sizing.

    Attributes:
        config: RegimeConfig with detection parameters.
        is_fitted: Whether the manager has been fitted.
        hmm_filter: The HMM regime filter (after fitting).
        gmm_filter: The GMM volatility filter (after fitting).
    """

    def __init__(self, config: RegimeConfig) -> None:
        """Initialize RegimeManager.

        Args:
            config: Configuration for regime detection.
        """
        self.config = config
        self.is_fitted: bool = False

        self.hmm_filter: HMMRegimeFilter | None = None
        self.gmm_filter: GMMVolatilityFilter | None = None

        # Internal state
        self._last_regime: RegimeState | None = None
        self._last_volatility: VolatilityCluster | None = None
        self._last_weight: float = 1.0
        self._last_confidence: float = 0.0

        # Rolling window for online updates
        self._price_history: list[float] = []
        self._bars_since_fit: int = 0

    def fit(self, bars: list[dict]) -> None:
        """Fit regime detection models on historical bar data.

        Args:
            bars: List of bar dictionaries with 'close', 'high', 'low' keys.

        Raises:
            ValueError: If insufficient data for fitting.
        """
        if len(bars) < self.config.min_bars_for_fit:
            raise ValueError(
                f"Insufficient data: {len(bars)} bars, "
                f"minimum {self.config.min_bars_for_fit} required"
            )

        # Extract close prices
        closes = np.array([bar["close"] for bar in bars], dtype=np.float64)

        # Calculate returns and volatility
        returns = calculate_returns(closes)
        volatility = calculate_volatility(returns, window=self.config.volatility_window)

        # Remove NaN values (from volatility calculation warmup)
        # Both returns and volatility have the same length (len(closes) - 1)
        valid_mask = ~np.isnan(volatility)
        returns_valid = returns[valid_mask]
        volatility_valid = volatility[valid_mask]

        # Ensure we still have enough data
        if len(returns_valid) < self.config.min_bars_for_fit:
            raise ValueError(
                f"Insufficient valid data after volatility calculation: "
                f"{len(returns_valid)} samples"
            )

        # Fit HMM
        self.hmm_filter = HMMRegimeFilter(
            n_states=self.config.hmm_states,
            n_iter=self.config.hmm_n_iter,
            n_init=self.config.hmm_n_init,
            min_samples=50,
        )
        self.hmm_filter.fit(returns_valid, volatility_valid)

        # Fit GMM
        self.gmm_filter = GMMVolatilityFilter(
            n_clusters=self.config.gmm_clusters,
            min_samples=50,
        )
        self.gmm_filter.fit(volatility_valid)

        # Store price history for online updates
        self._price_history = list(closes[-self.config.volatility_window * 2 :])
        self._bars_since_fit = 0

        self.is_fitted = True
        logger.info(
            f"RegimeManager fitted: HMM={self.config.hmm_states} states, "
            f"GMM={self.config.gmm_clusters} clusters"
        )

    def update(self, bar: dict) -> RegimeResult:
        """Update regime detection with new bar.

        Args:
            bar: Bar dictionary with 'close', 'high', 'low' keys.

        Returns:
            RegimeResult with current regime, volatility, weight, confidence.

        Raises:
            RuntimeError: If manager has not been fitted.
        """
        if not self.is_fitted or self.hmm_filter is None or self.gmm_filter is None:
            raise RuntimeError("RegimeManager not fitted. Call fit() first.")

        # Add to price history with validation
        close = float(bar["close"])
        if not np.isfinite(close) or close <= 0:
            # Skip invalid prices, return last known state
            return RegimeResult(
                regime=self._last_regime or RegimeState.RANGING,
                volatility=self._last_volatility or VolatilityCluster.MEDIUM,
                weight=self._last_weight,
                confidence=self._last_confidence,
            )
        self._price_history.append(close)

        # Keep rolling window
        max_history = self.config.volatility_window * 3
        if len(self._price_history) > max_history:
            self._price_history = self._price_history[-max_history:]

        # Calculate current returns and volatility
        if len(self._price_history) < 2:
            # Not enough history, return default
            return RegimeResult(
                regime=RegimeState.RANGING,
                volatility=VolatilityCluster.MEDIUM,
                weight=0.5,
                confidence=0.0,
            )

        prices = np.array(self._price_history, dtype=np.float64)
        returns = calculate_returns(prices)
        volatility = calculate_volatility(
            returns, window=min(len(returns), self.config.volatility_window)
        )

        # Get latest valid values with NaN/inf protection
        current_return = returns[-1]
        if not np.isfinite(current_return):
            current_return = 0.0  # Safe default for NaN/inf returns

        # Handle NaN/inf volatility with fallback chain
        if np.isfinite(volatility[-1]):
            current_volatility = volatility[-1]
        else:
            # Try nanmean, fallback to safe default if all NaN/inf
            mean_vol = np.nanmean(volatility)
            current_volatility = mean_vol if np.isfinite(mean_vol) else 0.01

        # Predict regime and volatility
        regime = self.hmm_filter.predict(current_return, current_volatility)
        volatility_cluster = self.gmm_filter.predict(current_volatility)

        # Get confidence from state probabilities
        hmm_probs = self.hmm_filter.get_state_probabilities(current_return, current_volatility)
        confidence = float(np.max(hmm_probs))

        # Calculate regime weight
        weight = self._calculate_regime_weight(regime, volatility_cluster, confidence)

        # Log regime transitions
        if self._last_regime is not None and regime != self._last_regime:
            logger.info(
                f"Regime transition: {self._last_regime.name} -> {regime.name} "
                f"(confidence: {confidence:.2f})"
            )

        # Update internal state
        self._last_regime = regime
        self._last_volatility = volatility_cluster
        self._last_weight = weight
        self._last_confidence = confidence
        self._bars_since_fit += 1

        return RegimeResult(
            regime=regime,
            volatility=volatility_cluster,
            weight=weight,
            confidence=confidence,
        )

    def _calculate_regime_weight(
        self,
        regime: RegimeState,
        volatility: VolatilityCluster,
        confidence: float,
    ) -> float:
        """Calculate position sizing weight based on regime.

        Higher weights for trending regimes with low volatility.
        Lower weights for ranging/volatile regimes.

        Args:
            regime: Current regime state.
            volatility: Current volatility cluster.
            confidence: Prediction confidence.

        Returns:
            Weight between 0.0 and 1.0.
        """
        # Base weight by regime
        regime_weights = {
            RegimeState.TRENDING_UP: 1.0,
            RegimeState.TRENDING_DOWN: 1.0,
            RegimeState.RANGING: 0.5,
            RegimeState.VOLATILE: 0.3,
        }
        base_weight = regime_weights.get(regime, 0.5)

        # Volatility adjustment
        volatility_adjustments = {
            VolatilityCluster.LOW: 1.0,
            VolatilityCluster.MEDIUM: 0.8,
            VolatilityCluster.HIGH: 0.5,
        }
        vol_adjustment = volatility_adjustments.get(volatility, 0.8)

        # Combine with confidence
        weight = base_weight * vol_adjustment * (0.5 + 0.5 * confidence)

        return max(0.0, min(1.0, weight))

    def get_regime_weight(self) -> float:
        """Get the current regime-based position weight.

        Returns:
            Weight between 0.0 and 1.0.
        """
        return self._last_weight
