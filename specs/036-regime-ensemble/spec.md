# Feature Specification: Regime Ensemble Voting with BOCD

**Feature Branch**: `036-regime-ensemble`
**Created**: 2026-01-06
**Status**: Draft
**Source**: Gap #8 (MED) | [Canonical Mapping](../028-validation/gaps_to_specs_mapping.md)

## Problem Statement

Current regime detection uses IIRRegimeDetector and SpectralRegimeDetector independently. No ensemble voting, no real-time changepoint detection. Regime switches detected by FFT/HMM but not real-time BOCD.

**Solution** (Adams & MacKay 2007): Add Bayesian Online Changepoint Detection (BOCD) for real-time regime change detection and create ensemble voting across multiple detectors with weighted voting based on detector confidence.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-Time Regime Change Detection (Priority: P1)

A strategy developer configures their trading strategy to use real-time regime detection. When market conditions shift from low-volatility trending to high-volatility mean-reverting, the system detects the changepoint within 2-3 bars and adjusts strategy parameters accordingly. The developer reviews regime transition logs showing detection timestamps, confidence scores, and which detector(s) triggered the change.

**Why this priority**: Real-time changepoint detection is the core value proposition. Without BOCD, regime changes are detected late (5-20 bars delay) using FFT or HMM methods, causing strategies to continue using stale parameters during regime transitions.

**Independent Test**: Can be fully tested by feeding historical price data with known regime changes (e.g., 2020 COVID crash, 2022 crypto winter) and verifying BOCD detects changepoints within 3 bars with confidence > 0.7. Delivers immediate value by reducing lag in regime-dependent strategies.

**Acceptance Scenarios**:

1. **Given** a price series transitioning from trending to mean-reverting regime, **When** BOCD processes each new bar, **Then** the system flags a regime change within 3 bars of the true changepoint with confidence >= 0.7
2. **Given** stable market conditions with no regime change, **When** BOCD processes 100 consecutive bars, **Then** no false regime changes are detected (false positive rate < 5%)
3. **Given** a regime change event, **When** BOCD detects the changepoint, **Then** the system emits a regime change event with timestamp, old regime, new regime, and confidence score

---

### User Story 2 - Ensemble Voting Reduces False Positives (Priority: P1)

A trader runs a multi-strategy portfolio where each strategy adapts to regime. Single detectors (IIR, Spectral, HMM) occasionally produce false signals causing unnecessary parameter changes and transaction costs. The ensemble voting system requires 2 out of 4 detectors to agree before declaring a regime change, reducing false positives from 15% to < 5%.

**Why this priority**: False regime changes cause real financial harm through unnecessary rebalancing and strategy parameter adjustments. Ensemble voting provides robustness without adding complexity for the end user.

**Independent Test**: Can be tested by comparing false positive rates on historical data: (1) each detector alone, (2) ensemble with majority voting. Verifies ensemble reduces false positives while maintaining true positive rate. Delivers value by reducing trading costs from regime change churn.

**Acceptance Scenarios**:

1. **Given** four regime detectors (IIR, Spectral, HMM, BOCD) with individual false positive rates of 10-15%, **When** ensemble voting is enabled with 2-out-of-4 threshold, **Then** combined false positive rate is reduced to < 5%
2. **Given** a true regime change where 3 out of 4 detectors agree, **When** ensemble evaluates the signals, **Then** regime change is confirmed within 1 bar of majority agreement
3. **Given** conflicting detector signals (2 say trending, 2 say mean-reverting), **When** ensemble cannot reach majority, **Then** system maintains current regime classification and logs the uncertainty

---

### User Story 3 - Confidence-Weighted Voting (Priority: P2)

A quantitative researcher configures the ensemble to use weighted voting instead of simple majority. BOCD (high precision, low noise) receives weight 0.4, IIR (fast but noisy) receives weight 0.2, Spectral (accurate but slow) receives weight 0.3, and HMM (if available) receives weight 0.1. The ensemble decision is based on weighted confidence scores, allowing fine-tuned control over sensitivity vs specificity tradeoff.

**Why this priority**: Weighted voting allows domain expertise to be encoded in the system. Different detectors have different strengths (speed vs accuracy, noise tolerance vs precision). This enables advanced users to optimize for their specific regime detection requirements.

**Independent Test**: Can be tested by comparing equal-weight vs expert-weighted ensemble performance on labeled regime data. Measures improvement in F1 score and detection lag. Delivers value for advanced users who understand detector characteristics.

**Acceptance Scenarios**:

1. **Given** detector weights configured as {BOCD: 0.4, IIR: 0.2, Spectral: 0.3, HMM: 0.1}, **When** all detectors signal regime change with confidence [0.8, 0.6, 0.9, 0.5], **Then** weighted score is calculated as (0.4×0.8 + 0.2×0.6 + 0.3×0.9 + 0.1×0.5) = 0.74
2. **Given** weighted voting threshold set to 0.7, **When** weighted confidence score is 0.74, **Then** regime change is confirmed
3. **Given** user updates detector weights at runtime, **When** next bar is processed, **Then** new weights are applied immediately without restarting the system

---

### User Story 4 - Integration with Existing Strategies (Priority: P2)

A developer updates their existing strategy that currently uses `IIRRegimeDetector` directly. They replace the single detector with `RegimeEnsemble` by changing 3 lines of configuration code. The strategy continues to receive regime signals via the same callback interface, but now benefits from ensemble voting and BOCD. No changes required to strategy logic or risk management code.

