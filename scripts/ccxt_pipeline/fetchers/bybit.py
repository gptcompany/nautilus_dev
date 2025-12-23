"""Bybit exchange fetcher implementation.

This module provides the BybitFetcher class for fetching Open Interest,
Funding Rates, and Liquidations from Bybit Linear Perpetuals using CCXT.
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

logger = get_logger("bybit_fetcher")


class BybitFetcher(BaseFetcher):
    """Bybit Linear Perpetuals data fetcher using CCXT.

    Fetches Open Interest, Funding Rates, and Liquidations from Bybit
    Linear Perpetuals markets.

    Note: Bybit OI history has a 200-record limit per request. Uses chunked
    fetching to work around this limitation.

    Attributes:
        venue_name: Returns "BYBIT".
        ccxt_id: Returns "bybit".
    """

    # Bybit API pagination limits
    OI_HISTORY_LIMIT = 200  # Bybit has lower limit than Binance
    FUNDING_HISTORY_LIMIT = 200

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        sandbox: bool = False,
    ) -> None:
        """Initialize the Bybit fetcher.

        Args:
            api_key: Optional Bybit API key.
            api_secret: Optional Bybit API secret.
            sandbox: Use testnet if True.
        """
        self._api_key = api_key
        self._api_secret = api_secret
        self._sandbox = sandbox
        self._exchange: ccxt.bybit | None = None
        self._connected = False

    @property
    def venue_name(self) -> str:
        """Return the venue name."""
        return "BYBIT"

    @property
    def ccxt_id(self) -> str:
        """Return the CCXT exchange ID."""
        return "bybit"

    def _ensure_connected(self) -> ccxt.bybit:
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

        self._exchange = ccxt.bybit(config)
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
            venue=Venue.BYBIT,
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
            venue=Venue.BYBIT,
            funding_rate=safe_float(data.get("fundingRate")),
            next_funding_time=self._parse_timestamp(next_ts) if next_ts else None,
            predicted_rate=data.get("predictedFundingRate"),
        )

    def _parse_liquidation(self, original_symbol: str, data: dict) -> Liquidation:
        """Parse CCXT liquidation data into Liquidation model.

        Args:
            original_symbol: The original symbol passed by the caller.
            data: CCXT liquidation response dictionary.

        Returns:
            Liquidation model instance.

        Raises:
            ValueError: If price or quantity is invalid (<=0).

        Note:
            CCXT side mapping for liquidations:
            - "sell" = The position was forced to sell = LONG position liquidated
            - "buy" = The position was forced to buy = SHORT position liquidated
        """
        timestamp = self._parse_timestamp(data.get("timestamp"))

        # CCXT side -> Position side that was liquidated
        # "sell" = The position was forced to sell = LONG position liquidated
        # "buy" = The position was forced to buy = SHORT position liquidated
        ccxt_side = data.get("side", "").lower()
        if ccxt_side == "sell":
            side = Side.LONG
        elif ccxt_side == "buy":
            side = Side.SHORT
        else:
            logger.warning(f"Unknown liquidation side '{ccxt_side}', defaulting to LONG")
            side = Side.LONG

        # Use safe_float for None-safe parsing (BUG-001 fix)
        price = safe_float(data.get("price"), default=0.0)
        quantity = safe_float(data.get("amount"), default=0.0)

        # Validate required fields (Liquidation model has gt=0 constraints)
        if price <= 0 or quantity <= 0:
            raise ValueError(f"Invalid price ({price}) or quantity ({quantity})")

        value = price * quantity

        return Liquidation(
            timestamp=timestamp,
            symbol=original_symbol.upper(),
            venue=Venue.BYBIT,
            side=side,
            quantity=quantity,
            price=price,
            value=value,
        )

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

        Uses chunked pagination to work around Bybit's 200-record limit.

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
            logger.debug(f"Fetching OI history since {since} (Bybit chunk)")
            try:
                response = await exchange.fetch_open_interest_history(
                    ccxt_symbol, since=since, limit=self.OI_HISTORY_LIMIT
                )
            except Exception as e:
                logger.warning(f"Bybit OI history fetch error: {e}")
                break

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
            try:
                response = await exchange.fetch_funding_rate_history(
                    ccxt_symbol, since=since, limit=self.FUNDING_HISTORY_LIMIT
                )
            except Exception as e:
                logger.warning(f"Bybit funding history fetch error: {e}")
                break

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
        via ReconnectingStream. The stream will automatically retry
        with exponential backoff on connection errors.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT-PERP').
            callback: Function to call with each Liquidation event.

        Raises:
            RuntimeError: If not connected.
            ConnectionError: If max retries exceeded.
            asyncio.CancelledError: If stream is cancelled (graceful shutdown).

        Example:
            ```python
            async def on_liquidation(liq: Liquidation) -> None:
                print(f"{liq.timestamp} {liq.side} liquidated: {liq.quantity} @ {liq.price}")

            await fetcher.stream_liquidations("BTCUSDT-PERP", on_liquidation)
            ```

        Note:
            Output format matches CLI spec:
            [timestamp] EXCHANGE SYMBOL SIDE liquidated: QTY @ PRICE ($VALUE)
        """
        exchange = self._ensure_connected()
        ccxt_symbol = self.normalize_symbol(symbol)

        stream = ReconnectingStream()

        async def watch_func() -> list[dict]:
            """Watch for liquidation events via WebSocket."""
            return await exchange.watch_liquidations(ccxt_symbol)

        def process_func(liquidations: list[dict]) -> None:
            """Process batch of liquidation events."""
            for liq_data in liquidations:
                try:
                    liquidation = self._parse_liquidation(symbol, liq_data)
                    callback(liquidation)
                except Exception as e:
                    logger.warning(f"Failed to parse liquidation for {symbol}: {e}")

        logger.info(f"Starting liquidation stream for {symbol}")
        await stream.run(watch_func, process_func, symbol)
