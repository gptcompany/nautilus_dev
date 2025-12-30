# Research: TradingView Lightweight Charts Dashboard

**Feature**: 003-tradingview-lightweight-charts
**Date**: 2025-12-25

## Research Tasks

### 1. TradingView Lightweight Charts Library

**Question**: What version and features are available for real-time financial charts?

**Decision**: Use TradingView Lightweight Charts v4.x

**Rationale**:
- Open source (Apache 2.0 license)
- Lightweight: ~40KB gzipped
- Purpose-built for financial time-series data
- Native support for line series, area series, histogram, and markers
- Sub-millisecond render performance
- Built-in crosshair and time scale

**CDN**: `https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js`

**Key APIs**:
```javascript
// Create chart
const chart = createChart(container, {
  width: 800,
  height: 400,
  layout: { background: { color: '#1a1a2e' }, textColor: '#e0e0e0' },
  timeScale: { timeVisible: true, secondsVisible: false }
});

// Add line series for OI
const oiSeries = chart.addLineSeries({ color: '#2196F3', lineWidth: 2 });
oiSeries.setData([{ time: 1234567890, value: 50000 }]);
oiSeries.update({ time: 1234567891, value: 50100 });

// Add markers for liquidations
oiSeries.setMarkers([{
  time: 1234567890,
  position: 'aboveBar',
  color: '#f44336',
  shape: 'arrowDown',
  text: 'LONG LIQ'
}]);
```

**Alternatives Considered**:
- Chart.js: Too general, not optimized for financial data
- Apache ECharts: Heavy, complex API
- D3.js: Too low-level for this use case

---

### 2. WebSocket Bridge Architecture

**Question**: How to connect browser to existing DaemonRunner data streams?

**Decision**: Create a WebSocket bridge server using FastAPI + python-websockets

**Rationale**:
- DaemonRunner already collects OI, Funding, Liquidations
- Need to expose this data to browser via WebSocket
- FastAPI provides both REST (historical) and WebSocket (real-time)
- Can inject into DaemonRunner's callback chain

**Implementation Approach**:
```python
# Modify DaemonRunner to support external callbacks
class DaemonRunner:
    def __init__(self, ..., external_callbacks: list[Callable] = None):
        self._external_callbacks = external_callbacks or []

    def _on_liquidation(self, liquidation: Liquidation):
        # Existing logic...
        # Also notify external callbacks
        for callback in self._external_callbacks:
            callback({"type": "liquidation", **liquidation.model_dump()})
```

**Alternative**: Run separate WebSocket server that reads from Parquet store
- Rejected: Too much latency, not real-time

---

### 3. Existing Data Models (Spec 001)

**Question**: What data structures exist for OI, Funding, Liquidations?

**Findings**: Models already defined in `scripts/ccxt_pipeline/models/`

**OpenInterest** (`open_interest.py`):
```python
class OpenInterest(BaseModel):
    timestamp: datetime
    symbol: str           # "BTCUSDT-PERP"
    venue: Venue          # BINANCE, BYBIT, HYPERLIQUID
    open_interest: float  # Contracts
    open_interest_value: float  # USD
```

**FundingRate** (`funding_rate.py`):
```python
class FundingRate(BaseModel):
    timestamp: datetime
    symbol: str
    venue: Venue
    funding_rate: float   # Decimal (0.0001 = 0.01%)
    next_funding_time: datetime | None
    predicted_rate: float | None
```

**Liquidation** (`liquidation.py`):
```python
class Liquidation(BaseModel):
    timestamp: datetime
    symbol: str
    venue: Venue
    side: Side           # LONG, SHORT
    quantity: float
    price: float
    value: float         # USD
```

**Decision**: Reuse these models directly, serialize to JSON for WebSocket

---

### 4. Standalone HTML Bundling

**Question**: How to create a single HTML file with all assets embedded?

**Decision**: Use esbuild with inline CSS and JS

**Build Command**:
```bash
npx esbuild src/app.js --bundle --minify --format=iife --outfile=dist/bundle.js
```

**Final HTML Template**:
```html
<!DOCTYPE html>
<html>
<head>
  <style>/* Inlined CSS */</style>
</head>
<body>
  <div id="app"></div>
  <script>/* Lightweight Charts inlined */</script>
  <script>/* Bundle.js inlined */</script>
</body>
</html>
```

**Build Script** (`build.js`):
```javascript
const esbuild = require('esbuild');
const fs = require('fs');

// Build JS bundle
esbuild.buildSync({
  entryPoints: ['src/app.js'],
  bundle: true,
  minify: true,
  format: 'iife',
  outfile: 'dist/bundle.js'
});

// Read components
const css = fs.readFileSync('styles/main.css', 'utf8');
const lwc = fs.readFileSync('node_modules/lightweight-charts/dist/lightweight-charts.standalone.production.js', 'utf8');
const bundle = fs.readFileSync('dist/bundle.js', 'utf8');
const template = fs.readFileSync('index.html', 'utf8');

// Inject into template
const html = template
  .replace('<!-- CSS -->', `<style>${css}</style>`)
  .replace('<!-- LWC -->', `<script>${lwc}</script>`)
  .replace('<!-- BUNDLE -->', `<script>${bundle}</script>`);

fs.writeFileSync('dist/dashboard.html', html);
console.log('Built dist/dashboard.html');
```

---

### 5. WebSocket Reconnection Strategy

**Question**: How to handle WebSocket disconnections gracefully?

**Decision**: Exponential backoff with visual status indicator

**Algorithm**:
```javascript
class ReconnectingWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.reconnectDelay = options.initialDelay || 1000;
    this.maxDelay = options.maxDelay || 30000;
    this.currentDelay = this.reconnectDelay;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => {
      this.currentDelay = this.reconnectDelay;  // Reset on success
      this.onStatusChange('connected');
    };
    this.ws.onclose = () => {
      this.onStatusChange('reconnecting');
      setTimeout(() => this.connect(), this.currentDelay);
      this.currentDelay = Math.min(this.currentDelay * 2, this.maxDelay);
    };
  }
}
```

**UI Indicator**:
- 🟢 Connected
- 🟡 Reconnecting (with countdown)
- 🔴 Disconnected (after max retries)

---

### 6. Data Buffer Management

**Question**: How to handle 24 hours of data without memory issues?

**Decision**: Rolling window buffer with configurable max points

**Implementation**:
```javascript
class DataBuffer {
  constructor(maxPoints = 50000) {
    this.maxPoints = maxPoints;
    this.data = [];
  }

  add(point) {
    this.data.push(point);
    if (this.data.length > this.maxPoints) {
      // Remove oldest 10% when limit exceeded
      this.data = this.data.slice(this.data.length * 0.1);
    }
  }

  getAll() {
    return this.data;
  }
}
```

**Rationale**:
- 50k points × ~50 bytes = ~2.5MB memory (acceptable)
- OI every 5 min = 288/day = 2016/week
- Liquidations variable, but throttled to 10/sec max

---

### 7. Chart Color Scheme

**Question**: What colors for dark theme trading dashboard?

**Decision**: Dark theme with semantic colors

| Element | Color | Hex |
|---------|-------|-----|
| Background | Dark navy | #1a1a2e |
| Text | Light gray | #e0e0e0 |
| OI Line | Blue | #2196F3 |
| Funding Positive | Red/Orange | #ff5722 |
| Funding Negative | Green | #4caf50 |
| Long Liquidation | Red | #f44336 |
| Short Liquidation | Green | #00c853 |
| Grid | Subtle gray | #2a2a4a |

---

## Summary

All research questions resolved. Ready to proceed with data-model.md and contracts.
