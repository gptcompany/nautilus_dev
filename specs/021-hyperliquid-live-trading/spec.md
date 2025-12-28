# Spec 021: Hyperliquid Live Trading Integration

## Overview

Integrate NautilusTrader's native Rust Hyperliquid adapter for live trading and historical data persistence. Hyperliquid is a DEX with low fees - our **primary target exchange** for live trading.

## Problem Statement

Current live trading specs focus on Binance (Spec 015). Hyperliquid offers:
- **Decentralized**: No KYC, self-custody
- **Low fees**: 0.01% maker / 0.035% taker
- **On-chain orderbook**: Full transparency
- **Native NautilusTrader support**: Rust adapter available

## Goals

1. **Live Trading**: Configure HyperliquidExecClient for perpetual futures
2. **Data Feed**: Stream real-time market data via HyperliquidDataClient
3. **Historical Data**: Persist data to ParquetDataCatalog for backtesting
4. **Risk Integration**: Integrate with Spec 011 (Stop-Loss & Position Limits)

## Adapter Status

> **Source**: [NautilusTrader Hyperliquid Docs](https://docs.nautilustrader.io/nightly/integrations/hyperliquid)
> **GitHub Issue**: [#3152 - Execution and reconciliation testing](https://github.com/nautechsystems/nautilus_trader/issues/3152)

| Component | Status | Notes |
|-----------|--------|-------|
| `HyperliquidHttpClient` | ✅ Ready | REST API connectivity |
| `HyperliquidWebSocketClient` | ✅ Ready | WebSocket streaming |
| `HyperliquidInstrumentProvider` | ✅ Ready | Instrument loading |
| `HyperliquidDataClient` | ✅ Ready | Market data feeds |
| `HyperliquidExecutionClient` | 🔨 Building | Order execution (testing in progress) |

## User Stories

### US1: Live Data Feed (P1 - MVP)
**As a** trader,
**I want** to stream real-time Hyperliquid market data,
**So that** my strategies can react to live market conditions.

**Acceptance Criteria**:
- [ ] Subscribe to BTC-USD-PERP, ETH-USD-PERP quotes and trades
- [ ] Receive orderbook depth updates via WebSocket
- [ ] Data formatted as NautilusTrader native types (QuoteTick, TradeTick, OrderBookDelta)

### US2: Historical Data Persistence (P1 - MVP)
**As a** quant developer,
**I want** to persist Hyperliquid data to ParquetDataCatalog,
**So that** I can backtest strategies with real exchange data.

**Acceptance Criteria**:
- [ ] Record trades, quotes, orderbook to Parquet files
- [ ] Catalog compatible with BacktestNode
- [ ] Incremental updates (append, not overwrite)

### US3: Live Order Execution (P2)
**As a** trader,
**I want** to execute orders on Hyperliquid,
**So that** I can deploy my backtested strategies live.

**Acceptance Criteria**:
- [ ] Submit MARKET, LIMIT orders
- [ ] Submit STOP_MARKET, STOP_LIMIT for risk management
- [ ] Receive fill confirmations via WebSocket
- [ ] `reduce_only=True` supported for stop-loss orders

### US4: Risk Manager Integration (P2)
**As a** risk-conscious trader,
**I want** RiskManager (Spec 011) to work with Hyperliquid,
**So that** positions are protected with automatic stop-losses.

**Acceptance Criteria**:
- [ ] Stop-loss orders placed on PositionOpened
- [ ] Position limits enforced before order submission
- [ ] Works in both backtest and live modes

### US5: Testnet Validation (P3)
**As a** developer,
**I want** to test full order lifecycle on Hyperliquid testnet,
**So that** I can validate before risking real funds.

**Acceptance Criteria**:
- [ ] Connect to testnet with `testnet=True`
- [ ] Execute full trade cycle (open → stop-loss → close)
- [ ] Verify reconciliation on restart

## Requirements

### Functional Requirements

#### FR-001: Data Client Configuration
```python
from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.adapters.hyperliquid import HyperliquidDataClientConfig
from nautilus_trader.config import InstrumentProviderConfig

data_config = {
    HYPERLIQUID: HyperliquidDataClientConfig(
        instrument_provider=InstrumentProviderConfig(
            load_all=False,
            load_ids=[
                InstrumentId.from_str("BTC-USD-PERP.HYPERLIQUID"),
                InstrumentId.from_str("ETH-USD-PERP.HYPERLIQUID"),
            ],
        ),
        testnet=False,  # Production
    ),
}
```

#### FR-002: Execution Client Configuration
```python
from nautilus_trader.adapters.hyperliquid import HyperliquidExecClientConfig

exec_config = {
    HYPERLIQUID: HyperliquidExecClientConfig(
        private_key=None,  # Loads from HYPERLIQUID_PK env var
        vault_address=None,  # Optional vault trading
        instrument_provider=InstrumentProviderConfig(load_all=True),
        testnet=False,
        max_retries=3,
        retry_delay_initial_ms=100,
        retry_delay_max_ms=5000,
    ),
}
```

#### FR-003: Supported Order Types
| Order Type | Support | Notes |
|------------|---------|-------|
| MARKET | ✅ | Executed as IOC limit |
| LIMIT | ✅ | GTC, IOC supported |
| STOP_MARKET | ✅ | Native trigger orders |
| STOP_LIMIT | ✅ | Native trigger orders |
| MARKET_IF_TOUCHED | ✅ | Take profit at market |
| LIMIT_IF_TOUCHED | ✅ | Take profit with limit |

#### FR-004: Symbology
```python
# Perpetual Futures
InstrumentId.from_str("BTC-USD-PERP.HYPERLIQUID")
InstrumentId.from_str("ETH-USD-PERP.HYPERLIQUID")
InstrumentId.from_str("SOL-USD-PERP.HYPERLIQUID")

# Spot Markets
InstrumentId.from_str("PURR-USDC-SPOT.HYPERLIQUID")
InstrumentId.from_str("HYPE-USDC-SPOT.HYPERLIQUID")
```

#### FR-005: Data Persistence Pipeline
```python
# Use DataRecorder for live-to-catalog persistence
from nautilus_trader.persistence.wranglers import TradeTickDataWrangler
from nautilus_trader.persistence.catalog import ParquetDataCatalog

catalog = ParquetDataCatalog("./catalog/hyperliquid")
# Strategy subscribes, data auto-persisted
```

### Non-Functional Requirements

#### NFR-001: Latency
- Order submission < 200ms (network dependent, on-chain confirmation)
- Fill notification < 100ms after on-chain settlement
- Data feed latency < 50ms

#### NFR-002: Reliability
- Auto-reconnect on WebSocket disconnect
- Order state consistency after reconnect
- Graceful handling of chain congestion

#### NFR-003: Security
- Private keys NEVER in code or config files
- Use environment variables only
- Testnet credentials separate from mainnet

## Technical Design

### TradingNode Configuration

```python
from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.adapters.hyperliquid import HyperliquidDataClientConfig
from nautilus_trader.adapters.hyperliquid import HyperliquidExecClientConfig

config = TradingNodeConfig(
    trader_id="TRADER-HL-001",
    data_clients={
        HYPERLIQUID: HyperliquidDataClientConfig(
            instrument_provider=InstrumentProviderConfig(load_all=True),
            testnet=False,
        ),
    },
    exec_clients={
        HYPERLIQUID: HyperliquidExecClientConfig(
            private_key=None,  # From HYPERLIQUID_PK env
            instrument_provider=InstrumentProviderConfig(load_all=True),
            testnet=False,
            max_retries=3,
        ),
    },
)
```

### Strategy Integration

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_dev.risk import RiskConfig, RiskManager

class HyperliquidStrategy(Strategy):
    def __init__(self, config: HyperliquidStrategyConfig):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str("BTC-USD-PERP.HYPERLIQUID")

        # Integrate with Spec 011 RiskManager
        self.risk_manager = RiskManager(
            config=config.risk,
            strategy=self,
        )

    def on_start(self) -> None:
        self.subscribe_quote_ticks(self.instrument_id)
        self.subscribe_trade_ticks(self.instrument_id)
        self.subscribe_order_book_deltas(self.instrument_id)

    def on_event(self, event: Event) -> None:
        self.risk_manager.handle_event(event)
```

### Environment Variables

```bash
# Mainnet
export HYPERLIQUID_PK="your_private_key_here"
export HYPERLIQUID_VAULT="vault_address_here"  # Optional

# Testnet
export HYPERLIQUID_TESTNET_PK="your_testnet_private_key"
export HYPERLIQUID_TESTNET_VAULT="testnet_vault_address"  # Optional
```

## Known Issues (Discord)

### Adapter Status
> "Hyperliquid adapter is still in the `building` phase and not yet operational"
> — Discord questions.md:1369

**Mitigation**: Track GitHub issue #3152, use latest nightly wheels.

### WebSocket Handler
> "wildcard arm `_ => {}` in handler.rs drops some message variants"
> — Discord questions.md:1363

**Mitigation**: Fixed in recent commits, use nightly >= 2025-12-20.

## Dependencies

### External Dependencies
- NautilusTrader nightly >= 1.222.0 (for Hyperliquid adapter)
- Hyperliquid account with USDC deposit
- EVM wallet (MetaMask or similar)

### Internal Dependencies
- Spec 011 (Stop-Loss & Position Limits) - for RiskManager integration
- Spec 001 (Data Pipeline) - for catalog structure reference
- Spec 014 (TradingNode Configuration) - for TradingNode patterns

## Testing Strategy

### Phase 1: Data Feed Validation
- [ ] Connect to Hyperliquid mainnet data
- [ ] Subscribe to BTC-USD-PERP quotes/trades
- [ ] Verify data types match NautilusTrader schema

### Phase 2: Testnet Trading
- [ ] Configure testnet credentials
- [ ] Submit test MARKET order
- [ ] Submit test LIMIT order
- [ ] Submit test STOP_MARKET order
- [ ] Verify fill events received

### Phase 3: Risk Manager Integration
- [ ] Open position on testnet
- [ ] Verify stop-loss auto-created
- [ ] Close position manually
- [ ] Verify stop-loss auto-cancelled

### Phase 4: Data Persistence
- [ ] Record live data for 1 hour
- [ ] Verify Parquet files created
- [ ] Load catalog in BacktestNode
- [ ] Run backtest with recorded data

## Success Metrics

- Live data feed operational with < 50ms latency
- Order execution success rate > 99%
- Stop-loss orders placed within 100ms of position open
- Historical data persisted for backtesting

## File Structure

```
nautilus_dev/
├── configs/
│   └── hyperliquid/
│       ├── trading_node.py      # TradingNode config
│       ├── data_client.py       # Data-only config
│       └── testnet.py           # Testnet config
├── strategies/
│   └── hyperliquid/
│       ├── __init__.py
│       ├── config.py            # Strategy config
│       └── base_strategy.py     # Base with RiskManager
├── scripts/
│   └── hyperliquid/
│       ├── record_data.py       # Data recording script
│       └── run_live.py          # Live trading launcher
└── tests/
    └── hyperliquid/
        ├── test_data_client.py
        ├── test_exec_client.py
        └── integration/
            └── test_live_cycle.py
```

## Comparison: Hyperliquid vs Binance

| Aspect | Hyperliquid | Binance |
|--------|-------------|---------|
| Type | DEX (on-chain) | CEX |
| KYC | No | Yes |
| Custody | Self | Exchange |
| Fees | 0.01%/0.035% | 0.02%/0.04% |
| Latency | ~200ms (on-chain) | ~50ms |
| Adapter | Rust (building) | Rust (stable) |
| Stop Orders | Native | Algo Order API |
| Risk | Smart contract | Exchange |

## Priority Justification

Hyperliquid is our **primary target** because:
1. **DEX**: True ownership of funds
2. **Low fees**: Better for HFT/scalping
3. **No KYC**: Faster onboarding
4. **Native adapter**: NautilusTrader Rust implementation
5. **Growing liquidity**: Major DEX by volume
