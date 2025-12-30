"""FundingRate data model."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from .open_interest import Venue


class FundingRate(BaseModel):
    """Funding Rate data point.

    Represents the periodic payment rate between longs and shorts on perpetual contracts.
    """

    timestamp: datetime = Field(description="When the funding was applied (UTC)")
    symbol: str = Field(description="Unified symbol")
    venue: Venue = Field(description="Exchange name")
    funding_rate: float = Field(description="Rate as decimal (e.g., 0.0001 = 0.01%)")
    next_funding_time: datetime | None = Field(default=None, description="Next funding timestamp")
    predicted_rate: float | None = Field(default=None, description="Predicted next rate")

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
