"""Binance exchange fetcher implementation.

This module provides the BinanceFetcher class for fetching Open Interest,
Funding Rates, and Liquidations from Binance Futures using CCXT.
"""

from datetime import datetime, timezone
from typing import Callable

import ccxt.async_support as ccxt

from scripts.ccxt_pipeline.fetchers.base import BaseFetcher
from scripts.ccxt_pipeline.models import (
    FundingRate,
    Liquidation,
    OpenInterest,
    Side,
    Venue,
)
from scripts.ccxt_pipeline.utils.logging import get_logger
from scripts.ccxt_pipeline.utils.parsing import safe_float
from scripts.ccxt_pipeline.utils.reconnect import ReconnectingStream

logger = get_logger("binance_fetcher")


class BinanceFetcher(BaseFetcher):
    """Binance Futures data fetcher using CCXT.

    Fetches Open Interest, Funding Rates, and Liquidations from Binance
    USDT-Margined Futures markets.

    Attributes:
        venue_name: Returns "BINANCE".
        ccxt_id: Returns "binance".
    """

    # Binance API pagination limits
    OI_HISTORY_LIMIT = 500
    FUNDING_HISTORY_LIMIT = 1000

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        sandbox: bool = False,
    ) -> None:
        """Initialize the Binance fetcher.

        Args:
            api_key: Optional Binance API key.
            api_secret: Optional Binance API secret.
            sandbox: Use testnet if True.
        """
        self._api_key = api_key
        self._api_secret = api_secret
        self._sandbox = sandbox
        self._exchange: ccxt.binance | None = None
        self._connected = False

    @property
    def venue_name(self) -> str:
        """Return the venue name."""
        return "BINANCE"

    @property
    def ccxt_id(self) -> str:
        """Return the CCXT exchange ID."""
        return "binance"

    def _ensure_connected(self) -> ccxt.binance:
        """Ensure exchange is connected and return it.

        Returns:
            The connected CCXT exchange instance.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._connected or self._exchange is None:
            raise RuntimeError(f"{self.venue_name} not connected. Call connect() first.")
        return self._exchange

    async def connect(self) -> None:
        """Initialize the exchange connection.

        Loads markets and prepares the exchange for API calls.
        """
        if self._connected and self._exchange is not None:
            return

        config: dict = {
            "enableRateLimit": True,
            "options": {"defaultType": "swap"},
        }
        if self._api_key:
            config["apiKey"] = self._api_key
        if self._api_secret:
            config["secret"] = self._api_secret
        if self._sandbox:
            config["sandbox"] = True

        self._exchange = ccxt.binance(config)
        await self._exchange.load_markets()
        self._connected = True
        logger.info(f"Connected to {self.venue_name}")

    async def close(self) -> None:
        """Close the exchange connection."""
        if self._exchange is not None:
            await self._exchange.close()
            self._exchange = None
        self._connected = False
        logger.debug(f"Disconnected from {self.venue_name}")

    def _parse_timestamp(self, ts_ms: int | None) -> datetime:
        """Parse millisecond timestamp to UTC datetime.

        Args:
            ts_ms: Timestamp in milliseconds, or None for current time.

        Returns:
            UTC datetime object.
        """
        if ts_ms is None:
            return datetime.now(timezone.utc)
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

    def _parse_open_interest(self, original_symbol: str, data: dict) -> OpenInterest:
        """Parse CCXT response into OpenInterest model.

        Args:
            original_symbol: The original symbol passed by the caller.
            data: CCXT response dictionary.

        Returns:
            OpenInterest model instance.
        """
        return OpenInterest(
            timestamp=self._parse_timestamp(data.get("timestamp")),
            symbol=original_symbol.upper(),
            venue=Venue.BINANCE,
            open_interest=safe_float(data.get("openInterestAmount")),
            open_interest_value=safe_float(data.get("openInterestValue")),
        )

    def _parse_funding_rate(self, original_symbol: str, data: dict) -> FundingRate:
        """Parse CCXT response into FundingRate model.

        Args:
            original_symbol: The original symbol passed by the caller.
            data: CCXT response dictionary.

        Returns:
            FundingRate model instance.
        """
        next_ts = data.get("fundingTimestamp")
        return FundingRate(
            timestamp=self._parse_timestamp(data.get("timestamp")),
            symbol=original_symbol.upper(),
            venue=Venue.BINANCE,
            funding_rate=safe_float(data.get("fundingRate")),
            next_funding_time=self._parse_timestamp(next_ts) if next_ts else None,
            predicted_rate=data.get("predictedFundingRate"),
        )

    def _parse_liquidation(self, original_symbol: str, data: dict) -> Liquidation | None:
        """Parse CCXT liquidation data into Liquidation model.

        Uses safe_float for None-safe parsing (BUG-001 fix).
        Side mapping: CCXT "sell" = LONG position liquidated,
                      CCXT "buy" = SHORT position liquidated.

        Args:
            original_symbol: The original symbol passed by the caller.
            data: CCXT liquidation event dictionary.

        Returns:
            Liquidation model instance, or None if data is invalid.
        """
        # Extract and validate required fields
        quantity = safe_float(data.get("amount"))
        price = safe_float(data.get("price"))

        # Skip invalid liquidations (Liquidation model has gt=0 constraints)
        if quantity <= 0 or price <= 0:
            logger.warning(f"Skipping invalid liquidation data: {data}")
            return None

        # Calculate value (quantity * price)
        value = quantity * price

        # Map CCXT side to our Side enum
        # CCXT "sell" side means a LONG position was liquidated (forced sell)
        # CCXT "buy" side means a SHORT position was liquidated (forced buy)
        ccxt_side = data.get("side", "").lower()
        if ccxt_side == "sell":
            side = Side.LONG
        elif ccxt_side == "buy":
            side = Side.SHORT
        else:
            logger.warning(f"Unknown liquidation side '{ccxt_side}', defaulting to LONG")
            side = Side.LONG

        try:
            return Liquidation(
                timestamp=self._parse_timestamp(data.get("timestamp")),
                symbol=original_symbol.upper(),
                venue=Venue.BINANCE,
                side=side,
                quantity=quantity,
                price=price,
                value=value,
            )
        except Exception as e:
            logger.warning(f"Failed to parse liquidation: {e}, data: {data}")
            return None

    async def fetch_open_interest(self, symbol: str) -> OpenInterest:
        """Fetch current open interest for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT-PERP').

        Returns:
            OpenInterest data point.

        Raises:
            RuntimeError: If not connected.
        """
        exchange = self._ensure_connected()
        ccxt_symbol = self.normalize_symbol(symbol)

        response = await exchange.fetch_open_interest(ccxt_symbol)

        return self._parse_open_interest(symbol, response)

    async def fetch_open_interest_history(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[OpenInterest]:
        """Fetch historical open interest for a date range.

        Uses pagination to fetch all data within the range. Binance returns
        data in 5-minute intervals.

        Args:
            symbol: Trading pair symbol.
            start: Start datetime (UTC).
            end: End datetime (UTC).

        Returns:
            List of OpenInterest data points.

        Raises:
            RuntimeError: If not connected.
        """
        exchange = self._ensure_connected()
        ccxt_symbol = self.normalize_symbol(symbol)

        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)

        results: list[OpenInterest] = []
        since = start_ms

        while since < end_ms:
            logger.debug(f"Fetching OI history since {since}")
            response = await exchange.fetch_open_interest_history(
                ccxt_symbol, since=since, limit=self.OI_HISTORY_LIMIT
            )

            if not response:
                break

            for record in response:
                record_ts = record.get("timestamp", 0)
                if record_ts > end_ms:
                    logger.info(f"Fetched {len(results)} OI history records for {symbol}")
                    return results

                results.append(self._parse_open_interest(symbol, record))

            # Move to next page
            last_ts = response[-1].get("timestamp", since)
            if last_ts <= since:
                # Avoid infinite loop if API returns same timestamp
                break
            since = last_ts + 1

        logger.info(f"Fetched {len(results)} OI history records for {symbol}")
        return results

    async def fetch_funding_rate(self, symbol: str) -> FundingRate:
        """Fetch current funding rate for a symbol.

        Args:
            symbol: Trading pair symbol.

        Returns:
            FundingRate data point.

        Raises:
            RuntimeError: If not connected.
        """
        exchange = self._ensure_connected()
        ccxt_symbol = self.normalize_symbol(symbol)

        response = await exchange.fetch_funding_rate(ccxt_symbol)

        return self._parse_funding_rate(symbol, response)

    async def fetch_funding_rate_history(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[FundingRate]:
        """Fetch historical funding rates for a date range.

        Uses pagination to fetch all data within the range. Funding rates
        are recorded every 8 hours on Binance.

        Args:
            symbol: Trading pair symbol.
            start: Start datetime (UTC).
            end: End datetime (UTC).

        Returns:
            List of FundingRate data points.

        Raises:
            RuntimeError: If not connected.
        """
        exchange = self._ensure_connected()
        ccxt_symbol = self.normalize_symbol(symbol)

        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)

        results: list[FundingRate] = []
        since = start_ms

        while since < end_ms:
            logger.debug(f"Fetching funding history since {since}")
            response = await exchange.fetch_funding_rate_history(
                ccxt_symbol, since=since, limit=self.FUNDING_HISTORY_LIMIT
            )

            if not response:
                break

            for record in response:
                record_ts = record.get("timestamp", 0)
                if record_ts > end_ms:
                    logger.info(f"Fetched {len(results)} funding history records for {symbol}")
                    return results

                results.append(self._parse_funding_rate(symbol, record))

            # Move to next page
            last_ts = response[-1].get("timestamp", since)
            if last_ts <= since:
                break
            since = last_ts + 1

        logger.info(f"Fetched {len(results)} funding history records for {symbol}")
        return results

    async def stream_liquidations(
        self, symbol: str, callback: Callable[[Liquidation], None]
    ) -> None:
        """Stream real-time liquidation events via WebSocket.

        Uses CCXT Pro watch_liquidations with automatic reconnection
        and exponential backoff on connection errors.

        Alpha-Evolve Selection: Approach B (ReconnectingStream Wrapper)
        - Reuses existing ReconnectingStream infrastructure
        - Consistent backoff behavior across codebase
        - Better separation of concerns

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT-PERP').
            callback: Function to call with each liquidation event.

        Raises:
            RuntimeError: If not connected.
            ConnectionError: If max retries exceeded.
            asyncio.CancelledError: If stream is cancelled.
        """
        exchange = self._ensure_connected()
        ccxt_symbol = self.normalize_symbol(symbol)

        stream = ReconnectingStream()

        async def watch_fn() -> list[dict]:
            """Coroutine to watch liquidations from WebSocket."""
            return await exchange.watch_liquidations(ccxt_symbol)

        def process_fn(liquidations: list[dict]) -> None:
            """Process received liquidation events."""
            for liq_data in liquidations:
                liq = self._parse_liquidation(symbol, liq_data)
                if liq is not None:
                    callback(liq)

        logger.info(f"Starting liquidation stream for {symbol}")
        await stream.run(watch_fn, process_fn, symbol)
