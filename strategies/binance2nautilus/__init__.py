"""Binance to NautilusTrader v1.222.0 Data Ingestion Pipeline.

Converts Binance historical CSV data to NautilusTrader ParquetDataCatalog format.

Quick Start:
    >>> from binance2nautilus import convert_klines, convert_trades
    >>> from binance2nautilus import get_instrument, create_catalog

    # Get instrument
    >>> instrument = get_instrument("BTCUSDT")

    # Convert klines
    >>> bars, count = convert_klines("BTCUSDT", timeframe="1m")

    # Write to catalog
    >>> catalog = create_catalog("/path/to/catalog")
    >>> catalog.write_instrument(instrument)
    >>> catalog.write_bars(bars)

Key Features:
    - V1 Wranglers only (BacktestEngine compatible)
    - 128-bit precision (Linux nightly default)
    - Chunked processing for large trade files
    - Incremental update support
"""

from .catalog import CatalogWriter, create_catalog
from .config import ConverterConfig
from .converters import KlinesConverter, TradesConverter
from .converters.klines import convert_klines
from .converters.trades import convert_trades
from .instruments import (
    create_btcusdt_perp,
    create_ethusdt_perp,
    get_instrument,
    list_supported_symbols,
)
from .state import ConversionState, load_state, save_state
from .validate import ValidationResult, validate_catalog, verify_record_count
from .wrangler_factory import get_bar_wrangler, get_trade_wrangler

__version__ = "0.1.0"

__all__ = [
    # Main functions
    "convert_klines",
    "convert_trades",
    "create_catalog",
    "validate_catalog",
    "verify_record_count",
    # Instruments
    "get_instrument",
    "create_btcusdt_perp",
    "create_ethusdt_perp",
    "list_supported_symbols",
    # Converters
    "KlinesConverter",
    "TradesConverter",
    # Catalog
    "CatalogWriter",
    # Config & State
    "ConverterConfig",
    "ConversionState",
    "load_state",
    "save_state",
    # Wranglers
    "get_bar_wrangler",
    "get_trade_wrangler",
    # Validation
    "ValidationResult",
]
