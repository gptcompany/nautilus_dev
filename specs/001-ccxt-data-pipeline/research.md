# Research: CCXT Multi-Exchange Data Pipeline

**Created**: 2025-12-22
**Status**: Complete

## Research Questions Resolved

### 1. CCXT Exchange Support

**Question**: Do all three exchanges (Binance, Bybit, Hyperliquid) support the required methods?

**Decision**: All three exchanges are supported

**Rationale**: Based on CCXT documentation research:
- **Binance**: Full support for `fetch_open_interest`, `fetch_open_interest_history`, `fetch_funding_rate_history`, `watch_liquidations`
- **Bybit**: Full support with known bug in `fetch_open_interest_history` (max 200 records)
- **Hyperliquid**: Supported since CCXT 4.4.0 with `fetch_open_interest`, `fetch_funding_rate_history`

**Alternatives considered**:
- Direct exchange APIs: Rejected due to 3x maintenance overhead

---

### 2. CCXT Pro Licensing

**Question**: Is CCXT Pro required for WebSocket features? What is the cost?

**Decision**: CCXT Pro is free (merged into CCXT 1.95+)

**Rationale**: As of CCXT version 1.95, all Pro (WebSocket) features are included in the free CCXT package. No separate license required.

**Alternatives considered**:
- Use REST polling for liquidations: Fallback option for exchanges without WebSocket support

---

### 3. Hyperliquid Liquidation Stream

**Question**: Does Hyperliquid support liquidation streaming?

**Decision**: Unclear - implement polling fallback

**Rationale**: CCXT documentation does not confirm `watch_liquidations` for Hyperliquid. Will implement polling as fallback if WebSocket is unavailable.

**Alternatives considered**:
- Direct Hyperliquid WebSocket API: More complex, CCXT preferred for consistency

---

### 4. NautilusTrader Parquet Compatibility

**Question**: What format does ParquetDataCatalog expect?

**Decision**: Use partitioned Parquet with specific schema

**Rationale**: Based on NautilusTrader documentation:
- Directory structure: `{data_type}/{instrument_id}/`
- File naming: `{date}.parquet`
- Required columns: `ts_event`, `ts_init`, plus type-specific fields

**Alternatives considered**:
- Single file per data type: Rejected due to slow queries on large files

---

### 5. Rate Limiting Strategy

**Question**: How to handle rate limits across exchanges?

**Decision**: Use CCXT built-in rate limiter + custom backoff

**Rationale**:
- CCXT has `enableRateLimit=True` option
- Custom exponential backoff for 429 errors
- Respect exchange-specific limits:
  - Binance: 2400 req/min (general), 500 req/5min (OI stats)
  - Bybit: Varies by endpoint
  - Hyperliquid: Standard REST limits

**Alternatives considered**:
- Fixed delay between requests: Less efficient, may still hit limits

---

### 6. Symbol Normalization

**Question**: How to handle different symbol formats across exchanges?

**Decision**: Use CCXT unified symbol format with venue suffix

**Rationale**:
- CCXT normalizes symbols to `BASE/QUOTE:SETTLE` format
- Add venue suffix for clarity: `BTC/USDT:USDT.BINANCE`
- Store original exchange symbol for reference

| Exchange | Exchange Symbol | CCXT Symbol | Storage Symbol |
|----------|-----------------|-------------|----------------|
| Binance | BTCUSDT | BTC/USDT:USDT | BTCUSDT-PERP.BINANCE |
| Bybit | BTCUSDT | BTC/USDT:USDT | BTCUSDT-PERP.BYBIT |
| Hyperliquid | BTC | BTC/USD:USD | BTC-USD-PERP.HYPERLIQUID |

---

### 7. Bybit OI History Bug Workaround

**Question**: How to handle Bybit's 200-record limit in fetch_open_interest_history?

**Decision**: Chunk requests into smaller date ranges

**Rationale**: Known CCXT bug limits Bybit OI history to 200 records per request. Workaround:
- Calculate required date chunks based on interval
- Make multiple requests
- Merge results chronologically

**Alternatives considered**:
- Wait for CCXT fix: Uncertain timeline
- Use direct Bybit API: More maintenance

---

## Technology Best Practices

### Async Python with CCXT

```python
import ccxt.async_support as ccxt

async def fetch_all_exchanges():
    exchanges = [
        ccxt.binance({'enableRateLimit': True}),
        ccxt.bybit({'enableRateLimit': True}),
        ccxt.hyperliquid({'enableRateLimit': True}),
    ]
    try:
        results = await asyncio.gather(
            *[ex.fetch_open_interest('BTC/USDT:USDT') for ex in exchanges]
        )
    finally:
        await asyncio.gather(*[ex.close() for ex in exchanges])
    return results
```

### Pydantic Model Validation

```python
from pydantic import BaseModel, field_validator
from datetime import datetime

class OpenInterest(BaseModel):
    timestamp: datetime
    symbol: str
    venue: str
    open_interest: float
    open_interest_value: float

    @field_validator('open_interest')
    @classmethod
    def positive_oi(cls, v):
        if v < 0:
            raise ValueError('OI must be positive')
        return v
```

### Parquet Storage Pattern

```python
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

def write_parquet(data: list[OpenInterest], catalog_path: Path):
    table = pa.Table.from_pylist([d.model_dump() for d in data])
    path = catalog_path / "open_interest" / f"{data[0].symbol.replace('/', '_')}"
    path.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path / f"{data[0].timestamp.date()}.parquet")
```

---

## All NEEDS CLARIFICATION Resolved

No remaining clarifications. Ready for Phase 1 implementation.
