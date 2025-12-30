# Order Reconciliation Guide

This guide explains how to configure and use NautilusTrader's order reconciliation system for production trading.

## Overview

Order reconciliation ensures your TradingNode's internal state matches the exchange state after restarts or disconnections. NautilusTrader provides three reconciliation mechanisms:

1. **Startup Reconciliation** - Syncs state on TradingNode start
2. **Continuous Polling** - Periodic checks during operation
3. **In-Flight Monitoring** - Tracks pending order confirmations

## Quick Start

### Minimal Configuration

```python
from nautilus_trader.config import (
    TradingNodeConfig,
    LiveExecEngineConfig,
    CacheConfig,
    DatabaseConfig,
)

config = TradingNodeConfig(
    trader_id="TRADER-001",
    exec_engine=LiveExecEngineConfig(
        reconciliation=True,
        reconciliation_startup_delay_secs=10.0,
    ),
    cache=CacheConfig(
        database=DatabaseConfig(host="localhost", port=6379),
        persist_account_events=True,  # CRITICAL for recovery
    ),
)
```

### Using Presets

```python
from config.reconciliation import ReconciliationPreset
from config.trading_node import LiveTradingNodeConfig

# Standard production settings
config = LiveTradingNodeConfig(
    trader_id="TRADER-001",
    reconciliation=ReconciliationPreset.STANDARD,
)

# Or conservative for initial setup
config = LiveTradingNodeConfig(
    trader_id="TRADER-001",
    reconciliation=ReconciliationPreset.CONSERVATIVE,
)
```

## Presets

| Preset | Use Case | Startup Delay | Lookback |
|--------|----------|---------------|----------|
| `STANDARD` | Production | 10s | Unlimited |
| `CONSERVATIVE` | Initial setup, unstable networks | 15s | 120 min |
| `AGGRESSIVE` | Low-latency trading | 10s | 30 min |
| `DISABLED` | Testing only | - | - |

## Configuration Options

### Startup Reconciliation

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enabled` | `True` | Enable reconciliation |
| `startup_delay_secs` | `10.0` | Wait for accounts to connect (min 10s) |
| `lookback_mins` | `None` | History lookback (None = max available) |

### In-Flight Monitoring

| Parameter | Default | Description |
|-----------|---------|-------------|
| `inflight_check_interval_ms` | `2000` | Check interval for pending orders |
| `inflight_check_threshold_ms` | `5000` | Threshold before querying venue |
| `inflight_check_retries` | `5` | Max retry attempts |

### Continuous Polling

| Parameter | Default | Description |
|-----------|---------|-------------|
| `open_check_interval_secs` | `5.0` | Polling interval (None = disabled) |
| `open_check_lookback_mins` | `60` | Open order lookback (min 60 min) |
| `open_check_threshold_ms` | `5000` | Discrepancy threshold |

### Memory Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| `purge_closed_orders_interval_mins` | `10` | Purge frequency |
| `purge_closed_orders_buffer_mins` | `60` | Grace period before purge |

## External Order Claims

To claim orders placed outside NautilusTrader (via exchange web/app):

```python
from config.reconciliation import ExternalOrderClaimConfig

# Claim specific instruments
claims = ExternalOrderClaimConfig(
    instrument_ids=[
        "BTCUSDT-PERP.BINANCE",
        "ETHUSDT-PERP.BINANCE",
    ],
)

# Or claim all instruments
claims = ExternalOrderClaimConfig(claim_all=True)
```

## Redis Requirement

Redis is **required** for production reconciliation. It stores account events for recovery:

```bash
# Check Redis status
redis-cli ping  # Should return PONG

# Start Redis if needed
sudo systemctl start redis
```

## Known Issues

### Binance HEDGING Mode (Bug #3104)
- Issue: Reconciliation fails in hedge mode
- **Workaround**: Use NETTING mode only

### Bybit Hedge Mode
- Issue: Not supported
- **Workaround**: Use NETTING mode only

### External Positions
- Issue: Positions opened via web/app may not reconcile
- **Workaround**: Use `external_order_claims` configuration

## Monitoring

Check logs for reconciliation status:

```
INFO  Reconciliation starting...
INFO  Querying venue for open orders
INFO  Querying venue for recent fills
INFO  Querying venue for positions
INFO  Reconciliation complete - 0 discrepancies found
```

## Troubleshooting

### Reconciliation takes too long
- Reduce `lookback_mins` (but never below actual position age)
- Use `AGGRESSIVE` preset for faster startup

### Position discrepancies
- Verify Redis is running and `persist_account_events=True`
- Check that `startup_delay_secs >= 10.0`
- Ensure you're using NETTING mode (not HEDGING)

### External orders not detected
- Verify `external_order_claims` includes the instrument IDs
- Check that reconciliation is enabled
