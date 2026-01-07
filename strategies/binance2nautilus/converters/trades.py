"""Trades converter for Binance CSV to NautilusTrader TradeTick.

Converts individual trade execution data using chunked processing for
memory efficiency with large datasets (500M+ records).
"""

from collections.abc import Generator
from pathlib import Path

import pandas as pd
from nautilus_trader.model.data import TradeTick

from ..config import ConverterConfig
from ..instruments import get_instrument
from ..state import ConversionState
from ..wrangler_factory import get_trade_wrangler
from .base import BaseConverter


class TradesConverter(BaseConverter):
    """Converter for Binance trades CSV to NautilusTrader TradeTick objects."""

    def __init__(
        self,
        symbol: str,
        config: ConverterConfig | None = None,
        state: ConversionState | None = None,
    ) -> None:
        """Initialize the trades converter.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            config: Converter configuration
            state: Conversion state for incremental updates
        """
        super().__init__(symbol, config, state)
        self._instrument = get_instrument(symbol)
        self._wrangler = get_trade_wrangler(
            instrument=self._instrument,
            config=self.config,
        )

    @property
    def data_type(self) -> str:
        """Return the data type identifier."""
        return "trades"

    @property
    def instrument(self):
        """Return the instrument."""
        return self._instrument

    def get_source_path(self) -> Path:
        """Return the source directory path for trades CSV files."""
        return self.config.get_trades_path(self.symbol)

    def get_file_pattern(self) -> str:
        """Return the glob pattern for trades CSV files."""
        return f"{self.symbol}-trades-*.csv"

    def parse_csv(self, file_path: Path) -> pd.DataFrame:
        """Parse a trades CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame with raw trades data
        """
        return pd.read_csv(file_path)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw trades CSV to wrangler format.

        Args:
            df: Raw DataFrame from CSV with columns:
                id, price, qty, quote_qty, time, is_buyer_maker

        Returns:
            DataFrame formatted for TradeTickDataWrangler with DatetimeIndex (UTC)
            and columns: price, quantity, buyer_maker, trade_id

        Note:
            - Column must be 'quantity' NOT 'size' for V1 wrangler
            - buyer_maker: True means buyer was maker, so SELLER was aggressor
        """
        # Create DataFrame with required columns for V1 wrangler
        # Note: Use .values to avoid pandas index alignment issues
        tick_df = pd.DataFrame(
            {
                "price": df["price"].values.astype("float64"),
                "quantity": df["qty"].values.astype("float64"),  # V1 requires 'quantity'
                "buyer_maker": df["is_buyer_maker"].values,  # bool
                "trade_id": df["id"].astype(str).values,
            },
        )
        tick_df.index = pd.to_datetime(df["time"], unit="ms", utc=True)
        return tick_df

    def wrangle(self, df: pd.DataFrame) -> list[TradeTick]:
        """Convert DataFrame to TradeTick objects using V1 wrangler.

        Args:
            df: Transformed DataFrame with trade data

        Returns:
            List of TradeTick objects
        """
        return self._wrangler.process(df)

    def process_file_chunked(
        self,
        file_path: Path,
        chunk_size: int | None = None,
    ) -> Generator[list[TradeTick], None, None]:
        """Process a trades file in chunks for memory efficiency.

        Args:
            file_path: Path to CSV file
            chunk_size: Rows per chunk (default 100k from config)

        Yields:
            Lists of TradeTick objects
        """
        chunk_size = chunk_size or self.config.chunk_size

        for chunk_df in pd.read_csv(file_path, chunksize=chunk_size):
            transformed = self.transform(chunk_df)
            yield self.wrangle(transformed)


def convert_trades(
    symbol: str,
    config: ConverterConfig | None = None,
    state: ConversionState | None = None,
    skip_processed: bool = True,
    use_chunked: bool = True,
) -> tuple[int, int]:
    """Convert all trades files for a symbol.

    Args:
        symbol: Trading symbol
        config: Converter configuration
        state: Conversion state
        skip_processed: Skip already processed files
        use_chunked: Use chunked processing (recommended for large files)

    Returns:
        Tuple of (total_ticks, file_count)

    Note:
        Unlike klines, trades are NOT returned due to memory constraints.
        They should be written to catalog in chunks.
    """
    converter = TradesConverter(
        symbol=symbol,
        config=config,
        state=state,
    )

    total_ticks = 0
    file_count = 0

    files = converter.get_pending_files() if skip_processed else converter.discover_files()

    for file_path in files:
        file_ticks = 0
        first_ts = None
        last_ts = None

        if use_chunked:
            for ticks in converter.process_file_chunked(file_path):
                file_ticks += len(ticks)
                if ticks:
                    if first_ts is None:
                        first_ts = ticks[0].ts_event
                    last_ts = ticks[-1].ts_event
        else:
            ticks = converter.process_file(file_path)
            file_ticks = len(ticks)
            if ticks:
                first_ts = ticks[0].ts_event
                last_ts = ticks[-1].ts_event

        total_ticks += file_ticks
        file_count += 1

        if state is not None and first_ts is not None and last_ts is not None:
            converter.mark_processed(
                file_path=file_path,
                record_count=file_ticks,
                first_ts=first_ts,
                last_ts=last_ts,
            )

    return total_ticks, file_count
