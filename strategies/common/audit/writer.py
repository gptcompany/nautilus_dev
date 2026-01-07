"""Append-Only Writer (Spec 030).

This module implements the AppendOnlyWriter for audit trail logging.
Uses O_APPEND flag to ensure atomic appends at the OS level.

Key features:
- O_APPEND flag prevents overwrites (kernel guarantee)
- Thread-safe via mutex lock
- Daily rotation for log management
- Optional fsync for trade events

Performance:
- Async (no fsync): <1ms per write
- Sync (with fsync): 5-10ms per write
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel


# Module logger
_log = logging.getLogger(__name__)


class AppendOnlyWriter:
    """Thread-safe append-only JSON Lines writer.

    Uses O_APPEND flag to ensure atomic appends at the OS level.
    This prevents any process from overwriting existing data.

    Attributes:
        base_path: Directory for audit log files.
        sync_writes: If True, fsync after each write.
        rotate_daily: If True, create new file each day.

    Example:
        >>> writer = AppendOnlyWriter(
        ...     base_path=Path("./data/audit/hot"),
        ...     sync_writes=False,
        ...     rotate_daily=True,
        ... )
        >>> from strategies.common.audit.events import AuditEvent, AuditEventType
        >>> event = AuditEvent(
        ...     event_type=AuditEventType.PARAM_STATE_CHANGE,
        ...     source="test",
        ... )
        >>> writer.write(event)
        >>> writer.close()
    """

    def __init__(
        self,
        base_path: Path | str,
        sync_writes: bool = False,
        rotate_daily: bool = True,
        min_disk_space_mb: int = 100,
    ) -> None:
        """Initialize the AppendOnlyWriter.

        Args:
            base_path: Directory for audit log files (accepts str or Path).
            sync_writes: If True, fsync after each write.
            rotate_daily: If True, create new file each day.
            min_disk_space_mb: Minimum disk space in MB before degradation.
        """
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._sync_writes = sync_writes
        self._rotate_daily = rotate_daily
        self._min_disk_space_mb = min_disk_space_mb
        self._lock = threading.Lock()
        self._fd: int | None = None
        self._current_date: str | None = None

        # Graceful degradation state
        self._disk_full_warned = False
        self._degraded_mode = False

        _log.debug(
            "AppendOnlyWriter initialized: path=%s, sync=%s, rotate=%s",
            self._base_path,
            self._sync_writes,
            self._rotate_daily,
        )

    @property
    def base_path(self) -> Path:
        """Base directory for audit log files."""
        return self._base_path

    @property
    def sync_writes(self) -> bool:
        """Whether fsync is called after each write."""
        return self._sync_writes

    @property
    def current_file(self) -> Path | None:
        """Current log file path, or None if not open."""
        if self._current_date is None:
            return None
        return self._get_filename()

    @property
    def is_degraded(self) -> bool:
        """Whether writer is in degraded mode due to disk full."""
        return self._degraded_mode

    def _check_disk_space(self) -> bool:
        """Check if there's enough disk space.

        Returns:
            True if enough space, False if degraded mode should activate.
        """
        try:
            import shutil

            total, used, free = shutil.disk_usage(self._base_path)
            free_mb = free / (1024 * 1024)

            if free_mb < self._min_disk_space_mb:
                if not self._disk_full_warned:
                    _log.warning(
                        "Disk space low: %.1f MB free (min: %d MB). "
                        "Entering degraded mode - only critical events will be logged.",
                        free_mb,
                        self._min_disk_space_mb,
                    )
                    self._disk_full_warned = True
                self._degraded_mode = True
                return False

            # Recovered from low disk space
            if self._degraded_mode:
                _log.info(
                    "Disk space recovered: %.1f MB free. Exiting degraded mode.",
                    free_mb,
                )
                self._degraded_mode = False
                self._disk_full_warned = False

            return True
        except OSError:
            # If we can't check, assume it's okay
            return True

    def _get_filename(self) -> Path:
        """Get current filename (rotates daily if enabled).

        Returns:
            Path to current log file.
        """
        if self._rotate_daily:
            date_str = datetime.utcnow().strftime("%Y%m%d")
            return self._base_path / f"audit_{date_str}.jsonl"
        return self._base_path / "audit.jsonl"

    def _ensure_file(self) -> int:
        """Ensure file is open, handle rotation.

        Returns:
            File descriptor for writing.
        """
        today = datetime.utcnow().strftime("%Y%m%d")

        # Check if we need to rotate
        if self._fd is None or (self._rotate_daily and self._current_date != today):
            # Close existing file if open
            if self._fd is not None:
                try:
                    os.close(self._fd)
                except OSError:
                    pass  # Already closed

            # Open new file with O_APPEND
            path = self._get_filename()
            self._fd = os.open(
                str(path),
                os.O_WRONLY | os.O_APPEND | os.O_CREAT,
                0o644,
            )
            self._current_date = today
            _log.debug("Opened audit log: %s", path)

        return self._fd

    def write(self, event: BaseModel, critical: bool = False) -> bool:
        """Write event to append-only log.

        The event is serialized to JSON and written with a newline.
        Thread-safe via mutex lock.

        In degraded mode (low disk space), only critical events are written.
        Trade events are always considered critical.

        Args:
            event: Pydantic event model to write.
            critical: If True, write even in degraded mode.

        Returns:
            True if event was written, False if skipped due to degraded mode.
        """
        # Check disk space (every write to catch recovery)
        has_space = self._check_disk_space()

        # In degraded mode, skip non-critical events
        if not has_space and not critical:
            # Check if this is a trade event (always critical)
            event_type = getattr(event, "event_type", None)
            if event_type is not None:
                event_type_str = (
                    str(event_type.value) if hasattr(event_type, "value") else str(event_type)
                )
                if not event_type_str.startswith("trade."):
                    return False

        line = event.model_dump_json() + "\n"
        data = line.encode("utf-8")

        with self._lock:
            try:
                fd = self._ensure_file()
                os.write(fd, data)

                if self._sync_writes:
                    os.fsync(fd)

                return True
            except OSError as e:
                _log.error("Failed to write audit event: %s", e)
                return False

    def write_raw(self, line: str) -> bool:
        """Write raw string to append-only log.

        Used for recovery from partial writes.

        Args:
            line: Raw string to write (should end with newline).

        Returns:
            True if write succeeded, False on error.
        """
        if not line.endswith("\n"):
            line = line + "\n"
        data = line.encode("utf-8")

        with self._lock:
            try:
                fd = self._ensure_file()
                os.write(fd, data)

                if self._sync_writes:
                    os.fsync(fd)

                return True
            except OSError as e:
                _log.error("Failed to write raw audit data: %s", e)
                return False

    def flush(self) -> None:
        """Flush pending writes to disk.

        Forces an fsync regardless of sync_writes setting.
        """
        with self._lock:
            if self._fd is not None:
                os.fsync(self._fd)

    def close(self) -> None:
        """Close the file descriptor.

        Should be called when shutting down the audit system.
        """
        with self._lock:
            if self._fd is not None:
                try:
                    os.fsync(self._fd)
                    os.close(self._fd)
                except OSError:
                    pass  # Already closed
                self._fd = None
                self._current_date = None
                _log.debug("Closed audit log")

    def __enter__(self) -> AppendOnlyWriter:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
