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

## Academic Research → Trading Strategy Pipeline (spec-022)

### Purpose

Bridge between academic research knowledge graph and NautilusTrader strategy development. Automatically classifies trading papers, extracts methodology, maps to native indicators, and generates implementation-ready specs.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACADEMIC RESEARCH PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ ACADEMIC RESEARCH REPO (/media/sam/1TB/academic_research)             │ │
│  │                                                                        │ │
│  │  ┌─────────────────┐    ┌───────────────────┐    ┌─────────────────┐  │ │
│  │  │ Semantic Router │───▶│ Query Classifier  │───▶│ Paper Search    │  │ │
│  │  │ MCP Server      │    │ (trading_strategy │    │ (arXiv, SSRN,   │  │ │
│  │  │                 │    │  stem_cs, biomed) │    │  papers-w-code) │  │ │
│  │  └─────────────────┘    └───────────────────┘    └────────┬────────┘  │ │
│  │                                                            │           │ │
│  │                                                            ▼           │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │ memory.json (Knowledge Graph)                                   │  │ │
│  │  │ - source__ entities (papers)                                    │  │ │
│  │  │ - strategy__ entities (trading methodologies) ← NEW             │  │ │
│  │  │ - concept__ entities (indicators, patterns)                     │  │ │
│  │  │ - Relationships: based_on, uses_concept, targets_asset          │  │ │
│  │  └──────────────────────────────┬──────────────────────────────────┘  │ │
│  │                                 │                                      │ │
│  └─────────────────────────────────┼──────────────────────────────────────┘ │
│                                    │                                        │
│                    sync_research.py (staleness detection)                   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ NAUTILUS DEV REPO (/media/sam/1TB/nautilus_dev)                       │ │
│  │                                                                        │ │
│  │  ┌─────────────────┐    ┌───────────────────┐    ┌─────────────────┐  │ │
│  │  │ strategy-       │───▶│ paper-to-strategy │───▶│ alpha-evolve    │  │ │
│  │  │ researcher      │    │ skill             │    │ agent           │  │ │
│  │  │ agent           │    │                   │    │ (multi-impl)    │  │ │
│  │  └────────┬────────┘    └────────┬──────────┘    └────────┬────────┘  │ │
│  │           │                      │                        │           │ │
│  │           │                      ▼                        │           │ │
│  │           │         ┌───────────────────────┐             │           │ │
│  │           │         │ Mapping Tables        │             │           │ │
│  │           │         │ - indicator_mapping   │             │           │ │
│  │           │         │ - order_mapping       │             │           │ │
│  │           │         └───────────────────────┘             │           │ │
│  │           │                      │                        │           │ │
│  │           ▼                      ▼                        ▼           │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │ specs/{n}-{strategy_name}/                                     │  │ │
│  │  │ - spec.md (NautilusTrader-compatible specification)            │  │ │
│  │  │ - research.md (paper summary, methodology notes)               │  │ │
│  │  │ - plan.md (implementation approach)                            │  │ │
│  │  └──────────────────────────────┬──────────────────────────────────┘  │ │
│  │                                 │                                      │ │
│  │                                 ▼                                      │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │ │
│  │  │ strategies/{strategy_name}/                                    │  │ │
│  │  │ - {strategy_name}_strategy.py (implemented strategy)           │  │ │
│  │  │ - config.py (parameters, risk limits)                          │  │ │
│  │  └─────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
"Research momentum reversal strategies for crypto"
        │
        │ 1. Query classification
        ▼
┌───────────────────┐
│ Semantic Router   │
│ (trading_strategy │
│  confidence > 0.8)│
└────────┬──────────┘
         │
         │ 2. Memory check (incremental support)
         ▼
┌───────────────────┐
│ memory.json       │ ←─ Existing strategy__ entities?
│ (search_nodes)    │    Yes → Differential report
└────────┬──────────┘    No  → Full research
         │
         │ 3. Paper search
         ▼
┌───────────────────┐
│ arXiv (q-fin)     │
│ SSRN              │
│ papers-with-code  │
└────────┬──────────┘
         │
         │ 4. Paper analysis (Claude or Gemini 2M)
         ▼
