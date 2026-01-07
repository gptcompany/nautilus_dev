"""Recovery State Manager (Spec 017).

This module implements the RecoveryStateManager for tracking and persisting
recovery state during TradingNode restarts.

Implementation Note:
    MVP uses JSON file persistence. Future versions may integrate with
    Redis or other distributed state stores.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any

from strategies.common.recovery.models import (
    RecoveryState,
    RecoveryStatus,
)


# Module logger
_log = logging.getLogger(__name__)


def _now_ns() -> int:
    """Get current time in nanoseconds."""
    return int(time.time() * 1_000_000_000)


def _sanitize_trader_id(trader_id: str) -> str:
    """Sanitize trader_id for safe filesystem usage (B4 fix).

    Replaces any non-word characters (except hyphen) with underscore.

    Args:
        trader_id: Raw trader identifier.

    Returns:
        Filesystem-safe trader identifier.
    """
    return re.sub(r"[^\w\-]", "_", trader_id)


class RecoveryStateManager:
    """Manager for recovery state tracking and persistence.

    Tracks recovery progress and persists state to JSON file for
    crash recovery. Provides methods to update, save, and load state.

    Attributes:
        trader_id: Trader identifier for state isolation.
        state_dir: Directory for state file persistence.
        state: Current recovery state.

    Example:
        >>> manager = RecoveryStateManager(
        ...     trader_id="TRADER-001",
        ...     state_dir=Path("/var/nautilus/state"),
        ... )
        >>> manager.start_recovery()
        >>> manager.increment_positions_recovered()
        >>> manager.set_indicators_warmed()
        >>> manager.complete_recovery()
        >>> manager.save_state()
    """

    def __init__(
        self,
        trader_id: str,
        state_dir: Path | str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the RecoveryStateManager.

        Args:
            trader_id: Trader identifier for state file naming.
            state_dir: Directory for state file persistence.
                      If None, state is held in memory only.
            logger: Optional custom logger. If None, uses module logger.
        """
        self._trader_id = trader_id
        self._state_dir = Path(state_dir) if state_dir else None
        self._log = logger or _log
        self._state = RecoveryState()
        self._file_lock = threading.Lock()  # Thread safety for file ops (B3 fix)

        # Ensure state directory exists
        if self._state_dir:
            self._state_dir.mkdir(parents=True, exist_ok=True)

    @property
    def trader_id(self) -> str:
        """Trader identifier for state isolation."""
        return self._trader_id

    @property
    def state(self) -> RecoveryState:
        """Current recovery state (read-only copy)."""
        return self._state.model_copy()

    @property
    def state_file_path(self) -> Path | None:
        """Path to the state file, if state_dir is configured."""
        if self._state_dir:
            # Sanitize trader_id for safe filesystem usage (B4 fix)
            safe_id = _sanitize_trader_id(self._trader_id)
            return self._state_dir / f"recovery_state_{safe_id}.json"
        return None

    def get_state(self) -> RecoveryState:
        """Get current recovery state.

        Returns:
            Copy of the current recovery state.
        """
        return self._state.model_copy()

    def update_state(self, **kwargs: Any) -> RecoveryState:
        """Update recovery state with provided values.

        Creates a new state instance with updated values.
        Use specific methods (start_recovery, complete_recovery, etc.)
        for common state transitions.

        Args:
            **kwargs: Fields to update on the state.

        Returns:
            The updated recovery state.

        Example:
            >>> manager.update_state(
            ...     positions_recovered=5,
            ...     indicators_warmed=True,
            ... )
        """
        current_dict = self._state.model_dump()
        current_dict.update(kwargs)
        self._state = RecoveryState(**current_dict)
        self._log.debug("Recovery state updated: %s", kwargs)
        return self._state.model_copy()

    def start_recovery(self) -> RecoveryState:
        """Mark recovery as started.

        Sets status to IN_PROGRESS and records start timestamp.

        Returns:
            The updated recovery state.
        """
        self._state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=_now_ns(),
            positions_recovered=0,
            indicators_warmed=False,
            orders_reconciled=False,
            ts_completed=None,
            error_message=None,
        )
        self._log.info("Recovery started for trader_id=%s", self._trader_id)
        return self._state.model_copy()

    def increment_positions_recovered(self, count: int = 1) -> RecoveryState:
        """Increment the count of recovered positions.

        Args:
            count: Number to add to positions_recovered.

        Returns:
            The updated recovery state.
        """
        return self.update_state(positions_recovered=self._state.positions_recovered + count)

    def set_indicators_warmed(self, warmed: bool = True) -> RecoveryState:
        """Set indicators warmed status.

        Args:
            warmed: Whether indicators are warmed.

        Returns:
            The updated recovery state.
        """
        return self.update_state(indicators_warmed=warmed)

    def set_orders_reconciled(self, reconciled: bool = True) -> RecoveryState:
        """Set orders reconciled status.

        Args:
            reconciled: Whether orders are reconciled.

        Returns:
            The updated recovery state.
        """
        return self.update_state(orders_reconciled=reconciled)

    def complete_recovery(self) -> RecoveryState:
        """Mark recovery as completed successfully.

        Sets status to COMPLETED and records completion timestamp.

        Returns:
            The updated recovery state.
        """
        self._state = RecoveryState(
            status=RecoveryStatus.COMPLETED,
            ts_started=self._state.ts_started,
            ts_completed=_now_ns(),
            positions_recovered=self._state.positions_recovered,
            indicators_warmed=self._state.indicators_warmed,
            orders_reconciled=self._state.orders_reconciled,
            error_message=None,
        )
        self._log.info(
            "Recovery completed for trader_id=%s: positions=%d duration_ms=%s",
            self._trader_id,
            self._state.positions_recovered,
            self._state.recovery_duration_ms,
        )
        return self._state.model_copy()

    def fail_recovery(self, error_message: str) -> RecoveryState:
        """Mark recovery as failed.

        Sets status to FAILED and records error message.

        Args:
            error_message: Human-readable error message.

        Returns:
            The updated recovery state.
        """
        self._state = RecoveryState(
            status=RecoveryStatus.FAILED,
            ts_started=self._state.ts_started,
            ts_completed=_now_ns(),
            positions_recovered=self._state.positions_recovered,
            indicators_warmed=self._state.indicators_warmed,
            orders_reconciled=self._state.orders_reconciled,
            error_message=error_message,
        )
        self._log.error(
            "Recovery failed for trader_id=%s: %s",
            self._trader_id,
            error_message,
        )
        return self._state.model_copy()

    def timeout_recovery(self) -> RecoveryState:
        """Mark recovery as timed out.

        Sets status to TIMEOUT and records completion timestamp.

        Returns:
            The updated recovery state.
        """
        self._state = RecoveryState(
            status=RecoveryStatus.TIMEOUT,
            ts_started=self._state.ts_started,
            ts_completed=_now_ns(),
            positions_recovered=self._state.positions_recovered,
            indicators_warmed=self._state.indicators_warmed,
            orders_reconciled=self._state.orders_reconciled,
            error_message="Recovery exceeded max_recovery_time_secs",
        )
        self._log.warning(
            "Recovery timed out for trader_id=%s: positions=%d",
            self._trader_id,
            self._state.positions_recovered,
        )
        return self._state.model_copy()

    def reset_state(self) -> RecoveryState:
        """Reset state to initial PENDING state.

        Useful for retry scenarios or testing.

        Returns:
            The reset recovery state.
        """
        self._state = RecoveryState()
        self._log.debug("Recovery state reset for trader_id=%s", self._trader_id)
        return self._state.model_copy()

    def save_state(self) -> bool:
        """Persist current state to JSON file.

        Uses thread-safe atomic write pattern (B3 fix).

        Returns:
            True if save succeeded, False if state_dir not configured.

        Raises:
            IOError: If file write fails.
        """
        if not self.state_file_path:
            self._log.warning(
                "Cannot save state: state_dir not configured for trader_id=%s",
                self._trader_id,
            )
            return False

        state_dict = self._state.model_dump(mode="json")
        state_dict["trader_id"] = self._trader_id
        state_dict["ts_saved"] = _now_ns()

        # Thread-safe atomic write (B3 fix)
        with self._file_lock:
            try:
                # Write to temp file first, then atomic rename
                temp_path = self.state_file_path.with_suffix(".tmp")
                with open(temp_path, "w") as f:
                    json.dump(state_dict, f, indent=2)
                temp_path.rename(self.state_file_path)  # Atomic on POSIX
                self._log.info(
                    "Recovery state saved to %s",
                    self.state_file_path,
                )
                return True
            except Exception as e:
                self._log.error(
                    "Failed to save recovery state to %s: %s",
                    self.state_file_path,
                    e,
                )
                raise

    def load_state(self) -> RecoveryState | None:
        """Load state from JSON file.

        Uses thread-safe read pattern (B3 fix).

        Returns:
            Loaded recovery state, or None if file doesn't exist.

        Raises:
            IOError: If file read fails.
            ValidationError: If JSON doesn't match RecoveryState schema.
        """
        if not self.state_file_path:
            self._log.warning(
                "Cannot load state: state_dir not configured for trader_id=%s",
                self._trader_id,
            )
            return None

        if not self.state_file_path.exists():
            self._log.info(
                "No existing state file found at %s",
                self.state_file_path,
            )
            return None

        # Thread-safe read (B3 fix)
        with self._file_lock:
            try:
                with open(self.state_file_path) as f:
                    state_dict = json.load(f)

                # Remove non-model fields
                state_dict.pop("trader_id", None)
                state_dict.pop("ts_saved", None)

                self._state = RecoveryState(**state_dict)
                self._log.info(
                    "Recovery state loaded from %s: status=%s positions=%d",
                    self.state_file_path,
                    self._state.status.value,
                    self._state.positions_recovered,
                )
                return self._state.model_copy()
            except Exception as e:
                self._log.error(
                    "Failed to load recovery state from %s: %s",
                    self.state_file_path,
                    e,
                )
                raise

    def delete_state_file(self) -> bool:
        """Delete the state file if it exists.

        Useful for cleanup after successful recovery.

        Returns:
            True if file was deleted, False if not applicable.
        """
        if not self.state_file_path:
            return False

        if self.state_file_path.exists():
            self.state_file_path.unlink()
            self._log.info(
                "Recovery state file deleted: %s",
                self.state_file_path,
            )
            return True

        return False
