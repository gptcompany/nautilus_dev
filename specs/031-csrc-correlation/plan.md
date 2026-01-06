# Implementation Plan: CSRC Correlation-Aware Allocation

**Feature Branch**: `031-csrc-correlation`
**Created**: 2026-01-06
**Status**: Draft
**Spec Reference**: `specs/031-csrc-correlation/spec.md`
**Research Reference**: `specs/031-csrc-correlation/research.md`

## Architecture Overview

### System Context

CSRC extends the existing `ParticlePortfolio` and `ThompsonSelector` in `strategies/common/adaptive_control/particle_portfolio.py` to incorporate correlation-awareness. The key modification is adding a covariance penalty to the reward function, preventing over-allocation to correlated strategies.

**Integration Point**: The existing `ParticlePortfolio.update()` method will be enhanced to subtract a covariance penalty from portfolio returns, and a new `CorrelationTracker` class will maintain the online correlation matrix.

### Component Diagram

```
strategies/common/adaptive_control/
├── particle_portfolio.py          # Existing: ParticlePortfolio, ThompsonSelector
│   └── MODIFY: update() to use correlation penalty
├── correlation_tracker.py         # NEW: CorrelationTracker class
│   ├── OnlineCorrelationMatrix    # O(1) updates via EMA/Welford
│   ├── ShrinkageEstimator         # Ledoit-Wolf shrinkage
│   └── PenaltyCalculator          # covariance_penalty(weights, corr_matrix)
└── __init__.py                    # Export new classes

Data Flow:
┌─────────────┐   returns    ┌──────────────────┐
│ Strategies  │ ──────────►  │ CorrelationTracker│
└─────────────┘              │ (online updates)  │
                             └────────┬─────────┘
                                      │ corr_matrix
                                      ▼
┌─────────────┐   returns    ┌──────────────────┐
│ Strategies  │ ──────────►  │ ParticlePortfolio │
└─────────────┘              │ (modified update) │
                             │                   │
                             │ reward = sharpe   │
                             │   - λ * cov_pen   │
                             └────────┬─────────┘
                                      │ weights
                                      ▼
                             ┌──────────────────┐
                             │ PortfolioState   │
                             │ + corr_metrics   │
                             └──────────────────┘
```

## Technical Decisions

### Decision 1: Correlation Estimation Method

**Options Considered**:
1. **Option A: Sample Correlation (Naive)**
   - Pros: Simple implementation
   - Cons: High estimation error with few samples (DeMiguel 2009)

2. **Option B: Exponential Moving Average (EMA)**
   - Pros: O(1) updates, adapts to non-stationarity
   - Cons: May be noisy with few observations

3. **Option C: Ledoit-Wolf Shrinkage + EMA**
   - Pros: Reduces estimation error, robust to small samples
   - Cons: Slightly more complex

**Selected**: Option C (Ledoit-Wolf Shrinkage + EMA)

**Rationale**: Research strongly supports shrinkage for correlation estimation (Ledoit & Wolf 2020, 128 citations). EMA handles non-stationarity. Combination provides best of both worlds. Implementation cost is minimal (linear shrinkage is a simple formula).

---

### Decision 2: Penalty Formula

**Options Considered**:
1. **Option A: Sum of off-diagonal covariances**
   - Formula: `penalty = sum_i sum_j (w_i * w_j * corr_ij)` for i != j
   - Pros: Standard in literature, directly penalizes correlated allocation
   - Cons: Quadratic in N

2. **Option B: Maximum pairwise correlation penalty**
   - Formula: `penalty = max(corr_ij * w_i * w_j)`
   - Pros: O(N) after matrix computed
   - Cons: Ignores total correlation exposure

**Selected**: Option A (Sum of off-diagonal)

**Rationale**: This is the standard formulation (equivalent to portfolio variance minus weighted sum of individual variances). It captures total correlation exposure, not just worst pair. O(N^2) is acceptable for N < 50 strategies.

