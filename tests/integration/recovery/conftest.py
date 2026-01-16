"""Integration test fixtures for recovery module (Spec 017).

These fixtures are isolated from other integration tests to avoid
import issues with NautilusTrader adapter modules.
"""

from __future__ import annotations

# Python 3.10 compatibility
import datetime as _dt
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_cache():
    """Create a mock NautilusTrader cache for testing."""
    cache = MagicMock()
    cache.positions.return_value = []
    cache.positions_open.return_value = []
    cache.orders_open.return_value = []
    cache.account.return_value = None
    return cache


@pytest.fixture
def mock_clock():
    """Create a mock clock for testing."""
    clock = MagicMock()
    clock.timestamp_ns.return_value = 1704153600000000000
    clock.utc_now.return_value = datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC)
    return clock


@pytest.fixture
def recovery_config():
    """Create a default RecoveryConfig for testing."""
    from strategies.common.recovery.config import RecoveryConfig

    return RecoveryConfig(
        trader_id="TESTER-001",
        recovery_enabled=True,
        warmup_lookback_days=2,
        startup_delay_secs=10.0,
        max_recovery_time_secs=30.0,
        claim_external_positions=True,
    )


@pytest.fixture
def position_snapshot():
    """Create a sample PositionSnapshot for testing."""
    from strategies.common.recovery.models import PositionSnapshot

    return PositionSnapshot(
        instrument_id="BTCUSDT-PERP.BINANCE",
        side="LONG",
        quantity=Decimal("1.5"),
        avg_entry_price=Decimal("42000.00"),
        unrealized_pnl=Decimal("500.00"),
        realized_pnl=Decimal("0.00"),
        ts_opened=1704067200000000000,
        ts_last_updated=1704153600000000000,
    )


@pytest.fixture
def recovery_state_pending():
    """Create a pending RecoveryState for testing."""
    from strategies.common.recovery.models import RecoveryState, RecoveryStatus

    return RecoveryState(
        status=RecoveryStatus.PENDING,
        positions_recovered=0,
        indicators_warmed=False,
        orders_reconciled=False,
    )


@pytest.fixture
def recovery_state_complete():
    """Create a completed RecoveryState for testing."""
    from strategies.common.recovery.models import RecoveryState, RecoveryStatus

    return RecoveryState(
        status=RecoveryStatus.COMPLETED,
        positions_recovered=2,
        indicators_warmed=True,
        orders_reconciled=True,
        ts_started=1704067200000000000,
        ts_completed=1704067205000000000,
    )
