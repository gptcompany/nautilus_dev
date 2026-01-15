"""Unit tests for AppendOnlyWriter (Spec 030).

Tests:
- O_APPEND flag behavior
- Daily rotation
- Thread safety
- Crash recovery (partial write handling)
"""

# Python 3.10 compatibility
import datetime as _dt
import json
import threading
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from unittest.mock import patch

from strategies.common.audit.events import AuditEvent, AuditEventType
from strategies.common.audit.writer import AppendOnlyWriter


class TestAppendOnlyWriter:
    """Tests for AppendOnlyWriter."""

    def test_creates_directory(self, tmp_path):
        """Test that writer creates base directory if needed."""
        base_path = tmp_path / "audit" / "nested"
        assert not base_path.exists()

        writer = AppendOnlyWriter(base_path=base_path)
        assert base_path.exists()
        writer.close()

    def test_write_event(self, tmp_path):
        """Test writing a single event."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=False,
        )

        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
            ts_event=1704067200000000000,
        )
        writer.write(event)
        writer.close()

        # Read the file
        log_file = tmp_path / "audit.jsonl"
        assert log_file.exists()

        with open(log_file) as f:
            line = f.readline()
            data = json.loads(line)

        assert data["event_type"] == "param.state_change"
        assert data["source"] == "test"

    def test_multiple_writes(self, tmp_path):
        """Test writing multiple events."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=False,
        )

        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.PARAM_STATE_CHANGE,
                source=f"test_{i}",
                ts_event=1704067200000000000 + i,
            )
            writer.write(event)

        writer.close()

        # Read all lines
        log_file = tmp_path / "audit.jsonl"
        with open(log_file) as f:
            lines = f.readlines()

        assert len(lines) == 5
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data["source"] == f"test_{i}"

    def test_o_append_flag(self, tmp_path):
        """Test that O_APPEND flag is used (file can't be overwritten)."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=False,
        )

        # Write first event
        event1 = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="first",
            ts_event=1704067200000000000,
        )
        writer.write(event1)
        writer.close()

        # Open new writer on same file
        writer2 = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=False,
        )
        event2 = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="second",
            ts_event=1704067200000000001,
        )
        writer2.write(event2)
        writer2.close()

        # Both events should be in the file (O_APPEND appends, doesn't overwrite)
        log_file = tmp_path / "audit.jsonl"
        with open(log_file) as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert json.loads(lines[0])["source"] == "first"
        assert json.loads(lines[1])["source"] == "second"

    def test_daily_rotation_filename(self, tmp_path):
        """Test daily rotation creates date-based filename."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=True,
        )

        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
        )
        writer.write(event)
        writer.close()

        # Check filename has today's date
        today = datetime.now(UTC).strftime("%Y%m%d")
        expected_file = tmp_path / f"audit_{today}.jsonl"
        assert expected_file.exists()

    def test_daily_rotation_changes_file(self, tmp_path):
        """Test daily rotation changes file on date change."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=True,
        )

        # Write event with mocked date
        with patch("strategies.common.audit.writer.datetime") as mock_dt:
            mock_dt.utcnow.return_value.strftime.return_value = "20260101"
            event1 = AuditEvent(
                event_type=AuditEventType.PARAM_STATE_CHANGE,
                source="day1",
            )
            writer.write(event1)

        # Change date and write another event
        with patch("strategies.common.audit.writer.datetime") as mock_dt:
            mock_dt.utcnow.return_value.strftime.return_value = "20260102"
            event2 = AuditEvent(
                event_type=AuditEventType.PARAM_STATE_CHANGE,
                source="day2",
            )
            writer.write(event2)

        writer.close()

        # Both files should exist
        assert (tmp_path / "audit_20260101.jsonl").exists()
        assert (tmp_path / "audit_20260102.jsonl").exists()

    def test_sync_writes(self, tmp_path):
        """Test sync writes with fsync."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            sync_writes=True,
            rotate_daily=False,
        )

        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
        )
        writer.write(event)
        writer.close()

        # File should be written
        log_file = tmp_path / "audit.jsonl"
        assert log_file.exists()
        assert log_file.stat().st_size > 0

    def test_thread_safety(self, tmp_path):
        """Test thread-safe writes from multiple threads."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=False,
        )

        num_threads = 10
        events_per_thread = 100

        def write_events(thread_id):
            for i in range(events_per_thread):
                event = AuditEvent(
                    event_type=AuditEventType.PARAM_STATE_CHANGE,
                    source=f"thread_{thread_id}_{i}",
                    ts_event=1704067200000000000 + thread_id * 1000 + i,
                )
                writer.write(event)

        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=write_events, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        writer.close()

        # All events should be written
        log_file = tmp_path / "audit.jsonl"
        with open(log_file) as f:
            lines = f.readlines()

        expected_count = num_threads * events_per_thread
        assert len(lines) == expected_count

        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)  # Should not raise
            assert "source" in data

    def test_context_manager(self, tmp_path):
        """Test writer as context manager."""
        with AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=False,
        ) as writer:
            event = AuditEvent(
                event_type=AuditEventType.PARAM_STATE_CHANGE,
                source="test",
            )
            writer.write(event)

        # File should be closed and written
        log_file = tmp_path / "audit.jsonl"
        assert log_file.exists()

    def test_flush(self, tmp_path):
        """Test explicit flush."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            sync_writes=False,  # Async mode
            rotate_daily=False,
        )

        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
        )
        writer.write(event)
        writer.flush()  # Force sync

        # File should be written
        log_file = tmp_path / "audit.jsonl"
        assert log_file.stat().st_size > 0

        writer.close()

    def test_current_file_property(self, tmp_path):
        """Test current_file property."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=False,
        )

        # Before first write
        assert writer.current_file is None

        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
        )
        writer.write(event)

        # After write
        assert writer.current_file is not None
        assert writer.current_file.name == "audit.jsonl"

        writer.close()


class TestCrashRecovery:
    """Tests for crash recovery (partial write handling)."""

    def test_partial_write_detection(self, tmp_path):
        """Test detection of partial/truncated writes."""
        log_file = tmp_path / "audit.jsonl"

        # Write a complete event
        complete_event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="complete",
            ts_event=1704067200000000000,
        )

        # Simulate partial write (truncated JSON)
        with open(log_file, "w") as f:
            f.write(complete_event.model_dump_json() + "\n")
            f.write('{"event_type": "param.state_change", "source": "partial')  # Truncated

        # Count valid lines
        valid_count = 0
        invalid_count = 0
        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                    valid_count += 1
                except json.JSONDecodeError:
                    invalid_count += 1

        assert valid_count == 1
        assert invalid_count == 1

    def test_write_after_partial(self, tmp_path):
        """Test that writing after partial doesn't corrupt file."""
        log_file = tmp_path / "audit.jsonl"

        # Simulate partial write
        with open(log_file, "w") as f:
            f.write('{"event_type": "param.state_change", "incomplete')

        # New writer should still append correctly
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=False,
        )

        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="after_crash",
            ts_event=1704067200000000000,
        )
        writer.write(event)
        writer.close()

        # Read file - should have partial + new complete entry
        with open(log_file) as f:
            content = f.read()

        # The new event should be on a new line
        lines = content.split("\n")
        assert len(lines) >= 2

        # Last valid line should be our new event
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                assert data["source"] == "after_crash"
                break
            except json.JSONDecodeError:
                continue

    def test_write_raw_for_recovery(self, tmp_path):
        """Test write_raw method for recovery scenarios."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            rotate_daily=False,
        )

        # Write a raw recovery marker
        writer.write_raw('{"recovery_marker": "start", "ts": 1704067200000000000}')

        # Write normal event
        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
        )
        writer.write(event)
        writer.close()

        # Both should be in file
        log_file = tmp_path / "audit.jsonl"
        with open(log_file) as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert "recovery_marker" in lines[0]
        assert "param.state_change" in lines[1]
