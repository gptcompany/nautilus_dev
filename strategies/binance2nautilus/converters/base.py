"""Base converter class for Binance CSV to NautilusTrader data.

Provides common functionality for all converters including:
- File discovery and sorting
- State tracking integration
- Chunked processing support
"""

import glob
from abc import ABC, abstractmethod
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import ConverterConfig
from ..state import ConversionState


class BaseConverter(ABC):
    """Base class for Binance data converters."""

    def __init__(
        self,
        symbol: str,
        config: ConverterConfig | None = None,
        state: ConversionState | None = None,
    ) -> None:
        """Initialize the converter.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            config: Converter configuration
            state: Conversion state for incremental updates
        """
        self.symbol = symbol
        self.config = config or ConverterConfig()
        self.state = state

    @property
    @abstractmethod
    def data_type(self) -> str:
        """Return the data type identifier (e.g., 'klines_1m', 'trades')."""
        ...

    @abstractmethod
    def get_source_path(self) -> Path:
        """Return the source directory path for CSV files."""
        ...

    @abstractmethod
    def get_file_pattern(self) -> str:
        """Return the glob pattern for matching CSV files."""
        ...

    @abstractmethod
    def parse_csv(self, file_path: Path) -> pd.DataFrame:
        """Parse a CSV file and return a DataFrame.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame with parsed data
        """
        ...

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw CSV data to wrangler format.

        Args:
            df: Raw DataFrame from CSV

        Returns:
            DataFrame formatted for wrangler
        """
        ...

    @abstractmethod
    def wrangle(self, df: pd.DataFrame) -> list[Any]:
        """Convert DataFrame to NautilusTrader objects.

        Args:
            df: Transformed DataFrame

        Returns:
            List of NautilusTrader data objects (Bar, TradeTick, etc.)
        """
        ...

    def discover_files(self) -> list[Path]:
        """Discover all CSV files matching the pattern.

        Returns:
            Sorted list of file paths
        """
        source_path = self.get_source_path()
        pattern = self.get_file_pattern()
        files = glob.glob(str(source_path / pattern))
        return sorted(Path(f) for f in files)

    def get_pending_files(self) -> list[Path]:
        """Get files that haven't been processed yet.

        Returns:
            List of unprocessed file paths
        """
        all_files = self.discover_files()
        if self.state is None:
            return all_files

        all_filenames = [f.name for f in all_files]
        pending_filenames = self.state.get_pending_files(self.symbol, self.data_type, all_filenames)
        return [f for f in all_files if f.name in pending_filenames]

    def process_file(self, file_path: Path) -> list[Any]:
        """Process a single file.

        Args:
            file_path: Path to CSV file

        Returns:
            List of converted NautilusTrader objects
        """
        df = self.parse_csv(file_path)
        df = self.transform(df)
        return self.wrangle(df)

    def process_file_chunked(
        self,
        file_path: Path,
        chunk_size: int | None = None,
    ) -> Generator[list[Any], None, None]:
        """Process a file in chunks for memory efficiency.

        Args:
            file_path: Path to CSV file
            chunk_size: Rows per chunk (default from config)

        Yields:
            Lists of converted NautilusTrader objects
        """
        chunk_size = chunk_size or self.config.chunk_size

        for chunk_df in pd.read_csv(file_path, chunksize=chunk_size):
            transformed = self.transform(chunk_df)
            yield self.wrangle(transformed)

    def process_all(
        self,
        skip_processed: bool = True,
    ) -> Generator[tuple[Path, list[Any]], None, None]:
        """Process all pending files.

        Args:
            skip_processed: If True, skip already processed files

        Yields:
            Tuples of (file_path, converted_objects)
        """
        files = self.get_pending_files() if skip_processed else self.discover_files()

        for file_path in files:
            objects = self.process_file(file_path)
            yield file_path, objects

    def mark_processed(
        self,
        file_path: Path,
        record_count: int,
        first_ts: int,
        last_ts: int,
    ) -> None:
        """Mark a file as processed in state.

        Args:
            file_path: The processed file path
            record_count: Number of records processed
            first_ts: First timestamp (nanoseconds)
            last_ts: Last timestamp (nanoseconds)
        """
        if self.state is not None:
            self.state.mark_file_processed(
                symbol=self.symbol,
                data_type=self.data_type,
                filename=file_path.name,
                record_count=record_count,
                first_timestamp_ns=first_ts,
                last_timestamp_ns=last_ts,
            )
