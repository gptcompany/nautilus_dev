"""AggTrades converter for Binance CSV to NautilusTrader TradeTick.

Converts aggregated trade data (aggTrades) using memory-efficient chunked
processing. AggTrades are ~50% smaller than raw trades with same info for VPIN.

Features:
- Handles both header and headerless CSV formats (pre/post ~2021)
- Memory-efficient chunked processing (default 50k rows)
- Date range filtering for subset conversion
- Streaming writes to catalog
"""

from collections.abc import Generator
from datetime import datetime
from pathlib import Path

import pandas as pd
from nautilus_trader.model.data import TradeTick

from ..config import ConverterConfig
from ..instruments import get_instrument
from ..state import ConversionState
from ..wrangler_factory import get_trade_wrangler
from .base import BaseConverter

# Standard Binance aggTrades column names
AGGTRADES_COLUMNS = [
    "agg_trade_id",
    "price",
    "quantity",
    "first_trade_id",
    "last_trade_id",
    "transact_time",
    "is_buyer_maker",
]


class AggTradesConverter(BaseConverter):
    """Converter for Binance aggTrades CSV to NautilusTrader TradeTick objects.

    Memory-optimized for large datasets (100GB+) using:
    - Chunked CSV reading (default 50k rows)
    - Streaming writes to parquet
    - Immediate memory release after each chunk
    """

    def __init__(
        self,
        symbol: str,
        config: ConverterConfig | None = None,
        state: ConversionState | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        chunk_size: int = 50_000,
    ) -> None:
        """Initialize the aggTrades converter.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            config: Converter configuration
            state: Conversion state for incremental updates
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)
            chunk_size: Rows per chunk for memory efficiency (default 50k)
        """
        super().__init__(symbol, config, state)
        self._instrument = get_instrument(symbol)
        self._wrangler = get_trade_wrangler(
            instrument=self._instrument,
            config=self.config,
        )
        self.start_date = start_date
        self.end_date = end_date
        self._chunk_size = chunk_size

    @property
    def data_type(self) -> str:
        """Return the data type identifier."""
        return "aggtrades"

    @property
    def instrument(self):
        """Return the instrument."""
        return self._instrument

    def get_source_path(self) -> Path:
        """Return the source directory path for aggTrades CSV files."""
        return self.config.source_dir / self.symbol / "aggTrades"

    def get_file_pattern(self) -> str:
        """Return the glob pattern for aggTrades CSV files."""
        return f"{self.symbol}-aggTrades-*.csv"

    def _is_file_in_date_range(self, file_path: Path) -> bool:
        """Check if file is within the configured date range.

        Args:
            file_path: Path to CSV file (format: BTCUSDT-aggTrades-2025-01-01.csv)

        Returns:
            True if file is within date range, False otherwise
        """
        if self.start_date is None and self.end_date is None:
            return True

        # Extract date from filename: BTCUSDT-aggTrades-2025-01-01.csv
        try:
            parts = file_path.stem.split("-")
            # Last 3 parts should be YYYY-MM-DD
            year, month, day = int(parts[-3]), int(parts[-2]), int(parts[-1])
            file_date = datetime(year, month, day)

            if self.start_date and file_date < self.start_date:
                return False
            if self.end_date and file_date > self.end_date:
                return False
            return True
        except (ValueError, IndexError):
            # If we can't parse date, include the file
            return True

    def get_pending_files(self) -> list[Path]:
        """Get files that haven't been processed yet, filtered by date range.

        Returns:
            List of unprocessed file paths within date range
        """
        all_files = super().get_pending_files()
        return [f for f in all_files if self._is_file_in_date_range(f)]

    def discover_files(self) -> list[Path]:
        """Discover all CSV files matching the pattern, filtered by date range.

        Returns:
            Sorted list of file paths within date range
        """
        all_files = super().discover_files()
        return [f for f in all_files if self._is_file_in_date_range(f)]

    def parse_csv(self, file_path: Path) -> pd.DataFrame:
        """Parse an aggTrades CSV file.

        Handles both header and headerless formats automatically.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame with raw aggTrades data
        """
        # Read with explicit column names (handles headerless case)
        df = pd.read_csv(file_path, header=None, names=AGGTRADES_COLUMNS)

        # If first row looks like header, skip it
        first_val = str(df.iloc[0]["agg_trade_id"])
        if first_val == "agg_trade_id" or not first_val.isdigit():
            df = df.iloc[1:].reset_index(drop=True)

        # Convert numeric columns
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
        df["transact_time"] = pd.to_numeric(df["transact_time"], errors="coerce")

        # Convert is_buyer_maker to boolean
        df["is_buyer_maker"] = df["is_buyer_maker"].apply(
            lambda x: x if isinstance(x, bool) else str(x).lower() == "true"
        )

        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw aggTrades CSV to wrangler format.

        Args:
            df: Raw DataFrame from CSV with aggTrades columns

        Returns:
            DataFrame formatted for TradeTickDataWrangler with DatetimeIndex (UTC)
            and columns: price, quantity, buyer_maker, trade_id
        """
        # Create DataFrame with required columns for V1 wrangler
        tick_df = pd.DataFrame(
            {
                "price": df["price"].values.astype("float64"),
                "quantity": df["quantity"].values.astype("float64"),
                "buyer_maker": df["is_buyer_maker"].values,
                "trade_id": df["agg_trade_id"].astype(str).values,
            },
        )
        tick_df.index = pd.to_datetime(df["transact_time"], unit="ms", utc=True)
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
        """Process an aggTrades file in chunks for memory efficiency.

        This is the recommended method for large files.

        Args:
            file_path: Path to CSV file
            chunk_size: Rows per chunk (default from init or 50k)

        Yields:
            Lists of TradeTick objects
        """
        chunk_size = chunk_size or self._chunk_size

        # Read in chunks with explicit column names
        for chunk_df in pd.read_csv(
            file_path,
            header=None,
            names=AGGTRADES_COLUMNS,
            chunksize=chunk_size,
        ):
            # Skip header row if present in chunk
            first_val = str(chunk_df.iloc[0]["agg_trade_id"])
            if first_val == "agg_trade_id" or not first_val.isdigit():
                chunk_df = chunk_df.iloc[1:].reset_index(drop=True)
                if chunk_df.empty:
                    continue

            # Convert types
            chunk_df["price"] = pd.to_numeric(chunk_df["price"], errors="coerce")
            chunk_df["quantity"] = pd.to_numeric(chunk_df["quantity"], errors="coerce")
            chunk_df["transact_time"] = pd.to_numeric(chunk_df["transact_time"], errors="coerce")
            chunk_df["is_buyer_maker"] = chunk_df["is_buyer_maker"].apply(
                lambda x: x if isinstance(x, bool) else str(x).lower() == "true"
            )

            # Drop any rows with NaN values (corrupted data)
            chunk_df = chunk_df.dropna(subset=["price", "quantity", "transact_time"])

            if chunk_df.empty:
                continue

            transformed = self.transform(chunk_df)
            ticks = self.wrangle(transformed)

            yield ticks

            # Explicit cleanup to help garbage collector
            del transformed
            del chunk_df


def get_aggtrades_date_range(
    symbol: str,
    source_dir: Path,
) -> tuple[datetime | None, datetime | None]:
    """Get the date range of available aggTrades files.

    Args:
        symbol: Trading symbol
        source_dir: Base source directory

    Returns:
        Tuple of (min_date, max_date) or (None, None) if no files
    """
    aggtrades_dir = source_dir / symbol / "aggTrades"
    if not aggtrades_dir.exists():
        return None, None

    files = sorted(aggtrades_dir.glob(f"{symbol}-aggTrades-*.csv"))
    if not files:
        return None, None

    def parse_date(file_path: Path) -> datetime | None:
        try:
            parts = file_path.stem.split("-")
            year, month, day = int(parts[-3]), int(parts[-2]), int(parts[-1])
            return datetime(year, month, day)
        except (ValueError, IndexError):
            return None

    dates = [d for d in (parse_date(f) for f in files) if d is not None]
    if not dates:
        return None, None

    return min(dates), max(dates)
