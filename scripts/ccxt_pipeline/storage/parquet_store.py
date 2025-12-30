"""Parquet storage for CCXT pipeline data."""

from datetime import datetime
from pathlib import Path
from typing import TypeVar

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.ccxt_pipeline.models import FundingRate, Liquidation, OpenInterest
from scripts.ccxt_pipeline.utils.logging import get_logger

T = TypeVar("T", OpenInterest, FundingRate, Liquidation)
logger = get_logger("storage")


class ParquetStore:
    """Parquet-based storage for pipeline data.

    Stores data in a directory structure compatible with NautilusTrader:
    {catalog_path}/{data_type}/{symbol}.{venue}/{date}.parquet
    """

    def __init__(self, catalog_path: Path) -> None:
        """Initialize the Parquet store.

        Args:
            catalog_path: Root path for the data catalog.
        """
        self.catalog_path = Path(catalog_path)
        self.catalog_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized ParquetStore at {self.catalog_path}")

    def _get_data_type_name(self, data_type: type[T]) -> str:
        """Get directory name for a data type."""
        return {
            OpenInterest: "open_interest",
            FundingRate: "funding_rate",
            Liquidation: "liquidations",
        }.get(data_type, data_type.__name__.lower())

    def _get_schema(self, data_type: type[T]) -> pa.Schema:
        """Get PyArrow schema for a data type."""
        if data_type == OpenInterest:
            return pa.schema(
                [
                    ("timestamp", pa.timestamp("us", tz="UTC")),
                    ("symbol", pa.string()),
                    ("venue", pa.string()),
                    ("open_interest", pa.float64()),
                    ("open_interest_value", pa.float64()),
                ]
            )
        elif data_type == FundingRate:
            return pa.schema(
                [
                    ("timestamp", pa.timestamp("us", tz="UTC")),
                    ("symbol", pa.string()),
                    ("venue", pa.string()),
                    ("funding_rate", pa.float64()),
                    ("next_funding_time", pa.timestamp("us", tz="UTC")),
                    ("predicted_rate", pa.float64()),
                ]
            )
        elif data_type == Liquidation:
            return pa.schema(
                [
                    ("timestamp", pa.timestamp("us", tz="UTC")),
                    ("symbol", pa.string()),
                    ("venue", pa.string()),
                    ("side", pa.string()),
                    ("quantity", pa.float64()),
                    ("price", pa.float64()),
                    ("value", pa.float64()),
                ]
            )
        raise ValueError(f"Unknown data type: {data_type}")

    def _get_partition_path(self, data_type: type[T], symbol: str, venue: str) -> Path:
        """Get the partition path for a symbol/venue combination."""
        type_name = self._get_data_type_name(data_type)
        return self.catalog_path / type_name / f"{symbol}.{venue}"

    def _get_file_path(self, data_type: type[T], symbol: str, venue: str, date: datetime) -> Path:
        """Get the file path for a specific date."""
        partition = self._get_partition_path(data_type, symbol, venue)
        return partition / f"{date.strftime('%Y-%m-%d')}.parquet"

    def write(self, data: list[T]) -> None:
        """Write data to Parquet files, partitioned by date.

        Args:
            data: List of data points (must be same type).
        """
        if not data:
            return

        data_type = type(data[0])
        schema = self._get_schema(data_type)

        # Group by symbol, venue, and date
        from collections import defaultdict

        groups: dict[tuple[str, str, str], list[T]] = defaultdict(list)

        for item in data:
            date_str = item.timestamp.strftime("%Y-%m-%d")
            venue = item.venue.value if hasattr(item.venue, "value") else str(item.venue)
            groups[(item.symbol, venue, date_str)].append(item)

        # Write each group to its own file
        for (symbol, venue, date_str), group in groups.items():
            file_path = self._get_partition_path(data_type, symbol, venue) / f"{date_str}.parquet"
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to records
            records = []
            for item in group:
                record = item.model_dump()
                record["venue"] = (
                    item.venue.value if hasattr(item.venue, "value") else str(item.venue)
                )
                if hasattr(item, "side") and hasattr(item.side, "value"):
                    record["side"] = item.side.value
                records.append(record)

            table = pa.Table.from_pylist(records, schema=schema)

            if file_path.exists():
                existing = pq.read_table(file_path)
                table = pa.concat_tables([existing, table])

            pq.write_table(table, file_path)
            logger.debug(f"Wrote {len(group)} records to {file_path}")

    def read(
        self,
        data_type: type[T],
        symbol: str,
        venue: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict]:
        """Read data from Parquet files.

        Args:
            data_type: Type of data to read.
            symbol: Trading pair symbol.
            venue: Exchange name (optional, if None reads from all venues).
            start: Start datetime filter.
            end: End datetime filter.

        Returns:
            List of data records as dictionaries.
        """
        tables = []
        type_name = self._get_data_type_name(data_type)
        type_dir = self.catalog_path / type_name

        if not type_dir.exists():
            return []

        if venue:
            # Read from specific venue
            partition = self._get_partition_path(data_type, symbol, venue)
            if partition.exists():
                for file_path in sorted(partition.glob("*.parquet")):
                    tables.append(pq.read_table(file_path))
        else:
            # Read from all venues for this symbol
            for partition in type_dir.glob(f"{symbol}.*"):
                if partition.is_dir():
                    for file_path in sorted(partition.glob("*.parquet")):
                        tables.append(pq.read_table(file_path))

        if not tables:
            return []

        table = pa.concat_tables(tables)
        df = table.to_pandas()

        if start:
            df = df[df["timestamp"] >= start]
        if end:
            df = df[df["timestamp"] <= end]

        return df.to_dict("records")

    def get_last_timestamp(self, data_type: type[T], symbol: str, venue: str) -> datetime | None:
        """Get the most recent timestamp for a symbol/venue.

        Args:
            data_type: Type of data.
            symbol: Trading pair symbol.
            venue: Exchange name.

        Returns:
            Most recent timestamp or None if no data exists.
        """
        partition = self._get_partition_path(data_type, symbol, venue)

        if not partition.exists():
            return None

        files = sorted(partition.glob("*.parquet"), reverse=True)
        if not files:
            return None

        table = pq.read_table(files[0])
        if table.num_rows == 0:
            return None

        timestamps = table.column("timestamp").to_pylist()
        return max(timestamps) if timestamps else None
