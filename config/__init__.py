"""
TradingNode Configuration Package.

Production-ready configuration system for NautilusTrader live trading.

Example Usage::

    from config import TradingNodeConfigFactory

    # Create testnet configuration from environment
    config = TradingNodeConfigFactory.create_testnet(strategies=[my_strategy])

    # Or create production configuration
    config = TradingNodeConfigFactory.create_production(strategies=[my_strategy])

    # Or build from custom settings
    from config import TradingNodeSettings
    settings = TradingNodeSettings.from_env()
    config = TradingNodeConfigFactory.from_settings(settings)
"""

from __future__ import annotations

from config.factory import TradingNodeConfigFactory
from config.models import (
    BinanceCredentials,
    BybitCredentials,
    ConfigEnvironment,
    ExchangeCredentials,
    LoggingSettings,
    RedisConfig,
    StreamingSettings,
    TradingNodeSettings,
)

__all__ = [
    # Factory
    "TradingNodeConfigFactory",
    # Settings
    "TradingNodeSettings",
    "ConfigEnvironment",
    "RedisConfig",
    "LoggingSettings",
    "StreamingSettings",
    # Credentials
    "ExchangeCredentials",
    "BinanceCredentials",
    "BybitCredentials",
]
