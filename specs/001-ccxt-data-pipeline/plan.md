# Implementation Plan: CCXT Multi-Exchange Data Pipeline

**Feature Branch**: `001-ccxt-data-pipeline`
**Created**: 2025-12-22
**Status**: Draft
**Spec Reference**: `specs/001-ccxt-data-pipeline/spec.md`

## Constitution Check

| Principle | Compliance | Notes |
|-----------|------------|-------|
| Black Box Design | ✅ | Clean API per exchange, hidden CCXT internals |
| KISS & YAGNI | ✅ | Python only, no premature optimization |
| Native First | ✅ | Uses ParquetDataCatalog compatible format |
| NO df.iterrows() | ✅ | Streaming writes, no DataFrame iteration |
| Async I/O | ✅ | asyncio for concurrent fetching |
| TDD Discipline | ✅ | Tests first for each component |
| Type hints | ✅ | All public functions typed |
| Coverage > 80% | ✅ | Target met |

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CCXT Data Pipeline                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│   │   Binance   │  │    Bybit    │  │ Hyperliquid │   EXCHANGES    │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│          │                │                │                        │
│          ▼                ▼                ▼                        │
│   ┌─────────────────────────────────────────────────┐              │
│   │              CCXT Unified API                    │   FETCHER   │
│   │  (fetch_open_interest, fetch_funding_rate,      │   LAYER     │
│   │   watch_liquidations)                            │              │
│   └──────────────────────┬──────────────────────────┘              │
│                          │                                          │
│                          ▼                                          │
│   ┌─────────────────────────────────────────────────┐              │
│   │              Data Normalizer                     │   NORMALIZE │
│   │  (Pydantic models, validation, unified format)  │   LAYER     │
│   └──────────────────────┬──────────────────────────┘              │
│                          │                                          │
│                          ▼                                          │
│   ┌─────────────────────────────────────────────────┐              │
│   │              Parquet Writer                      │   STORAGE   │
│   │  (NautilusTrader compatible, partitioned)       │   LAYER     │
│   └──────────────────────┬──────────────────────────┘              │
│                          │                                          │
│                          ▼                                          │
│   ┌─────────────────────────────────────────────────┐              │
│   │         /data/ccxt_catalog/                      │   CATALOG   │
│   │  ├── open_interest/                             │              │
│   │  ├── funding_rate/                              │              │
│   │  └── liquidations/                              │              │
│   └─────────────────────────────────────────────────┘              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Integration with NautilusTrader:
┌─────────────────────────────────────────────────────────────────────┐
│  NautilusTrader                                                     │
│  ├── ParquetDataCatalog ◄──────── ccxt_catalog (compatible format) │
│  ├── Strategy ◄─────────────────── Custom data via on_data()       │
│  └── BacktestNode ◄────────────── Historical OI/Funding for tests  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                          ccxt_pipeline/                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   models/    │    │  fetchers/   │    │   storage/   │         │
│  │              │    │              │    │              │         │
│  │ OpenInterest │    │ BaseFetcher  │    │ ParquetStore │         │
│  │ FundingRate  │◄───│ BinanceFetch │───►│              │         │
│  │ Liquidation  │    │ BybitFetch   │    │              │         │
│  │              │    │ HyperFetch   │    │              │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│         ▲                   │                    │                 │
│         │                   │                    │                 │
│         │            ┌──────┴──────┐            │                 │
│         │            │             │            │                 │
│         │     ┌──────────────┐  ┌──────────────┐                  │
│         │     │  scheduler/  │  │     cli/     │                  │
│         │     │              │  │              │                  │
│         └─────│ DaemonRunner │  │ main.py      │                  │
│               │              │  │              │                  │
│               └──────────────┘  └──────────────┘                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Technical Decisions

### Decision 1: CCXT vs Direct Exchange APIs

**Options Considered**:
1. **CCXT**: Unified API for all exchanges
   - Pros: Less code, maintained by community, handles rate limits
   - Cons: Abstraction overhead, may lag behind exchange updates
2. **Direct APIs**: Custom implementation per exchange
   - Pros: Full control, latest features
   - Cons: 3x code, 3x maintenance, inconsistent error handling

**Selected**: CCXT

**Rationale**: CCXT provides unified methods for all three exchanges (fetch_open_interest, fetch_funding_rate, watch_liquidations). The abstraction overhead is minimal and outweighed by reduced maintenance burden. CCXT is actively maintained and supports async.

---

### Decision 2: Async Architecture

**Options Considered**:
1. **Sync with threading**: Traditional approach
   - Pros: Simpler mental model
   - Cons: GIL issues, resource heavy
