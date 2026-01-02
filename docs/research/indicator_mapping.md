# NautilusTrader Indicator Mapping

Reference table for mapping academic paper indicator terminology to native NautilusTrader Rust implementations.

## Native Rust Indicators (ALWAYS Use These)

**Import**: `from nautilus_trader.indicators import {ClassName}` (Nightly)

| Paper Term | Alternative Names | NautilusTrader Class | Parameters |
|------------|-------------------|---------------------|------------|
| EMA | Exponential MA, EWMA | `ExponentialMovingAverage` | `period: int` |
| SMA | Simple MA, Moving Average | `SimpleMovingAverage` | `period: int` |
| WMA | Weighted MA | `WeightedMovingAverage` | `period: int` |
| HMA | Hull MA | `HullMovingAverage` | `period: int` |
| DEMA | Double EMA | `DoubleExponentialMovingAverage` | `period: int` |
| RSI | Relative Strength Index | `RelativeStrengthIndex` | `period: int` |
| MACD | - | `MovingAverageConvergenceDivergence` | `fast_period, slow_period, signal_period` |
| ATR | Average True Range | `AverageTrueRange` | `period: int` |
| BB | Bollinger Bands | `BollingerBands` | `period: int, k: float` |
| Stochastic | %K, %D | `Stochastic` | `period_k, period_d` |
| ADX | Average Directional Index | `AverageDirectionalIndex` | `period: int` |
| CCI | Commodity Channel Index | `CommodityChannelIndex` | `period: int` |
| ROC | Rate of Change | `RateOfChange` | `period: int` |
| OBV | On-Balance Volume | `OnBalanceVolume` | - |
| VWAP | Volume Weighted Avg Price | `VolumeWeightedAveragePrice` | - |
| Keltner | Keltner Channels | `KeltnerChannel` | `period, k_multiplier` |
| Donchian | Donchian Channels | `DonchianChannel` | `period: int` |
| Aroon | Aroon Indicator | `AroonIndicator` | `period: int` |

## Usage Pattern (Native Rust)

```python
# NautilusTrader Nightly - all indicators in single module
from nautilus_trader.indicators import (
    ExponentialMovingAverage,
    RelativeStrengthIndex,
    AverageTrueRange,
    Indicator,  # Base class for custom indicators
)

class MyStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        # Native Rust indicators - 100x faster than Python
        self.ema = ExponentialMovingAverage(period=20)
        self.rsi = RelativeStrengthIndex(period=14)
        self.atr = AverageTrueRange(period=14)

    def on_bar(self, bar: Bar) -> None:
        # Update indicators with bar data
        self.ema.handle_bar(bar)
        self.rsi.handle_bar(bar)
        self.atr.handle_bar(bar)

        # Access computed values
        if self.ema.initialized and self.rsi.initialized:
            ema_value = self.ema.value
            rsi_value = self.rsi.value
```

## Indicators NOT in NautilusTrader (Require Custom Implementation)

| Indicator | Notes | Suggested Alternative |
|-----------|-------|----------------------|
| Ichimoku Cloud | Complex multi-line indicator | Use EMA combination |
| Supertrend | ATR-based trend indicator | ATR + EMA |
| Heikin-Ashi | Modified candlesticks | Process in wrangler |
| Renko | Non-time bars | Custom bar aggregator |
| Elliott Wave | Pattern-based | Not applicable |
| Gann Lines | Geometric patterns | Not applicable |
| Volume Profile | Distribution analysis | Custom implementation |
| Order Flow Delta | Tick-level analysis | Custom tick processor |

## Academic Paper Terminology Mapping

| Paper Says | Maps To |
|------------|---------|
| "20-day moving average" | `ExponentialMovingAverage(period=20)` or `SimpleMovingAverage(period=20)` |
| "RSI(14)" | `RelativeStrengthIndex(period=14)` |
| "Bollinger Bands (20, 2)" | `BollingerBands(period=20, k=2.0)` |
| "MACD(12,26,9)" | `MovingAverageConvergenceDivergence(fast_period=12, slow_period=26, signal_period=9)` |
| "ATR-based volatility" | `AverageTrueRange(period=14)` |
| "momentum indicator" | `RateOfChange(period=10)` or `RelativeStrengthIndex(period=14)` |
| "trend filter" | `ExponentialMovingAverage(period=50)` or `AverageDirectionalIndex(period=14)` |
| "overbought/oversold" | `RelativeStrengthIndex(period=14)` with thresholds 70/30 |
| "volatility bands" | `BollingerBands` or `KeltnerChannel` |
| "volume confirmation" | `OnBalanceVolume` or `VolumeWeightedAveragePrice` |

## Context7 Documentation Links

For the most up-to-date indicator documentation, query Context7:
- "Show NautilusTrader indicator classes"
- "How to use ExponentialMovingAverage in NautilusTrader"
- "List all momentum indicators in NautilusTrader"

## Version Notes

- **Nightly v1.222.0+**: All indicators listed are available
- **Stable**: Some newer indicators may be missing
- Always prefer native Rust indicators over custom Python implementations
