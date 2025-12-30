"""Hyperliquid Strategy Configuration (Spec 021 - US4).

This module provides configuration classes for Hyperliquid trading strategies
with integrated risk management from Spec 011.

Example:
    >>> from strategies.hyperliquid.config import HyperliquidStrategyConfig
    >>> from risk import RiskConfig
    >>> from decimal import Decimal
    >>>
    >>> config = HyperliquidStrategyConfig(
    ...     instrument_id="BTC-USD-PERP.HYPERLIQUID",
    ...     order_size=Decimal("0.01"),
    ...     max_position_size=Decimal("0.1"),
    ...     risk=RiskConfig(stop_loss_pct=Decimal("0.02")),
    ... )
"""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field

from risk import RiskConfig


class HyperliquidStrategyConfig(BaseModel):
    """Configuration for Hyperliquid trading strategies.

    Integrates with Spec 011 RiskManager for automatic stop-loss
    and position limit enforcement.

    Attributes:
        instrument_id: Hyperliquid instrument to trade (e.g., "BTC-USD-PERP.HYPERLIQUID").
        order_size: Base order size in base currency units.
        max_position_size: Maximum position size allowed.
        risk: Risk management configuration from Spec 011.

    Example:
        >>> config = HyperliquidStrategyConfig(
        ...     instrument_id="BTC-USD-PERP.HYPERLIQUID",
        ...     order_size=Decimal("0.01"),
        ...     max_position_size=Decimal("0.1"),
        ... )
    """

    instrument_id: Annotated[str, Field(min_length=1)] = "BTC-USD-PERP.HYPERLIQUID"
    order_size: Annotated[Decimal, Field(gt=0)] = Decimal("0.001")
    max_position_size: Annotated[Decimal, Field(gt=0)] = Decimal("0.1")
    risk: RiskConfig = Field(default_factory=RiskConfig)

    model_config = {"frozen": False, "validate_assignment": True}

    def get_risk_config_with_limits(self) -> RiskConfig:
        """Get RiskConfig with max_position_size applied.

        Returns a RiskConfig with the max_position_size from this config
        merged into the risk configuration.

        Returns:
            RiskConfig with position limits set.
        """
        # Create a copy of the risk config with position limits merged
        risk_dict = self.risk.model_dump()
        existing_limits = self.risk.max_position_size or {}
        risk_dict["max_position_size"] = {
            **existing_limits,
            self.instrument_id: self.max_position_size,
        }
        return RiskConfig(**risk_dict)
