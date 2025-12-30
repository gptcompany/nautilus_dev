# WebSocket API Contract

**Feature**: 003-tradingview-lightweight-charts
**Version**: 1.0
**Date**: 2025-12-25

## Overview

WebSocket API for real-time streaming of Open Interest, Funding Rates, and Liquidation events from the CCXT pipeline daemon to browser-based dashboards.

## Connection

**Endpoint**: `ws://localhost:8765/ws`

**Protocol**: WebSocket (RFC 6455)

**Subprotocol**: None (JSON messages)

---

## Message Types

### Server → Client Messages

#### 1. OI Update

Sent when new Open Interest data is fetched (every 5 minutes per exchange).

```json
{
  "type": "oi",
  "timestamp": 1703500800000,
  "symbol": "BTCUSDT-PERP",
  "venue": "BINANCE",
  "open_interest": 50000.5,
  "open_interest_value": 2500000000.0
}
```

| Field | Type | Description |
|-------|------|-------------|
| type | string | Always "oi" |
| timestamp | number | Unix milliseconds |
| symbol | string | Trading pair |
| venue | string | Exchange: BINANCE, BYBIT, HYPERLIQUID |
| open_interest | number | OI in base contracts |
| open_interest_value | number | OI value in USD |

---

#### 2. Funding Rate Update

Sent when new funding rate data is fetched (every 60 minutes, or on 8-hour interval).

```json
{
  "type": "funding",
  "timestamp": 1703500800000,
  "symbol": "BTCUSDT-PERP",
  "venue": "BINANCE",
  "funding_rate": 0.0001,
  "next_funding_time": 1703529600000,
  "predicted_rate": 0.00012
}
```

| Field | Type | Description |
|-------|------|-------------|
| type | string | Always "funding" |
| timestamp | number | Unix milliseconds |
| symbol | string | Trading pair |
| venue | string | Exchange name |
| funding_rate | number | Rate as decimal (0.0001 = 0.01%) |
| next_funding_time | number? | Next funding timestamp (ms) |
| predicted_rate | number? | Predicted next rate |

---

#### 3. Liquidation Event

Sent immediately when a liquidation occurs (real-time from exchange WebSocket).

```json
{
  "type": "liquidation",
  "timestamp": 1703500800123,
  "symbol": "BTCUSDT-PERP",
  "venue": "BINANCE",
  "side": "LONG",
  "quantity": 0.5,
  "price": 50000.0,
  "value": 25000.0
}
```

| Field | Type | Description |
|-------|------|-------------|
| type | string | Always "liquidation" |
| timestamp | number | Unix milliseconds |
| symbol | string | Trading pair |
| venue | string | Exchange name |
| side | string | "LONG" or "SHORT" |
| quantity | number | Size liquidated |
| price | number | Liquidation price |
| value | number | USD value |

---

#### 4. Connection Status

Sent on connect and when exchange connection status changes.

```json
{
  "type": "status",
  "connected": true,
  "exchanges": ["BINANCE", "BYBIT", "HYPERLIQUID"],
  "subscribed_symbols": ["BTCUSDT-PERP"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| type | string | Always "status" |
| connected | boolean | True if daemon is running |
| exchanges | string[] | Connected exchanges |
| subscribed_symbols | string[] | Currently subscribed symbols |

---

#### 5. Error

Sent when an error occurs.

```json
{
  "type": "error",
  "code": "INVALID_SYMBOL",
  "message": "Symbol XYZUSDT-PERP not supported"
}
```

| Field | Type | Description |
|-------|------|-------------|
| type | string | Always "error" |
| code | string | Error code |
| message | string | Human-readable message |

**Error Codes**:
- `INVALID_SYMBOL`: Requested symbol not supported
- `DAEMON_NOT_RUNNING`: Backend daemon not available
- `RATE_LIMIT`: Too many requests

---

### Client → Server Messages

#### 1. Subscribe

Subscribe to real-time updates for specified symbols.

```json
{
  "action": "subscribe",
  "symbols": ["BTCUSDT-PERP", "ETHUSDT-PERP"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| action | string | Always "subscribe" |
| symbols | string[] | Symbols to subscribe |

**Response**: Server sends `status` message confirming subscription.

---

#### 2. Unsubscribe

Unsubscribe from specified symbols.

```json
{
  "action": "unsubscribe",
  "symbols": ["ETHUSDT-PERP"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| action | string | Always "unsubscribe" |
| symbols | string[] | Symbols to unsubscribe |

---

#### 3. Ping

Heartbeat to keep connection alive.

```json
{
  "action": "ping"
}
```

**Response**:
```json
{
  "type": "pong",
  "timestamp": 1703500800000
}
```

---

## Connection Lifecycle

```
Client                                    Server
   │                                         │
   │──────── WebSocket Connect ─────────────►│
   │                                         │
   │◄──────── status (initial) ─────────────│
   │                                         │
   │──────── subscribe ─────────────────────►│
   │                                         │
   │◄──────── status (confirmed) ───────────│
   │                                         │
   │◄──────── oi/funding/liquidation ───────│ (continuous)
   │                                         │
   │──────── ping ──────────────────────────►│ (every 30s)
   │◄──────── pong ─────────────────────────│
   │                                         │
   │──────── unsubscribe ───────────────────►│
   │                                         │
   │──────── Close ─────────────────────────►│
   │                                         │
```

---

## Rate Limits

| Message Type | Max Rate |
|--------------|----------|
| Liquidations | 10/second (aggregated if exceeded) |
| OI Updates | ~3/5min (one per exchange) |
| Funding Updates | ~3/60min (one per exchange) |
| Client Pings | 1/30 seconds |

---

## Error Handling

### Connection Errors

- **Close code 1000**: Normal closure
- **Close code 1001**: Server going away
- **Close code 1008**: Policy violation (invalid messages)
- **Close code 1011**: Server error

### Reconnection Strategy

Client should implement exponential backoff:
1. Initial delay: 1 second
2. Max delay: 30 seconds
3. Multiplier: 2x after each failure
4. Reset delay on successful reconnect

---

## Example Session

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8765/ws');

ws.onopen = () => {
  // Subscribe to BTCUSDT
  ws.send(JSON.stringify({
    action: 'subscribe',
    symbols: ['BTCUSDT-PERP']
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  switch (msg.type) {
    case 'oi':
      updateOIChart(msg);
      break;
    case 'funding':
      updateFundingDisplay(msg);
      break;
    case 'liquidation':
      addLiquidationMarker(msg);
      break;
    case 'status':
      updateConnectionStatus(msg);
      break;
    case 'error':
      showError(msg);
      break;
  }
};

// Heartbeat
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'ping' }));
  }
}, 30000);
```
