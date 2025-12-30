"""OpenInterest data model."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Venue(str, Enum):
    """Supported trading venues."""

    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
    HYPERLIQUID = "HYPERLIQUID"


class OpenInterest(BaseModel):
    """Open Interest data point.

    Represents the total number of outstanding derivative contracts at a point in time.
    """

    timestamp: datetime = Field(description="When the data was recorded (UTC)")
    symbol: str = Field(description="Unified symbol (e.g., BTCUSDT-PERP)")
    venue: Venue = Field(description="Exchange name")
    open_interest: float = Field(ge=0, description="OI in base currency contracts")
    open_interest_value: float = Field(ge=0, description="OI value in USD")

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
        # Make v timezone-aware if it isn't
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v > now:
            raise ValueError("Timestamp cannot be in the future")
        return v

    model_config = {"frozen": True}
