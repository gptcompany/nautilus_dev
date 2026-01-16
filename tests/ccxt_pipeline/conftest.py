"""Test fixtures for CCXT pipeline tests."""

# Python 3.10 compatibility
import datetime as _dt
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.ccxt_pipeline.config import CCXTPipelineConfig
from scripts.ccxt_pipeline.models import FundingRate, Liquidation, OpenInterest, Side, Venue
from scripts.ccxt_pipeline.storage.parquet_store import ParquetStore


@pytest.fixture
def sample_open_interest() -> OpenInterest:
    """Create a sample OpenInterest record."""
    return OpenInterest(
        timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
        symbol="BTCUSDT-PERP",
        venue=Venue.BINANCE,
        open_interest=125432.50,
        open_interest_value=12543250000.0,
    )


@pytest.fixture
def sample_funding_rate() -> FundingRate:
    """Create a sample FundingRate record."""
    return FundingRate(
        timestamp=datetime(2025, 1, 15, 8, 0, 0, tzinfo=UTC),
        symbol="BTCUSDT-PERP",
        venue=Venue.BINANCE,
        funding_rate=0.0001,
        next_funding_time=datetime(2025, 1, 15, 16, 0, 0, tzinfo=UTC),
        predicted_rate=0.00012,
    )


@pytest.fixture
def sample_liquidation() -> Liquidation:
    """Create a sample Liquidation record."""
    return Liquidation(
        timestamp=datetime(2025, 1, 15, 12, 34, 56, tzinfo=UTC),
        symbol="BTCUSDT-PERP",
        venue=Venue.BINANCE,
        side=Side.LONG,
        quantity=1.25,
        price=99500.0,
        value=124375.0,
    )


@pytest.fixture
def temp_catalog_path() -> Path:
    """Create a temporary catalog directory."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def parquet_store(temp_catalog_path: Path) -> ParquetStore:
    """Create a ParquetStore with a temporary catalog."""
    return ParquetStore(temp_catalog_path)


@pytest.fixture
def test_config(temp_catalog_path: Path) -> CCXTPipelineConfig:
    """Create a test configuration."""
    return CCXTPipelineConfig(catalog_path=temp_catalog_path)


@pytest.fixture
def multiple_open_interests() -> list[OpenInterest]:
    """Create multiple OpenInterest records for different exchanges."""
    return [
        OpenInterest(
            timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
            symbol="BTCUSDT-PERP",
            venue=Venue.BINANCE,
            open_interest=125432.50,
            open_interest_value=12543250000.0,
        ),
        OpenInterest(
            timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
            symbol="BTCUSDT-PERP",
            venue=Venue.BYBIT,
            open_interest=85123.25,
            open_interest_value=8512325000.0,
        ),
        OpenInterest(
            timestamp=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
            symbol="BTC-USD-PERP",
            venue=Venue.HYPERLIQUID,
            open_interest=42567.10,
            open_interest_value=4256710000.0,
        ),
    ]
