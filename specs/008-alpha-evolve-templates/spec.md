# Feature Specification: Alpha-Evolve Strategy Templates

**Feature Branch**: `008-alpha-evolve-templates`
**Created**: 2025-12-27
**Status**: Draft
**Input**: Template di strategie NautilusTrader con EVOLVE-BLOCK markers. Base class con equity tracking e seed strategies (momentum) per iniziare evoluzione.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Base Evolvable Strategy (Priority: P1)

As a strategy evolution system, I need a base strategy class with EVOLVE-BLOCK markers so that mutations target only decision logic while infrastructure (order execution, position tracking) remains stable.

**Why this priority**: Foundation for all evolvable strategies. Without proper structure, mutations break non-decision code.

**Independent Test**: Can be fully tested by inheriting from base class and verifying EVOLVE-BLOCK markers are present and replaceable.

**Acceptance Scenarios**:

1. **Given** a class inheriting from BaseEvolveStrategy, **When** strategy is loaded, **Then** EVOLVE-BLOCK markers are present in expected location.
2. **Given** a running strategy, **When** on_bar() is called, **Then** equity curve is tracked automatically.
3. **Given** a strategy with mutated decision logic, **When** strategy executes, **Then** order submission and position tracking work correctly.
4. **Given** a strategy, **When** requesting equity curve, **Then** returns list of {timestamp, equity} entries.

---

### User Story 2 - Seed Momentum Strategy (Priority: P1)

As a user starting evolution, I need a working seed strategy so that evolution has a viable starting point rather than random code.

**Why this priority**: Evolution needs a functional starting point. Random initialization produces mostly invalid strategies.

**Independent Test**: Can be fully tested by running backtest with seed strategy and verifying it produces trades and metrics.

**Acceptance Scenarios**:

1. **Given** seed momentum strategy, **When** backtested on 6 months BTC data, **Then** produces at least 10 trades.
2. **Given** seed strategy, **When** EVOLVE-BLOCK is extracted, **Then** contains decision logic (entry/exit signals).
3. **Given** seed strategy, **When** mutated via patching system, **Then** modified version still executes without errors.
4. **Given** seed strategy, **When** evaluated, **Then** returns non-zero Sharpe and Calmar ratios.

---

### User Story 3 - Native Indicator Integration (Priority: P1)

As a strategy developer, I need templates that use native Rust indicators so that evolved strategies maintain high performance.

**Why this priority**: Python indicators are 100x slower. Native Rust indicators are essential for backtest performance.

**Independent Test**: Can be fully tested by verifying strategy uses nautilus_trader.indicators imports.

**Acceptance Scenarios**:

1. **Given** seed strategy, **When** inspecting imports, **Then** uses ExponentialMovingAverage from nautilus_trader.indicators.
2. **Given** evolved strategy mutating indicator periods, **When** backtested, **Then** performance difference is measurable.
3. **Given** EVOLVE-BLOCK, **When** LLM adds new indicator, **Then** must use native Rust indicator classes.

---

### User Story 4 - Order Management Utilities (Priority: P2)

As a strategy template, I need helper methods for common order patterns so that EVOLVE-BLOCK can focus on signal logic.

**Why this priority**: Simplifies mutation targets. LLM doesn't need to reimplement order submission.

**Independent Test**: Can be fully tested by calling helper methods and verifying orders are created correctly.

**Acceptance Scenarios**:

1. **Given** strategy with open position, **When** _close_position() is called, **Then** market order is submitted to close.
2. **Given** no open position, **When** _enter_long(quantity) is called, **Then** market buy order is submitted.
3. **Given** open long position, **When** _enter_short(quantity) is called, **Then** closes long and opens short.
4. **Given** order helpers, **When** used in EVOLVE-BLOCK, **Then** LLM can write simpler decision logic.

---

### Edge Cases

- What happens when strategy receives bar with zero volume?
- What happens when position size exceeds available balance?
- How does strategy handle exchange disconnection during backtest?
- What happens when indicator needs more bars than available history?
- How are partial fills handled in order helpers?

