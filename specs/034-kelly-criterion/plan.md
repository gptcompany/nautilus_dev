# Implementation Plan: Kelly Criterion Portfolio Integration

**Feature**: spec-034-kelly-criterion
**Created**: 2026-01-12
**Status**: Draft
**Effort**: 4 hours (as estimated)

---

## Overview

Integrate Kelly Criterion as an **optional final scaling layer** in the existing position sizing pipeline:

```
Signal → SOPS → Giller → [Kelly Scaling] → Risk Limits → Final Position
```

**Target Integration Point**: `strategies/common/adaptive_control/meta_portfolio.py`

**Key Design Decision**: Kelly is applied at **portfolio level** (strategy allocation), not individual trade level. This aligns with academic research (Baker & McHale 2013) and our existing analysis in `docs/research/kelly-vs-giller-analysis.md`.

---

## Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                        MetaPortfolio                                │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐  │
│  │ ThompsonSampler │   │ EnsembleSelector│   │ KellyAllocator  │  │
│  │  (weights)      │──▶│  (selection)    │──▶│  (scaling)      │  │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘  │
│                                                       │            │
│  ┌─────────────────────────────────────────────────────┐          │
│  │              EstimationUncertainty                   │          │
│  │  - Sample size tracking                              │          │
│  │  - Confidence adjustment                             │          │
│  └─────────────────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Strategy returns → ReturnTracker (per strategy)
2. ReturnTracker → EstimationUncertainty (μ, σ², confidence)
3. EstimationUncertainty → KellyAllocator (f* calculation)
4. KellyAllocator → MetaPortfolio.aggregate() (final scaling)
5. Risk Limits → Clipping (hard constraints)
```

---

## File Structure

### New Files

```
strategies/common/adaptive_control/
├── kelly_allocator.py          # NEW: KellyAllocator, EstimationUncertainty, KellyConfig
└── (meta_portfolio.py)         # MODIFY: Integration

tests/strategies/common/adaptive_control/
└── test_kelly_allocator.py     # NEW: Unit tests
```

### Modified Files

```
strategies/common/adaptive_control/
├── meta_portfolio.py           # Add Kelly integration (optional layer)
└── __init__.py                 # Export new classes
```

---

## Detailed Design

### 1. KellyConfig (Dataclass)

```python
@dataclass
class KellyConfig:
    """Configuration for Kelly Criterion integration."""

    enabled: bool = False           # Disabled by default (backward compat)
    beta: float = 0.25              # Fractional Kelly (conservative)
    min_samples: int = 30           # Minimum days before Kelly kicks in
    max_fraction: float = 2.0       # Cap Kelly fraction
    decay: float = 0.99             # Exponential decay for return weighting
    uncertainty_adjustment: bool = True  # Adjust for estimation confidence
    min_allocation: float = 0.01    # Minimum allocation per strategy (1%)
```

### 2. EstimationUncertainty

Quantifies confidence in μ/σ² estimates based on sample size.

```python
class EstimationUncertainty:
    """Quantifies confidence in return estimates."""

    def __init__(
        self,
        min_samples: int = 30,
        max_samples: int = 180,
        min_confidence: float = 0.5,
    ):
        self.min_samples = min_samples
        self.max_samples = max_samples
        self.min_confidence = min_confidence

    def confidence_factor(self, sample_size: int) -> float:
        """
        Returns confidence factor in [min_confidence, 1.0].

        - < min_samples: returns 0.0 (insufficient data)
        - = min_samples: returns min_confidence
        - >= max_samples: returns 1.0
        - Between: linear interpolation
        """
        if sample_size < self.min_samples:
            return 0.0  # Insufficient data

        if sample_size >= self.max_samples:
            return 1.0  # Full confidence

        # Linear interpolation
        progress = (sample_size - self.min_samples) / (self.max_samples - self.min_samples)
        return self.min_confidence + progress * (1.0 - self.min_confidence)
