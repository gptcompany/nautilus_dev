"""Hyperliquid configuration module for NautilusTrader integration.

This module provides factory functions for configuring Hyperliquid data and execution
clients within the NautilusTrader framework.

Key Components:
- create_hyperliquid_data_client(): Factory for data client configuration
- create_hyperliquid_exec_client(): Factory for execution client configuration
- create_hyperliquid_trading_node(): Factory for complete TradingNode configuration
- create_testnet_trading_node(): Factory for testnet-specific configuration
- create_recording_trading_node(): Factory for data recording configuration
"""

from configs.hyperliquid.data_client import (
    DEFAULT_INSTRUMENTS,
    create_data_only_trading_node,
    create_hyperliquid_data_client,
)
from configs.hyperliquid.exec_client import create_hyperliquid_exec_client
from configs.hyperliquid.persistence import (
    DEFAULT_CATALOG_PATH,
    create_persistence_config,
    create_recording_trading_node,
)
from configs.hyperliquid.testnet import create_testnet_trading_node
from configs.hyperliquid.trading_node import create_hyperliquid_trading_node

__all__ = [
    # Data client
    "create_hyperliquid_data_client",
    "create_data_only_trading_node",
    "DEFAULT_INSTRUMENTS",
    # Execution client
    "create_hyperliquid_exec_client",
    # Persistence
    "create_persistence_config",
    "create_recording_trading_node",
    "DEFAULT_CATALOG_PATH",
    # Testnet
    "create_testnet_trading_node",
    # Production
    "create_hyperliquid_trading_node",
]
