#!/usr/bin/env python3
"""Stream live market data from Hyperliquid (Spec 021 - US1).

This script demonstrates connecting to Hyperliquid and streaming real-time
market data including quotes, trades, and orderbook updates.

Usage:
    python scripts/hyperliquid/stream_data.py [--testnet] [--duration SECONDS]

Example:
    # Stream mainnet data for 60 seconds
    python scripts/hyperliquid/stream_data.py --duration 60

    # Stream testnet data for 30 seconds
    python scripts/hyperliquid/stream_data.py --testnet --duration 30
"""

import argparse
import time
from datetime import datetime

from nautilus_trader.common.enums import LogLevel
from nautilus_trader.config import LoggingConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import QuoteTick, TradeTick, OrderBookDelta
from nautilus_trader.trading.strategy import Strategy

from configs.hyperliquid.data_client import (
    create_data_only_trading_node,
    DEFAULT_INSTRUMENTS,
)


class DataStreamStrategy(Strategy):
    """Strategy that subscribes to and logs market data.

    This strategy demonstrates subscribing to:
    - Quote ticks (bid/ask prices)
    - Trade ticks (executed trades)
    - Order book deltas (orderbook updates)
    """

    def __init__(self, instruments: list[str], duration_secs: int = 60):
        super().__init__()
        self.instruments = instruments
        self.duration_secs = duration_secs
        self.start_time: float | None = None

        # Counters for data received
        self.quote_count = 0
        self.trade_count = 0
        self.orderbook_count = 0

    def on_start(self) -> None:
        """Subscribe to all data types for configured instruments."""
        self.start_time = time.time()
        self.log.info(f"Starting data stream for {self.duration_secs} seconds")

        for instrument_id_str in self.instruments:
            # Get instrument from cache
            instrument_id = self.cache.instrument_id(instrument_id_str)
            if instrument_id is None:
                self.log.warning(f"Instrument not found: {instrument_id_str}")
                continue

            # Subscribe to all data types
            self.subscribe_quote_ticks(instrument_id)
            self.subscribe_trade_ticks(instrument_id)
            self.subscribe_order_book_deltas(instrument_id)

            self.log.info(f"Subscribed to {instrument_id}")

    def on_quote_tick(self, tick: QuoteTick) -> None:
        """Handle incoming quote ticks."""
        self.quote_count += 1

        # Log every 100th quote to avoid flooding
        if self.quote_count % 100 == 0:
            latency_ns = time.time_ns() - tick.ts_event
            latency_ms = latency_ns / 1_000_000
            self.log.info(
                f"Quote #{self.quote_count}: {tick.instrument_id} "
                f"bid={tick.bid_price} ask={tick.ask_price} "
                f"latency={latency_ms:.1f}ms"
            )

        self._check_duration()

    def on_trade_tick(self, tick: TradeTick) -> None:
        """Handle incoming trade ticks."""
        self.trade_count += 1

        # Log every trade
        latency_ns = time.time_ns() - tick.ts_event
        latency_ms = latency_ns / 1_000_000
        self.log.info(
            f"Trade #{self.trade_count}: {tick.instrument_id} "
            f"price={tick.price} size={tick.size} side={tick.aggressor_side} "
            f"latency={latency_ms:.1f}ms"
        )

        self._check_duration()

    def on_order_book_delta(self, delta: OrderBookDelta) -> None:
        """Handle incoming orderbook updates."""
        self.orderbook_count += 1

        # Log every 500th delta to avoid flooding
        if self.orderbook_count % 500 == 0:
            latency_ns = time.time_ns() - delta.ts_event
            latency_ms = latency_ns / 1_000_000
            self.log.info(
                f"OrderBook #{self.orderbook_count}: {delta.instrument_id} "
                f"action={delta.action} latency={latency_ms:.1f}ms"
            )

        self._check_duration()

    def _check_duration(self) -> None:
        """Check if we've exceeded the streaming duration."""
        if self.start_time is None:
            return

        elapsed = time.time() - self.start_time
        if elapsed >= self.duration_secs:
            self.log.info(
                f"Duration complete. "
                f"Quotes: {self.quote_count}, "
                f"Trades: {self.trade_count}, "
                f"OrderBook: {self.orderbook_count}"
            )
            self.stop()

    def on_stop(self) -> None:
        """Log final statistics."""
        elapsed = time.time() - (self.start_time or time.time())
        self.log.info(
            f"Stream ended after {elapsed:.1f}s. "
            f"Total: Quotes={self.quote_count}, "
            f"Trades={self.trade_count}, "
            f"OrderBook={self.orderbook_count}"
        )


def main():
    """Run the data streaming script."""
    parser = argparse.ArgumentParser(
        description="Stream live market data from Hyperliquid"
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Use Hyperliquid testnet instead of mainnet",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration to stream data in seconds (default: 60)",
    )
    parser.add_argument(
        "--instruments",
        nargs="+",
        default=None,
        help="Instruments to subscribe to (default: BTC-USD-PERP, ETH-USD-PERP)",
    )
    args = parser.parse_args()

    instruments = args.instruments or DEFAULT_INSTRUMENTS

    print(f"[{datetime.now()}] Starting Hyperliquid data stream")
    print(f"  Testnet: {args.testnet}")
    print(f"  Duration: {args.duration}s")
    print(f"  Instruments: {instruments}")

    # Create node configuration
    config = create_data_only_trading_node(
        trader_id="TRADER-HL-STREAM",
        testnet=args.testnet,
        instruments=instruments,
    )

    # Add logging configuration
    config.logging = LoggingConfig(
        log_level=LogLevel.INFO,
    )

    # Create and configure node
    node = TradingNode(config=config)

    # Add strategy
    strategy = DataStreamStrategy(
        instruments=instruments,
        duration_secs=args.duration,
    )
    node.trader.add_strategy(strategy)

    # Run node
    try:
        node.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        print(f"[{datetime.now()}] Data stream complete")


if __name__ == "__main__":
    main()
