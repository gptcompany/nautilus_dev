"""Audit Configuration (Spec 030).

This module defines the configuration for the audit trail system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AuditConfig:
    """Configuration for audit trail system.

    Attributes:
        base_path: Base directory for audit logs (accepts str or Path).
        sync_writes: If True, fsync after each write (for trade events).
        rotate_daily: If True, rotate log files daily.
        retention_days: Number of days to retain audit logs (0 = forever).
        trader_id: Default trader ID for events.

    Example:
        >>> config = AuditConfig(
        ...     base_path=Path("./data/audit"),
        ...     sync_writes=False,
        ...     rotate_daily=True,
        ...     retention_days=90,
        ... )
    """

    base_path: Path | str = field(default_factory=lambda: Path("./data/audit/hot"))
    sync_writes: bool = False
    rotate_daily: bool = True
    retention_days: int = 90
    trader_id: str = "TRADER-001"

    def __post_init__(self) -> None:
        """Convert base_path to Path if string."""
        if isinstance(self.base_path, str):
            self.base_path = Path(self.base_path)
