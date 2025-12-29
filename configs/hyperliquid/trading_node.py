"""Hyperliquid Production TradingNode configuration (Spec 021 - Phase 8).

This module provides factory functions for creating production-ready
TradingNode configurations with Redis caching and reconciliation.

Environment Variables Required (Mainnet):
    HYPERLIQUID_MAINNET_PK: Private key for mainnet trading

Example:
    >>> from configs.hyperliquid.trading_node import create_hyperliquid_trading_node
    >>> config = create_hyperliquid_trading_node(trader_id="TRADER-PROD-001")
    >>> node = TradingNode(config=config)
"""

from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.adapters.hyperliquid import HyperliquidDataClientConfig
from nautilus_trader.adapters.hyperliquid import HyperliquidExecClientConfig
from nautilus_trader.config import (
    CacheConfig,
    DatabaseConfig,
    InstrumentProviderConfig,
    LiveExecEngineConfig,
    TradingNodeConfig,
)

from configs.hyperliquid.data_client import DEFAULT_INSTRUMENTS


def create_hyperliquid_trading_node(
    trader_id: str = "TRADER-HL-001",
    testnet: bool = False,
    instruments: list[str] | None = None,
    load_all: bool = False,
    redis_enabled: bool = True,
    redis_host: str = "localhost",
    redis_port: int = 6379,
    reconciliation: bool = True,
    reconciliation_delay_secs: float = 10.0,
    max_retries: int = 3,
) -> TradingNodeConfig:
    """Create a production-ready Hyperliquid TradingNode configuration.

    This configuration includes:
    - Data client for market data streaming
    - Execution client for order submission
    - Redis cache for persistence (optional)
    - Reconciliation for position consistency (optional)

    Args:
        trader_id: Unique identifier for the trader.
        testnet: If True, connect to testnet. Default False (mainnet).
        instruments: List of instrument IDs to load. If None, uses defaults.
        load_all: If True, load all available instruments.
        redis_enabled: If True, enable Redis caching. Default True.
        redis_host: Redis server host. Default "localhost".
        redis_port: Redis server port. Default 6379.
        reconciliation: If True, enable position reconciliation. Default True.
        reconciliation_delay_secs: Delay before reconciliation on startup. Default 10.0.
        max_retries: Maximum retry attempts for failed requests. Default 3.

    Returns:
        TradingNodeConfig configured for production trading.

    Example:
        >>> config = create_hyperliquid_trading_node(
        ...     trader_id="TRADER-PROD-001",
        ...     testnet=False,
        ...     redis_enabled=True,
        ... )
        >>> node = TradingNode(config=config)
        >>> node.trader.add_strategy(my_strategy)
        >>> node.run()
    """
    # Configure instrument provider
    if load_all:
        instrument_provider = InstrumentProviderConfig(load_all=True)
    else:
        load_ids = instruments or DEFAULT_INSTRUMENTS
        instrument_provider = InstrumentProviderConfig(
            load_all=False,
            load_ids=load_ids,
        )

    # Configure cache (Redis for production)
    cache_config = None
    if redis_enabled:
        cache_config = CacheConfig(
            database=DatabaseConfig(
                host=redis_host,
                port=redis_port,
            ),
            flush_on_start=False,  # Preserve state across restarts
        )

    # Configure execution engine
    exec_engine_config = None
    if reconciliation:
        exec_engine_config = LiveExecEngineConfig(
            reconciliation=True,
            reconciliation_lookback_mins=60 * 24,  # 24 hours
        )

    return TradingNodeConfig(
        trader_id=trader_id,
        data_clients={
            HYPERLIQUID: HyperliquidDataClientConfig(
                instrument_provider=instrument_provider,
                testnet=testnet,
            ),
        },
        exec_clients={
            HYPERLIQUID: HyperliquidExecClientConfig(
                private_key=None,  # Loaded from env
                instrument_provider=instrument_provider,
                testnet=testnet,
                max_retries=max_retries,
                retry_delay_initial_ms=100,
                retry_delay_max_ms=5000,
            ),
        },
        cache=cache_config,
        exec_engine=exec_engine_config,
    )
