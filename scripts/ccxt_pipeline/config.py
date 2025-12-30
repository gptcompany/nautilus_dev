"""Configuration for CCXT pipeline."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class CCXTPipelineConfig(BaseSettings):
    """Configuration for the CCXT data pipeline.

    Settings can be overridden via environment variables with CCXT_ prefix.
    """

    # Storage
    catalog_path: Path = Field(
        default=Path("/media/sam/1TB/nautilus_dev/data/ccxt_catalog"),
        description="Path to the data catalog directory",
    )

    # Exchanges
    exchanges: list[str] = Field(
        default=["binance", "bybit", "hyperliquid"],
        description="List of exchanges to fetch from",
    )

    # Symbols
    symbols: list[str] = Field(
        default=["BTCUSDT-PERP", "ETHUSDT-PERP"],
        description="Default symbols to fetch",
    )

    # Scheduler intervals
    oi_fetch_interval_seconds: int = Field(
        default=300, description="OI fetch interval (default 5 minutes)"
    )
    funding_fetch_interval_seconds: int = Field(
        default=3600, description="Funding fetch interval (default 1 hour)"
    )

    # Rate limiting
    max_concurrent_requests: int = Field(default=5, description="Max concurrent API requests")

    # API Keys (optional for public data)
    binance_api_key: str | None = Field(default=None, description="Binance API key")
    binance_api_secret: str | None = Field(default=None, description="Binance API secret")
    bybit_api_key: str | None = Field(default=None, description="Bybit API key")
    bybit_api_secret: str | None = Field(default=None, description="Bybit API secret")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    model_config = {
        "env_prefix": "CCXT_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


def get_config() -> CCXTPipelineConfig:
    """Get the pipeline configuration."""
    return CCXTPipelineConfig()