```

### 3. KellyAllocator

Core Kelly fraction calculation with uncertainty adjustment.

```python
class KellyAllocator:
    """
    Calculates Kelly-optimal fractions for strategy allocation.

    Pipeline: μ/σ² → f* → fractional β → uncertainty adjustment → final
    """

    def __init__(self, config: KellyConfig):
        self.config = config
        self.uncertainty = EstimationUncertainty(
            min_samples=config.min_samples,
            max_samples=config.min_samples * 6,  # 180 days default
        )
        # Per-strategy return tracking
        self._returns: dict[str, deque] = {}

    def update_return(self, strategy_id: str, daily_return: float) -> None:
        """Track strategy return for Kelly estimation."""
        if strategy_id not in self._returns:
            self._returns[strategy_id] = deque(maxlen=self.config.min_samples * 6)
        self._returns[strategy_id].append(daily_return)

    def calculate_fraction(self, strategy_id: str) -> tuple[float, dict]:
        """
        Calculate Kelly fraction for a strategy.

        Returns:
            fraction: Final Kelly-adjusted fraction
            audit: Dict with μ, σ², f*, confidence, etc.
        """
        returns = self._returns.get(strategy_id, [])
        sample_size = len(returns)

        # Insufficient data check
        if sample_size < self.config.min_samples:
            return 1.0, {
                "status": "insufficient_data",
                "sample_size": sample_size,
                "min_required": self.config.min_samples,
            }

        # Calculate μ and σ² with exponential weighting
        weights = np.array([self.config.decay ** i for i in range(sample_size)][::-1])
        weights /= weights.sum()

        returns_arr = np.array(returns)
        mu = np.average(returns_arr, weights=weights)
        sigma_sq = np.average((returns_arr - mu) ** 2, weights=weights)

        # Handle edge cases
        if mu <= 0:
            # Negative expected return → don't allocate
            return 0.0, {
                "status": "negative_mu",
                "mu": mu,
                "sigma_sq": sigma_sq,
            }

        if sigma_sq < 1e-10:
            # Near-zero variance → cap Kelly
            f_star = self.config.max_fraction
        else:
            f_star = mu / sigma_sq

        # Cap Kelly fraction
        f_star = min(f_star, self.config.max_fraction)

        # Apply fractional Kelly
        f_fractional = self.config.beta * f_star

        # Uncertainty adjustment
        confidence = 1.0
        if self.config.uncertainty_adjustment:
            confidence = self.uncertainty.confidence_factor(sample_size)
            f_final = f_fractional * confidence
        else:
            f_final = f_fractional

        return f_final, {
            "status": "ok",
            "mu": mu,
            "sigma_sq": sigma_sq,
            "f_star": f_star,
            "f_fractional": f_fractional,
            "f_final": f_final,
            "confidence": confidence,
            "sample_size": sample_size,
        }

    def allocate(self, strategy_ids: list[str]) -> dict[str, float]:
        """
        Calculate normalized Kelly allocations for all strategies.

        Returns dict mapping strategy_id → allocation fraction (sums to 1.0 or less)
        """
        fractions = {}
        audits = {}

        for sid in strategy_ids:
            f, audit = self.calculate_fraction(sid)
            fractions[sid] = f
            audits[sid] = audit

        # Handle all-negative-mu case: use min_allocation for all strategies
        if all(f == 0.0 for f in fractions.values()) and strategy_ids:
            logger.warning("All strategies have negative μ - using min_allocation fallback")
            fractions = {k: self.config.min_allocation for k in strategy_ids}

        # Normalize if sum > 1.0
        total = sum(fractions.values())
        if total > 1.0:
            fractions = {k: v / total for k, v in fractions.items()}

        # Log audit trail
        logger.debug(f"Kelly allocations: {fractions}")
        logger.debug(f"Kelly audits: {audits}")

        return fractions
```

### 4. MetaPortfolio Integration

Modify `MetaPortfolio.__init__` to accept optional `kelly_config`:

```python
class MetaPortfolio:
    def __init__(
        self,
        base_size: float = 1.0,
        giller_exponent: float = 0.5,
        adaptation_rate: float = 0.1,
        min_weight: float = 0.05,
        max_weight: float = 0.40,
        deactivation_threshold: float = 0.01,
        kelly_config: KellyConfig | None = None,  # NEW
    ):
        # ... existing init ...

        # Kelly integration (optional)
        self._kelly_config = kelly_config or KellyConfig(enabled=False)
        self._kelly_allocator = None
        if self._kelly_config.enabled:
            self._kelly_allocator = KellyAllocator(self._kelly_config)
```

Modify `MetaPortfolio.update_pnl` to track returns:

```python
def update_pnl(self, strategy_id: str, pnl: float, ...) -> ...:
    # ... existing logic ...

    # Track returns for Kelly (NEW)
    if self._kelly_allocator and strategy_id in self._systems:
        state = self._systems[strategy_id]
        if state.equity > 0:
            daily_return = pnl / state.equity
            self._kelly_allocator.update_return(strategy_id, daily_return)
```

Modify `MetaPortfolio.aggregate` to apply Kelly scaling:

```python
def aggregate(self, signals: dict[str, float]) -> dict[str, float]:
    """
    Aggregate strategy signals with optional Kelly scaling.

    Pipeline:
    1. Thompson sampling weights
    2. Ensemble selection
    3. Kelly scaling (if enabled)  # NEW
    4. Risk limits
    """
    # ... existing ensemble/thompson logic ...

    # Apply Kelly scaling if enabled
    if self._kelly_allocator and self._kelly_config.enabled:
        kelly_fractions = self._kelly_allocator.allocate(list(signals.keys()))

        for sid in weighted_signals:
            if sid in kelly_fractions:
                weighted_signals[sid] *= kelly_fractions[sid]

        logger.debug(f"Applied Kelly scaling: {kelly_fractions}")

    # ... existing risk limits logic ...
