# Feature Specification: Adaptive Discounted Thompson Sampling (ADTS)

**Feature Branch**: `032-adts-discounting`
**Created**: 2026-01-06
**Status**: Draft
**Source**: Gap #3 (HIGH) | [Canonical Mapping](../028-validation/gaps_to_specs_mapping.md)

## Problem Statement

Thompson Sampling in `particle_portfolio.py` uses uniform decay rate, not regime-adaptive. In volatile markets, old performance data should be forgotten faster; in stable markets, historical data should be preserved longer.

**Solution** (de Freitas Fonseca et al. 2024): Make decay factor a function of regime volatility:
```python
decay = 0.99 - 0.04 * normalized_volatility  # Range: [0.95, 0.99]
```

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adaptive Forgetting in Volatile Regimes (Priority: P1)

As a portfolio manager, when market volatility increases, I need the system to forget old performance data faster so that it can quickly adapt to new market conditions and avoid using outdated strategy weights.

**Why this priority**: This is the core value proposition - enabling faster adaptation in volatile markets. Without this, the system remains slow to respond during regime changes, leading to suboptimal strategy selection and potential losses.

**Independent Test**: Can be fully tested by simulating a regime transition from low to high volatility and verifying that decay rates increase (from ~0.99 to ~0.95) and old performance data is discounted faster, resulting in quicker strategy weight adjustments.

**Acceptance Scenarios**:

1. **Given** a stable market regime with low volatility (variance_ratio < 0.7), **When** the Thompson Sampling update is called, **Then** the decay factor should be high (~0.99) to preserve historical performance data
2. **Given** a volatile/trending market regime with high volatility (variance_ratio > 1.5), **When** the Thompson Sampling update is called, **Then** the decay factor should be low (~0.95) to quickly forget old performance data
3. **Given** a normal market regime with moderate volatility (0.7 <= variance_ratio <= 1.5), **When** the Thompson Sampling update is called, **Then** the decay factor should be interpolated between 0.95 and 0.99 based on the normalized volatility level

---

### User Story 2 - Seamless Integration with Regime Detection (Priority: P2)

As a strategy developer, I need the adaptive decay mechanism to automatically integrate with the existing IIRRegimeDetector so that volatility-driven decay adjustments happen without manual configuration or parameter tuning.

**Why this priority**: This ensures the feature is truly "non-parametric" (Pillar P3) and doesn't introduce new hyperparameters that would require optimization. It leverages existing infrastructure for regime detection.

**Independent Test**: Can be tested by instantiating a ThompsonSelector with an IIRRegimeDetector and verifying that decay rates automatically adjust based on the detector's variance_ratio output, with no additional configuration required.

**Acceptance Scenarios**:

1. **Given** a ThompsonSelector initialized with an IIRRegimeDetector, **When** strategy returns are updated, **Then** the decay factor is automatically calculated from the regime detector's variance_ratio without requiring manual parameter specification
2. **Given** the regime detector outputs a variance_ratio, **When** the decay factor is calculated, **Then** it follows the formula: `decay = 0.99 - 0.04 * normalized_volatility` where normalized_volatility is derived from variance_ratio
3. **Given** a ThompsonSelector without a regime detector, **When** updates are called, **Then** it falls back to the fixed decay rate (0.99) for backward compatibility

---

### User Story 3 - Observable Decay Behavior (Priority: P3)

As a system monitor, I need to observe how decay rates change over time and correlate with regime changes so that I can verify the adaptive mechanism is working correctly and debug unexpected strategy selection behavior.

**Why this priority**: Observability is important for validation and debugging but doesn't directly impact trading performance. It's a supporting feature for the core adaptive mechanism.

**Independent Test**: Can be tested by capturing decay rates during simulated regime transitions and verifying they can be logged, retrieved, and correlated with variance_ratio changes through the existing audit trail system.

**Acceptance Scenarios**:

