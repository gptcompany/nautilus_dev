"""Funding rate converter for Binance CSV to NautilusTrader custom data.

Converts Binance funding rate historical data to a NautilusTrader-compatible
custom data type for accurate perpetual futures PnL calculation.
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pandas as pd

from nautilus_trader.core.data import Data
from nautilus_trader.model.identifiers import InstrumentId

from ..config import ConverterConfig
from ..instruments import get_instrument
from ..state import ConversionState
from .base import BaseConverter


@dataclass
class FundingRate(Data):
    """Custom data type for funding rate data.

    Stores periodic funding rate for perpetual futures contracts.
    Compatible with NautilusTrader's ParquetDataCatalog.

    Attributes:
        instrument_id: The instrument identifier
        funding_rate: Funding rate as decimal (e.g., 0.0001 = 0.01%)
        funding_interval_hours: Interval between funding (typically 8)
        ts_event: Funding calculation timestamp (nanoseconds)
        ts_init: Record initialization timestamp (nanoseconds)
    """

    instrument_id: InstrumentId
    funding_rate: Decimal
    funding_interval_hours: int
    ts_event: int
    ts_init: int

    def __post_init__(self) -> None:
        """Validate the funding rate data."""
        if not isinstance(self.instrument_id, InstrumentId):
            raise TypeError(
                f"instrument_id must be InstrumentId, got {type(self.instrument_id)}"
            )
        if not isinstance(self.funding_rate, Decimal):
            raise TypeError(
                f"funding_rate must be Decimal, got {type(self.funding_rate)}"
            )
        if self.ts_event <= 0:
            raise ValueError(f"ts_event must be positive, got {self.ts_event}")
        if self.ts_init <= 0:
            raise ValueError(f"ts_init must be positive, got {self.ts_init}")


class FundingRateConverter(BaseConverter):
    """Converter for Binance funding rate CSV to FundingRate objects."""

    def __init__(
        self,
        symbol: str,
        config: ConverterConfig | None = None,
        state: ConversionState | None = None,
    ) -> None:
        """Initialize the funding rate converter.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            config: Converter configuration
            state: Conversion state for incremental updates
        """
        super().__init__(symbol, config, state)
        self._instrument = get_instrument(symbol)

    @property
    def data_type(self) -> str:
        """Return the data type identifier."""
        return "funding"

    @property
    def instrument(self):
        """Return the instrument."""
        return self._instrument

    def get_source_path(self) -> Path:
        """Return the source directory path for funding rate CSV files."""
        return self.config.get_funding_path(self.symbol)

    def get_file_pattern(self) -> str:
        """Return the glob pattern for funding rate CSV files."""
        return f"{self.symbol}-fundingRate-*.csv"

    def parse_csv(self, file_path: Path) -> pd.DataFrame:
        """Parse a funding rate CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame with raw funding rate data
        """
        return pd.read_csv(file_path)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform raw funding rate CSV to internal format.

        Args:
            df: Raw DataFrame from CSV with columns:
                calc_time (ms), funding_interval_hours, last_funding_rate

        Returns:
            DataFrame with columns: ts_event (ns), funding_interval_hours, funding_rate
        """
        return pd.DataFrame(
            {
                "ts_event": (df["calc_time"] * 1_000_000).astype("int64"),  # ms -> ns
                "funding_interval_hours": df["funding_interval_hours"].astype("int64"),
                "funding_rate": df["last_funding_rate"].astype("float64"),
            }
        )

    def wrangle(self, df: pd.DataFrame) -> list[FundingRate]:
        """Convert DataFrame to FundingRate objects.

        Args:
            df: Transformed DataFrame with funding rate data

        Returns:
            List of FundingRate objects
        """
        funding_rates = []
        instrument_id = self._instrument.id

        for _, row in df.iterrows():
            ts_event = int(row["ts_event"])
            funding_rate = FundingRate(
                instrument_id=instrument_id,
                funding_rate=Decimal(str(row["funding_rate"])),
                funding_interval_hours=int(row["funding_interval_hours"]),
                ts_event=ts_event,
                ts_init=ts_event,  # Same as ts_event for historical data
            )
            funding_rates.append(funding_rate)

        return funding_rates


def convert_funding_rates(
    symbol: str,
    config: ConverterConfig | None = None,
    state: ConversionState | None = None,
    skip_processed: bool = True,
) -> tuple[list[FundingRate], int]:
    """Convert all funding rate files for a symbol.

    Args:
        symbol: Trading symbol
        config: Converter configuration
        state: Conversion state
        skip_processed: Skip already processed files

    Returns:
        Tuple of (all_funding_rates, file_count)
    """
    converter = FundingRateConverter(
        symbol=symbol,
        config=config,
        state=state,
    )

    all_rates: list[FundingRate] = []
    file_count = 0

    for file_path, rates in converter.process_all(skip_processed=skip_processed):
        all_rates.extend(rates)
        file_count += 1

        if rates and state is not None:
            converter.mark_processed(
                file_path=file_path,
                record_count=len(rates),
                first_ts=rates[0].ts_event,
                last_ts=rates[-1].ts_event,
            )

    return all_rates, file_count
