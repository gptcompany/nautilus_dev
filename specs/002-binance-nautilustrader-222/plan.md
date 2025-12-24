# Implementation Plan: Binance to NautilusTrader v1.222.0 Data Ingestion Pipeline

**Feature Branch**: `002-binance-nautilustrader-222`
**Created**: 2025-12-24
**Status**: Ready for Implementation
**Spec Reference**: `specs/002-binance-nautilustrader-222/spec.md`

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         n8n Workflow (Daily @ 03:45)                    │
│                    Downloads CSV from Binance Data API                  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              /media/sam/3TB-WDC/binance-history-data-downloader/        │
│                                                                         │
│  data/BTCUSDT/                  data/ETHUSDT/                           │
│  ├── klines/1m/*.csv            ├── klines/1m/*.csv                     │
│  ├── trades/*.csv               ├── trades/*.csv                        │
│  └── fundingRate/*.csv          └── fundingRate/*.csv                   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     binance2nautilus CLI                                │
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │ CSV Parser  │───▶│ V1 Wrangler │───▶│  Catalog    │                  │
│  │  (pandas)   │    │ (Cython)    │    │  Writer     │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│                                                                         │
│  State Tracker: conversion_state.json                                   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              /media/sam/2TB-NVMe/nautilus_catalog_v1222/                │
│                                                                         │
│  data/                                                                  │
│  ├── crypto_perpetual/BTCUSDT-PERP.BINANCE/*.parquet                    │
│  ├── bar/BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL/*.parquet          │
│  └── trade_tick/BTCUSDT-PERP.BINANCE/*.parquet                          │
│                                                                         │
│  Schema: v1.222.0 (128-bit precision, fixed_size_binary[16])            │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  NautilusTrader v1.222.0 Nightly                        │
│                                                                         │
│  BacktestNode / BacktestEngine                                          │
│  ├── ParquetDataCatalog.bars()                                          │
│  ├── ParquetDataCatalog.trade_ticks()                                   │
│  └── Strategy execution                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    binance2nautilus Package                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │    cli.py      │  │  converter.py  │  │   state.py     │  │
│  │                │  │                │  │                │  │
│  │ - convert      │  │ - KlineConv.   │  │ - load_state   │  │
│  │ - update       │  │ - TradeConv.   │  │ - save_state   │  │
│  │ - validate     │  │ - FundingConv. │  │ - get_pending  │  │
│  │ - status       │  │                │  │                │  │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘  │
│          │                   │                   │           │
│          └───────────────────┼───────────────────┘           │
│                              │                               │
│  ┌───────────────────────────▼───────────────────────────┐   │
│  │                   instruments.py                      │   │
│  │                                                       │   │
│  │  - create_btcusdt_perp()                              │   │
│  │  - create_ethusdt_perp()                              │   │
│  │  - get_instrument(symbol: str) -> CryptoPerpetual     │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Technical Decisions

### Decision 1: Wrangler Version

**Options Considered**:
1. **V1 Wranglers** (`BarDataWrangler`, `TradeTickDataWrangler`)
   - Pros: Compatible with BacktestEngine, production-tested
   - Cons: Slightly slower than V2
2. **V2 Wranglers** (`BarDataWranglerV2`, `TradeTickDataWranglerV2`)
   - Pros: Native Rust/PyO3, potentially faster
   - Cons: **NOT compatible with BacktestEngine** (PyO3 objects)

**Selected**: Option 1 (V1 Wranglers)

**Rationale**: V2 wranglers produce PyO3 objects that cannot be used with the current BacktestEngine. This was confirmed in Discord discussions and NautilusTrader documentation.

---

### Decision 2: Precision Mode

**Options Considered**:
1. **64-bit precision** (`fixed_size_binary[8]`)
   - Pros: Smaller file size, faster on Windows
   - Cons: 9 decimal precision only
2. **128-bit precision** (`fixed_size_binary[16]`)
   - Pros: 16 decimal precision, Linux default
   - Cons: Larger file size

**Selected**: Option 2 (128-bit precision)

**Rationale**: Linux nightly builds default to 128-bit. Mixing precision modes causes schema errors. The old catalog failed due to this mismatch.

---

### Decision 3: Processing Strategy

**Options Considered**:
1. **Load all data into memory**
   - Pros: Simple implementation
   - Cons: Will crash with 5+ years of trade ticks (RAM exhaustion)
2. **Chunked processing with generators**
   - Pros: Constant memory usage, works with any data size
   - Cons: Slightly more complex implementation

**Selected**: Option 2 (Chunked processing)

**Rationale**: Trade tick data is 500M+ records. Must use chunked processing (100k rows per chunk) to avoid memory exhaustion.

---

## Implementation Strategy

### Phase 1: Foundation

**Goal**: Create instrument definitions and basic converter structure

**Deliverables**:
- [x] `instruments.py` - CryptoPerpetual definitions for BTCUSDT, ETHUSDT
- [x] `state.py` - Conversion state tracking (JSON-based)
- [x] `config.py` - Configuration model with paths and settings
- [x] Basic project structure with `__init__.py`

**Dependencies**: None

**Files**:
```
strategies/binance2nautilus/
├── __init__.py
├── instruments.py      # Instrument definitions
├── state.py            # State tracking
└── config.py           # Configuration
```

---

### Phase 2: Klines Converter

**Goal**: Convert Binance klines CSV to NautilusTrader Bar objects

**Deliverables**:
- [ ] `converters/klines.py` - Klines to Bar conversion
- [ ] Support for 1m, 5m, 15m timeframes
- [ ] Chunked file processing
- [ ] Unit tests for klines conversion

**Dependencies**: Phase 1

**Key Implementation**:
```python
# Transform Binance CSV to wrangler format
bar_df = pd.DataFrame({
    'open': data['open'].astype('float64'),
    'high': data['high'].astype('float64'),
    'low': data['low'].astype('float64'),
    'close': data['close'].astype('float64'),
    'volume': data['volume'].astype('float64'),
}, index=pd.to_datetime(data['open_time'], unit='ms', utc=True))

# Use V1 wrangler
bar_type = BarType.from_str('BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL')
wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = wrangler.process(bar_df)
```

---

### Phase 3: Trades Converter

**Goal**: Convert Binance trades CSV to NautilusTrader TradeTick objects

**Deliverables**:
- [ ] `converters/trades.py` - Trades to TradeTick conversion
- [ ] Chunked processing (100k rows per chunk)
- [ ] Memory-efficient generator pattern
- [ ] Unit tests for trades conversion

**Dependencies**: Phase 2

**Key Implementation**:
```python
# Transform Binance trades to wrangler format
# Note: Column must be 'quantity' NOT 'size' for V1 wrangler
tick_df = pd.DataFrame({
    'price': chunk['price'].astype('float64'),
    'quantity': chunk['qty'].astype('float64'),       # NOT 'size'
    'buyer_maker': chunk['is_buyer_maker'],           # bool
    'trade_id': chunk['id'].astype(str),
}, index=pd.to_datetime(chunk['time'], unit='ms', utc=True))

wrangler = TradeTickDataWrangler(instrument=instrument)
ticks = wrangler.process(tick_df)
```

---

### Phase 4: CLI Interface

**Goal**: Create command-line interface for conversion operations

**Deliverables**:
- [ ] `cli.py` - Click-based CLI with commands: convert, update, validate, status
- [ ] Progress bars for long operations
- [ ] JSON output mode for automation
- [ ] Configuration file support

**Dependencies**: Phase 3

---

### Phase 5: Integration & Validation

**Goal**: Validate catalog works with BacktestEngine

**Deliverables**:
- [ ] `validate.py` - Catalog validation logic
- [ ] BacktestEngine compatibility test
- [ ] Integration tests with sample strategy
- [ ] Performance benchmarks

**Dependencies**: Phase 4

---

### Phase 6: Incremental Updates

**Goal**: Support daily incremental updates from n8n workflow

**Deliverables**:
- [ ] State tracking for last processed file
- [ ] Detect new files since last run
- [ ] Append-only catalog updates
- [ ] n8n integration documentation

**Dependencies**: Phase 5

---

## File Structure

```
strategies/binance2nautilus/
├── __init__.py
├── cli.py                    # Click CLI entry point
├── config.py                 # Configuration model
├── instruments.py            # CryptoPerpetual definitions
├── state.py                  # Conversion state tracking
├── validate.py               # Catalog validation
├── converters/
│   ├── __init__.py
│   ├── base.py               # Base converter class
│   ├── klines.py             # Klines → Bar converter
│   ├── trades.py             # Trades → TradeTick converter
│   └── funding.py            # Funding rate converter
└── tests/
    ├── __init__.py
    ├── test_instruments.py
    ├── test_klines.py
    ├── test_trades.py
    └── test_integration.py
```

## API Design

### Public Interface

```python
from binance2nautilus import convert_klines, convert_trades, update_catalog

# Convert specific data type
convert_klines(
    symbol='BTCUSDT',
    timeframe='1m',
    source_dir='/media/sam/3TB-WDC/binance-history-data-downloader/data',
    output_dir='/media/sam/2TB-NVMe/nautilus_catalog_v1222',
)

# Incremental update
update_catalog(
    symbols=['BTCUSDT', 'ETHUSDT'],
    source_dir=...,
    output_dir=...,
)
```

### Configuration

```python
from pydantic import BaseModel
from pathlib import Path

class ConverterConfig(BaseModel):
    source_dir: Path = Path('/media/sam/3TB-WDC/binance-history-data-downloader/data')
    output_dir: Path = Path('/media/sam/2TB-NVMe/nautilus_catalog_v1222')
    symbols: list[str] = ['BTCUSDT', 'ETHUSDT']
    timeframes: list[str] = ['1m', '5m', '15m']
    chunk_size: int = 100_000
    nautilus_env: Path = Path('/media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env')
```

## Testing Strategy

### Unit Tests
- [x] Test instrument creation (CryptoPerpetual fields)
- [ ] Test CSV parsing for each format (klines, trades, funding)
- [ ] Test DataFrame transformation (correct columns, types)
- [ ] Test wrangler output (Bar, TradeTick objects)
- [ ] Test state tracking (load, save, update)

### Integration Tests
- [ ] Test full conversion pipeline (CSV → Parquet)
- [ ] Test catalog loading with ParquetDataCatalog
- [ ] Test BacktestEngine compatibility
- [ ] Test incremental update scenario

### Performance Tests
- [ ] Benchmark: 1 month klines conversion time
- [ ] Benchmark: Wrangler throughput (records/sec)
- [ ] Memory profiling for trade tick conversion
- [ ] Catalog query performance

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Schema mismatch (precision) | High | Low | Verified 128-bit mode in nightly |
| Memory exhaustion (trades) | High | Medium | Chunked processing (100k rows) |
| V2 wrangler incompatibility | High | Low | Explicitly use V1 wranglers only |
| Disk space insufficient | Medium | Low | Check space before bulk conversion |
| n8n workflow conflict | Low | Low | Lock file during conversion |

## Dependencies

### External Dependencies
- NautilusTrader v1.222.0 nightly
- pandas >= 2.0
- click >= 8.0 (CLI)
- pydantic >= 2.0 (config)
- tqdm (progress bars)

### Internal Dependencies
- Existing n8n workflow for CSV downloads
- Source data at `/media/sam/3TB-WDC/binance-history-data-downloader/`
- Target storage at `/media/sam/2TB-NVMe/`

## Acceptance Criteria

- [x] Research complete (research.md)
- [x] Data model defined (data-model.md)
- [x] CLI contract defined (contracts/cli-interface.md)
- [x] Quickstart guide written (quickstart.md)
- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Catalog validates successfully
- [ ] BacktestEngine runs without errors
- [ ] Incremental updates work correctly
- [ ] Performance meets SC-001, SC-002 criteria

## Next Steps

1. Run `/speckit.tasks` to generate task breakdown
2. Implement Phase 1 (instruments, state, config)
3. Test with 1-month subset using quickstart.md
4. Proceed with remaining phases