1. **Given** an active ThompsonSelector with audit trail enabled, **When** decay rates are calculated, **Then** they are logged through the audit system with metadata including variance_ratio, regime type, and timestamp
2. **Given** historical decay rate logs, **When** analyzing strategy selection behavior, **Then** users can correlate decay rate changes with regime transitions and understand why strategy weights changed

---

### Edge Cases

- What happens when variance_ratio is extremely high (>10)? System should cap normalized_volatility at 1.0 to prevent decay from going below 0.95
- What happens when variance_ratio is zero or near-zero? System should handle division by zero and default to normal regime (decay ~0.97)
- What happens when IIRRegimeDetector is not provided? System should fall back to fixed decay rate (0.99) for backward compatibility
- What happens during warmup period when variance estimates are unstable? System should use default decay rate until regime detector has sufficient samples

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate decay factor as a function of regime volatility using the formula: `decay = 0.99 - 0.04 * normalized_volatility` where normalized_volatility ranges from 0.0 (low volatility) to 1.0 (high volatility)
- **FR-002**: System MUST derive normalized_volatility from the IIRRegimeDetector's variance_ratio property by mapping variance_ratio ranges to [0.0, 1.0] scale (e.g., variance_ratio < 0.7 → 0.0, variance_ratio > 1.5 → 1.0, linear interpolation between)
- **FR-003**: System MUST apply the adaptive decay factor during Thompson Sampling updates, replacing the current fixed `self.decay` multiplication with the calculated adaptive decay
- **FR-004**: System MUST maintain backward compatibility by supporting both fixed decay (when no regime detector is provided) and adaptive decay (when regime detector is integrated)
- **FR-005**: System MUST clamp decay factor to the range [0.95, 0.99] to prevent extreme forgetting or over-retention of historical data
- **FR-006**: System MUST integrate with existing IIRRegimeDetector without requiring new hyperparameters or configuration beyond providing the detector instance
- **FR-007**: System MUST log adaptive decay events through the audit trail system (if enabled) including decay_rate, variance_ratio, regime, and timestamp for observability

### Key Entities

- **AdaptiveDecayCalculator**: Component responsible for calculating decay factor from variance_ratio, encapsulating the mapping logic and clamping behavior
- **VolatilityContext**: Data structure containing variance_ratio, regime type, and normalized_volatility used as input for decay calculation
- **DecayEvent**: Audit trail event capturing decay_rate, variance_ratio, regime, and timestamp for observability

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: During simulated regime transitions from stable to volatile markets, strategy weight adaptation time decreases by at least 30% compared to fixed decay baseline (measured as number of periods to reach new equilibrium weights)
- **SC-002**: System adapts decay rates across the full [0.95, 0.99] range within 3 standard regime transitions (stable → volatile → stable) without manual intervention
- **SC-003**: All existing tests for ThompsonSelector continue to pass with backward compatibility maintained (zero regressions)
- **SC-004**: Decay rate changes are observable in audit logs with 100% coverage of regime transitions (every regime change produces a corresponding decay event in audit trail)
- **SC-005**: Integration requires zero new hyperparameters beyond providing an IIRRegimeDetector instance (fully parameter-free as per Pillar P3)

## Assumptions

- IIRRegimeDetector is already implemented and provides variance_ratio property that reliably indicates regime volatility
- Variance_ratio ranges are approximately: < 0.7 (mean-reverting/stable), 0.7-1.5 (normal), > 1.5 (trending/volatile)
- The decay range [0.95, 0.99] is appropriate for typical trading timeframes (inferred from existing code using 0.99 as fixed decay)
- Audit trail system (Spec 030) is available for logging decay events, though not required for core functionality
- Thompson Sampling update methods (update() and update_continuous()) are the appropriate integration points for adaptive decay

## References

- de Freitas Fonseca et al. 2024, "Bandit Networks with Adaptive Discounted Thompson Sampling"
- CLAUDE.md Pillar P3 "Non Parametrico" - adaptive to data, not fixed parameters
- `strategies/common/adaptive_control/particle_portfolio.py` (ThompsonSelector class)
- `strategies/common/adaptive_control/dsp_filters.py` (IIRRegimeDetector class)
