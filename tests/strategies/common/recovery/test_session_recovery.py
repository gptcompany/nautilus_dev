"""Comprehensive tests for Position Recovery module (Spec 017).

CRITICAL: This module handles PRODUCTION trading position recovery after crashes.
Tests MUST cover all edge cases, failure modes, and race conditions.

Test Coverage:
- RecoveryStateManager: State persistence, thread safety, file operations
- PositionRecoveryProvider: Position/balance reconciliation, discrepancy detection
- RecoverableStrategy: Position detection, historical warmup, exit orders
- EventReplayManager: Event replay, synthetic event generation, gap detection
- RecoveryEventEmitter: Event emission, callback invocation
- Models: Validation, edge cases, serialization
- Config: Parameter validation, cross-field validation
"""

from __future__ import annotations

import json
import tempfile
import threading
import time
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from pydantic import ValidationError

from strategies.common.recovery.config import RecoveryConfig
from strategies.common.recovery.event_emitter import RecoveryEventEmitter
from strategies.common.recovery.event_replay import (
    EventReplayManager,
    SyntheticEvent,
)
from strategies.common.recovery.events import (
    IndicatorsReadyEvent,
    IndicatorsWarmingEvent,
    PositionDiscrepancyEvent,
    PositionLoadedEvent,
    PositionReconciledEvent,
    RecoveryCompletedEvent,
    RecoveryFailedEvent,
    RecoveryStartedEvent,
    RecoveryTimeoutEvent,
)
from strategies.common.recovery.models import (
    IndicatorState,
    PositionSnapshot,
    RecoveryState,
    RecoveryStatus,
    StrategySnapshot,
)
from strategies.common.recovery.provider import PositionRecoveryProvider
from strategies.common.recovery.recoverable_strategy import (
    RecoverableStrategy,
    RecoverableStrategyConfig,
)
from strategies.common.recovery.state_manager import RecoveryStateManager

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_state_dir():
    """Temporary directory for state file persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def state_manager(temp_state_dir):
    """RecoveryStateManager instance with temp directory."""
    return RecoveryStateManager(
        trader_id="TRADER-TEST-001",
        state_dir=temp_state_dir,
    )


@pytest.fixture
def state_manager_no_dir():
    """RecoveryStateManager instance without state directory."""
    return RecoveryStateManager(
        trader_id="TRADER-TEST-002",
        state_dir=None,
    )


@pytest.fixture
def mock_cache():
    """Mock NautilusTrader cache."""
    cache = MagicMock()
    cache.positions.return_value = []
    cache.account.return_value = None
    return cache


@pytest.fixture
def recovery_provider(mock_cache):
    """PositionRecoveryProvider instance with mock cache."""
    return PositionRecoveryProvider(cache=mock_cache)


@pytest.fixture
def event_emitter():
    """RecoveryEventEmitter instance."""
    return RecoveryEventEmitter(trader_id="TRADER-TEST-001")


@pytest.fixture
def event_replay_manager(mock_cache):
    """EventReplayManager instance with mock cache."""
    return EventReplayManager(cache=mock_cache)


@pytest.fixture
def recovery_config():
    """Default RecoveryConfig for tests."""
    return RecoveryConfig(
        trader_id="TRADER-TEST-001",
        recovery_enabled=True,
        warmup_lookback_days=2,
        startup_delay_secs=10.0,
        max_recovery_time_secs=30.0,
        claim_external_positions=True,
    )


@pytest.fixture
def position_snapshot():
    """Sample PositionSnapshot for testing."""
    return PositionSnapshot(
        instrument_id="BTCUSDT-PERP.BINANCE",
        side="LONG",
        quantity=Decimal("1.5"),
        avg_entry_price=Decimal("42000.00"),
        unrealized_pnl=Decimal("1500.00"),
        realized_pnl=Decimal("0.00"),
        ts_opened=1_000_000_000_000,
        ts_last_updated=1_000_001_000_000,
    )


@pytest.fixture
def mock_position():
    """Mock Position object for testing."""
    pos = MagicMock()
    pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
    pos.side.value = "LONG"
    pos.quantity.as_decimal.return_value = Decimal("1.5")
    pos.avg_px_open = Decimal("42000.00")
    pos.is_open = True
    return pos


@pytest.fixture
def mock_balance():
    """Mock Balance object for testing."""
    bal = MagicMock()
    bal.currency.code = "USDT"
    bal.total.as_decimal.return_value = Decimal("10000.00")
    bal.locked.as_decimal.return_value = Decimal("1000.00")
    bal.free.as_decimal.return_value = Decimal("9000.00")
    return bal


# =============================================================================
# RecoveryStateManager Tests
# =============================================================================


class TestRecoveryStateManager:
    """Tests for RecoveryStateManager state tracking and persistence."""

    def test_initialization_creates_state_dir(self, temp_state_dir):
        """Test state directory is created on initialization."""
        subdir = temp_state_dir / "subdir"
        manager = RecoveryStateManager(
            trader_id="TRADER-001",
            state_dir=subdir,
        )
        assert subdir.exists()
        assert manager.trader_id == "TRADER-001"

    def test_initialization_without_state_dir(self):
        """Test initialization without state directory."""
        manager = RecoveryStateManager(
            trader_id="TRADER-001",
            state_dir=None,
        )
        assert manager.state_file_path is None
        assert manager.state.status == RecoveryStatus.PENDING

    def test_sanitize_trader_id_in_filename(self, temp_state_dir):
        """Test trader_id is sanitized for filesystem safety."""
        manager = RecoveryStateManager(
            trader_id="TRADER:001/TEST",
            state_dir=temp_state_dir,
        )
        # Should replace non-word chars with underscores
        assert manager.state_file_path.name == "recovery_state_TRADER_001_TEST.json"

    def test_start_recovery_initializes_state(self, state_manager):
        """Test start_recovery sets status to IN_PROGRESS."""
        state = state_manager.start_recovery()
        assert state.status == RecoveryStatus.IN_PROGRESS
        assert state.ts_started is not None
        assert state.positions_recovered == 0
        assert state.indicators_warmed is False
        assert state.orders_reconciled is False

    def test_increment_positions_recovered(self, state_manager):
        """Test increment_positions_recovered updates count."""
        state_manager.start_recovery()
        state = state_manager.increment_positions_recovered(count=3)
        assert state.positions_recovered == 3
        state = state_manager.increment_positions_recovered(count=2)
        assert state.positions_recovered == 5

    def test_set_indicators_warmed(self, state_manager):
        """Test set_indicators_warmed updates flag."""
        state_manager.start_recovery()
        state = state_manager.set_indicators_warmed(warmed=True)
        assert state.indicators_warmed is True
        state = state_manager.set_indicators_warmed(warmed=False)
        assert state.indicators_warmed is False

    def test_set_orders_reconciled(self, state_manager):
        """Test set_orders_reconciled updates flag."""
        state_manager.start_recovery()
        state = state_manager.set_orders_reconciled(reconciled=True)
        assert state.orders_reconciled is True

    def test_complete_recovery_sets_completed(self, state_manager):
        """Test complete_recovery sets status to COMPLETED."""
        state_manager.start_recovery()
        state_manager.increment_positions_recovered(count=5)
        state_manager.set_indicators_warmed(warmed=True)
        state = state_manager.complete_recovery()
        assert state.status == RecoveryStatus.COMPLETED
        assert state.ts_completed is not None
        assert state.positions_recovered == 5
        assert state.indicators_warmed is True
        assert state.recovery_duration_ms is not None

    def test_fail_recovery_sets_failed(self, state_manager):
        """Test fail_recovery sets status to FAILED."""
        state_manager.start_recovery()
        state = state_manager.fail_recovery(error_message="Test failure")
        assert state.status == RecoveryStatus.FAILED
        assert state.error_message == "Test failure"
        assert state.ts_completed is not None

    def test_timeout_recovery_sets_timeout(self, state_manager):
        """Test timeout_recovery sets status to TIMEOUT."""
        state_manager.start_recovery()
        state = state_manager.timeout_recovery()
        assert state.status == RecoveryStatus.TIMEOUT
        assert state.error_message == "Recovery exceeded max_recovery_time_secs"

    def test_reset_state_clears_all(self, state_manager):
        """Test reset_state returns to initial PENDING state."""
        state_manager.start_recovery()
        state_manager.increment_positions_recovered(count=5)
        state = state_manager.reset_state()
        assert state.status == RecoveryStatus.PENDING
        assert state.positions_recovered == 0
        assert state.ts_started is None

    def test_save_state_creates_file(self, state_manager, temp_state_dir):
        """Test save_state creates JSON file."""
        state_manager.start_recovery()
        state_manager.increment_positions_recovered(count=3)
        result = state_manager.save_state()
        assert result is True
        assert state_manager.state_file_path.exists()

    def test_save_state_without_dir(self, state_manager_no_dir):
        """Test save_state without state_dir returns False."""
        result = state_manager_no_dir.save_state()
        assert result is False

    def test_load_state_reads_file(self, state_manager):
        """Test load_state reads persisted state from file."""
        state_manager.start_recovery()
        state_manager.increment_positions_recovered(count=5)
        state_manager.save_state()

        # Create new manager and load state
        new_manager = RecoveryStateManager(
            trader_id="TRADER-TEST-001",
            state_dir=state_manager._state_dir,
        )
        loaded_state = new_manager.load_state()
        assert loaded_state is not None
        assert loaded_state.positions_recovered == 5
        assert loaded_state.status == RecoveryStatus.IN_PROGRESS

    def test_load_state_nonexistent_file(self, state_manager):
        """Test load_state returns None if file doesn't exist."""
        loaded_state = state_manager.load_state()
        assert loaded_state is None

    def test_load_state_corrupted_json(self, state_manager, temp_state_dir):
        """Test load_state raises on corrupted JSON."""
        # Write invalid JSON
        state_file = state_manager.state_file_path
        state_file.write_text("{invalid json")

        with pytest.raises(Exception):
            state_manager.load_state()

    def test_load_state_invalid_schema(self, state_manager):
        """Test load_state raises ValidationError on schema mismatch."""
        # Write valid JSON but invalid schema
        state_file = state_manager.state_file_path
        state_file.write_text(json.dumps({"status": "INVALID_STATUS"}))

        with pytest.raises(ValidationError):
            state_manager.load_state()

    def test_delete_state_file_removes_file(self, state_manager):
        """Test delete_state_file removes the state file."""
        state_manager.start_recovery()
        state_manager.save_state()
        assert state_manager.state_file_path.exists()

        result = state_manager.delete_state_file()
        assert result is True
        assert not state_manager.state_file_path.exists()

    def test_delete_state_file_without_dir(self, state_manager_no_dir):
        """Test delete_state_file without state_dir returns False."""
        result = state_manager_no_dir.delete_state_file()
        assert result is False

    def test_thread_safety_concurrent_saves(self, state_manager):
        """Test thread-safe concurrent save operations."""
        state_manager.start_recovery()
        errors = []

        def save_state():
            try:
                for _ in range(10):
                    state_manager.increment_positions_recovered(count=1)
                    state_manager.save_state()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=save_state) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # State file should exist and be valid
        loaded_state = state_manager.load_state()
        assert loaded_state is not None

    def test_atomic_write_pattern(self, state_manager):
        """Test save_state uses atomic write pattern (temp file + rename)."""
        state_manager.start_recovery()
        state_manager.save_state()

        # Verify no .tmp file remains
        tmp_files = list(state_manager._state_dir.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_get_state_returns_copy(self, state_manager):
        """Test get_state returns a copy, not reference."""
        state_manager.start_recovery()
        state1 = state_manager.get_state()
        state_manager.increment_positions_recovered(count=5)
        state2 = state_manager.get_state()

        # state1 should not be affected by later changes
        assert state1.positions_recovered == 0
        assert state2.positions_recovered == 5

    def test_update_state_arbitrary_fields(self, state_manager):
        """Test update_state can update arbitrary fields."""
        state_manager.start_recovery()
        state = state_manager.update_state(
            positions_recovered=10,
            indicators_warmed=True,
        )
        assert state.positions_recovered == 10
        assert state.indicators_warmed is True


# =============================================================================
# PositionRecoveryProvider Tests
# =============================================================================


class TestPositionRecoveryProvider:
    """Tests for PositionRecoveryProvider position reconciliation."""

    def test_get_cached_positions_empty(self, recovery_provider, mock_cache):
        """Test get_cached_positions with empty cache."""
        mock_cache.positions.return_value = []
        positions = recovery_provider.get_cached_positions(trader_id="TRADER-001")
        assert len(positions) == 0

    def test_get_cached_positions_multiple(self, recovery_provider, mock_cache):
        """Test get_cached_positions returns all positions."""
        mock_positions = [MagicMock() for _ in range(3)]
        mock_cache.positions.return_value = mock_positions
        positions = recovery_provider.get_cached_positions(trader_id="TRADER-001")
        assert len(positions) == 3

    def test_get_exchange_positions(self, recovery_provider, mock_cache):
        """Test get_exchange_positions queries cache (default impl)."""
        mock_positions = [MagicMock() for _ in range(2)]
        mock_cache.positions.return_value = mock_positions
        positions = recovery_provider.get_exchange_positions(trader_id="TRADER-001")
        assert len(positions) == 2

    def test_reconcile_positions_no_discrepancies(self, recovery_provider, mock_position):
        """Test reconcile_positions with matching positions."""
        mock_position.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        mock_position.side.value = "LONG"
        mock_position.quantity.as_decimal.return_value = Decimal("1.5")

        reconciled, discrepancies = recovery_provider.reconcile_positions(
            cached=[mock_position],
            exchange=[mock_position],
        )
        assert len(reconciled) == 1
        assert len(discrepancies) == 0
        assert recovery_provider.discrepancy_count == 0

    def test_reconcile_positions_quantity_mismatch(self, recovery_provider):
        """Test reconcile_positions detects quantity mismatch."""
        cached_pos = MagicMock()
        cached_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        cached_pos.side.value = "LONG"
        cached_pos.quantity.as_decimal.return_value = Decimal("1.0")

        exchange_pos = MagicMock()
        exchange_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        exchange_pos.side.value = "LONG"
        exchange_pos.quantity.as_decimal.return_value = Decimal("2.0")

        reconciled, discrepancies = recovery_provider.reconcile_positions(
            cached=[cached_pos],
            exchange=[exchange_pos],
        )
        assert len(reconciled) == 1
        assert len(discrepancies) == 1
        assert "Quantity mismatch" in discrepancies[0]
        assert recovery_provider.discrepancy_count == 1

    def test_reconcile_positions_side_mismatch(self, recovery_provider):
        """Test reconcile_positions detects side mismatch."""
        cached_pos = MagicMock()
        cached_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        cached_pos.side.value = "LONG"
        cached_pos.quantity.as_decimal.return_value = Decimal("1.0")

        exchange_pos = MagicMock()
        exchange_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        exchange_pos.side.value = "SHORT"
        exchange_pos.quantity.as_decimal.return_value = Decimal("1.0")

        reconciled, discrepancies = recovery_provider.reconcile_positions(
            cached=[cached_pos],
            exchange=[exchange_pos],
        )
        assert len(reconciled) == 1
        assert len(discrepancies) == 1
        assert "Side mismatch" in discrepancies[0]

    def test_reconcile_positions_external_position(self, recovery_provider):
        """Test reconcile_positions detects external position."""
        exchange_pos = MagicMock()
        exchange_pos.instrument_id.value = "ETHUSDT-PERP.BINANCE"
        exchange_pos.side.value = "LONG"
        exchange_pos.quantity.as_decimal.return_value = Decimal("10.0")

        reconciled, discrepancies = recovery_provider.reconcile_positions(
            cached=[],
            exchange=[exchange_pos],
        )
        assert len(reconciled) == 1
        assert len(discrepancies) == 1
        assert "External position detected" in discrepancies[0]

    def test_reconcile_positions_closed_on_exchange(self, recovery_provider):
        """Test reconcile_positions detects closed positions."""
        cached_pos = MagicMock()
        cached_pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        cached_pos.side.value = "LONG"
        cached_pos.quantity.as_decimal.return_value = Decimal("1.0")

        reconciled, discrepancies = recovery_provider.reconcile_positions(
            cached=[cached_pos],
            exchange=[],
        )
        assert len(reconciled) == 0
        assert len(discrepancies) == 1
        assert "Position closed on exchange" in discrepancies[0]

    def test_reconcile_positions_duplicate_instrument_ids(self, recovery_provider):
        """Test reconcile_positions warns on duplicate instrument_ids."""
        pos1 = MagicMock()
        pos1.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        pos1.side.value = "LONG"
        pos1.quantity.as_decimal.return_value = Decimal("1.0")

        pos2 = MagicMock()
        pos2.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        pos2.side.value = "SHORT"
        pos2.quantity.as_decimal.return_value = Decimal("2.0")

        # Should log warning but not crash
        reconciled, discrepancies = recovery_provider.reconcile_positions(
            cached=[pos1, pos2],
            exchange=[pos1],
        )
        # Latest position overwrites in dict
        assert len(reconciled) >= 1

    def test_get_cached_balances_no_account(self, recovery_provider, mock_cache):
        """Test get_cached_balances with no account in cache."""
        mock_cache.account.return_value = None
        balances = recovery_provider.get_cached_balances(trader_id="TRADER-001")
        assert len(balances) == 0

    def test_get_cached_balances_with_account(self, recovery_provider, mock_cache, mock_balance):
        """Test get_cached_balances returns account balances."""
        mock_account = MagicMock()
        mock_account.balances.return_value = [mock_balance]
        mock_cache.account.return_value = mock_account

        balances = recovery_provider.get_cached_balances(trader_id="TRADER-001")
        assert len(balances) == 1

    def test_reconcile_balances_no_changes(self, recovery_provider, mock_balance):
        """Test reconcile_balances with matching balances."""
        reconciled, changes = recovery_provider.reconcile_balances(
            cached=[mock_balance],
            exchange=[mock_balance],
        )
        assert len(reconciled) == 1
        assert len(changes) == 0
        assert recovery_provider.balance_change_count == 0

    def test_reconcile_balances_total_mismatch(self, recovery_provider):
        """Test reconcile_balances detects total balance mismatch."""
        cached_bal = MagicMock()
        cached_bal.currency.code = "USDT"
        cached_bal.total.as_decimal.return_value = Decimal("10000.00")
        cached_bal.locked.as_decimal.return_value = Decimal("1000.00")

        exchange_bal = MagicMock()
        exchange_bal.currency.code = "USDT"
        exchange_bal.total.as_decimal.return_value = Decimal("12000.00")
        exchange_bal.locked.as_decimal.return_value = Decimal("1000.00")

        reconciled, changes = recovery_provider.reconcile_balances(
            cached=[cached_bal],
            exchange=[exchange_bal],
        )
        assert len(reconciled) == 1
        assert len(changes) == 1
        assert "Total balance mismatch" in changes[0]

    def test_reconcile_balances_locked_mismatch(self, recovery_provider):
        """Test reconcile_balances detects locked balance mismatch."""
        cached_bal = MagicMock()
        cached_bal.currency.code = "USDT"
        cached_bal.total.as_decimal.return_value = Decimal("10000.00")
        cached_bal.locked.as_decimal.return_value = Decimal("1000.00")

        exchange_bal = MagicMock()
        exchange_bal.currency.code = "USDT"
        exchange_bal.total.as_decimal.return_value = Decimal("10000.00")
        exchange_bal.locked.as_decimal.return_value = Decimal("2000.00")

        reconciled, changes = recovery_provider.reconcile_balances(
            cached=[cached_bal],
            exchange=[exchange_bal],
        )
        assert len(reconciled) == 1
        assert len(changes) == 1
        assert "Locked balance mismatch" in changes[0]

    def test_reconcile_balances_new_currency(self, recovery_provider):
        """Test reconcile_balances detects new currency."""
        exchange_bal = MagicMock()
        exchange_bal.currency.code = "BTC"
        exchange_bal.total.as_decimal.return_value = Decimal("1.5")
        exchange_bal.locked.as_decimal.return_value = Decimal("0.0")

        reconciled, changes = recovery_provider.reconcile_balances(
            cached=[],
            exchange=[exchange_bal],
        )
        assert len(reconciled) == 1
        assert len(changes) == 1
        assert "New balance detected" in changes[0]

    def test_reconcile_balances_removed_currency(self, recovery_provider):
        """Test reconcile_balances detects removed currency."""
        cached_bal = MagicMock()
        cached_bal.currency.code = "ETH"
        cached_bal.total.as_decimal.return_value = Decimal("10.0")

        reconciled, changes = recovery_provider.reconcile_balances(
            cached=[cached_bal],
            exchange=[],
        )
        assert len(reconciled) == 0
        assert len(changes) == 1
        assert "Balance removed from exchange" in changes[0]

    def test_compute_balance_delta_increase(self, recovery_provider):
        """Test compute_balance_delta calculates increase correctly."""
        cached = MagicMock()
        cached.total.as_decimal.return_value = Decimal("10000.00")
        cached.locked.as_decimal.return_value = Decimal("1000.00")

        exchange = MagicMock()
        exchange.total.as_decimal.return_value = Decimal("15000.00")
        exchange.locked.as_decimal.return_value = Decimal("1500.00")

        delta = recovery_provider.compute_balance_delta(
            currency="USDT",
            cached=cached,
            exchange=exchange,
        )
        assert delta["currency"] == "USDT"
        assert delta["total_change"] == Decimal("5000.00")
        assert delta["percent_change"] == 50.0
        assert delta["locked_change"] == Decimal("500.00")
        assert delta["is_new"] is False
        assert delta["is_removed"] is False

    def test_compute_balance_delta_new_currency(self, recovery_provider):
        """Test compute_balance_delta for new currency."""
        exchange = MagicMock()
        exchange.total.as_decimal.return_value = Decimal("5000.00")
        exchange.locked.as_decimal.return_value = Decimal("0.00")

        delta = recovery_provider.compute_balance_delta(
            currency="BTC",
            cached=None,
            exchange=exchange,
        )
        assert delta["is_new"] is True
        assert delta["cached_total"] == Decimal("0")
        assert delta["exchange_total"] == Decimal("5000.00")
        assert delta["percent_change"] == 100.0

    def test_compute_balance_delta_removed_currency(self, recovery_provider):
        """Test compute_balance_delta for removed currency."""
        cached = MagicMock()
        cached.total.as_decimal.return_value = Decimal("1000.00")
        cached.locked.as_decimal.return_value = Decimal("0.00")

        delta = recovery_provider.compute_balance_delta(
            currency="ETH",
            cached=cached,
            exchange=None,
        )
        assert delta["is_removed"] is True
        assert delta["cached_total"] == Decimal("1000.00")
        assert delta["exchange_total"] == Decimal("0")

    def test_is_significant_change_large_percent(self, recovery_provider):
        """Test is_significant_change detects large percent changes."""
        delta = {
            "percent_change": 25.0,
            "is_new": False,
            "is_removed": False,
        }
        assert recovery_provider.is_significant_change(delta, threshold_percent=10.0) is True

    def test_is_significant_change_below_threshold(self, recovery_provider):
        """Test is_significant_change ignores small changes."""
        delta = {
            "percent_change": 5.0,
            "is_new": False,
            "is_removed": False,
        }
        assert recovery_provider.is_significant_change(delta, threshold_percent=10.0) is False

    def test_is_significant_change_new_currency(self, recovery_provider):
        """Test is_significant_change always flags new currencies."""
        delta = {
            "percent_change": 0.0,
            "is_new": True,
            "is_removed": False,
        }
        assert recovery_provider.is_significant_change(delta, threshold_percent=10.0) is True


# =============================================================================
# RecoveryEventEmitter Tests
# =============================================================================


class TestRecoveryEventEmitter:
    """Tests for RecoveryEventEmitter event emission."""

    def test_emit_recovery_started(self, event_emitter):
        """Test emit_recovery_started creates RecoveryStartedEvent."""
        event = event_emitter.emit_recovery_started(cached_positions_count=5)
        assert isinstance(event, RecoveryStartedEvent)
        assert event.trader_id == "TRADER-TEST-001"
        assert event.cached_positions_count == 5
        assert event.ts_event > 0

    def test_emit_position_loaded(self, event_emitter):
        """Test emit_position_loaded creates PositionLoadedEvent."""
        event = event_emitter.emit_position_loaded(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="LONG",
            quantity="1.5",
            avg_entry_price="42000.00",
        )
        assert isinstance(event, PositionLoadedEvent)
        assert event.instrument_id == "BTCUSDT-PERP.BINANCE"
        assert event.side == "LONG"
        assert event.quantity == "1.5"

    def test_emit_position_reconciled(self, event_emitter):
        """Test emit_position_reconciled creates PositionReconciledEvent."""
        event = event_emitter.emit_position_reconciled(
            instrument_id="BTCUSDT-PERP.BINANCE",
            cached_quantity="1.0",
            exchange_quantity="1.5",
            reconciled=True,
        )
        assert isinstance(event, PositionReconciledEvent)
        assert event.reconciled is True

    def test_emit_position_discrepancy(self, event_emitter):
        """Test emit_position_discrepancy creates PositionDiscrepancyEvent."""
        event = event_emitter.emit_position_discrepancy(
            instrument_id="ETHUSDT-PERP.BINANCE",
            resolution="External position claimed",
            cached_side=None,
            exchange_side="LONG",
        )
        assert isinstance(event, PositionDiscrepancyEvent)
        assert event.resolution == "External position claimed"

    def test_emit_indicators_warming(self, event_emitter):
        """Test emit_indicators_warming creates IndicatorsWarmingEvent."""
        event = event_emitter.emit_indicators_warming(
            strategy_id="STRATEGY-001",
            indicator_count=3,
            lookback_days=2,
        )
        assert isinstance(event, IndicatorsWarmingEvent)
        assert event.indicator_count == 3

    def test_emit_warmup_complete(self, event_emitter):
        """Test emit_warmup_complete creates IndicatorsReadyEvent."""
        event = event_emitter.emit_warmup_complete(
            strategy_id="STRATEGY-001",
            warmup_duration_ms=1500.5,
            bars_processed=200,
        )
        assert isinstance(event, IndicatorsReadyEvent)
        assert event.warmup_duration_ms == 1500.5
        assert event.bars_processed == 200

    def test_emit_reconciliation_complete(self, event_emitter):
        """Test emit_reconciliation_complete creates RecoveryCompletedEvent."""
        event = event_emitter.emit_reconciliation_complete(
            positions_recovered=5,
            discrepancies_resolved=2,
            total_duration_ms=3000.0,
            strategies_ready=3,
        )
        assert isinstance(event, RecoveryCompletedEvent)
        assert event.positions_recovered == 5

    def test_emit_recovery_failed(self, event_emitter):
        """Test emit_recovery_failed creates RecoveryFailedEvent."""
        event = event_emitter.emit_recovery_failed(
            error_code="CACHE_ERROR",
            error_message="Cache connection failed",
            positions_recovered=2,
            recoverable=True,
        )
        assert isinstance(event, RecoveryFailedEvent)
        assert event.error_code == "CACHE_ERROR"
        assert event.recoverable is True

    def test_emit_recovery_timeout(self, event_emitter):
        """Test emit_recovery_timeout creates RecoveryTimeoutEvent."""
        event = event_emitter.emit_recovery_timeout(
            timeout_secs=30.0,
            elapsed_secs=45.0,
            positions_recovered=3,
        )
        assert isinstance(event, RecoveryTimeoutEvent)
        assert event.timeout_secs == 30.0
        assert event.elapsed_secs == 45.0

    def test_event_callback_invoked(self, event_emitter):
        """Test on_event callback is invoked for each event."""
        events = []

        def callback(event):
            events.append(event)

        emitter = RecoveryEventEmitter(
            trader_id="TRADER-001",
            on_event=callback,
        )
        emitter.emit_recovery_started(cached_positions_count=5)
        assert len(events) == 1
        assert isinstance(events[0], RecoveryStartedEvent)


# =============================================================================
# EventReplayManager Tests
# =============================================================================


class TestEventReplayManager:
    """Tests for EventReplayManager event replay and synthesis."""

    def test_replay_events_empty_cache(self, event_replay_manager, mock_cache):
        """Test replay_events with empty cache."""
        mock_cache.position_events.return_value = []
        events = event_replay_manager.replay_events(trader_id="TRADER-001")
        assert len(events) == 0

    def test_replay_events_no_position_events_method(self, event_replay_manager, mock_cache):
        """Test replay_events gracefully handles missing position_events method."""
        del mock_cache.position_events
        events = event_replay_manager.replay_events(trader_id="TRADER-001")
        assert len(events) == 0

    def test_replay_events_sorted_by_timestamp(self, event_replay_manager, mock_cache):
        """Test replay_events returns events sorted by timestamp."""
        event1 = MagicMock()
        event1.ts_event = 3_000_000_000_000
        event2 = MagicMock()
        event2.ts_event = 1_000_000_000_000
        event3 = MagicMock()
        event3.ts_event = 2_000_000_000_000

        mock_cache.position_events.return_value = [event1, event2, event3]
        events = event_replay_manager.replay_events(trader_id="TRADER-001")
        assert events[0].ts_event == 1_000_000_000_000
        assert events[1].ts_event == 2_000_000_000_000
        assert events[2].ts_event == 3_000_000_000_000

    def test_replay_events_instrument_filter(self, event_replay_manager, mock_cache):
        """Test replay_events filters by instrument_id."""
        event_btc = MagicMock()
        event_btc.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        event_btc.ts_event = 1_000_000_000_000

        event_eth = MagicMock()
        event_eth.instrument_id.value = "ETHUSDT-PERP.BINANCE"
        event_eth.ts_event = 2_000_000_000_000

        mock_cache.position_events.return_value = [event_btc, event_eth]
        events = event_replay_manager.replay_events(
            trader_id="TRADER-001",
            instrument_id="BTCUSDT-PERP.BINANCE",
        )
        assert len(events) == 1
        assert events[0].instrument_id.value == "BTCUSDT-PERP.BINANCE"

    def test_replay_events_time_range_filter(self, event_replay_manager, mock_cache):
        """Test replay_events filters by time range."""
        event1 = MagicMock()
        event1.ts_event = 1_000_000_000_000
        event2 = MagicMock()
        event2.ts_event = 2_000_000_000_000
        event3 = MagicMock()
        event3.ts_event = 3_000_000_000_000

        mock_cache.position_events.return_value = [event1, event2, event3]
        events = event_replay_manager.replay_events(
            trader_id="TRADER-001",
            start_ns=1_500_000_000_000,
            end_ns=2_500_000_000_000,
        )
        assert len(events) == 1
        assert events[0].ts_event == 2_000_000_000_000

    def test_get_next_sequence_number_increments(self, event_replay_manager):
        """Test get_next_sequence_number increments correctly."""
        seq1 = event_replay_manager.get_next_sequence_number(trader_id="TRADER-001")
        seq2 = event_replay_manager.get_next_sequence_number(trader_id="TRADER-001")
        assert seq2 == seq1 + 1

    def test_reset_sequence(self, event_replay_manager):
        """Test reset_sequence resets to specified value."""
        event_replay_manager.get_next_sequence_number(trader_id="TRADER-001")
        event_replay_manager.reset_sequence(sequence=0)
        seq = event_replay_manager.get_next_sequence_number(trader_id="TRADER-001")
        assert seq == 1

    def test_generate_position_opened_event(self, event_replay_manager, position_snapshot):
        """Test generate_position_opened_event creates synthetic event."""
        event = event_replay_manager.generate_position_opened_event(
            position=position_snapshot,
            ts_event=1_000_000_000_000,
        )
        assert isinstance(event, SyntheticEvent)
        assert event.event_type == "position.opened"
        assert event.instrument_id == "BTCUSDT-PERP.BINANCE"
        assert event.side == "LONG"
        assert event.quantity == Decimal("1.5")
        assert event.is_synthetic is True

    def test_generate_position_opened_event_requires_position(self, event_replay_manager):
        """Test generate_position_opened_event raises if position is None."""
        with pytest.raises(ValueError, match="position is required"):
            event_replay_manager.generate_position_opened_event(
                position=None,
                ts_event=1_000_000_000_000,
            )

    def test_generate_position_changed_event(self, event_replay_manager, position_snapshot):
        """Test generate_position_changed_event creates synthetic event."""
        event = event_replay_manager.generate_position_changed_event(
            position=position_snapshot,
            previous_quantity=Decimal("1.0"),
            ts_event=1_000_000_000_000,
        )
        assert event.event_type == "position.changed"
        assert event.previous_quantity == Decimal("1.0")
        assert event.quantity == Decimal("1.5")

    def test_generate_synthetic_fill_event(self, event_replay_manager):
        """Test generate_synthetic_fill_event creates fill event."""
        event = event_replay_manager.generate_synthetic_fill_event(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="BUY",
            quantity=Decimal("1.5"),
            price=Decimal("42000.00"),
            ts_event=1_000_000_000_000,
        )
        assert event.event_type == "order.filled"
        assert event.side == "BUY"
        assert event.quantity == Decimal("1.5")

    def test_generate_synthetic_fill_event_invalid_quantity(self, event_replay_manager):
        """Test generate_synthetic_fill_event raises if quantity <= 0."""
        with pytest.raises(ValueError, match="quantity must be positive"):
            event_replay_manager.generate_synthetic_fill_event(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="BUY",
                quantity=Decimal("0"),
                price=Decimal("42000.00"),
                ts_event=1_000_000_000_000,
            )

    def test_generate_synthetic_events_for_position(self, event_replay_manager, position_snapshot):
        """Test generate_synthetic_events creates events for position."""
        events = event_replay_manager.generate_synthetic_events(
            position=position_snapshot,
            ts_recovery=2_000_000_000_000,
        )
        assert len(events) >= 1
        assert events[0].event_type == "position.opened"

    def test_detect_event_gaps_no_events(self, event_replay_manager, mock_cache):
        """Test detect_event_gaps returns empty list with no events."""
        mock_cache.position_events.return_value = []
        gaps = event_replay_manager.detect_event_gaps(trader_id="TRADER-001")
        assert len(gaps) == 0

    def test_detect_event_gaps_sequence_gap(self, event_replay_manager, mock_cache):
        """Test detect_event_gaps detects missing sequence numbers."""
        event1 = MagicMock()
        event1.sequence = 1
        event1.ts_event = 1_000_000_000_000

        event2 = MagicMock()
        event2.sequence = 5
        event2.ts_event = 2_000_000_000_000

        mock_cache.position_events.return_value = [event1, event2]
        gaps = event_replay_manager.detect_event_gaps(trader_id="TRADER-001")
        assert len(gaps) >= 1
        assert gaps[0]["start_seq"] == 2
        assert gaps[0]["end_seq"] == 4

    def test_fill_event_gap(self, event_replay_manager, position_snapshot):
        """Test fill_event_gap generates synthetic events."""
        gap = {
            "start_seq": 2,
            "end_seq": 4,
            "start_ts": 1_000_000_000_000,
            "end_ts": 2_000_000_000_000,
        }
        events = event_replay_manager.fill_event_gap(
            gap=gap,
            position=position_snapshot,
        )
        assert len(events) >= 1
        assert events[0].is_synthetic is True


# =============================================================================
# RecoveryConfig Tests
# =============================================================================


class TestRecoveryConfig:
    """Tests for RecoveryConfig validation."""

    def test_valid_config(self, recovery_config):
        """Test valid RecoveryConfig creation."""
        assert recovery_config.trader_id == "TRADER-TEST-001"
        assert recovery_config.recovery_enabled is True
        assert recovery_config.warmup_lookback_days == 2

    def test_max_recovery_time_validation(self):
        """Test max_recovery_time must exceed startup_delay."""
        with pytest.raises(ValidationError, match="must exceed startup_delay_secs"):
            RecoveryConfig(
                trader_id="TRADER-001",
                startup_delay_secs=20.0,
                max_recovery_time_secs=15.0,
            )

    def test_warmup_lookback_days_range(self):
        """Test warmup_lookback_days validation."""
        with pytest.raises(ValidationError):
            RecoveryConfig(
                trader_id="TRADER-001",
                warmup_lookback_days=0,  # Must be >= 1
            )

        with pytest.raises(ValidationError):
            RecoveryConfig(
                trader_id="TRADER-001",
                warmup_lookback_days=100,  # Must be <= 30
            )

    def test_config_is_frozen(self, recovery_config):
        """Test RecoveryConfig is immutable."""
        with pytest.raises(ValidationError):
            recovery_config.recovery_enabled = False


# =============================================================================
# RecoveryState and Models Tests
# =============================================================================


class TestRecoveryModels:
    """Tests for recovery data models."""

    def test_recovery_state_defaults(self):
        """Test RecoveryState default values."""
        state = RecoveryState()
        assert state.status == RecoveryStatus.PENDING
        assert state.positions_recovered == 0
        assert state.indicators_warmed is False
        assert state.orders_reconciled is False

    def test_recovery_state_duration_calculation(self):
        """Test recovery_duration_ms property calculation."""
        state = RecoveryState(
            ts_started=1_000_000_000_000,
            ts_completed=1_002_000_000_000,
        )
        assert state.recovery_duration_ms == 2000.0

    def test_recovery_state_duration_none_if_incomplete(self):
        """Test recovery_duration_ms is None if not completed."""
        state = RecoveryState(ts_started=1_000_000_000_000)
        assert state.recovery_duration_ms is None

    def test_recovery_state_is_complete(self):
        """Test is_complete property."""
        state = RecoveryState(
            status=RecoveryStatus.COMPLETED,
            indicators_warmed=True,
            orders_reconciled=True,
        )
        assert state.is_complete is True

        state = RecoveryState(
            status=RecoveryStatus.COMPLETED,
            indicators_warmed=False,
            orders_reconciled=True,
        )
        assert state.is_complete is False

    def test_position_snapshot_valid(self, position_snapshot):
        """Test PositionSnapshot validation."""
        assert position_snapshot.instrument_id == "BTCUSDT-PERP.BINANCE"
        assert position_snapshot.side == "LONG"
        assert position_snapshot.quantity == Decimal("1.5")

    def test_position_snapshot_side_validation(self):
        """Test PositionSnapshot side validation."""
        snapshot = PositionSnapshot(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="long",  # Lowercase should be converted
            quantity=Decimal("1.0"),
            avg_entry_price=Decimal("42000.00"),
            ts_opened=1_000_000_000_000,
            ts_last_updated=1_000_001_000_000,
        )
        assert snapshot.side == "LONG"

        with pytest.raises(ValidationError, match="Invalid position side"):
            PositionSnapshot(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="INVALID",
                quantity=Decimal("1.0"),
                avg_entry_price=Decimal("42000.00"),
                ts_opened=1_000_000_000_000,
                ts_last_updated=1_000_001_000_000,
            )

    def test_position_snapshot_timestamp_validation(self):
        """Test PositionSnapshot timestamp validation."""
        with pytest.raises(ValidationError, match="cannot be before ts_opened"):
            PositionSnapshot(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="LONG",
                quantity=Decimal("1.0"),
                avg_entry_price=Decimal("42000.00"),
                ts_opened=2_000_000_000_000,
                ts_last_updated=1_000_000_000_000,  # Before ts_opened
            )

    def test_indicator_state_valid(self):
        """Test IndicatorState creation."""
        state = IndicatorState(
            name="EMA-20",
            period=20,
            value=42000.0,
            is_ready=True,
            warmup_count=25,
        )
        assert state.name == "EMA-20"
        assert state.period == 20

    def test_strategy_snapshot_valid(self):
        """Test StrategySnapshot creation."""
        snapshot = StrategySnapshot(
            strategy_id="STRATEGY-001",
            indicator_states=[
                IndicatorState(name="EMA-20", period=20),
            ],
            custom_state={"last_signal": "BUY"},
            pending_signals=["SIGNAL-1"],
            ts_saved=1_000_000_000_000,
        )
        assert len(snapshot.indicator_states) == 1
        assert snapshot.custom_state["last_signal"] == "BUY"


# =============================================================================
# RecoverableStrategy Tests (Integration)
# =============================================================================


class TestRecoverableStrategy:
    """Tests for RecoverableStrategy base class."""

    @pytest.fixture
    def strategy_config(self, recovery_config):
        """RecoverableStrategyConfig for tests."""
        return RecoverableStrategyConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            recovery=recovery_config,
        )

    @pytest.fixture
    def mock_strategy_deps(self):
        """Mock dependencies for RecoverableStrategy."""
        deps = {
            "cache": MagicMock(),
            "clock": MagicMock(),
            "trader_id": "TRADER-001",
        }
        deps["cache"].instrument.return_value = MagicMock()
        deps["cache"].positions.return_value = []
        deps["cache"].orders_open.return_value = []
        deps["clock"].timestamp_ns.return_value = 1_000_000_000_000
        deps["clock"].utc_now.return_value = MagicMock()
        return deps

    def test_strategy_initialization(self, strategy_config, mock_strategy_deps):
        """Test RecoverableStrategy initialization."""
        with patch.object(RecoverableStrategy, "cache", new_callable=PropertyMock) as mock_cache:
            mock_cache.return_value = mock_strategy_deps["cache"]
            with patch.object(RecoverableStrategy, "clock", new_callable=PropertyMock) as mock_clock:
                mock_clock.return_value = mock_strategy_deps["clock"]
                with patch.object(RecoverableStrategy, "trader_id", new_callable=PropertyMock) as mock_trader:
                    mock_trader.return_value = "TRADER-001"

                    strategy = RecoverableStrategy(config=strategy_config)
                    assert strategy.instrument_id.value == "BTCUSDT-PERP.BINANCE"
                    assert strategy.recovery_config.trader_id == "TRADER-TEST-001"

    def test_strategy_default_recovery_config(self):
        """Test RecoverableStrategy uses default recovery config if not provided."""
        config = RecoverableStrategyConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            recovery=None,
        )
        with patch.object(RecoverableStrategy, "trader_id", new_callable=PropertyMock) as mock_trader:
            mock_trader.return_value = "TRADER-001"
            strategy = RecoverableStrategy(config=config)
            assert strategy.recovery_config is not None
            assert strategy.recovery_config.recovery_enabled is True

    def test_is_warming_up_property(self, strategy_config):
        """Test is_warming_up property."""
        strategy = RecoverableStrategy(config=strategy_config)
        assert strategy.is_warming_up is True
        strategy._warmup_complete = True
        assert strategy.is_warming_up is False

    def test_is_ready_property(self, strategy_config):
        """Test is_ready property."""
        strategy = RecoverableStrategy(config=strategy_config)
        assert strategy.is_ready is False

        strategy._warmup_complete = True
        strategy.recovery_state = RecoveryState(status=RecoveryStatus.COMPLETED)
        assert strategy.is_ready is True

    def test_recovered_positions_count_property(self, strategy_config):
        """Test recovered_positions_count property."""
        strategy = RecoverableStrategy(config=strategy_config)
        assert strategy.recovered_positions_count == 0

        mock_pos1 = MagicMock()
        mock_pos2 = MagicMock()
        strategy._recovered_positions = [mock_pos1, mock_pos2]
        assert strategy.recovered_positions_count == 2


