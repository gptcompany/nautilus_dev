# Data Model: CCXT Multi-Exchange Data Pipeline

**Created**: 2025-12-22
**Status**: Complete

## Entity Definitions

### OpenInterest

Represents the total number of outstanding derivative contracts at a point in time.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `timestamp` | datetime | When the data was recorded | Required, UTC |
| `symbol` | str | Unified symbol (e.g., "BTCUSDT-PERP") | Required, non-empty |
| `venue` | str | Exchange name (e.g., "BINANCE") | Required, enum |
| `open_interest` | float | OI in base currency contracts | Required, >= 0 |
| `open_interest_value` | float | OI value in USD | Required, >= 0 |

**Relationships**: None

**State Transitions**: None (immutable time-series data)

---

### FundingRate

Represents the periodic payment rate between longs and shorts on perpetual contracts.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `timestamp` | datetime | When the funding was applied | Required, UTC |
| `symbol` | str | Unified symbol | Required, non-empty |
| `venue` | str | Exchange name | Required, enum |
| `funding_rate` | float | Rate as decimal (e.g., 0.0001 = 0.01%) | Required |
| `next_funding_time` | datetime | Next funding timestamp | Optional |
| `predicted_rate` | float | Predicted next rate | Optional |

**Relationships**: None

**State Transitions**: None (immutable time-series data)

**Notes**:
- Funding rate can be positive (longs pay shorts) or negative (shorts pay longs)
- Funding intervals vary: 8h (Binance, Bybit), variable (Hyperliquid)

---

### Liquidation

Represents a forced position closure event.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `timestamp` | datetime | When liquidation occurred | Required, UTC |
| `symbol` | str | Unified symbol | Required, non-empty |
| `venue` | str | Exchange name | Required, enum |
| `side` | str | Position side liquidated | Required, "LONG" or "SHORT" |
| `quantity` | float | Size of liquidated position | Required, > 0 |
| `price` | float | Liquidation price | Required, > 0 |
| `value` | float | USD value of liquidation | Required, > 0 |

**Relationships**: None

**State Transitions**: None (immutable event data)

---

### Exchange (Configuration)

Represents a supported trading venue configuration.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `name` | str | Exchange identifier | Required, enum |
| `ccxt_id` | str | CCXT exchange ID | Required |
| `supports_oi` | bool | OI fetching supported | Default: True |
| `supports_oi_history` | bool | Historical OI supported | Default: True |
| `supports_funding` | bool | Funding rates supported | Default: True |
| `supports_liquidations_ws` | bool | WebSocket liquidations | Varies |
| `rate_limit_per_minute` | int | API rate limit | Required, > 0 |

**Supported Exchanges**:

| Name | CCXT ID | OI | OI History | Funding | Liq WS |
|------|---------|----|-----------| --------|--------|
| BINANCE | binance | ✅ | ✅ | ✅ | ✅ |
| BYBIT | bybit | ✅ | ⚠️ (200 limit) | ✅ | ✅ |
| HYPERLIQUID | hyperliquid | ✅ | ✅ | ✅ | ❓ |

---

## Storage Schema

### Directory Structure

```
/data/ccxt_catalog/
├── open_interest/
│   ├── BTCUSDT-PERP.BINANCE/
│   │   ├── 2025-01-01.parquet
│   │   ├── 2025-01-02.parquet
│   │   └── ...
│   ├── BTCUSDT-PERP.BYBIT/
│   └── BTC-USD-PERP.HYPERLIQUID/
├── funding_rate/
│   ├── BTCUSDT-PERP.BINANCE/
│   └── ...
└── liquidations/
    ├── BTCUSDT-PERP.BINANCE/
    └── ...
```

### Parquet Schema

**OpenInterest**:
```
timestamp: timestamp[us, tz=UTC]
symbol: string
venue: string
open_interest: float64
open_interest_value: float64
```

**FundingRate**:
```
timestamp: timestamp[us, tz=UTC]
symbol: string
venue: string
funding_rate: float64
next_funding_time: timestamp[us, tz=UTC] (nullable)
predicted_rate: float64 (nullable)
```

**Liquidation**:
```
timestamp: timestamp[us, tz=UTC]
symbol: string
venue: string
side: string
quantity: float64
price: float64
value: float64
```

---

## Validation Rules

### Symbol Format

- Must match pattern: `{BASE}{QUOTE}-PERP.{VENUE}` or `{BASE}-{QUOTE}-PERP.{VENUE}`
- Examples: `BTCUSDT-PERP.BINANCE`, `BTC-USD-PERP.HYPERLIQUID`

### Timestamp Rules

- All timestamps in UTC
- No future timestamps allowed
- Microsecond precision

### Numeric Rules

- `open_interest` >= 0
- `open_interest_value` >= 0
- `quantity` > 0
- `price` > 0
- `value` > 0
- `funding_rate` can be negative
