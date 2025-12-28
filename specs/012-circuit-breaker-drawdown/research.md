# Research: Circuit Breaker (Max Drawdown)

**Created**: 2025-12-28
**Status**: Complete
**Spec**: 012-circuit-breaker-drawdown

## Research Questions

### RQ-001: Portfolio Equity Access

**Question**: How to access portfolio equity and account balance in NautilusTrader?

**Finding**:
- `self.portfolio.account(venue)` returns Account object
- `account.balance_total(currency)` returns total balance
- `account.balances()` returns dict of all currency balances
- Strategies have direct access via `self.portfolio` property

**Code Example**:
```python
from nautilus_trader.trading.strategy import Strategy

class MyStrategy(Strategy):
    def get_equity(self) -> Decimal:
        account = self.portfolio.account(BINANCE)
        return account.balance_total(Currency.from_str("USDT"))
```

**Source**: NautilusTrader nightly v1.222.0 API, Discord discussions

---

### RQ-002: Event Hooks for Monitoring

**Question**: Best event hooks for monitoring equity changes?

**Finding**:
- `on_account_state(event: AccountState)` - triggered on balance changes
- Can also use periodic timer via `self.clock.set_timer()`
- AccountState contains balances, margins, and venue info

**Strategy Event Handlers Available**:
- `on_start` - strategy initialization
- `on_stop` - strategy shutdown
- `on_event` - generic event handler
- `on_account_state` - account balance changes
- `on_position_opened/closed/changed` - position lifecycle

**Recommendation**: Use both `on_account_state` for immediate updates AND periodic timer for safety net.

---

### RQ-003: QuestDB Schema for State Machine

**Question**: Best practices for storing state machine transitions in QuestDB?

**Finding**:
- Use SYMBOL type for state enums (indexed, efficient)
- Use DOUBLE for numeric values (drawdown percentage)
- Partition by DAY for time-series data
- No deduplication needed (each event is unique)

**Existing Pattern** (from monitoring/schemas/):
```sql
CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    timestamp TIMESTAMP,
    trader_id SYMBOL,
    state SYMBOL,           -- ACTIVE, WARNING, REDUCING, HALTED
    current_drawdown DOUBLE,
    peak_equity DOUBLE,
    current_equity DOUBLE
) TIMESTAMP(timestamp) PARTITION BY DAY WAL;
```

**Dedup Not Needed**: State transitions are discrete events, not continuous metrics.

---

### RQ-004: Integration with NautilusTrader Event Loop

**Question**: How to integrate CircuitBreaker with NautilusTrader's event-driven architecture?

**Finding**:
- Preferred pattern is Actor (not Strategy) for cross-cutting concerns
- Actor can subscribe to MessageBus topics
- Actor has same lifecycle as TradingNode

**Actor Pattern**:
```python
from nautilus_trader.common.actor import Actor

class CircuitBreakerActor(Actor):
    def on_start(self):
        # Subscribe to account updates
        self.subscribe_account_updates()
        # Set periodic timer
        self.clock.set_timer("cb_check", timedelta(seconds=60))
```

**Discovery**: Strategies can access actors via `self.cache` if registered properly.

---

### RQ-005: Existing Risk Management in Codebase

**Question**: What risk management infrastructure already exists?

**Finding**: Spec 011 (Stop-Loss & Position Limits) provides:
- `RiskManager` class for per-position protection
- `RiskConfig` model for configuration
- Integration pattern for strategies

**Integration Point**:
- CircuitBreaker provides global (portfolio-level) protection
- RiskManager provides local (position-level) protection
- They complement each other

**Files**:
- `/specs/011-stop-loss-position-limits/contracts/risk_manager_api.py`
- `/strategies/examples/risk_managed_strategy.py`

---

### RQ-006: Discord Community Insights

**Question**: Any community discussions on circuit breakers or drawdown protection?

**Finding**:
- Limited discussion on circuit breakers specifically
- General interest in visualization of equity curves and drawdowns (Plotly mentioned)
- Risk limits mentioned in context of middle-office features
- No existing circuit breaker implementations shared

**Quote** (discord/questions.md:684):
> "How far into the middle office does Nautilus go - or plan to go in the future? For example... tools to set risk limits?"

**Implication**: This is a gap that Spec 012 addresses.

---

## Decisions Made

### Decision: Use balance_total (not unrealized PnL)

**Rationale**:
- Simpler calculation
- More stable (not affected by short-term price fluctuations)
- Unrealized PnL handled at position level by RiskManager

### Decision: Standalone Actor (not Strategy mixin)

**Rationale**:
- Single source of truth for global state
- Decoupled from individual strategies
- Cleaner separation of concerns

### Decision: MVP without auto-close

**Rationale**:
- Auto-close in volatile markets can lock in losses
- Block-only approach allows trader discretion
- Can add auto-close as configurable option later

---

## Unresolved Questions

None - all clarifications resolved.

---

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| State Machine | Python enum | Simple, type-safe, native |
| Configuration | Pydantic BaseModel | Validation, immutability, serialization |
| Persistence (MVP) | In-memory dict | Fast, sufficient for backtest |
| Monitoring | QuestDB + Grafana | Already integrated (Spec 005) |
| Integration | Actor pattern | NautilusTrader native, event-driven |

---

## References

- NautilusTrader Nightly v1.222.0 API
- Discord Community (last 90 days)
- Spec 005: Grafana/QuestDB Monitoring
- Spec 011: Stop-Loss & Position Limits
- `monitoring/schemas/*.sql` - existing QuestDB patterns
