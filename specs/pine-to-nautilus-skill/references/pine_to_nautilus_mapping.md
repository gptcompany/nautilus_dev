# Pine Script to NautilusTrader Function Mapping

## Moving Averages

| Pine Script | NautilusTrader Python | NautilusTrader Rust |
|-------------|----------------------|---------------------|
| `ta.sma(src, len)` | `from nautilus_trader.indicators.average.sma import SimpleMovingAverage` | `nautilus_indicators::average::sma::SimpleMovingAverage` |
| `ta.ema(src, len)` | `from nautilus_trader.indicators.average.ema import ExponentialMovingAverage` | `nautilus_indicators::average::ema::ExponentialMovingAverage` |
| `ta.wma(src, len)` | `from nautilus_trader.indicators.average.wma import WeightedMovingAverage` | `nautilus_indicators::average::wma::WeightedMovingAverage` |
| `ta.hma(src, len)` | `from nautilus_trader.indicators.average.hma import HullMovingAverage` | `nautilus_indicators::average::hma::HullMovingAverage` |
| `ta.vwma(src, len)` | `from nautilus_trader.indicators.average.vwap import VolumeWeightedAveragePrice` | Custom implementation |
| `ta.dema(src, len)` | `from nautilus_trader.indicators.average.dema import DoubleExponentialMovingAverage` | Custom |
| `ta.tema(src, len)` | Custom implementation | Custom implementation |

## Momentum Indicators

| Pine Script | NautilusTrader Python |
|-------------|----------------------|
| `ta.rsi(src, len)` | `from nautilus_trader.indicators.rsi import RelativeStrengthIndex` |
| `ta.macd(src, fast, slow, signal)` | `from nautilus_trader.indicators.macd import MovingAverageConvergenceDivergence` |
| `ta.cci(src, len)` | `from nautilus_trader.indicators.cci import CommodityChannelIndex` |
| `ta.stoch(close, high, low, len)` | `from nautilus_trader.indicators.stochastics import Stochastics` |
| `ta.mfi(hlc3, vol, len)` | Custom implementation |

## Volatility Indicators

| Pine Script | NautilusTrader Python |
|-------------|----------------------|
| `ta.atr(len)` | `from nautilus_trader.indicators.atr import AverageTrueRange` |
| `ta.bb(src, len, mult)` | `from nautilus_trader.indicators.bollinger_bands import BollingerBands` |
| `ta.kc(src, len, mult)` | `from nautilus_trader.indicators.keltner_channel import KeltnerChannel` |
| `ta.donchian(len)` | `from nautilus_trader.indicators.donchian_channel import DonchianChannel` |

## Crossover/Crossunder Logic

```python
# Pine: ta.crossover(a, b)
def crossover(current_a: float, current_b: float, prev_a: float, prev_b: float) -> bool:
    return current_a > current_b and prev_a <= prev_b

# Pine: ta.crossunder(a, b)
def crossunder(current_a: float, current_b: float, prev_a: float, prev_b: float) -> bool:
    return current_a < current_b and prev_a >= prev_b
```

## Null Handling

```python
# Pine: nz(x, replacement)
def nz(x, replacement=0):
    return x if x is not None and not math.isnan(x) else replacement

# Pine: na(x)
def na(x) -> bool:
    return x is None or math.isnan(x)

# Pine: fixnan(x) - replace NaN with previous valid value
# Requires maintaining state in indicator
```

## Price Sources

| Pine Script | NautilusTrader |
|-------------|----------------|
| `close` | `float(bar.close)` |
| `open` | `float(bar.open)` |
| `high` | `float(bar.high)` |
| `low` | `float(bar.low)` |
| `volume` | `float(bar.volume)` |
| `hl2` | `(float(bar.high) + float(bar.low)) / 2` |
| `hlc3` | `(float(bar.high) + float(bar.low) + float(bar.close)) / 3` |
| `ohlc4` | `(float(bar.open) + float(bar.high) + float(bar.low) + float(bar.close)) / 4` |

## Historical References

Pine Script usa `[]` per riferimenti storici:
```pinescript
// Pine: valore di 1 barra fa
close[1]
```

In NautilusTrader, mantenere un buffer:
```python
from collections import deque

class MyIndicator(Indicator):
    def __init__(self, lookback: int = 10):
        self._closes = deque(maxlen=lookback + 1)
    
    def handle_bar(self, bar):
        self._closes.append(float(bar.close))
        
        if len(self._closes) >= 2:
            current_close = self._closes[-1]
            prev_close = self._closes[-2]  # equivalent to close[1]
```

## Math Functions

| Pine Script | Python |
|-------------|--------|
| `math.abs(x)` | `abs(x)` |
| `math.max(a, b)` | `max(a, b)` |
| `math.min(a, b)` | `min(a, b)` |
| `math.sqrt(x)` | `math.sqrt(x)` |
| `math.pow(x, y)` | `x ** y` or `math.pow(x, y)` |
| `math.log(x)` | `math.log(x)` |
| `math.exp(x)` | `math.exp(x)` |
| `math.round(x)` | `round(x)` |
| `math.floor(x)` | `math.floor(x)` |
| `math.ceil(x)` | `math.ceil(x)` |

## Conditional Logic

```pinescript
// Pine
result = condition ? valueIfTrue : valueIfFalse
```

```python
# Python
result = value_if_true if condition else value_if_false
```

## Loop Equivalents

Pine Script v5+ supporta loop, ma spesso sono usati per calcoli su serie.
In NautilusTrader, preferire:
- `sum()` per somme
- `max()/min()` per estremi
- List comprehensions per trasformazioni
- `numpy` per operazioni vettoriali su buffer grandi
