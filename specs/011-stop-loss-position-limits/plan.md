# Implementation Plan: Stop-Loss & Position Limits

**Feature Branch**: `011-stop-loss-position-limits`
**Created**: 2025-12-28
**Status**: Draft
**Spec Reference**: `specs/011-stop-loss-position-limits/spec.md`
**Research Reference**: `specs/011-stop-loss-position-limits/research.md`

## Architecture Overview

This feature implements core risk management controls for NautilusTrader strategies:
1. **Automatic Stop-Loss**: Every position entry generates a corresponding protective stop order
2. **Position Limits**: Enforce maximum position size per instrument and total exposure
3. **Integration**: Seamless integration with BacktestNode and TradingNode

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                      NautilusTrader Engine                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Strategy   │────▶│ RiskManager  │────▶│  RiskEngine  │    │
│  │ (on_event)   │     │  (new)       │     │  (existing)  │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│         │                    │                    │             │
│         ▼                    ▼                    ▼             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │ OrderFactory │     │ Stop Orders  │     │   Denied     │    │
│  │              │     │ (SL/TP)      │     │   Orders     │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                       Event Bus                           │  │
│  │  PositionOpened │ PositionClosed │ PositionChanged       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
specs/011-stop-loss-position-limits/
├── spec.md                    # Requirements
├── plan.md                    # This file
├── research.md                # Academic background + API research
├── data-model.md              # Entity definitions (TODO)
└── contracts/                 # API contracts (TODO)

nautilus_dev/
├── risk/
│   ├── __init__.py
│   ├── config.py              # RiskConfig Pydantic model
│   ├── manager.py             # RiskManager class
│   └── ou_estimator.py        # OU parameter estimation (optional)
└── tests/
    ├── test_risk_config.py
    ├── test_risk_manager.py
    └── integration/
        └── test_risk_backtest.py
