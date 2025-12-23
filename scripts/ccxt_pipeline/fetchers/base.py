"""Base fetcher abstract class."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable

from scripts.ccxt_pipeline.models import FundingRate, Liquidation, OpenInterest


class BaseFetcher(ABC):
    """Abstract base class for exchange data fetchers.

    Each exchange implementation must inherit from this class
    and implement all abstract methods.
    """

    @property
    @abstractmethod
    def venue_name(self) -> str:
        """Return the venue name (e.g., 'BINANCE')."""
        ...

    @property
    @abstractmethod
    def ccxt_id(self) -> str:
        """Return the CCXT exchange ID (e.g., 'binance')."""
        ...

    @abstractmethod
    async def connect(self) -> None:
        """Initialize the exchange connection."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the exchange connection."""
        ...

    @abstractmethod
    async def fetch_open_interest(self, symbol: str) -> OpenInterest:
        """Fetch current open interest for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT-PERP')

        Returns:
            OpenInterest data point.
        """
        ...

    @abstractmethod
    async def fetch_open_interest_history(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[OpenInterest]:
        """Fetch historical open interest for a date range.

        Args:
            symbol: Trading pair symbol
            start: Start datetime (UTC)
            end: End datetime (UTC)

        Returns:
            List of OpenInterest data points.
        """
        ...

    @abstractmethod
    async def fetch_funding_rate(self, symbol: str) -> FundingRate:
        """Fetch current funding rate for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            FundingRate data point.
        """
        ...

    @abstractmethod
    async def fetch_funding_rate_history(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[FundingRate]:
        """Fetch historical funding rates for a date range.

        Args:
            symbol: Trading pair symbol
            start: Start datetime (UTC)
            end: End datetime (UTC)

        Returns:
            List of FundingRate data points.
        """
        ...

    @abstractmethod
    async def stream_liquidations(
        self, symbol: str, callback: Callable[[Liquidation], None]
    ) -> None:
        """Stream real-time liquidation events.

        Args:
            symbol: Trading pair symbol
            callback: Function to call with each liquidation event
        """
        ...

    def normalize_symbol(self, symbol: str) -> str:
        """Normalize a symbol to CCXT format.

        Override in subclass if exchange needs specific normalization.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT-PERP')

        Returns:
            CCXT-compatible symbol (e.g., 'BTC/USDT:USDT')
        """
        symbol = symbol.upper().replace("-PERP", "")
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            return f"{base}/USDT:USDT"
        elif symbol.endswith("USD"):
            base = symbol[:-3]
            return f"{base}/USD:USD"
        return symbol