┌───────────────────┐
│ Methodology       │
│ Extraction        │
│ - entry_logic     │
│ - exit_logic      │
│ - indicators      │
│ - risk_mgmt       │
└────────┬──────────┘
         │
         │ 5. NautilusTrader mapping
         ▼
┌───────────────────┐
│ Native Indicators │    Paper: "20-day EMA"
│ Order Types       │ →  NT: ExponentialMovingAverage(20)
│ Position Sizing   │
└────────┬──────────┘
         │
         │ 6. Spec generation
         ▼
┌───────────────────┐
│ specs/027-crypto- │
│ momentum-reversal/│
│ - spec.md         │
│ - research.md     │
└────────┬──────────┘
         │
         │ 7. Optional: Alpha-Evolve
         ▼
┌───────────────────┐
│ Multi-Impl        │
│ Generation        │
│ - Variant A       │
│ - Variant B       │
│ - Variant C       │
└────────┬──────────┘
         │
         │ 8. Backtest & rank
         ▼
   Best Implementation
   (strategies/momentum_reversal/)
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Semantic Router | academic_research/semantic_router_mcp/ | Query classification |
| strategy__ Schema | academic_research/docs/entity_schemas.md | Entity structure |
| Validation | academic_research/scripts/validate_entity.py | Entity validation |
| strategy-researcher | nautilus_dev/.claude/agents/strategy-researcher.md | Agent definition |
| paper-to-strategy | nautilus_dev/.claude/skills/paper-to-strategy/ | Spec generation |
| Indicator Mapping | nautilus_dev/docs/research/indicator_mapping.md | Paper → NT mapping |
| Order Mapping | nautilus_dev/docs/research/order_mapping.md | Order type mapping |
| Sync Script | nautilus_dev/scripts/sync_research.py | Cross-repo sync |
| Strategies Output | nautilus_dev/docs/research/strategies.json | Synced entities |

### Entity Schema (strategy__)

```yaml
ID Format: strategy__{methodology}_{asset}_{year}
Example: strategy__momentum_btc_2024

Required Observations:
  - source_paper: "source__arxiv_2103_15879"
  - methodology_type: momentum|mean_reversion|market_making|arbitrage|trend_following|statistical_arbitrage
  - entry_logic: "Buy when RSI < 30 and EMA crossover"
  - exit_logic: "Sell when RSI > 70 or trailing stop hit"
  - implementation_status: not_started|in_progress|implemented|validated|production

Relationships:
  - based_on → source__ (paper entity)
  - uses_concept → concept__ (indicator entities)
  - targets_asset → domain__ (asset class)
```

### Sync Mechanism

```python
# scripts/sync_research.py
# Syncs strategy__ entities from academic_research → nautilus_dev

CONFIG = {
    "source": Path("/media/sam/1TB/academic_research/memory.json"),
    "target": Path("/media/sam/1TB/nautilus_dev/docs/research/strategies.json"),
    "entity_prefix": "strategy__",
    "stale_threshold_hours": 24,
}

# Commands
python scripts/sync_research.py           # Normal sync (if stale)
python scripts/sync_research.py --force   # Force sync
python scripts/sync_research.py --dry-run # Preview only
```

### Troubleshooting

See `specs/022-academic-research-pipeline/troubleshooting.md` for:
- Semantic router classification issues
- Entity validation errors
- Sync script problems
- Paper-to-strategy conversion errors

---

## Strategy Organization (100+ Scalable)

### Directory Structure

```
strategies/
├── _templates/           # Base classes (DO NOT MODIFY)
│   ├── base_strategy.py  # BaseStrategy, BaseStrategyConfig
│   └── base_evolve.py    # Alpha-evolve compatible base
│
├── production/           # ✅ Deployed, stable strategies
│   └── {name}/
│       ├── strategy.py
│       ├── config.py
│       └── README.md
│
├── development/          # 🔧 Work in progress
├── evolved/              # 🧬 Alpha-evolve output (gen_XXX/)
├── converted/            # 📜 From /pinescript command
├── archive/              # 📦 Deprecated strategies
│
├── common/               # Shared utilities (risk, sizing)
├── examples/             # Example implementations
└── hyperliquid/          # Exchange-specific strategies
```

