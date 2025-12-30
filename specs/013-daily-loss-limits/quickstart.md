# Quickstart: Daily Loss Limits (Spec 013)

## Prerequisites

- NautilusTrader nightly v1.222.0+
- Spec 011 (Stop-Loss) implemented
- Spec 012 (Circuit Breaker) implemented

## Basic Usage

### 1. Configure Daily Loss Limits

```python
from decimal import Decimal
from risk import DailyLossConfig, DailyPnLTracker

# Absolute limit: $1000 daily loss max
config = DailyLossConfig(
    daily_loss_limit=Decimal("1000"),
    reset_time_utc="00:00",
    close_positions_on_limit=True,
)

# OR percentage limit: 2% of starting capital
config = DailyLossConfig(
    daily_loss_pct=Decimal("0.02"),
    reset_time_utc="00:00",
)
```

### 2. Integrate with Strategy

```python
from nautilus_trader.trading.strategy import Strategy
from risk import DailyLossConfig, DailyPnLTracker, RiskManager

class MyStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)

        # Create daily PnL tracker
        daily_config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
        self.daily_tracker = DailyPnLTracker(
            config=daily_config,
            strategy=self,
        )

        # Optionally integrate with RiskManager
        self.risk_manager = RiskManager(
            config=risk_config,
            strategy=self,
            daily_tracker=self.daily_tracker,
        )

    def on_event(self, event):
        # Route events to tracker
        self.daily_tracker.handle_event(event)

    def on_bar(self, bar):
        # Check if trading allowed
        if not self.daily_tracker.can_trade():
            return  # Daily limit hit, skip trading

        # Your trading logic here
        ...
```

### 3. Monitor Daily PnL

```python
# Check current state
print(f"Realized today: ${self.daily_tracker.daily_realized}")
print(f"Unrealized: ${self.daily_tracker.daily_unrealized}")
print(f"Total PnL: ${self.daily_tracker.total_daily_pnl}")
print(f"Limit triggered: {self.daily_tracker.limit_triggered}")
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `daily_loss_limit` | Decimal | 1000 | Absolute limit (USD) |
| `daily_loss_pct` | Decimal | None | % of starting capital |
| `reset_time_utc` | str | "00:00" | Daily reset time |
| `per_strategy` | bool | False | Per-strategy vs global |
| `close_positions_on_limit` | bool | True | Auto-close on trigger |
| `warning_threshold_pct` | Decimal | 0.5 | Alert at 50% of limit |

## Integration with Circuit Breaker

Daily loss limits work alongside circuit breaker for layered protection:

```python
from risk import CircuitBreaker, CircuitBreakerConfig, DailyPnLTracker

# Circuit breaker: protects against total drawdown
circuit_config = CircuitBreakerConfig(
    level1_drawdown_pct=Decimal("0.10"),  # 10% warning
    level3_drawdown_pct=Decimal("0.20"),  # 20% halt
)
circuit_breaker = CircuitBreaker(config=circuit_config, portfolio=portfolio)

# Daily tracker: protects against single-day losses
daily_config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
daily_tracker = DailyPnLTracker(config=daily_config, strategy=self)

# Check both before trading
def can_open_position(self) -> bool:
    return (
        circuit_breaker.can_open_position() and
        daily_tracker.can_trade()
    )
```

## Testing

```python
import pytest
from decimal import Decimal
from risk import DailyLossConfig, DailyPnLTracker

def test_limit_triggers():
    config = DailyLossConfig(daily_loss_limit=Decimal("100"))
    tracker = DailyPnLTracker(config=config, strategy=mock_strategy)

    # Simulate loss
    tracker._add_realized(-Decimal("150"))

    assert tracker.limit_triggered is True
    assert tracker.can_trade() is False
```
