"""
Test fixtures for configuration testing (T010).

Provides reusable fixtures for testing TradingNode configuration models and factory.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path for imports (required before importing config module)
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import os  # noqa: E402

import pytest  # noqa: E402

from config.models import (  # noqa: E402
    BinanceCredentials,
    BybitCredentials,
    ConfigEnvironment,
    LoggingSettings,
    RedisConfig,
    StreamingSettings,
    TradingNodeSettings,
)


@pytest.fixture
def valid_trader_id() -> str:
    """Valid trader ID."""
    return "PROD-TRADER-001"


@pytest.fixture
def valid_config_environment(valid_trader_id: str) -> ConfigEnvironment:
    """Valid ConfigEnvironment instance."""
    return ConfigEnvironment(
        trader_id=valid_trader_id,
        environment="SANDBOX",
    )


@pytest.fixture
def valid_redis_config() -> RedisConfig:
    """Valid RedisConfig instance with defaults."""
    return RedisConfig()


@pytest.fixture
def valid_logging_settings() -> LoggingSettings:
    """Valid LoggingSettings instance with defaults."""
    return LoggingSettings()


@pytest.fixture
def valid_streaming_settings() -> StreamingSettings:
    """Valid StreamingSettings instance with defaults."""
    return StreamingSettings()


@pytest.fixture
def valid_binance_credentials() -> BinanceCredentials:
    """Valid BinanceCredentials for testing."""
    return BinanceCredentials(
        api_key="test_api_key_1234567890123456",
        api_secret="test_api_secret_1234567890123456",
        testnet=True,
        account_type="USDT_FUTURES",
        us=False,
    )


@pytest.fixture
def valid_bybit_credentials() -> BybitCredentials:
    """Valid BybitCredentials for testing."""
    return BybitCredentials(
        api_key="test_api_key_1234567890123456",
        api_secret="test_api_secret_1234567890123456",
        testnet=True,
        product_types=["LINEAR"],
        demo=False,
    )


@pytest.fixture
def valid_trading_node_settings(
    valid_config_environment: ConfigEnvironment,
    valid_binance_credentials: BinanceCredentials,
) -> TradingNodeSettings:
    """Valid TradingNodeSettings instance with Binance only."""
    return TradingNodeSettings(
        environment=valid_config_environment,
        binance=valid_binance_credentials,
    )


@pytest.fixture
def valid_trading_node_settings_both_exchanges(
    valid_config_environment: ConfigEnvironment,
    valid_binance_credentials: BinanceCredentials,
    valid_bybit_credentials: BybitCredentials,
) -> TradingNodeSettings:
    """Valid TradingNodeSettings instance with both exchanges."""
    return TradingNodeSettings(
        environment=valid_config_environment,
        binance=valid_binance_credentials,
        bybit=valid_bybit_credentials,
    )


@pytest.fixture
def mock_env_vars() -> dict[str, str]:
    """Complete set of environment variables for testing."""
    return {
        "NAUTILUS_TRADER_ID": "TEST-TRADER-001",
        "NAUTILUS_ENVIRONMENT": "SANDBOX",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_PASSWORD": "",
        "REDIS_TIMEOUT": "2.0",
        "NAUTILUS_LOG_LEVEL": "INFO",
        "NAUTILUS_LOG_LEVEL_FILE": "DEBUG",
        "NAUTILUS_LOG_DIRECTORY": "/tmp/nautilus_test",
        "NAUTILUS_LOG_FORMAT": "json",
        "NAUTILUS_CATALOG_PATH": "/tmp/nautilus_test/catalog",
        "NAUTILUS_FLUSH_INTERVAL_MS": "2000",
        "BINANCE_API_KEY": "test_binance_api_key_1234",
        "BINANCE_API_SECRET": "test_binance_api_secret_1234",
        "BINANCE_TESTNET": "true",
        "BINANCE_ACCOUNT_TYPE": "USDT_FUTURES",
        "BINANCE_US": "false",
    }


@pytest.fixture
def mock_env_vars_bybit_only() -> dict[str, str]:
    """Environment variables with only Bybit configured."""
    return {
        "NAUTILUS_TRADER_ID": "TEST-TRADER-001",
        "NAUTILUS_ENVIRONMENT": "SANDBOX",
        "BYBIT_API_KEY": "test_bybit_api_key_12345",
        "BYBIT_API_SECRET": "test_bybit_api_secret_12345",
        "BYBIT_TESTNET": "true",
        "BYBIT_DEMO": "false",
    }


@pytest.fixture
def set_env_vars(mock_env_vars: dict[str, str]):
    """Context manager to set environment variables."""
    original = os.environ.copy()
    os.environ.update(mock_env_vars)
    yield mock_env_vars
    os.environ.clear()
    os.environ.update(original)


@pytest.fixture
def clean_env():
    """Context manager to ensure clean environment."""
    original = os.environ.copy()
    # Remove any nautilus/exchange env vars
    keys_to_remove = [
        k
        for k in os.environ
        if k.startswith(("NAUTILUS_", "REDIS_", "BINANCE_", "BYBIT_"))
    ]
    for key in keys_to_remove:
        del os.environ[key]
    yield
    os.environ.clear()
    os.environ.update(original)
