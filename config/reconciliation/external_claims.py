"""
External Order Claims Configuration.

This module provides configuration for claiming external orders placed
outside NautilusTrader (e.g., via exchange web interface or mobile app).
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator, model_validator

# NautilusTrader instrument ID pattern: SYMBOL[-EXPIRY].VENUE
# Examples: BTCUSDT-PERP.BINANCE, ETHUSDT.BINANCE, ES-Z24.CME
INSTRUMENT_ID_PATTERN = re.compile(r"^[A-Z0-9_-]+\.[A-Z]+$")


class ExternalOrderClaimConfig(BaseModel):
    """
    Configuration for claiming external orders.

    External orders are orders placed outside NautilusTrader (e.g., via
    exchange web interface or mobile app). This configuration specifies
    which instruments should have their external orders claimed.

    Example:
        >>> config = ExternalOrderClaimConfig(
        ...     instrument_ids=["BTCUSDT-PERP.BINANCE", "ETHUSDT-PERP.BINANCE"],
        ... )
        >>> # Or claim all instruments:
        >>> config = ExternalOrderClaimConfig(claim_all=True)
    """

    instrument_ids: list[str] = Field(
        default_factory=list,
        description="Specific instrument IDs to claim external orders for",
    )
    claim_all: bool = Field(
        default=False,
        description="Claim all external orders regardless of instrument",
    )

    model_config = {"frozen": True}

    @field_validator("instrument_ids", mode="after")
    @classmethod
    def validate_instrument_ids(cls, v: list[str]) -> list[str]:
        """Validate instrument ID format."""
        for instrument_id in v:
            if not INSTRUMENT_ID_PATTERN.match(instrument_id):
                msg = (
                    f"Invalid instrument ID format: '{instrument_id}'. "
                    f"Expected format: 'SYMBOL[-EXPIRY].VENUE' "
                    f"(e.g., 'BTCUSDT-PERP.BINANCE')"
                )
                raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_mutual_exclusion(self) -> ExternalOrderClaimConfig:
        """Ensure claim_all and instrument_ids are mutually exclusive."""
        if self.claim_all and len(self.instrument_ids) > 0:
            msg = (
                "Cannot specify both 'claim_all=True' and 'instrument_ids'. "
                "Use either claim_all for all instruments, or provide specific IDs."
            )
            raise ValueError(msg)
        return self

    def get_external_order_claims(self) -> list[str] | None:
        """
        Get external order claims for strategy configuration.

        Returns:
            List of instrument IDs to claim, or None if claim_all is True.
            None indicates "claim all instruments" semantically.

        Example:
            >>> config = ExternalOrderClaimConfig(
            ...     instrument_ids=["BTCUSDT-PERP.BINANCE"],
            ... )
            >>> strategy_config.external_order_claims = config.get_external_order_claims()
        """
        if self.claim_all:
            return None
        return self.instrument_ids