## Requirements *(mandatory)*

### Functional Requirements

#### Base Strategy
- **FR-001**: BaseEvolveStrategy MUST inherit from nautilus_trader.trading.strategy.Strategy
- **FR-002**: BaseEvolveStrategy MUST track equity curve on every bar (timestamp, equity)
- **FR-003**: BaseEvolveStrategy MUST define `_on_bar_evolved(bar)` method with EVOLVE-BLOCK markers
- **FR-004**: BaseEvolveStrategy MUST provide `get_equity_curve()` method
- **FR-005**: BaseEvolveStrategy MUST handle strategy lifecycle (on_start, on_stop, on_reset)

#### Seed Strategy
- **FR-006**: MomentumEvolveStrategy MUST use dual EMA crossover as baseline logic
- **FR-007**: Seed strategy MUST be profitable on at least one symbol in sample period
- **FR-008**: Seed strategy MUST use only native Rust indicators
- **FR-009**: Seed strategy MUST have complete EVOLVE-BLOCK with entry/exit logic

#### Order Helpers
- **FR-010**: Template MUST provide _enter_long(quantity) helper method
- **FR-011**: Template MUST provide _enter_short(quantity) helper method
- **FR-012**: Template MUST provide _close_position() helper method
- **FR-013**: Template MUST provide _get_position_size() helper method
- **FR-014**: Helpers MUST handle insufficient balance gracefully

### Key Entities

- **BaseEvolveStrategy**: Abstract base class for evolvable strategies. Contains lifecycle management, equity tracking, order helpers.
- **MomentumEvolveStrategy**: Concrete seed strategy using EMA crossover. Starting point for evolution.
- **EquityPoint**: Single equity curve entry. Attributes: timestamp (datetime), equity (float)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Seed strategy produces positive returns on at least 50% of 6-month backtests
- **SC-002**: 90% of valid mutations produce strategies that execute without runtime errors
- **SC-003**: Equity tracking overhead adds less than 5% to backtest runtime
- **SC-004**: Order helpers reduce EVOLVE-BLOCK complexity by 50% (fewer lines needed for same logic)
- **SC-005**: Templates work with both 1-minute and 1-hour bar data

## Assumptions

- Strategies trade single symbol at a time (multi-symbol support in future iteration)
- Market orders only (limit orders in future iteration)
- No leverage configuration (uses exchange defaults)
- BTC and ETH are primary target symbols

## Dependencies

- **NautilusTrader**: Strategy base class, indicators, order types
- **spec-006**: EVOLVE-BLOCK marker format for patching compatibility

## Out of Scope

- Multi-symbol strategies
- Limit order management
- Risk management rules (stop-loss, position sizing)
- Portfolio-level allocation
- Strategy parameter optimization (handled by evolution)

---

## Future Enhancements (Black Book Concepts)

> **Source**: "The Black Book of Financial Hacking" - J.C. Lotter
> **Philosophy**: Add complexity ONLY if OOS shows problems.

### FE-001: Multiple Evolvable Blocks

**Current**: Single EVOLVE-BLOCK for all decision logic

**Enhancement**: Multiple named blocks for entry, exit, sizing

```python
class MultiBlockEvolveStrategy(Strategy):
    def _on_bar_evolved(self, bar):
        # === EVOLVE-BLOCK: entry_logic ===
        # LLM can mutate entry signals independently
        if self.ema_fast.value > self.ema_slow.value:
            entry_signal = True
        # === END EVOLVE-BLOCK ===

        # === EVOLVE-BLOCK: exit_logic ===
        # LLM can mutate exit logic independently
        if self.position and self.ema_fast.value < self.ema_slow.value:
            self._close_position()
        # === END EVOLVE-BLOCK ===

        # === EVOLVE-BLOCK: position_sizing ===
        # LLM can mutate sizing independently
        size = self.calculate_kelly_size(entry_signal)
        # === END EVOLVE-BLOCK ===
```

**Trigger**: When single-block evolution struggles to optimize entry/exit/sizing together (conflicting objectives)

