# Quickstart: Stop-Loss & Position Limits

## Installation

The risk module is part of `nautilus_dev`. No additional installation required.

```python
from nautilus_dev.risk import RiskConfig, RiskManager
```

## Basic Usage

### 1. Configure Risk Management

```python
from decimal import Decimal
from nautilus_dev.risk import RiskConfig

# Minimal config: 2% stop-loss
risk_config = RiskConfig(
    stop_loss_pct=Decimal("0.02"),  # 2% stop-loss
)

# Full config example
risk_config = RiskConfig(
    # Stop-Loss
    stop_loss_enabled=True,
    stop_loss_pct=Decimal("0.02"),
    stop_loss_type="market",  # or "limit", "emulated"

    # Position Limits
    max_position_size={
        "BTC/USDT.BINANCE": Decimal("0.5"),
        "ETH/USDT.BINANCE": Decimal("5.0"),
    },
    max_total_exposure=Decimal("10000"),  # $10k max
)
```

### 2. Integrate with Your Strategy

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.events import Event, PositionOpened, PositionClosed
from nautilus_dev.risk import RiskConfig, RiskManager


class MyStrategyConfig(StrategyConfig):
    instrument_id: str
    risk: RiskConfig = RiskConfig()  # Default risk settings


class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig):
        super().__init__(config)
        self.risk_manager = RiskManager(
            config=config.risk,
            strategy=self,
        )

    def on_start(self) -> None:
        # Subscribe to instrument
        self.subscribe_bars(self.config.instrument_id)

    def on_event(self, event: Event) -> None:
        # Delegate position events to risk manager
        self.risk_manager.handle_event(event)

    def on_bar(self, bar: Bar) -> None:
        # Your trading logic here
        if self.should_buy(bar):
            self.buy(bar)

    def buy(self, bar: Bar) -> None:
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=Quantity.from_str("0.1"),
        )

        # Validate against position limits
        if not self.risk_manager.validate_order(order):
            self.log.warning("Order rejected by risk manager")
            return

        self.submit_order(order)
        # RiskManager will automatically create stop-loss on PositionOpened
```

### 3. Run Backtest

```python
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.backtest.config import BacktestRunConfig

config = BacktestRunConfig(
    # ... your backtest config
)

node = BacktestNode(config=config)
node.add_strategy(MyStrategy, MyStrategyConfig(
    instrument_id="BTC/USDT.BINANCE",
    risk=RiskConfig(
        stop_loss_pct=Decimal("0.02"),
        max_position_size={"BTC/USDT.BINANCE": Decimal("0.5")},
    ),
))

result = node.run()
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `stop_loss_enabled` | bool | True | Enable automatic stop-loss |
| `stop_loss_pct` | Decimal | 0.02 | Stop distance (2% = 0.02) |
| `stop_loss_type` | str | "market" | "market", "limit", or "emulated" |
| `trailing_stop` | bool | False | Enable trailing stop |
| `trailing_distance_pct` | Decimal | 0.01 | Trailing distance |
| `max_position_size` | dict | None | Per-instrument limits |
| `max_total_exposure` | Decimal | None | Total portfolio limit |

## Examples

### Fixed Stop-Loss (2%)

```python
RiskConfig(stop_loss_pct=Decimal("0.02"))
```

- LONG @ $100 → stop @ $98
- SHORT @ $100 → stop @ $102

### Trailing Stop

```python
RiskConfig(
    trailing_stop=True,
    trailing_distance_pct=Decimal("0.01"),  # 1% trailing
)
```

- LONG @ $100, price rises to $110 → stop trails to $108.90

### Position Limits Only (No Stop-Loss)

```python
RiskConfig(
    stop_loss_enabled=False,
    max_position_size={"BTC/USDT.BINANCE": Decimal("1.0")},
    max_total_exposure=Decimal("50000"),
)
```

## Troubleshooting

### Stop order triggers immediately (Bybit)

**Problem**: Stop orders fill instantly regardless of price.

**Solution**: Use NautilusTrader nightly with Rust-based Bybit adapter.

```bash
pip install --upgrade nautilus_trader --pre
```

### Binance STOP_MARKET error

**Problem**: `Order type not supported for this endpoint`

**Solution**: Update to nightly version after 2025-12-10.

### Position flip on stop-loss

**Problem**: Stop-loss creates opposite position instead of closing.

**Solution**: Ensure your RiskManager uses `reduce_only=True` (default).

```python
# RiskManager does this automatically:
stop_order = self.order_factory.stop_market(
    ...,
    reduce_only=True,  # Prevents position flip
)
```

## Best Practices

1. **Always use `reduce_only=True`** for stop-loss orders
2. **Validate orders before submission** with `risk_manager.validate_order()`
3. **Use STOP_MARKET** for guaranteed fills (default)
4. **Use nightly NautilusTrader** for Binance/Bybit support
5. **Test with BacktestNode** before live trading

## Related Documentation

- [NautilusTrader Orders](https://docs.nautilustrader.io/nightly/api_reference/model/orders)
- [Spec 011: Stop-Loss & Position Limits](./spec.md)
- [Research: Optimal Stopping Theory](./research.md)
