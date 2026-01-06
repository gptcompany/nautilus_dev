"""Unit tests for ParquetConverter (Spec 030).

Tests:
- JSONL to Parquet conversion
- Date partitioning
- Retention policy
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest


class TestParquetConverter:
    """Tests for ParquetConverter."""

    def test_convert_single_file(self):
        """Test converting a single JSONL file."""
        pytest.importorskip("pyarrow")

        from strategies.common.audit.converter import ParquetConverter

        with tempfile.TemporaryDirectory() as tmpdir:
            hot_path = Path(tmpdir) / "hot"
            cold_path = Path(tmpdir) / "cold"
            hot_path.mkdir()
            cold_path.mkdir()

            # Create test JSONL file
            jsonl_file = hot_path / "audit_20260105.jsonl"
            events = [
                {
                    "ts_event": 1736121600000000000,  # 2025-01-06
                    "event_type": "param.state_change",
                    "source": "meta_controller",
                    "trader_id": "TRADER-001",
                    "sequence": 0,
                    "param_name": "system_state",
                    "old_value": "VENTRAL",
                    "new_value": "SYMPATHETIC",
                },
                {
                    "ts_event": 1736121601000000000,
                    "event_type": "param.k_change",
                    "source": "sops_sizer",
                    "trader_id": "TRADER-001",
                    "sequence": 1,
                    "param_name": "adaptive_k",
                    "old_value": "1.0",
                    "new_value": "0.8",
                },
            ]

            with open(jsonl_file, "w") as f:
                for event in events:
                    f.write(json.dumps(event) + "\n")

            # Convert
            converter = ParquetConverter(hot_path, cold_path)
            result = converter.convert_file(jsonl_file)

            assert result is not None
            assert result.exists()
            assert result.suffix == ".parquet"

    def test_date_partitioning(self):
        """Test that events are partitioned by date."""
        pytest.importorskip("pyarrow")

        from strategies.common.audit.converter import ParquetConverter

        with tempfile.TemporaryDirectory() as tmpdir:
            hot_path = Path(tmpdir) / "hot"
            cold_path = Path(tmpdir) / "cold"
            hot_path.mkdir()
            cold_path.mkdir()

            # Create events from different dates
            jsonl_file = hot_path / "multi_day.jsonl"
            events = [
                {
                    "ts_event": 1736035200000000000,  # 2025-01-05
                    "event_type": "param.state_change",
                    "source": "test",
                    "trader_id": "TRADER-001",
                    "sequence": 0,
                },
                {
                    "ts_event": 1736121600000000000,  # 2025-01-06
                    "event_type": "param.state_change",
                    "source": "test",
                    "trader_id": "TRADER-001",
                    "sequence": 1,
                },
            ]

            with open(jsonl_file, "w") as f:
                for event in events:
                    f.write(json.dumps(event) + "\n")

            converter = ParquetConverter(hot_path, cold_path)
            converter.convert_file(jsonl_file)

            # Check partitions exist
            parquet_files = list(cold_path.rglob("*.parquet"))
            assert len(parquet_files) >= 1  # At least one partition

    def test_retention_policy(self):
        """Test retention policy deletes old partitions."""
        pytest.importorskip("pyarrow")

        from strategies.common.audit.converter import ParquetConverter

        with tempfile.TemporaryDirectory() as tmpdir:
            cold_path = Path(tmpdir) / "cold"

            # Create old partition (100 days ago)
            old_date = datetime.now() - timedelta(days=100)
            old_partition = cold_path / old_date.strftime("%Y/%m/%d")
            old_partition.mkdir(parents=True)
            (old_partition / "test.parquet").touch()

            # Create recent partition (5 days ago)
            recent_date = datetime.now() - timedelta(days=5)
            recent_partition = cold_path / recent_date.strftime("%Y/%m/%d")
            recent_partition.mkdir(parents=True)
            (recent_partition / "test.parquet").touch()

            converter = ParquetConverter(
                hot_path=Path(tmpdir) / "hot",
                cold_path=cold_path,
                retention_days=90,
            )

            deleted = converter.apply_retention()

            # Old partition should be deleted
            assert not old_partition.exists()
            # Recent partition should remain
            assert recent_partition.exists()
            assert deleted == 1

    def test_convert_all(self):
        """Test converting all JSONL files."""
        pytest.importorskip("pyarrow")

        from strategies.common.audit.converter import ParquetConverter

        with tempfile.TemporaryDirectory() as tmpdir:
            hot_path = Path(tmpdir) / "hot"
            cold_path = Path(tmpdir) / "cold"
            hot_path.mkdir()
            cold_path.mkdir()

            # Create multiple JSONL files
            for i in range(3):
                jsonl_file = hot_path / f"audit_{i}.jsonl"
                event = {
                    "ts_event": 1736121600000000000 + i * 1000000000,
                    "event_type": "param.state_change",
                    "source": "test",
                    "trader_id": "TRADER-001",
                    "sequence": i,
                }
                with open(jsonl_file, "w") as f:
                    f.write(json.dumps(event) + "\n")

            converter = ParquetConverter(hot_path, cold_path)
            converted = converter.convert_all()

            assert converted == 3

    def test_empty_file(self):
        """Test handling of empty JSONL file."""
        pytest.importorskip("pyarrow")

        from strategies.common.audit.converter import ParquetConverter

        with tempfile.TemporaryDirectory() as tmpdir:
            hot_path = Path(tmpdir) / "hot"
            cold_path = Path(tmpdir) / "cold"
            hot_path.mkdir()
            cold_path.mkdir()

            # Create empty file
            (hot_path / "empty.jsonl").touch()

            converter = ParquetConverter(hot_path, cold_path)
            result = converter.convert_file(hot_path / "empty.jsonl")

            assert result is None

    def test_partition_stats(self):
        """Test getting partition statistics."""
        pytest.importorskip("pyarrow")
        import pyarrow as pa
        import pyarrow.parquet as pq

        from strategies.common.audit.converter import ParquetConverter

        with tempfile.TemporaryDirectory() as tmpdir:
            cold_path = Path(tmpdir) / "cold"

            # Create a test parquet file
            partition = cold_path / "2026/01/06"
            partition.mkdir(parents=True)

            table = pa.Table.from_pylist(
                [
                    {"ts_event": 1736121600000000000, "event_type": "test"},
                    {"ts_event": 1736121601000000000, "event_type": "test"},
                ]
            )
            pq.write_table(table, partition / "test.parquet")

            converter = ParquetConverter(
                hot_path=Path(tmpdir) / "hot",
                cold_path=cold_path,
            )

            stats = converter.get_partition_stats()

            assert stats["total_files"] == 1
            assert stats["total_rows"] == 2
            assert "2026/01/06" in stats["partitions"]
