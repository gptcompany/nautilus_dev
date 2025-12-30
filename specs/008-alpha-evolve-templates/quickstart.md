# Quickstart: Alpha-Evolve Strategy Templates

## Prerequisites

1. NautilusTrader nightly environment activated:
   ```bash
   source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
   ```

2. ParquetDataCatalog populated with BTC data

## Basic Usage

### 1. Create a Seed Strategy

```python
from decimal import Decimal
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId

from scripts.alpha_evolve.templates import MomentumEvolveStrategy, MomentumEvolveConfig

# Configure strategy
config = MomentumEvolveConfig(
    instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
    trade_size=Decimal("0.1"),
    fast_period=10,
    slow_period=30,
)

# Create strategy instance
strategy = MomentumEvolveStrategy(config)
```

### 2. Run Backtest

```python
from scripts.alpha_evolve.evaluator import BacktestEvaluator, BacktestConfig

evaluator = BacktestEvaluator(
    BacktestConfig(
        data_catalog_path="/path/to/catalog",
        symbols=["BTCUSDT-PERP.BINANCE"],
        start_date="2024-01-01",
        end_date="2024-06-01",
    )
)

# Evaluate strategy
result = await evaluator.evaluate(strategy)
print(f"Sharpe: {result.metrics.sharpe_ratio}")
print(f"Calmar: {result.metrics.calmar_ratio}")
```

### 3. Access Equity Curve

```python
# After backtest
curve = strategy.get_equity_curve()
for point in curve[-10:]:  # Last 10 points
    print(f"{point.timestamp}: ${point.equity:.2f}")
```

### 4. Create Custom Evolvable Strategy

```python
from scripts.alpha_evolve.templates import BaseEvolveStrategy, BaseEvolveConfig
from nautilus_trader.indicators import RelativeStrengthIndex

class RSIEvolveConfig(BaseEvolveConfig, frozen=True):
    rsi_period: int = 14
    overbought: float = 70.0
    oversold: float = 30.0

class RSIEvolveStrategy(BaseEvolveStrategy):
    def __init__(self, config: RSIEvolveConfig) -> None:
        super().__init__(config)
        self.rsi = RelativeStrengthIndex(config.rsi_period)

    def on_start(self) -> None:
        super().on_start()
        self.register_indicator_for_bars(self.config.bar_type, self.rsi)

    def _on_bar_evolved(self, bar) -> None:
        if not self.indicators_initialized():
            return

        # === EVOLVE-BLOCK: decision_logic ===
        if self.rsi.value < self.config.oversold:
            if self.portfolio.is_flat(self.config.instrument_id):
                self._enter_long(self.config.trade_size)
        elif self.rsi.value > self.config.overbought:
            if self.portfolio.is_net_long(self.config.instrument_id):
                self._close_position()
        # === END EVOLVE-BLOCK ===
```

## Order Helpers

All strategies have these helper methods:

| Method | Description |
|--------|-------------|
| `_enter_long(qty)` | Market buy, closes short if needed |
| `_enter_short(qty)` | Market sell, closes long if needed |
| `_close_position()` | Close all positions |
| `_get_position_size()` | Current net position |
| `_get_equity()` | Account balance + unrealized PnL |

## EVOLVE-BLOCK Guidelines

1. **Location**: Inside `_on_bar_evolved()` method
2. **Markers**: Use exact format:
   ```python
   # === EVOLVE-BLOCK: decision_logic ===
   # Your trading logic here
   # === END EVOLVE-BLOCK ===
   ```
3. **Content**: Entry/exit signals using order helpers
4. **Avoid**: Position sizing, risk management (keep simple)

## Common Patterns

### Entry with Confirmation

```python
# === EVOLVE-BLOCK: decision_logic ===
if self.fast_ema.value > self.slow_ema.value:  # Trend
    if self.rsi.value < 50:  # Confirmation
        if self.portfolio.is_flat(self.config.instrument_id):
            self._enter_long(self.config.trade_size)
# === END EVOLVE-BLOCK ===
```

### Exit with Multiple Conditions

```python
# === EVOLVE-BLOCK: decision_logic ===
should_exit = (
    self.fast_ema.value < self.slow_ema.value  # Trend reversal
    or self.rsi.value > 80  # Overbought
)
if should_exit and self.portfolio.is_net_long(self.config.instrument_id):
    self._close_position()
# === END EVOLVE-BLOCK ===
```
