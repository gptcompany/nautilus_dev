"""OrderflowManager - Unified Interface for Orderflow Indicators (Spec 025).

This module provides a unified interface for managing VPIN and Hawkes OFI
indicators, simplifying strategy integration and enabling coordinated
orderflow analysis.

Tasks:
- T036: OrderflowManager.__init__
- T037: OrderflowManager.handle_bar, properties
- T038: OrderflowManager.reset, get_result
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from strategies.common.orderflow.config import OrderflowConfig
from strategies.common.orderflow.hawkes_ofi import HawkesOFI
from strategies.common.orderflow.vpin import ToxicityLevel, VPINIndicator

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar


@dataclass(frozen=True)
class OrderflowResult:
    """Combined result from all orderflow indicators.

    Attributes:
        vpin_value: VPIN value in range [0.0, 1.0]
        toxicity: Categorical toxicity level (LOW, MEDIUM, HIGH)
        ofi: Hawkes Order Flow Imbalance in range [-1.0, 1.0]
        is_valid: True if indicators have enough data for valid readings
        buy_intensity: Hawkes buy-side intensity (if enabled)
        sell_intensity: Hawkes sell-side intensity (if enabled)
    """

    vpin_value: float
    toxicity: ToxicityLevel
    ofi: float
    is_valid: bool
    buy_intensity: float = 0.0
    sell_intensity: float = 0.0


class OrderflowManager:
    """Unified interface for orderflow indicators.

    Combines VPIN and Hawkes OFI for comprehensive orderflow analysis.
    Provides a single point of integration for strategies that need
    to monitor market toxicity and order flow imbalance.

    Key features:
    - Selective enabling of indicators via config
    - Unified handle_bar() interface for both indicators
    - Easy access to toxicity and OFI values
    - Combined result with all indicator outputs

    Example:
        >>> from strategies.common.orderflow import OrderflowConfig, OrderflowManager
        >>> config = OrderflowConfig(enable_vpin=True, enable_hawkes=True)
        >>> manager = OrderflowManager(config)
        >>> for bar in bars:
        ...     manager.handle_bar(bar)
        ...     print(f"Toxicity: {manager.toxicity}, OFI: {manager.ofi}")
    """

    def __init__(self, config: OrderflowConfig) -> None:
        """Initialize with config.

        Creates VPIN and Hawkes indicators based on config settings.
        Indicators can be selectively enabled/disabled.

        Args:
            config: OrderflowConfig with VPIN and Hawkes settings
        """
        self._config = config

        # Create VPIN indicator if enabled
        if config.enable_vpin:
            self._vpin: VPINIndicator | None = VPINIndicator(config=config.vpin)
        else:
            self._vpin = None

        # Create Hawkes indicator if enabled
        if config.enable_hawkes:
            self._hawkes: HawkesOFI | None = HawkesOFI(config=config.hawkes)
        else:
            self._hawkes = None

    def handle_bar(self, bar: Bar) -> None:
        """Update both indicators with new bar data.

        Delegates bar handling to enabled indicators. Indicators
        will extract price, volume, and timestamp from the bar
        and update their internal state.

        Args:
            bar: NautilusTrader Bar object with OHLCV data
        """
        if self._vpin is not None:
            self._vpin.handle_bar(bar)

        if self._hawkes is not None:
            self._hawkes.handle_bar(bar)

    @property
    def toxicity(self) -> ToxicityLevel:
        """Get current VPIN toxicity level.

        Returns:
            ToxicityLevel (LOW, MEDIUM, or HIGH)
            Returns LOW if VPIN is disabled
        """
        if self._vpin is None:
            return ToxicityLevel.LOW
        return self._vpin.toxicity_level

    @property
    def vpin_value(self) -> float:
        """Get current VPIN value [0.0, 1.0].

        Returns:
            VPIN value as float in range [0.0, 1.0]
            Returns 0.0 if VPIN is disabled or not yet valid
        """
        if self._vpin is None:
            return 0.0
        return self._vpin.value

    @property
    def ofi(self) -> float:
        """Get current Hawkes OFI [-1.0, 1.0].

        Positive values indicate buy pressure, negative indicates sell pressure.

        Returns:
            OFI value as float in range [-1.0, 1.0]
            Returns 0.0 if Hawkes is disabled
        """
        if self._hawkes is None:
            return 0.0
        return self._hawkes.ofi

    @property
    def is_valid(self) -> bool:
        """True if indicators have enough data.

        Validity requires:
        - If VPIN enabled: Must have filled n_buckets
        - If Hawkes enabled: Must be fitted

        If both are disabled, returns False.

        Returns:
            True if enabled indicators have valid readings
        """
        # If both disabled, not valid
        if self._vpin is None and self._hawkes is None:
            return False

        # Check VPIN validity if enabled
        vpin_valid = True
        if self._vpin is not None:
            vpin_valid = self._vpin.is_valid

        # Check Hawkes validity if enabled
        hawkes_valid = True
        if self._hawkes is not None:
            hawkes_valid = self._hawkes.is_fitted

        # Valid if all enabled indicators are valid
        return vpin_valid and hawkes_valid

    def reset(self) -> None:
        """Reset all indicators.

        Clears internal state of both VPIN and Hawkes indicators.
        After reset, is_valid will return False until new data
        is processed.
        """
        if self._vpin is not None:
            self._vpin.reset()

        if self._hawkes is not None:
            self._hawkes.reset()

    def get_result(self) -> OrderflowResult:
        """Get combined result from all indicators.

        Returns:
            OrderflowResult with VPIN, toxicity, OFI, and validity status
        """
        # Get Hawkes intensities if available
        buy_intensity = 0.0
        sell_intensity = 0.0
        if self._hawkes is not None:
            buy_intensity = self._hawkes.buy_intensity
            sell_intensity = self._hawkes.sell_intensity

        return OrderflowResult(
            vpin_value=self.vpin_value,
            toxicity=self.toxicity,
            ofi=self.ofi,
            is_valid=self.is_valid,
            buy_intensity=buy_intensity,
            sell_intensity=sell_intensity,
        )
