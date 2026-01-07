"""Audit Query Interface (Spec 030).

This module provides DuckDB-based queries on the audit trail.
Supports time-range queries, event type filtering, and incident reconstruction.

Key features:
- DuckDB backend for fast analytical queries
- Time-range queries with event type filtering
- Aggregation by event type
- Incident reconstruction (±N minutes around timestamp)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _sanitize_sql_string(value: str) -> str:
    """Sanitize a string value for safe SQL interpolation.

    Escapes single quotes to prevent SQL injection attacks.

    Args:
        value: The string value to sanitize.

    Returns:
        Sanitized string safe for SQL interpolation.
    """
    if not isinstance(value, str):
        raise ValueError(f"Expected string, got {type(value).__name__}")
    # Escape single quotes by doubling them (standard SQL escaping)
    return value.replace("'", "''")


class AuditQuery:
    """Query interface for audit trail data.

    Uses DuckDB for fast analytical queries on Parquet-formatted audit data.

    Attributes:
        cold_path: Path to Parquet audit data.

    Example:
        >>> query = AuditQuery(cold_path=Path("./data/audit/cold"))
        >>> events = query.query_time_range(
        ...     start_time=datetime(2026, 1, 1),
        ...     end_time=datetime(2026, 1, 2),
        ...     event_type="param.state_change",
        ... )
        >>> for event in events:
        ...     print(event)
    """

    def __init__(self, cold_path: Path) -> None:
        """Initialize the AuditQuery.

        Args:
            cold_path: Path to Parquet audit data directory.
        """
        self.cold_path = Path(cold_path)
        self._conn = None

    def _get_connection(self):
        """Get or create DuckDB connection."""
        if self._conn is not None:
            return self._conn

        try:
            import duckdb

            self._conn = duckdb.connect(":memory:")
            return self._conn
        except ImportError:
            logger.error("duckdb not installed. Run: pip install duckdb")
            raise

    def query_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        event_type: str | None = None,
        source: str | None = None,
        limit: int = 10000,
    ) -> list[dict[str, Any]]:
        """Query events within a time range.

        Args:
            start_time: Start of time range (inclusive).
            end_time: End of time range (inclusive).
            event_type: Optional filter by event type (e.g., "param.state_change").
            source: Optional filter by source component.
            limit: Maximum number of results.

        Returns:
            List of event dictionaries.
        """
        conn = self._get_connection()

        # Convert times to nanoseconds
        start_ns = int(start_time.timestamp() * 1_000_000_000)
        end_ns = int(end_time.timestamp() * 1_000_000_000)

        # Build partition filter based on date range
        partitions = self._get_partitions_for_range(start_time, end_time)
        if not partitions:
            logger.warning("No partitions found for time range")
            return []

        # Build query
        parquet_pattern = str(self.cold_path / "**" / "*.parquet")

        sql = f"""
        SELECT *
        FROM read_parquet('{parquet_pattern}', union_by_name=true)
        WHERE ts_event >= {start_ns}
          AND ts_event <= {end_ns}
        """

        if event_type:
            sql += f"\n  AND event_type = '{_sanitize_sql_string(event_type)}'"

        if source:
            sql += f"\n  AND source = '{_sanitize_sql_string(source)}'"

        sql += f"\nORDER BY ts_event\nLIMIT {limit}"

        try:
            result = conn.execute(sql).fetchall()
            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row, strict=False)) for row in result]
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    def count_by_type(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, int]:
        """Count events by type.

        Args:
            start_time: Optional start of time range.
            end_time: Optional end of time range.

        Returns:
            Dictionary mapping event type to count.
        """
        conn = self._get_connection()

        parquet_pattern = str(self.cold_path / "**" / "*.parquet")

        sql = f"""
        SELECT event_type, COUNT(*) as count
        FROM read_parquet('{parquet_pattern}', union_by_name=true)
        """

        conditions = []
        if start_time:
            start_ns = int(start_time.timestamp() * 1_000_000_000)
            conditions.append(f"ts_event >= {start_ns}")

        if end_time:
            end_ns = int(end_time.timestamp() * 1_000_000_000)
            conditions.append(f"ts_event <= {end_ns}")

        if conditions:
            sql += "\nWHERE " + " AND ".join(conditions)

        sql += "\nGROUP BY event_type\nORDER BY count DESC"

        try:
            result = conn.execute(sql).fetchall()
            return {row[0]: row[1] for row in result}
        except Exception as e:
            logger.error(f"Count query failed: {e}")
            return {}

    def reconstruct_incident(
        self,
        incident_time: datetime,
        window_minutes: int = 5,
    ) -> list[dict[str, Any]]:
        """Reconstruct events around an incident.

        Args:
            incident_time: Timestamp of the incident.
            window_minutes: Minutes before and after to include.

        Returns:
            List of events in chronological order.
        """
        start_time = incident_time - timedelta(minutes=window_minutes)
        end_time = incident_time + timedelta(minutes=window_minutes)

        events = self.query_time_range(
            start_time=start_time,
            end_time=end_time,
            limit=50000,  # Higher limit for forensics
        )

        logger.info(f"Reconstructed {len(events)} events around incident at {incident_time}")
        return events

    def get_parameter_history(
        self,
        param_name: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Get history of a specific parameter.

        Args:
            param_name: Name of the parameter to track.
            start_time: Optional start of time range.
            end_time: Optional end of time range.

        Returns:
            List of parameter change events.
        """
        conn = self._get_connection()

        parquet_pattern = str(self.cold_path / "**" / "*.parquet")

        sql = f"""
        SELECT *
        FROM read_parquet('{parquet_pattern}', union_by_name=true)
        WHERE event_type LIKE 'param.%'
          AND param_name = '{_sanitize_sql_string(param_name)}'
        """

        if start_time:
            start_ns = int(start_time.timestamp() * 1_000_000_000)
            sql += f"\n  AND ts_event >= {start_ns}"

        if end_time:
            end_ns = int(end_time.timestamp() * 1_000_000_000)
            sql += f"\n  AND ts_event <= {end_ns}"

        sql += "\nORDER BY ts_event"

        try:
            result = conn.execute(sql).fetchall()
            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row, strict=False)) for row in result]
        except Exception as e:
            logger.error(f"Parameter history query failed: {e}")
            return []

    def verify_checksums(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, Any]:
        """Verify checksums for events in a time range.

        Args:
            start_time: Start of time range.
            end_time: End of time range.

        Returns:
            Dictionary with verification results.
        """
        import hashlib
        import json

        events = self.query_time_range(start_time, end_time, limit=100000)

        results = {
            "total_events": len(events),
            "valid_checksums": 0,
            "invalid_checksums": 0,
            "missing_checksums": 0,
            "corrupted_events": [],
        }

        # Base event field order as defined in AuditEvent (Pydantic model)
        # The checksum is computed by Pydantic which outputs keys in definition order
        base_field_order = ["ts_event", "event_type", "source", "trader_id", "sequence"]

        for event in events:
            stored_checksum = event.get("checksum")
            if not stored_checksum:
                results["missing_checksums"] += 1
                continue

            # Recompute checksum - must match the format used by AuditEvent.checksum
            # The original uses Pydantic's model_dump_json() which produces compact JSON
            # without spaces and with keys in field definition order.
            # Database queries may return columns in different order, so we must
            # enforce the original field order for consistent checksums.
            event_copy = {}
            # First add base fields in correct order
            for key in base_field_order:
                if key in event and key != "checksum":
                    event_copy[key] = event[key]
            # Then add any additional fields (subclass-specific) in their order
            for key, value in event.items():
                if key not in event_copy and key != "checksum":
                    event_copy[key] = value

            # Use compact JSON without spaces (matches Pydantic's default)
            payload = json.dumps(event_copy, separators=(",", ":"))
            computed = hashlib.sha256(payload.encode()).hexdigest()[:16]

            if computed == stored_checksum:
                results["valid_checksums"] += 1
            else:
                results["invalid_checksums"] += 1
                results["corrupted_events"].append(
                    {
                        "ts_event": event.get("ts_event"),
                        "event_type": event.get("event_type"),
                        "stored_checksum": stored_checksum,
                        "computed_checksum": computed,
                    }
                )

        return results

    def _get_partitions_for_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[str]:
        """Get list of partition paths for a time range.

        Args:
            start_time: Start of time range.
            end_time: End of time range.

        Returns:
            List of partition paths.
        """
        partitions = []
        current = start_time.date()
        end_date = end_time.date()

        while current <= end_date:
            partition_path = self.cold_path / current.strftime("%Y/%m/%d")
            if partition_path.exists():
                partitions.append(str(partition_path))
            current += timedelta(days=1)

        return partitions

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> AuditQuery:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
