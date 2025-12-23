"""Async orchestrator for concurrent multi-exchange fetching."""

import asyncio
from datetime import datetime
from typing import Callable

from scripts.ccxt_pipeline.fetchers.base import BaseFetcher
from scripts.ccxt_pipeline.models import FundingRate, Liquidation, OpenInterest
from scripts.ccxt_pipeline.utils.logging import get_logger

logger = get_logger("orchestrator")


class FetchResult:
    """Container for fetch operation results."""

    def __init__(
        self,
        venue: str,
        data: OpenInterest | FundingRate | list | None = None,
        error: Exception | None = None,
    ) -> None:
        self.venue = venue
        self.data = data
        self.error = error
        self.success = error is None


class FetchOrchestrator:
    """Orchestrates concurrent fetching from multiple exchanges.

    Uses asyncio.gather for parallel execution across all configured exchanges.
    """

    def __init__(self, fetchers: list[BaseFetcher]) -> None:
        """Initialize the orchestrator.

        Args:
            fetchers: List of exchange fetchers to use.
        """
        self.fetchers = {f.venue_name: f for f in fetchers}
        self._connected = False

    async def connect_all(self) -> None:
        """Connect to all exchanges concurrently."""
        if self._connected:
            return

        tasks = [f.connect() for f in self.fetchers.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        self._connected = True
        logger.info(f"Connected to {len(self.fetchers)} exchanges")

    async def close_all(self) -> None:
        """Close all exchange connections."""
        tasks = [f.close() for f in self.fetchers.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        self._connected = False
        logger.info("Closed all exchange connections")

    async def fetch_open_interest(
        self, symbol: str, exchanges: list[str] | None = None
    ) -> list[FetchResult]:
        """Fetch current open interest from all exchanges concurrently.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT-PERP').
            exchanges: Optional list of exchanges to fetch from.

        Returns:
            List of FetchResult objects with data or errors.
        """
        await self.connect_all()

        target_fetchers = self._get_target_fetchers(exchanges)

        async def _fetch(venue: str, fetcher: BaseFetcher) -> FetchResult:
            try:
                data = await fetcher.fetch_open_interest(symbol)
                return FetchResult(venue=venue, data=data)
            except Exception as e:
                logger.error(f"Error fetching OI from {venue}: {e}")
                return FetchResult(venue=venue, error=e)

        tasks = [_fetch(venue, f) for venue, f in target_fetchers.items()]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def fetch_open_interest_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        exchanges: list[str] | None = None,
    ) -> list[FetchResult]:
        """Fetch historical open interest from all exchanges concurrently.

        Args:
            symbol: Trading pair symbol.
            start: Start datetime (UTC).
            end: End datetime (UTC).
            exchanges: Optional list of exchanges.

        Returns:
            List of FetchResult objects.
        """
        await self.connect_all()

        target_fetchers = self._get_target_fetchers(exchanges)

        async def _fetch(venue: str, fetcher: BaseFetcher) -> FetchResult:
            try:
                data = await fetcher.fetch_open_interest_history(symbol, start, end)
                return FetchResult(venue=venue, data=data)
            except Exception as e:
                logger.error(f"Error fetching OI history from {venue}: {e}")
                return FetchResult(venue=venue, error=e)

        tasks = [_fetch(venue, f) for venue, f in target_fetchers.items()]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def fetch_funding_rate(
        self, symbol: str, exchanges: list[str] | None = None
    ) -> list[FetchResult]:
        """Fetch current funding rate from all exchanges concurrently.

        Args:
            symbol: Trading pair symbol.
            exchanges: Optional list of exchanges.

        Returns:
            List of FetchResult objects.
        """
        await self.connect_all()

        target_fetchers = self._get_target_fetchers(exchanges)

        async def _fetch(venue: str, fetcher: BaseFetcher) -> FetchResult:
            try:
                data = await fetcher.fetch_funding_rate(symbol)
                return FetchResult(venue=venue, data=data)
            except Exception as e:
                logger.error(f"Error fetching funding from {venue}: {e}")
                return FetchResult(venue=venue, error=e)

        tasks = [_fetch(venue, f) for venue, f in target_fetchers.items()]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def fetch_funding_rate_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        exchanges: list[str] | None = None,
    ) -> list[FetchResult]:
        """Fetch historical funding rates from all exchanges concurrently.

        Args:
            symbol: Trading pair symbol.
            start: Start datetime (UTC).
            end: End datetime (UTC).
            exchanges: Optional list of exchanges.

        Returns:
            List of FetchResult objects.
        """
        await self.connect_all()

        target_fetchers = self._get_target_fetchers(exchanges)

        async def _fetch(venue: str, fetcher: BaseFetcher) -> FetchResult:
            try:
                data = await fetcher.fetch_funding_rate_history(symbol, start, end)
                return FetchResult(venue=venue, data=data)
            except Exception as e:
                logger.error(f"Error fetching funding history from {venue}: {e}")
                return FetchResult(venue=venue, error=e)

        tasks = [_fetch(venue, f) for venue, f in target_fetchers.items()]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def stream_liquidations(
        self,
        symbol: str,
        callback: Callable[[Liquidation], None],
        exchanges: list[str] | None = None,
    ) -> None:
        """Stream liquidations from all exchanges concurrently.

        Runs all fetcher streams concurrently using asyncio.gather.
        Each fetcher handles its own reconnection logic.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT-PERP').
            callback: Function to call with each liquidation event.
            exchanges: Optional list of exchanges to stream from.
        """
        await self.connect_all()

        target_fetchers = self._get_target_fetchers(exchanges)

        async def _stream(venue: str, fetcher: BaseFetcher) -> None:
            try:
                logger.info(f"Starting liquidation stream from {venue}")
                await fetcher.stream_liquidations(symbol, callback)
            except asyncio.CancelledError:
                logger.info(f"Liquidation stream from {venue} cancelled")
                raise
            except Exception as e:
                logger.error(f"Error streaming liquidations from {venue}: {e}")

        # Run all streams concurrently
        tasks = [_stream(venue, f) for venue, f in target_fetchers.items()]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _get_target_fetchers(self, exchanges: list[str] | None) -> dict[str, BaseFetcher]:
        """Get fetchers for specified exchanges or all if not specified."""
        if not exchanges:
            return self.fetchers

        return {
            venue: f
            for venue, f in self.fetchers.items()
            if venue.upper() in [e.upper() for e in exchanges]
        }
