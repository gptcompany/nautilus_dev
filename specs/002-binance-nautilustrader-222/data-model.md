# Data Model: Binance to NautilusTrader v1.222.0 Data Ingestion

## Entity Relationship Diagram

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   BinanceKlineCSV   │     │   BinanceTradeCSV   │     │BinanceFundingRateCSV│
│  (Source Format)    │     │   (Source Format)   │     │   (Source Format)   │
└──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘
           │                           │                           │
           ▼                           ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   BarDataWrangler   │     │TradeTickDataWrangler│     │  FundingConverter   │
│      (V1 Only)      │     │      (V1 Only)      │     │   (Custom Logic)    │
└──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘
           │                           │                           │
           ▼                           ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│        Bar          │     │      TradeTick      │     │    FundingRate      │
│  (Nautilus Type)    │     │   (Nautilus Type)   │     │   (Custom Data)     │
└──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘
           │                           │                           │
           └───────────────────────────┼───────────────────────────┘
                                       ▼
                              ┌─────────────────────┐
                              │ ParquetDataCatalog  │
                              │   (v1.222.0 Schema) │
                              └─────────────────────┘
```

---

## Source Entities (Binance CSV)

### BinanceKlineCSV

**Description**: Raw OHLCV candlestick data from Binance historical data API.

| Field | Type | Description |
|-------|------|-------------|
| `open_time` | int64 (ms) | Candle open timestamp in milliseconds |
| `open` | float | Opening price |
| `high` | float | Highest price |
| `low` | float | Lowest price |
| `close` | float | Closing price |
| `volume` | float | Base asset volume |
| `close_time` | int64 (ms) | Candle close timestamp in milliseconds |
| `quote_volume` | float | Quote asset volume |
| `count` | int | Number of trades |
| `taker_buy_volume` | float | Taker buy base asset volume |
| `taker_buy_quote_volume` | float | Taker buy quote asset volume |
| `ignore` | int | Unused field |

**Source Path**: `/media/sam/3TB-WDC/binance-history-data-downloader/data/{SYMBOL}/klines/{TIMEFRAME}/`

**File Naming**: `{SYMBOL}-{TIMEFRAME}-{YYYY-MM-DD}.csv`

---

### BinanceTradeCSV

**Description**: Raw individual trade execution data from Binance.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int64 | Unique trade ID |
| `price` | float | Trade execution price |
| `qty` | float | Trade quantity (base asset) |
| `quote_qty` | float | Trade value (quote asset) |
| `time` | int64 (ms) | Trade timestamp in milliseconds |
| `is_buyer_maker` | bool | True if buyer was market maker |

**Source Path**: `/media/sam/3TB-WDC/binance-history-data-downloader/data/{SYMBOL}/trades/`

**File Naming**: `{SYMBOL}-trades-{YYYY-MM-DD}.csv`

---

### BinanceFundingRateCSV

**Description**: Funding rate history for perpetual futures contracts.

| Field | Type | Description |
|-------|------|-------------|
| `calcTime` | int64 (ms) | Funding calculation timestamp |
| `fundingIntervalHours` | int | Funding interval (typically 8) |
| `lastFundingRate` | float | Funding rate as decimal |

**Source Path**: `/media/sam/3TB-WDC/binance-history-data-downloader/data/{SYMBOL}/fundingRate/`

**File Naming**: `{SYMBOL}-fundingRate-{YYYY-MM}.csv`

---

## Target Entities (NautilusTrader v1.222.0)

### CryptoPerpetual

**Description**: Instrument definition for perpetual futures contract.

| Field | Type | Description |
|-------|------|-------------|
| `instrument_id` | InstrumentId | e.g., `BTCUSDT-PERP.BINANCE` |
| `raw_symbol` | Symbol | e.g., `BTCUSDT` |
| `base_currency` | Currency | e.g., `BTC` |
| `quote_currency` | Currency | e.g., `USDT` |
| `settlement_currency` | Currency | e.g., `USDT` |
| `is_inverse` | bool | `False` for linear contracts |
| `price_precision` | int | Decimal places for price (2 for BTCUSDT) |
| `size_precision` | int | Decimal places for size (3 for BTCUSDT) |
| `price_increment` | Price | Minimum price tick (0.01) |
| `size_increment` | Quantity | Minimum size tick (0.001) |
| `margin_init` | Decimal | Initial margin requirement |
| `margin_maint` | Decimal | Maintenance margin requirement |
| `maker_fee` | Decimal | Maker fee rate |
| `taker_fee` | Decimal | Taker fee rate |
| `ts_event` | int64 (ns) | Event timestamp |
| `ts_init` | int64 (ns) | Initialization timestamp |

---

### Bar

**Description**: OHLCV candlestick in NautilusTrader format.

| Field | Type | Schema (Parquet) | Description |
|-------|------|------------------|-------------|
| `bar_type` | BarType | metadata | e.g., `BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL` |
| `open` | Price | fixed_size_binary[16] | Opening price |
| `high` | Price | fixed_size_binary[16] | Highest price |
| `low` | Price | fixed_size_binary[16] | Lowest price |
| `close` | Price | fixed_size_binary[16] | Closing price |
| `volume` | Quantity | fixed_size_binary[16] | Volume |
| `ts_event` | int64 (ns) | uint64 | Event timestamp (candle open) |
| `ts_init` | int64 (ns) | uint64 | Init timestamp (candle close) |

**Catalog Path**: `data/bar/{BAR_TYPE}/`

---

### TradeTick

**Description**: Individual trade execution in NautilusTrader format.

| Field | Type | Schema (Parquet) | Description |
|-------|------|------------------|-------------|
| `instrument_id` | InstrumentId | metadata | e.g., `BTCUSDT-PERP.BINANCE` |
| `price` | Price | fixed_size_binary[16] | Trade price |
| `size` | Quantity | fixed_size_binary[16] | Trade size |
| `aggressor_side` | AggressorSide | uint8 | `BUYER` (1) or `SELLER` (2) |
| `trade_id` | str | string | Unique trade identifier |
| `ts_event` | int64 (ns) | uint64 | Trade timestamp |
| `ts_init` | int64 (ns) | uint64 | Init timestamp |

**Catalog Path**: `data/trade_tick/{INSTRUMENT_ID}/`

---

### FundingRate (Custom Data)

**Description**: Periodic funding rate for perpetual futures in NautilusTrader-compatible format.

| Field | Type | Schema (Parquet) | Description |
|-------|------|------------------|-------------|
| `instrument_id` | InstrumentId | metadata | e.g., `BTCUSDT-PERP.BINANCE` |
| `funding_rate` | Decimal | fixed_size_binary[16] | Funding rate as decimal (e.g., 0.0001 = 0.01%) |
| `funding_interval_hours` | int | uint8 | Interval between funding (typically 8) |
| `ts_event` | int64 (ns) | uint64 | Funding calculation timestamp |
| `ts_init` | int64 (ns) | uint64 | Record initialization timestamp |

**Catalog Path**: `data/custom/funding_rate/{INSTRUMENT_ID}/`

**Implementation Notes**:
- Stored as custom data type (not native NautilusTrader type)
- Queryable by timestamp range via ParquetDataCatalog
- Used for accurate perpetual futures PnL calculation
- Funding rate is typically between -0.01 and +0.01 (±1%)

**Transformation from BinanceFundingRateCSV**:
```python
# Binance CSV → FundingRate
funding_rate = Decimal(str(row['lastFundingRate']))
ts_event = int(row['calcTime']) * 1_000_000  # ms → ns
funding_interval_hours = int(row['fundingIntervalHours'])
```

---

## Transformation Entities

### ConversionState

**Description**: Tracks conversion progress for incremental updates.

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | str | Trading symbol (e.g., `BTCUSDT`) |
| `data_type` | str | Data type (`klines_1m`, `trades`, `funding`) |
| `last_file` | str | Last processed filename |
| `last_timestamp` | int64 (ns) | Last processed timestamp |
| `record_count` | int | Total records processed |
| `updated_at` | datetime | Last update time |

**Storage**: JSON file at `{CATALOG_PATH}/conversion_state.json`

---

## Validation Rules

### Timestamp Validation
- `ts_event` must be before `ts_init` for bars
- All timestamps must be positive (> 0)
- No future timestamps (< current time + 1 day buffer)

### Price Validation
- All prices must be positive (> 0)
- `high >= open, close, low`
- `low <= open, close, high`

### Volume Validation
- Volume must be non-negative (>= 0)
- Zero volume bars are allowed (no trading in period)

### Trade Validation
- `trade_id` must be unique within the same instrument
- `size` must be positive (> 0)
- `aggressor_side` must be `BUYER` or `SELLER`

---

## State Transitions

### Conversion Pipeline States

```
[IDLE] ─── scan_new_files() ───▶ [SCANNING]
                                     │
                                     ▼
                              [CONVERTING]
                                     │
                        ┌────────────┼────────────┐
                        ▼            ▼            ▼
                  [SUCCESS]    [PARTIAL]     [FAILED]
                        │            │            │
                        │            │            ▼
                        │            │     [RETRY] ──▶ [CONVERTING]
                        │            │
                        └────────────┴───▶ [IDLE]
```

### File Processing States

| State | Description |
|-------|-------------|
| `PENDING` | File detected, not yet processed |
| `PROCESSING` | Currently being converted |
| `COMPLETED` | Successfully converted and written |
| `SKIPPED` | Duplicate or already exists in catalog |
| `FAILED` | Conversion error, needs retry |
