# Data Model: Alpha-Evolve Strategy Templates

**Created**: 2025-12-27
**Spec Reference**: `specs/008-alpha-evolve-templates/spec.md`

## Entities

### EquityPoint

Single equity curve entry recorded during strategy execution.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | datetime | Yes | Bar timestamp when equity was recorded |
| equity | float | Yes | Account equity (balance + unrealized PnL) |

**Notes**:
- Recorded on every `on_bar()` call
- Used for performance analysis post-backtest
- Lightweight (no persistence, in-memory list)

---

### BaseEvolveConfig

Configuration for evolvable strategy base class.

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| instrument_id | InstrumentId | Yes | - | Valid NautilusTrader InstrumentId |
| bar_type | BarType | Yes | - | Valid NautilusTrader BarType |
| trade_size | Decimal | Yes | - | > 0 |

**Notes**:
- Inherits from `StrategyConfig` (frozen=True)
- Extended by concrete strategy configs

---

### MomentumEvolveConfig

Configuration for momentum seed strategy.

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| instrument_id | InstrumentId | Yes | - | Valid NautilusTrader InstrumentId |
| bar_type | BarType | Yes | - | Valid NautilusTrader BarType |
| trade_size | Decimal | Yes | - | > 0 |
| fast_period | int | No | 10 | >= 2 |
| slow_period | int | No | 30 | > fast_period |

**Notes**:
- Extends BaseEvolveConfig
- fast_period must be < slow_period for valid crossover

---

## Class Hierarchy

```
nautilus_trader.trading.strategy.Strategy
    │
    └── BaseEvolveStrategy (abstract)
            │
            ├── MomentumEvolveStrategy (seed)
            │
            └── [Future evolved variants]
```

---

## BaseEvolveStrategy API

### Abstract Methods

```python
def _on_bar_evolved(self, bar: Bar) -> None:
    """
    Handle bar with evolvable decision logic.

    Contains EVOLVE-BLOCK markers for mutation targeting.
    Must be implemented by concrete strategies.
    """
    ...
```

### Concrete Methods

```python
# Equity Tracking
def get_equity_curve(self) -> list[EquityPoint]:
    """Return recorded equity curve."""

# Order Helpers
def _enter_long(self, quantity: Decimal) -> None:
    """Submit market buy, closing short if needed."""

def _enter_short(self, quantity: Decimal) -> None:
    """Submit market sell, closing long if needed."""

def _close_position(self) -> None:
    """Close all positions for configured instrument."""

def _get_position_size(self) -> Decimal:
    """Get current net position size."""

def _get_equity(self) -> float:
    """Get current account equity."""
```

### Lifecycle Methods (Inherited)

```python
def on_start(self) -> None:
    """Initialize instrument, subscribe to bars."""

def on_bar(self, bar: Bar) -> None:
    """
    Handle bar event.

    1. Call _on_bar_evolved(bar)
    2. Record equity point
    """

def on_stop(self) -> None:
    """Cancel orders, close positions."""

def on_reset(self) -> None:
    """Reset indicators and equity curve."""
```

---

## State Transitions

### Strategy Lifecycle

```
INITIALIZED ──on_start()──> RUNNING ──on_stop()──> STOPPED
     │                          │                      │
     │                          │                      │
     └──────────────────on_reset()─────────────────────┘
```

### Position States

```
FLAT ───_enter_long()───> LONG ───_close_position()───> FLAT
  │                         │
  │                         └───_enter_short()───> [closes long] ───> SHORT
  │
  └───_enter_short()───> SHORT ───_close_position()───> FLAT
```

---

## Validation Rules

### BaseEvolveConfig

1. `instrument_id` must be parseable as NautilusTrader InstrumentId
2. `bar_type` must be parseable as NautilusTrader BarType
3. `trade_size` must be > 0

### MomentumEvolveConfig

1. All BaseEvolveConfig rules
2. `fast_period` >= 2
3. `slow_period` > `fast_period`

---

## Example Usage

```python
from decimal import Decimal
from nautilus_trader.model.data import BarType
from nautilus_trader.model.identifiers import InstrumentId

config = MomentumEvolveConfig(
    instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    bar_type=BarType.from_str("BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"),
    trade_size=Decimal("0.1"),
    fast_period=10,
    slow_period=30,
)

strategy = MomentumEvolveStrategy(config)

# After backtest
curve = strategy.get_equity_curve()
for point in curve:
    print(f"{point.timestamp}: ${point.equity:.2f}")
```
