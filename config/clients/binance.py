"""
Binance Client Configuration Builders (Spec 015).

Builds NautilusTrader Binance data and exec client configurations.

Notes
-----
- USDT_FUTURES: Perpetual USDT-margined futures
- COIN_FUTURES: Coin-margined futures
- ONE-WAY (NETTING) mode recommended due to HEDGE mode bug #3104
- Requires NautilusTrader Nightly >= 2025-12-10 for Algo Order API (STOP_MARKET)
"""

from __future__ import annotations

from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
from nautilus_trader.adapters.binance.config import (
    BinanceDataClientConfig,
    BinanceExecClientConfig,
)
from nautilus_trader.adapters.binance.futures.enums import BinanceFuturesMarginType
from nautilus_trader.config import InstrumentProviderConfig

from config.models import BinanceCredentials

# Account type mapping
_BINANCE_ACCOUNT_TYPES = {
    "SPOT": BinanceAccountType.SPOT,
    "USDT_FUTURES": BinanceAccountType.USDT_FUTURES,
    "COIN_FUTURES": BinanceAccountType.COIN_FUTURES,
}

# Margin type mapping for futures
_MARGIN_TYPES = {
    "CROSS": BinanceFuturesMarginType.CROSS,
    "ISOLATED": BinanceFuturesMarginType.ISOLATED,
}


def build_binance_data_client_config(
    credentials: BinanceCredentials,
    update_instruments_interval_mins: int = 60,
) -> BinanceDataClientConfig:
    """
    Build Binance data client configuration.

    Parameters
    ----------
    credentials : BinanceCredentials
        Binance API credentials with account settings.
    update_instruments_interval_mins : int, default 60
        Interval in minutes to update instrument definitions.

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
        update_instruments_interval_mins=update_instruments_interval_mins,
        instrument_provider=InstrumentProviderConfig(load_all=False),
    )


def build_binance_exec_client_config(
    credentials: BinanceCredentials,
    max_retries: int = 3,
    retry_delay_initial_ms: int = 500,
    retry_delay_max_ms: int = 5000,
    futures_leverages: dict[str, int] | None = None,
    futures_margin_types: dict[str, str] | None = None,
) -> BinanceExecClientConfig:
    """
    Build Binance execution client configuration.

    Parameters
    ----------
    credentials : BinanceCredentials
        Binance API credentials with account settings.
    max_retries : int, default 3
        Maximum number of retries for transient errors.
        Limit to 3 to avoid rate limit bans.
    retry_delay_initial_ms : int, default 500
        Initial retry delay in milliseconds.
    retry_delay_max_ms : int, default 5000
        Maximum retry delay in milliseconds (exponential backoff cap).
    futures_leverages : dict[str, int], optional
        Symbol to leverage mapping, e.g., {"BTCUSDT": 10, "ETHUSDT": 5}.
        Only applies to USDT_FUTURES and COIN_FUTURES account types.
    futures_margin_types : dict[str, str], optional
        Symbol to margin type mapping, e.g., {"BTCUSDT": "CROSS"}.
        Values must be "CROSS" or "ISOLATED".
        Only applies to USDT_FUTURES and COIN_FUTURES account types.

    Returns
    -------
    BinanceExecClientConfig
        NautilusTrader Binance exec client configuration.

    Notes
    -----
    Production settings:
    - use_reduce_only=True enforces ONE-WAY (NETTING) mode for safety
    - use_position_ids=True required for position tracking
    - recv_window_ms=5000 for network latency tolerance
    - max_retries=3 to avoid rate limit bans

    WARNING: HEDGE mode is NOT recommended due to reconciliation bug #3104.
    Use ONE-WAY (NETTING) mode for reliable position management.
    """
    account_type = _BINANCE_ACCOUNT_TYPES[credentials.account_type]

    # Convert futures_leverages to BinanceSymbol keys
    leverages = None
    if futures_leverages:
        from nautilus_trader.adapters.binance.common.symbol import BinanceSymbol

        # Validate leverage values (Binance max is 125x)
        for symbol, lev in futures_leverages.items():
            if lev <= 0:
                raise ValueError(f"Leverage must be positive, got {lev} for {symbol}")
            if lev > 125:
                raise ValueError(f"Leverage {lev} exceeds Binance max of 125x for {symbol}")

        leverages = {BinanceSymbol(symbol): lev for symbol, lev in futures_leverages.items()}

    # Convert futures_margin_types to BinanceSymbol keys with enum values
    margin_types = None
    if futures_margin_types:
        from nautilus_trader.adapters.binance.common.symbol import BinanceSymbol

        margin_types = {
            BinanceSymbol(symbol): _MARGIN_TYPES[margin_type]
            for symbol, margin_type in futures_margin_types.items()
        }

    return BinanceExecClientConfig(
        account_type=account_type,
        testnet=credentials.testnet,
        us=credentials.us,
        use_reduce_only=True,  # Enforce NETTING mode (HEDGE bug #3104)
        use_position_ids=True,
        recv_window_ms=5000,
        max_retries=max_retries,
        retry_delay_initial_ms=retry_delay_initial_ms,
        retry_delay_max_ms=retry_delay_max_ms,
        futures_leverages=leverages,
        futures_margin_types=margin_types,
        listen_key_ping_max_failures=3,
        instrument_provider=InstrumentProviderConfig(load_all=False),
    )
