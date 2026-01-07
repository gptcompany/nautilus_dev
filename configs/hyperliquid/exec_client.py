"""Hyperliquid Execution Client configuration factory (Spec 021 - US3).

This module provides factory functions for creating HyperliquidExecClientConfig
for order execution on Hyperliquid.

Environment Variables:
    HYPERLIQUID_TESTNET_PK: Private key for testnet trading
    HYPERLIQUID_PK: Private key for mainnet trading (production)
    HYPERLIQUID_TESTNET_VAULT: Optional vault address for testnet
    HYPERLIQUID_VAULT: Optional vault address for mainnet

Example:
    >>> from configs.hyperliquid import create_hyperliquid_exec_client
    >>> exec_config = create_hyperliquid_exec_client(testnet=True)
"""

from nautilus_trader.adapters.hyperliquid import HYPERLIQUID, HyperliquidExecClientConfig
from nautilus_trader.config import InstrumentProviderConfig

from configs.hyperliquid.data_client import DEFAULT_INSTRUMENTS


def create_hyperliquid_exec_client(
    testnet: bool = True,
    instruments: list[str] | None = None,
    load_all: bool = False,
    max_retries: int = 3,
    retry_delay_initial_ms: int = 100,
    retry_delay_max_ms: int = 5000,
    http_timeout_secs: int = 10,
) -> dict:
    """Create Hyperliquid execution client configuration.

    IMPORTANT: Private key is loaded from environment variables:
    - Testnet: HYPERLIQUID_TESTNET_PK
    - Mainnet: HYPERLIQUID_PK

    Never pass private keys directly in code!

    Args:
        testnet: If True, connect to Hyperliquid testnet. Default True for safety.
        instruments: List of instrument IDs to load. If None, uses DEFAULT_INSTRUMENTS.
        load_all: If True, load all available instruments.
        max_retries: Maximum retry attempts for failed requests. Default 3.
        retry_delay_initial_ms: Initial retry delay in milliseconds. Default 100.
        retry_delay_max_ms: Maximum retry delay in milliseconds. Default 5000.
        http_timeout_secs: HTTP request timeout in seconds. Default 10.

    Returns:
        Dictionary with HYPERLIQUID key and HyperliquidExecClientConfig value,
        ready to be passed to TradingNodeConfig.exec_clients.

    Example:
        >>> exec_config = create_hyperliquid_exec_client(testnet=True)
        >>> node_config = TradingNodeConfig(exec_clients=exec_config)
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
        HYPERLIQUID: HyperliquidExecClientConfig(
            private_key=None,  # Loaded from env: HYPERLIQUID_TESTNET_PK or HYPERLIQUID_MAINNET_PK
            vault_address=None,  # Optional, loaded from env if needed
            instrument_provider=instrument_provider,
            testnet=testnet,
            max_retries=max_retries,
            retry_delay_initial_ms=retry_delay_initial_ms,
            retry_delay_max_ms=retry_delay_max_ms,
            http_timeout_secs=http_timeout_secs,
        ),
    }
