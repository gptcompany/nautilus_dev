# Quickstart: TradingView Lightweight Charts Dashboard

**Feature**: 003-tradingview-lightweight-charts
**Date**: 2025-12-25

## Prerequisites

1. **Spec 001 Complete**: CCXT Pipeline with DaemonRunner
2. **Node.js 18+**: For building standalone HTML
3. **Python 3.11+**: Already configured via NautilusTrader nightly

## Quick Start (5 minutes)

### Step 1: Ensure DaemonRunner is Running

```bash
# Activate nightly environment
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate

# Start the daemon (if not already running)
cd /media/sam/1TB/nautilus_dev
PYTHONPATH=. python -m scripts.ccxt_pipeline daemon start
```

### Step 2: Start the Dashboard Server

```bash
# From project root
cd /media/sam/1TB/nautilus_dev/dashboard

# Install dependencies (first time only)
uv pip install fastapi websockets uvicorn

# Start server
uv run python server.py
```

Server starts at:
- REST API: http://localhost:8765/api
- WebSocket: ws://localhost:8765/ws

### Step 3: Open Dashboard

```bash
# Open in browser
xdg-open http://localhost:8765
```

Or open `dashboard/dist/dashboard.html` directly (standalone mode).

---

## Development Workflow

### Running in Development Mode

```bash
# Terminal 1: Start daemon
PYTHONPATH=/media/sam/1TB/nautilus_dev python -m scripts.ccxt_pipeline daemon start

# Terminal 2: Start dashboard server with hot reload
cd dashboard
uv run uvicorn server:app --reload --port 8765

# Terminal 3: Watch JS changes (optional)
npx esbuild src/app.js --bundle --outfile=dist/bundle.js --watch
```

### Building Standalone HTML

```bash
cd dashboard

# Install build dependencies
npm install esbuild

# Build bundled HTML
node build.js

# Output: dist/dashboard.html (single file, ~200KB)
```

---

## Verification Tests

### Test 1: WebSocket Connection

```javascript
// Open browser console at http://localhost:8765
const ws = new WebSocket('ws://localhost:8765/ws');

ws.onopen = () => {
  console.log('Connected!');
  ws.send(JSON.stringify({ action: 'subscribe', symbols: ['BTCUSDT-PERP'] }));
};

ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));

// Expected: status message, then oi/funding/liquidation updates
```

### Test 2: REST API

```bash
# Check server status
curl http://localhost:8765/api/status | jq

# List symbols
curl http://localhost:8765/api/symbols | jq

# Fetch historical OI (last 24 hours)
curl "http://localhost:8765/api/history/oi?symbol=BTCUSDT-PERP&from=2025-12-24&to=2025-12-25" | jq
```

### Test 3: Chart Rendering

1. Open http://localhost:8765
2. Verify:
   - [ ] OI chart displays and updates
   - [ ] Funding rate shows with color (red/green)
   - [ ] Connection status indicator is green
   - [ ] Symbol dropdown works

---

## Common Issues

### Issue: "DaemonRunner not started"

**Cause**: Backend daemon not running.

**Fix**:
```bash
# Check daemon status
PYTHONPATH=. python -m scripts.ccxt_pipeline daemon status

# Start if not running
PYTHONPATH=. python -m scripts.ccxt_pipeline daemon start
```

### Issue: "No data in charts"

**Cause**: Daemon just started, no data fetched yet.

**Fix**: Wait 5 minutes for first OI fetch, or trigger manually:
```bash
PYTHONPATH=. python -m scripts.ccxt_pipeline fetch-oi BTCUSDT-PERP --store
```

### Issue: "WebSocket connection failed"

**Cause**: Dashboard server not running or wrong port.

**Fix**:
```bash
# Verify server is running
curl http://localhost:8765/api/status

# If not, start server
cd dashboard && uv run python server.py
```

### Issue: "CORS error in browser"

**Cause**: Opening HTML file directly (file://) instead of via server.

**Fix**: Access via http://localhost:8765, not file://

---

## Integration Scenarios

### Scenario 1: Real-Time Monitoring

```
User opens dashboard → sees live OI/Funding/Liquidations
DaemonRunner fetches OI every 5 min → chart updates
Liquidation occurs → marker appears immediately
User switches to ETHUSDT → charts switch symbols
```

### Scenario 2: Historical Analysis

```
User opens dashboard → requests historical data
Dashboard calls /api/history/oi → loads past 7 days
Real-time stream continues → appends new data
Clear visual distinction between historical (faded) and live (bright)
```

### Scenario 3: Connection Recovery

```
WebSocket disconnects (network issue)
Dashboard shows "Reconnecting..." status
Exponential backoff: 1s, 2s, 4s, 8s...
Reconnects → resumes streaming
No data loss (buffered on server)
```

---

## File Locations

| File | Purpose |
|------|---------|
| `dashboard/server.py` | WebSocket bridge + REST API |
| `dashboard/index.html` | Development entry point |
| `dashboard/src/app.js` | Main application |
| `dashboard/dist/dashboard.html` | Standalone bundle |
| `scripts/ccxt_pipeline/` | Data pipeline (Spec 001) |
| `data/catalog/ccxt/` | Parquet data storage |

---

## Next Steps After Quickstart

1. **Customize Theme**: Edit `dashboard/styles/main.css`
2. **Add Symbols**: Modify `dashboard/src/ui/symbol-selector.js`
3. **Deploy**: Copy `dist/dashboard.html` to any web server
4. **Docker**: See `dashboard/Dockerfile` for containerized deployment