# =============================================================================
# Edge Cases and Stress Tests
# =============================================================================


class TestEdgeCases:
    """Edge case and stress tests for recovery module."""

    def test_concurrent_state_saves_no_data_loss(self, state_manager):
        """Test concurrent saves don't corrupt state file."""
        state_manager.start_recovery()
        save_count = [0]
        errors = []

        def save_repeatedly():
            try:
                for _i in range(20):
                    state_manager.increment_positions_recovered(count=1)
                    state_manager.save_state()
                    save_count[0] += 1
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=save_repeatedly) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # State should be loadable
        loaded = state_manager.load_state()
        assert loaded is not None

    def test_empty_reconciliation(self, recovery_provider):
        """Test reconciliation with empty lists."""
        reconciled, discrepancies = recovery_provider.reconcile_positions(
            cached=[],
            exchange=[],
        )
        assert len(reconciled) == 0
        assert len(discrepancies) == 0

    def test_large_position_list_reconciliation(self, recovery_provider):
        """Test reconciliation with large position lists."""
        # Create 1000 mock positions
        positions = []
        for i in range(1000):
            pos = MagicMock()
            pos.instrument_id.value = f"INST-{i}.EXCHANGE"
            pos.side.value = "LONG"
            pos.quantity.as_decimal.return_value = Decimal("1.0")
            positions.append(pos)

        reconciled, discrepancies = recovery_provider.reconcile_positions(
            cached=positions,
            exchange=positions,
        )
        assert len(reconciled) == 1000
        assert len(discrepancies) == 0

    def test_state_file_corruption_recovery(self, state_manager):
        """Test graceful handling of corrupted state file."""
        state_manager.start_recovery()
        state_manager.save_state()

        # Corrupt the file
        state_manager.state_file_path.write_text("corrupted data")

        # Should raise exception, not crash silently
        with pytest.raises(Exception):
            state_manager.load_state()

    def test_missing_state_directory_parent(self, temp_state_dir):
        """Test state manager creates missing parent directories."""
        nested_dir = temp_state_dir / "level1" / "level2" / "level3"
        RecoveryStateManager(
            trader_id="TRADER-001",
            state_dir=nested_dir,
        )
        assert nested_dir.exists()

    def test_zero_positions_recovered(self, state_manager):
        """Test recovery with zero positions recovered."""
        state_manager.start_recovery()
        state = state_manager.complete_recovery()
        assert state.positions_recovered == 0
        assert state.status == RecoveryStatus.COMPLETED

    def test_event_emission_without_callback(self, event_emitter):
        """Test event emission works without on_event callback."""
        event = event_emitter.emit_recovery_started(cached_positions_count=0)
        assert isinstance(event, RecoveryStartedEvent)

    def test_replay_manager_sequence_overflow(self, event_replay_manager):
        """Test sequence number can handle large values."""
        event_replay_manager._sequence_number = 999_999_999
        seq = event_replay_manager.get_next_sequence_number(trader_id="TRADER-001")
        assert seq == 1_000_000_000


