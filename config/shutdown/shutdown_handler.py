"""
Graceful shutdown handler for NautilusTrader TradingNode.

This module provides a handler that ensures orderly shutdown when receiving
SIGTERM/SIGINT signals or when unhandled exceptions occur.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from config.shutdown.shutdown_config import ShutdownConfig, ShutdownReason

if TYPE_CHECKING:
    from nautilus_trader.live.node import TradingNode


class GracefulShutdownHandler:
    """Handles graceful shutdown of TradingNode.

    Shutdown sequence:
    1. Halt trading (TradingState.HALTED)
    2. Cancel all pending orders
    3. Verify stop-losses for open positions (warning if missing)
    4. Flush cache (native NautilusTrader behavior)
    5. Close exchange connections
    6. Exit

    Example:
        ```python
        node = TradingNode(config)
        shutdown_handler = GracefulShutdownHandler(node, ShutdownConfig())
        shutdown_handler.setup_signal_handlers()

        try:
            node.run()
        except Exception as e:
            asyncio.run(shutdown_handler.shutdown(reason="exception"))
        ```
    """

    def __init__(self, node: TradingNode, config: ShutdownConfig | None = None) -> None:
        """Initialize the shutdown handler.

        Args:
            node: The TradingNode to manage shutdown for
            config: Shutdown configuration (uses defaults if None)
        """
        self.node = node
        self.config = config or ShutdownConfig()
        self._shutdown_requested = False
        self._shutdown_lock = asyncio.Lock()
        self._shutdown_started_at: datetime | None = None
        self._shutdown_reason: ShutdownReason | None = None
        self._orders_cancelled = 0
        self._positions_unprotected = 0
        self._logger = logging.getLogger(__name__)

    def setup_signal_handlers(self) -> None:
        """Register signal handlers for SIGTERM/SIGINT.

        Uses asyncio signal handlers for proper integration with the event loop.
        Must be called from the main thread before node.run().
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, use get_event_loop for setup
            loop = asyncio.get_event_loop()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_signal(s)),
            )
        self._logger.info("Signal handlers registered for SIGTERM/SIGINT")

    async def _handle_signal(self, signum: int) -> None:
        """Handle incoming signal.

        Args:
            signum: The signal number received
        """
        reason = (
            ShutdownReason.SIGNAL_SIGTERM
            if signum == signal.SIGTERM
            else ShutdownReason.SIGNAL_SIGINT
        )
        self._logger.warning(f"Received {reason.value}, initiating graceful shutdown")
        await self.shutdown(reason=reason.value)

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested.

        Returns:
            True if shutdown is in progress or requested
        """
        return self._shutdown_requested

    async def shutdown(self, reason: str = "signal") -> None:
        """Execute graceful shutdown sequence.

        Args:
            reason: Why shutdown was triggered (for logging)
        """
        # Use lock to prevent race condition on concurrent shutdown calls
        async with self._shutdown_lock:
            if self._shutdown_requested:
                self._logger.warning("Shutdown already in progress, ignoring duplicate request")
                return

            self._shutdown_requested = True
            self._shutdown_started_at = datetime.utcnow()
        # Map reason string to enum, default to MANUAL for unknown reasons
        try:
            self._shutdown_reason = ShutdownReason(reason)
        except ValueError:
            self._shutdown_reason = ShutdownReason.MANUAL
            self._logger.warning(f"Unknown shutdown reason '{reason}', using MANUAL")

        self._logger.info(
            f"Starting graceful shutdown (reason: {reason}, timeout: {self.config.timeout_secs}s)"
        )

        try:
            await asyncio.wait_for(
                self._shutdown_sequence(),
                timeout=self.config.timeout_secs,
            )
        except TimeoutError:
            self._logger.error(
                f"Shutdown timed out after {self.config.timeout_secs}s, forcing exit"
            )
            self._force_exit(1)
        except Exception as e:
            self._logger.exception(f"Error during shutdown: {e}")
            self._force_exit(1)

    async def _shutdown_sequence(self) -> None:
        """Execute the shutdown sequence steps."""
        # Step 1: Halt trading
        await self._halt_trading()

        # Step 2: Cancel pending orders
        if self.config.cancel_orders:
            await self._cancel_all_orders()

        # Step 3: Verify stop-losses
        if self.config.verify_stop_losses:
            await self._verify_stop_losses()

        # Step 4: Flush cache (native behavior, just log)
        if self.config.flush_cache:
            self._logger.info("Cache flush handled by NautilusTrader native behavior")

        # Step 5: Close connections
        await self._close_connections()

        # Log completion
        if self._shutdown_started_at is not None:
            elapsed = (datetime.utcnow() - self._shutdown_started_at).total_seconds()
        else:
            elapsed = 0.0
        self._logger.info(
            f"Shutdown complete in {elapsed:.2f}s "
            f"(orders_cancelled={self._orders_cancelled}, "
            f"positions_unprotected={self._positions_unprotected})"
        )

        self._force_exit(0)

    async def _halt_trading(self) -> None:
        """Halt trading to prevent new orders."""
        try:
            from nautilus_trader.model.enums import TradingState

            if hasattr(self.node, "trader") and self.node.trader is not None:
                self.node.trader.trading_state = TradingState.HALTED
                self._logger.info("Trading halted (TradingState.HALTED)")
            else:
                self._logger.warning("No trader available to halt")
        except ImportError:
            self._logger.warning("TradingState not available, skipping halt")
        except Exception as e:
            self._logger.error(f"Failed to halt trading: {e}")

    async def _cancel_all_orders(self) -> None:
        """Cancel all open/pending orders."""
        try:
            if not hasattr(self.node, "cache"):
                self._logger.warning("No cache available, skipping order cancellation")
                return

            open_orders = self.node.cache.orders_open() or []
            self._logger.info(f"Found {len(open_orders)} open orders to cancel")

            for order in open_orders:
                try:
                    if hasattr(order, "is_pending") and order.is_pending:
                        self.node.cancel_order(order)
                        self._orders_cancelled += 1
                except Exception as e:
                    self._logger.error(f"Failed to cancel order {order.client_order_id}: {e}")

            # Wait for cancellations to process
            if self._orders_cancelled > 0:
                await asyncio.sleep(2.0)
                self._logger.info(f"Cancelled {self._orders_cancelled} orders")

        except Exception as e:
            self._logger.error(f"Error during order cancellation: {e}")

    async def _verify_stop_losses(self) -> None:
        """Verify all open positions have stop-loss orders."""
        try:
            if not hasattr(self.node, "cache"):
                self._logger.warning("No cache available, skipping stop-loss verification")
                return

            from nautilus_trader.model.enums import OrderType

            positions = self.node.cache.positions_open() or []
            open_orders = self.node.cache.orders_open() or []

            for position in positions:
                # Find stop-loss orders for this position's instrument
                stops = [
                    o
                    for o in open_orders
                    if o.instrument_id == position.instrument_id
                    and hasattr(o, "order_type")
                    and o.order_type == OrderType.STOP_MARKET
                ]
                if not stops:
                    self._positions_unprotected += 1
                    self._logger.warning(
                        f"Position {position.id} ({position.instrument_id}) has no stop-loss order!"
                    )

            if self._positions_unprotected == 0 and len(positions) > 0:
                self._logger.info(f"All {len(positions)} positions have stop-loss protection")

        except ImportError:
            self._logger.warning("OrderType not available, skipping stop-loss verification")
        except Exception as e:
            self._logger.error(f"Error during stop-loss verification: {e}")

    async def _close_connections(self) -> None:
        """Close exchange connections."""
        try:
            if hasattr(self.node, "stop"):
                self._logger.info("Stopping TradingNode...")
                self.node.stop()
            elif hasattr(self.node, "dispose"):
                self._logger.info("Disposing TradingNode...")
                self.node.dispose()
            else:
                self._logger.warning("No stop/dispose method available on node")
        except Exception as e:
            self._logger.error(f"Error closing connections: {e}")

    def _force_exit(self, code: int) -> None:
        """Force exit with given code.

        Args:
            code: Exit code (0 for success, non-zero for error)
        """
        self._logger.info(f"Exiting with code {code}")
        sys.exit(code)

    def handle_exception(self, exc: Exception) -> None:
        """Handle unhandled exception by triggering graceful shutdown.

        Args:
            exc: The exception that was raised
        """
        self._logger.exception(f"Unhandled exception: {exc}")
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(self.shutdown(reason=ShutdownReason.EXCEPTION.value))
            # Add callback to log any exceptions from the shutdown task
            task.add_done_callback(self._shutdown_task_done)
        except RuntimeError:
            # No running loop, run synchronously
            asyncio.run(self.shutdown(reason=ShutdownReason.EXCEPTION.value))

    def _shutdown_task_done(self, task: asyncio.Task) -> None:
        """Callback for shutdown task completion.

        Args:
            task: The completed shutdown task
        """
        if task.cancelled():
            self._logger.warning("Shutdown task was cancelled")
        elif task.exception() is not None:
            self._logger.exception(
                f"Shutdown task failed: {task.exception()}", exc_info=task.exception()
            )
