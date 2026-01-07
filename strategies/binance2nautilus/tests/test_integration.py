"""Integration tests for BacktestEngine compatibility.

Verifies that converted data works with NautilusTrader v1.222.0 BacktestEngine.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.model.data import BarType
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from strategies.binance2nautilus import (
    CatalogWriter,
    ConverterConfig,
    get_instrument,
    validate_catalog,
)
from strategies.binance2nautilus.wrangler_factory import get_bar_wrangler


@pytest.fixture
def btcusdt_instrument():
    """Create BTCUSDT perpetual instrument."""
    return get_instrument("BTCUSDT")


@pytest.fixture
def sample_bar_df():
    """Create sample bar DataFrame in wrangler format."""
    timestamps = pd.date_range(
        start="2024-01-01",
        periods=100,
        freq="1min",
        tz="UTC",
    )
    return pd.DataFrame(
        {
            "open": [90000.0 + i * 10 for i in range(100)],
            "high": [90050.0 + i * 10 for i in range(100)],
            "low": [89950.0 + i * 10 for i in range(100)],
            "close": [90025.0 + i * 10 for i in range(100)],
            "volume": [100.0 + i for i in range(100)],
        },
        index=timestamps,
    )


@pytest.fixture
def temp_catalog_dir():
    """Create a temporary directory for catalog."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestBacktestEngineCompatibility:
    """Tests for BacktestEngine compatibility with converted data."""

    def test_v1_wrangler_produces_compatible_bars(
        self,
        btcusdt_instrument,
        sample_bar_df,
    ):
        """V1 wrangler should produce Cython Bar objects compatible with BacktestEngine."""
        config = ConverterConfig(use_rust_wranglers=False)
        bar_type = BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL")

        wrangler = get_bar_wrangler(
            bar_type=bar_type,
            instrument=btcusdt_instrument,
            config=config,
        )
        bars = wrangler.process(sample_bar_df)

        assert len(bars) == 100
        assert bars[0].bar_type == bar_type

        # Verify BacktestEngine compatibility
        # v1.222.0 requires venue before instrument
        from nautilus_trader.backtest.models import FillModel
        from nautilus_trader.model.currencies import USDT
        from nautilus_trader.model.enums import AccountType, OmsType
        from nautilus_trader.model.objects import Money

        engine_config = BacktestEngineConfig(trader_id="TEST-001")
        engine = BacktestEngine(config=engine_config)
        engine.add_venue(
            venue=btcusdt_instrument.id.venue,
            oms_type=OmsType.HEDGING,
            account_type=AccountType.MARGIN,
            base_currency=None,
            starting_balances=[Money(1_000_000, USDT)],
            fill_model=FillModel(),
        )
        engine.add_instrument(btcusdt_instrument)
        engine.add_data(bars)  # Should not raise

    def test_v2_wrangler_raises_not_implemented(self, btcusdt_instrument):
        """V2 wrangler should raise NotImplementedError (not yet supported)."""
        config = ConverterConfig(use_rust_wranglers=True)
        bar_type = BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL")

        with pytest.raises(NotImplementedError, match="not yet compatible"):
            get_bar_wrangler(
                bar_type=bar_type,
                instrument=btcusdt_instrument,
                config=config,
            )

    def test_catalog_write_and_read(
        self,
        btcusdt_instrument,
        sample_bar_df,
        temp_catalog_dir,
    ):
        """Catalog should correctly write and read bars."""
        config = ConverterConfig(use_rust_wranglers=False)
        bar_type = BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL")

        # Wrangle bars
        wrangler = get_bar_wrangler(
            bar_type=bar_type,
            instrument=btcusdt_instrument,
            config=config,
        )
        bars = wrangler.process(sample_bar_df)

        # Write to catalog
        writer = CatalogWriter(temp_catalog_dir)
        writer.write_instrument(btcusdt_instrument)
        writer.write_bars(bars)

        # Read from catalog
        catalog = ParquetDataCatalog(str(temp_catalog_dir))
        instruments = catalog.instruments()
        loaded_bars = catalog.bars()

        assert len(instruments) == 1
        assert str(instruments[0].id) == "BTCUSDT-PERP.BINANCE"
        assert len(loaded_bars) == 100

    def test_catalog_validation(
        self,
        btcusdt_instrument,
        sample_bar_df,
        temp_catalog_dir,
    ):
        """Catalog validation should pass for correctly written data."""
        config = ConverterConfig(use_rust_wranglers=False)
        bar_type = BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL")

        # Wrangle and write
        wrangler = get_bar_wrangler(
            bar_type=bar_type,
            instrument=btcusdt_instrument,
            config=config,
        )
        bars = wrangler.process(sample_bar_df)

        writer = CatalogWriter(temp_catalog_dir)
        writer.write_instrument(btcusdt_instrument)
        writer.write_bars(bars)

        # Validate
        result = validate_catalog(temp_catalog_dir, run_backtest_test=True)

        assert result.is_valid
        assert "BTCUSDT-PERP.BINANCE" in result.instruments
        assert result.backtest_compatible is True
        assert len(result.errors) == 0

    def test_timestamp_precision_nanoseconds(
        self,
        btcusdt_instrument,
        sample_bar_df,
    ):
        """Timestamps should be in nanoseconds."""
        config = ConverterConfig(use_rust_wranglers=False)
        bar_type = BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL")

        wrangler = get_bar_wrangler(
            bar_type=bar_type,
            instrument=btcusdt_instrument,
            config=config,
        )
        bars = wrangler.process(sample_bar_df)

        # ts_event should be in nanoseconds (> 1e18 for 2024)
        assert bars[0].ts_event > 1_700_000_000_000_000_000
        assert bars[0].ts_init > 1_700_000_000_000_000_000


class TestInstruments:
    """Tests for instrument definitions."""

    def test_btcusdt_instrument_creation(self):
        """BTCUSDT instrument should have correct properties."""
        instrument = get_instrument("BTCUSDT")

        assert str(instrument.id) == "BTCUSDT-PERP.BINANCE"
        assert str(instrument.raw_symbol) == "BTCUSDT"
        assert instrument.price_precision == 2
        assert instrument.size_precision == 3
        assert instrument.is_inverse is False

    def test_ethusdt_instrument_creation(self):
        """ETHUSDT instrument should have correct properties."""
        instrument = get_instrument("ETHUSDT")

        assert str(instrument.id) == "ETHUSDT-PERP.BINANCE"
        assert str(instrument.raw_symbol) == "ETHUSDT"
        assert instrument.price_precision == 2
        assert instrument.size_precision == 3

    def test_unsupported_symbol_raises(self):
        """Unsupported symbol should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported symbol"):
            get_instrument("INVALID")
