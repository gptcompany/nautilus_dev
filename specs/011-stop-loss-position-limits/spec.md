# Spec 011: Stop-Loss & Position Limits

## Overview

Implement core risk management controls for NautilusTrader strategies: automatic stop-loss orders and position size limits.

## Problem Statement

Current strategies in alpha-evolve have NO stop-loss protection. A single bad trade can wipe out the account. Position sizes are configurable but not enforced at the risk engine level.

## Goals

1. **Automatic Stop-Loss**: Every entry generates a corresponding stop-loss order
2. **Position Limits**: Enforce max position size per instrument
3. **Integration**: Works with both BacktestNode and TradingNode

## Requirements

### Functional Requirements

#### FR-001: Stop-Loss Order Generation
- When a position is opened, automatically submit a stop-loss order
- Stop-loss price = entry_price * (1 - stop_loss_pct) for LONG
- Stop-loss price = entry_price * (1 + stop_loss_pct) for SHORT
- Configurable stop_loss_pct (default: 2%)

#### FR-002: Position Size Limits
- Max position size per instrument (configurable)
- Max total exposure across all instruments (configurable)
- Reject orders that would exceed limits

#### FR-003: Stop-Loss Types
- Support STOP_MARKET (default, guaranteed fill)
- Support STOP_LIMIT (optional, better price but may not fill)
- Trailing stop-loss (optional, advanced)

#### FR-004: Configuration
```python
class RiskConfig(BaseModel):
    stop_loss_pct: Decimal = Decimal("0.02")  # 2%
    stop_loss_type: Literal["market", "limit"] = "market"
    max_position_size: Decimal | None = None
    max_total_exposure: Decimal | None = None
    trailing_stop: bool = False
    trailing_distance_pct: Decimal = Decimal("0.01")
```

### Non-Functional Requirements

#### NFR-001: Performance
- Stop-loss order must be submitted within 10ms of entry fill
- No impact on strategy execution speed

#### NFR-002: Reliability
- Stop-loss must survive strategy restart
- OCO (One-Cancels-Other) pairing with take-profit if applicable

## Technical Design

### Component: RiskManager

```python
class RiskManager:
    """Manages stop-loss and position limits for strategies."""

    def __init__(self, config: RiskConfig, strategy: Strategy):
        self.config = config
        self.strategy = strategy
        self.active_stops: dict[PositionId, OrderId] = {}

    def on_position_opened(self, event: PositionOpened) -> None:
        """Generate stop-loss when position opens."""
        stop_price = self._calculate_stop_price(event)
        stop_order = self._create_stop_order(event.position, stop_price)
        self.strategy.submit_order(stop_order)
        self.active_stops[event.position.id] = stop_order.client_order_id

    def on_position_closed(self, event: PositionClosed) -> None:
        """Cancel stop-loss when position closes."""
        if event.position.id in self.active_stops:
            self.strategy.cancel_order(self.active_stops[event.position.id])
            del self.active_stops[event.position.id]

    def validate_order(self, order: Order) -> bool:
        """Check if order would exceed position limits."""
        # Implementation
```

### Integration Pattern

```python
class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig):
        super().__init__(config)
        self.risk_manager = RiskManager(config.risk, self)

    def on_event(self, event: Event) -> None:
        if isinstance(event, PositionOpened):
            self.risk_manager.on_position_opened(event)
        elif isinstance(event, PositionClosed):
            self.risk_manager.on_position_closed(event)
```

## Known Issues (from Discord)

### Bybit Stop-Loss Bug
- Stop-loss orders were triggering immediately due to incorrect trigger direction
- **Fix**: STOP BUY triggers when price >= trigger price
- For SHORT position stop-loss: trigger price must be ABOVE entry

### Binance STOP_MARKET
- Requires Algo Order API (fixed in development wheels)
- Use latest nightly version

## Testing Strategy

1. **Unit Tests**: RiskManager logic
2. **Integration Tests**: BacktestNode with stop-loss execution
3. **Edge Cases**: Gap through stop, partial fills, position flip

## Dependencies

- NautilusTrader nightly v1.222.0+
- Spec 008 (BaseEvolveStrategy) for integration

## Success Metrics

- 100% of positions have corresponding stop-loss
- Zero positions exceed configured limits
- Stop-loss execution latency < 10ms
