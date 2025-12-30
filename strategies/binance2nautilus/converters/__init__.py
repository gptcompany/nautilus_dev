"""Converters for Binance CSV data to NautilusTrader format.

This module provides converters for:
- Klines (OHLCV candlesticks) -> Bar objects
- Trades (individual executions) -> TradeTick objects
- Funding rates -> FundingRateUpdate (native NautilusTrader type)
"""

from .base import BaseConverter
from .funding import FundingRateConverter
from .klines import KlinesConverter
from .trades import TradesConverter

__all__ = [
    "BaseConverter",
    "FundingRateConverter",
    "KlinesConverter",
    "TradesConverter",
]
