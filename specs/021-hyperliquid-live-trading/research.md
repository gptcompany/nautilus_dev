# Research: Hyperliquid Live Trading

**Spec**: 021-hyperliquid-live-trading
**Date**: 2025-12-28
**Status**: Complete

## NautilusTrader Hyperliquid Adapter

### Official Documentation

**Source**: `docs/integrations/hyperliquid.md` (local copy from NautilusTrader docs)

The adapter is implemented in **native Rust** with Python bindings:

| Component | Purpose | Status |
|-----------|---------|--------|
| `HyperliquidHttpClient` | REST API | ✅ Ready |
| `HyperliquidWebSocketClient` | WebSocket streaming | ✅ Ready |
| `HyperliquidInstrumentProvider` | Instrument loading | ✅ Ready |
| `HyperliquidDataClient` | Market data feeds | ✅ Ready |
| `HyperliquidExecutionClient` | Order execution | 🔨 Building |
| `HyperliquidLiveDataClientFactory` | Factory for TradingNode | ✅ Ready |
| `HyperliquidLiveExecClientFactory` | Factory for TradingNode | 🔨 Building |

### GitHub Issues

1. **#3152**: [Hyperliquid] Execution and reconciliation testing
   - Status: Open (enhancement, rust)
   - Focus: Testing execution client reliability

### Discord Knowledge

**From questions.md:1363**:
> "Could someone confirm whether the wildcard arm `_ => {}` in `handler.rs` (line 180) is intentionally left to drop all other `HyperliquidWsMessage` variants?"

**Response (questions.md:1369)**:
> "The Hyperliquid adapter is still in the `building` phase and not yet operational"

**From general.md:822**:
> "Just curious to know how long we've to wait for official full working Hyperliquid Connector?"

**From questions.md:709**:
> "On Hyperliquid there are many things being juggled, more like month units than year units of measurement though"

### Interpretation

- **Data Client**: Fully operational for market data streaming
- **Execution Client**: Under development, basic functionality available
- **Timeline**: Estimated completion within months, not years
- **Recommendation**: Use data client now, test execution on testnet

---

## Hyperliquid Exchange Characteristics

### Fee Structure

| Fee Type | Rate | Notes |
|----------|------|-------|
| Maker | 0.01% | Best in industry |
| Taker | 0.035% | Competitive |
| Funding | Variable | 8-hour intervals |

### Product Support

| Product | Trading | Data | Notes |
|---------|---------|------|-------|
| Perpetual Futures | ✅ | ✅ | Primary focus |
| Spot | ✅ | ✅ | USDC settled |
| Options | ❌ | ❌ | Not available |

### Order Types (from docs)

| Order Type | Perps | Spot | Notes |
|------------|-------|------|-------|
| MARKET | ✅ | ✅ | Executed as IOC limit |
| LIMIT | ✅ | ✅ | GTC, IOC |
| STOP_MARKET | ✅ | ✅ | Native trigger |
| STOP_LIMIT | ✅ | ✅ | Native trigger |
| MARKET_IF_TOUCHED | ✅ | ✅ | Take profit |
| LIMIT_IF_TOUCHED | ✅ | ✅ | Take profit |

### Time in Force

| TIF | Support | Notes |
|-----|---------|-------|
| GTC | ✅ | Good Till Canceled |
| IOC | ✅ | Immediate or Cancel |
| FOK | ❌ | Not supported |
| GTD | ❌ | Not supported |

### Execution Instructions

| Instruction | Support | Notes |
|-------------|---------|-------|
| `post_only` | ✅ | ALO time in force |
| `reduce_only` | ✅ | For stop-loss orders |

---

## Data Pipeline Integration

### Option 1: Native NautilusTrader Recording

Use `DataRecorder` actor with HyperliquidDataClient:

```python
from nautilus_trader.persistence.wranglers import QuoteTickDataWrangler
from nautilus_trader.persistence.catalog import ParquetDataCatalog

# TradingNode with data persistence
config = TradingNodeConfig(
    data_clients={...},
    persistence=PersistenceConfig(
        catalog_path="./catalog/hyperliquid",
        catalog_store="parquet",
    ),
)
```

### Option 2: Existing CCXT Pipeline (Spec 001)

Our `scripts/ccxt_pipeline/fetchers/hyperliquid.py` already exists:

```python
# From specs/001-ccxt-data-pipeline
# Supports: trades, orderbook, funding rates, open interest
```

### Recommendation

Use **Option 1** for live trading (native integration).
Use **Option 2** for historical data backfill.

---

## Security Considerations

### Private Key Management

```bash
# NEVER commit private keys
# Use environment variables only

# Mainnet
export HYPERLIQUID_PK="0x..."
export HYPERLIQUID_VAULT="0x..."  # Optional vault

# Testnet (separate keys!)
export HYPERLIQUID_TESTNET_PK="0x..."
export HYPERLIQUID_TESTNET_VAULT="0x..."
```

### Wallet Setup

1. Create dedicated trading wallet (not main wallet)
2. Fund with minimal USDC for testing
3. Use hardware wallet for mainnet (when supported)

---

## Risk Comparison

| Risk | Hyperliquid (DEX) | Binance (CEX) |
|------|-------------------|---------------|
| Custody | Self (smart contract) | Exchange |
| KYC | None | Required |
| Withdrawal | Instant (on-chain) | Delayed (manual) |
| Hacking | Smart contract exploit | Exchange breach |
| Regulatory | Lower (decentralized) | Higher (centralized) |
| Liquidity | Good (growing) | Best |

---

## Implementation Priority

### Phase 1: Data Feed (Week 1)
- Configure HyperliquidDataClient
- Subscribe to BTC-USD-PERP, ETH-USD-PERP
- Verify data types and latency

### Phase 2: Data Persistence (Week 1-2)
- Integrate with ParquetDataCatalog
- Record trades, quotes, orderbook
- Verify BacktestNode compatibility

### Phase 3: Testnet Trading (Week 2-3)
- Get testnet credentials
- Submit test orders
- Verify fill handling

### Phase 4: RiskManager Integration (Week 3-4)
- Test with Spec 011 RiskManager
- Verify stop-loss on Hyperliquid
- End-to-end validation

### Phase 5: Mainnet Trading (Week 4+)
- Small position testing
- Full strategy deployment
- Monitoring and alerts

---

## References

1. [NautilusTrader Hyperliquid Docs](https://docs.nautilustrader.io/nightly/integrations/hyperliquid)
2. [Hyperliquid Official Docs](https://hyperliquid.gitbook.io/)
3. [GitHub Issue #3152](https://github.com/nautechsystems/nautilus_trader/issues/3152)
4. Local: `docs/integrations/hyperliquid.md`
5. Local: `scripts/ccxt_pipeline/fetchers/hyperliquid.py`
