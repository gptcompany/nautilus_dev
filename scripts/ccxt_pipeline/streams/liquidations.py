"""Native WebSocket streams for liquidation events.

Bypasses CCXT to use exchange-native WebSocket APIs for real-time liquidation data.
CCXT doesn't support watchLiquidations() for most exchanges yet.

Supported exchanges:
- Binance Futures: wss://fstream.binance.com/ws/!forceOrder@arr
- Bybit Linear: wss://stream.bybit.com/v5/public/linear
"""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Callable

import websockets
from websockets.exceptions import ConnectionClosed

from scripts.ccxt_pipeline.models import Liquidation, Side, Venue
from scripts.ccxt_pipeline.utils.logging import get_logger

logger = get_logger("liquidation_stream")


class BaseLiquidationStream(ABC):
    """Base class for native liquidation WebSocket streams."""

    def __init__(self, symbols: list[str], callback: Callable[[Liquidation], None]):
        self.symbols = symbols
        self.callback = callback
        self._running = False
        self._ws = None
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0

    @property
    @abstractmethod
    def venue(self) -> Venue:
        """Return the venue for this stream."""
        pass

    @property
    @abstractmethod
    def ws_url(self) -> str:
        """Return the WebSocket URL."""
        pass

    @abstractmethod
    def parse_message(self, data: dict) -> Liquidation | None:
        """Parse a WebSocket message into a Liquidation object."""
        pass

    async def start(self) -> None:
        """Start the WebSocket stream with auto-reconnect."""
        self._running = True
        logger.info(f"Starting {self.venue.value} liquidation stream for {self.symbols}")

        while self._running:
            try:
                await self._connect_and_stream()
            except ConnectionClosed as e:
                if not self._running:
                    break
                logger.warning(
                    f"{self.venue.value} WebSocket closed: {e}. "
                    f"Reconnecting in {self._reconnect_delay}s..."
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
            except Exception as e:
                if not self._running:
                    break
                logger.error(
                    f"{self.venue.value} stream error: {e}. "
                    f"Reconnecting in {self._reconnect_delay}s..."
                )
                await asyncio.sleep(self._reconnect_delay)
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

    async def _connect_and_stream(self) -> None:
        """Connect to WebSocket and process messages."""
        async with websockets.connect(self.ws_url, ping_interval=20) as ws:
            self._ws = ws
            self._reconnect_delay = 1.0  # Reset on successful connect
            logger.info(f"Connected to {self.venue.value} liquidation stream")

            # Send subscription if needed
            await self._subscribe(ws)

            async for message in ws:
                if not self._running:
                    break
                try:
                    data = json.loads(message)
                    liquidation = self.parse_message(data)
                    if liquidation:
                        self.callback(liquidation)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {self.venue.value}: {message[:100]}")
                except Exception as e:
                    logger.error(f"Error parsing {self.venue.value} message: {e}")

    async def _subscribe(self, ws) -> None:
        """Send subscription message if required by the exchange."""
        pass  # Override in subclasses if needed

    async def stop(self) -> None:
        """Stop the WebSocket stream."""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        logger.info(f"Stopped {self.venue.value} liquidation stream")


class BinanceLiquidationStream(BaseLiquidationStream):
    """Binance Futures liquidation stream.

    Uses the aggregate forceOrder stream for all symbols.
    Endpoint: wss://fstream.binance.com/ws/!forceOrder@arr
    """

    @property
    def venue(self) -> Venue:
        return Venue.BINANCE

    @property
    def ws_url(self) -> str:
        return "wss://fstream.binance.com/ws/!forceOrder@arr"

    def parse_message(self, data: dict) -> Liquidation | None:
        """Parse Binance forceOrder message.

        Format:
        {
            "e": "forceOrder",
            "E": 1234567890123,
            "o": {
                "s": "BTCUSDT",
                "S": "SELL",
                "o": "LIMIT",
                "f": "IOC",
                "q": "0.014",
                "p": "9910",
                "ap": "9910",
                "X": "FILLED",
                "l": "0.014",
                "z": "0.014",
                "T": 1234567890123
            }
        }
        """
        if data.get("e") != "forceOrder":
            return None

        order = data.get("o", {})
        symbol = order.get("s", "")

        # Filter by our symbols (normalize to match)
        symbol_base = symbol.replace("USDT", "").replace("USD", "")
        matching = any(
            symbol_base in s.upper().replace("-", "").replace("/", "") for s in self.symbols
        )
        if not matching:
            return None

        try:
            price = float(order.get("ap", order.get("p", 0)))
            quantity = float(order.get("q", 0))
            # Skip invalid data (Liquidation model requires gt=0)
            if price <= 0 or quantity <= 0:
                return None
            return Liquidation(
                timestamp=datetime.fromtimestamp(
                    order.get("T", data.get("E", 0)) / 1000, tz=timezone.utc
                ),
                symbol=f"{symbol}-PERP",
                venue=Venue.BINANCE,
                # SELL order = LONG position liquidated, BUY order = SHORT position liquidated
                side=Side.LONG if order.get("S") == "SELL" else Side.SHORT,
                price=price,
                quantity=quantity,
                value=price * quantity,
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse Binance liquidation: {e}")
            return None


class BybitLiquidationStream(BaseLiquidationStream):
    """Bybit Linear liquidation stream.

    Uses the V5 public WebSocket API.
    Endpoint: wss://stream.bybit.com/v5/public/linear
    """

    @property
    def venue(self) -> Venue:
        return Venue.BYBIT

    @property
    def ws_url(self) -> str:
        return "wss://stream.bybit.com/v5/public/linear"

    async def _subscribe(self, ws) -> None:
        """Subscribe to liquidation topics for each symbol."""
        # Convert symbols to Bybit format (e.g., BTCUSDT-PERP -> BTCUSDT)
        bybit_symbols = []
        for s in self.symbols:
            cleaned = s.upper().replace("-PERP", "").replace("/", "").replace(":USDT", "")
            if not cleaned.endswith("USDT"):
                cleaned += "USDT"
            bybit_symbols.append(cleaned)

        topics = [f"liquidation.{sym}" for sym in bybit_symbols]

        subscribe_msg = {
            "op": "subscribe",
            "args": topics,
        }
        await ws.send(json.dumps(subscribe_msg))
        logger.info(f"Subscribed to Bybit topics: {topics}")

    def parse_message(self, data: dict) -> Liquidation | None:
        """Parse Bybit liquidation message.

        Format:
        {
            "topic": "liquidation.BTCUSDT",
            "type": "snapshot",
            "ts": 1234567890123,
            "data": {
                "updatedTime": 1234567890123,
                "symbol": "BTCUSDT",
                "side": "Buy",
                "size": "0.001",
                "price": "50000"
            }
        }
        """
        if not data.get("topic", "").startswith("liquidation."):
            return None

        liq_data = data.get("data", {})
        if not liq_data:
            return None

        symbol = liq_data.get("symbol", "")

        try:
            price = float(liq_data.get("price", 0))
            quantity = float(liq_data.get("size", 0))
            # Skip invalid data (Liquidation model requires gt=0)
            if price <= 0 or quantity <= 0:
                return None
            return Liquidation(
                timestamp=datetime.fromtimestamp(
                    liq_data.get("updatedTime", data.get("ts", 0)) / 1000,
                    tz=timezone.utc,
                ),
                symbol=f"{symbol}-PERP",
                venue=Venue.BYBIT,
                # Buy order = SHORT position liquidated, Sell order = LONG position liquidated
                side=Side.SHORT if liq_data.get("side") == "Buy" else Side.LONG,
                price=price,
                quantity=quantity,
                value=price * quantity,
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse Bybit liquidation: {e}")
            return None


class HyperliquidLiquidationStream(BaseLiquidationStream):
    """Hyperliquid liquidation stream via trades WebSocket.

    Hyperliquid exposes liquidations through their trades stream.
    Trades with liquidation=true are liquidation events.
    Endpoint: wss://api.hyperliquid.xyz/ws
    """

    @property
    def venue(self) -> Venue:
        return Venue.HYPERLIQUID

    @property
    def ws_url(self) -> str:
        return "wss://api.hyperliquid.xyz/ws"

    async def _subscribe(self, ws) -> None:
        """Subscribe to trades for each symbol (liquidations appear as trades)."""
        # Convert symbols to Hyperliquid format (e.g., BTCUSDT-PERP -> BTC)
        for s in self.symbols:
            # Extract base asset (BTC from BTCUSDT-PERP)
            coin = s.upper().replace("-PERP", "").replace("USDT", "").replace("/", "")

            subscribe_msg = {
                "method": "subscribe",
                "subscription": {"type": "trades", "coin": coin},
            }
            await ws.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to Hyperliquid trades for {coin}")

    def parse_message(self, data: dict) -> Liquidation | None:
        """Parse Hyperliquid trade message for liquidations.

        Format:
        {
            "channel": "trades",
            "data": [
                {
                    "coin": "BTC",
                    "side": "A",  // A = sell (ask), B = buy (bid)
                    "px": "50000.0",
                    "sz": "0.1",
                    "time": 1234567890123,
                    "hash": "0x...",
                    "liquidation": true  // Only present for liquidations
                }
            ]
        }
        """
        if data.get("channel") != "trades":
            return None

        trades = data.get("data", [])
        for trade in trades:
            # Only process liquidations
            if not trade.get("liquidation"):
                continue

            coin = trade.get("coin", "")

            try:
                price = float(trade.get("px", 0))
                quantity = float(trade.get("sz", 0))
                # Skip invalid data (Liquidation model requires gt=0)
                if price <= 0 or quantity <= 0:
                    continue
                return Liquidation(
                    timestamp=datetime.fromtimestamp(trade.get("time", 0) / 1000, tz=timezone.utc),
                    symbol=f"{coin}USDT-PERP",
                    venue=Venue.HYPERLIQUID,
                    # A (ask/sell) = LONG position liquidated, B (bid/buy) = SHORT position liquidated
                    side=Side.LONG if trade.get("side") == "A" else Side.SHORT,
                    price=price,
                    quantity=quantity,
                    value=price * quantity,
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse Hyperliquid liquidation: {e}")

        return None


class LiquidationStreamManager:
    """Manages multiple liquidation streams across exchanges."""

    def __init__(
        self,
        symbols: list[str],
        callback: Callable[[Liquidation], None],
        exchanges: list[str] | None = None,
    ):
        self.symbols = symbols
        self.callback = callback
        self.exchanges = exchanges or ["binance", "bybit", "hyperliquid"]
        self._streams: list[BaseLiquidationStream] = []
        self._tasks: list[asyncio.Task] = []

    def _create_streams(self) -> list[BaseLiquidationStream]:
        """Create stream instances for configured exchanges."""
        streams = []
        for exchange in self.exchanges:
            if exchange.lower() == "binance":
                streams.append(BinanceLiquidationStream(self.symbols, self.callback))
            elif exchange.lower() == "bybit":
                streams.append(BybitLiquidationStream(self.symbols, self.callback))
            elif exchange.lower() == "hyperliquid":
                streams.append(HyperliquidLiquidationStream(self.symbols, self.callback))
        return streams

    async def start(self) -> None:
        """Start all liquidation streams."""
        self._streams = self._create_streams()
        self._tasks = [asyncio.create_task(stream.start()) for stream in self._streams]
        logger.info(f"Started {len(self._streams)} liquidation streams for {self.symbols}")

    async def stop(self) -> None:
        """Stop all liquidation streams."""
        for stream in self._streams:
            await stream.stop()

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._streams.clear()
        self._tasks.clear()
        logger.info("All liquidation streams stopped")