# =============================================================================
# Performance Benchmarks (Light)
# =============================================================================


class TestPerformance:
    """Light performance tests for recovery operations."""

    def test_reconciliation_performance_1000_positions(self, recovery_provider):
        """Test reconciliation completes quickly with 1000 positions."""
        positions = []
        for i in range(1000):
            pos = MagicMock()
            pos.instrument_id.value = f"INST-{i}.EXCHANGE"
            pos.side.value = "LONG"
            pos.quantity.as_decimal.return_value = Decimal("1.0")
            positions.append(pos)

        start = time.time()
        reconciled, discrepancies = recovery_provider.reconcile_positions(
            cached=positions,
            exchange=positions,
        )
        duration = time.time() - start

        # Should complete in < 1 second for O(n+m) algorithm
        assert duration < 1.0
        assert len(reconciled) == 1000

    def test_state_save_load_performance(self, state_manager):
        """Test state save/load completes quickly."""
        state_manager.start_recovery()
        for _ in range(100):
            state_manager.increment_positions_recovered(count=1)

        start = time.time()
        for _ in range(10):
            state_manager.save_state()
            state_manager.load_state()
        duration = time.time() - start

        # 10 save/load cycles should complete in < 0.5 seconds
        assert duration < 0.5


# =============================================================================
# Additional Tests for Coverage (90%+ Target)
# =============================================================================


