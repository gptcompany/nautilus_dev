# NautilusTrader Indicator Patterns

## Pattern Base: Python Indicator

```python
from collections import deque
from nautilus_trader.indicators.base.indicator import Indicator
from nautilus_trader.model.data import Bar

class CustomIndicator(Indicator):
    """
    Docstring: descrizione dell'indicatore, parametri, formula.
    """
    
    def __init__(
        self,
        period: int = 14,
        multiplier: float = 2.0,
    ):
        # Chiamare super().__init__ con lista parametri per identificazione
        super().__init__([period, multiplier])
        
        # Parametri
        self.period = period
        self.multiplier = multiplier
        
        # Buffer per dati storici (se necessari)
        self._values: deque[float] = deque(maxlen=period)
        
        # Sotto-indicatori (se usati)
        # self._ema = ExponentialMovingAverage(period)
        
        # Output values
        self.value: float = 0.0
        # Altri output se necessari
        # self.upper_band: float = 0.0
        # self.lower_band: float = 0.0
        # self.signal: int = 0  # -1, 0, 1
    
    def handle_bar(self, bar: Bar) -> None:
        """
        Aggiorna l'indicatore con una nuova barra.
        Questo metodo è chiamato automaticamente quando registrato.
        """
        # Estrarre valori dalla barra
        close = float(bar.close)
        high = float(bar.high)
        low = float(bar.low)
        
        # Aggiornare sotto-indicatori
        # self._ema.handle_bar(bar)
        
        # Aggiungere al buffer
        self._values.append(close)
        
        # Verificare se abbiamo abbastanza dati
        if len(self._values) < self.period:
            return
        
        # Calcolare il valore dell'indicatore
        self.value = self._calculate()
        
        # Marcare come inizializzato
        self._set_has_inputs(True)
        self._set_initialized(True)
    
    def _calculate(self) -> float:
        """Logica di calcolo privata."""
        # Implementare qui la formula
        return sum(self._values) / len(self._values)
    
    def reset(self) -> None:
        """Reset dell'indicatore allo stato iniziale."""
        self._values.clear()
        # self._ema.reset()
        self.value = 0.0
        self._set_has_inputs(False)
        self._set_initialized(False)
    
    @property
    def name(self) -> str:
        """Nome dell'indicatore per logging/debug."""
        return f"CustomIndicator({self.period}, {self.multiplier})"
```

## Pattern: Indicatore con Sotto-Indicatori

```python
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.indicators.atr import AverageTrueRange

class CompositeIndicator(Indicator):
    def __init__(self, fast_period: int = 12, slow_period: int = 26, atr_period: int = 14):
        super().__init__([fast_period, slow_period, atr_period])
        
        # Sotto-indicatori - Nautilus li gestisce automaticamente
        self._fast_ema = ExponentialMovingAverage(fast_period)
        self._slow_ema = ExponentialMovingAverage(slow_period)
        self._atr = AverageTrueRange(atr_period)
        
        self.value: float = 0.0
        self.signal: int = 0
    
    def handle_bar(self, bar: Bar) -> None:
        # Aggiornare tutti i sotto-indicatori
        self._fast_ema.handle_bar(bar)
        self._slow_ema.handle_bar(bar)
        self._atr.handle_bar(bar)
        
        # Verificare che tutti siano inizializzati
        if not (self._fast_ema.initialized and 
                self._slow_ema.initialized and 
                self._atr.initialized):
            return
        
        # Calcolare
        self.value = self._fast_ema.value - self._slow_ema.value
        self.signal = 1 if self.value > 0 else -1
        
        self._set_has_inputs(True)
        self._set_initialized(True)
    
    def reset(self) -> None:
        self._fast_ema.reset()
        self._slow_ema.reset()
        self._atr.reset()
        self.value = 0.0
        self.signal = 0
        self._set_has_inputs(False)
        self._set_initialized(False)
```

## Pattern: Indicatore con Bande

