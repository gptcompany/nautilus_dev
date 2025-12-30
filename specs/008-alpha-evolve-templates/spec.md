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
