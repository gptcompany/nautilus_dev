"""Converters for Binance CSV data to NautilusTrader format.

This module provides converters for:
- Klines (OHLCV candlesticks) -> Bar objects
- Trades (individual executions) -> TradeTick objects
- Funding rates -> Custom data type
"""

from .base import BaseConverter
from .klines import KlinesConverter
from .trades import TradesConverter

__all__ = [
    "BaseConverter",
    "KlinesConverter",
    "TradesConverter",
]
