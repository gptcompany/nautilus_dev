# Research: Binance to NautilusTrader v1.222.0 Data Ingestion

**Date**: 2025-12-24
**NautilusTrader Version**: `1.222.0` (nightly, Full Rust)
**Environment**: `/media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/`
**Sources**: Context7, Discord, NautilusTrader nightly docs, Live testing

## Version Verification (2025-12-24)

```
Version: 1.222.0
Rust core (pyo3): ✅ Available
V1 BarDataWrangler: ✅ nautilus_trader.persistence.wranglers
V1 TradeTickDataWrangler: ✅ nautilus_trader.persistence.wranglers
V2 BarDataWranglerV2: ✅ Available (PyO3) - DO NOT USE with BacktestEngine
ParquetDataCatalog: ✅ nautilus_trader.persistence.catalog.parquet
Precision Mode: 128-bit (fixed_size_binary[16]) - Linux default
```

---

## Critical Findings

### 1. Wrangler Selection: V1 vs V2

**Decision**: Use **V1 Wranglers** (`BarDataWrangler`, `TradeTickDataWrangler`)

**Rationale**: V2 wranglers produce PyO3 objects that are NOT compatible with `BacktestEngine.add_data()`. From docs:
> "These PyO3 provided data objects are not compatible where the legacy Cython objects are currently used"

**Why can't we use Rust BacktestEngine with V2 Wranglers?**
- V2 Wranglers produce: `nautilus_trader.core.nautilus_pyo3.model.Bar` (Rust/PyO3)
- BacktestEngine expects: `nautilus_trader.model.data.Bar` (Cython)
- The Rust core is available but BacktestEngine hasn't been fully migrated to accept PyO3 objects yet
- This is a **transition period** - future versions will support V2 wranglers with BacktestEngine

**VERIFIED (2025-12-24)**: BacktestEngine source code (`engine.pyx`) contains EXPLICIT rejection:
```python
if isinstance(data[0], NAUTILUS_PYO3_DATA_TYPES):
    raise TypeError(
        f"Cannot add data of type `{type(data[0]).__name__}` from pyo3 directly to engine. "
        "This will be supported in a future release.",
    )
```

**Discord Confirmation** (2025-11-17, @faysou):
> "rust objects are not supposed to be used now, they are not compatible with the existing cython system"

**Alternatives considered**:
- V2 Wranglers (`BarDataWranglerV2`, `TradeTickDataWranglerV2`) - Rejected due to BacktestEngine incompatibility

| Wrangler | Output Type | BacktestEngine Compatible |
|----------|-------------|---------------------------|
| `BarDataWrangler` (V1) | Cython objects | ✅ Yes |
| `TradeTickDataWrangler` (V1) | Cython objects | ✅ Yes |
| `BarDataWranglerV2` | PyO3 objects | ❌ No (yet) |
| `TradeTickDataWranglerV2` | PyO3 objects | ❌ No (yet) |

**Note**: V1 wranglers are still very fast (~400k records/sec). The bottleneck is typically I/O, not wrangling.

**Alternative: BacktestNode with DataCatalog** (discovered during verification):
```python
from nautilus_trader.backtest.node import BacktestNode

node = BacktestNode(configs=[...])
node.run()  # Uses DataFusion streaming internally - may handle PyO3 differently
```
This high-level API uses DataFusion streaming backend. Worth investigating for future compatibility.

---

### 2. Precision Mode: 128-bit (High Precision)

**Decision**: Ensure catalog is built with **128-bit precision** (`fixed_size_binary[16]`)

**Rationale**: Linux nightly builds use 128-bit by default. Mixing precision modes causes:
```
ParseError("price", "Invalid value length: expected 16, found 8")
```

**Critical**: The old catalog failed with exactly this error:
```
InvalidColumnType("price", 0, FixedSizeBinary(16), Int64)
```

**Verification**:
```python
# Check nightly precision mode
import nautilus_trader
# Linux default = HIGH_PRECISION = 128-bit
```

---

### 3. Instrument ID Format

**Decision**: Use format `{SYMBOL}-PERP.BINANCE` for perpetual futures

**Examples**:
- `BTCUSDT-PERP.BINANCE`
- `ETHUSDT-PERP.BINANCE`

**CryptoPerpetual Creation**:
```python
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue

instrument_id = InstrumentId(
    symbol=Symbol('BTCUSDT-PERP'),
    venue=Venue('BINANCE')
)
```

---

### 4. Binance CSV Format Mapping

#### Klines CSV (1m, 5m, 15m)

**Source columns**:
```csv
open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore
1764547200000,90320.50,90396.90,90254.00,90376.80,393.365,1764547259999,35522468.40870,8771,173.579,15676612.26210,0
```

**Mapping to Bar**:
| CSV Column | Bar Field | Transformation |
|------------|-----------|----------------|
| `open_time` | `ts_event` | `open_time * 1_000_000` (ms → ns) |
| `open` | `open` | `Price.from_str(str(value))` |
| `high` | `high` | `Price.from_str(str(value))` |
| `low` | `low` | `Price.from_str(str(value))` |
| `close` | `close` | `Price.from_str(str(value))` |
| `volume` | `volume` | `Quantity.from_str(str(value))` |
| `close_time` | `ts_init` | `close_time * 1_000_000` (ms → ns) |

**BarType Format**: `BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL`

#### Trades CSV

