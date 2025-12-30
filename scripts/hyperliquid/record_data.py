#!/usr/bin/env python3
"""Record live Hyperliquid data to ParquetDataCatalog (Spec 021 - US2).

This script records market data from Hyperliquid to a local ParquetDataCatalog
for later use in backtesting.

Usage:
    python scripts/hyperliquid/record_data.py [--testnet] [--duration SECONDS] [--catalog PATH]

Example:
    # Record mainnet data for 5 minutes
    python scripts/hyperliquid/record_data.py --duration 300

    # Record to custom catalog path
    python scripts/hyperliquid/record_data.py --catalog ./my_catalog --duration 600
"""

import argparse
import time
from datetime import datetime
from pathlib import Path

from nautilus_trader.common.enums import LogLevel
from nautilus_trader.config import LoggingConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import QuoteTick, TradeTick, OrderBookDelta
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy

from configs.hyperliquid.persistence import (
    create_recording_trading_node,
    DEFAULT_CATALOG_PATH,
)
from configs.hyperliquid.data_client import DEFAULT_INSTRUMENTS


class DataRecordingStrategy(Strategy):
    """Strategy that subscribes to data for automatic persistence.

    When used with a TradingNode configured with StreamingConfig,
    all received data is automatically persisted to the catalog.
    """

    def __init__(self, instruments: list[str], duration_secs: int = 300):
        super().__init__()
        self.instruments = instruments
        self.duration_secs = duration_secs
        self.start_time: float | None = None

        # Counters
        self.quote_count = 0
        self.trade_count = 0
        self.orderbook_count = 0

    def on_start(self) -> None:
        """Subscribe to all data types for configured instruments."""
        self.start_time = time.time()
        self.log.info(f"Starting data recording for {self.duration_secs} seconds")

        for instrument_id_str in self.instruments:
            # Parse instrument ID
            instrument_id = InstrumentId.from_str(instrument_id_str)
            # Verify instrument is loaded in cache
            if self.cache.instrument(instrument_id) is None:
                self.log.warning(f"Instrument not loaded: {instrument_id_str}")
                continue

            self.subscribe_quote_ticks(instrument_id)
            self.subscribe_trade_ticks(instrument_id)
            self.subscribe_order_book_deltas(instrument_id)

            self.log.info(f"Recording: {instrument_id}")

    def on_quote_tick(self, tick: QuoteTick) -> None:
        """Count incoming quotes."""
        self.quote_count += 1
        if self.quote_count % 1000 == 0:
            self._log_progress()
        self._check_duration()

    def on_trade_tick(self, tick: TradeTick) -> None:
        """Count incoming trades."""
        self.trade_count += 1
        self._check_duration()

    def on_order_book_delta(self, delta: OrderBookDelta) -> None:
        """Count incoming orderbook updates."""
        self.orderbook_count += 1
        self._check_duration()

    def _log_progress(self) -> None:
        """Log recording progress."""
        elapsed = time.time() - (self.start_time or time.time())
        self.log.info(
            f"Recording progress [{elapsed:.0f}s]: "
            f"Quotes={self.quote_count}, Trades={self.trade_count}, "
            f"OrderBook={self.orderbook_count}"
        )

    def _check_duration(self) -> None:
        """Check if recording duration has been reached."""
        if self.start_time is None:
            return

        elapsed = time.time() - self.start_time
        if elapsed >= self.duration_secs:
            self.log.info(
                f"Recording complete. Total: "
                f"Quotes={self.quote_count}, Trades={self.trade_count}, "
                f"OrderBook={self.orderbook_count}"
            )
            self.stop()

    def on_stop(self) -> None:
        """Log final statistics."""
        elapsed = time.time() - (self.start_time or time.time())
        self.log.info(
            f"Recording ended after {elapsed:.1f}s. "
            f"Final counts: Quotes={self.quote_count}, "
            f"Trades={self.trade_count}, OrderBook={self.orderbook_count}"
        )


def main():
    """Run the data recording script."""
    parser = argparse.ArgumentParser(
        description="Record live Hyperliquid data to ParquetDataCatalog"
    )
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Use Hyperliquid testnet instead of mainnet",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Duration to record data in seconds (default: 300 = 5 minutes)",
    )
    parser.add_argument(
        "--catalog",
        type=str,
        default=DEFAULT_CATALOG_PATH,
        help=f"Path to ParquetDataCatalog (default: {DEFAULT_CATALOG_PATH})",
    )
    parser.add_argument(
        "--instruments",
        nargs="+",
        default=None,
        help="Instruments to record (default: BTC-USD-PERP, ETH-USD-PERP)",
    )
    args = parser.parse_args()

    instruments = args.instruments or DEFAULT_INSTRUMENTS
    catalog_path = Path(args.catalog)

    print(f"[{datetime.now()}] Starting Hyperliquid data recording")
    print(f"  Testnet: {args.testnet}")
    print(f"  Duration: {args.duration}s")
    print(f"  Catalog: {catalog_path.absolute()}")
    print(f"  Instruments: {instruments}")

    # Ensure catalog directory exists
    catalog_path.mkdir(parents=True, exist_ok=True)

    # Create base configuration with streaming
    base_config = create_recording_trading_node(
        trader_id="TRADER-HL-RECORD",
        testnet=args.testnet,
        instruments=instruments,
        catalog_path=str(catalog_path),
    )

    # Reconstruct config with logging (TradingNodeConfig is frozen)
    from nautilus_trader.config import TradingNodeConfig

    config = TradingNodeConfig(
        trader_id=base_config.trader_id,
        data_clients=base_config.data_clients,
        streaming=base_config.streaming,
        logging=LoggingConfig(log_level=LogLevel.INFO),
    )

    # Create node
    node = TradingNode(config=config)

    # Add recording strategy
    strategy = DataRecordingStrategy(
        instruments=instruments,
        duration_secs=args.duration,
    )
    node.trader.add_strategy(strategy)

    # Run node
    try:
        node.run()
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        print(f"[{datetime.now()}] Data recording complete")
        print(f"Data saved to: {catalog_path.absolute()}")


if __name__ == "__main__":
    main()
