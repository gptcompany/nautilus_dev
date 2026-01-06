# Feature Specification: Transaction Cost Model with Kyle's Lambda

**Feature Branch**: `035-transaction-cost`
**Created**: 2026-01-06
**Status**: Draft
**Source**: Gap #5 (MED) | [Canonical Mapping](../028-validation/gaps_to_specs_mapping.md)

## Problem Statement

`sops_sizing.py` produces theoretical position sizes but does NOT adjust for market impact. Position sizing ignores transaction costs, violating Pillar P4 (Scalare).

**Solution** (Almgren-Chriss 2001): Implement Kyle's Lambda market impact model:
```
impact = lambda * sqrt(volume / ADV)
```

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Market Impact Estimation Before Order Execution (Priority: P1)

A strategy using SOPS position sizing receives a signal to buy 5 BTC when the current daily volume is 1000 BTC. The transaction cost model estimates that this order will consume approximately 0.5% of daily volume and calculates expected price impact of 8 basis points. The system adjusts the theoretical position from 5 BTC to 4.8 BTC to account for this slippage, ensuring the expected return after costs remains positive.

**Why this priority**: Core functionality - without market impact adjustment, position sizing violates Pillar P4 (Scalare) by assuming infinite liquidity. This is the minimum viable feature that addresses Gap #5.

**Independent Test**: Can be fully tested by feeding synthetic signals to the sizing module with known liquidity parameters and verifying that position sizes are reduced proportionally to expected impact. Delivers immediate value by preventing oversized orders in low-liquidity conditions.

**Acceptance Scenarios**:

1. **Given** a theoretical position size of 5 BTC and daily volume of 1000 BTC, **When** market impact is calculated using Kyle's Lambda with default parameters, **Then** expected impact is between 5-15 basis points and adjusted position size is 4.85-4.95 BTC
2. **Given** a theoretical position size of 100 BTC and daily volume of 1000 BTC (10% of volume), **When** market impact is calculated, **Then** expected impact exceeds 100 basis points and adjusted position size is reduced to below 50 BTC
3. **Given** a theoretical position size of 0.1 BTC and daily volume of 10000 BTC (0.001% of volume), **When** market impact is calculated, **Then** expected impact is below 1 basis point and adjusted position size is within 1% of theoretical size

---

### User Story 2 - Adaptive Lambda Calibration from Historical Fills (Priority: P2)

After executing 50 orders over a week, the system has collected actual fill prices vs expected prices for each order. Using this data, it calibrates the Kyle's Lambda parameter from the default 0.1 to 0.15 for BTC-USD based on observed slippage patterns. Future position sizing for BTC-USD uses the calibrated lambda, improving accuracy of market impact estimates.

**Why this priority**: Enhances the basic model by learning from real execution data. This is not required for initial deployment but significantly improves accuracy over time.

**Independent Test**: Can be tested by simulating a series of trades with known slippage patterns, verifying that lambda converges toward the true value used in simulation. Delivers value by adapting to specific market microstructure.

**Acceptance Scenarios**:

1. **Given** 30+ historical fills with consistent 12 basis points average slippage and theoretical impact of 8 basis points, **When** lambda calibration runs, **Then** lambda increases from 0.1 to approximately 0.13-0.16
2. **Given** 30+ historical fills with consistent 5 basis points average slippage and theoretical impact of 8 basis points, **When** lambda calibration runs, **Then** lambda decreases from 0.1 to approximately 0.06-0.09
3. **Given** only 10 historical fills, **When** lambda calibration is requested, **Then** system continues using default lambda and logs insufficient data warning

---

### User Story 3 - Multi-Instrument Lambda Configuration (Priority: P3)

A portfolio strategy trades both BTC-USD (high liquidity, low lambda) and DOGE-USD (low liquidity, high lambda). The transaction cost model maintains separate lambda parameters for each instrument: 0.05 for BTC-USD and 0.25 for DOGE-USD. When sizing positions, each instrument uses its calibrated lambda, preventing oversizing in illiquid markets while maintaining aggressiveness in liquid ones.

**Why this priority**: Important for multi-instrument strategies but not essential for single-instrument deployments. Can be added after core functionality is validated.

**Independent Test**: Can be tested by creating a mock portfolio with two synthetic instruments having different liquidity profiles, verifying that each instrument's position sizing uses its specific lambda parameter. Delivers value for diversified strategies.

**Acceptance Scenarios**:

