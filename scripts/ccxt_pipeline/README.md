# CCXT Multi-Exchange Data Pipeline

A high-performance data pipeline for fetching Open Interest, Funding Rates, and Liquidations from cryptocurrency derivatives exchanges using CCXT.

## Features

- **Multi-Exchange Support**: Binance, Bybit, Hyperliquid
- **Multiple Data Types**: Open Interest, Funding Rates, Liquidations
- **Real-Time Streaming**: WebSocket liquidation streaming with auto-reconnect
- **Historical Data**: Paginated historical data fetching
- **NautilusTrader Compatible**: Parquet storage format
- **Daemon Mode**: 24/7 continuous data collection
- **Rich CLI**: User-friendly command-line interface

## Installation

```bash
# From the repository root
pip install -e scripts/ccxt_pipeline

# Or install dependencies directly
pip install ccxt pydantic pyarrow click rich apscheduler
```

## Quick Start

### Fetch Current Data

```bash
# Fetch Open Interest from all exchanges
ccxt-cli fetch-oi BTCUSDT-PERP

# Fetch from specific exchanges
ccxt-cli fetch-oi BTCUSDT-PERP -e binance -e bybit

# Store to Parquet catalog
ccxt-cli fetch-oi BTCUSDT-PERP --store
```

### Fetch Historical Data

```bash
# Fetch historical OI for date range
ccxt-cli fetch-oi BTCUSDT-PERP --from 2025-01-01 --to 2025-01-31 --store

# Fetch funding rates
ccxt-cli fetch-funding BTCUSDT-PERP --from 2025-01-01 --to 2025-01-07 --store
```

### Stream Liquidations

```bash
# Stream liquidations from all exchanges
ccxt-cli stream-liquidations BTCUSDT-PERP

# Stream and store
ccxt-cli stream-liquidations BTCUSDT-PERP --store

# Quiet mode (store only, no output)
ccxt-cli stream-liquidations BTCUSDT-PERP --store --quiet
```

### Query Stored Data

```bash
# Query OI data
ccxt-cli query oi BTCUSDT-PERP

# Query funding rates from specific exchange
ccxt-cli query funding BTCUSDT-PERP -e binance

# Query with date range and JSON output
ccxt-cli query liquidations BTCUSDT-PERP --from 2025-01-01 --format json -n 100
```

### Daemon Mode

```bash
# Start daemon with defaults
ccxt-cli daemon start

# Custom configuration
ccxt-cli daemon start -s BTCUSDT-PERP -s ETHUSDT-PERP -e binance --oi-interval 1

# Press Ctrl+C to stop gracefully
```

## Configuration

Environment variables:

```bash
export CCXT_CATALOG_PATH=/path/to/parquet/catalog
export CCXT_LOG_LEVEL=INFO
export BINANCE_API_KEY=your_api_key
export BINANCE_API_SECRET=your_api_secret
```

## Data Models

### Open Interest
```python
OpenInterest(
    timestamp: datetime,
    symbol: str,           # e.g., "BTCUSDT-PERP"
    venue: Venue,          # BINANCE, BYBIT, HYPERLIQUID
    open_interest: float,  # In contracts
    open_interest_value: float,  # In USD
)
```

### Funding Rate
```python
FundingRate(
    timestamp: datetime,
    symbol: str,
    venue: Venue,
    funding_rate: float,   # e.g., 0.0001 = 0.01%
    next_funding_time: datetime | None,
    predicted_rate: float | None,
)
```

### Liquidation
```python
Liquidation(
    timestamp: datetime,
    symbol: str,
    venue: Venue,
    side: Side,           # LONG or SHORT
    quantity: float,
    price: float,
    value: float,         # USD value
)
```

## Architecture

```
scripts/ccxt_pipeline/
├── __init__.py
├── __main__.py          # Entry point
├── cli.py               # Click CLI commands
├── config.py            # Pydantic Settings
├── fetchers/
│   ├── __init__.py
│   ├── base.py          # BaseFetcher ABC
│   ├── binance.py       # Binance implementation
│   ├── bybit.py         # Bybit implementation
│   ├── hyperliquid.py   # Hyperliquid implementation
│   └── orchestrator.py  # Concurrent multi-exchange fetching
├── models/
│   ├── __init__.py
│   ├── open_interest.py
│   ├── funding_rate.py
│   └── liquidation.py
├── storage/
│   ├── __init__.py
│   └── parquet_store.py # Parquet read/write
├── scheduler/
│   ├── __init__.py
│   └── daemon.py        # 24/7 daemon runner
└── utils/
    ├── __init__.py
    ├── logging.py
    ├── parsing.py       # Safe parsing utilities
    └── reconnect.py     # WebSocket reconnection
```

## Development

```bash
# Run tests
pytest tests/ccxt_pipeline/ -v

# Run specific test class
pytest tests/ccxt_pipeline/test_daemon.py::TestDaemonScheduling -v

# Code formatting
ruff check scripts/ccxt_pipeline/ --fix
ruff format scripts/ccxt_pipeline/
```

## Exchange Notes

### Binance
- Uses `BTC/USDT:USDT` symbol format for linear perpetuals
- OI history in 5-minute intervals
- Funding every 8 hours
- WebSocket liquidation streaming supported

### Bybit
- Uses `BTC/USDT:USDT` symbol format
- Limited OI history (30 days)
- Funding every 8 hours
- WebSocket liquidation streaming supported

### Hyperliquid
- Uses `BTC/USD:USD` symbol format (USD, not USDT)
- Variable funding intervals (not fixed 8h)
- Liquidation polling fallback (no WebSocket)

## License

MIT License