### Strategy Lifecycle

```
/pinescript URL        → converted/{name}/
/research + implement  → development/{name}/
alpha-evolve           → evolved/gen_{N}/
Manual promotion       → production/{name}/
Deprecate             → archive/{name}/
```

### Naming Convention

```
{methodology}_{asset}_{version}/
```

Examples: `momentum_btc_v3/`, `mean_reversion_eth_v1/`, `ema_cross_multi_v2/`

### Commands

| Command | Output Location | Purpose |
|---------|-----------------|---------|
| `/research <topic>` | docs/research/ + memory.json | Academic paper research |
| `/pinescript <url>` | strategies/converted/ | TradingView conversion |
| `/speckit.implement` | strategies/development/ | Spec implementation |
| alpha-evolve | strategies/evolved/ | Strategy evolution |

---

## Related Specs

| Spec | Description | Status |
|------|-------------|--------|
| spec-002 | Binance to NautilusTrader v1.222.0 Data Ingestion | Complete |
| spec-003 | TradingView Lightweight Charts Dashboard | Planned |
| spec-006 | Alpha-Evolve Core Infrastructure | Complete |
| spec-007 | Alpha-Evolve Backtest Evaluator | Complete |
| spec-008 | Alpha-Evolve Strategy Templates | Complete |
| spec-009 | Alpha-Evolve Controller & CLI | Complete |
| spec-010 | Alpha-Evolve Grafana Dashboard | Complete |
| spec-011 | Stop-Loss & Position Limits | Planned |
| spec-012 | Circuit Breaker (Max Drawdown) | Planned |
| spec-013 | Daily Loss Limits | Planned |
| spec-014 | TradingNode Configuration | Planned |
| spec-015 | Binance Exec Client Integration | Planned |
| spec-016 | Order Reconciliation | Planned |
| spec-017 | Position Recovery | Planned |
| spec-018 | Redis Cache Backend | Planned |
| spec-019 | Graceful Shutdown | Planned |
| spec-020 | Walk-Forward Validation | Complete |
| spec-022 | Academic Research → Trading Strategy Pipeline | Complete |

---

## Production Readiness Notes

### Version Compatibility (CRITICAL)

> **ATTENZIONE**: Questo progetto usa ESCLUSIVAMENTE NautilusTrader **Nightly** (v1.222.0+).
> Le versioni Stable hanno schema diverso e sono INCOMPATIBILI.

| Componente | Versione | Note |
|------------|----------|------|
| NautilusTrader | Nightly v1.222.0+ | Breaking changes frequenti |
| Python | 3.12.11 | Richiesto per nightly |
| Precision Mode | 128-bit | Linux nightly default |
| Catalog Schema | v1.222.0 | Non retro-compatibile |

### Known Issues (Discord Community - Dec 2025)

