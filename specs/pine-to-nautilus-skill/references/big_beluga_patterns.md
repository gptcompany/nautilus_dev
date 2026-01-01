# Big Beluga Indicator Patterns

Big Beluga è noto per indicatori visivamente ricchi con logiche spesso basate su:
- Smoothing avanzato
- ATR-based dynamic bands
- Multi-timeframe analysis
- Segnali visuali (colori, frecce, label)

## Pattern Comuni Big Beluga

### 1. Double/Triple Smoothing

Big Beluga spesso applica EMA multiple per smoothing:

```pinescript
// Pine Script tipico Big Beluga
smoothed = ta.ema(ta.ema(ta.ema(src, len), len), len)
```

```python
# NautilusTrader equivalent
class TripleEMA(Indicator):
    def __init__(self, period: int = 14):
        super().__init__([period])
        self._ema1 = ExponentialMovingAverage(period)
        self._ema2 = ExponentialMovingAverage(period)
        self._ema3 = ExponentialMovingAverage(period)
        
        self.value: float = 0.0
        self._stage: int = 0  # Track warmup
    
    def handle_bar(self, bar: Bar) -> None:
        # Stage 1: Prima EMA
        self._ema1.handle_bar(bar)
        if not self._ema1.initialized:
            return
        
        # Stage 2: Seconda EMA (su output della prima)
        # Creare una "fake bar" con il valore EMA1
        self._feed_value_to_ema(self._ema2, self._ema1.value)
        if not self._ema2.initialized:
            return
        
        # Stage 3: Terza EMA
        self._feed_value_to_ema(self._ema3, self._ema2.value)
        if not self._ema3.initialized:
            return
        
        self.value = self._ema3.value
        self._set_initialized(True)
    
    def _feed_value_to_ema(self, ema, value: float):
        """Alimentare un valore raw a un EMA."""
        # Gli EMA Nautilus aspettano Bar, quindi usiamo update raw
        ema.update_raw(value)
```

### 2. ATR-Based Dynamic Bands

```pinescript
// Pine: Bande basate su ATR
atr = ta.atr(atrPeriod)
basis = ta.sma(close, period)
upperBand = basis + (multiplier * atr)
lowerBand = basis - (multiplier * atr)
```

```python
class ATRBands(Indicator):
    def __init__(self, period: int = 20, atr_period: int = 14, multiplier: float = 2.0):
        super().__init__([period, atr_period, multiplier])
        
        self.multiplier = multiplier
        self._sma = SimpleMovingAverage(period)
        self._atr = AverageTrueRange(atr_period)
        
        self.basis: float = 0.0
        self.upper: float = 0.0
        self.lower: float = 0.0
    
    def handle_bar(self, bar: Bar) -> None:
        self._sma.handle_bar(bar)
        self._atr.handle_bar(bar)
        
        if not (self._sma.initialized and self._atr.initialized):
            return
        
        self.basis = self._sma.value
        band_width = self.multiplier * self._atr.value
        self.upper = self.basis + band_width
        self.lower = self.basis - band_width
        
        self._set_initialized(True)
```

### 3. Trend Detection con Colori

Big Beluga usa spesso colori per indicare trend:

```pinescript
// Pine: Colore basato su trend
trendColor = close > basis ? color.green : color.red
```

```python
from enum import IntEnum

class Trend(IntEnum):
    DOWN = -1
    NEUTRAL = 0
    UP = 1

class TrendIndicator(Indicator):
    def __init__(self, period: int = 20):
        super().__init__([period])
        self._sma = SimpleMovingAverage(period)
        
        self.value: float = 0.0
        self.trend: Trend = Trend.NEUTRAL
    
    def handle_bar(self, bar: Bar) -> None:
        self._sma.handle_bar(bar)
        
        if not self._sma.initialized:
            return
        
        close = float(bar.close)
        self.value = self._sma.value
        
        # Determinare trend
        if close > self.value:
            self.trend = Trend.UP
        elif close < self.value:
            self.trend = Trend.DOWN
        else:
            self.trend = Trend.NEUTRAL
        
        self._set_initialized(True)
```

### 4. Signal Arrows/Labels

Big Beluga mostra frecce per segnali entry:

```pinescript
// Pine: Frecce su crossover
buySignal = ta.crossover(fastMA, slowMA)
sellSignal = ta.crossunder(fastMA, slowMA)
plotshape(buySignal, style=shape.triangleup, location=location.belowbar)
plotshape(sellSignal, style=shape.triangledown, location=location.abovebar)
```

