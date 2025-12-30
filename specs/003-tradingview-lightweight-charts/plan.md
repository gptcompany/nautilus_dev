# Implementation Plan: TradingView Lightweight Charts Real-Time Dashboard

**Feature Branch**: `003-tradingview-lightweight-charts`
**Created**: 2025-12-25
**Status**: Draft
**Spec Reference**: `specs/003-tradingview-lightweight-charts/spec.md`

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                     Trading Dashboard                            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │   TradingView Lightweight Charts (Frontend - Pure JS)       │ │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐         │ │
│  │   │ OI Chart │  │ Funding  │  │ Liquidations     │         │ │
│  │   │ (Line)   │  │ (Line)   │  │ (Markers)        │         │ │
│  │   └────┬─────┘  └────┬─────┘  └────────┬─────────┘         │ │
│  │        │             │                 │                    │ │
│  │   ┌────┴─────────────┴─────────────────┴───────┐           │ │
│  │   │         WebSocket Data Connector            │           │ │
│  │   │   (Connect to existing ccxt_pipeline WS)    │           │ │
│  │   └────────────────────┬───────────────────────┘           │ │
│  └────────────────────────┼───────────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│              Existing Infrastructure (Spec 001)                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   DaemonRunner                               │  │
│  │  - OI fetch every 5 min (Binance, Bybit, Hyperliquid)       │  │
│  │  - Funding fetch every 60 min                                │  │
│  │  - Liquidation WebSocket streams (real-time)                 │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              ParquetStore (Historical Data)                   │  │
│  │  Path: /media/sam/1TB/nautilus_dev/data/catalog/ccxt/        │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
dashboard/
├── index.html              # Single-file dashboard (standalone deployable)
├── src/
│   ├── app.js              # Main application entry
│   ├── charts/
│   │   ├── base-chart.js   # Shared chart setup
│   │   ├── oi-chart.js     # Open Interest line chart
│   │   ├── funding-chart.js # Funding rate chart
│   │   └── liquidation-layer.js  # Liquidation event markers
│   ├── data/
│   │   ├── ws-client.js          # WebSocket connector
│   │   ├── buffer.js             # Rolling window buffer
│   │   └── api-client.js         # REST API client for historical data
│   ├── ui/
│   │   ├── symbol-selector.js    # Symbol dropdown
│   │   ├── status.js             # Connection status
│   │   ├── funding-display.js    # Funding rate panel
│   │   └── date-range.js         # Date range selector
│   └── utils/
│       └── format.js             # Number/time formatting
├── styles/
│   └── main.css            # Custom styles
└── dist/
    └── dashboard.html      # Bundled standalone file (FR-009)
```

## Technical Decisions

### Decision 1: Chart Library

**Options Considered**:
1. **TradingView Lightweight Charts** (open-source)
   - Pros: Free, performant (<1ms render), lightweight (~40KB gzipped), excellent for financial data
   - Cons: Limited to time-series, no 3D/heatmaps
2. **Chart.js**
   - Pros: Very popular, many plugins
   - Cons: Not optimized for financial data, no built-in crosshair/time axis

**Selected**: Option 1 - TradingView Lightweight Charts

**Rationale**: Purpose-built for financial data, matches spec requirement exactly, excellent performance for real-time updates, and supports markers for liquidation events.

---

### Decision 2: Data Delivery Architecture

**Options Considered**:
1. **Direct WebSocket to Exchanges** (browser connects directly)
   - Pros: Lowest latency, no backend
   - Cons: CORS issues, API key exposure, duplicate connections
2. **WebSocket Proxy via Python Backend**
   - Pros: Reuses existing DaemonRunner, single connection, auth handled server-side
   - Cons: Additional latency (~10ms), requires backend running
3. **Server-Sent Events (SSE)**
   - Pros: Simpler than WebSocket, auto-reconnect
   - Cons: Unidirectional, less common for real-time trading

**Selected**: Option 2 - WebSocket Proxy via Python Backend

**Rationale**:
- Reuses existing `LiquidationStreamManager` from Spec 001
- No browser CORS issues
- Single point of data aggregation (all exchanges → one stream)
- Authentication/rate limits handled server-side
- Small latency acceptable for OI/Funding (not HFT)

---

### Decision 3: Historical Data Loading

**Options Considered**:
1. **Python REST API** serving Parquet data as JSON
   - Pros: Simple, browser-compatible
   - Cons: Requires running Python service
2. **Pre-generated JSON files**
   - Pros: Static hosting possible
   - Cons: Stale data, no query flexibility
3. **DuckDB WASM in browser**
   - Pros: Query Parquet directly in browser
   - Cons: Complex setup, large WASM bundle

**Selected**: Option 1 - Python REST API

**Rationale**: Matches existing tech stack, can serve historical + real-time, simple JSON output for browser consumption.

---

### Decision 4: Deployment Strategy

**Options Considered**:
1. **Single HTML file with CDN dependencies**
   - Pros: Easy distribution, no build step
   - Cons: Requires internet for CDN
2. **Bundled HTML with embedded assets**
   - Pros: Truly standalone, works offline
   - Cons: Larger file, requires build step
3. **Docker container**
   - Pros: Includes backend
   - Cons: Complex for simple dashboard

**Selected**: Option 2 - Bundled HTML with embedded assets (FR-009)

**Rationale**: Spec explicitly requires "standalone HTML file with embedded assets". Use esbuild to bundle JS/CSS inline.

---

## Implementation Strategy

### Phase 1: Foundation & WebSocket Bridge

**Goal**: Establish data flow from existing DaemonRunner to browser

**Deliverables**:
- [ ] WebSocket bridge server (Python: FastAPI + websockets)
- [ ] WebSocket client (JavaScript)
- [ ] Connection status indicator (UI)
- [ ] Basic HTML structure with Lightweight Charts loaded

**Dependencies**: Spec 001 complete (DaemonRunner running)

---

### Phase 2: Core Charts (US1, US2, US3)

**Goal**: Display OI, Funding, and Liquidations in real-time

**Deliverables**:
- [ ] Open Interest line chart with real-time updates (US1)
- [ ] Funding Rate display with color coding (US2)
- [ ] Liquidation markers on chart (US3)
- [ ] Symbol selector dropdown (FR-005)
- [ ] Auto-reconnect on WebSocket disconnect (FR-006)

**Dependencies**: Phase 1

---

### Phase 3: Historical Data & Polish (US4, US5)

**Goal**: Add historical overlay and multi-symbol support

**Deliverables**:
- [ ] Historical data API endpoint (Python)
- [ ] Historical data overlay with visual distinction (US4)
- [ ] Multi-symbol switching (US5)
- [ ] Chart state preservation across switches (FR-010)
- [ ] Standalone HTML bundling (FR-009)

**Dependencies**: Phase 2

---

## File Structure

```
dashboard/                      # Dashboard application
├── index.html                  # Entry point
├── server.py                   # WebSocket bridge + REST API
├── models.py                   # Pydantic models for WebSocket messages
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies (esbuild)
├── src/
│   ├── app.js                  # Main application
│   ├── charts/
│   │   ├── base-chart.js       # Shared chart setup
│   │   ├── oi-chart.js         # Open Interest chart
│   │   ├── funding-chart.js    # Funding rate chart
│   │   └── liquidation-layer.js # Liquidation markers
│   ├── data/
│   │   ├── ws-client.js        # WebSocket client
│   │   ├── buffer.js           # Data buffer (24h rolling)
│   │   └── api-client.js       # REST API client
│   ├── ui/
│   │   ├── symbol-selector.js  # Symbol dropdown
│   │   ├── status.js           # Connection status
│   │   ├── funding-display.js  # Funding rate panel
│   │   └── date-range.js       # Date range selector
│   └── utils/
│       └── format.js           # Formatters
├── styles/
│   └── main.css                # Dashboard styles
├── build.js                    # esbuild config
└── dist/
    └── dashboard.html          # Bundled output
