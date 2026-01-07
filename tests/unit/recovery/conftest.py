"""Unit test fixtures for recovery module (Spec 017).

These fixtures provide mocks for unit testing position recovery
without requiring NautilusTrader adapter dependencies.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_cache():
    """Create a mock NautilusTrader cache for testing.

    Returns a MagicMock with common cache methods stubbed:
    - positions(): Returns empty list by default
    - positions_open(): Returns empty list by default
    - orders_open(): Returns empty list by default
    - account(): Returns None by default
    """
    cache = MagicMock()
    cache.positions.return_value = []
    cache.positions_open.return_value = []
    cache.orders_open.return_value = []
    cache.account.return_value = None
    return cache


@pytest.fixture
def mock_clock():
    """Create a mock clock for testing.

    Returns a MagicMock with:
    - timestamp_ns(): Returns fixed nanosecond timestamp
    - utc_now(): Returns fixed datetime (2024-01-02 00:00:00 UTC)
    """
    clock = MagicMock()
    clock.timestamp_ns.return_value = 1704153600000000000
    clock.utc_now.return_value = datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC)
    return clock


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing log output.

    Returns a MagicMock with standard logging methods stubbed.
    """
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    return logger


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


def create_mock_position(
    instrument_id: str,
    side: str = "LONG",
    quantity: Decimal = Decimal("1.0"),
    avg_px_open: Decimal = Decimal("1000.00"),
    is_open: bool = True,
) -> MagicMock:
    """Factory function to create mock positions.

    Args:
        instrument_id: Full instrument ID (e.g., BTCUSDT-PERP.BINANCE)
        side: Position side (LONG or SHORT)
        quantity: Position quantity
        avg_px_open: Average entry price
        is_open: Whether position is currently open

    Returns:
        MagicMock configured as a Position object
    """
    pos = MagicMock()
    pos.instrument_id = MagicMock()
    pos.instrument_id.value = instrument_id
    pos.side = MagicMock()
    pos.side.value = side
    pos.quantity = MagicMock()
    pos.quantity.as_decimal.return_value = quantity
    pos.avg_px_open = MagicMock()
    pos.avg_px_open.as_decimal.return_value = avg_px_open
    pos.is_open = is_open
    return pos


@pytest.fixture
def mock_btc_position():
    """Create a mock BTC position."""
    return create_mock_position(
        instrument_id="BTCUSDT-PERP.BINANCE",
        side="LONG",
        quantity=Decimal("1.5"),
        avg_px_open=Decimal("42000.00"),
    )


@pytest.fixture
def mock_eth_position():
    """Create a mock ETH position."""
    return create_mock_position(
        instrument_id="ETHUSDT-PERP.BINANCE",
        side="SHORT",
        quantity=Decimal("10.0"),
        avg_px_open=Decimal("2200.00"),
    )
