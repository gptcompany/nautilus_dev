#!/usr/bin/env python3
"""
Multi-Exchange Data Recorder for Binance and Hyperliquid.

Records live market data to ParquetDataCatalog:
- Trade ticks (every trade)
- Quote ticks (bid/ask)
- OrderBook deltas (L2 updates)
- Mark Price (Binance only)

Uses NautilusTrader nightly with native Rust adapters.

NOTE: Open Interest and Liquidation streams are NOT available in NautilusTrader.
      For those, use Tardis or direct exchange APIs.

Usage:
    # Activate nightly environment first:
    source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate

    # Run recorder:
    python record_binance_hyperliquid.py

Environment Variables:
    BINANCE_API_KEY      - Binance API key (optional for public data)
    BINANCE_API_SECRET   - Binance API secret (optional for public data)
    HYPERLIQUID_PK       - Hyperliquid private key (optional for public data)
"""

import signal
from datetime import datetime
from pathlib import Path

from nautilus_trader.adapters.binance import BINANCE
from nautilus_trader.adapters.binance import BinanceAccountType
from nautilus_trader.adapters.binance import BinanceDataClientConfig
from nautilus_trader.adapters.binance import BinanceLiveDataClientFactory
from nautilus_trader.adapters.binance import BinanceFuturesMarkPriceUpdate
from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.adapters.hyperliquid import HyperliquidDataClientConfig
from nautilus_trader.adapters.hyperliquid import HyperliquidLiveDataClientFactory
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import StreamingConfig
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.data import DataType
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId


# Configuration
CATALOG_PATH = Path("/media/sam/1TB/nautilus_dev/data/live_catalog")
CATALOG_PATH.mkdir(parents=True, exist_ok=True)

# Instruments to record (BTC and ETH only)
BINANCE_INSTRUMENTS = [
    "BTCUSDT-PERP.BINANCE",
    "ETHUSDT-PERP.BINANCE",
]

HYPERLIQUID_INSTRUMENTS = [
    "BTC-USD-PERP.HYPERLIQUID",
    "ETH-USD-PERP.HYPERLIQUID",
]


def create_config() -> TradingNodeConfig:
    """Create TradingNode configuration for data recording."""
    return TradingNodeConfig(
        trader_id=f"DATA-RECORDER-{datetime.now().strftime('%Y%m%d')}",
        logging=LoggingConfig(
            log_level="INFO",
            log_level_file="DEBUG",
            log_directory=str(CATALOG_PATH / "logs"),
            log_file_format="{trader_id}_{instance_id}",
        ),
        streaming=StreamingConfig(
            catalog_path=str(CATALOG_PATH),
            flush_interval_ms=1000,  # Flush every second
        ),
        data_clients={
            BINANCE: BinanceDataClientConfig(
                account_type=BinanceAccountType.USDT_FUTURES,
                instrument_provider=InstrumentProviderConfig(load_all=False),
            ),
            HYPERLIQUID: HyperliquidDataClientConfig(
                testnet=False,
                instrument_provider=InstrumentProviderConfig(load_all=False),
            ),
        },
        exec_clients={},  # No execution - data only
    )


class DataRecorder:
    """Manages the data recording node."""

    def __init__(self):
        self.node: TradingNode | None = None
        self._running = False

    def build(self) -> None:
        """Build the trading node."""
        config = create_config()
        self.node = TradingNode(config=config)

        # Register data client factories
        self.node.add_data_client_factory(BINANCE, BinanceLiveDataClientFactory)
        self.node.add_data_client_factory(HYPERLIQUID, HyperliquidLiveDataClientFactory)

        self.node.build()
        print(f"[INFO] Node built. Catalog: {CATALOG_PATH}")

    def subscribe_instruments(self) -> None:
        """Subscribe to market data for configured instruments."""
        if not self.node:
            raise RuntimeError("Node not built")

        # Subscribe Binance instruments
        for symbol in BINANCE_INSTRUMENTS:
            instrument_id = InstrumentId.from_str(symbol)
            # Core data
            self.node.subscribe_trade_ticks(instrument_id)
            self.node.subscribe_quote_ticks(instrument_id)
            # OrderBook L2 deltas
            self.node.subscribe_order_book_deltas(instrument_id)
            # Mark Price (Binance-specific custom data type)
            self.node.subscribe_data(
                data_type=DataType(
                    BinanceFuturesMarkPriceUpdate,
                    metadata={"instrument_id": instrument_id},
                ),
                client_id=ClientId("BINANCE"),
            )
            print(f"[INFO] Subscribed (trades, quotes, orderbook, mark_price): {symbol}")

        # Subscribe Hyperliquid instruments
        for symbol in HYPERLIQUID_INSTRUMENTS:
            instrument_id = InstrumentId.from_str(symbol)
            # Core data
            self.node.subscribe_trade_ticks(instrument_id)
            self.node.subscribe_quote_ticks(instrument_id)
            # OrderBook L2 deltas
            self.node.subscribe_order_book_deltas(instrument_id)
            # Note: Mark Price NOT available for Hyperliquid yet
            print(f"[INFO] Subscribed (trades, quotes, orderbook): {symbol}")

    def run(self) -> None:
        """Run the data recorder."""
        if not self.node:
            raise RuntimeError("Node not built")

        self._running = True
        print(f"[INFO] Starting data recording at {datetime.now()}")
        print(f"[INFO] Press Ctrl+C to stop")

        try:
            self.node.run()
        except KeyboardInterrupt:
            print("\n[INFO] Keyboard interrupt received")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the data recorder gracefully."""
        if self.node and self._running:
            print("[INFO] Stopping node...")
            self.node.dispose()
            self._running = False
            print(f"[INFO] Data recording stopped at {datetime.now()}")
            print(f"[INFO] Data saved to: {CATALOG_PATH}")


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("NautilusTrader Multi-Exchange Data Recorder")
    print("=" * 60)
    print(f"Binance instruments: {BINANCE_INSTRUMENTS}")
    print(f"Hyperliquid instruments: {HYPERLIQUID_INSTRUMENTS}")
    print(f"Catalog path: {CATALOG_PATH}")
    print("")
    print("Data types recorded:")
    print("  - Trade ticks (every trade)")
    print("  - Quote ticks (bid/ask)")
    print("  - OrderBook deltas (L2 updates)")
    print("  - Mark Price (Binance only)")
    print("")
    print("NOT available (use Tardis/Coinglass):")
    print("  - Open Interest (OI)")
    print("  - Liquidation stream")
    print("=" * 60)

    recorder = DataRecorder()

    # Handle signals for graceful shutdown
    def signal_handler(sig, frame):
        print(f"\n[INFO] Signal {sig} received")
        recorder.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Build and run
    recorder.build()
    recorder.subscribe_instruments()
    recorder.run()


if __name__ == "__main__":
    main()