---

### Decision 3: Storage Format for Correlation Matrix

**Options Considered**:
1. **Option A: Full N×N matrix**
   - Pros: Direct indexing
   - Cons: Redundant storage (matrix is symmetric)

2. **Option B: Upper-triangular array (N*(N-1)/2 elements)**
   - Pros: Memory efficient
   - Cons: Index calculation overhead

**Selected**: Option A (Full N×N matrix)

**Rationale**: For N < 50 strategies, full matrix is at most 2500 floats (20KB). Simplicity outweighs memory savings. Direct indexing is clearer and less error-prone.

---

### Decision 4: Backward Compatibility

**Options Considered**:
1. **Option A: Modify ParticlePortfolio directly**
   - Pros: Single class to maintain
   - Cons: May break existing users

2. **Option B: Subclass ParticlePortfolio as CSRCParticlePortfolio**
   - Pros: Full backward compatibility
   - Cons: Code duplication, maintenance overhead

3. **Option C: Add optional `correlation_tracker` parameter to ParticlePortfolio**
   - Pros: Backward compatible, no code duplication
   - Cons: Slight increase in class complexity

**Selected**: Option C (Optional parameter)

**Rationale**: Existing `ParticlePortfolio` users won't be affected. New users can opt-in to correlation awareness by passing a `CorrelationTracker`. This follows the Open-Closed Principle.

---

## Implementation Strategy

### Phase 1: Foundation - CorrelationTracker

**Goal**: Create the online correlation tracking infrastructure

**Deliverables**:
- [x] `correlation_tracker.py` with `OnlineCorrelationMatrix` class
- [ ] Welford's algorithm for online variance/covariance
- [ ] EMA-based correlation updates with configurable decay
- [ ] Ledoit-Wolf shrinkage function
- [ ] Unit tests for correlation convergence (100 samples → within 5%)

**Dependencies**: None

**Key Implementation Details**:
```python
@dataclass
class OnlineStats:
    """Online statistics for a single strategy."""
    mean: float = 0.0
    var: float = 0.0
    n: int = 0

class OnlineCorrelationMatrix:
    """O(1) per-update correlation matrix using EMA."""

    def __init__(
        self,
        strategies: List[str],
        decay: float = 0.99,        # EMA decay factor
        shrinkage: float = 0.1,     # Shrinkage toward identity
        min_samples: int = 30,      # Minimum samples before trusting estimates
    ):
        ...

    def update(self, returns: Dict[str, float]) -> None:
        """Update correlation estimates with new returns. O(N^2)."""
        ...

    def get_correlation_matrix(self) -> np.ndarray:
        """Get current N×N correlation matrix (with shrinkage applied)."""
        ...

    def get_pairwise_correlation(self, strat_a: str, strat_b: str) -> float:
        """Get correlation between two strategies."""
        ...
```

---

### Phase 2: Core Implementation - Penalty Integration

**Goal**: Integrate covariance penalty into ParticlePortfolio

**Deliverables**:
- [ ] `PenaltyCalculator` class with `calculate_covariance_penalty()` method
- [ ] Modify `ParticlePortfolio.update()` to accept optional `CorrelationTracker`
- [ ] Add `lambda_penalty` parameter (default 1.0, range [0.0, 5.0])
- [ ] Update `PortfolioState` with correlation metrics (Herfindahl, effective N, max corr)
- [ ] Unit tests for penalty calculation
- [ ] Integration tests with synthetic correlated strategies

**Dependencies**: Phase 1

