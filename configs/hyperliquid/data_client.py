"""Hyperliquid Data Client configuration factory.

This module provides factory functions for creating HyperliquidDataClientConfig
and data-only TradingNode configurations.

Example:
    >>> from configs.hyperliquid import create_hyperliquid_data_client
    >>> data_config = create_hyperliquid_data_client(testnet=True)
"""

from nautilus_trader.adapters.hyperliquid import HYPERLIQUID, HyperliquidDataClientConfig
from nautilus_trader.config import InstrumentProviderConfig, TradingNodeConfig

# Default instruments for Hyperliquid perpetual futures
DEFAULT_INSTRUMENTS: list[str] = [
    "BTC-USD-PERP.HYPERLIQUID",
    "ETH-USD-PERP.HYPERLIQUID",
]


def create_hyperliquid_data_client(
    testnet: bool = False,
    instruments: list[str] | None = None,
    load_all: bool = False,
    http_timeout_secs: int = 10,
) -> dict:
    """Create Hyperliquid data client configuration.

    Args:
        testnet: If True, connect to Hyperliquid testnet. Default False (mainnet).
        instruments: List of instrument IDs to load. If None, uses DEFAULT_INSTRUMENTS.
        load_all: If True, load all available instruments. Overrides instruments param.
        http_timeout_secs: HTTP request timeout in seconds. Default 10.

    Returns:
        Dictionary with HYPERLIQUID key and HyperliquidDataClientConfig value,
        ready to be passed to TradingNodeConfig.data_clients.

    Example:
        >>> config = create_hyperliquid_data_client(testnet=True)
        >>> node_config = TradingNodeConfig(data_clients=config)
    """
    if load_all:
        instrument_provider = InstrumentProviderConfig(load_all=True)
    else:
        load_ids = instruments or DEFAULT_INSTRUMENTS
        instrument_provider = InstrumentProviderConfig(
            load_all=False,
            load_ids=load_ids,
        )

    return {
        HYPERLIQUID: HyperliquidDataClientConfig(
            instrument_provider=instrument_provider,
            testnet=testnet,
            http_timeout_secs=http_timeout_secs,
        ),
    }


def create_data_only_trading_node(
    trader_id: str = "TRADER-HL-DATA",
    testnet: bool = False,
    instruments: list[str] | None = None,
    load_all: bool = False,
) -> TradingNodeConfig:
    """Create a data-only TradingNode configuration (no execution).

    Use this for streaming market data without order execution capability.
    Useful for data recording and analysis.

    Args:
        trader_id: Unique identifier for the trader. Default "TRADER-HL-DATA".
        testnet: If True, connect to Hyperliquid testnet. Default False (mainnet).
        instruments: List of instrument IDs to load. If None, uses DEFAULT_INSTRUMENTS.
        load_all: If True, load all available instruments.

    Returns:
        TradingNodeConfig configured for data streaming only.

    Example:
        >>> config = create_data_only_trading_node(testnet=False)
        >>> node = TradingNode(config=config)
        >>> node.run()
    """
    data_clients = create_hyperliquid_data_client(
        testnet=testnet,
        instruments=instruments,
        load_all=load_all,
    )

    return TradingNodeConfig(
        trader_id=trader_id,
        data_clients=data_clients,
    )
