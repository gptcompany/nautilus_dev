"""
Example TradingNode Configuration with Redis Cache (Spec 018 - T010)

Demonstrates how to configure TradingNode for position, order,
account, and instrument persistence with Redis backend.
"""

from nautilus_trader.config import (
    TradingNodeConfig,
    LiveExecEngineConfig,
)

# Import our Redis cache config factory
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.cache.redis_config import create_redis_cache_config


def create_trading_node_config(
    trader_id: str = "TRADER-001",
    reconciliation: bool = True,
) -> TradingNodeConfig:
    """
    Create TradingNode configuration with Redis cache.

    This configuration persists:
    - Positions (trader-position:*)
    - Orders (trader-order:*)
    - Accounts (trader-account:*)
    - Instruments (trader-instrument:*)

    Args:
        trader_id: Unique trader identifier
        reconciliation: Enable exchange reconciliation on startup

    Returns:
        TradingNodeConfig ready for live trading with persistence
    """
    return TradingNodeConfig(
        trader_id=trader_id,
        cache=create_redis_cache_config(),
        exec_engine=LiveExecEngineConfig(
            reconciliation=reconciliation,
            reconciliation_lookback_mins=None,  # Max from venue
            reconciliation_startup_delay_secs=10.0,  # Minimum for production
            generate_missing_orders=True,
            # Continuous position checking
            position_check_interval_secs=30.0,
            position_check_lookback_mins=60,
            position_check_threshold_ms=5_000,
            # Graceful shutdown
            graceful_shutdown_on_exception=True,
        ),
    )


# Example usage
if __name__ == "__main__":
    config = create_trading_node_config()
    print("TradingNode config created:")
    print(f"  Trader ID: {config.trader_id}")
    print(f"  Cache type: {config.cache.database.type}")
    print(f"  Encoding: {config.cache.encoding}")
    print(f"  Persist events: {config.cache.persist_account_events}")
    print(f"  Reconciliation: {config.exec_engine.reconciliation}")
