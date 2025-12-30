"""
TradingNode Configuration Models

Pydantic models for loading and validating TradingNode configuration
from environment variables.
"""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ConfigEnvironment(BaseModel):
    """Core environment configuration."""

    trader_id: str = Field(
        ...,
        pattern=r"^[A-Z0-9-]+$",
        description="Unique trader identifier (e.g., PROD-TRADER-001)",
    )
    environment: Literal["LIVE", "SANDBOX"] = Field(
        default="SANDBOX",
        description="Trading environment",
    )

    @field_validator("trader_id")
    @classmethod
    def validate_trader_id(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 32:
            raise ValueError("trader_id must be 3-32 characters")
        return v


class RedisConfig(BaseModel):
    """Redis connection configuration."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    password: str | None = Field(default=None, description="Redis password")
    timeout: float = Field(
        default=2.0, ge=0.1, le=30.0, description="Connection timeout"
    )


class LoggingSettings(BaseModel):
    """Logging configuration."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Console log level",
    )
    log_level_file: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="DEBUG",
        description="File log level",
    )
    log_directory: str = Field(
        default="/var/log/nautilus",
        description="Log file directory",
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log file format",
    )
    max_size_mb: int = Field(
        default=100, ge=10, le=1000, description="Max log file size"
    )
    max_backup_count: int = Field(
        default=10, ge=1, le=100, description="Max backup files"
    )


class StreamingSettings(BaseModel):
    """Streaming/catalog configuration."""

    catalog_path: str = Field(
        default="/data/nautilus/catalog",
        description="Path to data catalog",
    )
    flush_interval_ms: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Flush interval in milliseconds",
    )
    rotation_mode: Literal["NONE", "SIZE", "TIME"] = Field(
        default="SIZE",
        description="File rotation mode",
    )
    max_file_size_mb: int = Field(
        default=128,
        ge=16,
        le=1024,
        description="Max file size before rotation",
    )


class ExchangeCredentials(BaseModel):
    """Base exchange credentials."""

    api_key: str = Field(..., min_length=16, description="API key")
    api_secret: str = Field(..., min_length=16, description="API secret")
    testnet: bool = Field(default=False, description="Use testnet")

    @field_validator("api_key", "api_secret")
    @classmethod
    def validate_not_placeholder(cls, v: str) -> str:
        if v.startswith("xxx") or v == "your_api_key":
            raise ValueError("Placeholder credentials not allowed")
        return v


class BinanceCredentials(ExchangeCredentials):
    """Binance-specific credentials."""

    account_type: Literal["SPOT", "USDT_FUTURES", "COIN_FUTURES"] = Field(
        default="USDT_FUTURES",
        description="Binance account type",
    )
    us: bool = Field(default=False, description="Use Binance.US endpoints")


class BybitCredentials(ExchangeCredentials):
    """Bybit-specific credentials."""

    product_types: list[Literal["LINEAR", "INVERSE", "SPOT", "OPTION"]] = Field(
        default=["LINEAR"],
        description="Bybit product types",
    )
    demo: bool = Field(default=False, description="Use demo mode")

    @field_validator("product_types")
    @classmethod
    def validate_product_types(cls, v: list) -> list:
        if "SPOT" in v and len(v) > 1:
            raise ValueError("SPOT cannot be mixed with derivatives")
        return v


class TradingNodeSettings(BaseModel):
    """Complete TradingNode settings."""

    # Core
    environment: ConfigEnvironment

    # Infrastructure
    redis: RedisConfig = Field(default_factory=RedisConfig)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    streaming: StreamingSettings = Field(default_factory=StreamingSettings)

    # Exchange credentials (at least one required)
    binance: BinanceCredentials | None = None
    bybit: BybitCredentials | None = None

    # Execution settings
    reconciliation_lookback_mins: int = Field(default=60, ge=60, le=1440)
    reconciliation_startup_delay_secs: float = Field(default=10.0, ge=10.0, le=60.0)

    # Rate limits
    max_order_submit_rate: str = Field(default="100/00:00:01")
    max_order_modify_rate: str = Field(default="100/00:00:01")

    @model_validator(mode="after")
    def validate_at_least_one_exchange(self) -> "TradingNodeSettings":
        if self.binance is None and self.bybit is None:
            raise ValueError("At least one exchange must be configured")
        return self

    @classmethod
    def from_env(cls) -> "TradingNodeSettings":
        """Load settings from environment variables."""
        # Core environment
        environment = ConfigEnvironment(
            trader_id=os.environ["NAUTILUS_TRADER_ID"],
            environment=os.environ.get("NAUTILUS_ENVIRONMENT", "SANDBOX"),  # type: ignore
        )

        # Redis
        redis = RedisConfig(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            password=os.environ.get("REDIS_PASSWORD") or None,
            timeout=float(os.environ.get("REDIS_TIMEOUT", "2.0")),
        )

        # Logging
        logging = LoggingSettings(
            log_level=os.environ.get("NAUTILUS_LOG_LEVEL", "INFO"),  # type: ignore
            log_level_file=os.environ.get("NAUTILUS_LOG_LEVEL_FILE", "DEBUG"),  # type: ignore
            log_directory=os.environ.get("NAUTILUS_LOG_DIRECTORY", "/var/log/nautilus"),
            log_format=os.environ.get("NAUTILUS_LOG_FORMAT", "json"),  # type: ignore
        )

        # Streaming
        streaming = StreamingSettings(
            catalog_path=os.environ.get(
                "NAUTILUS_CATALOG_PATH", "/data/nautilus/catalog"
            ),
            flush_interval_ms=int(os.environ.get("NAUTILUS_FLUSH_INTERVAL_MS", "2000")),
        )

        # Binance credentials (optional)
        binance = None
        if "BINANCE_API_KEY" in os.environ:
            binance = BinanceCredentials(
                api_key=os.environ["BINANCE_API_KEY"],
                api_secret=os.environ["BINANCE_API_SECRET"],
                testnet=os.environ.get("BINANCE_TESTNET", "false").lower() == "true",
                account_type=os.environ.get("BINANCE_ACCOUNT_TYPE", "USDT_FUTURES"),  # type: ignore
                us=os.environ.get("BINANCE_US", "false").lower() == "true",
            )

        # Bybit credentials (optional)
        bybit = None
        if "BYBIT_API_KEY" in os.environ:
            bybit = BybitCredentials(
                api_key=os.environ["BYBIT_API_KEY"],
                api_secret=os.environ["BYBIT_API_SECRET"],
                testnet=os.environ.get("BYBIT_TESTNET", "false").lower() == "true",
                demo=os.environ.get("BYBIT_DEMO", "false").lower() == "true",
            )

        return cls(
            environment=environment,
            redis=redis,
            logging=logging,
            streaming=streaming,
            binance=binance,
            bybit=bybit,
        )
