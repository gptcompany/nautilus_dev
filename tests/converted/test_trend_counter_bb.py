"""
Tests for TrendCounterBB strategy converted from Pine Script.

This validates the /pinescript skill conversion output.
"""

from decimal import Decimal

import pytest
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.test_kit.providers import TestInstrumentProvider

from strategies.converted.trend_counter_bb import (
    Trend,
    TrendCounterBBConfig,
    TrendCounterBBStrategy,
    TrendCounterIndicator,
)


class TestTrendCounterIndicator:
    """Tests for TrendCounterIndicator."""

    def test_initialization(self):
        """Test indicator initializes with correct parameters."""
        indicator = TrendCounterIndicator(length=20, smooth=5)

        assert indicator.length == 20
        assert indicator.smooth == 5
        assert indicator.value == 0.0
        assert indicator.trend == Trend.NEUTRAL
        assert indicator.strength == 0.0
        assert not indicator.initialized

    def test_invalid_length_raises(self):
        """Test that invalid length raises ValueError."""
        with pytest.raises(ValueError, match="length must be >= 2"):
            TrendCounterIndicator(length=1, smooth=5)

    def test_invalid_smooth_raises(self):
        """Test that invalid smooth raises ValueError."""
        with pytest.raises(ValueError, match="smooth must be >= 1"):
            TrendCounterIndicator(length=20, smooth=0)

    def test_name_property(self):
        """Test indicator name property."""
        indicator = TrendCounterIndicator(length=20, smooth=5)
        assert indicator.name == "TrendCounter(20,5)"

    def test_handle_bar_warmup(self):
        """Test indicator requires warmup period."""
        indicator = TrendCounterIndicator(length=20, smooth=5)
        instrument = TestInstrumentProvider.btcusdt_binance()
        bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")

        # Feed fewer bars than required
        for i in range(10):
            bar = Bar(
                bar_type=bar_type,
                open=instrument.make_price(50000 + i * 10),
                high=instrument.make_price(50050 + i * 10),
                low=instrument.make_price(49950 + i * 10),
                close=instrument.make_price(50025 + i * 10),
                volume=instrument.make_qty(100),
                ts_event=i * 60_000_000_000,
                ts_init=i * 60_000_000_000,
            )
            indicator.handle_bar(bar)

        # Should not be initialized yet
        assert not indicator.initialized

    def test_handle_bar_after_warmup(self):
        """Test indicator initializes after warmup period."""
        indicator = TrendCounterIndicator(length=20, smooth=5)
        instrument = TestInstrumentProvider.btcusdt_binance()
        bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")

        # Feed enough bars for warmup (length + smooth)
        for i in range(30):
            bar = Bar(
                bar_type=bar_type,
                open=instrument.make_price(50000 + i * 10),
                high=instrument.make_price(50050 + i * 10),
                low=instrument.make_price(49950 + i * 10),
                close=instrument.make_price(50025 + i * 10),
                volume=instrument.make_qty(100),
                ts_event=i * 60_000_000_000,
                ts_init=i * 60_000_000_000,
            )
            indicator.handle_bar(bar)

        # Should be initialized
        assert indicator.initialized
        assert indicator.value >= 0
        assert indicator.trend in list(Trend)
        assert 0 <= indicator.strength <= 1

    def test_uptrend_detection(self):
        """Test indicator detects uptrend correctly."""
        indicator = TrendCounterIndicator(length=10, smooth=3)
        instrument = TestInstrumentProvider.btcusdt_binance()
        bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")

        # Create strongly rising price series
        for i in range(20):
            base_price = 50000 + i * 100  # Strong uptrend
            bar = Bar(
                bar_type=bar_type,
                open=instrument.make_price(base_price),
                high=instrument.make_price(base_price + 50),
                low=instrument.make_price(base_price - 20),
                close=instrument.make_price(base_price + 40),
                volume=instrument.make_qty(100),
                ts_event=i * 60_000_000_000,
                ts_init=i * 60_000_000_000,
            )
            indicator.handle_bar(bar)

        assert indicator.initialized
        assert indicator.trend in (Trend.UP, Trend.STRONG_UP)

    def test_reset(self):
        """Test indicator reset clears state."""
        indicator = TrendCounterIndicator(length=10, smooth=3)
        instrument = TestInstrumentProvider.btcusdt_binance()
        bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")

        # Initialize indicator
        for i in range(15):
            bar = Bar(
                bar_type=bar_type,
                open=instrument.make_price(50000),
                high=instrument.make_price(50100),
                low=instrument.make_price(49900),
                close=instrument.make_price(50050),
                volume=instrument.make_qty(100),
                ts_event=i * 60_000_000_000,
                ts_init=i * 60_000_000_000,
            )
            indicator.handle_bar(bar)

        assert indicator.initialized

        # Reset
        indicator.reset()

        assert not indicator.initialized
        assert indicator.value == 0.0
        assert indicator.trend == Trend.NEUTRAL


class TestTrendCounterBBConfig:
    """Tests for TrendCounterBBConfig."""

    def test_config_creation(self):
        """Test configuration creation with valid parameters."""
        config = TrendCounterBBConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            trade_size=Decimal("0.1"),
            length=20,
            smooth=5,
            entry_strength=0.7,
        )

        assert config.instrument_id == "BTCUSDT-PERP.BINANCE"
        assert config.length == 20
        assert config.smooth == 5
        assert config.entry_strength == 0.7

    def test_config_defaults(self):
        """Test configuration default values."""
        config = TrendCounterBBConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
        )

        assert config.trade_size == Decimal("0.1")
        assert config.length == 20
        assert config.smooth == 5
        assert config.entry_strength == 0.7


class TestTrendCounterBBStrategy:
    """Tests for TrendCounterBBStrategy."""

    def test_strategy_creation(self):
        """Test strategy creation with valid config."""
        config = TrendCounterBBConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            trade_size=Decimal("0.1"),
            length=20,
            smooth=5,
        )

        strategy = TrendCounterBBStrategy(config)

        assert strategy.instrument_id == InstrumentId.from_str("BTCUSDT-PERP.BINANCE")
        assert strategy.trend_counter.length == 20
        assert strategy.trend_counter.smooth == 5

    def test_indicator_initialized(self):
        """Test strategy has trend counter indicator."""
        config = TrendCounterBBConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
        )

        strategy = TrendCounterBBStrategy(config)

        assert isinstance(strategy.trend_counter, TrendCounterIndicator)
        assert not strategy.trend_counter.initialized
