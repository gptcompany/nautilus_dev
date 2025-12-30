"""Integration test for position size accuracy after recovery (NFR-002 - T045).

Tests that recovered position sizes match the original positions exactly.
This validates the NFR-002 consistency requirement from Spec 017.

NFR-002: Consistency
- No duplicate orders after recovery
- Position sizes match exchange exactly
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from strategies.common.recovery.config import RecoveryConfig
from strategies.common.recovery.models import PositionSnapshot
from strategies.common.recovery.recoverable_strategy import (
    RecoverableStrategy,
    RecoverableStrategyConfig,
)


class PositionAccuracyStrategy(RecoverableStrategy):
    """Strategy subclass that tracks position data accuracy.

    Used to verify that recovered positions maintain exact values.
    """

    def __init__(self, config: RecoverableStrategyConfig) -> None:
        super().__init__(config)
        self.recovered_position_data: list[dict] = []

    def on_position_recovered(self, position) -> None:
        """Capture detailed position data for accuracy verification."""
        self.recovered_position_data.append({
            "instrument_id": str(position.instrument_id.value),
            "side": str(position.side.value),
            "quantity": position.quantity,
            "avg_px_open": position.avg_px_open,
            "is_open": position.is_open,
        })

    def on_historical_data(self, bar) -> None:
        """Skip historical data processing."""
        pass

    def on_warmup_complete(self) -> None:
        """Skip warmup complete."""
        pass


def create_mock_position(
    instrument_id: str,
    side: str,
    quantity: Decimal,
    avg_px_open: Decimal,
) -> MagicMock:
    """Factory to create mock positions with precise values."""
    position = MagicMock()
    position.instrument_id = MagicMock()
    position.instrument_id.value = instrument_id
    position.side = MagicMock()
    position.side.value = side
    position.quantity = quantity
    position.avg_px_open = avg_px_open
    position.is_open = True
    return position


@pytest.fixture
def mock_cache():
    """Create a mock cache."""
    cache = MagicMock()
    cache.positions.return_value = []
    cache.orders_open.return_value = []
    return cache


@pytest.fixture
def mock_clock():
    """Create a mock clock."""
    clock = MagicMock()
    clock.timestamp_ns.return_value = 1704153600000000000
    clock.utc_now.return_value = MagicMock()
    clock.utc_now.return_value.__sub__ = MagicMock(return_value=MagicMock())
    return clock


@pytest.fixture
def mock_instrument():
    """Create a mock instrument."""
    instrument = MagicMock()
    instrument.id = MagicMock()
    instrument.id.value = "BTCUSDT-PERP.BINANCE"
    return instrument


@pytest.fixture
def strategy_config():
    """Create a RecoverableStrategyConfig for testing."""
    return RecoverableStrategyConfig(
        instrument_id="BTCUSDT-PERP.BINANCE",
        bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
        recovery=RecoveryConfig(
            trader_id="TESTER-001",
            recovery_enabled=True,
            warmup_lookback_days=0,
            startup_delay_secs=0.0,
            max_recovery_time_secs=30.0,
        ),
    )


@pytest.mark.integration
@pytest.mark.recovery
class TestPositionSizeAccuracy:
    """Integration tests for NFR-002: Position size accuracy."""

    def test_position_quantity_exact_match(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that recovered position quantity matches exactly."""
        # Setup with precise quantity
        original_quantity = Decimal("1.23456789")
        mock_position = create_mock_position(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="LONG",
            quantity=original_quantity,
            avg_px_open=Decimal("42500.00"),
        )

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        strategy = PositionAccuracyStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # NFR-002 Verification: Exact quantity match
        assert len(strategy.recovered_position_data) == 1
        recovered = strategy.recovered_position_data[0]
        assert recovered["quantity"] == original_quantity, (
            f"Quantity mismatch: expected {original_quantity}, "
            f"got {recovered['quantity']}"
        )

    def test_position_avg_price_exact_match(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that recovered position avg entry price matches exactly."""
        # Setup with precise avg price
        original_avg_price = Decimal("42567.89123456")
        mock_position = create_mock_position(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="LONG",
            quantity=Decimal("1.5"),
            avg_px_open=original_avg_price,
        )

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        strategy = PositionAccuracyStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # NFR-002 Verification: Exact avg price match
        recovered = strategy.recovered_position_data[0]
        assert recovered["avg_px_open"] == original_avg_price

    def test_position_side_accuracy_long(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that LONG position side is recovered accurately."""
        mock_position = create_mock_position(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="LONG",
            quantity=Decimal("1.0"),
            avg_px_open=Decimal("42000.00"),
        )

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        strategy = PositionAccuracyStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # NFR-002 Verification: Side accuracy
        recovered = strategy.recovered_position_data[0]
        assert recovered["side"] == "LONG"

    def test_position_side_accuracy_short(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that SHORT position side is recovered accurately."""
        mock_position = create_mock_position(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="SHORT",
            quantity=Decimal("2.5"),
            avg_px_open=Decimal("43000.00"),
        )

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        strategy = PositionAccuracyStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # NFR-002 Verification: Side accuracy
        recovered = strategy.recovered_position_data[0]
        assert recovered["side"] == "SHORT"

    def test_multiple_positions_all_accurate(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test accuracy for multiple positions recovered."""
        # Setup multiple positions with varying values
        position_data = [
            ("LONG", Decimal("0.001"), Decimal("40000.00")),
            ("SHORT", Decimal("10.12345"), Decimal("45000.50")),
            ("LONG", Decimal("0.00001"), Decimal("42123.456789")),
        ]

        positions = [
            create_mock_position(
                "BTCUSDT-PERP.BINANCE", side, qty, avg_px
            )
            for side, qty, avg_px in position_data
        ]

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = positions

        strategy = PositionAccuracyStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # NFR-002 Verification: All positions accurate
        assert len(strategy.recovered_position_data) == 3

        for i, (expected_side, expected_qty, expected_avg_px) in enumerate(position_data):
            recovered = strategy.recovered_position_data[i]
            assert recovered["side"] == expected_side
            assert recovered["quantity"] == expected_qty
            assert recovered["avg_px_open"] == expected_avg_px

    def test_small_quantity_precision(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test precision for very small position quantities."""
        # Very small quantity (8 decimal places)
        small_quantity = Decimal("0.00000001")
        mock_position = create_mock_position(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="LONG",
            quantity=small_quantity,
            avg_px_open=Decimal("100000.00"),  # High price to make position meaningful
        )

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        strategy = PositionAccuracyStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # NFR-002 Verification: Small quantity precision
        recovered = strategy.recovered_position_data[0]
        assert recovered["quantity"] == small_quantity

    def test_large_quantity_precision(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test precision for large position quantities."""
        # Large quantity
        large_quantity = Decimal("1000000.12345678")
        mock_position = create_mock_position(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="LONG",
            quantity=large_quantity,
            avg_px_open=Decimal("0.001"),  # Low price for large qty
        )

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        strategy = PositionAccuracyStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # NFR-002 Verification: Large quantity precision
        recovered = strategy.recovered_position_data[0]
        assert recovered["quantity"] == large_quantity

    def test_instrument_id_accuracy(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that instrument ID is recovered accurately."""
        expected_instrument_id = "BTCUSDT-PERP.BINANCE"
        mock_position = create_mock_position(
            instrument_id=expected_instrument_id,
            side="LONG",
            quantity=Decimal("1.0"),
            avg_px_open=Decimal("42000.00"),
        )

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        strategy = PositionAccuracyStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # NFR-002 Verification: Instrument ID accuracy
        recovered = strategy.recovered_position_data[0]
        assert recovered["instrument_id"] == expected_instrument_id


@pytest.mark.integration
@pytest.mark.recovery
class TestPositionSnapshotAccuracy:
    """Tests for PositionSnapshot model accuracy."""

    def test_position_snapshot_preserves_decimal_precision(self):
        """Test that PositionSnapshot preserves decimal precision."""
        snapshot = PositionSnapshot(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="LONG",
            quantity=Decimal("1.23456789012345678"),
            avg_entry_price=Decimal("42567.89123456789"),
            unrealized_pnl=Decimal("123.456789"),
            realized_pnl=Decimal("-50.123456789"),
            ts_opened=1704067200000000000,
            ts_last_updated=1704153600000000000,
        )

        # NFR-002 Verification: Decimal precision preserved
        assert snapshot.quantity == Decimal("1.23456789012345678")
        assert snapshot.avg_entry_price == Decimal("42567.89123456789")
        assert snapshot.unrealized_pnl == Decimal("123.456789")
        assert snapshot.realized_pnl == Decimal("-50.123456789")

    def test_position_snapshot_side_validation(self):
        """Test that PositionSnapshot validates side correctly."""
        # Valid LONG
        long_snapshot = PositionSnapshot(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="LONG",
            quantity=Decimal("1.0"),
            avg_entry_price=Decimal("42000.00"),
            ts_opened=1704067200000000000,
            ts_last_updated=1704153600000000000,
        )
        assert long_snapshot.side == "LONG"

        # Valid SHORT
        short_snapshot = PositionSnapshot(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="SHORT",
            quantity=Decimal("1.0"),
            avg_entry_price=Decimal("42000.00"),
            ts_opened=1704067200000000000,
            ts_last_updated=1704153600000000000,
        )
        assert short_snapshot.side == "SHORT"

        # Valid FLAT
        flat_snapshot = PositionSnapshot(
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="FLAT",
            quantity=Decimal("0"),
            avg_entry_price=Decimal("42000.00"),
            ts_opened=1704067200000000000,
            ts_last_updated=1704153600000000000,
        )
        assert flat_snapshot.side == "FLAT"

    def test_position_snapshot_invalid_side_rejected(self):
        """Test that invalid side values are rejected."""
        with pytest.raises(ValueError, match="Invalid position side"):
            PositionSnapshot(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="INVALID",
                quantity=Decimal("1.0"),
                avg_entry_price=Decimal("42000.00"),
                ts_opened=1704067200000000000,
                ts_last_updated=1704153600000000000,
            )

    def test_position_snapshot_timestamp_ordering(self):
        """Test that ts_last_updated cannot be before ts_opened."""
        with pytest.raises(ValueError, match="ts_last_updated cannot be before ts_opened"):
            PositionSnapshot(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="LONG",
                quantity=Decimal("1.0"),
                avg_entry_price=Decimal("42000.00"),
                ts_opened=1704153600000000000,  # Later
                ts_last_updated=1704067200000000000,  # Earlier - invalid
            )
