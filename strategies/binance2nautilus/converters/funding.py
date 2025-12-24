"""Funding rate converter for Binance CSV to NautilusTrader FundingRateUpdate.

Converts Binance funding rate historical data to NautilusTrader's native
FundingRateUpdate type for accurate perpetual futures PnL calculation.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from ..config import ConverterConfig
from ..instruments import get_instrument
from ..state import ConversionState
from .base import BaseConverter

if TYPE_CHECKING:
    from nautilus_trader.model.data import FundingRateUpdate


class FundingRateConverter(BaseConverter):
    """Converter for Binance funding rate CSV to FundingRateUpdate objects."""

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

        Note:
            Timestamps beyond year 2500 are filtered out as they exceed
            NautilusTrader's uint64 nanosecond limit.
        """
        # Max valid timestamp in milliseconds (year 2500, well under uint64 limit)
        # uint64 max in ns = 18446744073709551615 ns = year ~2554
        # We use year 2500 for safety margin
        max_valid_ms = 16725225600000  # Year 2500

        # Filter out invalid timestamps (beyond year 2500)
        valid_mask = df["calc_time"] <= max_valid_ms
        df_valid = df[valid_mask]

        if len(df_valid) < len(df):
            import logging

            logger = logging.getLogger(__name__)
            skipped = len(df) - len(df_valid)
            logger.warning(
                f"Skipped {skipped} records with timestamps beyond year 2500"
            )

        return pd.DataFrame(
            {
                "ts_event": (df_valid["calc_time"] * 1_000_000).astype(
                    "int64"
                ),  # ms -> ns
                "funding_interval_hours": df_valid["funding_interval_hours"].astype(
                    "int64"
                ),
                "funding_rate": df_valid["last_funding_rate"].astype("float64"),
            }
        )

    def wrangle(self, df: pd.DataFrame) -> list[FundingRateUpdate]:
        """Convert DataFrame to FundingRateUpdate objects.

        Uses vectorized operations for performance (avoids df.iterrows()).

        Args:
            df: Transformed DataFrame with funding rate data

        Returns:
            List of FundingRateUpdate objects
        """
        from nautilus_trader.model.data import FundingRateUpdate

        instrument_id = self._instrument.id

        # Vectorized extraction of arrays
        ts_events = df["ts_event"].to_numpy()
        funding_rates_raw = df["funding_rate"].to_numpy()
        interval_hours = df["funding_interval_hours"].to_numpy()

        # Max uint64 for nanosecond timestamps (approx year 2554)
        max_uint64 = 18446744073709551615

        # Build list using list comprehension (faster than iterrows)
        funding_rates = []
        for ts_event, rate, interval_hr in zip(
            ts_events, funding_rates_raw, interval_hours, strict=True
        ):
            ts_event_int = int(ts_event)
            next_funding = ts_event_int + int(interval_hr * 3600 * 1_000_000_000)

            # Clamp next_funding to max uint64 to prevent overflow
            if next_funding > max_uint64:
                next_funding = max_uint64

            funding_rates.append(
                FundingRateUpdate(
                    instrument_id=instrument_id,
                    rate=Decimal(str(rate)),
                    ts_event=ts_event_int,
                    ts_init=ts_event_int,
                    next_funding_ns=next_funding,
                )
            )

        return funding_rates


def convert_funding_rates(
    symbol: str,
    config: ConverterConfig | None = None,
    state: ConversionState | None = None,
    skip_processed: bool = True,
) -> tuple[list["FundingRateUpdate"], int]:
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

    all_rates: list[FundingRateUpdate] = []
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
