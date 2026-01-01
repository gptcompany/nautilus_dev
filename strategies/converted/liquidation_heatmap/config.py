"""Configuration presets for LiquidationHeatMap strategy."""

from decimal import Decimal

from .liquidation_heatmap_strategy import LiquidationHeatMapConfig


def create_btc_config() -> LiquidationHeatMapConfig:
    """Create config for BTC/USDT on Binance."""
    return LiquidationHeatMapConfig(
        strategy_id="LIQ-HEATMAP-BTC-001",
        instrument_id="BTCUSDT-PERP.BINANCE",
        bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
        atr_period=200,
        pivot_lookback=2,
        max_zones=500,
        atr_multiplier=0.25,
        trade_size=Decimal("0.001"),
        max_position_size=Decimal("0.01"),
        zone_proximity_pct=0.001,
        min_volume_intensity=0.5,
    )


def create_eth_config() -> LiquidationHeatMapConfig:
    """Create config for ETH/USDT on Binance."""
    return LiquidationHeatMapConfig(
        strategy_id="LIQ-HEATMAP-ETH-001",
        instrument_id="ETHUSDT-PERP.BINANCE",
        bar_type="ETHUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
        atr_period=200,
        pivot_lookback=2,
        max_zones=500,
        atr_multiplier=0.25,
        trade_size=Decimal("0.01"),
        max_position_size=Decimal("0.1"),
        zone_proximity_pct=0.001,
        min_volume_intensity=0.5,
    )


# Timeframe-specific ATR multipliers (from Pine Script)
ATR_MULTIPLIERS = {
    "1m": 0.4,  # < 60 minutes
    "5m": 0.25,
    "15m": 0.25,
    "30m": 0.25,
    "1h": 0.2,  # >= 60 minutes
    "4h": 0.2,
    "1d": 0.2,  # Daily
}
