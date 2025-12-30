# Data Model: Order Reconciliation

**Spec**: 016-order-reconciliation
**Created**: 2025-12-30

## Overview

This data model documents the entities and relationships for order reconciliation configuration. Since we're leveraging NautilusTrader's native reconciliation, most entities are configuration models that wrap existing NautilusTrader types.

## Entity Relationship Diagram

```
┌─────────────────────────────┐
│    ReconciliationConfig     │
│─────────────────────────────│
│ + enabled: bool             │
│ + startup_delay_secs: float │
│ + lookback_mins: int?       │
│ + inflight_check_*: ...     │
│ + open_check_*: ...         │
│ + purge_*: ...              │
└──────────────┬──────────────┘
               │ uses
               ▼
┌─────────────────────────────┐
│   LiveExecEngineConfig      │
│   (NautilusTrader Native)   │
└──────────────┬──────────────┘
               │ part of
               ▼
┌─────────────────────────────┐
│    TradingNodeConfig        │
│─────────────────────────────│
│ + trader_id: str            │
│ + exec_engine: ...          │
│ + cache: CacheConfig        │
│ + strategies: List          │
└──────────────┬──────────────┘
               │ contains
               ▼
┌─────────────────────────────┐
│       CacheConfig           │
│─────────────────────────────│
│ + database: DatabaseConfig  │
│ + persist_account_events    │
└─────────────────────────────┘
```

## Entities

### 1. ReconciliationConfig

**Purpose**: High-level configuration for reconciliation with sensible defaults and validation.

| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| `enabled` | bool | `True` | - | Enable startup reconciliation |
| `startup_delay_secs` | float | `10.0` | `>= 10.0` | Delay before reconciliation starts |
| `lookback_mins` | int? | `None` | `>= 0` or None | History lookback (None = max) |
| `inflight_check_interval_ms` | int | `2000` | `>= 1000` | In-flight order check interval |
| `inflight_check_threshold_ms` | int | `5000` | `>= 1000` | Threshold before venue query |
| `inflight_check_retries` | int | `5` | `>= 1` | Max retry attempts |
| `open_check_interval_secs` | float? | `5.0` | `>= 1.0` or None | Continuous polling interval |
| `open_check_lookback_mins` | int | `60` | `>= 60` | Open order lookback window |
| `open_check_threshold_ms` | int | `5000` | `>= 1000` | Threshold for discrepancy |
| `purge_closed_orders_interval_mins` | int | `10` | `>= 1` | Purge frequency |
| `purge_closed_orders_buffer_mins` | int | `60` | `>= 1` | Grace period before purge |

**Validation Rules**:
- `startup_delay_secs >= 10.0` (community best practice)
- `open_check_lookback_mins >= 60` (never reduce below this)
- `inflight_check_threshold_ms >= inflight_check_interval_ms`

**State Transitions**: N/A (immutable configuration)

---

### 2. ReconciliationPreset (Enum)

**Purpose**: Named presets for common reconciliation scenarios.

| Preset | Description | Key Settings |
|--------|-------------|--------------|
| `CONSERVATIVE` | Safe defaults, longer delays | delay=15s, lookback=120min |
| `STANDARD` | Production recommended | delay=10s, lookback=60min |
| `AGGRESSIVE` | Fast reconciliation | delay=10s, lookback=30min |
| `DISABLED` | Reconciliation off | enabled=False |

---

### 3. ExternalOrderClaimConfig

**Purpose**: Configuration for claiming external orders placed outside NautilusTrader.

| Field | Type | Default | Constraints | Description |
|-------|------|---------|-------------|-------------|
| `instrument_ids` | List[str] | `[]` | Valid instrument ID format | Instruments to claim |
| `claim_all` | bool | `False` | - | Claim all instruments |

**Validation Rules**:
- `instrument_ids` must be valid NautilusTrader instrument ID format (e.g., "BTCUSDT-PERP.BINANCE")
- Cannot set both `claim_all=True` and specific `instrument_ids`

---

### 4. ReconciliationStatus (Runtime State)

**Purpose**: Runtime state for monitoring reconciliation status.

| Field | Type | Description |
|-------|------|-------------|
| `is_reconciled` | bool | Startup reconciliation complete |
| `last_check_time` | datetime? | Last continuous check timestamp |
| `pending_discrepancies` | int | Unresolved discrepancies count |
| `external_orders_count` | int | External orders detected |
| `inflight_orders_count` | int | Orders awaiting confirmation |

**State Transitions**:
```
INITIALIZING -> RECONCILING -> RECONCILED -> MONITORING
                    │                           │
                    └─────── ERROR ─────────────┘
```

---

## Relationships

### ReconciliationConfig → LiveExecEngineConfig
- **Cardinality**: 1:1
- **Type**: Conversion
- **Description**: ReconciliationConfig converts to kwargs for LiveExecEngineConfig

### TradingNodeConfig → CacheConfig
- **Cardinality**: 1:1
- **Type**: Composition
- **Description**: TradingNode requires cache for state persistence

### StrategyConfig → ExternalOrderClaimConfig
- **Cardinality**: 1:0..1
- **Type**: Optional composition
- **Description**: Strategy may have external order claims

---

## NautilusTrader Native Types (Reference)

These are NautilusTrader types we integrate with (not reimplemented):

### LiveExecEngineConfig
Native NautilusTrader configuration for live execution engine. Our `ReconciliationConfig` produces kwargs for this.

### CacheConfig
Native NautilusTrader configuration for caching. We require:
- `database: DatabaseConfig` with Redis connection
- `persist_account_events: True`

### StrategyConfig
Native NautilusTrader base strategy configuration. Extended with:
- `external_order_claims: List[InstrumentId]`

---

## Event Types (Reference)

Reconciliation generates these NautilusTrader events:

| Event | Description | Generated When |
|-------|-------------|----------------|
| `OrderFilled` | Fill event | Missing fill detected |
| `OrderAccepted` | Order acceptance | External order found |
| `OrderRejected` | Order rejection | In-flight timeout |
| `OrderCanceled` | Order cancellation | Pending cancel timeout |
| `PositionChanged` | Position update | Position discrepancy |

---

## Storage Requirements

### Redis Schema

```
# Account events (persist_account_events=True)
nautilus:{trader_id}:events:account:{account_id} -> List[Event]

# Order state
nautilus:{trader_id}:orders:{client_order_id} -> OrderState

# Position state
nautilus:{trader_id}:positions:{instrument_id} -> PositionState
```

### Retention
- Account events: Indefinite (required for recovery)
- Closed orders: Purged after `purge_closed_orders_buffer_mins`
- Closed positions: Configurable purge
