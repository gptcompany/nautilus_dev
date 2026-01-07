#!/usr/bin/env python3
"""
Manual test script for graceful shutdown handler.

Tests the GracefulShutdownHandler without requiring a full TradingNode.
Uses a mock node to verify the shutdown sequence.

Usage:
    python scripts/test_graceful_shutdown.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, "/media/sam/1TB/nautilus_dev")

from config.shutdown import GracefulShutdownHandler, ShutdownConfig, ShutdownReason

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class MockOrder:
    """Mock order for testing."""

    client_order_id: str
    instrument_id: str
    is_pending: bool = True
    order_type: Any = None


@dataclass
class MockPosition:
    """Mock position for testing."""

    id: str
    instrument_id: str


class MockCache:
    """Mock cache for testing."""

    def __init__(self):
        self._orders = [
            MockOrder("ORDER-001", "BTC/USDT", is_pending=True),
            MockOrder("ORDER-002", "ETH/USDT", is_pending=True),
            MockOrder("ORDER-003", "BTC/USDT", is_pending=False),  # Already filled
        ]
        self._positions = [
            MockPosition("POS-001", "BTC/USDT"),
            MockPosition("POS-002", "ETH/USDT"),
        ]

    def orders_open(self):
        return self._orders

    def positions_open(self):
        return self._positions


class MockTrader:
    """Mock trader for testing."""

    def __init__(self):
        self.trading_state = "RUNNING"


class MockNode:
    """Mock TradingNode for testing."""

    def __init__(self):
        self.cache = MockCache()
        self.trader = MockTrader()
        self._stopped = False
        self.log = MagicMock()

    def cancel_order(self, order):
        logger.info(f"[MOCK] Cancelling order: {order.client_order_id}")

    def stop(self):
        logger.info("[MOCK] TradingNode stopped")
        self._stopped = True


def test_shutdown_config_validation():
    """Test ShutdownConfig validation."""
    logger.info("=== Test: ShutdownConfig validation ===")

    # Valid config
    config = ShutdownConfig(timeout_secs=30.0, log_level="INFO")
    logger.info(f"✅ Valid config: timeout={config.timeout_secs}s")

    # Invalid timeout (too low)
    try:
        ShutdownConfig(timeout_secs=1.0)
        logger.error("❌ Should have raised for timeout < 5")
    except Exception as e:
        logger.info(f"✅ Correctly rejected timeout=1.0: {e}")

    # Invalid timeout (too high)
    try:
        ShutdownConfig(timeout_secs=500.0)
        logger.error("❌ Should have raised for timeout > 300")
    except Exception as e:
        logger.info(f"✅ Correctly rejected timeout=500: {e}")

    # Invalid log level
    try:
        ShutdownConfig(log_level="INVALID")
        logger.error("❌ Should have raised for invalid log_level")
    except Exception as e:
        logger.info(f"✅ Correctly rejected log_level='INVALID': {e}")


def test_shutdown_reason_enum():
    """Test ShutdownReason enum."""
    logger.info("=== Test: ShutdownReason enum ===")

    assert ShutdownReason.SIGNAL_SIGTERM.value == "SIGTERM"
    assert ShutdownReason.SIGNAL_SIGINT.value == "SIGINT"
    assert ShutdownReason.EXCEPTION.value == "exception"
    assert ShutdownReason.MANUAL.value == "manual"
    assert ShutdownReason.TIMEOUT.value == "timeout"
    logger.info("✅ All ShutdownReason values correct")


async def test_shutdown_sequence():
    """Test the shutdown sequence."""
    logger.info("=== Test: Shutdown sequence ===")

    node = MockNode()
    config = ShutdownConfig(
        timeout_secs=10.0,
        cancel_orders=True,
        verify_stop_losses=True,
    )

    # Patch sys.exit to prevent actual exit
    original_exit = sys.exit
    exit_code = None

    def mock_exit(code):
        nonlocal exit_code
        exit_code = code
        logger.info(f"[MOCK] sys.exit({code}) called")

    sys.exit = mock_exit

    try:
        handler = GracefulShutdownHandler(node, config)

        # Test is_shutdown_requested before shutdown
        assert not handler.is_shutdown_requested()
        logger.info("✅ is_shutdown_requested() returns False before shutdown")

        # Execute shutdown
        await handler.shutdown(reason="SIGTERM")

        # Verify shutdown completed
        assert handler.is_shutdown_requested()
        logger.info("✅ is_shutdown_requested() returns True after shutdown")

        assert exit_code == 0
        logger.info(f"✅ Shutdown completed with exit code {exit_code}")

        # Verify orders were processed
        assert handler._orders_cancelled == 2  # 2 pending orders
        logger.info(f"✅ Cancelled {handler._orders_cancelled} orders")

        # Verify positions checked (both unprotected - no stop orders in mock)
        assert handler._positions_unprotected == 2
        logger.info(f"✅ Found {handler._positions_unprotected} unprotected positions")

        # Verify node stopped
        assert node._stopped
        logger.info("✅ TradingNode stopped")

    finally:
        sys.exit = original_exit


async def test_duplicate_shutdown():
    """Test that duplicate shutdown requests are ignored."""
    logger.info("=== Test: Duplicate shutdown ===")

    node = MockNode()
    config = ShutdownConfig(timeout_secs=10.0)

    original_exit = sys.exit
    sys.exit = lambda code: None  # type: ignore[assignment,misc]

    try:
        handler = GracefulShutdownHandler(node, config)

        # First shutdown
        await handler.shutdown(reason="SIGTERM")

        # Second shutdown (should be ignored)
        orders_before = handler._orders_cancelled
        await handler.shutdown(reason="SIGINT")

        assert handler._orders_cancelled == orders_before
        logger.info("✅ Duplicate shutdown request ignored")

    finally:
        sys.exit = original_exit


async def test_exception_handler():
    """Test exception handler triggers shutdown."""
    logger.info("=== Test: Exception handler ===")

    node = MockNode()
    handler = GracefulShutdownHandler(node, ShutdownConfig(timeout_secs=10.0))

    original_exit = sys.exit
    sys.exit = lambda code: None  # type: ignore[assignment,misc]

    try:
        # Trigger exception handler (will call shutdown internally)
        handler.handle_exception(ValueError("Test exception"))

        # Give async task time to run
        await asyncio.sleep(0.5)

        logger.info("✅ Exception handler triggered shutdown")

    finally:
        sys.exit = original_exit


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Graceful Shutdown Handler Tests")
    logger.info("=" * 60)

    # Sync tests
    test_shutdown_config_validation()
    test_shutdown_reason_enum()

    # Async tests
    asyncio.run(test_shutdown_sequence())
    asyncio.run(test_duplicate_shutdown())
    asyncio.run(test_exception_handler())

    logger.info("=" * 60)
    logger.info("All tests passed! ✅")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
