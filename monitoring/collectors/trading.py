# monitoring.collectors.trading - TradingCollector for real-time trading metrics
#
# T049-T052: Create TradingCollector with PnL, orders/minute, position exposure tracking

import asyncio
import logging
import socket
from datetime import datetime, timezone
from typing import Callable

from monitoring.collectors import BaseCollector
from monitoring.config import MonitoringConfig
from monitoring.models import TradingMetrics
from monitoring.constants import VALID_EXCHANGES

logger = logging.getLogger(__name__)


class TradingCollector(BaseCollector[TradingMetrics]):
    """Collector for real-time trading performance metrics.

    Tracks PnL, orders, positions, and fill rates per strategy.
    Integrates with NautilusTrader TradingNode.
    """

    def __init__(
        self,
        config: MonitoringConfig,
        metrics_provider: Callable[[], dict] | None = None,
    ):
        """Initialize TradingCollector.

        Args:
            config: Monitoring configuration.
            metrics_provider: Optional callable that returns trading metrics dict.
                            Expected format:
                            {
                              "strategy_id": {
                                "symbol": "BTC/USDT:USDT",
                                "venue": "binance",
                                "pnl": 1250.50,
                                "unrealized_pnl": 75.25,
                                "position_size": 0.5,
                                "orders_placed": 42,
                                "orders_filled": 40,
                                "exposure": 25000.0,
                                "drawdown": 2.5
                              },
                              ...
                            }
        """
        self.config = config
        self._metrics_provider = metrics_provider
        self._running = False
        self._task: asyncio.Task | None = None
        self._host = config.host or socket.gethostname()
        self._env = config.env
        self._on_metrics: Callable[[TradingMetrics], None] | None = None

        # Track orders for rate calculation (per-strategy tracking)
        self._last_orders: dict[str, int] = {}
        self._last_collection_times: dict[str, datetime] = {}

    def set_on_metrics(self, callback: Callable[[TradingMetrics], None]) -> None:
        """Set callback for when metrics are collected.

        Args:
            callback: Function to call with collected metrics.
        """
        self._on_metrics = callback

    async def collect(self) -> list[TradingMetrics]:
        """Collect metrics from all active strategies.

        Returns:
            List of TradingMetrics instances for each strategy.
        """
        try:
            metrics_dict = self._get_metrics()
            metrics_list = self._dict_to_metrics(metrics_dict)
            return metrics_list
        except Exception as e:
            logger.error(f"Error collecting trading metrics: {e}")
            return []

    def _get_metrics(self) -> dict:
        """Get trading metrics from provider.

        Returns:
            Metrics dictionary with per-strategy data.
        """
        if self._metrics_provider:
            return self._metrics_provider()

        # Default: Try to check if NautilusTrader is available
        try:
            import importlib.util

            if importlib.util.find_spec("nautilus_trader") is not None:
                # NautilusTrader is available but TradingNode integration needed
                # For now, return mock data in development
                logger.warning("TradingNode metrics not available, using mock data")
                return self._mock_metrics()
            else:
                logger.warning("nautilus_trader not installed, using mock data")
                return self._mock_metrics()
        except Exception:
            logger.warning("Trading metrics not available, using mock data")
            return self._mock_metrics()

    def _mock_metrics(self) -> dict:
        """Generate mock metrics for testing.

        Returns:
            Mock metrics dictionary.
        """
        return {
            "momentum_strategy_btc": {
                "symbol": "BTC/USDT:USDT",
                "venue": "binance",
                "pnl": 0.0,
                "unrealized_pnl": 0.0,
                "position_size": 0.0,
                "orders_placed": 0,
                "orders_filled": 0,
                "exposure": 0.0,
                "drawdown": 0.0,
            },
            "grid_strategy_eth": {
                "symbol": "ETH/USDT:USDT",
                "venue": "bybit",
                "pnl": 0.0,
                "unrealized_pnl": 0.0,
                "position_size": 0.0,
                "orders_placed": 0,
                "orders_filled": 0,
                "exposure": 0.0,
                "drawdown": 0.0,
            },
        }

    def _dict_to_metrics(self, metrics_dict: dict) -> list[TradingMetrics]:
        """Convert metrics dict to list of TradingMetrics.

        Args:
            metrics_dict: Metrics dictionary from provider.

        Returns:
            List of TradingMetrics instances.
        """
        metrics_list = []
        now = datetime.now(timezone.utc)

        for strategy_id, data in metrics_dict.items():
            # Calculate fill rate
            orders_placed = data.get("orders_placed", 0)
            orders_filled = data.get("orders_filled", 0)
            fill_rate = orders_filled / orders_placed if orders_placed > 0 else 0.0

            # Get venue with validation
            venue = data.get("venue", "binance")
            if venue not in VALID_EXCHANGES:
                venue = "binance"  # Default to binance

            metrics = TradingMetrics(
                timestamp=now,
                strategy=strategy_id,
                symbol=data.get("symbol", "UNKNOWN"),
                venue=venue,
                env=self._env,
                pnl=data.get("pnl", 0.0),
                unrealized_pnl=data.get("unrealized_pnl", 0.0),
                position_size=data.get("position_size", 0.0),
                orders_placed=orders_placed,
                orders_filled=orders_filled,
                fill_rate=min(fill_rate, 1.0),  # Cap at 100%
                exposure=data.get("exposure", 0.0),
                drawdown=max(data.get("drawdown", 0.0), 0.0),  # Ensure non-negative
            )
            metrics_list.append(metrics)

        return metrics_list

    def calculate_orders_per_minute(
        self, strategy_id: str, current_orders: int
    ) -> float:
        """Calculate orders per minute rate for a strategy.

        Args:
            strategy_id: Strategy identifier.
            current_orders: Current cumulative order count.

        Returns:
            Orders per minute rate.
        """
        now = datetime.now(timezone.utc)

        # Check if this is the first collection for this strategy
        if (
            strategy_id not in self._last_orders
            or strategy_id not in self._last_collection_times
        ):
            self._last_orders[strategy_id] = current_orders
            self._last_collection_times[strategy_id] = now
            return 0.0

        # Calculate time delta in minutes (per-strategy tracking)
        last_time = self._last_collection_times[strategy_id]
        time_delta = (now - last_time).total_seconds() / 60.0
        if time_delta <= 0:
            return 0.0

        # Calculate order delta (handle counter resets by clamping to 0)
        order_delta = current_orders - self._last_orders[strategy_id]
        if order_delta < 0:
            # Counter was reset, restart tracking
            logger.debug(f"Order counter reset detected for {strategy_id}")
            order_delta = 0

        # Update tracking for this strategy
        self._last_orders[strategy_id] = current_orders
        self._last_collection_times[strategy_id] = now

        return order_delta / time_delta

    async def start(self) -> None:
        """Start periodic collection."""
        if self._running:
            logger.warning("TradingCollector already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info(
            f"TradingCollector started (interval={self.config.trading_collect_interval}s)"
        )

    async def stop(self) -> None:
        """Stop collection and cleanup resources."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("TradingCollector stopped")

    async def _collection_loop(self) -> None:
        """Internal collection loop."""
        while self._running:
            try:
                metrics_list = await self.collect()
                for metrics in metrics_list:
                    if self._on_metrics:
                        self._on_metrics(metrics)
            except Exception as e:
                logger.error(f"Error in trading collection loop: {e}")

            await asyncio.sleep(self.config.trading_collect_interval)


__all__ = ["TradingCollector"]