```python
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional

class SignalType(IntEnum):
    NONE = 0
    BUY = 1
    SELL = -1

@dataclass
class SignalEvent:
    signal_type: SignalType
    price: float
    strength: float = 1.0  # 0-1, per filtrare segnali deboli

class CrossoverSignal(Indicator):
    def __init__(self, fast_period: int = 12, slow_period: int = 26):
        super().__init__([fast_period, slow_period])
        
        self._fast_ema = ExponentialMovingAverage(fast_period)
        self._slow_ema = ExponentialMovingAverage(slow_period)
        
        self._prev_fast: float = 0.0
        self._prev_slow: float = 0.0
        
        self.signal: SignalType = SignalType.NONE
        self.last_signal_event: Optional[SignalEvent] = None
    
    def handle_bar(self, bar: Bar) -> None:
        # Salvare valori precedenti
        if self._fast_ema.initialized:
            self._prev_fast = self._fast_ema.value
            self._prev_slow = self._slow_ema.value
        
        # Aggiornare
        self._fast_ema.handle_bar(bar)
        self._slow_ema.handle_bar(bar)
        
        if not (self._fast_ema.initialized and self._slow_ema.initialized):
            return
        
        fast = self._fast_ema.value
        slow = self._slow_ema.value
        
        # Reset signal
        self.signal = SignalType.NONE
        
        # Check crossover (buy)
        if fast > slow and self._prev_fast <= self._prev_slow:
            self.signal = SignalType.BUY
            self.last_signal_event = SignalEvent(
                signal_type=SignalType.BUY,
                price=float(bar.close),
                strength=abs(fast - slow) / slow  # Strength = divergenza %
            )
        
        # Check crossunder (sell)
        elif fast < slow and self._prev_fast >= self._prev_slow:
            self.signal = SignalType.SELL
            self.last_signal_event = SignalEvent(
                signal_type=SignalType.SELL,
                price=float(bar.close),
                strength=abs(fast - slow) / slow
            )
        
        self._set_initialized(True)
```

### 5. Multi-Output Indicator (Dashboard Style)

Big Beluga spesso crea "dashboard" con multiple metriche:

```python
from dataclasses import dataclass

@dataclass
class DashboardOutput:
    trend: Trend
    momentum: float
    volatility: float
    signal: SignalType
    strength: float

class DashboardIndicator(Indicator):
    def __init__(self, period: int = 20):
        super().__init__([period])
        
        self._ema = ExponentialMovingAverage(period)
        self._rsi = RelativeStrengthIndex(14)
        self._atr = AverageTrueRange(14)
        
        self.output: Optional[DashboardOutput] = None
    
    def handle_bar(self, bar: Bar) -> None:
        self._ema.handle_bar(bar)
        self._rsi.handle_bar(bar)
        self._atr.handle_bar(bar)
        
        if not all([self._ema.initialized, self._rsi.initialized, self._atr.initialized]):
            return
        
        close = float(bar.close)
        
        # Calcolare trend
        trend = Trend.UP if close > self._ema.value else Trend.DOWN
        
        # Momentum normalizzato (-1 to 1)
        momentum = (self._rsi.value - 50) / 50
        
        # Volatilità relativa
        volatility = self._atr.value / close
        
        # Signal composito
        if trend == Trend.UP and momentum > 0.4:
            signal = SignalType.BUY
            strength = min(1.0, momentum)
        elif trend == Trend.DOWN and momentum < -0.4:
            signal = SignalType.SELL
            strength = min(1.0, abs(momentum))
        else:
            signal = SignalType.NONE
            strength = 0.0
        
        self.output = DashboardOutput(
            trend=trend,
            momentum=momentum,
            volatility=volatility,
            signal=signal,
            strength=strength
        )
        
        self._set_initialized(True)
```

## Conversione Elementi Visuali

| Elemento Pine | Traduzione Nautilus |
|---------------|---------------------|
| `color.green`/`color.red` | `Trend.UP`/`Trend.DOWN` enum |
| `plotshape(...triangleup)` | `SignalType.BUY` |
| `plotshape(...triangledown)` | `SignalType.SELL` |
| `bgcolor(...)` | Zone/State field nell'indicatore |
| `fill(p1, p2, color)` | `upper`/`lower` band values |
| `plot(value, color=...)` | Value + Trend enum |

## Note sulla Conversione Big Beluga

1. **Ignorare elementi puramente visivi**: Label text, colori decorativi
2. **Convertire colori significativi in enum**: Verde/Rosso → UP/DOWN
3. **Preservare la logica**: Focus su quando e perché i segnali si attivano
4. **Testare con stessi dati**: Esportare dati da TV, confrontare output
