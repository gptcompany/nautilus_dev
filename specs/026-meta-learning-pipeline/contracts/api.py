"""API Contracts for Meta-Learning Pipeline (Spec 026).

This module defines the public interfaces (protocols) for all components
in the meta-learning pipeline. Implementation classes MUST conform to
these interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


# =============================================================================
# Enums
# =============================================================================


class TripleBarrierLabel(Enum):
    """Triple barrier labeling outcomes.

    Values:
        STOP_LOSS: Price hit stop-loss barrier first (-1)
        TIMEOUT: Holding period expired without hitting barriers (0)
        TAKE_PROFIT: Price hit take-profit barrier first (+1)
    """

    STOP_LOSS = -1
    TIMEOUT = 0
    TAKE_PROFIT = 1


# =============================================================================
# Data Classes
# =============================================================================


@dataclass(frozen=True)
class BarrierEvent:
    """Represents a single barrier event during labeling."""

    entry_idx: int
    entry_price: float
    tp_barrier: float
    sl_barrier: float
    timeout_idx: int
    exit_idx: int
    exit_price: float
    label: TripleBarrierLabel


@dataclass(frozen=True)
class Changepoint:
    """Detected regime changepoint."""

    idx: int
    probability: float
    run_length_before: int
    trigger_refit: bool = True


@dataclass(frozen=True)
class IntegratedSize:
    """Result of integrated position sizing."""

    final_size: float
    direction: int
    signal_contribution: float
    meta_contribution: float
    regime_contribution: float
    toxicity_contribution: float
    kelly_fraction: float

    @property
    def factors(self) -> dict[str, float]:
        """Get breakdown of all factor values."""
        return {
            "signal": self.signal_contribution,
            "meta_confidence": self.meta_contribution,
            "regime_weight": self.regime_contribution,
            "toxicity_penalty": self.toxicity_contribution,
            "kelly_fraction": self.kelly_fraction,
        }


# =============================================================================
# Protocol Definitions
# =============================================================================


@runtime_checkable
class TripleBarrierLabelerProtocol(Protocol):
    """Protocol for triple barrier labeling implementations."""

    def apply(
        self,
        prices: NDArray[np.floating],
        atr_values: NDArray[np.floating],
        signals: NDArray[np.signedinteger] | None = None,
    ) -> NDArray[np.signedinteger]:
        """Apply triple barrier labeling to price series.

        Args:
            prices: Close prices array.
            atr_values: ATR values for barrier calculation.
            signals: Optional signal array (+1/-1) for entry points.
                    If None, labels all bars.

        Returns:
            Array of labels (-1, 0, +1) for each entry point.
        """
        ...

    def get_barrier_events(
        self,
        prices: NDArray[np.floating],
        atr_values: NDArray[np.floating],
        signals: NDArray[np.signedinteger] | None = None,
    ) -> list[BarrierEvent]:
        """Get detailed barrier events for analysis.

        Args:
            prices: Close prices array.
            atr_values: ATR values for barrier calculation.
            signals: Optional signal array for entry points.

        Returns:
            List of BarrierEvent objects with full details.
        """
        ...


@runtime_checkable
class MetaModelProtocol(Protocol):
    """Protocol for meta-model implementations."""

    def fit(
        self,
        features: NDArray[np.floating],
        primary_signals: NDArray[np.signedinteger],
        true_labels: NDArray[np.signedinteger],
    ) -> None:
        """Train meta-model on labeled data.

        Args:
            features: Feature matrix (n_samples, n_features).
            primary_signals: Primary model signals (+1, -1).
            true_labels: True labels from triple barrier.
        """
        ...

    def predict_proba(
        self,
        features: NDArray[np.floating],
    ) -> NDArray[np.floating]:
        """Predict P(primary_model_correct) for each sample.

        Args:
            features: Feature matrix (n_samples, n_features).

        Returns:
            Array of probabilities [0, 1] for each sample.
        """
        ...

    @property
    def is_fitted(self) -> bool:
        """Check if model has been fitted."""
        ...

    @property
    def feature_importances(self) -> NDArray[np.floating] | None:
        """Get feature importance scores if available."""
        ...


@runtime_checkable
class BOCDProtocol(Protocol):
    """Protocol for Bayesian Online Changepoint Detection."""

    def update(self, observation: float) -> None:
        """Process single observation.

        Args:
            observation: New data point (e.g., returns).
        """
        ...

    def get_changepoint_probability(self) -> float:
        """Get probability that a changepoint just occurred.

        Returns:
            P(run_length = 0) at current step.
        """
        ...

    def get_run_length_distribution(self) -> NDArray[np.floating]:
        """Get full posterior over run lengths.

        Returns:
            Array of P(run_length = r) for r in [0, max_run_length].
        """
        ...

    def is_changepoint(self, threshold: float = 0.8) -> bool:
        """Check if changepoint detected above threshold.

        Args:
            threshold: Detection threshold (default 0.8).

        Returns:
            True if P(changepoint) > threshold.
        """
        ...

    def reset(self) -> None:
        """Reset detector state."""
        ...


@runtime_checkable
class IntegratedSizerProtocol(Protocol):
    """Protocol for integrated position sizing."""

    def calculate(
        self,
        signal: float,
        meta_confidence: float | None = None,
        regime_weight: float | None = None,
        toxicity: float | None = None,
    ) -> IntegratedSize:
        """Calculate integrated position size.

        Args:
            signal: Trading signal (positive for long, negative for short).
            meta_confidence: P(correct) from meta-model [0, 1].
            regime_weight: Regime-based weight [0.4, 1.2].
            toxicity: VPIN toxicity [0, 1].

        Returns:
            IntegratedSize with final size and factor breakdown.
        """
        ...


# =============================================================================
# Abstract Base Classes (for inheritance-based implementations)
# =============================================================================


class BaseTripleBarrierLabeler(ABC):
    """Abstract base class for triple barrier labelers."""

    @abstractmethod
    def apply(
        self,
        prices: NDArray[np.floating],
        atr_values: NDArray[np.floating],
        signals: NDArray[np.signedinteger] | None = None,
    ) -> NDArray[np.signedinteger]:
        """Apply triple barrier labeling."""
        pass

    @abstractmethod
    def get_barrier_events(
        self,
        prices: NDArray[np.floating],
        atr_values: NDArray[np.floating],
        signals: NDArray[np.signedinteger] | None = None,
    ) -> list[BarrierEvent]:
        """Get detailed barrier events."""
        pass


class BaseMetaModel(ABC):
    """Abstract base class for meta-models."""

    @abstractmethod
    def fit(
        self,
        features: NDArray[np.floating],
        primary_signals: NDArray[np.signedinteger],
        true_labels: NDArray[np.signedinteger],
    ) -> None:
        """Train meta-model."""
        pass

    @abstractmethod
    def predict_proba(
        self,
        features: NDArray[np.floating],
    ) -> NDArray[np.floating]:
        """Predict probabilities."""
        pass

    @property
    @abstractmethod
    def is_fitted(self) -> bool:
        """Check if fitted."""
        pass


class BaseBOCD(ABC):
    """Abstract base class for BOCD implementations."""

    @abstractmethod
    def update(self, observation: float) -> None:
        """Process observation."""
        pass

    @abstractmethod
    def get_changepoint_probability(self) -> float:
        """Get changepoint probability."""
        pass

    @abstractmethod
    def is_changepoint(self, threshold: float = 0.8) -> bool:
        """Check if changepoint detected."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset state."""
        pass


class BaseIntegratedSizer(ABC):
    """Abstract base class for integrated sizing."""

    @abstractmethod
    def calculate(
        self,
        signal: float,
        meta_confidence: float | None = None,
        regime_weight: float | None = None,
        toxicity: float | None = None,
    ) -> IntegratedSize:
        """Calculate position size."""
        pass
