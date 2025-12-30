# Research: Daily Loss Limits (Spec 013)

**Date**: 2025-12-28
**Status**: Complete

## Research Questions

### RQ-001: How to track realized PnL from closed positions?

**Decision**: Use `PositionClosed.realized_pnl` property

**Rationale**:
- NautilusTrader fires `PositionClosed` event when positions close
- Event contains `realized_pnl: Money` property with closed PnL
- Already used in `risk/manager.py` → `_on_position_closed()`

**API**:
```python
def on_event(self, event: Event) -> None:
    if isinstance(event, PositionClosed):
        realized_pnl = event.realized_pnl  # Money object
        pnl_value = float(realized_pnl)  # Convert to float
```

**Alternatives considered**:
- Compute PnL from fills manually → More complex, error-prone
- Use portfolio.realized_pnls() → Aggregate only, no per-position granularity

**Source**: Discord help.md:1026, NautilusTrader position.pyx

---

### RQ-002: How to get unrealized PnL for open positions?

**Decision**: Use `portfolio.unrealized_pnls(venue)` or `position.unrealized_pnl(price)`

**Rationale**:
- Portfolio provides aggregate unrealized PnL per venue
- Position provides per-position unrealized PnL given current price

**API**:
```python
# Aggregate (venue-level)
unrealized = self.portfolio.unrealized_pnls(venue)

# Per-position (requires current price)
last_quote = self.cache.quote_tick(position.instrument_id)
unrealized = position.unrealized_pnl(last_quote.bid_price)
```

**Caveats**:
- Discord: Race condition on restart - portfolio venue mapping may fail if account not yet registered
- Must handle None returns gracefully

**Source**: Discord questions.md:2894-2922

---

### RQ-003: How to implement daily reset at specific time?

**Decision**: Use `clock.set_timer()` with daily interval

**Rationale**:
- NautilusTrader provides `clock.set_timer()` for scheduled callbacks
- Can specify time with `at_time` parameter for specific UTC time

**API**:
```python
def on_start(self):
    # Set daily timer at 00:00 UTC
    self.clock.set_timer(
        name="daily_reset",
        interval=timedelta(days=1),
        callback=self._on_daily_reset,
        start_time=self._next_reset_time(),  # Calculate next 00:00 UTC
    )

def _on_daily_reset(self, event: TimeEvent) -> None:
    """Reset daily PnL counters."""
    self.daily_realized = Decimal("0")
    self.limit_triggered = False
```

**Alternatives considered**:
- Check time on every bar → Inefficient, may miss exact reset
- External scheduler (cron) → Adds external dependency

---

### RQ-004: Architecture integration with existing risk module?

**Decision**: Extend existing `risk/` module with `DailyPnLTracker` class

**Rationale**:
- Follows established pattern from `RiskManager` and `CircuitBreaker`
- Shares config patterns with `RiskConfig`, `CircuitBreakerConfig`
- Can integrate with RiskManager.handle_event() for event routing

**Integration Pattern**:
```python
class RiskManager:
    def __init__(self, ..., daily_tracker: DailyPnLTracker | None = None):
        self._daily_tracker = daily_tracker

    def handle_event(self, event: Event) -> None:
        # Existing handlers...
        if self._daily_tracker:
            self._daily_tracker.handle_event(event)
```

**File Structure**:
```
risk/
├── __init__.py              # Add DailyPnLTracker export
├── daily_pnl_tracker.py     # NEW: Core implementation
├── daily_loss_config.py     # NEW: Configuration model
├── manager.py               # Extend to integrate tracker
```

---

### RQ-005: How to close all positions on limit trigger?

**Decision**: Reuse stop-loss pattern from RiskManager

**Rationale**:
- RiskManager already has position closure logic via stop orders
- Can emit market orders for immediate closure
- Use `reduce_only=True` to prevent position flip

**API**:
```python
def _close_all_positions(self) -> None:
    """Close all positions when daily limit triggered."""
    for position in self.strategy.cache.positions_open():
        close_order = self.strategy.order_factory.market(
            instrument_id=position.instrument_id,
            order_side=OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY,
            quantity=position.quantity,
            reduce_only=True,
        )
        self.strategy.submit_order(close_order)
```

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Spec 005 (QuestDB Monitoring) | Available | For daily_pnl table |
| Spec 011 (Stop-Loss) | Implemented | risk/manager.py |
| Spec 012 (Circuit Breaker) | Implemented | risk/circuit_breaker.py |
| NautilusTrader nightly | v1.222.0+ | Required for position events |

## Open Questions

None - all clarifications resolved.