class TestRecoverableStrategyMethods:
    """Test RecoverableStrategy internal methods directly.

    Uses PropertyMock to patch Cython attributes correctly.
    Covers lines: 242, 280, 353, 400
    """

    @pytest.fixture
    def strategy_config(self):
        """RecoverableStrategyConfig for tests."""
        return RecoverableStrategyConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            recovery=RecoveryConfig(
                trader_id="TRADER-TEST-001",
                recovery_enabled=True,
                warmup_lookback_days=2,
            ),
        )

    @pytest.fixture
    def mock_open_position(self):
        """Mock open position for recovery testing."""
        pos = MagicMock()
        pos.instrument_id = MagicMock()
        pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        pos.side = MagicMock()
        pos.side.value = "LONG"
        pos.quantity = MagicMock()
        pos.quantity.as_decimal = MagicMock(return_value=Decimal("1.5"))
        pos.avg_px_open = Decimal("42000.00")
        pos.is_open = True
        return pos

    def test_is_stop_order_stop_market_type(self, strategy_config):
        """Test _is_stop_order() returns True for STOP_MARKET (line 280)."""
        from nautilus_trader.model.enums import OrderType

        strategy = RecoverableStrategy(config=strategy_config)
        order = MagicMock()
        order.order_type = OrderType.STOP_MARKET

        assert strategy._is_stop_order(order) is True

    def test_is_stop_order_stop_limit_type(self, strategy_config):
        """Test _is_stop_order() returns True for STOP_LIMIT (line 280)."""
        from nautilus_trader.model.enums import OrderType

        strategy = RecoverableStrategy(config=strategy_config)
        order = MagicMock()
        order.order_type = OrderType.STOP_LIMIT

        assert strategy._is_stop_order(order) is True

    def test_is_stop_order_limit_type(self, strategy_config):
        """Test _is_stop_order() returns False for LIMIT order (line 280)."""
        from nautilus_trader.model.enums import OrderType

        strategy = RecoverableStrategy(config=strategy_config)
        order = MagicMock()
        order.order_type = OrderType.LIMIT

        assert strategy._is_stop_order(order) is False

    def test_is_stop_order_market_type(self, strategy_config):
        """Test _is_stop_order() returns False for MARKET order (line 280)."""
        from nautilus_trader.model.enums import OrderType

        strategy = RecoverableStrategy(config=strategy_config)
        order = MagicMock()
        order.order_type = OrderType.MARKET

        assert strategy._is_stop_order(order) is False

    def test_on_historical_data_hook_noop(self, strategy_config):
        """Test on_historical_data() is a no-op hook (line 353)."""
        strategy = RecoverableStrategy(config=strategy_config)
        mock_bar = MagicMock()

        # Should not raise, just pass
        result = strategy.on_historical_data(mock_bar)
        assert result is None

    def test_on_warmup_complete_hook_noop(self, strategy_config):
        """Test on_warmup_complete() is a no-op hook (line 400)."""
        strategy = RecoverableStrategy(config=strategy_config)

        # Should not raise, just pass
        result = strategy.on_warmup_complete()
        assert result is None

    def test_on_position_recovered_hook_noop(self, strategy_config, mock_open_position):
        """Test on_position_recovered() is a no-op hook (line 242)."""
        strategy = RecoverableStrategy(config=strategy_config)

        # Should not raise, just pass
        result = strategy.on_position_recovered(mock_open_position)
        assert result is None


