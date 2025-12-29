# NautilusTrader Indicator Mapping

Reference table for mapping academic paper indicator terminology to native NautilusTrader Rust implementations.

## Native Rust Indicators (ALWAYS Use These)

| Paper Term | Alternative Names | NautilusTrader Class | Module | Parameters |
|------------|-------------------|---------------------|--------|------------|
| EMA | Exponential MA, EWMA | `ExponentialMovingAverage` | `nautilus_trader.indicators.average.ema` | `period: int` |
| SMA | Simple MA, Moving Average | `SimpleMovingAverage` | `nautilus_trader.indicators.average.sma` | `period: int` |
| WMA | Weighted MA | `WeightedMovingAverage` | `nautilus_trader.indicators.average.wma` | `period: int` |
| HMA | Hull MA | `HullMovingAverage` | `nautilus_trader.indicators.average.hma` | `period: int` |
| DEMA | Double EMA | `DoubleExponentialMovingAverage` | `nautilus_trader.indicators.average.dema` | `period: int` |
| RSI | Relative Strength Index | `RelativeStrengthIndex` | `nautilus_trader.indicators.momentum.rsi` | `period: int` |
| MACD | - | `MovingAverageConvergenceDivergence` | `nautilus_trader.indicators.momentum.macd` | `fast_period, slow_period, signal_period` |
| ATR | Average True Range | `AverageTrueRange` | `nautilus_trader.indicators.volatility.atr` | `period: int` |
| BB | Bollinger Bands | `BollingerBands` | `nautilus_trader.indicators.volatility.bb` | `period: int, k: float` |
| Stochastic | %K, %D | `Stochastic` | `nautilus_trader.indicators.momentum.stoch` | `period_k, period_d` |
| ADX | Average Directional Index | `AverageDirectionalIndex` | `nautilus_trader.indicators.momentum.adx` | `period: int` |
| CCI | Commodity Channel Index | `CommodityChannelIndex` | `nautilus_trader.indicators.momentum.cci` | `period: int` |
| ROC | Rate of Change | `RateOfChange` | `nautilus_trader.indicators.momentum.roc` | `period: int` |
| OBV | On-Balance Volume | `OnBalanceVolume` | `nautilus_trader.indicators.volume.obv` | - |
| VWAP | Volume Weighted Avg Price | `VolumeWeightedAveragePrice` | `nautilus_trader.indicators.average.vwap` | - |
| Keltner | Keltner Channels | `KeltnerChannel` | `nautilus_trader.indicators.volatility.kc` | `period, k_multiplier` |
| Donchian | Donchian Channels | `DonchianChannel` | `nautilus_trader.indicators.volatility.dc` | `period: int` |
| Aroon | Aroon Indicator | `AroonIndicator` | `nautilus_trader.indicators.momentum.aroon` | `period: int` |

## Usage Pattern (Native Rust)

```python
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.indicators.momentum.rsi import RelativeStrengthIndex
from nautilus_trader.indicators.volatility.atr import AverageTrueRange

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
