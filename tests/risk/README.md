# Risk Manager Test Suite

## Overview
Comprehensive test coverage for the NautilusTrader risk management system.

## Test Files
- `test_risk_manager.py` - Original tests (35 tests)
- `test_risk_manager_extended.py` - Extended tests (41 tests)

## Coverage Achievement
**100% coverage** on `risk/manager.py` (154 statements)

## Test Categories

### 1. Core Functionality (`test_risk_manager.py`)
- **Stop-Loss Management**: Automatic stop generation, cancellation, trailing stops
- **Position Limits**: Per-instrument and total exposure limits
- **Circuit Breaker Integration**: Order rejection on HALTED/REDUCING states
- **Daily Loss Tracking**: Event routing and limit enforcement

### 2. Edge Cases & Error Handling (`test_risk_manager_extended.py`)

#### Zero Positions
- Order validation with no positions
- Zero exposure handling
- Empty position size queries

#### Limit Breaches
- Exact limit boundaries (inclusive/exclusive)
- Minimal breaches (1 unit, $1)
- Multiple instruments with independent limits

#### Rapid Updates
- Multiple PositionChanged events in sequence
- Trailing stop updates without active stops
- Disabled trailing stop behavior

#### Error Handling
- Missing stop orders in cache
- Missing positions in cache
- Exception during cancel_order (cleanup verification)
- Exception during trailing stop update (old stop preservation)

#### Notional Calculation
- Quote tick priority
- Bar close fallback
- Zero notional when no price available

#### Circuit Breaker Edge Cases
- check_limit() call order verification
- None circuit breaker handling
- None daily tracker handling

#### Short Positions
- Stop price above entry (correct direction)
- SELL order risk reduction
- Trailing stop for SHORT positions

#### Event Routing
- All events routed to daily tracker
- Spy verification on handle_event

#### Instrument Not Found
- Stop price calculation without instrument in cache
- Trailing stop calculation fallback to Price.from_str

#### Property Access
- Config property
- Circuit breaker property (None and instance)
- Daily tracker property (None and instance)
- Active stops dict property

#### NautilusTrader Position Behavior
- First match return (NautilusTrader aggregates positions)
- Single aggregated position enforcement

#### Coverage Completeness
- Early return paths
- Instrument not in limit dictionary
- None net_exposure handling

## Running Tests

```bash
# Run all risk manager tests with coverage
/media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/python -m pytest \
  tests/test_risk_manager.py \
  tests/risk/test_risk_manager_extended.py \
  --cov=risk.manager \
  --cov-report=term-missing \
  -v

# Run only extended tests
/media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/python -m pytest \
  tests/risk/test_risk_manager_extended.py \
  -v

# Run with specific markers
pytest -m "not slow" tests/risk/
```

## Test Patterns

### Mock Strategy Setup
All tests use comprehensive mock strategy fixtures with:
- Order factory (stop_market, stop_limit)
- Cache (positions_open, position, order, quote_tick, bar, instrument)
- Portfolio (net_exposure, unrealized_pnls)
- Clock (utc_now)

### Position Creation
Helper function `create_mock_position()` creates properly spec'd Position mocks:
- InstrumentId
- PositionSide (LONG/SHORT)
- Entry price
- Quantity
- Position ID

### Order Creation
Helper function `create_mock_order()` creates Order mocks:
- InstrumentId
- OrderSide (BUY/SELL)
- Quantity
- Order ID

## Critical Test Cases for Production

### Real Money Safety Tests
1. **Limit Breach Prevention** (`test_order_one_unit_over_position_limit`)
   - Ensures even smallest breach is rejected
   - Production critical: prevents over-leverage

2. **Error Handling** (`test_cancel_order_exception_does_not_prevent_cleanup`)
   - Exception during cancel doesn't leak mappings
   - Production critical: prevents orphaned stops

3. **Trailing Stop Safety** (`test_trailing_stop_update_exception_keeps_old_stop`)
   - Failed stop update keeps old protection active
   - Production critical: never leaves position unprotected

4. **Zero Position Handling** (`test_validate_order_with_no_positions`)
   - First order always allowed (no false rejections)
   - Production critical: prevents missing entry signals

5. **Circuit Breaker Integration** (`test_rejects_order_when_circuit_breaker_halted`)
   - HALTED state blocks all new positions
   - Production critical: prevents catastrophic drawdown

## Notes
- Uses NautilusTrader Nightly v1.222.0 (128-bit precision)
- All tests use pytest fixtures for consistency
- Mock objects use MagicMock with proper spec=Position/Order
- Tests verify both behavior and exception safety
