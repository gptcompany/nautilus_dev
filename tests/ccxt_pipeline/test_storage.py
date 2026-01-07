"""Unit tests for storage."""

from datetime import datetime, timedelta, timezone
from pathlib import Path


from scripts.ccxt_pipeline.models import OpenInterest, Venue
from scripts.ccxt_pipeline.storage.parquet_store import ParquetStore


class TestParquetStore:
    """Tests for ParquetStore."""

    def test_init_creates_directory(self, temp_catalog_path: Path) -> None:
        """Test that init creates the catalog directory."""
        store = ParquetStore(temp_catalog_path)
        assert store.catalog_path.exists()

    def test_write_open_interest(
        self, parquet_store: ParquetStore, sample_open_interest: OpenInterest
    ) -> None:
        """Test writing OpenInterest data."""
        parquet_store.write([sample_open_interest])

        partition = (
            parquet_store.catalog_path
            / "open_interest"
            / f"{sample_open_interest.symbol}.{sample_open_interest.venue.value}"
        )
        assert partition.exists()
        assert len(list(partition.glob("*.parquet"))) == 1

    def test_read_open_interest(
        self, parquet_store: ParquetStore, sample_open_interest: OpenInterest
    ) -> None:
        """Test reading OpenInterest data."""
        parquet_store.write([sample_open_interest])

        records = parquet_store.read(
            OpenInterest,
            sample_open_interest.symbol,
            sample_open_interest.venue.value,
        )

        assert len(records) == 1
        assert records[0]["symbol"] == sample_open_interest.symbol
        assert records[0]["open_interest"] == sample_open_interest.open_interest

    def test_read_with_date_filter(
        self, parquet_store: ParquetStore, multiple_open_interests: list[OpenInterest]
    ) -> None:
        """Test reading with date range filter."""
        oi = multiple_open_interests[0]
        parquet_store.write([oi])

        start = oi.timestamp - timedelta(hours=1)
        end = oi.timestamp + timedelta(hours=1)

        records = parquet_store.read(
            OpenInterest,
            oi.symbol,
            oi.venue.value,
            start=start,
            end=end,
        )

        assert len(records) == 1

    def test_read_nonexistent_returns_empty(self, parquet_store: ParquetStore) -> None:
        """Test reading nonexistent data returns empty list."""
        records = parquet_store.read(OpenInterest, "NONEXISTENT", "BINANCE")
        assert records == []

    def test_get_last_timestamp(
        self, parquet_store: ParquetStore, sample_open_interest: OpenInterest
    ) -> None:
        """Test getting the last timestamp."""
        parquet_store.write([sample_open_interest])

        last_ts = parquet_store.get_last_timestamp(
            OpenInterest,
            sample_open_interest.symbol,
            sample_open_interest.venue.value,
        )

        assert last_ts is not None
        assert last_ts == sample_open_interest.timestamp

    def test_get_last_timestamp_nonexistent(self, parquet_store: ParquetStore) -> None:
        """Test getting last timestamp for nonexistent data."""
        last_ts = parquet_store.get_last_timestamp(OpenInterest, "NONEXISTENT", "BINANCE")
        assert last_ts is None

    def test_write_multiple_records_same_date(self, parquet_store: ParquetStore) -> None:
        """Test writing multiple records for the same date."""
        base_time = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        records = [
            OpenInterest(
                timestamp=base_time + timedelta(minutes=i * 5),
                symbol="BTCUSDT-PERP",
                venue=Venue.BINANCE,
                open_interest=100.0 + i,
                open_interest_value=10000.0 + i * 100,
            )
            for i in range(5)
        ]

        parquet_store.write(records)

        read_records = parquet_store.read(OpenInterest, "BTCUSDT-PERP", "BINANCE")
        assert len(read_records) == 5

    def test_write_appends_to_existing(
        self, parquet_store: ParquetStore, sample_open_interest: OpenInterest
    ) -> None:
        """Test that writing appends to existing data."""
        parquet_store.write([sample_open_interest])

        new_oi = OpenInterest(
            timestamp=sample_open_interest.timestamp + timedelta(minutes=5),
            symbol=sample_open_interest.symbol,
            venue=sample_open_interest.venue,
            open_interest=sample_open_interest.open_interest + 100,
            open_interest_value=sample_open_interest.open_interest_value + 10000,
        )
        parquet_store.write([new_oi])

        records = parquet_store.read(
            OpenInterest,
            sample_open_interest.symbol,
            sample_open_interest.venue.value,
        )
        assert len(records) == 2

    def test_write_empty_list(self, parquet_store: ParquetStore) -> None:
        """Test that writing empty list does nothing."""
        parquet_store.write([])
        # Should not create any directories
        assert len(list(parquet_store.catalog_path.iterdir())) == 0

    def test_multiple_venues(
        self, parquet_store: ParquetStore, multiple_open_interests: list[OpenInterest]
    ) -> None:
        """Test storing data from multiple venues."""
        parquet_store.write(multiple_open_interests)

        oi_dir = parquet_store.catalog_path / "open_interest"
        assert oi_dir.exists()

        # Should have 3 venue directories
        venue_dirs = list(oi_dir.iterdir())
        assert len(venue_dirs) == 3
