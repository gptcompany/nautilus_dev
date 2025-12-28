# Research: Binance Exec Client (Spec 015)

**Research Date**: 2025-12-28
**Version Context**: NautilusTrader Nightly (v1.222.0+)
**Sources**: Context7, Discord (90-day window), GitHub Issues

---

## Technical Context Clarifications

### TC-001: BinanceExecClientConfig Parameters

**Decision**: Use documented defaults with production overrides

**Rationale**: Official API docs confirm parameter availability. Discord confirms best practices.

**Key Parameters**:
| Parameter | Recommended | Notes |
|-----------|-------------|-------|
| `account_type` | USDT_FUTURES | For perpetual futures trading |
| `use_position_ids` | True | Required for HEDGE mode |
| `max_retries` | 3 | Prevent account bans from excessive retries |
| `recv_window_ms` | 5000 | Default, works well |

### TC-002: Order Types Support

**Decision**: Focus on MARKET, LIMIT, STOP_MARKET, STOP_LIMIT

**Rationale**: Algo Order API fix merged (commit `62ef6f63a02`, 2025-12-10)

**Supported Order Types**:
- MARKET - Immediate execution
- LIMIT - Post-only supported
- STOP_MARKET - Requires Algo Order API (fixed in nightly)
- STOP_LIMIT - Requires Algo Order API (fixed in nightly)
- TAKE_PROFIT_MARKET - Via conditional orders
- TRAILING_STOP_MARKET - Exchange-side only

### TC-003: Position Mode

**Decision**: ONE-WAY mode (NETTING) as default

**Rationale**: HEDGE mode has known reconciliation bug (#3104 - still OPEN)

**Alternatives Considered**:
- HEDGE mode: Has bug with LiveExecEngine reconciliation
- ONE-WAY mode: Works correctly, recommended

### TC-004: Known Issues Resolution

| Issue | Status | Resolution |
|-------|--------|------------|
| ADL handling | FIXED | commit `32896d30bca` (2025-11-22) |
| Chinese characters | FIXED | nightly after 2025-10-26 |
| STOP_MARKET Algo API | FIXED | commit `62ef6f63a02` (2025-12-10) |
| HEDGE mode reconciliation | OPEN | Use NETTING mode |

### TC-005: External Order Claims

**Decision**: Implement external_order_claims for position recovery

**Pattern**:
```python
strategy_config = StrategyConfig(
    external_order_claims=[
        InstrumentId.from_str("BTCUSDT-PERP.BINANCE"),
    ],
)
```

**Why Required**: Discord confirms this trips people up when restarting without backing cache.

---

## Dependency Analysis

### Spec 014 (TradingNode Configuration)

**Status**: COMPLETED (commit `cb7a18b`)

**Integration Points**:
- Uses TradingNodeConfigFactory from Spec 014
- exec_clients dict maps to factory output
- CacheConfig and LiveExecEngineConfig already defined

### NautilusTrader Version

**Required**: Nightly >= 2025-12-10

**Why**: STOP_MARKET Algo Order API fix

---

## Best Practices (Discord Community)

### Production Configuration

1. **Cache Persistence**: Always use Redis for recovery
2. **Reconciliation Delay**: Minimum 10s (`reconciliation_startup_delay_secs=10.0`)
3. **OMS Type**: Set explicitly (NETTING recommended)
4. **External Claims**: Configure for restart scenarios
5. **Leverage**: Set via `futures_leverages` dict, not API calls

### Error Handling

1. **Rate Limits**: Exponential backoff, max 3 retries
2. **Network Errors**: Auto-reconnect WebSocket
3. **Insufficient Balance**: Log and skip, don't crash
4. **Invalid Symbol**: Fail fast with clear error

---

## Open Issues to Monitor

| Issue | Impact | Workaround |
|-------|--------|------------|
| #3104 | HEDGE mode reconciliation fails | Use NETTING |
| #3042 | Routing client reconciliation | Match venue to client |
| #3006 | Binance.US fill events | Use standard Binance |

---

## Implementation Recommendations

### Phase 1: Client Factory

```python
def create_binance_exec_client(
    account_type: BinanceAccountType = BinanceAccountType.USDT_FUTURES,
    testnet: bool = False,
    max_retries: int = 3,
) -> dict[str, BinanceExecClientConfig]:
    """Factory for Binance execution client."""
    return {
        "BINANCE": BinanceExecClientConfig(
            account_type=account_type,
            testnet=testnet,
            max_retries=max_retries,
            use_position_ids=True,
            warn_rate_limits=True,
        ),
    }
```

### Phase 2: Order Submission

```python
def submit_market_order(self, side: OrderSide, quantity: Quantity) -> None:
    """Submit market order with validation."""
    order = self.order_factory.market(
        instrument_id=self.instrument_id,
        order_side=side,
        quantity=quantity,
        time_in_force=TimeInForce.GTC,
    )
    self.submit_order(order)
```

### Phase 3: Error Handling

- Wrap order submission in try/except
- Log rate limit warnings
- Implement graceful degradation for transient errors

---

## Sources

- NautilusTrader API docs (Context7)
- `/media/sam/1TB/nautilus_dev/docs/discord/binance.md`
- `/media/sam/1TB/nautilus_dev/docs/discord/questions.md`
- `/media/sam/1TB/nautilus_dev/docs/discord/help.md`
- GitHub Issues: #3104, #3042, #3006, #3053, #3287