**Trade-off**: Requires coordinated mutation of multiple blocks, more complex patching

**Reference**: Black Book - "Evolve components independently when joint optimization fails"

### FE-002: State Machine Templates

**Current**: Simple signal-based logic

**Enhancement**: Explicit state machine for complex strategies

```python
class StateMachineTemplate(BaseEvolveStrategy):
    """
    State machine template for regime-aware strategies.

    States: ACCUMULATION, TRENDING, DISTRIBUTION, SIDEWAYS
    """
    def __init__(self):
        self.state = "SIDEWAYS"

    def _on_bar_evolved(self, bar):
        # === EVOLVE-BLOCK: state_detection ===
        # LLM mutates regime detection logic
        volatility = self.calculate_volatility()
        if volatility > threshold_high:
            self.state = "TRENDING"
        elif volatility < threshold_low:
            self.state = "SIDEWAYS"
        # === END EVOLVE-BLOCK ===

        # === EVOLVE-BLOCK: state_action ===
        # LLM mutates action per state
        if self.state == "TRENDING":
            self._trend_following_logic()
        elif self.state == "SIDEWAYS":
            self._mean_reversion_logic()
        # === END EVOLVE-BLOCK ===
```

**Trigger**: When single-strategy evolution produces inconsistent behavior across market regimes

**Trade-off**: More complex template, but better for adaptive strategies

**Reference**: Black Book - "Use state machines for regime-dependent logic"

### FE-003: Feature Engineering Helpers

**Current**: Only native Rust indicators (EMA, RSI, etc.)

**Enhancement**: Pre-built feature combinations for LLM to use

```python
class FeatureLibrary:
    """
    Pre-computed features for LLM to reference in EVOLVE-BLOCK.
    """
    @property
    def momentum_features(self):
        return {
            'ema_cross': self.ema_fast.value > self.ema_slow.value,
            'rsi_oversold': self.rsi.value < 30,
            'rsi_overbought': self.rsi.value > 70,
            'price_above_ema': self.bar.close > self.ema.value,
        }

    @property
    def volatility_features(self):
        return {
            'atr_expanding': self.atr.value > self.atr_slow.value,
            'bollinger_squeeze': self.bb_upper - self.bb_lower < threshold,
        }

    # LLM can reference in EVOLVE-BLOCK:
    # if self.features.momentum_features['ema_cross']:
```

**Trigger**: When LLM mutations frequently produce invalid indicator combinations or slow custom calculations

**Trade-off**: Larger template, but faster LLM mutation (no need to implement features from scratch)

**Reference**: Black Book - "Pre-compute features to reduce mutation complexity"

### FE-004: Risk-Aware Position Sizing

**Current**: Fixed position size or simple helpers

**Enhancement**: Built-in Kelly criterion and risk parity sizing

```python
class RiskAwareTemplate(BaseEvolveStrategy):
    def calculate_kelly_size(self, win_rate, avg_win, avg_loss):
        """
        Kelly criterion for optimal position sizing.

        f = (p * b - q) / b
        where p = win rate, q = 1-p, b = avg_win/avg_loss
        """
        if avg_loss == 0:
            return 0
        b = avg_win / avg_loss
        kelly_fraction = (win_rate * b - (1 - win_rate)) / b
        # Use half-Kelly for safety
        return max(0, kelly_fraction / 2)

    def calculate_risk_parity_size(self, volatility):
        """
        Size inversely proportional to volatility.
        """
        target_vol = 0.02  # 2% portfolio volatility
        return target_vol / volatility if volatility > 0 else 0
```

**Trigger**: When evolved strategies blow up in live trading due to over-sizing

**Trade-off**: More complex position sizing logic, but prevents ruin

**Reference**: Black Book - "Never evolve position sizing - use proven formulas"

---

**Decision Log** (2026-01-06):
- Single EVOLVE-BLOCK chosen for MVP simplicity
- Simple momentum template for seed strategy
- Black Book enhancements documented for complex strategy needs