```

## Technical Decisions

### Decision 1: Stop-Loss Approach

**Options Considered**:
1. **Option A: Static Stop-Loss** (percentage-based)
   - Pros: Simple, predictable, easy to configure
   - Cons: Theoretically suboptimal

2. **Option B: Dynamic Stop-Loss** (OU-based optimal boundaries)
   - Pros: Theoretically optimal per Kitapbayev & Leung (2025)
   - Cons: Complex, requires parameter estimation

3. **Option C: Hybrid Approach**
   - Static default with optional dynamic mode
   - Pros: Best of both worlds
   - Cons: More code paths

**Selected**: Option C - Hybrid Approach

**Rationale**: Static covers 95% of use cases. Dynamic available for mean-reversion strategies. Configuration-driven to choose mode.

---

### Decision 2: Stop Order Type

**Options Considered**:
1. **Option A: STOP_MARKET** (native)
   - Pros: Guaranteed fill, exchange-managed
   - Cons: May slip in gaps, requires venue support

2. **Option B: STOP_LIMIT** (native)
   - Pros: Price control
   - Cons: May not fill

3. **Option C: Emulated** (strategy-managed)
   - Pros: Works everywhere
   - Cons: Latency-dependent

**Selected**: Option A as default, Option C as fallback

**Rationale**:
- Use native STOP_MARKET with `reduce_only=True`
- Binance/Bybit now support via Algo Order API (nightly 2025-12-10+)
- Emulated mode for venues without native support

---

### Decision 3: Position Limits Implementation

**Options Considered**:
1. **Option A: RiskEngine only**
   - Use existing `max_notional_per_order`
   - Pros: Built-in
   - Cons: Limited granularity

2. **Option B: Strategy-level only**
   - Custom validation before order submission
   - Pros: Full control
   - Cons: Must implement ourselves

3. **Option C: Defense in Depth**
   - RiskEngine for global, Strategy for per-instrument
   - Pros: Multiple safety layers
   - Cons: More configuration

**Selected**: Option C - Defense in Depth

**Rationale**: RiskEngine catches balance violations. Strategy-level adds instrument-specific limits. Aligns with trading best practices.

---

### Decision 4: Integration Pattern

**Options Considered**:
1. **Option A: Mixin class**
   - `RiskMixin` that strategies inherit
   - Pros: Clean inheritance
   - Cons: Python MRO complexity

2. **Option B: Composition**
   - `RiskManager` instance inside strategy
   - Pros: Explicit, testable, no inheritance issues
   - Cons: Manual wiring

3. **Option C: Decorator**
   - `@with_risk_manager` decorator
   - Pros: Non-invasive
   - Cons: Magic, harder to debug

**Selected**: Option B - Composition

**Rationale**: Explicit is better than implicit. RiskManager is easy to test in isolation. No inheritance conflicts with NautilusTrader's Strategy base class.

---

## Implementation Strategy

### Phase 1: Foundation (RiskConfig & Core Types)

**Goal**: Define configuration model and core data structures

**Deliverables**:
- [x] `risk/config.py` - RiskConfig Pydantic model
- [x] Unit tests for configuration validation
- [ ] Documentation of configuration options

**Dependencies**: None

**Estimated Complexity**: Low

---

### Phase 2: RiskManager Core

**Goal**: Implement stop-loss generation and position tracking

**Deliverables**:
- [ ] `risk/manager.py` - RiskManager class
- [ ] `on_position_opened()` - Generate stop-loss
- [ ] `on_position_closed()` - Cancel stop-loss
- [ ] `on_position_changed()` - Update stop-loss (for trailing)
- [ ] Unit tests with mocked strategy

**Dependencies**: Phase 1

**Estimated Complexity**: Medium

---

### Phase 3: Position Limits

**Goal**: Implement position size validation

**Deliverables**:
- [ ] `validate_order()` method in RiskManager
- [ ] Per-instrument max position check
- [ ] Total exposure check
- [ ] Integration with RiskEngineConfig
- [ ] Unit tests for limit scenarios

**Dependencies**: Phase 2

**Estimated Complexity**: Medium

---

### Phase 4: Integration Testing

**Goal**: Verify end-to-end behavior with BacktestNode

**Deliverables**:
- [ ] `test_risk_backtest.py` - Integration tests
- [ ] Test stop-loss execution on gap
- [ ] Test position limit rejection
- [ ] Test with real market data

**Dependencies**: Phase 3

**Estimated Complexity**: Medium

---

### Phase 5: Advanced Features (Optional)

**Goal**: Trailing stops and dynamic boundaries

**Deliverables**:
- [ ] `trailing_stop_market()` integration
- [ ] `ou_estimator.py` - OU parameter estimation
- [ ] Dynamic boundary calculation
- [ ] Unit tests for advanced features

**Dependencies**: Phase 4

**Estimated Complexity**: High

---

## File Structure

```
nautilus_dev/
├── risk/
│   ├── __init__.py           # Public exports
│   ├── config.py             # RiskConfig, StopLossType enum
│   ├── manager.py            # RiskManager class
│   └── ou_estimator.py       # OU param estimation (Phase 5)
├── tests/
│   ├── test_risk_config.py   # Config validation tests
│   ├── test_risk_manager.py  # RiskManager unit tests
│   └── integration/
│       └── test_risk_backtest.py  # End-to-end tests
└── strategies/
    └── examples/
        └── risk_managed_strategy.py  # Example usage
```

## API Design

### Public Interface

```python
from nautilus_dev.risk import RiskConfig, RiskManager

class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig):
        super().__init__(config)
        self.risk_manager = RiskManager(
            config=config.risk,
            strategy=self,
        )

    def on_start(self) -> None:
        self.subscribe_to_positions()

    def on_event(self, event: Event) -> None:
        # Delegate risk events to manager
        self.risk_manager.handle_event(event)

    def submit_trade(self, instrument_id: InstrumentId, side: OrderSide, qty: Quantity) -> None:
        order = self.order_factory.market(instrument_id, side, qty)

        # Pre-flight validation
        if not self.risk_manager.validate_order(order):
            self.log.warning(f"Order rejected by risk manager: {order}")
            return

        self.submit_order(order)
```

### Configuration

```python
from pydantic import BaseModel
from decimal import Decimal
from typing import Literal

class RiskConfig(BaseModel):
    """Risk management configuration."""

    # Stop-Loss Settings
    stop_loss_enabled: bool = True
    stop_loss_pct: Decimal = Decimal("0.02")  # 2% default
    stop_loss_type: Literal["market", "limit", "emulated"] = "market"

    # Trailing Stop (optional)
    trailing_stop: bool = False
    trailing_distance_pct: Decimal = Decimal("0.01")  # 1%
    trailing_offset_type: Literal["price", "basis_points"] = "price"

    # Position Limits
    max_position_size: dict[str, Decimal] | None = None  # Per instrument
    max_total_exposure: Decimal | None = None  # Total portfolio

    # Advanced (Phase 5)
    dynamic_boundaries: bool = False  # OU-based
    ou_lookback_days: int = 30
