# Spec 017: Position Recovery

## Overview

Implement position state recovery after TradingNode restart, ensuring strategies resume with correct position state.

## Problem Statement

When TradingNode restarts, strategies need to know their current positions to make correct trading decisions. Without proper recovery, strategies may open duplicate positions or miss exit signals.

## Goals

1. **Position Restoration**: Load positions from cache on startup
2. **Strategy State**: Restore strategy-specific state (indicators, signals)
3. **Seamless Resume**: Trading continues without manual intervention

## Requirements

### Functional Requirements

#### FR-001: Position Loading
- Load positions from Redis cache on startup
- Verify against exchange positions (via reconciliation)
- Resolve discrepancies

#### FR-002: Strategy State Restoration
- Restore indicator warmup state (via historical data request)
- Restore pending order references (stop-loss, take-profit orders)
- Restore custom strategy state (user-defined variables, signal flags, position tracking state)

#### FR-003: Account Balance Restoration
- Load last known balances from cache
- Update with current exchange balances
- Track balance changes during downtime

#### FR-004: Event Replay (Optional)
- Replay missed events from cache
- Generate synthetic events for gap filling
- Maintain event sequence

### Non-Functional Requirements

#### NFR-001: Recovery Time
- Position recovery < 5 seconds (p95)
- Full state recovery < 30 seconds (p95)

#### NFR-002: Consistency
- No duplicate orders after recovery
- Position sizes match exchange exactly

## Technical Design

### Cache Schema for Positions

```python
# Redis key structure
# positions:{trader_id}:{venue}:{instrument_id}

position_data = {
    "instrument_id": "BTCUSDT-PERP.BINANCE",
    "side": "LONG",
    "quantity": "0.5",
    "avg_entry_price": "42500.00",
    "unrealized_pnl": "150.00",
    "realized_pnl": "0.00",
    "ts_opened": 1703721600000000000,
    "ts_last_updated": 1703725200000000000,
}
```

### Recovery Flow

```
TradingNode Start
        │
        ▼
┌───────────────────┐
│ Load positions    │
│ from Redis cache  │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Reconcile with    │ (Spec 016)
│ exchange state    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Restore strategy  │
│ references        │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Warm up           │
│ indicators        │
└────────┬──────────┘
         │
         ▼
    Strategy Ready
```

### Strategy Recovery Pattern

```python
class RecoverableStrategy(Strategy):
    """Base class for strategies with recovery support."""

    def on_start(self) -> None:
        # Check if we have existing positions (use cache, not portfolio)
        positions = self.cache.positions(instrument_id=self.instrument_id)
        if positions:
            self._restore_state(positions)
        else:
            self._initialize_fresh()

    def _restore_state(self, positions: list[Position]) -> None:
        """Restore strategy state from existing positions."""
        for position in positions:
            self.log.info(f"Recovered position: {position}")
            # Restore stop-loss orders if needed
            self._restore_stop_loss(position)

    def _restore_stop_loss(self, position: Position) -> None:
        """Recreate stop-loss order for recovered position."""
        # Check if stop-loss already exists
        open_orders = self.cache.orders_open(instrument_id=position.instrument_id)
        has_stop = any(o.type == OrderType.STOP_MARKET for o in open_orders)

        if not has_stop and position.is_open:
            # Create new stop-loss
            self.risk_manager.create_stop_loss(position)
```

### Cache Persistence Configuration

```python
CacheConfig(
    database=DatabaseConfig(
        type="redis",
        host="localhost",
        port=6379,
    ),
    persist_account_events=True,  # CRITICAL
    buffer_interval_ms=100,
)
```

## Testing Strategy

1. **Cold Start**: Node start with no prior state
2. **Warm Start**: Node restart with existing positions
3. **Position Mismatch**: Recovery when cache differs from exchange
4. **Strategy State**: Custom state recovery validation

## Dependencies

- Spec 016 (Order Reconciliation)
- Spec 018 (Redis Cache Backend)

## Success Metrics

- Position recovery accuracy: 100%
- Recovery time < 30 seconds
- Zero duplicate orders after recovery