#### Binance Adapter
| Issue | Severity | Status |
|-------|----------|--------|
| ADL order handling | MEDIUM | Fixed in nightly |
| Chinese character tokens | LOW | Fixed in nightly |
| STOP_MARKET requires Algo Order API | HIGH | Fixed in dev wheels |
| Order fills not triggering if instrument unavailable | HIGH | In progress (#3006) |

#### Bybit Adapter (Rust Port)
| Issue | Severity | Status |
|-------|----------|--------|
| Hedge mode (`positionIdx`) NOT supported | HIGH | Community PR in progress |
| `bars_timestamp_on_close` not applied to WS bars | MEDIUM | Known limitation |
| 1-bar offset in indicators (WS vs HTTP) | MEDIUM | Known limitation |
| `attachAlgoOrds` not supported | LOW | By design |

#### Interactive Brokers
| Issue | Severity | Status |
|-------|----------|--------|
| Reconciliation issues with external positions | HIGH | Open (#3054) |
| Max tick-by-tick requests limit (10190) | MEDIUM | Known limitation |
| BOND instruments fail reconciliation | LOW | Workaround available |

### Anti-Patterns (NEVER DO)

1. **MAI mischiare stable/nightly catalogs** - Schema incompatibile
2. **MAI caricare dataset interi in memoria** - Usa streaming/chunking
3. **MAI usare df.iterrows()** - 100x più lento, usa vectorized ops
4. **MAI fare live trading in Jupyter notebooks** - Event loop issues
5. **MAI usare low-level API senza setup** - Usa BacktestNode/TradingNode

### Production Requirements

#### Risk Management (MANDATORY)
- [ ] Stop-loss per ogni posizione
- [ ] Max position size limits
- [ ] Circuit breaker (max drawdown)
- [ ] Daily loss limits
- [ ] Margin validation

#### Live Trading Infrastructure
- [ ] TradingNode configuration
- [ ] Exchange exec clients (Binance/Bybit)
- [ ] Order reconciliation
- [ ] Position recovery on restart
- [ ] Redis-backed cache
- [ ] Graceful shutdown

#### Monitoring
- [x] QuestDB metrics storage
- [x] Grafana dashboards
- [x] Alert system (Telegram/Discord)
- [ ] Health checks / heartbeat
- [ ] Performance metrics

### TradingNode Configuration Template

```python
from nautilus_trader.config import (
    TradingNodeConfig,
    CacheConfig,
    DatabaseConfig,
    LiveExecEngineConfig,
    LoggingConfig,
)

config = TradingNodeConfig(
    trader_id="PROD-001",
    logging=LoggingConfig(
        log_level="INFO",
        log_level_file="DEBUG",
    ),
    cache=CacheConfig(
        database=DatabaseConfig(
            host="localhost",
            port=6379,  # Redis
        ),
        persist_account_events=True,  # CRITICO per recovery
    ),
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,  # MINIMO per produzione
        graceful_shutdown_on_exception=True,
    ),
    data_clients={...},
    exec_clients={...},
)
```

---

## Walk-Forward Validation (spec-020)

### Purpose

Prevents overfitting in evolved strategies by testing on out-of-sample data using rolling windows. Implements Lopez de Prado's advanced metrics (Deflated Sharpe Ratio, Probability of Backtest Overfitting).

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     WALK-FORWARD VALIDATION PIPELINE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Strategy Code ─────────────────────────────────────────────────────────┐   │
│        │                                                                │   │
│        ▼                                                                │   │
│  ┌────────────────────────────────────────────────────────────────────┐ │   │
│  │ WalkForwardValidator                                               │ │   │
│  │ ┌──────────────────────────────────────────────────────────────┐   │ │   │
│  │ │ Window Generation (Rolling)                                  │   │ │   │
│  │ │ ├── Train: 6 months  │  Test: 3 months  │  Step: 3 months   │   │ │   │
│  │ │ └── Embargo: 5 days pre-test, 3 days post-test              │   │ │   │
│  │ └──────────────────────────────────────────────────────────────┘   │ │   │
│  │                          │                                         │ │   │
│  │                          ▼                                         │ │   │
│  │ ┌──────────────────────────────────────────────────────────────┐   │ │   │
│  │ │ Per-Window Evaluation                                        │   │ │   │
│  │ │ ├── Window 1: Train → Test (train_metrics, test_metrics)    │   │ │   │
│  │ │ ├── Window 2: Train → Test                                  │   │ │   │
│  │ │ ├── ...                                                      │   │ │   │
│  │ │ └── Window N: Train → Test                                  │   │ │   │
│  │ └──────────────────────────────────────────────────────────────┘   │ │   │
│  │                          │                                         │ │   │
│  │                          ▼                                         │ │   │
│  │ ┌──────────────────────────────────────────────────────────────┐   │ │   │
│  │ │ Metrics Calculation                                          │   │ │   │
│  │ │ ├── Robustness Score (0-100)                                │   │ │   │
│  │ │ │   └── Consistency (30%) + Profitability (40%) + Degradation (30%) │
│  │ │ ├── Deflated Sharpe Ratio (Lopez de Prado Ch. 14)           │   │ │   │
│  │ │ └── Probability of Backtest Overfitting (Ch. 11)            │   │ │   │
│  │ └──────────────────────────────────────────────────────────────┘   │ │   │
│  │                          │                                         │ │   │
│  │                          ▼                                         │ │   │
│  │ ┌──────────────────────────────────────────────────────────────┐   │ │   │
│  │ │ Pass/Fail Criteria                                           │   │ │   │
│  │ │ ├── robustness_score >= 60                                  │   │ │   │
│  │ │ ├── profitable_windows >= 75%                               │   │ │   │
│  │ │ ├── max_drawdown <= 30%                                     │   │ │   │
│  │ │ └── test_sharpe >= 0.5 in majority                          │   │ │   │
│  │ └──────────────────────────────────────────────────────────────┘   │ │   │
│  └────────────────────────────────────────────────────────────────────┘ │   │
│                          │                                              │   │
│                          ▼                                              │   │
│  ┌────────────────────────────────────────────────────────────────────┐ │   │
│  │ WalkForwardResult                                                  │ │   │
│  │ ├── passed: bool                                                  │ │   │
│  │ ├── robustness_score: float                                       │ │   │
│  │ ├── deflated_sharpe_ratio: float                                  │ │   │
│  │ ├── probability_backtest_overfitting: float                       │ │   │
│  │ └── windows: list[WindowResult]                                   │ │   │
│  └────────────────────────────────────────────────────────────────────┘ │   │
│                                                                         │   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Integration with Alpha-Evolve

```python
from scripts.alpha_evolve.walk_forward import WalkForwardConfig
from datetime import datetime

# Configure validation
wf_config = WalkForwardConfig(
    data_start=datetime(2023, 1, 1),
    data_end=datetime(2024, 12, 1),
    train_months=6,
    test_months=3,
    step_months=3,
    embargo_before_days=5,
    embargo_after_days=3,
)

# Run evolution with validation
result, validation = await controller.evolve_with_validation(
    seed_strategy="momentum",
    experiment="my_experiment",
    iterations=50,
    walk_forward_config=wf_config,
)

if validation and validation.passed:
    print("Strategy ready for deployment!")
```

### Key Files

| Component | Location |
|-----------|----------|
| Configuration | `scripts/alpha_evolve/walk_forward/config.py` |
| Validator | `scripts/alpha_evolve/walk_forward/validator.py` |
| Metrics (DSR, PBO) | `scripts/alpha_evolve/walk_forward/metrics.py` |
| Report Generation | `scripts/alpha_evolve/walk_forward/report.py` |
| CLI | `scripts/alpha_evolve/walk_forward/cli.py` |
| Tests | `tests/test_walk_forward/` |

### Lopez de Prado Metrics

**Deflated Sharpe Ratio (DSR)** - Ch. 14:
- Adjusts Sharpe for multiple testing
- Formula: `DSR = Z⁻¹[Φ(SR) - ln(N)/√N]`
- Always <= raw Sharpe

**Probability of Backtest Overfitting (PBO)** - Ch. 11:
- Estimates false positive probability
- Uses combinatorial permutations
- PBO > 0.5 indicates likely overfitting

---

### Indicator Warmup Pattern

```python
def on_start(self):
    """Request historical data for indicator warmup."""
    self.request_bars(
        bar_type=self.bar_type,
        start=self.clock.utc_now() - timedelta(days=2),
        callback=self._warm_up_complete
    )

def on_historical_data(self, data):
    """Process historical bars to warm up indicators."""
    for bar in data.bars:
        self.ema.handle_bar(bar)
```

### Stop-Loss Pattern (Bybit)

```python
# NOTA: Per SHORT positions, trigger SOPRA entry price
stop_loss_order = self.order_factory.stop_market(
    instrument_id=instrument.id,
    order_side=OrderSide.BUY,  # Chiude SHORT
    quantity=position.quantity,
    trigger_price=instrument.make_price(stop_price),  # ABOVE entry
)
self.submit_order(stop_loss_order)
```
