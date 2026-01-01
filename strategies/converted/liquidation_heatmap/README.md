# Liquidation HeatMap Strategy

Converted from [Liquidation HeatMap [BigBeluga]](https://www.tradingview.com/script/tMtleB1G-Liqudation-HeatMap-BigBeluga/)

**License**: CC BY-NC-SA 4.0

## Overview

An advanced liquidity visualization and trading strategy that identifies potential liquidation zones (stop-loss clusters) and trades reversals at these levels.

## How It Works

### Indicator Logic (from Pine Script)

1. **Volume Collection**: Tracks volume data (or uses candle range if no volume)
2. **Pivot Detection**: Identifies pivot highs and lows with `pivot_lookback` bars
3. **Zone Creation**: Creates liquidation zones around pivots with ATR-based width
4. **Volume Intensity**: Colors zones based on volume (0.0 = low, 1.0 = high)
5. **Zone Consumption**: Removes zones when price crosses through their midpoint

### Trading Strategy

- **Long Entry**: When price approaches a high-volume zone below current price
- **Short Entry**: When price approaches a high-volume zone above current price
- **Exit**: When the target zone is consumed (price crosses midpoint)

## Configuration

```python
from strategies.converted.liquidation_heatmap import (
    LiquidationHeatMapConfig,
    LiquidationHeatMapStrategy,
)

config = LiquidationHeatMapConfig(
    strategy_id="LIQ-001",
    instrument_id="BTCUSDT-PERP.BINANCE",
    bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",

    # Indicator settings (from Pine Script)
    atr_period=200,           # ATR period for zone width
    pivot_lookback=2,         # Bars to look back for pivot detection
    max_zones=500,            # Maximum active zones
    atr_multiplier=0.25,      # ATR multiplier for zone width

    # Trading settings
    trade_size=Decimal("0.001"),
    max_position_size=Decimal("0.01"),
    zone_proximity_pct=0.001,      # 0.1% - how close to zone to enter
    min_volume_intensity=0.5,      # Minimum zone intensity to trade
)

strategy = LiquidationHeatMapStrategy(config)
```

## ATR Multipliers by Timeframe

From the original Pine Script:

| Timeframe | ATR Multiplier |
|-----------|----------------|
| < 1 hour  | 0.25 - 0.4     |
| >= 1 hour | 0.2            |
| Daily     | 0.2            |

## Files

```
strategies/converted/liquidation_heatmap/
├── __init__.py                      # Package exports
├── liquidation_zone_indicator.py    # Core indicator (LiquidationZoneIndicator)
├── liquidation_heatmap_strategy.py  # Trading strategy
├── config.py                        # Configuration presets
├── pine_source.txt                  # Original Pine Script
└── README.md                        # This file
```

## Pine Script Mapping

| Pine Script | NautilusTrader |
|-------------|----------------|
| `ta.atr(200)` | `AverageTrueRange(period=200)` (Native Rust) |
| `ta.pivothigh(2, 2)` | Custom pivot detection |
| `ta.pivotlow(2, 2)` | Custom pivot detection |
| `array<box>` | `list[LiquidationZone]` |
| `color.from_gradient()` | `volume_intensity` (0.0-1.0) |

## Testing

```bash
# Run unit tests
uv run pytest tests/strategies/test_liquidation_heatmap.py -v

# Run with coverage
uv run pytest tests/strategies/test_liquidation_heatmap.py --cov=strategies/converted/liquidation_heatmap
```

## Notes

- The original Pine Script is an **indicator** (visualization only)
- This conversion adds **trading logic** to execute at liquidation zones
- Zones are removed when "consumed" by price crossing through midpoint
- Volume intensity helps filter for higher-quality zones

## Credits

- Original Indicator: [BigBeluga](https://www.tradingview.com/u/BigBeluga/)
- Conversion: Claude Code `/pinescript` skill
