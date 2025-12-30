# Quickstart: CCXT Multi-Exchange Data Pipeline

## Installation

```bash
# From project root
cd /media/sam/1TB/nautilus_dev

# Install dependencies
uv add ccxt pydantic pyarrow click apscheduler

# Or with pip
pip install ccxt pydantic pyarrow click apscheduler
```

## Configuration

Set environment variables (optional for public data):

```bash
# Binance (required for some endpoints)
export CCXT_BINANCE_API_KEY="your_key"
export CCXT_BINANCE_API_SECRET="your_secret"

# Catalog path (default: ./data/ccxt_catalog)
export CCXT_CATALOG_PATH="/media/sam/1TB/nautilus_dev/data/ccxt_catalog"
```

## Quick Usage

### Fetch Current Open Interest

```bash
# All exchanges
python -m scripts.ccxt_pipeline fetch-oi BTCUSDT-PERP

# Specific exchange
python -m scripts.ccxt_pipeline fetch-oi BTCUSDT-PERP -e binance
```

### Fetch Historical Data

```bash
# Last 7 days of OI
python -m scripts.ccxt_pipeline fetch-oi BTCUSDT-PERP \
    --from $(date -d "7 days ago" +%Y-%m-%d) \
    --to $(date +%Y-%m-%d)

# Funding rate history
python -m scripts.ccxt_pipeline fetch-funding BTCUSDT-PERP \
    --from 2025-01-01 --to 2025-01-15
```

### Stream Liquidations

```bash
# Real-time liquidations (Ctrl+C to stop)
python -m scripts.ccxt_pipeline stream-liquidations BTCUSDT-PERP
```

### Run Daemon

```bash
# Start background collection
python -m scripts.ccxt_pipeline daemon start

# Check status
python -m scripts.ccxt_pipeline daemon status

# Stop daemon
python -m scripts.ccxt_pipeline daemon stop
```

## Python API

```python
import asyncio
from scripts.ccxt_pipeline import CCXTPipeline

async def main():
    pipeline = CCXTPipeline()

    # Fetch current OI
    oi_data = await pipeline.fetch_open_interest("BTCUSDT-PERP")
    for oi in oi_data:
        print(f"{oi.venue}: {oi.open_interest:,.2f} contracts")

    # Fetch historical funding
    from datetime import datetime, timedelta
    funding = await pipeline.fetch_funding_history(
        "BTCUSDT-PERP",
        start=datetime.now() - timedelta(days=7),
        end=datetime.now()
    )
    print(f"Got {len(funding)} funding records")

asyncio.run(main())
```

## Load Data in NautilusTrader

```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog
import pyarrow.parquet as pq

# Load CCXT data
catalog_path = "/media/sam/1TB/nautilus_dev/data/ccxt_catalog"

# Read OI data directly
oi_table = pq.read_table(
    f"{catalog_path}/open_interest/BTCUSDT-PERP.BINANCE/"
)
oi_df = oi_table.to_pandas()
print(oi_df.head())

# Use in strategy via custom data loading
# (OI/Funding are not native NautilusTrader types)
```

## Troubleshooting

### Rate Limit Errors

```bash
# Reduce concurrent requests
export CCXT_MAX_CONCURRENT=2
```

### Connection Issues

```bash
# Enable debug logging
export CCXT_LOG_LEVEL=DEBUG
python -m scripts.ccxt_pipeline fetch-oi BTCUSDT-PERP
```

### Missing Historical Data

Some exchanges have limited history:
- Bybit: Max 200 records per request (workaround: smaller date ranges)
- Hyperliquid: Limited to recent data

## Next Steps

1. **Configure daemon** for 24/7 collection
2. **Set up monitoring** for data completeness
3. **Integrate with strategies** via custom data loading
