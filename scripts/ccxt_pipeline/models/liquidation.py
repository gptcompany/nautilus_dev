"""Liquidation data model."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from .open_interest import Venue


class Side(str, Enum):
    """Position side for liquidation."""

    LONG = "LONG"
    SHORT = "SHORT"


class Liquidation(BaseModel):
    """Liquidation event data.

    Represents a forced position closure event.
    """

    timestamp: datetime = Field(description="When liquidation occurred (UTC)")
    symbol: str = Field(description="Unified symbol")
    venue: Venue = Field(description="Exchange name")
    side: Side = Field(description="Position side liquidated")
    quantity: float = Field(gt=0, description="Size of liquidated position")
    price: float = Field(gt=0, description="Liquidation price")
    value: float = Field(gt=0, description="USD value of liquidation")

    @field_validator("symbol")
    @classmethod
    def symbol_not_empty(cls, v: str) -> str:
        """Validate symbol is not empty."""
        if not v or not v.strip():
            raise ValueError("Symbol cannot be empty")
        return v.strip().upper()

    @field_validator("timestamp")
    @classmethod
    def timestamp_not_future(cls, v: datetime) -> datetime:
        """Validate timestamp is not in the future."""
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v > now:
            raise ValueError("Timestamp cannot be in the future")
        return v

    model_config = {"frozen": True}