class TestRecoverableStrategyWithMockedCacheAndClock:
    """Test RecoverableStrategy methods that require mocked cache.

    Uses PropertyMock to patch Cython attributes correctly.
    Covers lines: 183-189, 202-225, 259-265
    """

    @pytest.fixture
    def strategy_config(self):
        return RecoverableStrategyConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            recovery=RecoveryConfig(
                trader_id="TRADER-TEST-001",
                recovery_enabled=True,
            ),
        )

    @pytest.fixture
    def mock_open_position(self):
        """Mock open position."""
        pos = MagicMock()
        pos.instrument_id = MagicMock()
        pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        pos.side = MagicMock()
        pos.side.value = "LONG"
        pos.quantity = MagicMock()
        pos.quantity.as_decimal = MagicMock(return_value=Decimal("1.5"))
        pos.avg_px_open = Decimal("42000.00")
        pos.is_open = True
        return pos

    def test_handle_recovered_position_updates_state(
        self, strategy_config, mock_open_position
    ):
        """Test _handle_recovered_position updates recovery state (lines 202-210)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=1_000_000_000_000,
        )

        # Mock cache to avoid None access
        mock_cache = MagicMock()
        mock_cache.orders_open.return_value = []

        with patch.object(type(strategy), 'cache', new_callable=PropertyMock) as mock_cache_prop:
            mock_cache_prop.return_value = mock_cache
            with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
                mock_logger = MagicMock()
                mock_log_prop.return_value = mock_logger

                strategy._handle_recovered_position(mock_open_position)

        assert len(strategy._recovered_positions) == 1
        assert strategy.recovery_state.positions_recovered == 1

    def test_handle_recovered_position_logs_details(
        self, strategy_config, mock_open_position
    ):
        """Test _handle_recovered_position logs position details (lines 213-219)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=1_000_000_000_000,
        )

        mock_cache = MagicMock()
        mock_cache.orders_open.return_value = []

        with patch.object(type(strategy), 'cache', new_callable=PropertyMock) as mock_cache_prop:
            mock_cache_prop.return_value = mock_cache
            with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
                mock_logger = MagicMock()
                mock_log_prop.return_value = mock_logger

                strategy._handle_recovered_position(mock_open_position)

                # Should log recovery details
                mock_logger.info.assert_called()

    def test_setup_exit_orders_with_existing_stop(
        self, strategy_config, mock_open_position
    ):
        """Test _setup_exit_orders logs when stop already exists (lines 259-263)."""
        from nautilus_trader.model.enums import OrderType

        strategy = RecoverableStrategy(config=strategy_config)

        mock_stop_order = MagicMock()
        mock_stop_order.order_type = OrderType.STOP_MARKET

        mock_cache = MagicMock()
        mock_cache.orders_open.return_value = [mock_stop_order]

        with patch.object(type(strategy), 'cache', new_callable=PropertyMock) as mock_cache_prop:
            mock_cache_prop.return_value = mock_cache
            with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
                mock_logger = MagicMock()
                mock_log_prop.return_value = mock_logger

                strategy._setup_exit_orders(mock_open_position)

                # Should log that stop-loss already exists
                mock_logger.info.assert_called()
                info_calls = [str(c) for c in mock_logger.info.call_args_list]
                assert any("Stop-loss already exists" in c for c in info_calls)

    def test_setup_exit_orders_without_stop(
        self, strategy_config, mock_open_position
    ):
        """Test _setup_exit_orders warns when no stop exists (lines 265-269)."""
        from nautilus_trader.model.enums import OrderType

        strategy = RecoverableStrategy(config=strategy_config)

        # Limit order is NOT a stop
        mock_limit_order = MagicMock()
        mock_limit_order.order_type = OrderType.LIMIT

        mock_cache = MagicMock()
        mock_cache.orders_open.return_value = [mock_limit_order]

        with patch.object(type(strategy), 'cache', new_callable=PropertyMock) as mock_cache_prop:
            mock_cache_prop.return_value = mock_cache
            with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
                mock_logger = MagicMock()
                mock_log_prop.return_value = mock_logger

                strategy._setup_exit_orders(mock_open_position)

                # Should warn about missing stop-loss
                mock_logger.warning.assert_called()
                warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
                assert any("No stop-loss found" in c for c in warning_calls)

    def test_setup_exit_orders_no_orders(self, strategy_config, mock_open_position):
        """Test _setup_exit_orders warns when no orders exist."""
        strategy = RecoverableStrategy(config=strategy_config)

        mock_cache = MagicMock()
        mock_cache.orders_open.return_value = []  # No orders at all

        with patch.object(type(strategy), 'cache', new_callable=PropertyMock) as mock_cache_prop:
            mock_cache_prop.return_value = mock_cache
            with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
                mock_logger = MagicMock()
                mock_log_prop.return_value = mock_logger

                strategy._setup_exit_orders(mock_open_position)

                # Should warn about missing stop-loss
                mock_logger.warning.assert_called()

    def test_detect_recovered_positions_open_only(
        self, strategy_config, mock_open_position
    ):
        """Test _detect_recovered_positions only handles open positions (lines 183-189)."""
        strategy = RecoverableStrategy(config=strategy_config)

        # Create a closed position
        closed_pos = MagicMock()
        closed_pos.is_open = False

        mock_cache = MagicMock()
        mock_cache.positions.return_value = [mock_open_position, closed_pos]
        mock_cache.orders_open.return_value = []

        with patch.object(type(strategy), 'cache', new_callable=PropertyMock) as mock_cache_prop:
            mock_cache_prop.return_value = mock_cache
            with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
                mock_logger = MagicMock()
                mock_log_prop.return_value = mock_logger

                strategy._detect_recovered_positions()

        # Should only recover the open position
        assert len(strategy._recovered_positions) == 1

    def test_detect_recovered_positions_logs_count(
        self, strategy_config, mock_open_position
    ):
        """Test _detect_recovered_positions logs position count (lines 189)."""
        strategy = RecoverableStrategy(config=strategy_config)

        mock_cache = MagicMock()
        mock_cache.positions.return_value = [mock_open_position]
        mock_cache.orders_open.return_value = []

        with patch.object(type(strategy), 'cache', new_callable=PropertyMock) as mock_cache_prop:
            mock_cache_prop.return_value = mock_cache
            with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
                mock_logger = MagicMock()
                mock_log_prop.return_value = mock_logger

                strategy._detect_recovered_positions()

                # Should log position count
                info_calls = [str(c) for c in mock_logger.info.call_args_list]
                assert any("Position detection complete" in c for c in info_calls)