2. **Async with asyncio**: Modern Python
   - Pros: Efficient I/O, native CCXT support
   - Cons: Requires async/await throughout

**Selected**: Async with asyncio

**Rationale**: CCXT Pro (now merged into CCXT) is built on asyncio. Concurrent fetching from 3 exchanges benefits significantly from async. Constitution requires "async where needed" for I/O operations.

---

### Decision 3: Storage Format

**Options Considered**:
1. **Raw Parquet**: Direct parquet files
   - Pros: Simple, fast writes
   - Cons: Manual partitioning, no catalog integration
2. **NautilusTrader Compatible**: Match ParquetDataCatalog structure
   - Pros: Can be loaded alongside trade data
   - Cons: More complex schema

**Selected**: NautilusTrader Compatible

**Rationale**: Primary use case is correlating OI/funding with price action in backtests. Compatible format enables unified queries across all data types.

---

### Decision 4: Data Models

**Options Considered**:
1. **Dataclasses**: Simple Python dataclasses
   - Pros: Lightweight, fast
   - Cons: No validation
2. **Pydantic**: Validated models
   - Pros: Validation, serialization, type coercion
   - Cons: Slight overhead

**Selected**: Pydantic

**Rationale**: Exchange APIs return inconsistent data types. Pydantic handles type coercion and validation, catching malformed data before storage. Constitution skill "pydantic-model-generator" supports this.

---

## Implementation Strategy

### Phase 1: Foundation (P1 Stories: Current OI + Storage)

**Goal**: Fetch current OI from all exchanges and store to Parquet

**Deliverables**:
- [ ] Pydantic models (OpenInterest, FundingRate, Liquidation)
- [ ] BaseFetcher abstract class
- [ ] BinanceFetcher (current OI only)
- [ ] BybitFetcher (current OI only)
- [ ] HyperliquidFetcher (current OI only)
- [ ] ParquetStore (write, read, query)
- [ ] Basic CLI (fetch-oi command)
- [ ] Unit tests for all components

**Dependencies**: None

**Acceptance**: `ccxt-cli fetch-oi BTCUSDT-PERP` returns and stores OI from all exchanges

---

### Phase 2: Historical Data (P1 Stories: Historical OI)

**Goal**: Fetch and store historical OI with pagination and incremental updates

**Deliverables**:
- [ ] Historical OI fetching with pagination
- [ ] Incremental update logic (fetch only new)
- [ ] Date range queries
- [ ] CLI extensions (fetch-oi --from --to)
- [ ] Tests for pagination edge cases

**Dependencies**: Phase 1

**Acceptance**: `ccxt-cli fetch-oi BTCUSDT-PERP --from 2025-01-01 --to 2025-01-31` fetches 30 days in <60s

---

### Phase 3: Funding Rates (P2 Stories)

**Goal**: Add funding rate fetching (current + historical)

**Deliverables**:
- [ ] Funding rate fetcher methods
- [ ] FundingRate storage
- [ ] CLI command (fetch-funding)
- [ ] Tests

**Dependencies**: Phase 1

**Acceptance**: `ccxt-cli fetch-funding BTCUSDT-PERP` returns current and historical funding

---

### Phase 4: Liquidations Stream (P2 Stories)

**Goal**: Real-time liquidation streaming via WebSocket

**Deliverables**:
- [ ] WebSocket liquidation handler
- [ ] Reconnection with backoff
- [ ] Liquidation storage
- [ ] CLI command (stream-liquidations)
- [ ] Tests with mock WebSocket

**Dependencies**: Phase 1

**Acceptance**: `ccxt-cli stream-liquidations BTCUSDT-PERP` streams events in real-time

---

### Phase 5: Daemon Mode (P3 Stories)

**Goal**: Background service for continuous data collection

**Deliverables**:
- [ ] Scheduler integration (APScheduler)
- [ ] Daemon runner class
- [ ] Graceful shutdown handling
- [ ] CLI command (daemon start/stop)
- [ ] Integration tests (24h stability)

**Dependencies**: Phases 1-4

**Acceptance**: `ccxt-cli daemon start` runs 24+ hours without issues

---

## File Structure