```python
class BandIndicator(Indicator):
    def __init__(self, period: int = 20, multiplier: float = 2.0):
        super().__init__([period, multiplier])
        
        self.period = period
        self.multiplier = multiplier
        self._values: deque[float] = deque(maxlen=period)
        
        # Output multipli
        self.middle: float = 0.0
        self.upper: float = 0.0
        self.lower: float = 0.0
    
    def handle_bar(self, bar: Bar) -> None:
        close = float(bar.close)
        self._values.append(close)
        
        if len(self._values) < self.period:
            return
        
        # Calcolare media e deviazione standard
        values_list = list(self._values)
        self.middle = sum(values_list) / self.period
        
        variance = sum((x - self.middle) ** 2 for x in values_list) / self.period
        std_dev = variance ** 0.5
        
        self.upper = self.middle + (self.multiplier * std_dev)
        self.lower = self.middle - (self.multiplier * std_dev)
        
        self._set_has_inputs(True)
        self._set_initialized(True)
```

## Pattern: Indicatore con Segnali di Trading

```python
from enum import IntEnum

class Signal(IntEnum):
    STRONG_SELL = -2
    SELL = -1
    NEUTRAL = 0
    BUY = 1
    STRONG_BUY = 2

class SignalIndicator(Indicator):
    def __init__(self, period: int = 14, overbought: float = 70, oversold: float = 30):
        super().__init__([period, overbought, oversold])
        
        self.overbought = overbought
        self.oversold = oversold
        self._rsi = RelativeStrengthIndex(period)
        
        self.value: float = 0.0
        self.signal: Signal = Signal.NEUTRAL
        self._prev_value: float = 0.0
    
    def handle_bar(self, bar: Bar) -> None:
        self._rsi.handle_bar(bar)
        
        if not self._rsi.initialized:
            return
        
        self._prev_value = self.value
        self.value = self._rsi.value
        
        # Generare segnali
        if self.value < self.oversold:
            if self._prev_value >= self.oversold:  # Crossunder
                self.signal = Signal.BUY
            else:
                self.signal = Signal.STRONG_BUY
        elif self.value > self.overbought:
            if self._prev_value <= self.overbought:  # Crossover
                self.signal = Signal.SELL
            else:
                self.signal = Signal.STRONG_SELL
        else:
            self.signal = Signal.NEUTRAL
        
        self._set_has_inputs(True)
        self._set_initialized(True)
```

## Pattern: Registrazione in Strategy

```python
from nautilus_trader.trading.strategy import Strategy

class MyStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)
        
        # Creare indicatori
        self.custom_ind = CustomIndicator(period=20)
        self.signal_ind = SignalIndicator(period=14)
    
    def on_start(self) -> None:
        # Registrare indicatori per aggiornamento automatico
        self.register_indicator_for_bars(self.bar_type, self.custom_ind)
        self.register_indicator_for_bars(self.bar_type, self.signal_ind)
        
        # Richiedere dati storici per warmup
        self.request_bars(self.bar_type)
        
        # Sottoscrivere a dati live
        self.subscribe_bars(self.bar_type)
    
    def on_bar(self, bar: Bar) -> None:
        # Gli indicatori sono già aggiornati automaticamente
        if not self.custom_ind.initialized:
            return
        
        # Usare i valori degli indicatori
        if self.signal_ind.signal == Signal.BUY:
            self.buy(...)
        elif self.signal_ind.signal == Signal.SELL:
            self.sell(...)
```

## Pattern: Test di Validazione

```python
import pytest
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.test_kit.stubs.data import TestDataStubs

class TestCustomIndicator:
    def setup_method(self):
        self.indicator = CustomIndicator(period=14)
    
    def test_initialization(self):
        assert not self.indicator.initialized
        assert self.indicator.value == 0.0
    
    def test_warmup_period(self):
        """Verificare che servano 'period' barre per inizializzare."""
        instrument = TestInstrumentProvider.default_fx_ccy("EUR/USD")
        
        for i in range(13):
            bar = TestDataStubs.bar_5decimal()
            self.indicator.handle_bar(bar)
            assert not self.indicator.initialized
        
        bar = TestDataStubs.bar_5decimal()
        self.indicator.handle_bar(bar)
        assert self.indicator.initialized
    
    def test_known_values(self):
        """Confrontare con valori calcolati da TradingView."""
        # Valori attesi da TradingView export
        expected_values = [
            # (close, expected_indicator_value)
            (100.0, None),  # Non ancora inizializzato
            (101.0, None),
            # ... più valori ...
            (105.0, 102.5),  # Primo valore dopo warmup
        ]
        
        for close, expected in expected_values:
            bar = self._create_bar(close)
            self.indicator.handle_bar(bar)
            
            if expected is not None:
                assert abs(self.indicator.value - expected) < 0.0001
```
