"""
Example Strategy Configuration with External Order Claims.

This module demonstrates how to configure a strategy to claim external orders
placed outside NautilusTrader (e.g., via exchange web interface or mobile app).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from config.reconciliation.external_claims import ExternalOrderClaimConfig


class ExampleStrategyWithClaimsConfig(BaseModel):
    """
    Example strategy configuration with external order claims.

    This demonstrates the pattern for integrating external order claims
    with NautilusTrader strategy configuration.

    Example:
        >>> config = ExampleStrategyWithClaimsConfig(
        ...     strategy_id="MOMENTUM-001",
        ...     instrument_ids=["BTCUSDT-PERP.BINANCE"],
        ... )
        >>> # Use with NautilusTrader strategy:
        >>> claims = config.external_claims.get_external_order_claims()
    """

    # Strategy identification
    strategy_id: str = Field(
        description="Unique strategy identifier",
    )

    # Trading instruments
    instrument_ids: list[str] = Field(
        default_factory=list,
        description="Instruments this strategy trades",
    )

    # External order claims configuration
    external_claims: ExternalOrderClaimConfig = Field(
        default_factory=ExternalOrderClaimConfig,
        description="Configuration for claiming external orders",
    )

    # Strategy parameters (example)
    risk_per_trade: float = Field(
        default=0.01,
        ge=0.001,
        le=0.10,
        description="Risk per trade as fraction of equity",
    )

    model_config = {"frozen": True}

    @classmethod
    def with_claim_all(
        cls,
        strategy_id: str,
        instrument_ids: list[str],
        **kwargs,
    ) -> ExampleStrategyWithClaimsConfig:
        """
        Create config that claims all external orders.

        Args:
            strategy_id: Unique strategy identifier.
            instrument_ids: Instruments this strategy trades.
            **kwargs: Additional strategy parameters.

        Returns:
            Strategy configuration with claim_all enabled.
        """
        return cls(
            strategy_id=strategy_id,
            instrument_ids=instrument_ids,
            external_claims=ExternalOrderClaimConfig(claim_all=True),
            **kwargs,
        )

    @classmethod
    def with_specific_claims(
        cls,
        strategy_id: str,
        instrument_ids: list[str],
        claim_instruments: list[str] | None = None,
        **kwargs,
    ) -> ExampleStrategyWithClaimsConfig:
        """
        Create config that claims specific instruments.

        Args:
            strategy_id: Unique strategy identifier.
            instrument_ids: Instruments this strategy trades.
            claim_instruments: Instruments to claim external orders for.
                              If None, uses instrument_ids.
            **kwargs: Additional strategy parameters.

        Returns:
            Strategy configuration with specific claims.
        """
        claims = claim_instruments if claim_instruments is not None else instrument_ids
        return cls(
            strategy_id=strategy_id,
            instrument_ids=instrument_ids,
            external_claims=ExternalOrderClaimConfig(instrument_ids=claims),
            **kwargs,
        )