```
scripts/ccxt_pipeline/
├── __init__.py
├── __main__.py              # Entry point
├── cli.py                   # CLI commands (click/typer)
├── config.py                # Configuration (Pydantic Settings)
│
├── models/
│   ├── __init__.py
│   ├── open_interest.py     # OpenInterest model
│   ├── funding_rate.py      # FundingRate model
│   └── liquidation.py       # Liquidation model
│
├── fetchers/
│   ├── __init__.py
│   ├── base.py              # BaseFetcher ABC
│   ├── binance.py           # BinanceFetcher
│   ├── bybit.py             # BybitFetcher
│   └── hyperliquid.py       # HyperliquidFetcher
│
├── storage/
│   ├── __init__.py
│   └── parquet_store.py     # ParquetStore (read/write/query)
│
├── scheduler/
│   ├── __init__.py
│   └── daemon.py            # DaemonRunner
│
└── utils/
    ├── __init__.py
    ├── rate_limiter.py      # Rate limiting utilities
    └── logging.py           # Logging setup

tests/
├── ccxt_pipeline/
│   ├── test_models.py
│   ├── test_fetchers.py
│   ├── test_storage.py
│   ├── test_cli.py
│   └── test_daemon.py
└── integration/
    └── test_ccxt_pipeline_integration.py
```

## API Design

### Public Interface

```python
# Fetcher Interface
class BaseFetcher(ABC):
    async def fetch_open_interest(self, symbol: str) -> OpenInterest: ...
    async def fetch_open_interest_history(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[OpenInterest]: ...
    async def fetch_funding_rate(self, symbol: str) -> FundingRate: ...
    async def fetch_funding_rate_history(
        self, symbol: str, start: datetime, end: datetime
    ) -> list[FundingRate]: ...
    async def stream_liquidations(
        self, symbol: str, callback: Callable[[Liquidation], None]
    ) -> None: ...

# Storage Interface
class ParquetStore:
    def write(self, data: list[OpenInterest | FundingRate | Liquidation]) -> None: ...
    def read(
        self, data_type: type, symbol: str, start: datetime, end: datetime
    ) -> list: ...
    def get_last_timestamp(self, data_type: type, symbol: str) -> datetime | None: ...

# CLI Interface
ccxt-cli fetch-oi <SYMBOL> [--exchange EXCHANGE] [--from DATE] [--to DATE]
ccxt-cli fetch-funding <SYMBOL> [--exchange EXCHANGE] [--from DATE] [--to DATE]
ccxt-cli stream-liquidations <SYMBOL> [--exchange EXCHANGE]
ccxt-cli daemon start [--config CONFIG]
ccxt-cli daemon stop
```

### Configuration

```python
class CCXTPipelineConfig(BaseSettings):
    # Storage
    catalog_path: Path = Path("/media/sam/1TB/nautilus_dev/data/ccxt_catalog")

    # Exchanges
    exchanges: list[str] = ["binance", "bybit", "hyperliquid"]

    # Symbols
    symbols: list[str] = ["BTCUSDT-PERP", "ETHUSDT-PERP"]

    # Scheduler
    oi_fetch_interval_seconds: int = 300  # 5 minutes
    funding_fetch_interval_seconds: int = 3600  # 1 hour

    # API Keys (loaded from env)
    binance_api_key: str | None = None
    binance_api_secret: str | None = None

    class Config:
        env_prefix = "CCXT_"
```

## Testing Strategy

### Unit Tests
- [ ] Test Pydantic model validation (valid/invalid data)
- [ ] Test fetcher methods with mocked CCXT responses
- [ ] Test storage write/read/query operations
- [ ] Test CLI commands with mocked backend
- [ ] Test rate limiter behavior

### Integration Tests
- [ ] Test real API calls to exchanges (sandbox/testnet)
- [ ] Test end-to-end fetch → store → read flow
- [ ] Test incremental updates
- [ ] Test pagination for large date ranges
- [ ] Test WebSocket reconnection

### Performance Tests
- [ ] Benchmark concurrent fetching (3 exchanges)
- [ ] Benchmark storage write throughput
- [ ] Memory usage during long runs
- [ ] 24-hour daemon stability test

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Exchange API changes | High | Medium | Pin CCXT version, monitor changelogs |
| Rate limit exceeded | Medium | Medium | Built-in CCXT rate limiter + custom backoff |
| Bybit OI history bug | Low | Known | Workaround: smaller date chunks |
| Hyperliquid no liquidations | Low | Possible | Document limitation, use polling fallback |
| Disk full | Medium | Low | Pre-check disk space, log warnings |
| Memory leak in daemon | High | Low | Regular profiling, integration tests |

## Dependencies

### External Dependencies
- ccxt >= 4.4.0 (includes Pro features)
- pydantic >= 2.0
- pyarrow >= 14.0
- click or typer (CLI)
- apscheduler >= 3.10 (daemon)

### Internal Dependencies
- NautilusTrader ParquetDataCatalog (format reference only, no import)

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] CLI commands documented in README
- [ ] Daemon runs 24+ hours without issues
- [ ] Data loadable alongside NautilusTrader catalog
- [ ] Code review approved
