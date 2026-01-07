"""Klines (OHLCV candlestick) converter for Binance CSV to NautilusTrader Bar.

Supports 1m, 5m, 15m timeframes. Transforms Binance klines CSV format to
NautilusTrader Bar objects using V1 BarDataWrangler.
"""

from pathlib import Path
from typing import cast

import pandas as pd
from nautilus_trader.model.data import Bar, BarType

from ..config import ConverterConfig
from ..instruments import get_instrument
from ..state import ConversionState
from ..wrangler_factory import get_bar_wrangler
from .base import BaseConverter

# Map timeframe strings to BarType specification parts
TIMEFRAME_MAP = {
    "1m": "1-MINUTE",
    "5m": "5-MINUTE",
    "15m": "15-MINUTE",
    "1h": "1-HOUR",
    "4h": "4-HOUR",
    "1d": "1-DAY",
}


class KlinesConverter(BaseConverter):
    """Converter for Binance klines CSV to NautilusTrader Bar objects."""

    def __init__(
        self,
        symbol: str,
        timeframe: str = "1m",
        config: ConverterConfig | None = None,
        state: ConversionState | None = None,
    ) -> None:
        """Initialize the klines converter.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            timeframe: Kline timeframe (e.g., "1m", "5m", "15m")
            config: Converter configuration
            state: Conversion state for incremental updates
        """
        super().__init__(symbol, config, state)
        self.timeframe = timeframe
        self._instrument = get_instrument(symbol)
        self._bar_type = self._create_bar_type()
        self._wrangler = get_bar_wrangler(
            bar_type=self._bar_type,
            instrument=self._instrument,
            config=self.config,
        )

    def _create_bar_type(self) -> BarType:
        """Create the BarType for this converter."""
        tf_spec = TIMEFRAME_MAP.get(self.timeframe)
        if tf_spec is None:
            raise ValueError(f"Unsupported timeframe: {self.timeframe}")

        # Format: BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL
        bar_type_str = f"{self._instrument.id}-{tf_spec}-LAST-EXTERNAL"
        return BarType.from_str(bar_type_str)

    @property
    def data_type(self) -> str:
        """Return the data type identifier."""
        return f"klines_{self.timeframe}"

    @property
    def instrument(self):
        """Return the instrument."""
        return self._instrument

    @property
    def bar_type(self) -> BarType:
        """Return the bar type."""
        return self._bar_type

    def get_source_path(self) -> Path:
        """Return the source directory path for klines CSV files."""
        return self.config.get_klines_path(self.symbol, self.timeframe)

    def get_file_pattern(self) -> str:
        """Return the glob pattern for klines CSV files."""
        return f"{self.symbol}-{self.timeframe}-*.csv"

    def parse_csv(self, file_path: Path) -> pd.DataFrame:
        """Parse a klines CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame with raw klines data

        Note:
            Handles both headerless (old) and header (new) Binance CSV formats.
        """
        # Standard Binance klines column names
        column_names = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "count",
            "taker_buy_volume",
            "taker_buy_quote_volume",
            "ignore",
        ]

        # Try reading with header first, check if first row is data or header
        df = pd.read_csv(file_path, header=None, names=column_names)

        # If first row looks like header (has 'open_time' string), skip it
        if df.iloc[0]["open_time"] == "open_time":
            df = df.iloc[1:].reset_index(drop=True)

        # Convert numeric columns
        for col in ["open_time", "open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw klines CSV to wrangler format.

        Args:
            df: Raw DataFrame from CSV with columns:
                open_time, open, high, low, close, volume, close_time,
                quote_volume, count, taker_buy_volume, taker_buy_quote_volume, ignore

        Returns:
            DataFrame formatted for BarDataWrangler with DatetimeIndex (UTC)
            and columns: open, high, low, close, volume
        """
        # Create DataFrame with required columns
        # Note: Use .values to avoid pandas index alignment issues
        bar_df = pd.DataFrame(
            {
                "open": df["open"].values.astype("float64"),
                "high": df["high"].values.astype("float64"),
                "low": df["low"].values.astype("float64"),
                "close": df["close"].values.astype("float64"),
                "volume": df["volume"].values.astype("float64"),
            },
        )
        bar_df.index = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        return bar_df

    def wrangle(self, df: pd.DataFrame) -> list[Bar]:
        """Convert DataFrame to Bar objects using V1 wrangler.

        Args:
            df: Transformed DataFrame with OHLCV data

        Returns:
            List of Bar objects
        """
        return cast(list[Bar], self._wrangler.process(df))


def convert_klines(
    symbol: str,
    timeframe: str = "1m",
    config: ConverterConfig | None = None,
    state: ConversionState | None = None,
    skip_processed: bool = True,
) -> tuple[list[Bar], int]:
    """Convert all klines files for a symbol.

    Args:
        symbol: Trading symbol
        timeframe: Kline timeframe
        config: Converter configuration
        state: Conversion state
        skip_processed: Skip already processed files

    Returns:
        Tuple of (all_bars, file_count)
    """
    converter = KlinesConverter(
        symbol=symbol,
        timeframe=timeframe,
        config=config,
        state=state,
    )

    all_bars: list[Bar] = []
    file_count = 0

    for file_path, bars in converter.process_all(skip_processed=skip_processed):
        all_bars.extend(bars)
        file_count += 1

        if bars and state is not None:
            converter.mark_processed(
                file_path=file_path,
                record_count=len(bars),
                first_ts=bars[0].ts_event,
                last_ts=bars[-1].ts_event,
            )

    return all_bars, file_count
