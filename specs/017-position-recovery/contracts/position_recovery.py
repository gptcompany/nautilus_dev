"""
Position Recovery API Contracts (Spec 017)

This module defines the interfaces and contracts for position recovery
in NautilusTrader strategies.

These are DESIGN contracts - actual implementation will use
NautilusTrader's native types and patterns.
"""

from abc import ABC, abstractmethod
from datetime import timedelta
from enum import Enum
from typing import Protocol

from pydantic import BaseModel, Field

# Placeholder types (actual implementation uses NautilusTrader types)
InstrumentId = str
StrategyId = str
AccountId = str
ClientOrderId = str
PositionId = str


# --- Enums ---


class RecoveryPhase(str, Enum):
    """Phases of the recovery process."""

    CACHE_LOADING = "cache_loading"
    RECONCILING = "reconciling"
    DISCREPANCY_DETECTED = "discrepancy_detected"
    ALIGNED = "aligned"
    WARMING_UP = "warming_up"
    READY = "ready"


class ReconciliationStatus(str, Enum):
    """Outcome of reconciliation."""

    SUCCESS = "success"
    PARTIAL = "partial"  # Some discrepancies unresolved
    FAILED = "failed"


class ResolutionType(str, Enum):
    """How a discrepancy was resolved."""

    SYNTHETIC_FILL = "synthetic_fill"
    MANUAL = "manual"
    IGNORED = "ignored"


# --- Configuration Contracts ---


class RecoveryConfig(BaseModel):
    """Configuration for strategy recovery behavior."""

    external_order_claims: list[InstrumentId] = Field(
        default_factory=list,
        description="Instruments to claim external orders for",
    )
    warmup_bars: int = Field(
        default=500,
        ge=0,
        description="Number of historical bars for indicator warmup",
    )
    warmup_period: timedelta = Field(
        default=timedelta(days=2),
        description="Historical data lookback period for warmup",
    )
    restore_stop_loss: bool = Field(
        default=True,
        description="Recreate stop-loss orders for recovered positions",
    )
    restore_take_profit: bool = Field(
        default=True,
        description="Recreate take-profit orders for recovered positions",
    )

    class Config:
        frozen = True


# --- Data Contracts ---


class PositionDiscrepancy(BaseModel):
    """Details of a position mismatch between cache and exchange."""

    instrument_id: InstrumentId
    cached_qty: float
    venue_qty: float
    delta: float = Field(description="venue_qty - cached_qty")
    resolution: ResolutionType | None = None
    synthetic_order_id: ClientOrderId | None = None


class ReconciliationReport(BaseModel):
    """Report generated after startup reconciliation."""

    account_id: AccountId
    timestamp_ns: int
    cached_position_count: int
    venue_position_count: int
    discrepancies: list[PositionDiscrepancy] = Field(default_factory=list)
    synthetic_fills_generated: int = 0
    status: ReconciliationStatus


# --- Interface Contracts ---


class RecoverableStrategy(Protocol):
    """Protocol for strategies that support recovery."""

    @property
    def recovery_config(self) -> RecoveryConfig:
        """Recovery configuration for this strategy."""
        ...

    def on_recovery_start(self) -> None:
        """Called when recovery process begins."""
        ...

    def on_position_recovered(
        self,
        position_id: PositionId,
        instrument_id: InstrumentId,
        quantity: float,
        side: str,
    ) -> None:
        """Called for each position recovered from cache."""
        ...

    def on_reconciliation_complete(self, report: ReconciliationReport) -> None:
        """Called when reconciliation with exchange completes."""
        ...

    def on_warmup_complete(self) -> None:
        """Called when indicator warmup is finished."""
        ...

    def on_recovery_complete(self) -> None:
        """Called when full recovery process is finished."""
        ...


class PositionRestorer(ABC):
    """Abstract base for position restoration logic."""

    @abstractmethod
    def restore_stop_loss(
        self,
        position_id: PositionId,
        instrument_id: InstrumentId,
        entry_price: float,
        quantity: float,
        side: str,
    ) -> ClientOrderId | None:
        """
        Recreate stop-loss order for a recovered position.

        Returns:
            ClientOrderId of created stop-loss, or None if not created.
        """
        ...

    @abstractmethod
    def restore_take_profit(
        self,
        position_id: PositionId,
        instrument_id: InstrumentId,
        entry_price: float,
        quantity: float,
        side: str,
    ) -> ClientOrderId | None:
        """
        Recreate take-profit order for a recovered position.

        Returns:
            ClientOrderId of created take-profit, or None if not created.
        """
        ...


# --- Recovery Events (for messaging) ---


class RecoveryEvent(BaseModel):
    """Base class for recovery-related events."""

    timestamp_ns: int
    strategy_id: StrategyId


class RecoveryStartedEvent(RecoveryEvent):
    """Emitted when recovery process begins."""

    phase: RecoveryPhase = RecoveryPhase.CACHE_LOADING


class RecoveryProgressEvent(RecoveryEvent):
    """Emitted during recovery process."""

    phase: RecoveryPhase
    positions_loaded: int = 0
    positions_reconciled: int = 0
    indicators_warmed: int = 0


class RecoveryCompletedEvent(RecoveryEvent):
    """Emitted when recovery process completes."""

    phase: RecoveryPhase = RecoveryPhase.READY
    total_positions: int
    discrepancies_resolved: int
    warmup_bars_processed: int
    recovery_duration_ms: int
