"""Hyperliquid Testnet configuration (Spec 021 - US3/US5).

This module provides testnet-specific configurations for development and testing.

Environment Variables Required:
    HYPERLIQUID_TESTNET_PK: Private key for testnet trading

Example:
    >>> from configs.hyperliquid.testnet import create_testnet_trading_node
    >>> config = create_testnet_trading_node()
    >>> node = TradingNode(config=config)
"""

from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.adapters.hyperliquid import HyperliquidDataClientConfig
from nautilus_trader.adapters.hyperliquid import HyperliquidExecClientConfig
from nautilus_trader.config import InstrumentProviderConfig, TradingNodeConfig

from configs.hyperliquid.data_client import DEFAULT_INSTRUMENTS


def create_testnet_trading_node(
    trader_id: str = "TRADER-HL-TESTNET",
    instruments: list[str] | None = None,
    load_all: bool = False,
    max_retries: int = 3,
) -> TradingNodeConfig:
    """Create a TradingNode configuration for Hyperliquid testnet.

    This configuration enables both data streaming and order execution
    on the Hyperliquid testnet for development and testing.

    Args:
        trader_id: Unique identifier for the trader. Default "TRADER-HL-TESTNET".
        instruments: List of instrument IDs to load. If None, uses DEFAULT_INSTRUMENTS.
        load_all: If True, load all available instruments.
        max_retries: Maximum retry attempts for failed requests. Default 3.

    Returns:
        TradingNodeConfig configured for testnet trading.

    Example:
        >>> config = create_testnet_trading_node()
        >>> node = TradingNode(config=config)
        >>> node.trader.add_strategy(my_strategy)
        >>> node.run()
    """
    if load_all:
        instrument_provider = InstrumentProviderConfig(load_all=True)
    else:
        load_ids = instruments or DEFAULT_INSTRUMENTS
        instrument_provider = InstrumentProviderConfig(
            load_all=False,
            load_ids=load_ids,
        )

    return TradingNodeConfig(
        trader_id=trader_id,
        data_clients={
            HYPERLIQUID: HyperliquidDataClientConfig(
                instrument_provider=instrument_provider,
                testnet=True,
            ),
        },
        exec_clients={
            HYPERLIQUID: HyperliquidExecClientConfig(
                private_key=None,  # Loaded from HYPERLIQUID_TESTNET_PK
                instrument_provider=instrument_provider,
                testnet=True,
                max_retries=max_retries,
                retry_delay_initial_ms=100,
                retry_delay_max_ms=5000,
            ),
        },
    )