**Why this priority**: Backward compatibility ensures existing strategies can adopt ensemble voting without rewrites. This maximizes adoption and protects prior development investment.

**Independent Test**: Can be tested by running existing strategy backtests with (1) original IIRRegimeDetector, (2) RegimeEnsemble as drop-in replacement. Verifies API compatibility and performance improvement. Delivers value by enabling zero-friction upgrades.

**Acceptance Scenarios**:

1. **Given** an existing strategy using `self.regime_detector = IIRRegimeDetector(...)`, **When** developer changes to `self.regime_detector = RegimeEnsemble(...)`, **Then** strategy compiles and runs without errors
2. **Given** strategy expects `on_regime_change(regime: str)` callback, **When** RegimeEnsemble detects regime change, **Then** callback is invoked with same interface (regime name as string)
3. **Given** strategy queries `regime_detector.current_regime`, **When** called on RegimeEnsemble, **Then** returns current regime classification matching existing API

---

### Edge Cases

- What happens when BOCD initialization period (first 20 bars) has not completed but strategy requests current regime?
  - System should return default regime (e.g., "UNKNOWN" or last known regime) and log initialization status

- How does the system handle detector initialization at different speeds (BOCD needs 20 bars, IIR needs 5, Spectral needs 100 for FFT)?
  - Ensemble voting should only consider detectors that have completed warmup
  - Minimum 2 detectors required for ensemble decision; otherwise fallback to single detector

- What happens when market data has gaps (weekends, exchange downtime) causing timestamp discontinuities?
  - BOCD time-based priors may become invalid
  - System should detect gaps > 1 hour and reset changepoint priors

- How does ensemble handle detector failure or crash (e.g., Spectral FFT numerical overflow)?
  - Failed detector is removed from ensemble for N bars (cooling period)
  - Ensemble continues with remaining detectors if >= 2 are operational
  - Error is logged with detector name and exception details

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement Bayesian Online Changepoint Detection (BOCD) algorithm based on Adams & MacKay (2007) to detect regime transitions in real-time
- **FR-002**: BOCD detector MUST operate with O(1) amortized complexity per bar update (constant memory footprint, no growing buffers)
- **FR-003**: System MUST provide ensemble voting across minimum 2 detectors (IIRRegimeDetector, SpectralRegimeDetector, BOCDDetector, and optionally HMMRegimeDetector)
- **FR-004**: Ensemble MUST support both majority voting (N-out-of-M threshold) and weighted voting (confidence-weighted scores)
- **FR-005**: Each detector MUST output both regime classification (string label) and confidence score (float 0.0-1.0)
- **FR-006**: Ensemble MUST emit regime change events only when voting threshold is exceeded (configurable, default: majority)
- **FR-007**: System MUST track detector warmup state and exclude non-initialized detectors from voting
- **FR-008**: Ensemble MUST provide query interface for current regime, confidence score, and per-detector votes
- **FR-009**: System MUST log all regime changes with timestamp, old/new regime, confidence, and which detectors voted
- **FR-010**: Ensemble MUST be backward compatible with existing single-detector API (drop-in replacement)
- **FR-011**: System MUST handle detector failures gracefully by removing failed detector from ensemble and continuing with remaining detectors
- **FR-012**: BOCD MUST reset changepoint priors when data gaps > 1 hour are detected (configurable threshold)
- **FR-013**: System MUST allow runtime configuration of detector weights without restart
- **FR-014**: Ensemble MUST support regime classification into minimum 3 categories: trending, mean-reverting, high-volatility

### Key Entities

- **BOCDDetector**: Online changepoint detector tracking run-length distribution, hazard function, and predictive probability. Outputs regime classification and changepoint probability (confidence). Requires initialization period (default: 20 bars).

- **RegimeEnsemble**: Aggregates multiple regime detectors (IIR, Spectral, HMM, BOCD). Maintains detector registry with weights, warmup status, and health state. Outputs consensus regime and aggregated confidence score.

- **RegimeVote**: Represents single detector's regime assessment containing detector ID, regime label, confidence score, and timestamp. Used in ensemble aggregation logic.

- **RegimeChangeEvent**: Event emitted when ensemble confirms regime transition. Contains old regime, new regime, confidence, timestamp, and per-detector votes for audit trail.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: BOCD detector must detect known regime changes (validated on 2020 COVID crash, 2022 crypto winter datasets) within 3 bars of true changepoint with minimum 70% confidence
- **SC-002**: Ensemble voting must reduce false positive rate to below 5% compared to 10-15% for individual detectors (measured on 12-month historical data with labeled regimes)
- **SC-003**: System must maintain O(1) per-bar complexity for BOCD detector (constant memory usage verified across 1 million bar backtests)
- **SC-004**: Ensemble voting must reach consensus within 1 bar of majority detector agreement (< 100ms latency on typical hardware)
- **SC-005**: Backward compatibility must be verified by running 5 existing strategies with zero code changes (only configuration update) and confirming identical API behavior
- **SC-006**: System must handle detector failures gracefully with zero downtime (ensemble continues with N-1 detectors, verified by fault injection testing)
- **SC-007**: Weighted voting must improve F1 score by minimum 10% compared to equal-weight majority voting (measured on out-of-sample regime-labeled data)
