# NautilusTrader Architecture

> **Note**: This file is the canonical source for architecture documentation.
> When implementing new specs, update THIS file (not CLAUDE.md).

## Current Environment (2025-12-24)

### NautilusTrader Nightly v1.222.0 (Active)

| Component | Status | Details |
|-----------|--------|---------|
| **Version** | 1.222.0 | Nightly build |
| **Python** | 3.12.11 | Required for nightly |
| **Rust Core** | Available | `nautilus_pyo3` module |
| **Precision Mode** | 128-bit | `fixed_size_binary[16]` - Linux default |
| **Location** | `/media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/` |

**Activation**:
```bash
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
python -c "import nautilus_trader; print(nautilus_trader.__version__)"
# Expected: 1.222.0
```

---

## Wrangler Compatibility Matrix

### VERIFIED (2025-12-24)

| Component | Type | BacktestEngine Compatible |
|-----------|------|---------------------------|
| `BarDataWrangler` (V1) | Cython | Yes |
| `TradeTickDataWrangler` (V1) | Cython | Yes |
| `BarDataWranglerV2` | PyO3/Rust | **NO** |
| `TradeTickDataWranglerV2` | PyO3/Rust | **NO** |
| `BacktestEngine` | Cython | N/A (expects Cython data) |

**Source Verification**: `engine.pyx` lines 733-807 contain explicit rejection:
```python
if isinstance(data[0], NAUTILUS_PYO3_DATA_TYPES):
    raise TypeError(
        f"Cannot add data of type `{type(data[0]).__name__}` from pyo3 directly to engine. "
        "This will be supported in a future release.",
    )
```

**Migration Status**: Rust BacktestEngine is in development but NOT available yet.

---

## Data Pipeline Architecture

### Binance to NautilusTrader Ingestion (spec-002)

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
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────┐             │
│  │ CSV Parser  │───▶│ Wrangler Factory │───▶│  Catalog    │             │
│  │  (pandas)   │    │   (V1 or V2)     │    │  Writer     │             │
│  └─────────────┘    └──────────────────┘    └─────────────┘             │
│                                                                         │
│  wrangler_factory.py: V2-ready architecture                             │
│  - use_rust_wranglers=False → V1 (current)                              │
│  - use_rust_wranglers=True  → V2 (when available)                       │
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

---

## Key Technical Decisions

### 1. Wrangler Version Selection

**Decision**: V1 Wranglers with V2-Ready Architecture

**Rationale**: V2 wranglers (PyO3/Rust) are incompatible with current BacktestEngine (Cython).

**Implementation**:
```python
# wrangler_factory.py
def get_bar_wrangler(instrument, bar_type, config):
    if config.use_rust_wranglers:
        from nautilus_trader.core.nautilus_pyo3 import BarDataWrangler
    else:
        from nautilus_trader.persistence.wranglers import BarDataWrangler
    return BarDataWrangler(instrument=instrument, bar_type=bar_type)
```

**Migration Path**: When Rust BacktestEngine is available, flip `use_rust_wranglers=True`.

### 2. Precision Mode

**Decision**: 128-bit precision (`fixed_size_binary[16]`)

**Rationale**: Linux nightly builds default to 128-bit. Mixing precision modes causes:
```
InvalidColumnType("price", 0, FixedSizeBinary(16), Int64)
```

### 3. Data Processing

**Decision**: Chunked processing (100k rows per chunk)

**Rationale**: Trade tick data is 500M+ records. Must use generators to avoid memory exhaustion.

---

## Instrument ID Conventions

### Perpetual Futures

| Symbol | Instrument ID | BarType |
|--------|--------------|---------|
| BTCUSDT | `BTCUSDT-PERP.BINANCE` | `BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL` |
| ETHUSDT | `ETHUSDT-PERP.BINANCE` | `ETHUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL` |

### CryptoPerpetual Creation

```python
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue

instrument = CryptoPerpetual(
    instrument_id=InstrumentId(Symbol('BTCUSDT-PERP'), Venue('BINANCE')),
    raw_symbol=Symbol('BTCUSDT'),
    base_currency=Currency.from_str('BTC'),
    quote_currency=Currency.from_str('USDT'),
    settlement_currency=Currency.from_str('USDT'),
    is_inverse=False,
    price_precision=2,
    size_precision=3,
    price_increment=Price.from_str('0.01'),
    size_increment=Quantity.from_str('0.001'),
    # ... additional fields
)
```

