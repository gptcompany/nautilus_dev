"""Unit tests for AuditQuery (Spec 030).

Tests:
- Time-range queries
- Event type filtering
- Aggregation queries
- Incident reconstruction
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest


class TestAuditQuery:
    """Tests for AuditQuery."""

    @pytest.fixture
    def sample_data(self):
        """Create sample Parquet data for testing."""
        pytest.importorskip("pyarrow")
        pytest.importorskip("duckdb")

        import pyarrow as pa
        import pyarrow.parquet as pq

        with tempfile.TemporaryDirectory() as tmpdir:
            cold_path = Path(tmpdir) / "cold"

            # Create test data for 2026-01-06
            partition = cold_path / "2026/01/06"
            partition.mkdir(parents=True)

            # 2026-01-06 00:00:00 UTC = 1767657600 seconds = 1767657600000000000 ns
            events = [
                {
                    "ts_event": 1767657600000000000,  # 2026-01-06 00:00:00 UTC
                    "event_type": "param.state_change",
                    "source": "meta_controller",
                    "trader_id": "TRADER-001",
                    "sequence": 0,
                    "param_name": "system_state",
                    "old_value": "VENTRAL",
                    "new_value": "SYMPATHETIC",
                    "checksum": "abc123",
                },
                {
                    "ts_event": 1767657660000000000,  # +60s
                    "event_type": "param.k_change",
                    "source": "sops_sizer",
                    "trader_id": "TRADER-001",
                    "sequence": 1,
                    "param_name": "adaptive_k",
                    "old_value": "1.0",
                    "new_value": "0.8",
                    "checksum": "def456",
                },
                {
                    "ts_event": 1767657720000000000,  # +120s
                    "event_type": "trade.fill",
                    "source": "nautilus_trader",
                    "trader_id": "TRADER-001",
                    "sequence": 2,
                    "order_id": "O-001",
                    "checksum": "ghi789",
                },
            ]

            table = pa.Table.from_pylist(events)
            pq.write_table(table, partition / "test.parquet")

            yield cold_path

    def test_query_time_range(self, sample_data):
        """Test querying events in a time range."""
        from strategies.common.audit.query import AuditQuery

        query = AuditQuery(cold_path=sample_data)

        start = datetime(2026, 1, 6, 0, 0, 0)
        end = datetime(2026, 1, 6, 23, 59, 59)

        events = query.query_time_range(start, end)

        assert len(events) == 3
        assert events[0]["event_type"] == "param.state_change"
        assert events[1]["event_type"] == "param.k_change"
        assert events[2]["event_type"] == "trade.fill"

        query.close()

    def test_filter_by_event_type(self, sample_data):
        """Test filtering by event type."""
        from strategies.common.audit.query import AuditQuery

        query = AuditQuery(cold_path=sample_data)

        start = datetime(2026, 1, 6, 0, 0, 0)
        end = datetime(2026, 1, 6, 23, 59, 59)

        events = query.query_time_range(start, end, event_type="param.state_change")

        assert len(events) == 1
        assert events[0]["event_type"] == "param.state_change"

        query.close()

    def test_filter_by_source(self, sample_data):
        """Test filtering by source component."""
        from strategies.common.audit.query import AuditQuery

        query = AuditQuery(cold_path=sample_data)

        start = datetime(2026, 1, 6, 0, 0, 0)
        end = datetime(2026, 1, 6, 23, 59, 59)

        events = query.query_time_range(start, end, source="meta_controller")

        assert len(events) == 1
        assert events[0]["source"] == "meta_controller"

        query.close()

    def test_count_by_type(self, sample_data):
        """Test counting events by type."""
        from strategies.common.audit.query import AuditQuery

        query = AuditQuery(cold_path=sample_data)

        counts = query.count_by_type()

        assert counts["param.state_change"] == 1
        assert counts["param.k_change"] == 1
        assert counts["trade.fill"] == 1

        query.close()

    def test_reconstruct_incident(self, sample_data):
        """Test incident reconstruction."""
        from strategies.common.audit.query import AuditQuery

        query = AuditQuery(cold_path=sample_data)

        # Incident at the second event
        incident_time = datetime(2026, 1, 6, 0, 1, 0)

        events = query.reconstruct_incident(incident_time, window_minutes=5)

        # Should get all events within ±5 minutes
        assert len(events) == 3

        query.close()

    def test_get_parameter_history(self, sample_data):
        """Test getting parameter history."""
        from strategies.common.audit.query import AuditQuery

        query = AuditQuery(cold_path=sample_data)

        history = query.get_parameter_history("system_state")

        assert len(history) == 1
        assert history[0]["old_value"] == "VENTRAL"
        assert history[0]["new_value"] == "SYMPATHETIC"

        query.close()

    def test_context_manager(self, sample_data):
        """Test using query as context manager."""
        from strategies.common.audit.query import AuditQuery

        with AuditQuery(cold_path=sample_data) as query:
            events = query.query_time_range(
                datetime(2026, 1, 6, 0, 0, 0),
                datetime(2026, 1, 6, 23, 59, 59),
            )
            assert len(events) == 3

    def test_empty_result(self, sample_data):
        """Test query with no matching results."""
        from strategies.common.audit.query import AuditQuery

        query = AuditQuery(cold_path=sample_data)

        # Query for a date with no data
        events = query.query_time_range(
            datetime(2025, 1, 1, 0, 0, 0),
            datetime(2025, 1, 1, 23, 59, 59),
        )

        assert len(events) == 0

        query.close()

    def test_count_with_time_range(self, sample_data):
        """Test counting with time range filter."""
        from strategies.common.audit.query import AuditQuery

        query = AuditQuery(cold_path=sample_data)

        # Count only first minute
        start = datetime(2026, 1, 6, 0, 0, 0)
        end = datetime(2026, 1, 6, 0, 0, 59)

        counts = query.count_by_type(start_time=start, end_time=end)

        # Only first event should be counted
        assert counts.get("param.state_change", 0) == 1
        assert counts.get("param.k_change", 0) == 0

        query.close()
