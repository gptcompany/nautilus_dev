# Spec 016: Order Reconciliation

## Overview

Implement order reconciliation with 100% fill coverage and < 30s recovery time to ensure internal order state matches exchange state after restarts or disconnections.

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
- Periodic check every 5 seconds (configurable via `open_check_interval_secs`)
- Compare internal open orders vs exchange
- Alert on discrepancies via Grafana dashboard and configured alert rules

#### FR-004: In-Flight Order Monitoring
```python
LiveExecEngineConfig(
    inflight_check_interval_ms=2000,  # Check every 2 seconds
    inflight_check_threshold_ms=5000,  # Query venue after 5s without response
    inflight_check_retries=5,
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
    open_check_interval_secs=5.0,  # Continuous polling every 5 seconds
    open_check_lookback_mins=60,
    inflight_check_interval_ms=2000,
    inflight_check_threshold_ms=5000,
    inflight_check_retries=5,
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