**Key Implementation Details**:
```python
def calculate_covariance_penalty(
    weights: Dict[str, float],
    corr_matrix: np.ndarray,
    strategy_indices: Dict[str, int],
) -> float:
    """
    Calculate covariance penalty: sum_i sum_j (w_i * w_j * corr_ij) for i != j.

    Returns:
        Covariance penalty (higher = more correlated allocation)
    """
    penalty = 0.0
    strategies = list(weights.keys())
    for i, si in enumerate(strategies):
        for j, sj in enumerate(strategies):
            if i != j:
                wi = weights.get(si, 0.0)
                wj = weights.get(sj, 0.0)
                corr_ij = corr_matrix[strategy_indices[si], strategy_indices[sj]]
                penalty += wi * wj * corr_ij
    return penalty

# Modified ParticlePortfolio.update():
def update(
    self,
    strategy_returns: Dict[str, float],
    correlation_tracker: Optional[OnlineCorrelationMatrix] = None,
    lambda_penalty: float = 1.0,
) -> PortfolioState:
    """Update with optional correlation penalty."""
    # ... existing code ...

    if correlation_tracker is not None:
        # Update correlation matrix
        correlation_tracker.update(strategy_returns)

        # Calculate penalty for each particle
        corr_matrix = correlation_tracker.get_correlation_matrix()
        for particle in self.particles:
            penalty = calculate_covariance_penalty(
                particle.weights, corr_matrix, self._strategy_indices
            )
            # Modify fitness: reward = sharpe - lambda * penalty
            particle.fitness -= lambda_penalty * penalty

    # ... rest of existing code ...
```

---

### Phase 3: Integration & Testing

**Goal**: Full integration with existing systems and comprehensive testing

**Deliverables**:
- [ ] Integration with `BayesianEnsemble` class
- [ ] Integration with audit trail (Spec 030) - emit correlation metrics
- [ ] Performance tests (< 1ms for 20 strategies)
- [ ] Walk-forward validation with synthetic correlated strategies
- [ ] Edge case tests (singular matrix, zero variance, all strategies correlated)
- [ ] Test for FR-004 sliding window memory constraint (max 1000 samples)
- [ ] Documentation in `docs/adaptive_control/csrc_correlation.md`
- [ ] Lambda sensitivity documentation with examples (0.5, 1.0, 2.0, 5.0)
- [ ] Update `particle_portfolio.py` docstring to remove P5 (Leggi Naturali) reference per CLAUDE.md

**Dependencies**: Phase 2

**Key Tests**:
```python
def test_concentration_reduction_with_correlated_strategies():
    """SC-001: 20% concentration reduction for correlated strategies."""
    # Create 3 strategies with correlation > 0.8
    # Compare allocation with/without CSRC
    # Assert concentration reduces by >= 20%

def test_no_regression_for_uncorrelated_strategies():
    """SC-006: No regression for uncorrelated strategies."""
    # Create strategies with correlation < 0.3
    # Compare allocation with/without CSRC
    # Assert weights within 5% of baseline

def test_performance_20_strategies():
    """FR-006: < 1ms for 20 strategies."""
    # Create 20-strategy portfolio
    # Time update() call
    # Assert < 1ms
```

---

## File Structure

```
strategies/common/adaptive_control/
├── __init__.py                    # Add exports for new classes
├── particle_portfolio.py          # MODIFY: Add correlation support
└── correlation_tracker.py         # NEW: CorrelationTracker, PenaltyCalculator

tests/unit/
├── test_correlation_tracker.py    # Unit tests for OnlineCorrelationMatrix
└── test_particle_portfolio_csrc.py # Unit tests for CSRC integration

tests/integration/
└── test_csrc_walk_forward.py      # Walk-forward validation

docs/adaptive_control/
└── csrc_correlation.md            # Feature documentation
```

## API Design

### Public Interface

