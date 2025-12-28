# Spec 016: Order Reconciliation

## Overview

Implement robust order reconciliation to ensure internal order state matches exchange state after restarts or disconnections.

## Problem Statement

When TradingNode restarts or loses connection, internal order state may diverge from exchange state. Orders may have been filled, cancelled, or modified while disconnected.

## Goals

1. **State Synchronization**: Align internal state with exchange on startup
2. **Continuous Reconciliation**: Periodic checks during operation
3. **Gap Detection**: Identify and handle missing fills

## Requirements

### Functional Requirements

#### FR-001: Startup Reconciliation
- Query all open orders from exchange
- Query recent order history (last 24h)
- Generate missing OrderFilled events
- Update internal positions to match exchange

#### FR-002: Reconciliation Delay
```python
LiveExecEngineConfig(
    reconciliation=True,
    reconciliation_startup_delay_secs=10.0,  # Wait for all accounts to connect
)
```

#### FR-003: Continuous Reconciliation
- Periodic check every N minutes (configurable)
- Compare internal open orders vs exchange
- Alert on discrepancies

#### FR-004: In-Flight Order Monitoring
```python
LiveExecEngineConfig(
    inflight_check_interval_secs=5.0,
    inflight_timeout_ms=5000,
)
```

#### FR-005: External Order Claims
- Claim positions opened outside NautilusTrader
- Configure per strategy:
```python
StrategyConfig(
    external_order_claims=[
        InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    ],
)
```

### Non-Functional Requirements

#### NFR-001: Completeness
- 100% of fills reconciled
- No duplicate fill events

#### NFR-002: Timing
- Startup reconciliation < 30 seconds
- Periodic check < 5 seconds

## Technical Design

### Reconciliation Flow

```
TradingNode Start
        │
        ▼
┌───────────────────┐
│ Wait for accounts │ (reconciliation_startup_delay_secs)
│   to connect      │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Query exchange    │
│ - Open orders     │
│ - Recent fills    │
│ - Positions       │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Compare with      │
│ internal state    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Generate missing  │
│ events            │
│ - OrderFilled     │
│ - PositionChanged │
└────────┬──────────┘
         │
         ▼
    Trading Starts
```

### Configuration
```python
reconciliation_config = LiveExecEngineConfig(
    reconciliation=True,
    reconciliation_startup_delay_secs=10.0,
    reconciliation_interval_secs=300,  # Every 5 minutes
    inflight_check_interval_secs=5.0,
    inflight_timeout_ms=5000,
)
```

### Known Issues (Discord)

#### Binance Futures HEDGING
- Issue #3104: Reconciliation issues in hedge mode
- Workaround: Use one-way mode only

#### External Positions
- Positions opened via web/app may not reconcile correctly
- Use `external_order_claims` to claim them

#### Venue Mismatch
- Issue #3042: Routing client reconciliation when instrument venue differs
- Ensure instrument venue matches execution venue

## Testing Strategy

1. **Startup Tests**: Node restart with open positions
2. **Disconnection Tests**: Network interruption during order lifecycle
3. **Manual Orders**: Orders placed outside NautilusTrader

## Dependencies

- Spec 014 (TradingNode Configuration)
- Spec 015 (Binance Exec Client)
- Spec 018 (Redis Cache for state persistence)

## Success Metrics

- 100% of fills reconciled after restart
- Zero position discrepancies after 24h operation
- Reconciliation alerts when discrepancies found