---

## Binance CSV Format Reference

### Klines (OHLCV)

```csv
open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore
1764547200000,90320.50,90396.90,90254.00,90376.80,393.365,1764547259999,35522468.40870,8771,173.579,15676612.26210,0
```

**Mapping**:
| CSV Column | NautilusTrader | Transformation |
|------------|----------------|----------------|
| `open_time` | `ts_event` | `× 1_000_000` (ms → ns) |
| `open/high/low/close` | Price fields | `Price.from_str()` |
| `volume` | `volume` | `Quantity.from_str()` |
| `close_time` | `ts_init` | `× 1_000_000` (ms → ns) |

### Trades

```csv
id,price,qty,quote_qty,time,is_buyer_maker
6954502553,90320.5,0.003,270.9615,1764547200047,true
```

**Mapping**:
| CSV Column | NautilusTrader | Transformation |
|------------|----------------|----------------|
| `id` | `trade_id` | `str(id)` |
| `price` | `price` | `Price.from_str()` |
| `qty` | `size` | `Quantity.from_str()` |
| `time` | `ts_event`, `ts_init` | `× 1_000_000` (ms → ns) |
| `is_buyer_maker` | `aggressor_side` | `SELLER if true else BUYER` |

**Note**: `is_buyer_maker=true` means buyer was maker, so **seller was aggressor**.

---

## Storage Locations

| Resource | Path |
|----------|------|
| Nightly Environment | `/media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/` |
| Source Data (Binance CSV) | `/media/sam/3TB-WDC/binance-history-data-downloader/data/` |
| Target Catalog | `/media/sam/2TB-NVMe/nautilus_catalog_v1222/` |
| Old Catalog (INCOMPATIBLE) | `/media/sam/2TB-NVMe/nautilus_binance_catalog/` |

---

## Discord Knowledge References

Key verified information from Discord community:

1. **V2 Wranglers** (2025-11-17, @faysou):
   > "rust objects are not supposed to be used now, they are not compatible with the existing cython system"

2. **Rust Backtest Status** (2025-10-08, @cjdsellers):
   > "Backtesting is mostly done but requires more wiring up and work."

3. **Large File Processing**:
   > "I have 30GB of data in ticks... I'm trying to convert the CSV file to Parquet... it uses up all my RAM and crashes"

   **Solution**: Chunked processing with generators (100k rows per chunk).

---

## Alpha-Evolve Strategy Evolution (specs 006-010)

### Purpose

Evolutionary strategy discovery using LLM-driven mutations. Inspired by pwb-alphaevolve, adapted for NautilusTrader architecture.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ALPHA-EVOLVE SYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ CONTROLLER (spec-009)                                                  │ │
│  │ - Async evolution loop                                                 │ │
│  │ - Parent selection: 10% elite / 70% exploit / 20% explore             │ │
│  │ - Integrates with alpha-evolve agent for LLM mutations                │ │
│  │ - CLI interface: evolve start/status/best/export                      │ │
│  └───────────────────────────────────┬────────────────────────────────────┘ │
│                                      │                                      │
│                                      ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ STRATEGY TEMPLATES (spec-008)                                         │ │
│  │ - BaseEvolveStrategy: equity tracking, order helpers                  │ │
│  │ - EVOLVE-BLOCK markers for surgical mutations                         │ │
│  │ - Native Rust indicators (EMA, RSI, etc.)                            │ │
│  │ - Seed: MomentumEvolveStrategy (dual EMA crossover)                  │ │
│  └───────────────────────────────────┬────────────────────────────────────┘ │
│                                      │                                      │
│                                      ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ BACKTEST EVALUATOR (spec-007)                                         │ │
│  │ - Dynamic strategy loading from string                                │ │
│  │ - NautilusTrader BacktestNode wrapper                                 │ │
│  │ - KPI extraction: Sharpe, Calmar, CAGR, MaxDD                        │ │
│  │ - ParquetDataCatalog for streaming data                              │ │
│  └───────────────────────────────────┬────────────────────────────────────┘ │
│                                      │                                      │
│                                      ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ CORE INFRASTRUCTURE (spec-006)                                        │ │
│  │ - Patching: EVOLVE-BLOCK regex replacement + indent preservation      │ │
│  │ - Store: SQLite hall-of-fame (top_k, sample, prune)                  │ │
│  │ - Config: YAML for evolution parameters                              │ │
│  └───────────────────────────────────┬────────────────────────────────────┘ │
│                                      │                                      │
│                                      ▼                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ GRAFANA DASHBOARD (spec-010)                                          │ │
│  │ - Fitness progress over generations                                   │ │
│  │ - Top 10 strategies leaderboard                                       │ │
│  │ - Population statistics                                               │ │
│  │ - Mutation success rate                                               │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Seed Strategy (strategies/templates/momentum_evolve.py)
        │
        │ 1. Insert into Hall-of-Fame
        ▼