```

### RiskManager API

```python
class RiskManager:
    """Manages stop-loss orders and position limits."""

    def __init__(self, config: RiskConfig, strategy: Strategy) -> None:
        self.config = config
        self.strategy = strategy
        self.active_stops: dict[PositionId, ClientOrderId] = {}

    def handle_event(self, event: Event) -> None:
        """Route position events to appropriate handlers."""
        if isinstance(event, PositionOpened):
            self._on_position_opened(event)
        elif isinstance(event, PositionClosed):
            self._on_position_closed(event)
        elif isinstance(event, PositionChanged):
            self._on_position_changed(event)

    def validate_order(self, order: Order) -> bool:
        """Pre-flight check against position limits."""
        # Returns False if order would exceed limits

    def _on_position_opened(self, event: PositionOpened) -> None:
        """Generate stop-loss when position opens."""

    def _on_position_closed(self, event: PositionClosed) -> None:
        """Cancel stop-loss when position closes."""

    def _on_position_changed(self, event: PositionChanged) -> None:
        """Update trailing stop when position changes."""

    def _calculate_stop_price(self, position: Position) -> Price:
        """Calculate stop price based on config and position side."""

    def _create_stop_order(self, position: Position, stop_price: Price) -> Order:
        """Create appropriate stop order (market/limit/emulated)."""
```

## Testing Strategy

### Unit Tests

- [x] Test `RiskConfig` validation (invalid percentages, etc.)
- [ ] Test `_calculate_stop_price()` for LONG and SHORT
- [ ] Test `validate_order()` with position limits
- [ ] Test `handle_event()` routing
- [ ] Test stop order creation with `reduce_only=True`

### Integration Tests

- [ ] Test with BacktestNode: stop-loss triggers correctly
- [ ] Test gap-through scenario (price gaps past stop)
- [ ] Test position limit rejection
- [ ] Test trailing stop updates on favorable moves
- [ ] Test multiple positions with separate stops

### Edge Cases

- [ ] Position closed before stop created (race condition)
- [ ] Stop triggered by opening bar (Bybit bug scenario)
- [ ] Multiple rapid position changes
- [ ] Position flip attempt blocked by `reduce_only`

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Bybit trigger direction bug | High | Low (fixed in Rust) | Use nightly wheels, add warning |
| Binance API change | High | Low (fixed) | Version check, use nightly 12/10+ |
| Stop not created in time | High | Low | Submit stop immediately on PositionOpened |
| Position flip on stop | Medium | Medium | Always use `reduce_only=True` |
| Backtest fill unrealistic | Low | Medium | Use `BestPriceFillModel` |

## Dependencies

### External Dependencies

- NautilusTrader nightly >= 1.222.0 (for Binance Algo Order API fix)
- Pydantic >= 2.0 (for configuration)
- numpy (for OU estimation, Phase 5)

### Internal Dependencies

- Spec 008 (BaseEvolveStrategy) - for strategy integration
- NautilusTrader Strategy base class
- OrderFactory for stop order creation
- Cache for position tracking

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Stop-loss generated within 10ms of PositionOpened event
- [ ] 100% of positions have corresponding stop-loss (when enabled)
- [ ] Zero positions exceed configured limits
- [ ] Documentation updated with usage examples
- [ ] Code review approved
- [ ] Alpha-debug verification complete

## Constitution Check

### KISS & YAGNI
- [x] Static stop-loss is simple and covers most cases
- [x] Dynamic boundaries reserved for Phase 5 (optional)
- [x] No premature optimization

### Native First
- [x] Uses `order_factory.stop_market()` (native)
- [x] Uses `reduce_only=True` (native parameter)
- [x] Integrates with existing PositionOpened/Closed events

### Black Box Design
- [x] RiskManager has clean API, hidden implementation
- [x] Strategy integration via composition, not inheritance
- [x] Replaceable: if manager doesn't work, swap implementation

### Performance Constraints
- [x] No `df.iterrows()` (not using pandas)
- [x] Stop creation is O(1) operation
- [x] No blocking calls in event handlers

## Related Resources

- **Paper**: Kitapbayev & Leung (2025) - "A Coupled Optimal Stopping Approach to Pairs Trading"
- **GitHub Issue**: #3287 - Binance API change breaks conditional orders
- **Discord**: Stop-loss patterns documented in `docs/discord/questions.md:2177`
