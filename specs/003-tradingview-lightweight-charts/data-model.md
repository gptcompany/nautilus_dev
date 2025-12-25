# Data Model: TradingView Lightweight Charts Dashboard

**Feature**: 003-tradingview-lightweight-charts
**Date**: 2025-12-25

## Entity Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   OIDataPoint   │     │   FundingRate   │     │  Liquidation    │
│─────────────────│     │─────────────────│     │─────────────────│
│ timestamp       │     │ timestamp       │     │ timestamp       │
│ symbol          │     │ symbol          │     │ symbol          │
│ venue           │     │ venue           │     │ venue           │
│ open_interest   │     │ funding_rate    │     │ side            │
│ oi_value        │     │ next_funding    │     │ quantity        │
└────────┬────────┘     └────────┬────────┘     │ price           │
         │                       │              │ value           │
         │                       │              └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │     ChartDataPoint     │
                    │────────────────────────│
                    │ time: number (unix s)  │
                    │ value: number          │
                    └────────────────────────┘
```

## Entities

### 1. OIDataPoint (Reused from Spec 001)

**Source**: `scripts/ccxt_pipeline/models/open_interest.py`

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| timestamp | datetime | When recorded (UTC) | Not in future |
| symbol | string | Trading pair ("BTCUSDT-PERP") | Not empty, uppercase |
| venue | Venue | Exchange name | BINANCE, BYBIT, HYPERLIQUID |
| open_interest | float | OI in base contracts | >= 0 |
| open_interest_value | float | OI value in USD | >= 0 |

**Chart Mapping**:
```javascript
// Python OIDataPoint → JS ChartDataPoint
{
  time: Math.floor(timestamp.getTime() / 1000),  // Unix seconds
  value: open_interest_value  // Use USD value for better comparison
}
```

---

### 2. FundingRate (Reused from Spec 001)

**Source**: `scripts/ccxt_pipeline/models/funding_rate.py`

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| timestamp | datetime | Funding time (UTC) | Not in future |
| symbol | string | Trading pair | Not empty |
| venue | Venue | Exchange name | Enum |
| funding_rate | float | Rate as decimal | e.g., 0.0001 = 0.01% |
| next_funding_time | datetime? | Next funding | Optional |
| predicted_rate | float? | Predicted next | Optional |

**Chart Mapping**:
```javascript
// Convert to percentage for display
{
  time: Math.floor(timestamp.getTime() / 1000),
  value: funding_rate * 100  // Display as percentage
}
```

**Color Logic**:
```javascript
const color = funding_rate > 0 ? '#ff5722' : '#4caf50';  // Red if positive
```

---

### 3. Liquidation (Reused from Spec 001)

**Source**: `scripts/ccxt_pipeline/models/liquidation.py`

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| timestamp | datetime | When occurred (UTC) | Not in future |
| symbol | string | Trading pair | Not empty |
| venue | Venue | Exchange name | Enum |
| side | Side | Position liquidated | LONG, SHORT |
| quantity | float | Size | > 0 |
| price | float | Liquidation price | > 0 |
| value | float | USD value | > 0 |

**Chart Mapping** (as marker):
```javascript
// Liquidation → Chart Marker
{
  time: Math.floor(timestamp.getTime() / 1000),
  position: side === 'LONG' ? 'belowBar' : 'aboveBar',
  color: side === 'LONG' ? '#f44336' : '#00c853',
  shape: side === 'LONG' ? 'arrowDown' : 'arrowUp',
  text: `${side} $${(value / 1000).toFixed(0)}K`
}
```

---

### 4. ChartDataPoint (Frontend)

**Purpose**: TradingView Lightweight Charts native format

| Field | Type | Description |
|-------|------|-------------|
| time | number | Unix timestamp (seconds) |
| value | number | Y-axis value |

**Note**: Lightweight Charts expects time in **seconds**, not milliseconds.

---

### 5. WebSocketMessage (Transport)

**Purpose**: JSON messages between server and browser

#### Server → Client

```typescript
// OI Update
{
  "type": "oi",
  "timestamp": 1703500800000,  // Unix ms
  "symbol": "BTCUSDT-PERP",
  "venue": "BINANCE",
  "open_interest": 50000.5,
  "open_interest_value": 2500000000.0
}

// Funding Update
{
  "type": "funding",
  "timestamp": 1703500800000,
  "symbol": "BTCUSDT-PERP",
  "venue": "BINANCE",
  "funding_rate": 0.0001,
  "next_funding_time": 1703529600000
}

// Liquidation Event
{
  "type": "liquidation",
  "timestamp": 1703500800000,
  "symbol": "BTCUSDT-PERP",
  "venue": "BINANCE",
  "side": "LONG",
  "quantity": 0.5,
  "price": 50000.0,
  "value": 25000.0
}

// Connection Status
{
  "type": "status",
  "connected": true,
  "exchanges": ["BINANCE", "BYBIT", "HYPERLIQUID"]
}
```

#### Client → Server

```typescript
// Subscribe to symbols
{
  "action": "subscribe",
  "symbols": ["BTCUSDT-PERP", "ETHUSDT-PERP"]
}

// Unsubscribe
{
  "action": "unsubscribe",
  "symbols": ["ETHUSDT-PERP"]
}
```

---

### 6. DashboardState (Frontend)

**Purpose**: Track UI state

```typescript
interface DashboardState {
  currentSymbol: string;        // "BTCUSDT-PERP"
  connectionStatus: "connected" | "reconnecting" | "disconnected";
  chartZoom: { from: number; to: number };  // Visible range
  dataBuffers: {
    oi: ChartDataPoint[];
    funding: ChartDataPoint[];
    liquidations: ChartMarker[];
  };
}
```

---

## Relationships

```
WebSocketMessage (1) ──────► (1) OIDataPoint | FundingRate | Liquidation
         │
         │ parse
         ▼
ChartDataPoint (1) ◄──────── (1) OIDataPoint | FundingRate
ChartMarker (1) ◄──────────── (1) Liquidation
         │
         │ render
         ▼
TradingView Chart
```

---

## Validation Rules

### Time Validation
- All timestamps must be within 24 hours of current time for real-time data
- Historical data allows timestamps up to 1 year old

### Value Validation
- OI values: >= 0
- Funding rates: typically -0.05 to +0.05 (but allow extremes)
- Liquidation values: > 0

### Symbol Validation
- Must match pattern: `[A-Z]+USDT-PERP`
- Supported: BTCUSDT-PERP, ETHUSDT-PERP

---

## State Transitions

### Connection State

```
DISCONNECTED ──► CONNECTING ──► CONNECTED
      ▲               │              │
      │               │              │
      └───────────────┴──────────────┘
            (on error/timeout)
```

### Data Flow State

```
INITIAL ──► LOADING_HISTORY ──► STREAMING ──► PAUSED (tab inactive)
                                    │              │
                                    └──────────────┘
                                       (tab active)
```
