"""VPIN (Volume-Synchronized Probability of Informed Trading) Indicator.

This module implements the VPIN indicator for detecting toxic order flow.
VPIN measures the probability that informed traders are present in the market
by analyzing order flow imbalance across volume-synchronized time buckets.

References:
    Easley, D., Lopez de Prado, M., & O'Hara, M. (2012).
    Flow Toxicity and Liquidity in a High-Frequency World.
    The Review of Financial Studies.

Tasks:
    - T017: VPINBucket dataclass
    - T018: VPINIndicator.__init__
    - T019: VPINIndicator.update
    - T020: VPINIndicator.value
    - T021: VPINIndicator.toxicity_level
    - T022: VPINIndicator.reset
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from strategies.common.orderflow.config import VPINConfig
from strategies.common.orderflow.trade_classifier import (
    TradeClassification,
    TradeSide,
    create_classifier,
)

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar


class ToxicityLevel(Enum):
    """Categorical toxicity classification based on VPIN value.

    Values:
        LOW: VPIN < 0.3 - Safe to trade, low probability of informed traders
        MEDIUM: 0.3 <= VPIN < 0.7 - Trade with caution, moderate toxicity
        HIGH: VPIN >= 0.7 - Reduce position or avoid, high toxicity

    The thresholds are based on empirical studies showing that:
    - VPIN > 0.7 historically preceded the 2010 Flash Crash
    - VPIN persistently above 0.5 indicates elevated informed trading risk
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def from_vpin(cls, vpin: float) -> ToxicityLevel:
        """Convert VPIN value to toxicity level.

        Args:
            vpin: VPIN value in range [0.0, 1.0]

        Returns:
            ToxicityLevel corresponding to the VPIN value
        """
        if vpin < 0.3:
            return cls.LOW
        elif vpin < 0.7:
            return cls.MEDIUM
        else:
            return cls.HIGH


@dataclass
class VPINBucket:
    """A volume-synchronized bucket for VPIN calculation.

    VPIN divides trading activity into fixed-volume buckets rather than
    fixed-time periods. Each bucket accumulates trades until the target
    volume is reached, then calculates the order imbalance.

    Attributes:
        volume_target: Target volume for this bucket
        accumulated_volume: Current total volume accumulated
        buy_volume: Volume classified as buyer-initiated
        sell_volume: Volume classified as seller-initiated
        start_time: Bucket start timestamp in nanoseconds
        end_time: Bucket end timestamp in nanoseconds (None if incomplete)
    """

    volume_target: float
    start_time: int
    accumulated_volume: float = 0.0
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    end_time: int | None = None

    @property
    def order_imbalance(self) -> float:
        """Calculate the order imbalance for this bucket.

        Order imbalance (OI) = |V_buy - V_sell| / (V_buy + V_sell)

        Returns:
            Order imbalance value in range [0.0, 1.0]
            Returns 0.0 if no volume accumulated
        """
        total = self.buy_volume + self.sell_volume
        if total <= 0:
            return 0.0
        return abs(self.buy_volume - self.sell_volume) / total

    @property
    def is_complete(self) -> bool:
        """Check if the bucket has reached its target volume.

        Returns:
            True if accumulated volume >= target volume
        """
        return self.accumulated_volume >= self.volume_target


@dataclass(frozen=True)
class VPINResult:
    """Result from VPIN indicator.

    Attributes:
        value: VPIN value in range [0.0, 1.0]
        toxicity: Categorical toxicity level
        bucket_count: Number of completed buckets in history
        last_bucket_oi: Order imbalance of the last completed bucket
        is_valid: True if enough buckets for valid VPIN calculation
    """

    value: float
    toxicity: ToxicityLevel
    bucket_count: int
    last_bucket_oi: float
    is_valid: bool