**Source columns**:
```csv
id,price,qty,quote_qty,time,is_buyer_maker
6954502553,90320.5,0.003,270.9615,1764547200047,true
```

**Mapping to TradeTick**:
| CSV Column | TradeTick Field | Transformation |
|------------|-----------------|----------------|
| `id` | `trade_id` | `str(id)` |
| `price` | `price` | `Price.from_str(str(value))` |
| `qty` | `size` | `Quantity.from_str(str(value))` |
| `time` | `ts_event`, `ts_init` | `time * 1_000_000` (ms → ns) |
| `is_buyer_maker` | `aggressor_side` | `SELLER if true else BUYER` |

**Note**: `is_buyer_maker=true` means the buyer was the maker, so the **seller was the aggressor**.

#### Funding Rate CSV

**Source columns** (monthly files):
```csv
calcTime,fundingIntervalHours,lastFundingRate
1577836800000,8,0.0001
```

**Mapping**: Custom data type needed.

---

### 5. DataFrame Preparation for V1 Wranglers

**BarDataWrangler Requirements**:
```python
import pandas as pd

# MUST have:
# 1. DatetimeIndex with UTC timezone
# 2. Columns: ['open', 'high', 'low', 'close', 'volume']
# 3. All columns as float64

df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
}, index=pd.to_datetime(timestamps, unit='ms', utc=True))

df = df.astype('float64')
```

**TradeTickDataWrangler Requirements**:
```python
# MUST have:
# 1. DatetimeIndex with UTC timezone
# 2. Columns: ['price', 'quantity', 'buyer_maker', 'trade_id']
# NOTE: Column must be 'quantity' NOT 'size' for V1 wrangler

df = pd.DataFrame({
    'price': [...],
    'quantity': [...],          # NOT 'size'
    'buyer_maker': [...],       # bool: True = SELL aggressor
    'trade_id': [...]           # str
}, index=pd.to_datetime(timestamps, unit='ms', utc=True))
```

---

### 6. Catalog Directory Structure

**Expected output structure**:
```
/media/sam/2TB-NVMe/nautilus_catalog_v1222/
├── data/
│   ├── bar/
│   │   ├── BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL/
│   │   │   └── *.parquet
│   │   ├── BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL/
│   │   └── BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL/
│   ├── trade_tick/
│   │   ├── BTCUSDT-PERP.BINANCE/
│   │   └── ETHUSDT-PERP.BINANCE/
│   └── crypto_perpetual/
│       ├── BTCUSDT-PERP.BINANCE/
│       └── ETHUSDT-PERP.BINANCE/
```

---

### 7. Large File Handling

**From Discord** (Dec 15, 2025):
> "I have 30GB of data in ticks... I'm trying to convert the CSV file to Parquet... it uses up all my RAM and crashes"

**Solution**: Process in chunks using generators:
```python
def process_csv_in_chunks(csv_path, chunk_size=100_000):
    for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
        # Transform chunk
        yield transformed_chunk
```

**Alternative**: Use `catalog.write_data()` multiple times with smaller batches.

---

### 8. Key API Signatures

**ParquetDataCatalog**:
```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog

catalog = ParquetDataCatalog(path='/media/sam/2TB-NVMe/nautilus_catalog_v1222/')

# IMPORTANT: Write instrument BEFORE data
catalog.write_data([instrument])
catalog.write_data(bars)
catalog.write_data(ticks)
```

**BarDataWrangler**:
```python
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.model.data import BarType

bar_type = BarType.from_str('BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL')
wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = wrangler.process(df)  # Returns list[Bar]
```

**TradeTickDataWrangler**:
```python
from nautilus_trader.persistence.wranglers import TradeTickDataWrangler

wrangler = TradeTickDataWrangler(instrument=instrument)
ticks = wrangler.process(df)  # Returns list[TradeTick]
```

---

### 9. Validation Strategy

**Step 1**: Verify catalog loads without errors:
```python
catalog = ParquetDataCatalog('/media/sam/2TB-NVMe/nautilus_catalog_v1222/')
instruments = catalog.instruments()
bars = catalog.bars()
print(f"Instruments: {len(instruments)}, Bars: {len(bars)}")
```

**Step 2**: Verify BacktestEngine compatibility:
```python
from nautilus_trader.backtest.engine import BacktestEngine

engine = BacktestEngine()
engine.add_instrument(instrument)
engine.add_data(bars[:1000])  # Test subset
engine.run()
```

---

## Risks Identified

| Risk | Mitigation |
|------|------------|
| Precision mode mismatch | Verify Linux nightly uses 128-bit, test with small subset first |
| Memory exhaustion on large files | Process in chunks (100k rows), use generators |
| V2 wrangler incompatibility | Explicitly use V1 wranglers only |
| Timestamp precision loss | Multiply ms → ns before conversion |
| Duplicate data on incremental runs | Track processed files in state file |

---

## Implementation Approach

1. **Phase 1**: Create instrument definitions (CryptoPerpetual for BTCUSDT, ETHUSDT)
2. **Phase 2**: Convert klines CSV → Bar objects → Parquet (start with 1 month test)
3. **Phase 3**: Convert trades CSV → TradeTick objects → Parquet (chunked processing)
4. **Phase 4**: Add incremental update logic (track last processed file)
5. **Phase 5**: Validate with BacktestEngine

**Estimated bulk conversion time**: ~2 hours for 5 years of BTCUSDT data (based on ~400k bars/sec wrangler performance)
