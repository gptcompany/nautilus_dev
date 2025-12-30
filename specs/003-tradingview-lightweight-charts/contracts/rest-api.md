# REST API Contract

**Feature**: 003-tradingview-lightweight-charts
**Version**: 1.0
**Date**: 2025-12-25

## Overview

REST API for serving historical data and status information to the dashboard.

**Base URL**: `http://localhost:8765/api`

**Content-Type**: `application/json`

---

## Endpoints

### GET /api/symbols

List available trading symbols.

**Request**:
```http
GET /api/symbols
```

**Response** (200 OK):
```json
{
  "symbols": [
    {
      "symbol": "BTCUSDT-PERP",
      "name": "Bitcoin Perpetual",
      "exchanges": ["BINANCE", "BYBIT", "HYPERLIQUID"]
    },
    {
      "symbol": "ETHUSDT-PERP",
      "name": "Ethereum Perpetual",
      "exchanges": ["BINANCE", "BYBIT", "HYPERLIQUID"]
    }
  ]
}
```

---

### GET /api/status

Server health check and daemon status.

**Request**:
```http
GET /api/status
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "daemon_running": true,
  "uptime_seconds": 3600,
  "last_fetch": "2025-12-25T12:00:00Z",
  "connected_exchanges": ["BINANCE", "BYBIT", "HYPERLIQUID"],
  "fetch_count": 720,
  "error_count": 2,
  "liquidation_count": 1500
}
```

**Response** (503 Service Unavailable):
```json
{
  "status": "unhealthy",
  "daemon_running": false,
  "error": "DaemonRunner not started"
}
```

---

### GET /api/history/oi

Fetch historical Open Interest data.

**Request**:
```http
GET /api/history/oi?symbol=BTCUSDT-PERP&from=2025-01-01&to=2025-01-31&venue=BINANCE
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Trading pair (e.g., BTCUSDT-PERP) |
| from | string | Yes | Start date (ISO 8601 or YYYY-MM-DD) |
| to | string | Yes | End date (ISO 8601 or YYYY-MM-DD) |
| venue | string | No | Filter by exchange |
| limit | number | No | Max records (default: 10000) |

**Response** (200 OK):
```json
{
  "symbol": "BTCUSDT-PERP",
  "from": "2025-01-01T00:00:00Z",
  "to": "2025-01-31T23:59:59Z",
  "count": 8928,
  "data": [
    {
      "timestamp": 1704067200000,
      "venue": "BINANCE",
      "open_interest": 50000.5,
      "open_interest_value": 2500000000.0
    },
    {
      "timestamp": 1704067500000,
      "venue": "BINANCE",
      "open_interest": 50100.2,
      "open_interest_value": 2505000000.0
    }
  ]
}
```

**Response** (400 Bad Request):
```json
{
  "error": "INVALID_DATE_RANGE",
  "message": "from date must be before to date"
}
```

**Response** (404 Not Found):
```json
{
  "error": "NO_DATA",
  "message": "No OI data found for BTCUSDT-PERP in specified range"
}
```

---

### GET /api/history/funding

Fetch historical funding rate data.

**Request**:
```http
GET /api/history/funding?symbol=BTCUSDT-PERP&from=2025-01-01&to=2025-01-31
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Trading pair |
| from | string | Yes | Start date |
| to | string | Yes | End date |
| venue | string | No | Filter by exchange |
| limit | number | No | Max records (default: 1000) |

**Response** (200 OK):
```json
{
  "symbol": "BTCUSDT-PERP",
  "from": "2025-01-01T00:00:00Z",
  "to": "2025-01-31T23:59:59Z",
  "count": 93,
  "data": [
    {
      "timestamp": 1704067200000,
      "venue": "BINANCE",
      "funding_rate": 0.0001,
      "next_funding_time": 1704096000000
    },
    {
      "timestamp": 1704096000000,
      "venue": "BINANCE",
      "funding_rate": 0.00015,
      "next_funding_time": 1704124800000
    }
  ]
}
```

---

### GET /api/history/liquidations

Fetch historical liquidation events.

**Request**:
```http
GET /api/history/liquidations?symbol=BTCUSDT-PERP&from=2025-01-01&to=2025-01-02
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Trading pair |
| from | string | Yes | Start date |
| to | string | Yes | End date |
| venue | string | No | Filter by exchange |
| side | string | No | Filter by side (LONG, SHORT) |
| min_value | number | No | Minimum USD value |
| limit | number | No | Max records (default: 5000) |

**Response** (200 OK):
```json
{
  "symbol": "BTCUSDT-PERP",
  "from": "2025-01-01T00:00:00Z",
  "to": "2025-01-02T00:00:00Z",
  "count": 1234,
  "data": [
    {
      "timestamp": 1704067200123,
      "venue": "BINANCE",
      "side": "LONG",
      "quantity": 0.5,
      "price": 50000.0,
      "value": 25000.0
    },
    {
      "timestamp": 1704067201456,
      "venue": "BYBIT",
      "side": "SHORT",
      "quantity": 1.2,
      "price": 50050.0,
      "value": 60060.0
    }
  ]
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description"
}
```

**Error Codes**:

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_SYMBOL | 400 | Symbol not recognized |
| INVALID_DATE_RANGE | 400 | from > to or invalid format |
| MISSING_PARAMETER | 400 | Required parameter missing |
| NO_DATA | 404 | No data found for query |
| CATALOG_NOT_FOUND | 404 | Parquet catalog not available |
| INTERNAL_ERROR | 500 | Server error |
| DAEMON_NOT_RUNNING | 503 | Backend daemon unavailable |

---

## Rate Limits

| Endpoint | Rate Limit |
|----------|------------|
| /api/symbols | 60/minute |
| /api/status | 60/minute |
| /api/history/* | 10/minute |

**Rate Limit Response** (429 Too Many Requests):
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Retry after 60 seconds.",
  "retry_after": 60
}
```

---

## CORS Configuration

The server enables CORS for browser access:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local dev
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

---

## Example Usage

### JavaScript Fetch

```javascript
// Fetch historical OI
async function loadHistoricalOI(symbol, from, to) {
  const params = new URLSearchParams({ symbol, from, to });
  const response = await fetch(`http://localhost:8765/api/history/oi?${params}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message);
  }

  const result = await response.json();
  return result.data.map(d => ({
    time: Math.floor(d.timestamp / 1000),
    value: d.open_interest_value
  }));
}

// Check server status
async function checkServerHealth() {
  const response = await fetch('http://localhost:8765/api/status');
  const status = await response.json();
  return status.daemon_running;
}
```

### Python Requests

```python
import requests

# Fetch symbols
response = requests.get("http://localhost:8765/api/symbols")
symbols = response.json()["symbols"]

# Fetch historical funding
response = requests.get(
    "http://localhost:8765/api/history/funding",
    params={
        "symbol": "BTCUSDT-PERP",
        "from": "2025-01-01",
        "to": "2025-01-31"
    }
)
funding_data = response.json()["data"]
```
