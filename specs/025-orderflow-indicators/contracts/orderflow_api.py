"""Orderflow Indicators API Contract (Spec 025).

This module defines the public interface for orderflow indicators.
Implementation must conform to these contracts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

# =============================================================================
# Enums
# =============================================================================


class ToxicityLevel(Enum):
    """Categorical toxicity classification based on VPIN value."""

    LOW = "low"  # VPIN < 0.3 - Safe to trade
    MEDIUM = "medium"  # 0.3 <= VPIN < 0.7 - Trade with caution
    HIGH = "high"  # VPIN >= 0.7 - Reduce position or avoid

    @classmethod
    def from_vpin(cls, vpin: float) -> ToxicityLevel:
        """Convert VPIN value to toxicity level."""
        if vpin < 0.3:
            return cls.LOW
        elif vpin < 0.7:
            return cls.MEDIUM
        else:
            return cls.HIGH


class TradeSide(Enum):
    """Trade direction classification."""

    BUY = 1
    SELL = -1
    UNKNOWN = 0


# =============================================================================
# Data Classes
# =============================================================================


@dataclass(frozen=True)
class TradeClassification:
    """Result of classifying a trade as buy or sell."""

    side: TradeSide
    volume: float
    price: float
    timestamp_ns: int
    method: str
    confidence: float = 1.0


@dataclass
class VPINResult:
    """Result from VPIN indicator."""

    value: float  # VPIN value [0.0, 1.0]
    toxicity: ToxicityLevel
    bucket_count: int  # Number of completed buckets
    last_bucket_oi: float  # Order imbalance of last bucket
    is_valid: bool  # True if enough data for valid VPIN


@dataclass
class HawkesResult:
    """Result from Hawkes OFI indicator."""

    ofi: float  # Order Flow Imbalance [-1.0, 1.0]
    buy_intensity: float  # Current λ_buy
    sell_intensity: float  # Current λ_sell
    branching_ratio: float  # η = α/β (stationarity indicator)
    is_fitted: bool  # True if model has been fitted


# =============================================================================
# Protocols (Interfaces)
# =============================================================================


class TradeClassifier(Protocol):
    """Protocol for trade classification implementations."""

    def classify(
        self,
        price: float,
        volume: float,
        timestamp_ns: int,
        prev_price: float | None = None,
        open_price: float | None = None,
        high: float | None = None,
        low: float | None = None,
    ) -> TradeClassification:
        """Classify a trade as buy or sell.

        Args:
            price: Trade price (or bar close)
            volume: Trade volume
            timestamp_ns: Trade timestamp in nanoseconds
            prev_price: Previous price (for tick rule)
            open_price: Bar open price (for close-vs-open)
            high: Bar high (for BVC)
            low: Bar low (for BVC)

        Returns:
            TradeClassification with side and metadata
        """
        ...


class VPINIndicator(Protocol):
    """Protocol for VPIN indicator implementations."""

    @property
    def value(self) -> float:
        """Current VPIN value [0.0, 1.0]."""
        ...

    @property
    def toxicity_level(self) -> ToxicityLevel:
        """Current toxicity level."""
        ...

    @property
    def is_valid(self) -> bool:
        """True if enough buckets accumulated for valid VPIN."""
        ...

    def update(self, classification: TradeClassification) -> None:
        """Update VPIN with a new trade classification.

        Args:
            classification: Classified trade with side and volume
        """
        ...

    def reset(self) -> None:
        """Reset indicator state."""
        ...

    def get_result(self) -> VPINResult:
        """Get full VPIN result with metadata."""
        ...


class HawkesOFIIndicator(Protocol):
    """Protocol for Hawkes OFI indicator implementations."""

    @property
    def ofi(self) -> float:
        """Current Order Flow Imbalance [-1.0, 1.0]."""
        ...

    @property
    def buy_intensity(self) -> float:
        """Current buy-side intensity."""
        ...

    @property
    def sell_intensity(self) -> float:
        """Current sell-side intensity."""
        ...

    @property
    def is_fitted(self) -> bool:
        """True if Hawkes model has been fitted."""
        ...

    def update(self, classification: TradeClassification) -> None:
        """Update Hawkes model with a new trade classification.

        Args:
            classification: Classified trade with side and timestamp
        """
        ...

    def refit(self) -> None:
        """Refit the Hawkes model on accumulated data."""
        ...

    def reset(self) -> None:
        """Reset indicator state."""
        ...

    def get_result(self) -> HawkesResult:
        """Get full Hawkes result with metadata."""
        ...


class OrderflowManager(Protocol):
    """Protocol for unified orderflow management."""

    @property
    def toxicity(self) -> float:
        """Current toxicity from VPIN [0.0, 1.0]."""
        ...

    @property
    def ofi(self) -> float:
        """Current Order Flow Imbalance [-1.0, 1.0]."""
        ...

    @property
    def vpin_result(self) -> VPINResult:
        """Full VPIN result."""
        ...

    @property
    def hawkes_result(self) -> HawkesResult:
        """Full Hawkes result."""
        ...

    def handle_bar(self, bar) -> None:
        """Process a NautilusTrader Bar.

        Args:
            bar: nautilus_trader.model.data.Bar
        """
        ...

    def reset(self) -> None:
        """Reset all indicators."""
        ...


# =============================================================================
# Abstract Base Classes (for implementation guidance)
# =============================================================================


class BaseTradeClassifier(ABC):
    """Abstract base for trade classifiers."""

    @abstractmethod
    def classify(
        self,
        price: float,
        volume: float,
        timestamp_ns: int,
        prev_price: float | None = None,
        open_price: float | None = None,
        high: float | None = None,
        low: float | None = None,
    ) -> TradeClassification:
        """Classify a trade as buy or sell."""
        pass

    @property
    @abstractmethod
    def method_name(self) -> str:
        """Name of classification method."""
        pass


class BaseVPINIndicator(ABC):
    """Abstract base for VPIN indicators."""

    @abstractmethod
    def update(self, classification: TradeClassification) -> None:
        """Update with new trade."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset state."""
        pass

    @property
    @abstractmethod
    def value(self) -> float:
        """Current VPIN value."""
        pass

    @property
    def toxicity_level(self) -> ToxicityLevel:
        """Derived toxicity level."""
        return ToxicityLevel.from_vpin(self.value)

    @property
    @abstractmethod
    def is_valid(self) -> bool:
        """True if valid."""
        pass


class BaseHawkesOFI(ABC):
    """Abstract base for Hawkes OFI indicators."""

    @abstractmethod
    def update(self, classification: TradeClassification) -> None:
        """Update with new trade."""
        pass

    @abstractmethod
    def refit(self) -> None:
        """Refit model."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset state."""
        pass

    @property
    @abstractmethod
    def ofi(self) -> float:
        """Current OFI."""
        pass

    @property
    @abstractmethod
    def is_fitted(self) -> bool:
        """True if fitted."""
        pass
