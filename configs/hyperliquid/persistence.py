"""Hyperliquid Data Persistence configuration (Spec 021 - US2).

This module provides configuration for persisting live Hyperliquid data
to ParquetDataCatalog for backtesting.

Example:
    >>> from configs.hyperliquid.persistence import create_persistence_config
    >>> config = create_persistence_config()
"""

from pathlib import Path

from nautilus_trader.config import (
    StreamingConfig,
    TradingNodeConfig,
)
from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.adapters.hyperliquid import HyperliquidDataClientConfig
from nautilus_trader.config import InstrumentProviderConfig

from configs.hyperliquid.data_client import DEFAULT_INSTRUMENTS

# Default catalog path for Hyperliquid data
DEFAULT_CATALOG_PATH = "./catalog/hyperliquid"


def create_persistence_config(
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
) -> StreamingConfig:
    """Create streaming configuration for data persistence.

    Args:
        catalog_path: Path to the ParquetDataCatalog directory.
                     Default is "./catalog/hyperliquid".

    Returns:
        StreamingConfig for persisting data to Parquet files.

    Example:
        >>> config = create_persistence_config("./my_catalog")
    """
    return StreamingConfig(
        catalog_path=str(catalog_path),
    )


def create_recording_trading_node(
    trader_id: str = "TRADER-HL-RECORD",
    testnet: bool = False,
    instruments: list[str] | None = None,
    catalog_path: str | Path = DEFAULT_CATALOG_PATH,
) -> TradingNodeConfig:
    """Create a TradingNode configuration for recording live data.

    This configuration enables automatic persistence of market data
    (quotes, trades, orderbook) to a ParquetDataCatalog.

    Args:
        trader_id: Unique identifier for the trader. Default "TRADER-HL-RECORD".
        testnet: If True, connect to Hyperliquid testnet. Default False.
        instruments: List of instrument IDs to record. If None, uses defaults.
        catalog_path: Path for the ParquetDataCatalog. Default "./catalog/hyperliquid".

    Returns:
        TradingNodeConfig configured for data recording.

    Example:
        >>> config = create_recording_trading_node(testnet=False)
        >>> node = TradingNode(config=config)
        >>> # Add strategy that subscribes to data
        >>> node.run()  # Data auto-persisted to catalog
    """
    load_ids = instruments or DEFAULT_INSTRUMENTS

    return TradingNodeConfig(
        trader_id=trader_id,
        data_clients={
            HYPERLIQUID: HyperliquidDataClientConfig(
                instrument_provider=InstrumentProviderConfig(
                    load_all=False,
                    load_ids=load_ids,
                ),
                testnet=testnet,
            ),
        },
        streaming=create_persistence_config(catalog_path),
    )
