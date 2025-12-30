# Redis Key Structure (Spec 018)

## Key Pattern

```
trader-{type}:{identifier}
```

| Component | Description | Example |
|-----------|-------------|---------|
| prefix | `trader` (configurable) | `trader` |
| type | Data type | `position`, `order`, `account`, `instrument` |
| identifier | Unique ID | `BTCUSDT-PERP.BINANCE-001` |

## Key Types

### Positions

```
trader-position:{position_id}
```

**Example**:
```
trader-position:BTCUSDT-PERP.BINANCE-001
```

**Fields**: position_id, instrument_id, strategy_id, side, quantity, avg_px_open, ts_opened, ts_last

### Orders

```
trader-order:{client_order_id}
```

**Example**:
```
trader-order:O-20251230-001
```

**Fields**: client_order_id, venue_order_id, instrument_id, order_type, side, quantity, status, events

### Accounts

```
trader-account:{account_id}
```

**Example**:
```
trader-account:BINANCE-USDT_FUTURES-master
```

**Fields**: account_id, account_type, balances, margins

### Instruments

```
trader-instrument:{instrument_id}
```

**Example**:
```
trader-instrument:BTCUSDT-PERP.BINANCE
```

**Fields**: instrument_id, symbol, venue, asset_class, price_precision, size_precision

## Inspection Commands

```bash
# List all keys
redis-cli keys "trader-*"

# Count by type
redis-cli keys "trader-position:*" | wc -l
redis-cli keys "trader-order:*" | wc -l
redis-cli keys "trader-account:*" | wc -l
redis-cli keys "trader-instrument:*" | wc -l

# Get specific position (msgpack encoded)
redis-cli get "trader-position:BTCUSDT-PERP.BINANCE-001"

# Monitor writes in real-time
redis-cli monitor | grep "trader-"
```

## Encoding

| Format | Use Case | Size | Speed |
|--------|----------|------|-------|
| msgpack | Production | 30-50% smaller | Faster |
| json | Debugging | Larger | Slower |

Configure in CacheConfig:
```python
CacheConfig(encoding="msgpack")  # Production
CacheConfig(encoding="json")     # Debug
```
