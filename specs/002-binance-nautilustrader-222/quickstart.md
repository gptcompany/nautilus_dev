# Quickstart: Binance to NautilusTrader v1.222.0 Data Ingestion

## Prerequisites

```bash
# 1. Activate nightly environment
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate

# 2. Verify version
python -c "import nautilus_trader; print(nautilus_trader.__version__)"
# Expected: 1.222.0

# 3. Verify source data exists
ls /media/sam/3TB-WDC/binance-history-data-downloader/data/BTCUSDT/klines/1m/ | head -5
```

---

## Quick Test (1 Month Subset)

### Step 1: Create Instrument

```python
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.objects import Currency, Money, Price, Quantity
from nautilus_trader.core.datetime import dt_to_unix_nanos
from decimal import Decimal
from datetime import datetime
import pytz

# Create BTCUSDT perpetual instrument
btc = Currency.from_str('BTC')
usdt = Currency.from_str('USDT')

instrument = CryptoPerpetual(
    instrument_id=InstrumentId(Symbol('BTCUSDT-PERP'), Venue('BINANCE')),
    raw_symbol=Symbol('BTCUSDT'),
    base_currency=btc,
    quote_currency=usdt,
    settlement_currency=usdt,
    is_inverse=False,
    price_precision=2,
    size_precision=3,
    price_increment=Price.from_str('0.01'),
    size_increment=Quantity.from_str('0.001'),
    max_quantity=Quantity.from_str('1000'),
    min_quantity=Quantity.from_str('0.001'),
    max_notional=None,
    min_notional=Money(10, usdt),
    max_price=Price.from_str('1000000'),
    min_price=Price.from_str('0.01'),
    margin_init=Decimal('0.05'),
    margin_maint=Decimal('0.025'),
    maker_fee=Decimal('0.0002'),
    taker_fee=Decimal('0.0004'),
    ts_event=dt_to_unix_nanos(datetime(2019, 9, 1, tzinfo=pytz.UTC)),
    ts_init=dt_to_unix_nanos(datetime(2019, 9, 1, tzinfo=pytz.UTC)),
)
print(f"Created: {instrument.id}")
```

### Step 2: Convert Klines CSV to Bars

```python
import pandas as pd
import glob
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.model.data import BarType

# Load 1 month of klines
csv_files = sorted(glob.glob(
    '/media/sam/3TB-WDC/binance-history-data-downloader/data/BTCUSDT/klines/1m/BTCUSDT-1m-2024-01-*.csv'
))

dfs = []
for f in csv_files:
    df = pd.read_csv(f)
    dfs.append(df)

data = pd.concat(dfs, ignore_index=True)

# Transform to wrangler format
bar_df = pd.DataFrame({
    'open': data['open'].astype('float64'),
    'high': data['high'].astype('float64'),
    'low': data['low'].astype('float64'),
    'close': data['close'].astype('float64'),
    'volume': data['volume'].astype('float64'),
}, index=pd.to_datetime(data['open_time'], unit='ms', utc=True))

# Create bars using V1 wrangler
bar_type = BarType.from_str('BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL')
wrangler = BarDataWrangler(bar_type=bar_type, instrument=instrument)
bars = wrangler.process(bar_df)

print(f"Created {len(bars)} bars")
print(f"First: {bars[0]}")
print(f"Last: {bars[-1]}")
```

### Step 3: Write to Catalog

```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog

# Initialize catalog
catalog_path = '/media/sam/2TB-NVMe/nautilus_catalog_v1222'
catalog = ParquetDataCatalog(catalog_path)

# IMPORTANT: Write instrument FIRST
catalog.write_data([instrument])

# Write bars
catalog.write_data(bars)

print(f"Catalog written to: {catalog_path}")
```

### Step 4: Validate

```python
# Reload and verify
catalog = ParquetDataCatalog(catalog_path)

instruments = catalog.instruments()
print(f"Instruments: {len(instruments)}")

bars = catalog.bars()
print(f"Bars: {len(bars)}")
print(f"First bar: {bars[0]}")
```

### Step 5: Test with BacktestEngine

```python
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig

config = BacktestEngineConfig(
    trader_id='BACKTESTER-001',
)

engine = BacktestEngine(config=config)
engine.add_instrument(instrument)
engine.add_data(bars[:10000])  # Test with subset

print("BacktestEngine: COMPATIBLE")
```

---

## Full Conversion

Once the quick test passes, run full conversion:

```bash
# Convert all BTCUSDT 1-minute klines (5+ years)
binance2nautilus convert BTCUSDT klines --timeframe 1m --verbose

# Convert BTCUSDT trades (large dataset, chunked)
binance2nautilus convert BTCUSDT trades --chunk-size 100000 --verbose

# Convert ETHUSDT
binance2nautilus convert ETHUSDT klines --timeframe 1m
binance2nautilus convert ETHUSDT trades

# Validate final catalog
binance2nautilus validate /media/sam/2TB-NVMe/nautilus_catalog_v1222 --backtest-test
```

---

## Incremental Updates

After initial conversion, set up daily updates:

```bash
# Add to n8n workflow or cron (after 03:45 daily download)
# 0 4 * * * /path/to/binance2nautilus update

binance2nautilus update
```

---

## Troubleshooting

### Schema Error
```
ParseError("price", "Invalid value length: expected 16, found 8")
```
**Cause**: Precision mode mismatch (8-bit vs 16-bit)
**Fix**: Ensure using Linux nightly build (128-bit default)

### Memory Error
```
MemoryError: Unable to allocate...
```
**Cause**: Loading too much data at once
**Fix**: Use `--chunk-size 50000` or process fewer files

### V2 Wrangler Error
```
PyO3 objects not compatible with BacktestEngine
```
**Cause**: Using V2 wranglers instead of V1
**Fix**: Use `BarDataWrangler` not `BarDataWranglerV2`

---

## Expected Performance

| Data Type | Volume | Expected Time |
|-----------|--------|---------------|
| Klines 1m (5 years) | ~2.6M bars | ~10 minutes |
| Trades (5 years) | ~500M ticks | ~2 hours |
| Funding (5 years) | ~5.5K records | ~10 seconds |

**Wrangler throughput**: ~400,000 records/second