class VPINIndicator:
    """VPIN (Volume-Synchronized Probability of Informed Trading) Indicator.

    VPIN measures market toxicity by calculating the average order imbalance
    across n volume-synchronized buckets. High VPIN values indicate
    elevated probability of informed trading activity.

    Key characteristics:
    - Volume-synchronized: Uses volume buckets, not time periods
    - Rolling calculation: Uses last n_buckets for VPIN computation
    - Trade classification: Supports multiple methods (tick rule, BVC, etc.)

    Example:
        >>> from strategies.common.orderflow import VPINConfig, VPINIndicator
        >>> config = VPINConfig(bucket_size=1000.0, n_buckets=50)
        >>> indicator = VPINIndicator(config)
        >>> for bar in bars:
        ...     indicator.handle_bar(bar)
        ...     if indicator.is_valid:
        ...         print(f"VPIN: {indicator.value:.3f}, Toxicity: {indicator.toxicity_level}")
    """

    def __init__(self, config: VPINConfig) -> None:
        """Initialize the VPIN indicator.

        Args:
            config: VPIN configuration with bucket_size, n_buckets, and
                   classification method settings
        """
        self._config = config
        self._buckets: list[VPINBucket] = []
        self._current_bucket: VPINBucket | None = None
        self._classifier = create_classifier(config.classification_method)
        self._last_price: float | None = None

    @property
    def value(self) -> float:
        """Calculate current VPIN value.

        VPIN = mean(order_imbalance) for last n_buckets

        Returns:
            VPIN value in range [0.0, 1.0]
            Returns 0.0 if insufficient buckets available
        """
        if len(self._buckets) < self._config.n_buckets:
            return 0.0

        # Get the last n_buckets
        recent_buckets = self._buckets[-self._config.n_buckets :]

        # Calculate mean order imbalance
        total_oi = sum(bucket.order_imbalance for bucket in recent_buckets)
        return total_oi / len(recent_buckets)

    @property
    def toxicity_level(self) -> ToxicityLevel:
        """Get the current toxicity level based on VPIN value.

        Returns:
            ToxicityLevel (LOW, MEDIUM, or HIGH)
        """
        return ToxicityLevel.from_vpin(self.value)

    @property
    def is_valid(self) -> bool:
        """Check if enough buckets have been accumulated for valid VPIN.

        Returns:
            True if len(buckets) >= n_buckets
        """
        return len(self._buckets) >= self._config.n_buckets

    def update(self, classification: TradeClassification) -> None:
        """Update VPIN with a new trade classification.

        This method:
        1. Creates a new bucket if needed
        2. Adds volume to current bucket based on classification side
        3. Finalizes bucket when volume target is reached
        4. Creates new bucket for overflow volume

        Args:
            classification: Classified trade with side and volume
        """
        # Skip unknown classifications (no volume contribution)
        if classification.side == TradeSide.UNKNOWN:
            return

        # Create initial bucket if needed
        if self._current_bucket is None:
            self._current_bucket = VPINBucket(
                volume_target=self._config.bucket_size,
                start_time=classification.timestamp_ns,
            )

        # Add volume to current bucket
        remaining_volume = classification.volume

        while remaining_volume > 0:
            # Calculate how much volume this bucket can still accept
            space_in_bucket = (
                self._current_bucket.volume_target
                - self._current_bucket.accumulated_volume
            )

            # Determine volume to add to current bucket
            volume_to_add = min(remaining_volume, space_in_bucket)

            # Update bucket volumes
            self._current_bucket.accumulated_volume += volume_to_add
            if classification.side == TradeSide.BUY:
                self._current_bucket.buy_volume += volume_to_add
            else:  # SELL
                self._current_bucket.sell_volume += volume_to_add

            remaining_volume -= volume_to_add

            # Check if bucket is complete
            if self._current_bucket.is_complete:
                # Finalize the bucket
                self._current_bucket.end_time = classification.timestamp_ns
                self._buckets.append(self._current_bucket)

                # Create new bucket if there's remaining volume
                if remaining_volume > 0:
                    self._current_bucket = VPINBucket(
                        volume_target=self._config.bucket_size,
                        start_time=classification.timestamp_ns,
                    )
                else:
                    self._current_bucket = None

    def handle_bar(self, bar: Bar) -> None:
        """Process a NautilusTrader Bar.

        Extracts price and volume from the bar, classifies the trade,
        and updates the VPIN indicator.

        Args:
            bar: NautilusTrader Bar object with OHLCV data
        """
        # Extract bar data
        price = float(bar.close)
        volume = float(bar.volume)
        timestamp_ns = bar.ts_event

        # Classify the trade using the configured method
        classification = self._classifier.classify(
            price=price,
            volume=volume,
            timestamp_ns=timestamp_ns,
            prev_price=self._last_price,
            open_price=float(bar.open),
            high=float(bar.high),
            low=float(bar.low),
        )

        # Update VPIN with the classification
        self.update(classification)

        # Store price for next tick rule classification
        self._last_price = price

    def reset(self) -> None:
        """Reset the indicator state.

        Clears all buckets, current bucket, classifier state, and last price.
        """
        self._buckets.clear()
        self._current_bucket = None
        self._classifier.reset()
        self._last_price = None

    def get_result(self) -> VPINResult:
        """Get the full VPIN result with metadata.

        Returns:
            VPINResult with value, toxicity, bucket count, last OI, and validity
        """
        # Get last bucket order imbalance
        if self._buckets:
            last_bucket_oi = self._buckets[-1].order_imbalance
        else:
            last_bucket_oi = 0.0

        return VPINResult(
            value=self.value,
            toxicity=self.toxicity_level,
            bucket_count=len(self._buckets),
            last_bucket_oi=last_bucket_oi,
            is_valid=self.is_valid,
        )