┌───────────────────┐
│ Parent Selection  │ ←──────────────────────────────────────┐
│ (elite/exploit/   │                                         │
│  explore)         │                                         │
└────────┬──────────┘                                         │
         │                                                     │
         │ 2. Build mutation prompt                           │
         ▼                                                     │
┌───────────────────┐                                         │
│ Claude Code       │                                         │
│ (alpha-evolve     │                                         │
│  agent)           │                                         │
└────────┬──────────┘                                         │
         │                                                     │
         │ 3. Return mutated EVOLVE-BLOCK                     │
         ▼                                                     │
┌───────────────────┐                                         │
│ Patching System   │                                         │
│ (apply mutation)  │                                         │
└────────┬──────────┘                                         │
         │                                                     │
         │ 4. Generate child strategy code                    │
         ▼                                                     │
┌───────────────────┐                                         │
│ NautilusTrader    │                                         │
│ BacktestNode      │                                         │
└────────┬──────────┘                                         │
         │                                                     │
         │ 5. Extract KPIs (Sharpe, Calmar, CAGR, DD)        │
         ▼                                                     │
┌───────────────────┐                                         │
│ Hall-of-Fame      │─────────────────────────────────────────┘
│ (insert, prune,   │
│  rank)            │
└───────────────────┘
         │
         │ After N iterations
         ▼
   Best Strategy (top_k(k=1))
```

### Key Files

| Component | Location |
|-----------|----------|
| Patching System | `scripts/alpha_evolve/patching.py` |
| SQLite Store | `scripts/alpha_evolve/store.py` |
| Backtest Evaluator | `scripts/alpha_evolve/evaluator.py` |
| Evolution Controller | `scripts/alpha_evolve/controller.py` |
| CLI Runner | `scripts/alpha_evolve/cli.py` |
| Base Strategy Template | `strategies/templates/base_evolve.py` |
| Seed Strategy | `strategies/templates/momentum_evolve.py` |
| Grafana Dashboard | `monitoring/grafana/dashboards/alpha-evolve.json` |

### Configuration

```yaml
# scripts/alpha_evolve/config.yaml
evolution:
  population_size: 500
  archive_size: 50
  elite_ratio: 0.1       # Top 10% for elite selection
  exploration_ratio: 0.2 # Random 20% for exploration
  max_concurrent: 2      # Memory constraint

backtest:
  symbols: ["BTCUSDT-PERP.BINANCE", "ETHUSDT-PERP.BINANCE"]
  start_date: "2024-01-01"
  end_date: "2024-12-01"
  initial_capital: 100000.0
  data_catalog: "/media/sam/2TB-NVMe/nautilus_catalog_v1222/"

fitness:
  primary_metric: "calmar"
  constraints:
    max_drawdown: -0.25
    min_sharpe: 0.5
```

### Dependencies

- **Claude Code alpha-evolve agent**: LLM-guided mutations (zero cost)
- **NautilusTrader nightly v1.222.0**: BacktestNode for evaluation
- **ParquetDataCatalog**: Streaming historical data
- **Grafana + QuestDB**: Monitoring dashboard (already running)

---

## Related Specs

| Spec | Description | Status |
|------|-------------|--------|
| spec-002 | Binance to NautilusTrader v1.222.0 Data Ingestion | In Progress |
| spec-003 | TradingView Lightweight Charts Dashboard | Planned |
| spec-006 | Alpha-Evolve Core Infrastructure | Draft |
| spec-007 | Alpha-Evolve Backtest Evaluator | Draft |
| spec-008 | Alpha-Evolve Strategy Templates | Draft |
| spec-009 | Alpha-Evolve Controller & CLI | Draft |
| spec-010 | Alpha-Evolve Grafana Dashboard | Draft |
