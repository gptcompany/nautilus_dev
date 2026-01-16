"""Hyperliquid L2 orderbook data loader for NautilusTrader.

Loads LZ4-compressed JSON L2 orderbook snapshots from Hyperliquid historical data
and converts them to NautilusTrader OrderBookDepth10 objects.

Data format:
    {"time": "2024-08-05T00:00:05.402514755",
     "ver_num": 1,
     "raw": {"channel": "l2Book",
             "data": {"coin": "BTC",
                      "time": 1722816005022,
                      "levels": [[bids], [asks]]}}}

    Level format: {"px": "58167.0", "sz": "0.0172", "n": 1}
"""

from __future__ import annotations

import json
import logging
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import lz4.frame

if TYPE_CHECKING:
    from nautilus_trader.model.data import OrderBookDepth10
    from nautilus_trader.model.identifiers import InstrumentId

logger = logging.getLogger(__name__)


@dataclass
class HyperliquidL2Config:
    """Configuration for Hyperliquid L2 data loader.

    Attributes:
        price_precision: Decimal precision for prices (default: 1 for Hyperliquid)
        size_precision: Decimal precision for sizes (default: 5 for Hyperliquid)
        max_depth: Maximum depth levels to load (default: 10)
        venue: Venue name for instrument ID (default: "HYPERLIQUID")
    """

    price_precision: int = 1
    size_precision: int = 5
    max_depth: int = 10
    venue: str = "HYPERLIQUID"


