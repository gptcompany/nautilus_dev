#!/usr/bin/env python3
"""
Example TradingNode with graceful shutdown handler.

This example demonstrates how to integrate GracefulShutdownHandler with
a TradingNode for production use. The handler ensures orderly shutdown
when receiving SIGTERM/SIGINT signals.

Usage:
    python trading_node_graceful.py

    # In another terminal, send SIGTERM:
    kill -TERM $(pgrep -f trading_node_graceful)
"""

from __future__ import annotations

import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_trading_node_config():
    """Create TradingNode configuration with Redis cache."""
    from nautilus_trader.config import TradingNodeConfig, LiveExecEngineConfig
    from config.cache import create_redis_cache_config

    return TradingNodeConfig(
        trader_id="TRADER-GRACEFUL-001",
        cache=create_redis_cache_config(),
        exec_engine=LiveExecEngineConfig(
            graceful_shutdown_on_exception=True,
        ),
    )


def main():
    """Run TradingNode with graceful shutdown."""
    from nautilus_trader.live.node import TradingNode
    from config.shutdown import GracefulShutdownHandler, ShutdownConfig

    # Create node
    logger.info("Creating TradingNode...")
    config = create_trading_node_config()
    node = TradingNode(config)

    # Setup graceful shutdown handler
    shutdown_config = ShutdownConfig(
        timeout_secs=30.0,
        cancel_orders=True,
        verify_stop_losses=True,
        flush_cache=True,
        log_level="INFO",
    )
    shutdown_handler = GracefulShutdownHandler(node, shutdown_config)

    # Register signal handlers (must be done in main thread before run)
    logger.info("Setting up signal handlers...")
    shutdown_handler.setup_signal_handlers()

    # Run node with exception handling
    try:
        logger.info("Starting TradingNode...")
        node.run()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
        asyncio.run(shutdown_handler.shutdown(reason="SIGINT"))
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        shutdown_handler.handle_exception(e)


if __name__ == "__main__":
    main()