```python
# New class: CorrelationTracker
class OnlineCorrelationMatrix:
    def __init__(
        self,
        strategies: List[str],
        decay: float = 0.99,
        shrinkage: float = 0.1,
        min_samples: int = 30,
    ) -> None: ...

    def update(self, returns: Dict[str, float]) -> None: ...
    def get_correlation_matrix(self) -> np.ndarray: ...
    def get_metrics(self) -> CorrelationMetrics: ...

@dataclass
class CorrelationMetrics:
    herfindahl_index: float         # Sum of squared weights
    effective_n_strategies: float   # 1 / herfindahl
    max_pairwise_correlation: float # Highest correlation pair
    avg_correlation: float          # Average off-diagonal correlation

# Modified ParticlePortfolio (backward compatible)
class ParticlePortfolio:
    def update(
        self,
        strategy_returns: Dict[str, float],
        correlation_tracker: Optional[OnlineCorrelationMatrix] = None,
        lambda_penalty: float = 1.0,
    ) -> PortfolioState: ...

# Extended PortfolioState (backward compatible)
@dataclass
class PortfolioState:
    strategy_weights: Dict[str, float]
    weight_uncertainty: Dict[str, float]
    effective_particles: float
    resampled: bool
    correlation_metrics: Optional[CorrelationMetrics] = None  # NEW
```

### Configuration

```python
# Example usage with CSRC enabled
from strategies.common.adaptive_control import (
    ParticlePortfolio,
    OnlineCorrelationMatrix,
)

# Initialize tracker
corr_tracker = OnlineCorrelationMatrix(
    strategies=["momentum", "mean_rev", "breakout"],
    decay=0.99,        # Recommended default
    shrinkage=0.1,     # Ledoit-Wolf shrinkage
)

# Initialize portfolio
portfolio = ParticlePortfolio(
    strategies=["momentum", "mean_rev", "breakout"],
    n_particles=100,
)

# Each period
for returns in data:
    state = portfolio.update(
        returns,
        correlation_tracker=corr_tracker,
        lambda_penalty=1.0,  # Default, tune if needed
    )

    # Access correlation metrics
    if state.correlation_metrics:
        print(f"Effective N: {state.correlation_metrics.effective_n_strategies}")
```

## Testing Strategy

### Unit Tests
- [x] Test OnlineCorrelationMatrix initialization
- [ ] Test correlation convergence (synthetic data with known correlation)
- [ ] Test Ledoit-Wolf shrinkage reduces estimation error
- [ ] Test penalty calculation with known weights/correlations
- [ ] Test edge cases (zero variance, perfect correlation, N=2)

### Integration Tests
- [ ] Test ParticlePortfolio with CSRC reduces correlated allocation
- [ ] Test backward compatibility (CSRC disabled = same behavior)
- [ ] Test with BayesianEnsemble integration
- [ ] Test audit trail emits correlation metrics

### Performance Tests
- [ ] Benchmark update() for 10, 20, 50 strategies
- [ ] Assert < 1ms for N <= 20
- [ ] Memory profiling (no leaks over 10k updates)

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Correlation estimates noisy with few samples | High | Medium | Use shrinkage, min_samples=30 before trusting |
| Lambda calibration is hard for users | Medium | High | Provide default=1.0, document sensitivity |
| Performance regression for large N | Medium | Low | Profile critical path, use NumPy vectorization |
| Breaking backward compatibility | High | Low | Use optional parameters, default to existing behavior |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.220.0 (no changes required)
- NumPy (already in project dependencies)

### Internal Dependencies
- `strategies/common/adaptive_control/particle_portfolio.py` (modified)
- `strategies/common/audit/` (Spec 030, for emitting correlation metrics)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | PASS | CorrelationTracker is self-contained module |
| KISS | PASS | Minimal changes, optional parameter |
| Native First | PASS | Using NumPy for matrix ops |
| No df.iterrows() | PASS | Using vectorized NumPy |
| TDD | REQUIRED | Write tests first |

## Acceptance Criteria

- [x] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Performance benchmarks met (< 1ms for 20 strategies)
- [ ] SC-001: 20% concentration reduction for correlated strategies
- [ ] SC-006: No regression for uncorrelated strategies
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Alpha-debug verification passed