class HyperliquidL2DataLoader:
    """Loads Hyperliquid L2 orderbook data from LZ4-compressed JSON files.

    Converts Hyperliquid's L2 orderbook snapshots to NautilusTrader
    OrderBookDepth10 objects for use in backtesting and analysis.

    Example:
        >>> from data_loaders import HyperliquidL2DataLoader
        >>> from nautilus_trader.model.identifiers import InstrumentId
        >>>
        >>> loader = HyperliquidL2DataLoader()
        >>> instrument_id = InstrumentId.from_str("BTC-PERP.HYPERLIQUID")
        >>>
        >>> # Load single file
        >>> depths = loader.load(
        ...     filepath="/path/to/20240805-0.lz4",
        ...     instrument_id=instrument_id,
        ... )
        >>>
        >>> # Stream from multiple files
        >>> for depth in loader.stream_directory(
        ...     directory="/path/to/hyperliquid_data/BTC/2024/",
        ...     instrument_id=instrument_id,
        ...     date_range=("20240805", "20240807"),
        ... ):
        ...     process(depth)
    """

    def __init__(self, config: HyperliquidL2Config | None = None) -> None:
        """Initialize the loader.

        Args:
            config: Loader configuration. Uses defaults if None.
        """
        self._config = config or HyperliquidL2Config()

    @property
    def config(self) -> HyperliquidL2Config:
        """Get loader configuration."""
        return self._config

    def load(
        self,
        filepath: str | Path,
        instrument_id: InstrumentId,
        limit: int | None = None,
    ) -> list[OrderBookDepth10]:
        """Load OrderBookDepth10 objects from a single LZ4 file.

        Args:
            filepath: Path to LZ4-compressed JSON file.
            instrument_id: NautilusTrader instrument ID.
            limit: Maximum number of snapshots to load. None for unlimited.

        Returns:
            List of OrderBookDepth10 objects.
        """
        return list(self._stream_file(filepath, instrument_id, limit))

    def stream(
        self,
        filepath: str | Path,
        instrument_id: InstrumentId,
        limit: int | None = None,
    ) -> Generator[OrderBookDepth10, None, None]:
        """Stream OrderBookDepth10 objects from a single LZ4 file.

        Memory-efficient generator for large files.

        Args:
            filepath: Path to LZ4-compressed JSON file.
            instrument_id: NautilusTrader instrument ID.
            limit: Maximum number of snapshots to yield. None for unlimited.

        Yields:
            OrderBookDepth10 objects.
        """
        yield from self._stream_file(filepath, instrument_id, limit)

    def stream_directory(
        self,
        directory: str | Path,
        instrument_id: InstrumentId,
        date_range: tuple[str, str] | None = None,
        limit: int | None = None,
    ) -> Generator[OrderBookDepth10, None, None]:
        """Stream OrderBookDepth10 objects from all LZ4 files in a directory.

        Args:
            directory: Directory containing LZ4 files.
            instrument_id: NautilusTrader instrument ID.
            date_range: Optional (start_date, end_date) in YYYYMMDD format.
            limit: Maximum total snapshots to yield. None for unlimited.

        Yields:
            OrderBookDepth10 objects sorted by timestamp.
        """
        directory = Path(directory)
        files = sorted(directory.glob("*.lz4"))

        if date_range:
            start_date, end_date = date_range
            files = [f for f in files if start_date <= f.stem.split("-")[0] <= end_date]

        count = 0
        for filepath in files:
            for depth in self._stream_file(filepath, instrument_id):
                yield depth
                count += 1
                if limit and count >= limit:
                    return

    def _stream_file(
        self,
        filepath: str | Path,
        instrument_id: InstrumentId,
        limit: int | None = None,
    ) -> Generator[OrderBookDepth10, None, None]:
        """Internal generator for streaming from a single file."""
        from nautilus_trader.model.data import BookOrder, OrderBookDepth10
        from nautilus_trader.model.enums import OrderSide
        from nautilus_trader.model.objects import Price, Quantity

        filepath = Path(filepath)
        count = 0
        sequence = 0

        with lz4.frame.open(filepath, "rb") as f:
            for line in f:
                if limit and count >= limit:
                    break

                try:
                    data = json.loads(line)
                    levels = data["raw"]["data"]["levels"]
                    bids_raw = levels[0]
                    asks_raw = levels[1]

                    if not bids_raw or not asks_raw:
                        continue

                    # Parse timestamp
                    ts_str = data["time"]
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    ts_event = int(dt.timestamp() * 1_000_000_000)
                    ts_init = ts_event

                    # Build bid orders (top N levels)
                    bids = []
                    bid_counts = []
                    for i, level in enumerate(bids_raw[: self._config.max_depth]):
                        price = Price.from_str(level["px"])
                        size = Quantity.from_str(level["sz"])
                        order = BookOrder(
                            side=OrderSide.BUY,
                            price=price,
                            size=size,
                            order_id=i + 1,
                        )
                        bids.append(order)
                        bid_counts.append(level.get("n", 1))

                    # Build ask orders (top N levels)
                    asks = []
                    ask_counts = []
                    for i, level in enumerate(asks_raw[: self._config.max_depth]):
                        price = Price.from_str(level["px"])
                        size = Quantity.from_str(level["sz"])
                        order = BookOrder(
                            side=OrderSide.SELL,
                            price=price,
                            size=size,
                            order_id=i + 1,
                        )
                        asks.append(order)
                        ask_counts.append(level.get("n", 1))

                    # Pad to equal length (required by OrderBookDepth10)
                    max_len = max(len(bids), len(asks))
                    while len(bids) < max_len:
                        # Pad with zero-size orders
                        bids.append(
                            BookOrder(
                                side=OrderSide.BUY,
                                price=Price.from_str("0.0"),
                                size=Quantity.from_int(0),
                                order_id=0,
                            )
                        )
                        bid_counts.append(0)
                    while len(asks) < max_len:
                        asks.append(
                            BookOrder(
                                side=OrderSide.SELL,
                                price=Price.from_str("0.0"),
                                size=Quantity.from_int(0),
                                order_id=0,
                            )
                        )
                        ask_counts.append(0)

                    depth = OrderBookDepth10(
                        instrument_id=instrument_id,
                        bids=bids,
                        asks=asks,
                        bid_counts=bid_counts,
                        ask_counts=ask_counts,
                        flags=0,
                        sequence=sequence,
                        ts_event=ts_event,
                        ts_init=ts_init,
                    )

                    yield depth
                    count += 1
                    sequence += 1

                except (KeyError, ValueError, json.JSONDecodeError) as e:
                    logger.debug("Skipping malformed line: %s", e)
                    continue

        logger.info("Loaded %d OrderBookDepth10 from %s", count, filepath.name)

    def get_file_info(self, filepath: str | Path) -> dict:
        """Get metadata about an LZ4 file without loading all data.

        Args:
            filepath: Path to LZ4-compressed JSON file.

        Returns:
            Dict with file metadata (first_timestamp, last_timestamp, count estimate).
        """
        filepath = Path(filepath)
        first_ts = None
        last_ts = None
        count = 0

        with lz4.frame.open(filepath, "rb") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    ts_str = data["time"]
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

                    if first_ts is None:
                        first_ts = dt
                    last_ts = dt
                    count += 1
                except (KeyError, ValueError, json.JSONDecodeError):
                    continue

        return {
            "filepath": str(filepath),
            "first_timestamp": first_ts,
            "last_timestamp": last_ts,
            "count": count,
            "duration_seconds": (last_ts - first_ts).total_seconds() if first_ts and last_ts else 0,
        }
