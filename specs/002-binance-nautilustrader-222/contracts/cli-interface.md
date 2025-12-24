# CLI Interface Contract: Binance to Nautilus Converter

## Overview

Command-line interface for converting Binance historical data to NautilusTrader v1.222.0 ParquetDataCatalog format.

---

## Commands

### `convert`

Convert historical data from Binance CSV to Nautilus Parquet catalog.

```bash
binance2nautilus convert [OPTIONS] SYMBOL DATA_TYPE
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SYMBOL` | str | Yes | Trading symbol (e.g., `BTCUSDT`, `ETHUSDT`) |
| `DATA_TYPE` | str | Yes | Data type: `klines`, `trades`, `funding` |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--source-dir` | path | `/media/sam/3TB-WDC/binance-history-data-downloader/data` | Source CSV directory |
| `--output-dir` | path | `/media/sam/2TB-NVMe/nautilus_catalog_v1222` | Output catalog path |
| `--timeframe` | str | `1m` | Timeframe for klines (`1m`, `5m`, `15m`) |
| `--start-date` | date | None | Start date (YYYY-MM-DD), default: earliest |
| `--end-date` | date | None | End date (YYYY-MM-DD), default: latest |
| `--chunk-size` | int | 100000 | Rows per processing chunk |
| `--dry-run` | flag | False | Simulate without writing |
| `--verbose` | flag | False | Enable detailed logging |

**Examples**:
```bash
# Convert all BTCUSDT 1-minute klines
binance2nautilus convert BTCUSDT klines --timeframe 1m

# Convert trades for specific date range
binance2nautilus convert BTCUSDT trades --start-date 2024-01-01 --end-date 2024-12-31

# Dry run to see what would be processed
binance2nautilus convert ETHUSDT klines --dry-run --verbose
```

**Exit Codes**:
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Source data not found |
| 4 | Insufficient disk space |
| 5 | Schema validation failed |

---

### `update`

Incremental update - process only new files since last run.

```bash
binance2nautilus update [OPTIONS] [SYMBOL]
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SYMBOL` | str | No | Specific symbol, or all if omitted |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--source-dir` | path | (from config) | Source CSV directory |
| `--output-dir` | path | (from config) | Output catalog path |
| `--force` | flag | False | Reprocess even if already converted |

**Examples**:
```bash
# Update all symbols
binance2nautilus update

# Update only BTCUSDT
binance2nautilus update BTCUSDT

# Force reprocess last 7 days
binance2nautilus update --start-date 2025-12-17 --force
```

---

### `validate`

Validate catalog integrity and BacktestEngine compatibility.

```bash
binance2nautilus validate [OPTIONS] CATALOG_PATH
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `CATALOG_PATH` | path | Yes | Path to Nautilus catalog |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--quick` | flag | False | Skip full data integrity check |
| `--backtest-test` | flag | False | Run sample backtest to verify |
| `--fix` | flag | False | Attempt to fix minor issues |

**Examples**:
```bash
# Quick validation
binance2nautilus validate /media/sam/2TB-NVMe/nautilus_catalog_v1222 --quick

# Full validation with backtest test
binance2nautilus validate /media/sam/2TB-NVMe/nautilus_catalog_v1222 --backtest-test
```

**Output**:
```
Catalog Validation Report
========================
Path: /media/sam/2TB-NVMe/nautilus_catalog_v1222

Instruments: 2
  - BTCUSDT-PERP.BINANCE (CryptoPerpetual)
  - ETHUSDT-PERP.BINANCE (CryptoPerpetual)

Bars:
  - BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL: 2,628,000 bars
  - ETHUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL: 2,628,000 bars

Trade Ticks:
  - BTCUSDT-PERP.BINANCE: 45,000,000 ticks
  - ETHUSDT-PERP.BINANCE: 32,000,000 ticks

Schema: v1.222.0 (128-bit precision)
BacktestEngine: COMPATIBLE

Status: VALID
```

---

### `status`

Show conversion progress and catalog statistics.

```bash
binance2nautilus status [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--source-dir` | path | (from config) | Source CSV directory |
| `--output-dir` | path | (from config) | Output catalog path |
| `--json` | flag | False | Output as JSON |

**Examples**:
```bash
# Show status
binance2nautilus status

# JSON output for automation
binance2nautilus status --json
```

**Output**:
```
Conversion Status
=================
Source: /media/sam/3TB-WDC/binance-history-data-downloader/data
Catalog: /media/sam/2TB-NVMe/nautilus_catalog_v1222

BTCUSDT:
  klines_1m:  [##########] 100% (2628 files)
  klines_5m:  [#######---]  70% (1840/2628 files)
  trades:     [##--------]  20% (525/2628 files)
  funding:    [##########] 100% (60 files)

ETHUSDT:
  klines_1m:  [##########] 100% (2628 files)
  trades:     [----------]   0% (pending)

Last update: 2025-12-24 03:45:00 UTC
Next scheduled: 2025-12-25 03:45:00 UTC
```

---

## Configuration File

Located at `~/.config/binance2nautilus/config.yaml`:

```yaml
# Default paths
source_dir: /media/sam/3TB-WDC/binance-history-data-downloader/data
output_dir: /media/sam/2TB-NVMe/nautilus_catalog_v1222

# Symbols to process
symbols:
  - BTCUSDT
  - ETHUSDT

# Data types to convert
data_types:
  klines:
    timeframes: [1m, 5m, 15m]
  trades: true
  funding: true

# Processing settings
chunk_size: 100000
max_workers: 4

# Nautilus environment
nautilus_env: /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env

# Logging
log_level: INFO
log_file: ~/.local/share/binance2nautilus/convert.log
```

---

## Return Data Formats

### JSON Output (--json flag)

```json
{
  "status": "success",
  "catalog_path": "/media/sam/2TB-NVMe/nautilus_catalog_v1222",
  "symbols": {
    "BTCUSDT": {
      "klines_1m": {
        "files_processed": 2628,
        "records_written": 2628000,
        "last_timestamp": "2025-12-22T23:59:00Z"
      },
      "trades": {
        "files_processed": 2628,
        "records_written": 45000000,
        "last_timestamp": "2025-12-22T23:59:59.999Z"
      }
    }
  },
  "duration_seconds": 3600,
  "errors": []
}
```

---

## Error Messages

| Error | Cause | Resolution |
|-------|-------|------------|
| `Source directory not found` | Invalid `--source-dir` path | Verify path exists |
| `No CSV files found for {SYMBOL}` | Missing data files | Check source directory structure |
| `Schema version mismatch` | Catalog uses different Nautilus version | Rebuild catalog or use matching version |
| `Insufficient disk space` | Target disk < required space | Free up space or use different disk |
| `Duplicate timestamp detected` | Overlapping data files | Use `--force` to overwrite |
| `BacktestEngine incompatible` | V2 wrangler data in catalog | Rebuild with V1 wranglers |
