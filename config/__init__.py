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

Order Helpers (Spec 015)::

    from config import create_market_order, create_limit_order
    from nautilus_trader.model.enums import OrderSide
    from nautilus_trader.model.objects import Quantity, Price

    order = create_market_order(factory, instrument_id, OrderSide.BUY, Quantity.from_str("0.1"))
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
from config.order_helpers import (
    create_external_claims,
    create_limit_order,
    create_market_order,
    create_stop_limit_order,
    create_stop_market_order,
    validate_order_params,
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
    # Order Helpers (Spec 015 FR-002)
    "create_market_order",
    "create_limit_order",
    "create_stop_market_order",
    "create_stop_limit_order",
    "create_external_claims",
    "validate_order_params",
]
