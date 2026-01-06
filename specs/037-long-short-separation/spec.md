# Feature Specification: Long/Short Meta-Model Separation

**Feature Branch**: `037-long-short-separation`
**Created**: 2026-01-06
**Status**: Draft
**Input**: User description: "Long/Short Meta-Model Separation for improved strategy management"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Directional Strategy Tagging (Priority: P1)

A trading system operator needs to categorize strategies by their directional bias to enable different risk allocation and confidence thresholds for long versus short positions.

**Why this priority**: Foundation for all other features - without strategy classification, directional separation cannot occur. This enables the core architectural change recommended by JFDS research.

**Independent Test**: Can be tested by registering strategies with LONG_ONLY, SHORT_ONLY, or LONG_SHORT tags and verifying the meta-controller stores and retrieves these classifications correctly without any budget allocation logic.

**Acceptance Scenarios**:

1. **Given** a meta-controller is initialized, **When** a strategy is registered with `direction_bias=LONG_ONLY`, **Then** the strategy is classified as long-only in the meta-controller's strategy registry
2. **Given** strategies are registered with mixed directional biases, **When** querying the meta-controller for long-only strategies, **Then** only strategies tagged as LONG_ONLY or LONG_SHORT are returned
3. **Given** a strategy registered without an explicit direction_bias parameter, **When** the registration completes, **Then** the strategy defaults to LONG_SHORT (bidirectional)

---

### User Story 2 - Separate Budget Allocation by Direction (Priority: P1)

A portfolio manager needs to allocate different capital budgets to long versus short strategies to reflect different risk profiles and market conditions.

**Why this priority**: Core business requirement that directly addresses the JFDS research finding that long and short strategies have different risk characteristics and should be managed separately.

**Independent Test**: Can be tested by configuring long_budget=60% and short_budget=40%, registering mixed strategies, and verifying that weight allocation respects these budgets independently without requiring regime detection or confidence thresholds.

**Acceptance Scenarios**:

1. **Given** meta-controller configured with long_budget=0.6 and short_budget=0.4, **When** calculating strategy weights, **Then** total long strategy weights sum to max 0.6 and total short strategy weights sum to max 0.4
2. **Given** only long-only strategies are registered, **When** calculating weights, **Then** weights are allocated only from the long_budget pool, and short_budget remains unused
3. **Given** strategies of all directional types, **When** a LONG_SHORT strategy is weighted, **Then** its weight is allocated proportionally from both long and short budgets based on its current signal direction

---

### User Story 3 - Direction-Specific Confidence Thresholds (Priority: P2)

A risk manager needs to set different minimum confidence thresholds for long versus short positions because short strategies perform better in different market conditions.

**Why this priority**: Enhances risk management by allowing more conservative thresholds for riskier directional bets (typically shorts). Builds on P1 infrastructure.

**Independent Test**: Can be tested by setting long_min_confidence=0.55 and short_min_confidence=0.65, generating signals with varying confidence levels, and verifying that position sizing respects these different thresholds per direction.

**Acceptance Scenarios**:

1. **Given** long_min_confidence=0.55 and short_min_confidence=0.65, **When** a long signal has confidence=0.58, **Then** the position is sized normally
2. **Given** long_min_confidence=0.55 and short_min_confidence=0.65, **When** a short signal has confidence=0.60, **Then** the position size is zero (below threshold)
3. **Given** different confidence thresholds per direction, **When** a LONG_SHORT strategy generates both signals, **Then** each direction is evaluated against its respective threshold independently

---

### User Story 4 - Regime-Conditional Budget Adjustment (Priority: P3)

A portfolio manager needs to automatically increase short allocation during bear market regimes because short strategies typically perform better in downtrends.

**Why this priority**: Advanced feature that optimizes capital allocation based on market conditions. Requires all previous features to be implemented first.

**Independent Test**: Can be tested by simulating different regime detections (bull/normal/bear) and verifying that the long/short budget allocation adjusts according to configured regime rules without requiring live market data.

**Acceptance Scenarios**:

1. **Given** regime detected as "mean_reverting" (bear market proxy), **When** calculating budget allocation, **Then** short_budget increases by configured adjustment factor (e.g., +10% relative shift from long to short)
2. **Given** regime detected as "trending" (bull market proxy), **When** calculating budget allocation, **Then** long_budget receives the majority allocation (original configuration)
3. **Given** regime transitions from trending to mean_reverting, **When** budget reallocation occurs, **Then** existing positions are gradually rebalanced over N bars to avoid sudden exposure changes

