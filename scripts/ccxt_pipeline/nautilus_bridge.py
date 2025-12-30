"""Bridge to convert CCXT pipeline data to NautilusTrader catalog format.

Converts FundingRate data from CCXT Parquet format to NautilusTrader's
native FundingRateUpdate type for use in backtesting.
"""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from nautilus_trader.model.data import FundingRateUpdate
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.persistence.catalog import ParquetDataCatalog


def _symbol_to_instrument_id(symbol: str, venue: str) -> InstrumentId:
    """Convert CCXT symbol to NautilusTrader InstrumentId.

    Args:
        symbol: CCXT symbol (e.g., "BTCUSDT-PERP")
        venue: Venue name (e.g., "BINANCE")

    Returns:
        InstrumentId in NautilusTrader format
    """
    # Convert BTCUSDT-PERP to BTCUSDT-PERP.BINANCE
    return InstrumentId.from_str(f"{symbol}.{venue}")


def convert_funding_rates(
    ccxt_catalog_path: Path | str,
    nautilus_catalog_path: Path | str,
    symbol: str | None = None,
    venue: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> int:
    """Convert CCXT funding rate data to NautilusTrader catalog.

    Args:
        ccxt_catalog_path: Path to CCXT data catalog
        nautilus_catalog_path: Path to NautilusTrader catalog
        symbol: Optional symbol filter (e.g., "BTCUSDT-PERP")
        venue: Optional venue filter (e.g., "BINANCE")
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Number of FundingRateUpdate records written
    """
    ccxt_path = Path(ccxt_catalog_path)
    nautilus_path = Path(nautilus_catalog_path)

    funding_path = ccxt_path / "funding_rate"
    if not funding_path.exists():
        raise FileNotFoundError(f"Funding rate data not found: {funding_path}")

    # Find all parquet files
    pattern = "*.parquet"
    all_files = list(funding_path.rglob(pattern))

    if not all_files:
        print("No funding rate files found")
        return 0

    # Filter by symbol/venue if specified
    if symbol or venue:
        filtered = []
        for f in all_files:
            # Path format: funding_rate/BTCUSDT-PERP.BINANCE/2025-12-27.parquet
            dir_name = f.parent.name  # e.g., "BTCUSDT-PERP.BINANCE"
            parts = dir_name.rsplit(".", 1)
            if len(parts) == 2:
                file_symbol, file_venue = parts
                if symbol and file_symbol != symbol:
                    continue
                if venue and file_venue != venue:
                    continue
            filtered.append(f)
        all_files = filtered

    # Import Arrow serialization registration
    from strategies.binance2nautilus.catalog import _register_funding_rate_arrow

    _register_funding_rate_arrow()

    # Create NautilusTrader catalog
    nautilus_catalog = ParquetDataCatalog(str(nautilus_path))

    total_records = 0

    for file_path in sorted(all_files):
        # Parse directory name for symbol/venue
        dir_name = file_path.parent.name
        parts = dir_name.rsplit(".", 1)
        if len(parts) != 2:
            print(f"Skipping invalid path: {file_path}")
            continue

        file_symbol, file_venue = parts

        # Read parquet file
        table = pq.read_table(file_path)
        df = table.to_pandas()

        if df.empty:
            continue

        # Filter by date if specified
        if start_date:
            start_ts = start_date.replace(tzinfo=timezone.utc)
            df = df[df["timestamp"] >= start_ts]
        if end_date:
            end_ts = end_date.replace(tzinfo=timezone.utc)
            df = df[df["timestamp"] <= end_ts]

        if df.empty:
            continue

        # Convert to FundingRateUpdate objects
        instrument_id = _symbol_to_instrument_id(file_symbol, file_venue)

        funding_updates = []
        for _, row in df.iterrows():
            ts_event = int(row["timestamp"].value)  # nanoseconds

            # Handle next_funding_time
            next_funding_ns = None
            if pd.notna(row.get("next_funding_time")):
                next_funding_ns = int(row["next_funding_time"].value)

            # Handle NaN funding rate
            rate = row["funding_rate"]
            if pd.isna(rate):
                continue

            funding_updates.append(
                FundingRateUpdate(
                    instrument_id=instrument_id,
                    rate=Decimal(str(rate)),
                    ts_event=ts_event,
                    ts_init=ts_event,
                    next_funding_ns=next_funding_ns,
                )
            )

        if funding_updates:
            nautilus_catalog.write_data(funding_updates)
            total_records += len(funding_updates)
            print(f"Wrote {len(funding_updates)} records from {file_path.name} ({file_symbol})")

    return total_records


def main():
    """CLI for converting CCXT data to NautilusTrader catalog."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert CCXT pipeline data to NautilusTrader catalog"
    )
    parser.add_argument(
        "--ccxt-catalog",
        type=str,
        default="/media/sam/1TB/nautilus_dev/data/ccxt_catalog",
        help="Path to CCXT data catalog",
    )
    parser.add_argument(
        "--nautilus-catalog",
        type=str,
        default="/media/sam/2TB-NVMe/nautilus_catalog_v1222",
        help="Path to NautilusTrader catalog",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Filter by symbol (e.g., BTCUSDT-PERP)",
    )
    parser.add_argument(
        "--venue",
        type=str,
        help="Filter by venue (e.g., BINANCE)",
    )

    args = parser.parse_args()

    print(f"Converting funding rates from {args.ccxt_catalog}")
    print(f"Target catalog: {args.nautilus_catalog}")

    count = convert_funding_rates(
        ccxt_catalog_path=args.ccxt_catalog,
        nautilus_catalog_path=args.nautilus_catalog,
        symbol=args.symbol,
        venue=args.venue,
    )

    print(f"\nTotal records converted: {count}")


if __name__ == "__main__":
    main()