1. **Given** BTC-USD with lambda=0.05 and DOGE-USD with lambda=0.25, **When** both instruments receive identical signals for 10% of daily volume, **Then** DOGE-USD adjusted position is 40-60% smaller than BTC-USD adjusted position
2. **Given** an instrument without calibrated lambda, **When** market impact calculation is requested, **Then** system uses global default lambda and logs fallback event
3. **Given** lambda parameters stored in configuration, **When** strategy restarts, **Then** all instrument-specific lambdas are loaded correctly

---

### Edge Cases

- What happens when daily volume data is unavailable or zero? System should use a conservative default lambda (e.g., 0.5) and log a warning, preventing execution with unknown liquidity.
- How does the system handle position sizes that would exceed 50% of daily volume? Market impact becomes non-linear at high participation rates - system should apply a hard cap (e.g., max 10% of ADV) or use alternative execution strategy (TWAP).
- What if calibrated lambda becomes negative or excessively large (>5.0) due to outlier fills? System should validate lambda bounds [0.01, 1.0] and reject out-of-range calibrations with error logging.
- How does market impact interact with Giller power-law scaling? Impact calculation should occur BEFORE Giller scaling to maintain theoretical soundness: signal → SOPS → impact adjustment → Giller → final size.
- What happens during extreme volatility when historical fills may not be representative? System should weight recent fills more heavily or temporarily revert to default lambda if recent volatility exceeds 3x historical baseline.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST estimate market impact for every position sizing calculation using Kyle's Lambda model: `impact = lambda * sqrt(order_size / daily_volume)`
- **FR-002**: System MUST adjust theoretical position size by subtracting expected impact: `adjusted_size = theoretical_size * (1 - expected_impact_pct)`
- **FR-003**: System MUST accept configurable lambda parameter with default value of 0.1 (based on Almgren-Chriss 2001 empirical estimates)
- **FR-004**: System MUST support per-instrument lambda configuration, allowing different impact parameters for different assets
- **FR-005**: System MUST calibrate lambda from historical fill data when 30 or more fills are available for an instrument
- **FR-006**: System MUST validate lambda parameter bounds [0.01, 1.0] and reject out-of-range values
- **FR-007**: System MUST provide daily volume (ADV) input for each instrument, using 20-day rolling average as default calculation
- **FR-008**: System MUST integrate with existing SOPSGillerSizer pipeline: signal → SOPS → impact adjustment → Giller → tape weight → final size
- **FR-009**: System MUST emit audit events (Spec 030) for lambda calibration changes and market impact calculations that reduce position size by >20%
- **FR-010**: System MUST return zero position size when expected impact would exceed a configurable threshold (default: 50 basis points equals 5% adjustment)
- **FR-011**: System MUST handle missing volume data by using conservative default lambda and logging fallback event
- **FR-012**: System MUST persist calibrated lambda parameters across strategy restarts
- **FR-013**: System MUST expose current lambda values, average impact per instrument, and calibration statistics via property accessors for monitoring
- **FR-014**: System MUST weight recent fills exponentially (alpha=0.1) when calibrating lambda to adapt to changing market conditions
- **FR-015**: Users MUST be able to disable market impact adjustment via configuration flag for testing purposes

### Key Entities *(include if feature involves data)*

- **MarketImpactEstimator**: Core calculator that applies Kyle's Lambda formula to estimate price impact based on order size, daily volume, and lambda parameter
- **LambdaCalibrator**: Statistical component that analyzes historical fill data to estimate optimal lambda parameter for each instrument
- **InstrumentLiquidityProfile**: Data structure containing daily volume statistics, calibrated lambda, last calibration timestamp, and number of fills used for calibration
- **TransactionCostState**: Snapshot of market impact calculation including theoretical size, expected impact (basis points), adjusted size, lambda used, and volume participation rate

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Strategies using transaction cost model achieve average slippage within 20% of predicted impact across 100+ backtested trades
- **SC-002**: Position sizes are reduced by 5-30% in low-liquidity conditions (order size >1% of daily volume) compared to theoretical SOPS output
- **SC-003**: Lambda calibration converges within 10% of true market impact parameter after 50 simulated fills in backtests with known slippage
- **SC-004**: Market impact calculation adds less than 1 millisecond overhead to position sizing pipeline in 99% of cases
- **SC-005**: System prevents execution of orders that would exceed 10% of daily volume without explicit override
- **SC-006**: Backtest performance metrics (Sharpe ratio after costs) improve by 10-25% when transaction cost model is enabled compared to naive sizing
- **SC-007**: Calibrated lambda parameters remain stable (change <15%) across weekly recalibration cycles during normal market conditions
- **SC-008**: System correctly handles 100% of edge cases (zero volume, missing data, extreme positions) without crashing or producing infinite/NaN values
