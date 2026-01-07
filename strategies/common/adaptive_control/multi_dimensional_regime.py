"""
Multi-Dimensional Regime Detection

Multiple views of the same market reality:
1. HMM/GMM     → Probabilistic structure
2. Spectral    → Non-parametric (FFT slope)
3. Flow        → Fluid physics (Reynolds number)
4. IIR         → Fast variance ratio (O(1))

Each dimension sees differently.
When they AGREE → high confidence.
When they DISAGREE → reduce risk, uncertainty is high.

Usage:
    detector = MultiDimensionalRegimeDetector()

    for bar in stream:
        result = detector.update(
            price=bar.close,
            bid=bar.bid,
            ask=bar.ask,
            bid_size=bar.bid_size,
            ask_size=bar.ask_size,
            volume=bar.volume,
        )

        print(f"Regime: {result.consensus}")
        print(f"Confidence: {result.confidence:.2%}")
        print(f"Risk Multiplier: {result.risk_multiplier:.2f}")

        # Dimensions breakdown
        for dim in result.dimensions:
            print(f"  {dim.name}: {dim.regime} (conf: {dim.confidence:.2%})")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from .dsp_filters import IIRRegimeDetector
from .flow_physics import MarketFlowAnalyzer

logger = logging.getLogger(__name__)


class ConsensusRegime(Enum):
    """Consensus regime from all dimensions."""

    TRENDING = "trending"  # Most agree: trending
    MEAN_REVERTING = "mean_reverting"  # Most agree: mean reverting
    TURBULENT = "turbulent"  # High volatility/uncertainty
    TRANSITIONAL = "transitional"  # Changing regime
    CONFLICT = "conflict"  # Dimensions disagree strongly
    UNKNOWN = "unknown"  # Not enough data


@dataclass
class DimensionResult:
    """Result from a single dimension."""

    name: str
    regime: str
    confidence: float
    raw_value: float  # The underlying metric


@dataclass
class MultiDimensionalResult:
    """Combined result from all dimensions."""

    # Individual dimensions
    dimensions: list[DimensionResult]

    # Consensus
    consensus: ConsensusRegime
    confidence: float  # Overall confidence (0-1)
    agreement: float  # How much dimensions agree (0-1)

    # Actionable output
    risk_multiplier: float  # Scale positions by this
    should_trade: bool  # Is it safe to trade?

    # Breakdown
    trending_votes: int = 0
    reverting_votes: int = 0
    turbulent_votes: int = 0


class MultiDimensionalRegimeDetector:
    """
    Combines multiple regime detection approaches.

    Each dimension provides a different view:
    - IIR: Fast, O(1), variance-based
    - Flow: Physics-based (Reynolds number)
    - Spectral: Optional, more accurate but slower

    Philosophy:
    - Multiple independent views reduce overfitting
    - Disagreement = uncertainty = reduce risk
    - Agreement = confidence = full position
    """

    def __init__(
        self,
        # IIR settings
        iir_fast_period: int = 10,
        iir_slow_period: int = 50,
        # Flow settings
        flow_pressure_window: int = 20,
        flow_viscosity: float = 0.1,
        # Risk settings
        min_agreement_to_trade: float = 0.5,
        uncertainty_penalty: float = 0.5,
    ):
        """
        Args:
            iir_fast_period: Fast variance period for IIR
            iir_slow_period: Slow variance period for IIR
            flow_pressure_window: Window for flow pressure
            flow_viscosity: Market viscosity for flow
            min_agreement_to_trade: Minimum agreement to allow trading
            uncertainty_penalty: Penalty to risk when uncertain
        """
        self.min_agreement = min_agreement_to_trade
        self.uncertainty_penalty = uncertainty_penalty

        # Initialize dimensions
        self._iir = IIRRegimeDetector(
            fast_period=iir_fast_period,
            slow_period=iir_slow_period,
        )
        self._flow = MarketFlowAnalyzer(
            pressure_window=flow_pressure_window,
            viscosity=flow_viscosity,
        )

        # State
        self._last_price: float | None = None
        self._update_count: int = 0
        self._history: list[MultiDimensionalResult] = []

    def update(
        self,
        price: float,
        bid: float | None = None,
        ask: float | None = None,
        bid_size: float | None = None,
        ask_size: float | None = None,
        volume: float | None = None,
    ) -> MultiDimensionalResult:
        """
        Update all dimensions with new data.

        Args:
            price: Current price (required)
            bid: Best bid (optional, for flow)
            ask: Best ask (optional, for flow)
            bid_size: Bid size (optional, for flow)
            ask_size: Ask size (optional, for flow)
            volume: Volume (optional, for flow)

        Returns:
            MultiDimensionalResult with consensus and breakdown
        """
        self._update_count += 1
        dimensions = []

        # 1. IIR Dimension (always available, O(1))
        if self._last_price is not None and self._last_price > 0:
            ret = (price - self._last_price) / self._last_price
            iir_regime = self._iir.update(ret)
            iir_conf = min(1.0, abs(self._iir.variance_ratio - 1.0))  # Confidence from deviation

            dimensions.append(
                DimensionResult(
                    name="iir",
                    regime=iir_regime,
                    confidence=iir_conf,
                    raw_value=self._iir.variance_ratio,
                )
            )

        # 2. Flow Dimension (if order book data available)
        if all(v is not None for v in [bid, ask, bid_size, ask_size, volume]):
            flow_state = self._flow.update(
                bid=bid,
                ask=ask,
                bid_size=bid_size,
                ask_size=ask_size,
                last_price=price,
                volume=volume,
            )
            flow_regime = self._flow.get_flow_regime()

            # Map flow regime to standard terms
            if flow_regime == "turbulent":
                flow_mapped = "trending"  # Turbulent = momentum
            elif flow_regime == "laminar":
                flow_mapped = "mean_reverting"  # Laminar = smooth
            else:
                flow_mapped = "transitional"

            dimensions.append(
                DimensionResult(
                    name="flow",
                    regime=flow_mapped,
                    confidence=min(1.0, flow_state.reynolds_number / 2.0),
                    raw_value=flow_state.reynolds_number,
                )
            )

        # Update state
        self._last_price = price

        # Calculate consensus
        result = self._calculate_consensus(dimensions)
        self._history.append(result)

        # Keep history bounded
        if len(self._history) > 100:
            self._history = self._history[-100:]

        return result

    def _calculate_consensus(
        self,
        dimensions: list[DimensionResult],
    ) -> MultiDimensionalResult:
        """Calculate consensus from all dimensions."""
        if not dimensions:
            return MultiDimensionalResult(
                dimensions=[],
                consensus=ConsensusRegime.UNKNOWN,
                confidence=0.0,
                agreement=0.0,
                risk_multiplier=0.1,
                should_trade=False,
            )

        # Count votes
        votes = {
            "trending": 0,
            "mean_reverting": 0,
            "turbulent": 0,
            "transitional": 0,
            "normal": 0,
            "unknown": 0,
        }

        weighted_votes = dict.fromkeys(votes, 0.0)

        for dim in dimensions:
            regime = dim.regime.lower()
            if regime in votes:
                votes[regime] += 1
                weighted_votes[regime] += dim.confidence

        # Find winner
        total_dims = len(dimensions)
        max_votes = max(votes.values())
        winner = max(votes.items(), key=lambda x: weighted_votes[x[0]])[0]

        # Calculate agreement
        agreement = max_votes / total_dims if total_dims > 0 else 0

        # Map to consensus
        if agreement >= 0.75:
            if winner == "trending":
                consensus = ConsensusRegime.TRENDING
            elif winner == "mean_reverting":
                consensus = ConsensusRegime.MEAN_REVERTING
            elif winner == "turbulent":
                consensus = ConsensusRegime.TURBULENT
            else:
                consensus = ConsensusRegime.TRANSITIONAL
        elif agreement >= 0.5:
            consensus = ConsensusRegime.TRANSITIONAL
        else:
            consensus = ConsensusRegime.CONFLICT

        # Calculate overall confidence
        avg_confidence = sum(d.confidence for d in dimensions) / total_dims
        confidence = avg_confidence * agreement

        # Calculate risk multiplier
        if agreement < self.min_agreement:
            # Low agreement = high uncertainty = reduce risk
            risk_multiplier = self.uncertainty_penalty
        else:
            # Base risk on confidence
            risk_multiplier = 0.5 + 0.5 * confidence

        # Should we trade?
        should_trade = (
            agreement >= self.min_agreement
            and confidence >= 0.3
            and consensus != ConsensusRegime.CONFLICT
        )

        return MultiDimensionalResult(
            dimensions=dimensions,
            consensus=consensus,
            confidence=confidence,
            agreement=agreement,
            risk_multiplier=risk_multiplier,
            should_trade=should_trade,
            trending_votes=votes["trending"],
            reverting_votes=votes["mean_reverting"],
            turbulent_votes=votes["turbulent"],
        )

    def get_regime_history(self, n: int = 10) -> list[ConsensusRegime]:
        """Get recent regime history."""
        return [r.consensus for r in self._history[-n:]]

    def is_regime_stable(self, window: int = 10) -> bool:
        """Check if regime has been stable recently."""
        history = self.get_regime_history(window)
        if len(history) < window:
            return False

        # Check if all same regime
        return len(set(history)) == 1

    def get_average_agreement(self, window: int = 10) -> float:
        """Get average agreement over recent history."""
        if len(self._history) < window:
            return 0.0
        recent = self._history[-window:]
        return sum(r.agreement for r in recent) / len(recent)

    @property
    def update_count(self) -> int:
        """Number of updates processed."""
        return self._update_count

    @property
    def is_ready(self) -> bool:
        """Check if detector has enough data."""
        return self._update_count >= 20  # Minimum warmup


# Convenience function
def create_multi_regime_detector(
    fast: bool = True,
) -> MultiDimensionalRegimeDetector:
    """
    Factory to create regime detector.

    Args:
        fast: If True, use fast settings. If False, more accurate.

    Returns:
        Configured MultiDimensionalRegimeDetector
    """
    if fast:
        return MultiDimensionalRegimeDetector(
            iir_fast_period=5,
            iir_slow_period=20,
            flow_pressure_window=10,
        )
    else:
        return MultiDimensionalRegimeDetector(
            iir_fast_period=10,
            iir_slow_period=50,
            flow_pressure_window=20,
        )
