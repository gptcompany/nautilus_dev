"""
Tests for LiquidationHeatMap strategy.

Converted from: Liquidation HeatMap [BigBeluga]
"""

import pytest
from decimal import Decimal

from nautilus_trader.model.identifiers import InstrumentId

from strategies.converted.liquidation_heatmap import (
    LiquidationZone,
    LiquidationZoneIndicator,
    LiquidationHeatMapConfig,
    LiquidationHeatMapStrategy,
)


class TestLiquidationZone:
    """Tests for LiquidationZone dataclass."""

    def test_zone_creation(self):
        """Test zone can be created with valid parameters."""
        zone = LiquidationZone(
            start_bar_idx=100,
            top=50000.0,
            bottom=49500.0,
            volume_intensity=0.75,
            is_above_price=True,
        )
        assert zone.top == 50000.0
        assert zone.bottom == 49500.0
        assert zone.volume_intensity == 0.75
        assert zone.is_above_price is True
        assert zone.consumed is False

    def test_zone_midpoint(self):
        """Test zone midpoint calculation."""
        zone = LiquidationZone(
            start_bar_idx=0,
            top=50000.0,
            bottom=49000.0,
            volume_intensity=0.5,
            is_above_price=True,
        )
        assert zone.midpoint == 49500.0

    def test_zone_price_through(self):
        """Test price through detection."""
        zone = LiquidationZone(
            start_bar_idx=0,
            top=50000.0,
            bottom=49000.0,
            volume_intensity=0.5,
            is_above_price=True,
        )
        # Midpoint is 49500

        # Price bar crosses through midpoint
        assert zone.is_price_through(high=50000.0, low=49000.0) is True

        # Price bar doesn't cross midpoint
        assert zone.is_price_through(high=50000.0, low=49600.0) is False
        assert zone.is_price_through(high=49400.0, low=49000.0) is False


class TestLiquidationZoneIndicator:
    """Tests for LiquidationZoneIndicator."""

    def test_indicator_creation(self):
        """Test indicator can be created with default parameters."""
        indicator = LiquidationZoneIndicator()
        assert indicator.atr_period == 200
        assert indicator.pivot_lookback == 2
        assert indicator.max_zones == 500
        assert indicator.initialized is False

    def test_indicator_custom_params(self):
        """Test indicator with custom parameters."""
        indicator = LiquidationZoneIndicator(
            atr_period=100,
            pivot_lookback=3,
            max_zones=250,
            atr_multiplier=0.3,
        )
        assert indicator.atr_period == 100
        assert indicator.pivot_lookback == 3
        assert indicator.max_zones == 250
        assert indicator.atr_multiplier == 0.3

    def test_indicator_name(self):
        """Test indicator name property."""
        indicator = LiquidationZoneIndicator(atr_period=100, pivot_lookback=3)
        assert indicator.name == "LiquidationZone(100,3)"

    def test_indicator_reset(self):
        """Test indicator reset clears state."""
        indicator = LiquidationZoneIndicator()

        # Simulate some state
        indicator._bar_count = 100

        indicator.reset()

        assert indicator._bar_count == 0
        assert len(indicator._zones) == 0
        assert len(indicator._bar_history) == 0


class TestLiquidationHeatMapConfig:
    """Tests for LiquidationHeatMapConfig."""

    def test_config_creation(self):
        """Test config can be created with required parameters."""
        config = LiquidationHeatMapConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
        )
        assert config.instrument_id == "BTCUSDT-PERP.BINANCE"
        assert config.atr_period == 200
        assert config.pivot_lookback == 2

    def test_config_custom_params(self):
        """Test config with custom trading parameters."""
        config = LiquidationHeatMapConfig(
            instrument_id="ETHUSDT-PERP.BINANCE",
            bar_type="ETHUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL",
            trade_size=Decimal("0.1"),
            max_position_size=Decimal("1.0"),
            min_volume_intensity=0.7,
        )
        assert config.trade_size == Decimal("0.1")
        assert config.max_position_size == Decimal("1.0")
        assert config.min_volume_intensity == 0.7


class TestLiquidationHeatMapStrategy:
    """Tests for LiquidationHeatMapStrategy."""

    @pytest.fixture
    def config(self) -> LiquidationHeatMapConfig:
        """Create test config."""
        return LiquidationHeatMapConfig(
            strategy_id="TEST-LIQ-001",
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            trade_size=Decimal("0.001"),
            max_position_size=Decimal("0.01"),
        )

    def test_strategy_creation(self, config):
        """Test strategy can be created."""
        strategy = LiquidationHeatMapStrategy(config)

        assert strategy.instrument_id == InstrumentId.from_str("BTCUSDT-PERP.BINANCE")
        assert strategy.trade_size == Decimal("0.001")
        assert strategy.liq_indicator is not None
        assert strategy.liq_indicator.initialized is False

    def test_strategy_indicator_params(self, config):
        """Test strategy passes config to indicator."""
        config_custom = LiquidationHeatMapConfig(
            strategy_id="TEST-LIQ-002",
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            atr_period=100,
            pivot_lookback=3,
        )
        strategy = LiquidationHeatMapStrategy(config_custom)

        assert strategy.liq_indicator.atr_period == 100
        assert strategy.liq_indicator.pivot_lookback == 3


# Integration tests would require BacktestNode setup
# See: tests/integration/test_liquidation_heatmap_backtest.py
