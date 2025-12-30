# Data Model: Redis Cache Backend (Spec 018)

**Created**: 2025-12-30

---

## Redis Key Schema

### Key Pattern
```
{prefix}-{type}:{identifier}
```

| Component | Description | Example |
|-----------|-------------|---------|
| prefix | `trader` (configurable) | `trader` |
| type | Data type | `position`, `order`, `account` |
| identifier | Unique ID | `BTCUSDT-PERP.BINANCE-001` |

---

## Data Types

### Position
**Key**: `trader-position:{position_id}`

| Field | Redis Type | Description |
|-------|------------|-------------|
| position_id | string | Unique identifier |
| instrument_id | string | Trading instrument |
| strategy_id | string | Owning strategy |
| side | string | LONG/SHORT/FLAT |
| quantity | string | Position size (decimal) |
| avg_px_open | string | Entry price (decimal) |
| ts_opened | int | Open timestamp (ns) |
| ts_last | int | Last update (ns) |

### Order
**Key**: `trader-order:{client_order_id}`

| Field | Redis Type | Description |
|-------|------------|-------------|
| client_order_id | string | Client-assigned ID |
| venue_order_id | string | Exchange ID |
| instrument_id | string | Trading instrument |
| order_type | string | MARKET/LIMIT/STOP |
| side | string | BUY/SELL |
| quantity | string | Order size |
| status | string | Order status |
| events | list | Event history (serialized) |

### Account
**Key**: `trader-account:{account_id}`

| Field | Redis Type | Description |
|-------|------------|-------------|
| account_id | string | Account identifier |
| account_type | string | CASH/MARGIN |
| balances | hash | Currency -> balance |
| margins | hash | Instrument -> margin |

---

## TTL Policy

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Position (open) | None | Must persist |
| Position (closed) | 7 days | Historical reference |
| Order (open) | None | Must persist |
| Order (filled/canceled) | 7 days | Audit trail |
| Account | None | Must persist |
| Instrument | 24 hours | Can be refreshed |
| Tick/Bar | Capacity-based | Memory limit |
