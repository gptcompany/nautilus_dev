"""Hyperliquid exchange fetcher implementation.

This module provides the HyperliquidFetcher class for fetching Open Interest,
Funding Rates, and Liquidations from Hyperliquid Perpetuals using CCXT.
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

logger = get_logger("hyperliquid_fetcher")


class HyperliquidFetcher(BaseFetcher):
    """Hyperliquid Perpetuals data fetcher using CCXT.

    Fetches Open Interest, Funding Rates, and Liquidations from Hyperliquid
    Perpetual markets.

    Note: Hyperliquid uses USD-margined contracts with different symbol format
    (e.g., BTC-USD-PERP instead of BTCUSDT-PERP).

    Attributes:
        venue_name: Returns "HYPERLIQUID".
        ccxt_id: Returns "hyperliquid".
    """

    # Hyperliquid API pagination limits
    OI_HISTORY_LIMIT = 500
    FUNDING_HISTORY_LIMIT = 500

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
    ) -> None:
        """Initialize the Hyperliquid fetcher.

        Args:
            api_key: Optional Hyperliquid API key.
            api_secret: Optional Hyperliquid API secret.
        """
        self._api_key = api_key
        self._api_secret = api_secret
        self._exchange: ccxt.hyperliquid | None = None
        self._connected = False

    @property
    def venue_name(self) -> str:
        """Return the venue name."""
        return "HYPERLIQUID"

    @property
    def ccxt_id(self) -> str:
        """Return the CCXT exchange ID."""
        return "hyperliquid"

    def normalize_symbol(self, symbol: str) -> str:
        """Normalize a symbol to CCXT format for Hyperliquid.

        Hyperliquid uses USD instead of USDT for perpetuals.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USD-PERP' or 'BTCUSD-PERP')

        Returns:
            CCXT-compatible symbol (e.g., 'BTC/USD:USD')
        """
        symbol = symbol.upper().replace("-PERP", "")
        # Handle BTC-USD format
        if "-USD" in symbol:
            base = symbol.split("-")[0]
            return f"{base}/USD:USD"
        # Handle BTCUSD format
        if symbol.endswith("USD"):
            base = symbol[:-3]
            return f"{base}/USD:USD"
        # Handle BTCUSDT format (convert to USD for Hyperliquid)
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            return f"{base}/USD:USD"
        return symbol

    def _ensure_connected(self) -> ccxt.hyperliquid:
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
        }
        if self._api_key:
            config["apiKey"] = self._api_key
        if self._api_secret:
            config["secret"] = self._api_secret

        self._exchange = ccxt.hyperliquid(config)
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
            venue=Venue.HYPERLIQUID,
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
            venue=Venue.HYPERLIQUID,
            funding_rate=safe_float(data.get("fundingRate")),
            next_funding_time=self._parse_timestamp(next_ts) if next_ts else None,
            predicted_rate=data.get("predictedFundingRate"),
        )

    async def fetch_open_interest(self, symbol: str) -> OpenInterest:
        """Fetch current open interest for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USD-PERP').

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
            try:
                response = await exchange.fetch_open_interest_history(
                    ccxt_symbol, since=since, limit=self.OI_HISTORY_LIMIT
                )
            except Exception as e:
                logger.warning(f"Hyperliquid OI history fetch error: {e}")
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

        Note: Hyperliquid has variable funding intervals, not fixed 8h like Binance.

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
                logger.warning(f"Hyperliquid funding history fetch error: {e}")
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

    def _parse_liquidation(self, original_symbol: str, data: dict) -> Liquidation | None:
        """Parse CCXT response into Liquidation model.

        Uses safe_float for None-safe parsing. Returns None for invalid data
        (Liquidation model has gt=0 constraints that require valid values).

        Args:
            original_symbol: The original symbol passed by the caller.
            data: CCXT response dictionary.

        Returns:
            Liquidation model instance, or None if data is invalid.
        """

        # Extract and validate required fields
        price = safe_float(data.get("price"))
        quantity = safe_float(data.get("amount"))

        # Skip invalid liquidations (Liquidation model has gt=0 constraints)
        if quantity <= 0 or price <= 0:
            logger.warning(f"Skipping invalid liquidation data: {data}")
            return None

        # Calculate value
        value = quantity * price

        # CCXT returns side as the order side of the liquidation
        # "sell" = The position was forced to sell = LONG position liquidated
        # "buy" = The position was forced to buy = SHORT position liquidated
        raw_side = data.get("side", "").lower()
        if raw_side == "sell":
            side = Side.LONG
        elif raw_side == "buy":
            side = Side.SHORT
        else:
            logger.warning(f"Unknown liquidation side '{raw_side}', defaulting to LONG")
            side = Side.LONG

        try:
            return Liquidation(
                timestamp=self._parse_timestamp(data.get("timestamp")),
                symbol=original_symbol.upper(),
                venue=Venue.HYPERLIQUID,
                side=side,
                quantity=quantity,
                price=price,
                value=value,
            )
        except Exception as e:
            logger.warning(f"Failed to parse liquidation: {e}, data: {data}")
            return None

    async def stream_liquidations(
        self, symbol: str, callback: Callable[[Liquidation], None]
    ) -> None:
        """Stream liquidation events via polling fallback.

        Hyperliquid does not support WebSocket liquidation streaming,
        so we poll the REST API at 5-second intervals.

        Args:
            symbol: Trading pair symbol.
            callback: Function to call with each liquidation event.

        Raises:
            asyncio.CancelledError: If polling is cancelled.
        """
        import asyncio

        exchange = self._ensure_connected()
        ccxt_symbol = self.normalize_symbol(symbol)

        # Polling interval in seconds
        POLL_INTERVAL = 5.0

        # Track seen liquidations to avoid duplicates
        seen_timestamps: set[int] = set()

        logger.info(
            f"Starting liquidation polling for {symbol} on {self.venue_name} "
            f"(interval: {POLL_INTERVAL}s)"
        )

        while True:
            try:
                # Fetch recent liquidations via REST API
                # Note: Hyperliquid may use fetch_liquidations or similar
                try:
                    liquidations = await exchange.fetch_liquidations(ccxt_symbol)
                except AttributeError:
                    # Fallback: Some CCXT versions may use different method
                    logger.warning(
                        f"fetch_liquidations not available for {self.venue_name}, "
                        "trying fetch_my_liquidations"
                    )
                    try:
                        liquidations = await exchange.fetch_my_liquidations(ccxt_symbol)
                    except (AttributeError, Exception):
                        logger.warning(
                            f"No liquidation endpoint available for {self.venue_name}. "
                            "Liquidation streaming not supported."
                        )
                        # Sleep and retry - endpoint might become available
                        await asyncio.sleep(POLL_INTERVAL * 2)
                        continue

                for liq_data in liquidations:
                    ts = liq_data.get("timestamp", 0)
                    if ts in seen_timestamps:
                        continue

                    seen_timestamps.add(ts)

                    liquidation = self._parse_liquidation(symbol, liq_data)
                    if liquidation is not None:
                        callback(liquidation)
                        logger.debug(
                            f"Liquidation: {liquidation.side.value} "
                            f"{liquidation.quantity} @ {liquidation.price}"
                        )

                # Limit memory usage by pruning old timestamps
                if len(seen_timestamps) > 10000:
                    # Keep only most recent 5000
                    sorted_ts = sorted(seen_timestamps)
                    seen_timestamps.clear()
                    seen_timestamps.update(sorted_ts[-5000:])

            except asyncio.CancelledError:
                logger.info(f"Liquidation polling cancelled for {symbol}")
                raise

            except Exception as e:
                logger.warning(f"Polling error for {symbol}: {e}")

            await asyncio.sleep(POLL_INTERVAL)
