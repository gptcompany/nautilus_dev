"""Parquet Converter for Audit Trail (Spec 030).

This module converts JSONL audit logs to partitioned Parquet files for
efficient querying with DuckDB. Implements 90-day retention policy.

Key features:
- JSONL → Parquet conversion
- Date-partitioned output (year/month/day)
- 90-day retention policy with automatic cleanup
- Batch processing for efficiency
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


class ParquetConverter:
    """Convert JSONL audit logs to partitioned Parquet files.

    This class handles the conversion from hot-path JSONL logs to
    cold-path Parquet files optimized for DuckDB queries.

    Attributes:
        hot_path: Path to JSONL audit logs.
        cold_path: Path to Parquet output directory.
        retention_days: How many days of data to retain.

    Example:
        >>> converter = ParquetConverter(
        ...     hot_path=Path("./data/audit/hot"),
        ...     cold_path=Path("./data/audit/cold"),
        ...     retention_days=90,
        ... )
        >>> converter.convert_all()
        >>> converter.apply_retention()
    """

    def __init__(
        self,
        hot_path: Path,
        cold_path: Path,
        retention_days: int = 90,
    ) -> None:
        """Initialize the ParquetConverter.

        Args:
            hot_path: Path to JSONL audit logs (hot tier).
            cold_path: Path to Parquet output directory (cold tier).
            retention_days: How many days of data to retain.
        """
        self.hot_path = Path(hot_path)
        self.cold_path = Path(cold_path)
        self.retention_days = retention_days

        # Ensure directories exist
        self.cold_path.mkdir(parents=True, exist_ok=True)

    def convert_file(self, jsonl_file: Path) -> Path | None:
        """Convert a single JSONL file to Parquet.

        Args:
            jsonl_file: Path to JSONL file.

        Returns:
            Path to created Parquet file, or None if conversion failed.
        """
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            logger.error("pyarrow not installed. Run: pip install pyarrow")
            return None

        events = list(self._read_jsonl(jsonl_file))
        if not events:
            logger.warning(f"No events in {jsonl_file}")
            return None

        # Group events by date (using UTC to ensure consistent partitioning)
        events_by_date: dict[str, list[dict]] = {}
        for event in events:
            ts_ns = event.get("ts_event", 0)
            # Use UTC timezone for consistent date partitioning across systems
            dt = datetime.fromtimestamp(ts_ns / 1_000_000_000, tz=timezone.utc)
            date_key = dt.strftime("%Y/%m/%d")

            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append(event)

        # Write partitioned Parquet files
        output_paths = []
        for date_key, date_events in events_by_date.items():
            output_dir = self.cold_path / date_key
            output_dir.mkdir(parents=True, exist_ok=True)

            output_file = output_dir / f"audit_{jsonl_file.stem}.parquet"

            # Create table from events
            table = pa.Table.from_pylist(date_events)
            pq.write_table(table, output_file)

            output_paths.append(output_file)
            logger.debug(f"Converted {len(date_events)} events to {output_file}")

        return output_paths[0] if output_paths else None

    def convert_all(self) -> int:
        """Convert all JSONL files in hot path to Parquet.

        Returns:
            Number of files converted.
        """
        converted = 0
        for jsonl_file in self.hot_path.glob("*.jsonl"):
            if self.convert_file(jsonl_file):
                converted += 1

        logger.info(f"Converted {converted} JSONL files to Parquet")
        return converted

    def apply_retention(self) -> int:
        """Apply retention policy, deleting old Parquet files.

        Returns:
            Number of directories deleted.
        """
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted = 0

        # Find all year directories
        for year_dir in self.cold_path.iterdir():
            if not year_dir.is_dir():
                continue

            try:
                year = int(year_dir.name)
            except ValueError:
                continue

            # Find all month directories
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue

                try:
                    month = int(month_dir.name)
                except ValueError:
                    continue

                # Find all day directories
                for day_dir in month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue

                    try:
                        day = int(day_dir.name)
                        dir_date = datetime(year, month, day)
                    except ValueError:
                        continue

                    # Delete if older than retention
                    if dir_date < cutoff_date:
                        import shutil

                        shutil.rmtree(day_dir)
                        deleted += 1
                        logger.debug(f"Deleted old partition: {day_dir}")

        logger.info(
            f"Retention applied: deleted {deleted} partitions older than {self.retention_days} days"
        )
        return deleted

    def get_partition_stats(self) -> dict:
        """Get statistics about partitioned data.

        Returns:
            Dictionary with partition statistics.
        """
        try:
            import pyarrow.parquet as pq
        except ImportError:
            return {"error": "pyarrow not installed"}

        stats = {
            "total_files": 0,
            "total_rows": 0,
            "total_bytes": 0,
            "partitions": [],
            "oldest_date": None,
            "newest_date": None,
        }

        for parquet_file in self.cold_path.rglob("*.parquet"):
            stats["total_files"] += 1
            stats["total_bytes"] += parquet_file.stat().st_size

            # Get row count from metadata
            metadata = pq.read_metadata(parquet_file)
            stats["total_rows"] += metadata.num_rows

            # Extract date from path
            parts = parquet_file.relative_to(self.cold_path).parts
            if len(parts) >= 3:
                date_str = "/".join(parts[:3])
                if date_str not in stats["partitions"]:
                    stats["partitions"].append(date_str)

        if stats["partitions"]:
            stats["partitions"].sort()
            stats["oldest_date"] = stats["partitions"][0]
            stats["newest_date"] = stats["partitions"][-1]

        return stats

    def _read_jsonl(self, path: Path) -> Iterator[dict]:
        """Read JSONL file and yield events.

        Args:
            path: Path to JSONL file.

        Yields:
            Event dictionaries.
        """
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in {path}: {e}")
                    continue
