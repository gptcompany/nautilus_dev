"""
Binance Client Configuration Builders (T033).

Builds NautilusTrader Binance data and exec client configurations.
"""

from __future__ import annotations

from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
from nautilus_trader.adapters.binance.config import (
    BinanceDataClientConfig,
    BinanceExecClientConfig,
)
from nautilus_trader.config import InstrumentProviderConfig

from config.models import BinanceCredentials

# Account type mapping
_BINANCE_ACCOUNT_TYPES = {
    "SPOT": BinanceAccountType.SPOT,
    "USDT_FUTURES": BinanceAccountType.USDT_FUTURES,
    "COIN_FUTURES": BinanceAccountType.COIN_FUTURES,
}


def build_binance_data_client_config(
    credentials: BinanceCredentials,
) -> BinanceDataClientConfig:
    """
    Build Binance data client configuration.

    Parameters
    ----------
    credentials : BinanceCredentials
        Binance API credentials with account settings.

    Returns
    -------
    BinanceDataClientConfig
        NautilusTrader Binance data client configuration.
    """
    account_type = _BINANCE_ACCOUNT_TYPES[credentials.account_type]

    return BinanceDataClientConfig(
        account_type=account_type,
        testnet=credentials.testnet,
        us=credentials.us,
        update_instruments_interval_mins=60,
        instrument_provider=InstrumentProviderConfig(load_all=False),
    )


def build_binance_exec_client_config(
    credentials: BinanceCredentials,
) -> BinanceExecClientConfig:
    """
    Build Binance execution client configuration.

    Parameters
    ----------
    credentials : BinanceCredentials
        Binance API credentials with account settings.

    Returns
    -------
    BinanceExecClientConfig
        NautilusTrader Binance exec client configuration.

    Notes
    -----
    Production settings:
    - use_reduce_only=True for safe position exits
    - use_position_ids=True for hedging mode tracking
    - recv_window_ms=5000 for network latency tolerance
    - max_retries=3 for transient error handling
    """
    account_type = _BINANCE_ACCOUNT_TYPES[credentials.account_type]

    return BinanceExecClientConfig(
        account_type=account_type,
        testnet=credentials.testnet,
        us=credentials.us,
        use_reduce_only=True,
        use_position_ids=True,
        recv_window_ms=5000,
        max_retries=3,
        listen_key_ping_max_failures=3,
        instrument_provider=InstrumentProviderConfig(load_all=False),
    )
