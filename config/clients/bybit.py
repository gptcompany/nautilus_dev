"""
Bybit Client Configuration Builders (T034).

Builds NautilusTrader Bybit data and exec client configurations.
"""

from __future__ import annotations

from nautilus_trader.adapters.bybit import BybitProductType
from nautilus_trader.adapters.bybit.config import (
    BybitDataClientConfig,
    BybitExecClientConfig,
)
from nautilus_trader.config import InstrumentProviderConfig

from config.models import BybitCredentials

# Product type mapping
_BYBIT_PRODUCT_TYPES = {
    "LINEAR": BybitProductType.LINEAR,
    "INVERSE": BybitProductType.INVERSE,
    "SPOT": BybitProductType.SPOT,
    "OPTION": BybitProductType.OPTION,
}


def build_bybit_data_client_config(
    credentials: BybitCredentials,
) -> BybitDataClientConfig:
    """
    Build Bybit data client configuration.

    Parameters
    ----------
    credentials : BybitCredentials
        Bybit API credentials with product settings.

    Returns
    -------
    BybitDataClientConfig
        NautilusTrader Bybit data client configuration.

    Notes
    -----
    Known limitations (from CLAUDE.md):
    - Hedge mode (positionIdx) NOT supported in Rust port
    - bars_timestamp_on_close not applied to WebSocket bars
    - 1-bar offset in indicators (WebSocket vs HTTP)
    """
    product_types = [_BYBIT_PRODUCT_TYPES[pt] for pt in credentials.product_types]

    return BybitDataClientConfig(
        product_types=product_types,
        testnet=credentials.testnet,
        demo=credentials.demo,
        update_instruments_interval_mins=60,
        instrument_provider=InstrumentProviderConfig(load_all=False),
    )


def build_bybit_exec_client_config(
    credentials: BybitCredentials,
) -> BybitExecClientConfig:
    """
    Build Bybit execution client configuration.

    Parameters
    ----------
    credentials : BybitCredentials
        Bybit API credentials with product settings.

    Returns
    -------
    BybitExecClientConfig
        NautilusTrader Bybit exec client configuration.

    Notes
    -----
    Production settings:
    - recv_window_ms=5000 for network latency tolerance
    - max_retries=3 with exponential backoff
    - NETTING mode only (hedge mode not supported)
    """
    product_types = [_BYBIT_PRODUCT_TYPES[pt] for pt in credentials.product_types]

    return BybitExecClientConfig(
        product_types=product_types,
        testnet=credentials.testnet,
        demo=credentials.demo,
        recv_window_ms=5000,
        max_retries=3,
        retry_delay_initial_ms=1000,
        retry_delay_max_ms=10000,
        instrument_provider=InstrumentProviderConfig(load_all=False),
    )