```

---

## Test Plan

### Unit Tests (test_kelly_allocator.py)

| Test | Description | Priority |
|------|-------------|----------|
| `test_kelly_fraction_calculation` | f* = μ/σ² with known values | P1 |
| `test_fractional_kelly_scaling` | f_actual = β × f* | P1 |
| `test_normalization_over_100pct` | Sum > 100% → normalize | P1 |
| `test_negative_mu_returns_zero` | μ < 0 → f = 0 | P1 |
| `test_near_zero_variance_cap` | σ² ≈ 0 → f capped | P1 |
| `test_insufficient_samples_fallback` | < min_samples → skip Kelly | P1 |
| `test_uncertainty_adjustment` | Fewer samples → more conservative | P2 |
| `test_exponential_decay_weighting` | Recent returns weighted more | P2 |
| `test_kelly_disabled_passthrough` | enabled=False → no effect | P1 |

### Integration Tests (test_meta_portfolio.py additions)

| Test | Description | Priority |
|------|-------------|----------|
| `test_kelly_integration_disabled` | Backward compatibility | P1 |
| `test_kelly_integration_enabled` | Kelly modifies allocations | P1 |
| `test_kelly_with_thompson_sampling` | Combined pipeline | P2 |
| `test_kelly_respects_risk_limits` | Hard constraints honored | P1 |

### Backtest Validation

```python
# Compare Sharpe, drawdown, growth rate
# Variant A: Kelly disabled (baseline)
# Variant B: Kelly β=0.25
# Variant C: Kelly β=0.50

# Success criteria (from spec):
# - SC-001: 5-15% improvement in geometric growth rate
# - SC-002: Max drawdown ≤ 1.5x baseline
# - SC-003: Calculation < 1ms for 20 strategies
```

---

## Risk Mitigation

### Risk 1: Estimation Error

**Risk**: Noisy μ/σ² estimates lead to poor allocations.

**Mitigation**:
- Fractional Kelly (β=0.25 default)
- Uncertainty adjustment based on sample size
- min_samples threshold (30 days default)
- Exponential decay on returns (recent data weighted more)

### Risk 2: Backward Compatibility

**Risk**: Existing strategies break after integration.

**Mitigation**:
- `enabled=False` by default
- All changes are additive (no removal of existing logic)
- Explicit fallback paths for insufficient data
- Unit test for exact baseline equivalence when disabled

### Risk 3: Numerical Instability

**Risk**: Division by near-zero σ² causes extreme allocations.

**Mitigation**:
- `max_fraction` cap (default 2.0)
- σ² floor check (< 1e-10 → use max_fraction)
- Normalization when allocations sum > 100%

---

## Dependencies

### Internal

- `meta_portfolio.py` - Integration point
- `sops_sizing.py` - Existing SOPS+Giller pipeline (unchanged)
- `ensemble_selection.py` - Ensemble selector (called before Kelly)

### External

- `numpy` - Array operations, statistics
- `msgspec` - Dataclass serialization (if needed)

### NautilusTrader

- No direct NT dependencies for Kelly module
- Integration through MetaPortfolio which is NT-agnostic

---

## Implementation Order

1. **Create `kelly_allocator.py`** (1.5h)
   - KellyConfig dataclass
   - EstimationUncertainty class
   - KellyAllocator class
   - Unit tests

2. **Integrate into `meta_portfolio.py`** (1h)
   - Add kelly_config parameter
   - Track returns in update_pnl
   - Apply scaling in aggregate
   - Integration tests

3. **Documentation & Validation** (1h)
   - Update docstrings
   - Run full test suite
   - Backtest validation (if time permits)

4. **Code Review & Polish** (0.5h)
   - Address review feedback
   - Final cleanup

---

## Success Criteria Mapping

| Spec Criteria | Implementation Check |
|---------------|---------------------|
| SC-001: 5-15% growth improvement | Backtest comparison |
| SC-002: DD ≤ 1.5x baseline | Backtest comparison |
| SC-003: <1ms for 20 strategies | Performance test |
| SC-004: Fallback when data insufficient | Unit test |
| SC-005: Identical when disabled | Unit test |
| SC-006: 30-50% reduction when <60 days | Uncertainty adjustment test |

---

## Open Questions

1. **Q**: Should Kelly recalculate on every `aggregate()` call or on a schedule?
   **A**: Every call is fine - μ/σ² are cached, calculation is O(n) where n = sample_size.

2. **Q**: Should we persist return history across restarts?
   **A**: Yes, add to `save_state()`/`load_state()` methods in MetaPortfolio.

3. **Q**: Should uncertainty use linear or non-linear interpolation?
   **A**: Start with linear (KISS). Can revisit if needed.

---

## References

- `docs/research/kelly-vs-giller-analysis.md` - Detailed analysis
- `specs/034-kelly-criterion/spec.md` - Requirements
- Baker & McHale 2013 - Kelly with parameter uncertainty
- Giller 2020 - Power-law sizing
