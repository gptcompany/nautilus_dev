# CLI Interface Contract

**Version**: 1.0
**Created**: 2025-12-22

## Command Structure

```
ccxt-cli <command> [options]
```

## Commands

### fetch-oi

Fetch Open Interest data.

```bash
ccxt-cli fetch-oi <SYMBOL> [OPTIONS]
```

**Arguments**:
- `SYMBOL` (required): Trading pair symbol (e.g., `BTCUSDT-PERP`)

**Options**:
- `--exchange`, `-e`: Specific exchange (default: all)
  - Values: `binance`, `bybit`, `hyperliquid`, `all`
- `--from`, `-f`: Start date for historical data (ISO format)
- `--to`, `-t`: End date for historical data (ISO format)
- `--output`, `-o`: Output format
  - Values: `json`, `table`, `quiet` (default: `table`)
- `--no-store`: Don't save to catalog

**Examples**:
```bash
# Current OI from all exchanges
ccxt-cli fetch-oi BTCUSDT-PERP

# Current OI from Binance only
ccxt-cli fetch-oi BTCUSDT-PERP -e binance

# Historical OI for date range
ccxt-cli fetch-oi BTCUSDT-PERP --from 2025-01-01 --to 2025-01-31

# Output as JSON
ccxt-cli fetch-oi BTCUSDT-PERP -o json
```

**Output (table)**:
```
┌────────────────────┬──────────────────┬─────────────────┬───────────────────────┐
│ Exchange           │ Symbol           │ Open Interest   │ Value (USD)           │
├────────────────────┼──────────────────┼─────────────────┼───────────────────────┤
│ BINANCE            │ BTCUSDT-PERP     │ 125,432.50      │ $12,543,250,000       │
│ BYBIT              │ BTCUSDT-PERP     │ 85,123.25       │ $8,512,325,000        │
│ HYPERLIQUID        │ BTC-USD-PERP     │ 42,567.10       │ $4,256,710,000        │
└────────────────────┴──────────────────┴─────────────────┴───────────────────────┘
```

---

### fetch-funding

Fetch Funding Rate data.

```bash
ccxt-cli fetch-funding <SYMBOL> [OPTIONS]
```

**Arguments**:
- `SYMBOL` (required): Trading pair symbol

**Options**:
- `--exchange`, `-e`: Specific exchange (default: all)
- `--from`, `-f`: Start date for historical data
- `--to`, `-t`: End date for historical data
- `--output`, `-o`: Output format
- `--no-store`: Don't save to catalog

**Examples**:
```bash
# Current funding from all exchanges
ccxt-cli fetch-funding BTCUSDT-PERP

# Historical funding
ccxt-cli fetch-funding BTCUSDT-PERP --from 2025-01-01 --to 2025-01-07
```

**Output (table)**:
```
┌────────────────────┬──────────────────┬───────────────┬─────────────────────┐
│ Exchange           │ Symbol           │ Funding Rate  │ Next Funding        │
├────────────────────┼──────────────────┼───────────────┼─────────────────────┤
│ BINANCE            │ BTCUSDT-PERP     │ +0.0100%      │ 2025-01-15 08:00    │
│ BYBIT              │ BTCUSDT-PERP     │ +0.0085%      │ 2025-01-15 08:00    │
│ HYPERLIQUID        │ BTC-USD-PERP     │ -0.0023%      │ 2025-01-15 09:00    │
└────────────────────┴──────────────────┴───────────────┴─────────────────────┘
```

---

### stream-liquidations

Stream real-time liquidation events.

```bash
ccxt-cli stream-liquidations <SYMBOL> [OPTIONS]
```

**Arguments**:
- `SYMBOL` (required): Trading pair symbol

**Options**:
- `--exchange`, `-e`: Specific exchange (default: all with WebSocket support)
- `--output`, `-o`: Output format (`json`, `table`, `raw`)
- `--no-store`: Don't save to catalog
- `--quiet`, `-q`: Suppress output (store only)

**Examples**:
```bash
# Stream liquidations from all exchanges
ccxt-cli stream-liquidations BTCUSDT-PERP

# Stream from Binance only, output as JSON
ccxt-cli stream-liquidations BTCUSDT-PERP -e binance -o json
```

**Output (streaming)**:
```
[2025-01-15 12:34:56] BINANCE BTCUSDT-PERP LONG liquidated: 1.250 @ $99,500.00 ($124,375)
[2025-01-15 12:34:58] BYBIT BTCUSDT-PERP SHORT liquidated: 0.500 @ $100,100.00 ($50,050)
```

---

### daemon

Manage the background data collection daemon.

```bash
ccxt-cli daemon <SUBCOMMAND> [OPTIONS]
```

**Subcommands**:

#### start
```bash
ccxt-cli daemon start [OPTIONS]
```

**Options**:
- `--config`, `-c`: Path to config file
- `--foreground`, `-f`: Run in foreground (don't daemonize)
- `--pid-file`: Custom PID file location

#### stop
```bash
ccxt-cli daemon stop [OPTIONS]
```

**Options**:
- `--pid-file`: Custom PID file location
- `--force`: Force stop without graceful shutdown

#### status
```bash
ccxt-cli daemon status
```

**Output**:
```
Daemon Status: Running
PID: 12345
Uptime: 2d 5h 32m
Last OI Fetch: 2025-01-15 12:30:00
Last Funding Fetch: 2025-01-15 08:00:00
Liquidations Streamed: 1,234
Errors (24h): 3
```

---

### query

Query stored data from catalog.

```bash
ccxt-cli query <DATA_TYPE> <SYMBOL> [OPTIONS]
```

**Arguments**:
- `DATA_TYPE`: Type of data (`oi`, `funding`, `liquidations`)
- `SYMBOL`: Trading pair symbol

**Options**:
- `--exchange`, `-e`: Filter by exchange
- `--from`, `-f`: Start date
- `--to`, `-t`: End date
- `--output`, `-o`: Output format (`json`, `csv`, `table`)
- `--limit`, `-l`: Max records to return

**Examples**:
```bash
# Query last 10 OI records
ccxt-cli query oi BTCUSDT-PERP -l 10

# Export funding to CSV
ccxt-cli query funding BTCUSDT-PERP --from 2025-01-01 -o csv > funding.csv
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Exchange connection error |
| 4 | Rate limit exceeded |
| 5 | Storage error |
| 130 | Interrupted (Ctrl+C) |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CCXT_CATALOG_PATH` | Data catalog directory | `./data/ccxt_catalog` |
| `CCXT_BINANCE_API_KEY` | Binance API key | None |
| `CCXT_BINANCE_API_SECRET` | Binance API secret | None |
| `CCXT_LOG_LEVEL` | Logging level | `INFO` |
