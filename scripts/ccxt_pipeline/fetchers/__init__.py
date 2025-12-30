"""Exchange fetchers for CCXT pipeline."""

from scripts.ccxt_pipeline.fetchers.base import BaseFetcher
from scripts.ccxt_pipeline.fetchers.binance import BinanceFetcher
from scripts.ccxt_pipeline.fetchers.bybit import BybitFetcher
from scripts.ccxt_pipeline.fetchers.hyperliquid import HyperliquidFetcher
from scripts.ccxt_pipeline.fetchers.orchestrator import FetchOrchestrator, FetchResult

__all__ = [
    "BaseFetcher",
    "BinanceFetcher",
    "BybitFetcher",
    "HyperliquidFetcher",
    "FetchOrchestrator",
    "FetchResult",
    "get_fetcher",
    "get_all_fetchers",
]


def get_fetcher(
    exchange: str,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> BaseFetcher:
    """Factory function to create a fetcher for a specific exchange.

    Args:
        exchange: Exchange name (binance, bybit, hyperliquid).
        api_key: Optional API key.
        api_secret: Optional API secret.

    Returns:
        A fetcher instance for the specified exchange.

    Raises:
        ValueError: If exchange is not supported.
    """
    exchange_lower = exchange.lower()

    if exchange_lower == "binance":
        return BinanceFetcher(api_key=api_key, api_secret=api_secret)
    elif exchange_lower == "bybit":
        return BybitFetcher(api_key=api_key, api_secret=api_secret)
    elif exchange_lower == "hyperliquid":
        return HyperliquidFetcher(api_key=api_key, api_secret=api_secret)
    else:
        raise ValueError(
            f"Unsupported exchange: {exchange}. Supported: binance, bybit, hyperliquid"
        )


def get_all_fetchers(
    exchanges: list[str] | None = None,
) -> list[BaseFetcher]:
    """Create fetchers for all or specified exchanges.

    Args:
        exchanges: Optional list of exchanges. If None, creates all.

    Returns:
        List of fetcher instances.
    """
    if exchanges is None:
        exchanges = ["binance", "bybit", "hyperliquid"]

    return [get_fetcher(ex) for ex in exchanges]
