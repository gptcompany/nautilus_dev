"""Regime Ensemble Voting System.

Implements ensemble voting across multiple regime detectors (BOCD, HMM, GMM)
with configurable voting strategies (majority, weighted) for robust regime
detection with reduced false positives.

Design Principles:
    - P1 (Probabilistic): Confidence-weighted voting with uncertainty quantification
    - P2 (Non-Linear): BOCD handles fat-tailed changepoints
    - P3 (Non-Parametric): Detector weights are configurable, not fixed
    - P4 (Scale-Invariant): Works at any frequency via configurable update intervals

Key Components:
    - BaseRegimeDetector: Protocol for detector abstraction
    - RegimeEnsemble: Aggregates multiple detectors with voting
    - Voting strategies: Majority (N-out-of-M) and weighted confidence

Reference:
    Adams, R. P., & MacKay, D. J. (2007). Bayesian Online Changepoint Detection.
    arXiv preprint arXiv:0710.3742.

Example:
    >>> from strategies.common.regime_detection.ensemble import (
    ...     RegimeEnsemble, BaseRegimeDetector
    ... )
    >>> from strategies.common.regime_detection import BOCD, BOCDConfig
    >>>
    >>> # Create ensemble with detectors
    >>> ensemble = RegimeEnsemble(
    ...     detectors={"bocd": bocd_detector, "hmm": hmm_detector},
    ...     weights={"bocd": 0.5, "hmm": 0.5},
    ... )
    >>>
    >>> # Update with new observation
    >>> event = ensemble.update(0.02)  # 2% return
    >>> if event is not None:
    ...     print(f"Regime changed to {event.new_regime}")
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from strategies.common.regime_detection.events import RegimeChangeEvent, RegimeVote
from strategies.common.regime_detection.types import RegimeState

if TYPE_CHECKING:
    from strategies.common.regime_detection.bocd import BOCD
    from strategies.common.regime_detection.gmm_filter import GMMVolatilityFilter
    from strategies.common.regime_detection.hmm_filter import HMMRegimeFilter


logger = logging.getLogger(__name__)


# =============================================================================
# Base Protocol
# =============================================================================


@runtime_checkable
class BaseRegimeDetector(Protocol):
    """Protocol defining the interface for regime detectors.

    All detectors in the ensemble must satisfy this protocol.
    The protocol is designed to be minimal and flexible to accommodate
    different detector implementations (BOCD, HMM, GMM).

    Methods:
        update: Process a new observation
        current_regime: Get current regime classification
        confidence: Get confidence score (0.0-1.0)
        is_warmed_up: Check if detector has completed warmup
    """

    def update(self, value: float) -> None:
        """Process a new observation.

        Args:
            value: New data point (e.g., return, price change).
        """
        ...

    def current_regime(self) -> RegimeState:
        """Get the current regime classification.

        Returns:
            Current RegimeState (TRENDING_UP, TRENDING_DOWN, RANGING, VOLATILE).
        """
        ...

    def confidence(self) -> float:
        """Get confidence score for current regime.

        Returns:
            Confidence between 0.0 and 1.0.
        """
        ...

    def is_warmed_up(self) -> bool:
        """Check if detector has completed initialization/warmup.

        Returns:
            True if detector is ready to contribute to voting.
        """
        ...


# =============================================================================
# Detector Adapters
# =============================================================================


@dataclass
class DetectorState:
    """Tracks state of a detector in the ensemble.

    Attributes:
        name: Unique identifier for the detector.
        detector: The underlying detector instance.
        weight: Voting weight (0.0 to 1.0).
        is_healthy: Whether the detector is operational.
        last_error: Last error message if any.
        observations_processed: Count of observations processed.
    """

    name: str
    detector: BaseRegimeDetector
    weight: float = 1.0
    is_healthy: bool = True
    last_error: str | None = None
    observations_processed: int = 0


class BOCDAdapter:
    """Adapter to make BOCD satisfy BaseRegimeDetector protocol.

    BOCD is a changepoint detector, not a regime detector. This adapter
    interprets changepoint detection as regime information:
    - High changepoint probability → VOLATILE regime
    - Stable with increasing values → TRENDING_UP
    - Stable with decreasing values → TRENDING_DOWN
    - Otherwise → RANGING

    Attributes:
        bocd: The underlying BOCD instance.
        warmup_bars: Number of bars required for warmup.
    """

    def __init__(
        self,
        bocd: BOCD,
        warmup_bars: int = 20,
    ) -> None:
        """Initialize BOCD adapter.

        Args:
            bocd: The BOCD instance to wrap.
            warmup_bars: Bars required before contributing to voting.
        """
        from strategies.common.regime_detection.bocd import BOCD as BOCDClass

        if not isinstance(bocd, BOCDClass):
            raise TypeError(f"Expected BOCD instance, got {type(bocd)}")

        self._bocd = bocd
        self._warmup_bars = warmup_bars
        self._current_regime = RegimeState.RANGING
        self._confidence = 0.0
        self._last_values: list[float] = []
        self._max_history = 20

    def update(self, value: float) -> None:
        """Process a new observation.

        Args:
            value: New data point (e.g., return value).
        """
        # Update BOCD
        self._bocd.update(value)

        # Track recent values for regime inference
        self._last_values.append(value)
        if len(self._last_values) > self._max_history:
            self._last_values = self._last_values[-self._max_history :]

        # Infer regime from changepoint state and trend
        self._infer_regime()

    def _infer_regime(self) -> None:
        """Infer regime from BOCD state and recent values."""
        cp_prob = self._bocd.get_changepoint_probability()

        # High changepoint probability indicates volatility/instability
        if self._bocd.is_changepoint() or cp_prob > 0.5:
            self._current_regime = RegimeState.VOLATILE
            self._confidence = min(1.0, cp_prob * 2)  # Scale up confidence
            return

        # Analyze recent trend
        if len(self._last_values) >= 5:
            recent = self._last_values[-5:]
            mean_return = sum(recent) / len(recent)
            volatility = sum(abs(r - mean_return) for r in recent) / len(recent)

            # Classify based on mean return and volatility
            if volatility > 0.02:  # High volatility threshold (2% avg deviation)
                self._current_regime = RegimeState.VOLATILE
                self._confidence = 0.7
            elif mean_return > 0.001:  # Positive trend threshold
                self._current_regime = RegimeState.TRENDING_UP
                self._confidence = 0.6 + min(0.3, abs(mean_return) * 10)
            elif mean_return < -0.001:  # Negative trend threshold
                self._current_regime = RegimeState.TRENDING_DOWN
                self._confidence = 0.6 + min(0.3, abs(mean_return) * 10)
            else:
                self._current_regime = RegimeState.RANGING
                self._confidence = 0.5
        else:
            self._current_regime = RegimeState.RANGING
            self._confidence = 0.3

    def current_regime(self) -> RegimeState:
        """Get the current regime classification."""
        return self._current_regime

    def confidence(self) -> float:
        """Get confidence score for current regime."""
        return self._confidence

    def is_warmed_up(self) -> bool:
        """Check if detector has completed warmup."""
        return self._bocd.is_warmed_up(self._warmup_bars)


class HMMAdapter:
    """Adapter to make HMMRegimeFilter satisfy BaseRegimeDetector protocol.

    The HMM filter requires returns and volatility, so this adapter
    maintains a rolling window to calculate these features.

    Attributes:
        hmm: The underlying HMMRegimeFilter instance.
        warmup_bars: Number of bars required for warmup and fitting.
    """

    def __init__(
        self,
        hmm: HMMRegimeFilter,  # type: ignore[name-defined]
        warmup_bars: int = 50,
        volatility_window: int = 20,
    ) -> None:
        """Initialize HMM adapter.

        Args:
            hmm: The HMMRegimeFilter instance to wrap.
            warmup_bars: Bars required before contributing to voting.
            volatility_window: Window for volatility calculation.
        """
        from strategies.common.regime_detection.hmm_filter import HMMRegimeFilter

        if not isinstance(hmm, HMMRegimeFilter):
            raise TypeError(f"Expected HMMRegimeFilter instance, got {type(hmm)}")

        self._hmm = hmm
        self._warmup_bars = warmup_bars
        self._volatility_window = volatility_window
        self._current_regime = RegimeState.RANGING
        self._confidence = 0.0
        self._prices: list[float] = []
        self._observations = 0

    def update(self, value: float) -> None:
        """Process a new observation (price or return).

        Note: This adapter interprets the input as a price. For returns,
        use the value directly as the return and skip price-to-return conversion.

        Args:
            value: New data point (price).
        """
        self._prices.append(value)
        self._observations += 1

        # Keep rolling window
        max_history = self._warmup_bars * 2
        if len(self._prices) > max_history:
            self._prices = self._prices[-max_history:]

        # Fit HMM if not fitted and we have enough data
        if not self._hmm.is_fitted and len(self._prices) >= self._warmup_bars:
            self._fit_hmm()

        # Predict if fitted
        if self._hmm.is_fitted and len(self._prices) >= 2:
            self._predict()

    def _fit_hmm(self) -> None:
        """Fit HMM on historical data."""
        import numpy as np

        prices = np.array(self._prices)
        returns = np.diff(prices) / prices[:-1]

        # Simple volatility calculation (rolling std of returns)
        volatility = np.zeros_like(returns)
        for i in range(len(returns)):
            start = max(0, i - self._volatility_window + 1)
            volatility[i] = np.std(returns[start : i + 1]) if i >= start else 0.01

        # Fit HMM
        try:
            self._hmm.fit(returns, volatility)
        except ValueError:
            pass  # Not enough data, will retry

    def _predict(self) -> None:
        """Predict current regime."""
        import numpy as np

        prices = np.array(self._prices)
        returns = np.diff(prices) / prices[:-1]
        current_return = returns[-1]

        # Calculate current volatility
        vol_window = min(self._volatility_window, len(returns))
        current_volatility = np.std(returns[-vol_window:]) if vol_window > 1 else 0.01

        # Predict regime
        self._current_regime = self._hmm.predict(current_return, current_volatility)

        # Get confidence from state probabilities
        probs = self._hmm.get_state_probabilities(current_return, current_volatility)
        self._confidence = float(np.max(probs))

    def current_regime(self) -> RegimeState:
        """Get the current regime classification."""
        return self._current_regime

    def confidence(self) -> float:
        """Get confidence score for current regime."""
        return self._confidence

    def is_warmed_up(self) -> bool:
        """Check if detector has completed warmup."""
        return self._hmm.is_fitted and self._observations >= self._warmup_bars


class GMMAdapter:
    """Adapter to make GMMVolatilityFilter satisfy BaseRegimeDetector protocol.

    The GMM filter clusters volatility into LOW/MEDIUM/HIGH. This adapter
    maps volatility clusters to regime states.

    Attributes:
        gmm: The underlying GMMVolatilityFilter instance.
        warmup_bars: Number of bars required for warmup and fitting.
    """

    def __init__(
        self,
        gmm: GMMVolatilityFilter,  # type: ignore[name-defined]
        warmup_bars: int = 100,
        volatility_window: int = 20,
    ) -> None:
        """Initialize GMM adapter.

        Args:
            gmm: The GMMVolatilityFilter instance to wrap.
            warmup_bars: Bars required before contributing to voting.
            volatility_window: Window for volatility calculation.
        """
        from strategies.common.regime_detection.gmm_filter import GMMVolatilityFilter
        from strategies.common.regime_detection.types import VolatilityCluster

        if not isinstance(gmm, GMMVolatilityFilter):
            raise TypeError(f"Expected GMMVolatilityFilter instance, got {type(gmm)}")

        self._gmm = gmm
        self._warmup_bars = warmup_bars
        self._volatility_window = volatility_window
        self._current_regime = RegimeState.RANGING
        self._confidence = 0.0
        self._prices: list[float] = []
        self._observations = 0
        self._VolatilityCluster = VolatilityCluster

    def update(self, value: float) -> None:
        """Process a new observation (price).

        Args:
            value: New data point (price).
        """
        self._prices.append(value)
        self._observations += 1

        # Keep rolling window
        max_history = self._warmup_bars * 2
        if len(self._prices) > max_history:
            self._prices = self._prices[-max_history:]

        # Fit GMM if not fitted and we have enough data
        if not self._gmm.is_fitted and len(self._prices) >= self._warmup_bars:
            self._fit_gmm()

        # Predict if fitted
        if self._gmm.is_fitted and len(self._prices) >= self._volatility_window:
            self._predict()

    def _fit_gmm(self) -> None:
        """Fit GMM on historical volatility."""
        import numpy as np

        prices = np.array(self._prices)
        returns = np.diff(prices) / prices[:-1]

        # Calculate rolling volatility
        volatility = np.zeros(len(returns))
        for i in range(len(returns)):
            start = max(0, i - self._volatility_window + 1)
            volatility[i] = np.std(returns[start : i + 1]) if i >= start else 0.01

        # Fit GMM
        try:
            self._gmm.fit(volatility)
        except ValueError:
            pass  # Not enough data, will retry

    def _predict(self) -> None:
        """Predict current regime based on volatility cluster."""
        import numpy as np

        prices = np.array(self._prices)
        returns = np.diff(prices) / prices[:-1]

        # Calculate current volatility
        vol_window = min(self._volatility_window, len(returns))
        current_volatility = np.std(returns[-vol_window:]) if vol_window > 1 else 0.01

        # Predict volatility cluster
        cluster = self._gmm.predict(current_volatility)

        # Map volatility cluster to regime
        # LOW volatility → RANGING (calm market)
        # MEDIUM volatility → RANGING or TRENDING
        # HIGH volatility → VOLATILE
        if cluster == self._VolatilityCluster.HIGH:
            self._current_regime = RegimeState.VOLATILE
        elif cluster == self._VolatilityCluster.LOW:
            self._current_regime = RegimeState.RANGING
        else:  # MEDIUM - check trend
            recent_returns = returns[-5:] if len(returns) >= 5 else returns
            mean_return = np.mean(recent_returns)
            if mean_return > 0.001:
                self._current_regime = RegimeState.TRENDING_UP
            elif mean_return < -0.001:
                self._current_regime = RegimeState.TRENDING_DOWN
            else:
                self._current_regime = RegimeState.RANGING

        # Get confidence from cluster probabilities
        probs = self._gmm.get_cluster_probabilities(current_volatility)
        self._confidence = float(np.max(probs))

    def current_regime(self) -> RegimeState:
        """Get the current regime classification."""
        return self._current_regime

    def confidence(self) -> float:
        """Get confidence score for current regime."""
        return self._confidence

    def is_warmed_up(self) -> bool:
        """Check if detector has completed warmup."""
        return self._gmm.is_fitted and self._observations >= self._warmup_bars


# =============================================================================
# Ensemble Implementation
# =============================================================================


class RegimeEnsemble:
    """Ensemble voting system for regime detection.

    Aggregates multiple regime detectors and determines consensus
    regime using configurable voting strategies.

    Supports:
        - Majority voting: N-out-of-M threshold
        - Weighted voting: Confidence-weighted scores
        - Hybrid: Weighted with minimum detector threshold

    Attributes:
        detectors: Dictionary of registered detectors.
        weights: Voting weights for each detector.
        voting_threshold: Threshold for regime change (0.0-1.0).
        min_detectors: Minimum detectors required for consensus.
        use_weighted_voting: Whether to use weighted (True) or majority (False) voting.

    Example:
        >>> ensemble = RegimeEnsemble(
        ...     detectors={"bocd": bocd, "hmm": hmm_adapter},
        ...     weights={"bocd": 0.6, "hmm": 0.4},
        ...     voting_threshold=0.5,
        ... )
        >>> event = ensemble.update(0.01)
    """

    def __init__(
        self,
        detectors: dict[str, BaseRegimeDetector] | None = None,
        weights: dict[str, float] | None = None,
        voting_threshold: float = 0.5,
        min_detectors: int = 2,
        use_weighted_voting: bool = True,
        on_regime_change: Callable[[RegimeChangeEvent], None] | None = None,
    ) -> None:
        """Initialize RegimeEnsemble.

        Args:
            detectors: Dict of detector_name -> detector instance.
            weights: Dict of detector_name -> weight (0.0-1.0).
                    If None, equal weights are assigned.
            voting_threshold: Threshold for regime change confirmation (0.0-1.0).
                             For majority voting: fraction of detectors that must agree.
                             For weighted voting: minimum weighted confidence.
            min_detectors: Minimum number of warmed-up detectors required for voting.
            use_weighted_voting: If True, use confidence-weighted voting.
                                If False, use simple majority voting.
            on_regime_change: Optional callback invoked on regime changes (FR-010).
        """
        self._detectors: dict[str, DetectorState] = {}
        self._voting_threshold = voting_threshold
        self._min_detectors = min_detectors
        self._use_weighted_voting = use_weighted_voting
        self._on_regime_change = on_regime_change

        # State tracking
        self._current_regime: RegimeState = RegimeState.RANGING
        self._last_votes: list[RegimeVote] = []
        self._observations_processed: int = 0
        self._last_event_time: datetime | None = None

        # Register detectors
        if detectors:
            for name, detector in detectors.items():
                weight = weights.get(name, 1.0) if weights else 1.0
                self._detectors[name] = DetectorState(
                    name=name,
                    detector=detector,
                    weight=weight,
                )

            # Normalize weights if provided
            if weights:
                self._normalize_weights()

    def _normalize_weights(self) -> None:
        """Normalize detector weights to sum to 1.0."""
        total = sum(d.weight for d in self._detectors.values() if d.is_healthy)
        if total > 0:
            for state in self._detectors.values():
                if state.is_healthy:
                    state.weight /= total

    def add_detector(
        self,
        name: str,
        detector: BaseRegimeDetector,
        weight: float = 1.0,
    ) -> None:
        """Add a detector to the ensemble.

        Args:
            name: Unique identifier for the detector.
            detector: Detector instance satisfying BaseRegimeDetector protocol.
            weight: Initial voting weight (will be normalized).
        """
        if weight < 0:
            raise ValueError(f"Weight must be non-negative, got {weight}")

        self._detectors[name] = DetectorState(
            name=name,
            detector=detector,
            weight=weight,
        )
        self._normalize_weights()

    def remove_detector(self, name: str) -> None:
        """Remove a detector from the ensemble.

        Args:
            name: Detector identifier to remove.
        """
        if name in self._detectors:
            del self._detectors[name]
            self._normalize_weights()

    def set_weights(self, weights: dict[str, float]) -> None:
        """Update detector weights at runtime (FR-013).

        Args:
            weights: Dict of detector_name -> new weight.
                    Weights must be non-negative and will be normalized.

        Raises:
            ValueError: If any weight is negative or weights don't sum > 0.
        """
        # Validate weights
        for name, weight in weights.items():
            if weight < 0:
                raise ValueError(f"Weight for '{name}' must be non-negative, got {weight}")
            if name not in self._detectors:
                logger.warning(f"Unknown detector '{name}' in weights, ignoring")

        total = sum(weights.get(name, 0) for name in self._detectors)
        if total <= 0:
            raise ValueError("Weights must sum to a positive value")

        # Apply new weights
        for name, state in self._detectors.items():
            if name in weights:
                state.weight = weights[name]
            else:
                state.weight = 0.0

        self._normalize_weights()
        logger.debug(f"Updated detector weights: {self._get_weight_summary()}")

    def _get_weight_summary(self) -> dict[str, float]:
        """Get summary of current detector weights."""
        return {name: state.weight for name, state in self._detectors.items()}

    def update(self, value: float) -> RegimeChangeEvent | None:
        """Process a new observation across all detectors.

        Updates all healthy detectors and determines ensemble regime
        through voting. Emits RegimeChangeEvent if regime changes.

        Args:
            value: New observation (e.g., return, price change).

        Returns:
            RegimeChangeEvent if regime changed, None otherwise.
        """
        self._observations_processed += 1
        timestamp = datetime.now()
        votes: list[RegimeVote] = []

        # Update all healthy detectors
        for name, state in self._detectors.items():
            if not state.is_healthy:
                continue

            try:
                state.detector.update(value)
                state.observations_processed += 1

                # Collect vote if detector is warmed up
                if state.detector.is_warmed_up():
                    regime = state.detector.current_regime()
                    confidence = state.detector.confidence()
                    votes.append(
                        RegimeVote(
                            detector_id=name,
                            regime=regime,
                            confidence=confidence,
                            timestamp=timestamp,
                        )
                    )
            except Exception as e:
                # Handle detector failure gracefully (FR-011)
                self._handle_detector_failure(name, e)

        self._last_votes = votes

        # Check if we have enough detectors for voting
        if len(votes) < self._min_detectors:
            logger.debug(f"Insufficient detectors for voting: {len(votes)} < {self._min_detectors}")
            return None

        # Determine consensus regime
        new_regime, aggregate_conf = self._vote(votes)

        # Check for regime change
        if new_regime != self._current_regime and aggregate_conf >= self._voting_threshold:
            old_regime = self._current_regime
            self._current_regime = new_regime

            event = RegimeChangeEvent(
                old_regime=old_regime,
                new_regime=new_regime,
                confidence=aggregate_conf,
                timestamp=timestamp,
                votes=votes,
            )

            # Log regime change (FR-009)
            self._log_regime_change(event)

            # Invoke callback if registered (FR-010)
            if self._on_regime_change:
                try:
                    self._on_regime_change(event)
                except Exception as e:
                    logger.error(f"Error in regime change callback: {e}")

            self._last_event_time = timestamp
            return event

        return None

    def _vote(self, votes: list[RegimeVote]) -> tuple[RegimeState, float]:
        """Determine consensus regime from detector votes.

        Args:
            votes: List of detector votes.

        Returns:
            Tuple of (winning regime, aggregate confidence).
        """
        if self._use_weighted_voting:
            return self._weighted_vote(votes)
        else:
            return self._majority_vote(votes)

    def _majority_vote(self, votes: list[RegimeVote]) -> tuple[RegimeState, float]:
        """Simple majority voting (FR-004).

        Each detector gets one vote. Winner is regime with most votes.

        Args:
            votes: List of detector votes.

        Returns:
            Tuple of (winning regime, fraction of votes).
        """
        # Count votes per regime
        vote_counts: dict[RegimeState, int] = {}
        for vote in votes:
            vote_counts[vote.regime] = vote_counts.get(vote.regime, 0) + 1

        # Find winner
        winner = max(vote_counts, key=lambda r: vote_counts[r])
        confidence = vote_counts[winner] / len(votes)

        return winner, confidence

    def _weighted_vote(self, votes: list[RegimeVote]) -> tuple[RegimeState, float]:
        """Confidence-weighted voting (FR-004).

        Each detector's vote is weighted by its configured weight
        and confidence score.

        Args:
            votes: List of detector votes.

        Returns:
            Tuple of (winning regime, weighted confidence score).
        """
        # Calculate weighted scores per regime
        regime_scores: dict[RegimeState, float] = {}
        total_weight = 0.0

        for vote in votes:
            state = self._detectors.get(vote.detector_id)
            if state is None:
                continue

            weight = state.weight * vote.confidence
            regime_scores[vote.regime] = regime_scores.get(vote.regime, 0.0) + weight
            total_weight += weight

        # Normalize scores
        if total_weight > 0:
            for regime in regime_scores:
                regime_scores[regime] /= total_weight

        # Find winner
        if not regime_scores:
            return self._current_regime, 0.0

        winner = max(regime_scores, key=lambda r: regime_scores[r])
        confidence = regime_scores[winner]

        return winner, confidence

    def _handle_detector_failure(self, name: str, error: Exception) -> None:
        """Handle detector failure gracefully (FR-011).

        Marks detector as unhealthy and logs error.
        Ensemble continues with remaining healthy detectors.

        Args:
            name: Detector identifier.
            error: The exception that occurred.
        """
        state = self._detectors.get(name)
        if state:
            state.is_healthy = False
            state.last_error = str(error)
            logger.error(f"Detector '{name}' failed: {error}")
            logger.warning(
                f"Detector '{name}' removed from ensemble. "
                f"Remaining healthy detectors: {self._count_healthy_detectors()}"
            )
            self._normalize_weights()

    def _count_healthy_detectors(self) -> int:
        """Count number of healthy detectors."""
        return sum(1 for d in self._detectors.values() if d.is_healthy)

    def _log_regime_change(self, event: RegimeChangeEvent) -> None:
        """Log regime change with detector votes (FR-009)."""
        vote_summary = ", ".join(
            f"{v.detector_id}={v.regime.name}({v.confidence:.2f})" for v in event.votes
        )
        logger.info(
            f"Regime change: {event.old_regime.name} -> {event.new_regime.name} "
            f"(confidence={event.confidence:.2f}) votes=[{vote_summary}]"
        )

    def current_regime(self) -> RegimeState:
        """Get current consensus regime.

        Returns:
            Current RegimeState.
        """
        return self._current_regime

    @property
    def current_regime_property(self) -> RegimeState:
        """Property alias for backward compatibility (US4)."""
        return self._current_regime

    def get_votes(self) -> list[RegimeVote]:
        """Get votes from last update (FR-008).

        Returns:
            List of RegimeVote from most recent update.
        """
        return self._last_votes.copy()

    def aggregate_confidence(self) -> float:
        """Get aggregate confidence from last votes (FR-008).

        Returns:
            Aggregate confidence score (0.0-1.0).
        """
        if not self._last_votes:
            return 0.0

        if self._use_weighted_voting:
            _, confidence = self._weighted_vote(self._last_votes)
            return confidence
        else:
            _, confidence = self._majority_vote(self._last_votes)
            return confidence

    def is_healthy(self) -> bool:
        """Check if ensemble has sufficient healthy detectors.

        Returns:
            True if at least min_detectors are healthy.
        """
        return self._count_healthy_detectors() >= self._min_detectors

    def reset_detector(self, name: str) -> bool:
        """Reset a failed detector to healthy state.

        Args:
            name: Detector identifier.

        Returns:
            True if detector was reset, False if not found.
        """
        state = self._detectors.get(name)
        if state:
            state.is_healthy = True
            state.last_error = None
            self._normalize_weights()
            logger.info(f"Detector '{name}' reset to healthy")
            return True
        return False

    def get_detector_status(self) -> dict[str, dict]:
        """Get status of all detectors.

        Returns:
            Dict of detector_name -> status info.
        """
        return {
            name: {
                "healthy": state.is_healthy,
                "weight": state.weight,
                "warmed_up": state.detector.is_warmed_up() if state.is_healthy else False,
                "observations": state.observations_processed,
                "last_error": state.last_error,
            }
            for name, state in self._detectors.items()
        }
