"""Configuration for Binance to NautilusTrader data conversion.

Defines paths, symbols, and processing settings for the conversion pipeline.
"""

from pathlib import Path
from pydantic import BaseModel, Field


class ConverterConfig(BaseModel):
    """Configuration for Binance to NautilusTrader converter."""

    # Source and output directories
    source_dir: Path = Field(
        default=Path("/media/sam/3TB-WDC/binance-history-data-downloader/data"),
        description="Directory containing Binance CSV data",
    )
    output_dir: Path = Field(
        default=Path("/media/sam/2TB-NVMe/nautilus_catalog_v1222"),
        description="Output ParquetDataCatalog path",
    )

    # Symbols to process
    symbols: list[str] = Field(
        default=["BTCUSDT", "ETHUSDT"],
        description="Trading symbols to convert",
    )

    # Timeframes for klines
    timeframes: list[str] = Field(
        default=["1m", "5m", "15m"],
        description="Kline timeframes to process",
    )

    # Processing settings
    chunk_size: int = Field(
        default=100_000,
        description="Rows per processing chunk for memory efficiency",
    )

    # NautilusTrader environment
    nautilus_env: Path = Field(
        default=Path("/media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env"),
        description="Path to NautilusTrader virtual environment",
    )

    # Wrangler selection (V2-ready architecture)
    use_rust_wranglers: bool = Field(
        default=False,
        description="Use V2 Rust wranglers (when BacktestEngine supports PyO3)",
    )

    model_config = {"extra": "forbid"}

    def get_symbol_source_path(self, symbol: str) -> Path:
        """Get the source data path for a symbol."""
        return self.source_dir / symbol

    def get_klines_path(self, symbol: str, timeframe: str) -> Path:
        """Get the klines CSV directory for a symbol and timeframe."""
        return self.source_dir / symbol / "klines" / timeframe

    def get_trades_path(self, symbol: str) -> Path:
        """Get the trades CSV directory for a symbol."""
        return self.source_dir / symbol / "trades"

    def get_funding_path(self, symbol: str) -> Path:
        """Get the funding rate CSV directory for a symbol."""
        return self.source_dir / symbol / "fundingRate"