tests/
└── dashboard/
    ├── test_server.py          # Server unit tests
    └── test_e2e.py             # End-to-end tests (Playwright)
```

## API Design

### WebSocket Message Format

```typescript
// Server → Client messages
interface OIUpdate {
  type: "oi";
  timestamp: number;  // Unix ms
  symbol: string;
  venue: string;
  open_interest: number;
  open_interest_value: number;
}

interface FundingUpdate {
  type: "funding";
  timestamp: number;
  symbol: string;
  venue: string;
  funding_rate: number;  // Decimal (0.0001 = 0.01%)
  next_funding_time: number | null;
}

interface LiquidationEvent {
  type: "liquidation";
  timestamp: number;
  symbol: string;
  venue: string;
  side: "LONG" | "SHORT";
  quantity: number;
  price: number;
  value: number;
}

interface ConnectionStatus {
  type: "status";
  connected: boolean;
  exchanges: string[];
}

// Client → Server messages
interface Subscribe {
  action: "subscribe";
  symbols: string[];
}

interface Unsubscribe {
  action: "unsubscribe";
  symbols: string[];
}
```

### REST API (Historical Data)

```
GET /api/history/oi?symbol=BTCUSDT-PERP&from=2025-01-01&to=2025-01-31
GET /api/history/funding?symbol=BTCUSDT-PERP&from=2025-01-01&to=2025-01-31
GET /api/symbols  # List available symbols
GET /api/status   # Server health check
```

## Testing Strategy

### Unit Tests
- [ ] WebSocket client reconnection logic
- [ ] Data buffer overflow handling
- [ ] Chart update performance (< 16ms per frame)
- [ ] Number formatting edge cases

### Integration Tests
- [ ] WebSocket bridge receives DaemonRunner events
- [ ] Historical API returns valid Parquet data
- [ ] Symbol switching clears and reloads data

### E2E Tests (Playwright)
- [ ] Dashboard loads within 3 seconds (SC-002)
- [ ] OI updates appear within 1 second (SC-001)
- [ ] Chart remains responsive with 24h data (SC-003)
- [ ] Reconnection after disconnect (SC-004)

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| DaemonRunner not running | High | Medium | Show clear error message, check on connect |
| WebSocket overload (many liquidations) | Medium | Low | Throttle to 10 updates/second, aggregate |
| Browser memory with 24h data | Medium | Medium | Rolling buffer, limit to 50k points |
| CORS issues with REST API | Low | Low | FastAPI CORS middleware configured |

## Dependencies

### External Dependencies
- TradingView Lightweight Charts >= 4.0
- FastAPI >= 0.100.0
- websockets >= 12.0
- esbuild >= 0.20.0 (build only)

### Internal Dependencies
- Spec 001: CCXT Pipeline with DaemonRunner
- Spec 002: Nautilus Parquet Catalog (optional, for historical)

## Constitution Check

### KISS & YAGNI
- [x] Single-purpose files (chart per file)
- [x] No premature abstractions
- [x] No unused features planned

### Native First
- [x] Uses existing DaemonRunner (no reimplementation)
- [x] Reuses Pydantic models from Spec 001

### Performance
- [x] No df.iterrows() (Parquet streaming via DuckDB)
- [x] Async WebSocket handling

### TDD
- [ ] Tests defined in Testing Strategy
- [ ] E2E coverage for success criteria

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] E2E tests passing for SC-001 through SC-005
- [ ] Dashboard loads as standalone HTML file
- [ ] Documentation updated
- [ ] Code review approved