---

### Edge Cases

- What happens when all registered strategies have the same directional bias (e.g., all LONG_ONLY)? The unused budget (short_budget) should remain unallocated, and the system should operate normally with only long positions.
- How does the system handle budget constraints when individual strategy weights would exceed the directional budget? Strategy weights should be normalized proportionally to fit within the budget constraint, maintaining relative weight ratios.
- What happens when a LONG_SHORT strategy switches direction mid-trade? The weight allocation should transition smoothly from one budget pool to the other, with audit logging of the reallocation.
- How are confidence thresholds applied to LONG_SHORT strategies that can generate signals in both directions? Each direction is evaluated independently against its respective threshold when the strategy generates a signal.
- What happens during regime transitions when budgets are being adjusted? Budget changes should be applied gradually (over a configurable transition period) to avoid abrupt position changes that could impact execution quality.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support three directional bias classifications: LONG_ONLY, SHORT_ONLY, and LONG_SHORT
- **FR-002**: Meta-controller MUST maintain separate budget allocations for long and short strategies (long_budget and short_budget parameters)
- **FR-003**: System MUST enforce budget constraints such that total long strategy weights cannot exceed long_budget and total short strategy weights cannot exceed short_budget
- **FR-004**: System MUST support independent confidence thresholds for long and short directions (long_min_confidence and short_min_confidence)
- **FR-005**: System MUST allow regime-conditional budget adjustment where budget allocation shifts based on detected market regime
- **FR-006**: LONG_SHORT strategies MUST have their weights allocated from the appropriate budget pool based on their current signal direction
- **FR-007**: System MUST log all budget allocation changes and directional weight adjustments via the audit trail system
- **FR-008**: When strategy weights exceed directional budget, system MUST normalize weights proportionally to fit within budget while maintaining relative ratios
- **FR-009**: Default values MUST be: long_budget=0.60, short_budget=0.40, long_min_confidence=0.55, short_min_confidence=0.55
- **FR-010**: System MUST gracefully handle cases where no strategies match a particular directional bias (leaving that budget unallocated)

### Key Entities *(include if feature involves data)*

- **DirectionalBias**: Enumeration representing strategy directional classification
  - Values: LONG_ONLY, SHORT_ONLY, LONG_SHORT
  - Attribute of StrategyRegistration

- **DirectionalBudget**: Configuration object containing budget allocation rules
  - Attributes: long_budget (float 0-1), short_budget (float 0-1)
  - Constraint: long_budget + short_budget should typically equal 1.0 but can be less (conservative allocation)

- **DirectionalThresholds**: Configuration object for confidence requirements
  - Attributes: long_min_confidence (float 0-1), short_min_confidence (float 0-1)
  - Used by sizing calculation to filter signals below threshold

- **RegimeBudgetAdjustment**: Rules for budget reallocation based on market regime
  - Attributes: regime_type, budget_shift_pct, transition_bars
  - Relationships: Links MarketRegime to budget adjustments

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System can manage portfolios with separate long and short budget allocations, with allocation accuracy within 1% of configured budgets
- **SC-002**: Strategy weights respect directional budget constraints 100% of the time (no budget overruns)
- **SC-003**: Different confidence thresholds per direction result in measurably different position sizing behavior (verified through backtesting)
- **SC-004**: Regime-based budget adjustments occur automatically within 5 bars of regime change detection
- **SC-005**: All budget allocation changes and directional weight adjustments are captured in the audit trail with full traceability
- **SC-006**: Portfolio Sharpe ratio improves by 5-15% when using directional separation versus unified allocation (per JFDS research expectations)

## Assumptions

- Existing meta-controller infrastructure (MetaController class) provides the foundation for weight calculation
- Existing regime detection (SpectralRegimeDetector) accurately identifies market regimes for regime-conditional adjustments
- Existing audit trail system (Spec 030) is operational and can log parameter changes
- Strategy registration already includes callback mechanisms for weight updates
- Default budget split (60/40 long/short) is reasonable for most equity portfolios; users can override
- Confidence thresholds default to equal values (0.55) but can be adjusted independently
- Regime-conditional adjustments use a conservative approach (gradual transitions) to avoid execution quality degradation
