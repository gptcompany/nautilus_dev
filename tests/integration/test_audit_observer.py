"""Integration tests for AuditObserver (Spec 030).

Tests the AuditObserver's ability to handle NautilusTrader order and position events
and emit them to the audit trail.
"""

import tempfile
from unittest.mock import MagicMock, patch

from strategies.common.audit import AuditConfig, AuditEventEmitter
from strategies.common.audit.observer import AuditObserver, AuditObserverConfig


class TestAuditObserverConfig:
    """Tests for AuditObserverConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AuditObserverConfig()

        assert config.trader_id == "TRADER-001"
        assert config.audit_base_path == "./data/audit/hot"
        assert config.sync_writes is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AuditObserverConfig(
            trader_id="CUSTOM-TRADER",
            audit_base_path="/custom/path",
            sync_writes=False,
        )

        assert config.trader_id == "CUSTOM-TRADER"
        assert config.audit_base_path == "/custom/path"
        assert config.sync_writes is False


class TestAuditObserverOrderEvents:
    """Tests for AuditObserver order event handling."""

    def test_on_order_filled(self):
        """Test handling of OrderFilled event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditObserverConfig(
                component_id="AuditObserver-001",
                trader_id="TRADER-001",
                audit_base_path=tmpdir,
            )

            audit_config = AuditConfig(base_path=tmpdir)
            emitter = AuditEventEmitter(trader_id="TRADER-001", config=audit_config)

            observer = AuditObserver(config, emitter=emitter)

            # Create mock OrderFilled event
            mock_event = MagicMock()
            mock_event.client_order_id = "O-001"
            mock_event.instrument_id = "BTCUSDT.BINANCE"
            mock_event.order_side.name = "BUY"
            mock_event.last_qty = 0.5
            mock_event.last_px = 42000.0
            mock_event.strategy_id = "momentum_v1"

            # Patch isinstance check
            with patch(
                "strategies.common.audit.observer.isinstance",
                side_effect=lambda obj, cls: cls.__name__ == "OrderFilled"
                if hasattr(cls, "__name__") and cls.__name__ == "OrderFilled"
                else isinstance(obj, cls),
            ):
                observer._emitter = emitter
                observer._on_order_filled(mock_event)

            # Verify event was emitted
            assert emitter.sequence == 1

            emitter.close()

    def test_on_order_rejected(self):
        """Test handling of OrderRejected event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditObserverConfig(
                component_id="AuditObserver-001",
                trader_id="TRADER-001",
                audit_base_path=tmpdir,
            )

            audit_config = AuditConfig(base_path=tmpdir)
            emitter = AuditEventEmitter(trader_id="TRADER-001", config=audit_config)

            observer = AuditObserver(config, emitter=emitter)
            observer._emitter = emitter

            # Create mock OrderRejected event
            mock_event = MagicMock()
            mock_event.client_order_id = "O-002"
            mock_event.instrument_id = "BTCUSDT.BINANCE"
            mock_event.strategy_id = "momentum_v1"

            observer._on_order_rejected(mock_event)

            # Verify event was emitted
            assert emitter.sequence == 1

            emitter.close()

    def test_slippage_calculation(self):
        """Test slippage calculation for filled orders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditObserverConfig(
                component_id="AuditObserver-001",
                trader_id="TRADER-001",
                audit_base_path=tmpdir,
            )

            audit_config = AuditConfig(base_path=tmpdir)
            emitter = AuditEventEmitter(trader_id="TRADER-001", config=audit_config)

            observer = AuditObserver(config, emitter=emitter)
            observer._emitter = emitter

            # Set expected price before fill
            observer.set_expected_price("O-003", 42000.0)

            # Create mock OrderFilled event with different price (slippage)
            mock_event = MagicMock()
            mock_event.client_order_id = "O-003"
            mock_event.instrument_id = "BTCUSDT.BINANCE"
            mock_event.order_side.name = "BUY"
            mock_event.last_qty = 0.5
            mock_event.last_px = 42042.0  # 10 bps slippage
            mock_event.strategy_id = "momentum_v1"

            observer._on_order_filled(mock_event)

            # Expected price should be removed after fill
            assert "O-003" not in observer._expected_prices

            emitter.close()


class TestAuditObserverPositionEvents:
    """Tests for AuditObserver position event handling."""

    def test_on_position_opened(self):
        """Test handling of PositionOpened event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditObserverConfig(
                component_id="AuditObserver-001",
                trader_id="TRADER-001",
                audit_base_path=tmpdir,
            )

            audit_config = AuditConfig(base_path=tmpdir)
            emitter = AuditEventEmitter(trader_id="TRADER-001", config=audit_config)

            observer = AuditObserver(config, emitter=emitter)
            observer._emitter = emitter

            # Create mock PositionOpened event
            mock_event = MagicMock()
            mock_event.opening_order_id = "O-004"
            mock_event.instrument_id = "BTCUSDT.BINANCE"
            mock_event.entry.name = "BUY"
            mock_event.signed_qty = 0.5
            mock_event.avg_px_open = 42000.0
            mock_event.strategy_id = "momentum_v1"

            observer._on_position_opened(mock_event)

            assert emitter.sequence == 1

            emitter.close()

    def test_on_position_closed(self):
        """Test handling of PositionClosed event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditObserverConfig(
                component_id="AuditObserver-001",
                trader_id="TRADER-001",
                audit_base_path=tmpdir,
            )

            audit_config = AuditConfig(base_path=tmpdir)
            emitter = AuditEventEmitter(trader_id="TRADER-001", config=audit_config)

            observer = AuditObserver(config, emitter=emitter)
            observer._emitter = emitter

            # Create mock PositionClosed event
            mock_event = MagicMock()
            mock_event.closing_order_id = "O-005"
            mock_event.instrument_id = "BTCUSDT.BINANCE"
            mock_event.entry.name = "BUY"
            mock_event.signed_qty = 0.5
            mock_event.avg_px_close = 43000.0
            mock_event.realized_pnl = 500.0
            mock_event.strategy_id = "momentum_v1"

            observer._on_position_closed(mock_event)

            assert emitter.sequence == 1

            emitter.close()


class TestAuditObserverLifecycle:
    """Tests for AuditObserver lifecycle management."""

    def test_emitter_property(self):
        """Test access to underlying emitter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditObserverConfig(
                component_id="AuditObserver-001",
                trader_id="TRADER-001",
                audit_base_path=tmpdir,
            )

            audit_config = AuditConfig(base_path=tmpdir)
            emitter = AuditEventEmitter(trader_id="TRADER-001", config=audit_config)

            observer = AuditObserver(config, emitter=emitter)

            assert observer.emitter is emitter

            emitter.close()

    def test_expected_price_tracking(self):
        """Test expected price tracking for slippage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditObserverConfig(
                component_id="AuditObserver-001",
                audit_base_path=tmpdir,
            )

            observer = AuditObserver(config)

            # Set multiple expected prices
            observer.set_expected_price("O-001", 42000.0)
            observer.set_expected_price("O-002", 43000.0)

            assert observer._expected_prices["O-001"] == 42000.0
            assert observer._expected_prices["O-002"] == 43000.0
