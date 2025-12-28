# Spec 011: Stop-Loss & Position Limits

## Overview

Implement core risk management controls for NautilusTrader strategies: automatic stop-loss orders and position size limits.

## Problem Statement

Current strategies in alpha-evolve have NO stop-loss protection. A single bad trade can wipe out the account. Position sizes are configurable but not enforced at the risk engine level.

## Goals

1. **Automatic Stop-Loss**: Every entry generates a corresponding stop-loss order
2. **Position Limits**: Enforce max position size per instrument
3. **Integration**: Works with both BacktestNode and TradingNode

## User Stories

### US1: Automatic Stop-Loss (P1 - MVP)
**As a** trader running a strategy,
**I want** every position to automatically have a stop-loss order,
**So that** I am protected from catastrophic losses on any single trade.

**Acceptance Criteria**:
- [ ] When PositionOpened event fires, stop-loss order submitted within same event loop
- [ ] Stop price calculated correctly for LONG (below entry) and SHORT (above entry)
- [ ] Stop order uses `reduce_only=True` to prevent position flip
- [ ] When position closes (manually or via TP), stop order is cancelled

### US2: Position Limits (P2)
**As a** risk manager,
**I want** to enforce maximum position sizes per instrument and total exposure,
**So that** no single position or aggregate exposure exceeds predefined limits.

**Acceptance Criteria**:
- [ ] Orders exceeding per-instrument limit are rejected with clear message
- [ ] Orders exceeding total exposure limit are rejected with clear message
- [ ] Valid orders within limits are approved

### US3: Integration Testing (P3)
**As a** developer,
**I want** to verify risk management works end-to-end with BacktestNode,
**So that** I can trust the system before live deployment.

**Acceptance Criteria**:
- [ ] Stop-loss executes correctly when price drops below trigger
- [ ] Gap-through scenarios handled (price gaps past stop)
- [ ] Position limit rejections work in backtest context
- [ ] Multiple positions maintain separate stops

### US4: Advanced Features (P4 - Optional)
**As a** trader with sophisticated strategies,
**I want** trailing stops and STOP_LIMIT order types,
**So that** I can lock in profits and have more control over execution.

**Acceptance Criteria**:
- [ ] Trailing stop updates on favorable price moves
- [ ] STOP_LIMIT orders created with correct limit price offset
- [ ] PositionChanged events properly update trailing stops

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

> **Canonical Definition**: See `plan.md` → Configuration section for full RiskConfig model.
> See `data-model.md` for detailed field descriptions and validation rules.

```python
class RiskConfig(BaseModel):
    # Stop-Loss Settings
    stop_loss_enabled: bool = True
    stop_loss_pct: Decimal = Decimal("0.02")  # 2%
    stop_loss_type: Literal["market", "limit", "emulated"] = "market"

    # Trailing Stop (optional)
    trailing_stop: bool = False
    trailing_distance_pct: Decimal = Decimal("0.01")

    # Position Limits
    max_position_size: dict[str, Decimal] | None = None  # Per instrument
    max_total_exposure: Decimal | None = None
```

### Non-Functional Requirements

#### NFR-001: Performance
- Stop-loss order must be submitted within 10ms of entry fill (**live trading only** - backtest is synchronous)
- No impact on strategy execution speed

#### NFR-002: Reliability
- **MVP Scope (Backtest)**: Stop-loss state maintained in memory (`active_stops` dict) - no persistence required
- **Future Scope (Live Trading)**: Stop-loss state persisted to Redis/DB for restart recovery (out of MVP scope)
- OCO (One-Cancels-Other) pairing with take-profit: **Out of MVP scope** - manual cancellation via `on_order_filled()` event handler

## Technical Design

### Component: RiskManager

```python
class RiskManager:
    """Manages stop-loss and position limits for strategies."""

    def __init__(self, config: RiskConfig, strategy: Strategy):
        self.config = config
        self.strategy = strategy
        self.active_stops: dict[PositionId, ClientOrderId] = {}  # Maps position to stop order

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

### Edge Case: Partial Fills

**Scenario**: Order partially filled, creating position smaller than requested.

**Behavior**:
- PositionOpened fires with actual filled quantity
- Stop-loss created for actual position size (not requested size)
- No special handling needed - NautilusTrader events reflect actual fills

## Dependencies

- NautilusTrader nightly v1.222.0+
- Spec 008 (BaseEvolveStrategy) for integration

## Success Metrics

- 100% of positions have corresponding stop-loss
- Zero positions exceed configured limits
- Stop-loss execution latency < 10ms