class TestRecoverableStrategyWarmupMethods:
    """Test warmup-related methods with proper mocking.

    Covers lines: 292-303, 318-338, 361-386
    """

    @pytest.fixture
    def strategy_config(self):
        return RecoverableStrategyConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            recovery=RecoveryConfig(
                trader_id="TRADER-TEST-001",
                warmup_lookback_days=2,
            ),
        )

    def test_on_warmup_data_received_idempotency_guard(self, strategy_config):
        """Test _on_warmup_data_received is idempotent (lines 318-320)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy._warmup_complete = True  # Already complete!

        mock_bar = MagicMock()
        mock_bar.ts_event = 1_000_000_000_000

        with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
            mock_logger = MagicMock()
            mock_log_prop.return_value = mock_logger

            strategy._on_warmup_data_received([mock_bar])

            # Should warn about duplicate warmup
            mock_logger.warning.assert_called()
            warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
            assert any("after completion" in c for c in warning_calls)

    def test_on_warmup_data_received_empty_bars(self, strategy_config):
        """Test _on_warmup_data_received handles empty bars (lines 322-325)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy._warmup_complete = False
        strategy._warmup_start_ns = 1_000_000_000_000
        strategy.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=1_000_000_000_000,
        )

        with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
            mock_logger = MagicMock()
            mock_log_prop.return_value = mock_logger
            with patch.object(type(strategy), 'clock', new_callable=PropertyMock) as mock_clock_prop:
                mock_clock = MagicMock()
                mock_clock.timestamp_ns.return_value = 2_000_000_000_000
                mock_clock_prop.return_value = mock_clock

                strategy._on_warmup_data_received([])

                # Should warn and still complete
                mock_logger.warning.assert_called()
                warning_calls = [str(c) for c in mock_logger.warning.call_args_list]
                assert any("No warmup bars" in c for c in warning_calls)
                assert strategy._warmup_complete is True

    def test_on_warmup_data_received_processes_bars_sorted(self, strategy_config):
        """Test _on_warmup_data_received processes bars in timestamp order (lines 327-335)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy._warmup_complete = False
        strategy._warmup_start_ns = 1_000_000_000_000
        strategy.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=1_000_000_000_000,
        )

        # Create bars with different timestamps (unsorted)
        bar1 = MagicMock()
        bar1.ts_event = 3_000_000_000_000
        bar2 = MagicMock()
        bar2.ts_event = 1_000_000_000_000  # Oldest
        bar3 = MagicMock()
        bar3.ts_event = 2_000_000_000_000

        processed_timestamps = []
        original_on_historical = strategy.on_historical_data

        def track_bars(bar):
            processed_timestamps.append(bar.ts_event)
            return original_on_historical(bar)

        strategy.on_historical_data = track_bars

        with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
            mock_logger = MagicMock()
            mock_log_prop.return_value = mock_logger
            with patch.object(type(strategy), 'clock', new_callable=PropertyMock) as mock_clock_prop:
                mock_clock = MagicMock()
                mock_clock.timestamp_ns.return_value = 4_000_000_000_000
                mock_clock_prop.return_value = mock_clock

                strategy._on_warmup_data_received([bar1, bar2, bar3])

        # Should process oldest first (sorted)
        assert processed_timestamps == [1_000_000_000_000, 2_000_000_000_000, 3_000_000_000_000]
        assert strategy._warmup_bars_processed == 3

    def test_on_warmup_data_received_logs_count(self, strategy_config):
        """Test _on_warmup_data_received logs bar count (line 327)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy._warmup_complete = False
        strategy._warmup_start_ns = 1_000_000_000_000
        strategy.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=1_000_000_000_000,
        )

        mock_bar = MagicMock()
        mock_bar.ts_event = 1_000_000_000_000

        with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
            mock_logger = MagicMock()
            mock_log_prop.return_value = mock_logger
            with patch.object(type(strategy), 'clock', new_callable=PropertyMock) as mock_clock_prop:
                mock_clock = MagicMock()
                mock_clock.timestamp_ns.return_value = 2_000_000_000_000
                mock_clock_prop.return_value = mock_clock

                strategy._on_warmup_data_received([mock_bar])

                # Should log bar count
                info_calls = [str(c) for c in mock_logger.info.call_args_list]
                assert any("Received" in c and "warmup bars" in c for c in info_calls)

    def test_complete_warmup_sets_flag_and_state(self, strategy_config):
        """Test _complete_warmup sets all necessary state (lines 361-377)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy._warmup_complete = False
        strategy._warmup_start_ns = 1_000_000_000_000
        strategy._warmup_bars_processed = 50
        strategy.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            positions_recovered=3,
            ts_started=1_000_000_000_000,
        )

        with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
            mock_logger = MagicMock()
            mock_log_prop.return_value = mock_logger
            with patch.object(type(strategy), 'clock', new_callable=PropertyMock) as mock_clock_prop:
                mock_clock = MagicMock()
                mock_clock.timestamp_ns.return_value = 2_000_000_000_000
                mock_clock_prop.return_value = mock_clock

                strategy._complete_warmup()

        assert strategy._warmup_complete is True
        assert strategy.recovery_state.status == RecoveryStatus.COMPLETED
        assert strategy.recovery_state.indicators_warmed is True
        assert strategy.recovery_state.orders_reconciled is True
        assert strategy.recovery_state.positions_recovered == 3  # Preserved
        assert strategy.recovery_state.ts_completed == 2_000_000_000_000

    def test_complete_warmup_logs_duration(self, strategy_config):
        """Test _complete_warmup logs warmup duration (lines 379-383)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy._warmup_complete = False
        strategy._warmup_start_ns = 1_000_000_000_000
        strategy._warmup_bars_processed = 100
        strategy.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=1_000_000_000_000,
        )

        with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
            mock_logger = MagicMock()
            mock_log_prop.return_value = mock_logger
            with patch.object(type(strategy), 'clock', new_callable=PropertyMock) as mock_clock_prop:
                mock_clock = MagicMock()
                mock_clock.timestamp_ns.return_value = 2_000_000_000_000
                mock_clock_prop.return_value = mock_clock

                strategy._complete_warmup()

                # Should log warmup complete with duration
                info_calls = [str(c) for c in mock_logger.info.call_args_list]
                assert any("Warmup complete" in c for c in info_calls)
                assert any("duration_ms" in c for c in info_calls)
                assert any("bars_processed" in c for c in info_calls)

    def test_complete_warmup_calls_hook(self, strategy_config):
        """Test _complete_warmup calls on_warmup_complete hook (line 386)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy._warmup_complete = False
        strategy._warmup_start_ns = 1_000_000_000_000
        strategy._warmup_bars_processed = 50
        strategy.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=1_000_000_000_000,
        )

        hook_called = [False]
        original_hook = strategy.on_warmup_complete

        def hook_wrapper():
            hook_called[0] = True
            return original_hook()

        strategy.on_warmup_complete = hook_wrapper

        with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
            mock_logger = MagicMock()
            mock_log_prop.return_value = mock_logger
            with patch.object(type(strategy), 'clock', new_callable=PropertyMock) as mock_clock_prop:
                mock_clock = MagicMock()
                mock_clock.timestamp_ns.return_value = 2_000_000_000_000
                mock_clock_prop.return_value = mock_clock

                strategy._complete_warmup()

        assert hook_called[0] is True

    def test_complete_warmup_handles_none_warmup_start(self, strategy_config):
        """Test _complete_warmup handles None _warmup_start_ns (lines 365-366)."""
        strategy = RecoverableStrategy(config=strategy_config)
        strategy._warmup_complete = False
        strategy._warmup_start_ns = None  # Not set
        strategy._warmup_bars_processed = 50
        strategy.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=1_000_000_000_000,
        )

        with patch.object(type(strategy), 'log', new_callable=PropertyMock) as mock_log_prop:
            mock_logger = MagicMock()
            mock_log_prop.return_value = mock_logger
            with patch.object(type(strategy), 'clock', new_callable=PropertyMock) as mock_clock_prop:
                mock_clock = MagicMock()
                mock_clock.timestamp_ns.return_value = 2_000_000_000_000
                mock_clock_prop.return_value = mock_clock

                # Should not raise
                strategy._complete_warmup()

        assert strategy._warmup_complete is True


class TestPositionRecoveryProviderBalanceMethods:
    """Additional tests for PositionRecoveryProvider balance methods.

    Covers lines: 215-219, 346-373, 548-573, 612-628
    """

    @pytest.fixture
    def mock_cache(self):
        return MagicMock()

    def test_reconcile_positions_duplicate_exchange_ids_warning(self, mock_cache):
        """Test reconcile_positions warns on duplicate exchange instrument_ids (lines 214-219)."""
        provider = PositionRecoveryProvider(cache=mock_cache)

        # Create duplicate exchange positions
        pos1 = MagicMock()
        pos1.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        pos1.side.value = "LONG"
        pos1.quantity.as_decimal.return_value = Decimal("1.0")

        pos2 = MagicMock()
        pos2.instrument_id.value = "BTCUSDT-PERP.BINANCE"  # Duplicate!
        pos2.side.value = "SHORT"
        pos2.quantity.as_decimal.return_value = Decimal("2.0")

        # Should not crash, but should log warning
        reconciled, discrepancies = provider.reconcile_positions(
            cached=[],
            exchange=[pos1, pos2],
        )

        # Should still return reconciled positions (last one wins in dict)
        assert len(reconciled) >= 1

    def test_get_exchange_balances_no_account(self, mock_cache):
        """Test get_exchange_balances with no account returns empty (lines 351-353)."""
        mock_cache.account.return_value = None
        provider = PositionRecoveryProvider(cache=mock_cache)

        balances = provider.get_exchange_balances(trader_id="TRADER-001")
        assert len(balances) == 0

    def test_get_exchange_balances_with_account(self, mock_cache):
        """Test get_exchange_balances returns balances (lines 346-373)."""
        balance = MagicMock()
        balance.currency.code = "USDT"
        balance.total.as_decimal.return_value = Decimal("10000.00")
        balance.locked.as_decimal.return_value = Decimal("1000.00")
        balance.free.as_decimal.return_value = Decimal("9000.00")

        account = MagicMock()
        account.balances.return_value = [balance]
        mock_cache.account.return_value = account

        provider = PositionRecoveryProvider(cache=mock_cache)
        balances = provider.get_exchange_balances(trader_id="TRADER-001")

        assert len(balances) == 1

    def test_get_exchange_balances_logs_info(self, mock_cache):
        """Test get_exchange_balances logs retrieval (lines 357-361)."""
        balance = MagicMock()
        balance.currency.code = "USDT"
        balance.total.as_decimal.return_value = Decimal("10000.00")
        balance.locked.as_decimal.return_value = Decimal("1000.00")
        balance.free.as_decimal.return_value = Decimal("9000.00")

        account = MagicMock()
        account.balances.return_value = [balance]
        mock_cache.account.return_value = account

        mock_logger = MagicMock()
        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)

        provider.get_exchange_balances(trader_id="TRADER-001")

        # Should log retrieval
        mock_logger.info.assert_called()

    def test_get_balance_changes_only_returns_changed(self, mock_cache):
        """Test get_balance_changes only returns changed currencies (lines 548-573)."""
        provider = PositionRecoveryProvider(cache=mock_cache)

        # Same values - no change
        cached = MagicMock()
        cached.currency.code = "USDT"
        cached.total.as_decimal.return_value = Decimal("10000")
        cached.locked.as_decimal.return_value = Decimal("1000")

        exchange = MagicMock()
        exchange.currency.code = "USDT"
        exchange.total.as_decimal.return_value = Decimal("10000")
        exchange.locked.as_decimal.return_value = Decimal("1000")

        changes = provider.get_balance_changes(
            cached=[cached],
            exchange=[exchange],
        )
        assert len(changes) == 0

    def test_get_balance_changes_includes_total_changes(self, mock_cache):
        """Test get_balance_changes includes total balance changes (line 565-566)."""
        provider = PositionRecoveryProvider(cache=mock_cache)

        cached = MagicMock()
        cached.currency.code = "USDT"
        cached.total.as_decimal.return_value = Decimal("10000")
        cached.locked.as_decimal.return_value = Decimal("1000")

        exchange = MagicMock()
        exchange.currency.code = "USDT"
        exchange.total.as_decimal.return_value = Decimal("12000")  # Changed!
        exchange.locked.as_decimal.return_value = Decimal("1000")

        changes = provider.get_balance_changes(
            cached=[cached],
            exchange=[exchange],
        )
        assert len(changes) == 1
        assert changes[0]["total_change"] == Decimal("2000")

    def test_get_balance_changes_includes_locked_changes(self, mock_cache):
        """Test get_balance_changes includes locked balance changes (line 567)."""
        provider = PositionRecoveryProvider(cache=mock_cache)

        cached = MagicMock()
        cached.currency.code = "USDT"
        cached.total.as_decimal.return_value = Decimal("10000")
        cached.locked.as_decimal.return_value = Decimal("1000")

        exchange = MagicMock()
        exchange.currency.code = "USDT"
        exchange.total.as_decimal.return_value = Decimal("10000")  # Same
        exchange.locked.as_decimal.return_value = Decimal("2000")  # Changed!

        changes = provider.get_balance_changes(
            cached=[cached],
            exchange=[exchange],
        )
        assert len(changes) == 1
        assert changes[0]["locked_change"] == Decimal("1000")

    def test_get_balance_changes_includes_new_currencies(self, mock_cache):
        """Test get_balance_changes includes new currencies (lines 568-569)."""
        provider = PositionRecoveryProvider(cache=mock_cache)

        exchange = MagicMock()
        exchange.currency.code = "BTC"
        exchange.total.as_decimal.return_value = Decimal("1.5")
        exchange.locked.as_decimal.return_value = Decimal("0")

        changes = provider.get_balance_changes(
            cached=[],
            exchange=[exchange],
        )
        assert len(changes) == 1
        assert changes[0]["is_new"] is True

    def test_get_balance_changes_includes_removed_currencies(self, mock_cache):
        """Test get_balance_changes includes removed currencies (line 570)."""
        provider = PositionRecoveryProvider(cache=mock_cache)

        cached = MagicMock()
        cached.currency.code = "ETH"
        cached.total.as_decimal.return_value = Decimal("10")
        cached.locked.as_decimal.return_value = Decimal("0")

        changes = provider.get_balance_changes(
            cached=[cached],
            exchange=[],
        )
        assert len(changes) == 1
        assert changes[0]["is_removed"] is True

    def test_log_balance_changes_significant_as_warning(self, mock_cache):
        """Test log_balance_changes logs significant changes as warnings (lines 612-626)."""
        mock_logger = MagicMock()
        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)

        delta = {
            "currency": "USDT",
            "cached_total": Decimal("10000"),
            "exchange_total": Decimal("15000"),
            "total_change": Decimal("5000"),
            "percent_change": 50.0,
            "is_new": False,
            "is_removed": False,
        }

        provider.log_balance_changes([delta], threshold_percent=10.0)
        mock_logger.warning.assert_called()

    def test_log_balance_changes_non_significant_as_info(self, mock_cache):
        """Test log_balance_changes logs non-significant changes as info (line 628)."""
        mock_logger = MagicMock()
        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)

        delta = {
            "currency": "USDT",
            "cached_total": Decimal("10000"),
            "exchange_total": Decimal("10500"),
            "total_change": Decimal("500"),
            "percent_change": 5.0,
            "is_new": False,
            "is_removed": False,
        }

        provider.log_balance_changes([delta], threshold_percent=10.0)
        mock_logger.info.assert_called()

    def test_log_balance_changes_new_currency_as_warning(self, mock_cache):
        """Test log_balance_changes logs new currencies as warnings."""
        mock_logger = MagicMock()
        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)

        delta = {
            "currency": "BTC",
            "cached_total": Decimal("0"),
            "exchange_total": Decimal("1.0"),
            "total_change": Decimal("1.0"),
            "percent_change": 100.0,
            "is_new": True,
            "is_removed": False,
        }

        provider.log_balance_changes([delta], threshold_percent=10.0)
        mock_logger.warning.assert_called()

    def test_log_balance_changes_removed_currency_as_warning(self, mock_cache):
        """Test log_balance_changes logs removed currencies as warnings."""
        mock_logger = MagicMock()
        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)

        delta = {
            "currency": "ETH",
            "cached_total": Decimal("10.0"),
            "exchange_total": Decimal("0"),
            "total_change": Decimal("-10.0"),
            "percent_change": -100.0,
            "is_new": False,
            "is_removed": True,
        }

        provider.log_balance_changes([delta], threshold_percent=10.0)
        mock_logger.warning.assert_called()

    def test_log_balance_changes_empty_list(self, mock_cache):
        """Test log_balance_changes handles empty deltas list."""
        mock_logger = MagicMock()
        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)

        provider.log_balance_changes([], threshold_percent=10.0)
        mock_logger.warning.assert_not_called()
        mock_logger.info.assert_not_called()

    def test_log_balance_changes_multiple_deltas(self, mock_cache):
        """Test log_balance_changes handles multiple deltas correctly."""
        mock_logger = MagicMock()
        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)

        deltas = [
            {
                "currency": "USDT",
                "cached_total": Decimal("10000"),
                "exchange_total": Decimal("15000"),
                "total_change": Decimal("5000"),
                "percent_change": 50.0,  # Significant
                "is_new": False,
                "is_removed": False,
            },
            {
                "currency": "BTC",
                "cached_total": Decimal("1.0"),
                "exchange_total": Decimal("1.01"),
                "total_change": Decimal("0.01"),
                "percent_change": 1.0,  # Not significant
                "is_new": False,
                "is_removed": False,
            },
        ]

        provider.log_balance_changes(deltas, threshold_percent=10.0)

        # First should be warning, second should be info
        assert mock_logger.warning.call_count == 1
        assert mock_logger.info.call_count == 1
