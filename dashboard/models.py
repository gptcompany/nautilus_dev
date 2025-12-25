"""
WebSocket message models for the Trading Dashboard.

These models define the JSON message format between server and browser clients.
Reuses entity patterns from Spec 001 CCXT Pipeline.
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Venue(str, Enum):
    """Supported exchange venues."""

    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
    HYPERLIQUID = "HYPERLIQUID"


class Side(str, Enum):
    """Liquidation side."""

    LONG = "LONG"
    SHORT = "SHORT"


# =============================================================================
# Server → Client Messages
# =============================================================================


class OIUpdate(BaseModel):
    """Open Interest update message."""

    type: Literal["oi"] = "oi"
    timestamp: int = Field(..., description="Unix milliseconds")
    symbol: str = Field(..., description="Trading pair (e.g., BTCUSDT-PERP)")
    venue: str = Field(..., description="Exchange name")
    open_interest: float = Field(..., ge=0, description="OI in base contracts")
    open_interest_value: float = Field(..., ge=0, description="OI value in USD")


class FundingUpdate(BaseModel):
    """Funding rate update message."""

    type: Literal["funding"] = "funding"
    timestamp: int = Field(..., description="Unix milliseconds")
    symbol: str
    venue: str
    funding_rate: float = Field(..., description="Rate as decimal (0.0001 = 0.01%)")
    next_funding_time: int | None = Field(
        None, description="Next funding timestamp (ms)"
    )
    predicted_rate: float | None = None


class LiquidationEvent(BaseModel):
    """Liquidation event message."""

    type: Literal["liquidation"] = "liquidation"
    timestamp: int = Field(..., description="Unix milliseconds")
    symbol: str
    venue: str
    side: Side
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    value: float = Field(..., gt=0, description="USD value")


class ConnectionStatus(BaseModel):
    """Connection status message sent on connect and status changes."""

    type: Literal["status"] = "status"
    connected: bool
    exchanges: list[str] = Field(default_factory=list)
    subscribed_symbols: list[str] = Field(default_factory=list)


class ErrorMessage(BaseModel):
    """Error message."""

    type: Literal["error"] = "error"
    code: str
    message: str


class PongMessage(BaseModel):
    """Pong response to client ping."""

    type: Literal["pong"] = "pong"
    timestamp: int


# =============================================================================
# Client → Server Messages
# =============================================================================


class SubscribeRequest(BaseModel):
    """Subscribe to symbols."""

    action: Literal["subscribe"] = "subscribe"
    symbols: list[str]


class UnsubscribeRequest(BaseModel):
    """Unsubscribe from symbols."""

    action: Literal["unsubscribe"] = "unsubscribe"
    symbols: list[str]


class PingRequest(BaseModel):
    """Client ping for keepalive."""

    action: Literal["ping"] = "ping"


# =============================================================================
# REST API Response Models
# =============================================================================


class SymbolInfo(BaseModel):
    """Symbol information for /api/symbols endpoint."""

    symbol: str
    name: str
    exchanges: list[str]


class SymbolsResponse(BaseModel):
    """Response for GET /api/symbols."""

    symbols: list[SymbolInfo]


class StatusResponse(BaseModel):
    """Response for GET /api/status."""

    status: Literal["healthy", "unhealthy"]
    daemon_running: bool
    uptime_seconds: float = 0
    last_fetch: str | None = None
    connected_exchanges: list[str] = Field(default_factory=list)
    fetch_count: int = 0
    error_count: int = 0
    liquidation_count: int = 0
    error: str | None = None


class HistoricalDataPoint(BaseModel):
    """Single data point in historical response."""

    timestamp: int
    venue: str
    open_interest: float | None = None
    open_interest_value: float | None = None
    funding_rate: float | None = None
    next_funding_time: int | None = None
    side: str | None = None
    quantity: float | None = None
    price: float | None = None
    value: float | None = None


class HistoricalResponse(BaseModel):
    """Response for GET /api/history/* endpoints."""

    symbol: str
    from_: str = Field(..., alias="from")
    to: str
    count: int
    data: list[HistoricalDataPoint]

    class Config:
        populate_by_name = True


class ErrorResponse(BaseModel):
    """Error response for REST API."""

    error: str
    message: str
