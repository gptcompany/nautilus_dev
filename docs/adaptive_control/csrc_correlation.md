# CSRC: Correlation-Aware Strategy Allocation

**Spec Reference**: `specs/031-csrc-correlation/`

## Overview

CSRC (Correlation-aware Strategy Reweighting and Control) prevents over-allocation to correlated strategies by adding a covariance penalty to the particle portfolio fitness function.

**Problem**: Traditional portfolio allocation treats strategies independently, leading to concentration risk when strategies are correlated.

**Solution**: Online correlation tracking with covariance-penalized fitness:

```
fitness = portfolio_return - lambda * covariance_penalty
```

## Quick Start

```python
from strategies.common.adaptive_control import (
    ParticlePortfolio,
    OnlineCorrelationMatrix,
    CorrelationMetrics,
)

# Create correlation tracker
strategies = ["momentum_a", "momentum_b", "mean_reversion"]
tracker = OnlineCorrelationMatrix(
    strategies=strategies,
    decay=0.99,      # EMA decay for correlation updates
    shrinkage=0.1,   # Ledoit-Wolf shrinkage toward identity
    min_samples=30,  # Minimum samples before correlation is valid
)

# Create portfolio with CSRC enabled
portfolio = ParticlePortfolio(
    strategies=strategies,
    n_particles=100,
    correlation_tracker=tracker,
    lambda_penalty=1.0,  # Covariance penalty strength
)

# Update with returns
returns = {"momentum_a": 0.01, "momentum_b": 0.012, "mean_reversion": -0.005}
state = portfolio.update(returns)

# Access correlation metrics
if state.correlation_metrics:
    print(f"Effective N: {state.correlation_metrics.effective_n_strategies:.2f}")
    print(f"Max correlation: {state.correlation_metrics.max_pairwise_correlation:.2f}")
    print(f"Herfindahl: {state.correlation_metrics.herfindahl_index:.3f}")
```

## Core Components

### OnlineCorrelationMatrix

Tracks pairwise correlations using O(N^2) online updates with EMA weighting.

```python
tracker = OnlineCorrelationMatrix(
    strategies=["A", "B", "C"],
    decay=0.99,       # Higher = slower adaptation
    shrinkage=0.1,    # Higher = more regularization
    min_samples=30,   # Warmup period
)

# Update with each return observation
tracker.update({"A": 0.01, "B": 0.02, "C": -0.01})

# Get correlation matrix (N x N numpy array)
corr_matrix = tracker.get_correlation_matrix()

# Get pairwise correlation
corr_ab = tracker.get_pairwise_correlation("A", "B")

# Get metrics
metrics = tracker.get_metrics()
```

### CorrelationMetrics

Observability metrics returned with each portfolio update:

| Metric | Description | Interpretation |
|--------|-------------|----------------|
| `herfindahl_index` | Sum of squared weights | 0.33 = equal (3 strats), 1.0 = concentrated |
| `effective_n_strategies` | 1/Herfindahl | How many strategies are "active" |
| `max_pairwise_correlation` | Highest correlation | Risk of concentration |
| `avg_correlation` | Mean off-diagonal correlation | Overall diversification |

### calculate_covariance_penalty

The penalty function used in fitness calculation:

```python
from strategies.common.adaptive_control import calculate_covariance_penalty

penalty = calculate_covariance_penalty(
    weights={"A": 0.5, "B": 0.3, "C": 0.2},
    corr_matrix=corr_matrix,
    strategy_indices=tracker.strategy_indices,
)
# penalty = sum_i sum_j (w_i * w_j * corr_ij) for i != j
```

## Lambda Sensitivity

The `lambda_penalty` parameter controls diversification pressure:

| Lambda | Effect | Use Case |
|--------|--------|----------|
| 0.0 | No penalty (baseline) | Compare with/without CSRC |
| 0.5 | Mild diversification | Low correlation environment |
| 1.0 | Balanced (default) | General use |
| 2.0 | Strong diversification | High correlation, risk averse |
| 5.0 | Aggressive diversification | Very correlated strategies |

**Example: Testing lambda sensitivity**

```python
for lambda_val in [0.0, 1.0, 2.0]:
    portfolio = ParticlePortfolio(
        strategies=strategies,
        correlation_tracker=tracker,
        lambda_penalty=lambda_val,
    )
    # Run simulation...
    print(f"Lambda={lambda_val}: Effective N = {state.correlation_metrics.effective_n_strategies}")
```

## Integration with BayesianEnsemble

```python
from strategies.common.adaptive_control import BayesianEnsemble, OnlineCorrelationMatrix

ensemble = BayesianEnsemble(
    strategies=["strat_a", "strat_b", "strat_c"],
    n_particles=50,
)

# Add correlation tracker to internal portfolio
tracker = OnlineCorrelationMatrix(strategies=ensemble.strategies, min_samples=20)
ensemble.particle_portfolio.correlation_tracker = tracker
ensemble.particle_portfolio.lambda_penalty = 1.0

# Use ensemble as normal
state = ensemble.update(returns)
weights, selected = ensemble.get_allocation()
```

## Audit Trail Integration

CSRC emits `SYS_CORRELATION_UPDATE` events when correlation metrics change significantly:

```python
from strategies.common.audit import AuditEventEmitter, AuditEventType

# Events are emitted automatically when using audit_emitter
# Event payload includes:
# - herfindahl_index
# - effective_n_strategies
# - max_pairwise_correlation
# - avg_correlation
```

## Performance

- **Update latency**: < 1ms for 10-20 strategies
- **Memory**: O(N^2) for correlation matrix
- **Complexity**: O(N^2) per update

Benchmarked on typical hardware:
- 10 strategies: ~0.3ms per update
- 20 strategies: ~0.8ms per update

## Edge Cases

### Singular/Near-Singular Matrices

Handled via Ledoit-Wolf shrinkage + epsilon regularization:

```python
tracker = OnlineCorrelationMatrix(
    strategies=strategies,
    shrinkage=0.1,  # Pulls toward identity matrix
)
# Diagonal has epsilon (1e-6) added for numerical stability
```

### Zero Variance Strategy

If a strategy has zero variance (constant returns), its correlations are set to 0:

```python
# Strategy with constant returns
returns = {"A": 0.01, "B": 0.0, "C": -0.01}  # B has zero variance
# corr(A, B) = 0, corr(B, C) = 0
```

### All Strategies Correlated

When all strategies are highly correlated, CSRC:
1. Detects high correlation (max_pairwise > 0.8)
2. Applies penalty proportional to correlation
3. Portfolio weights remain valid (sum to 1, all positive)

### Two-Strategy Portfolio

Works correctly with N=2:

```python
tracker = OnlineCorrelationMatrix(strategies=["A", "B"])
# 2x2 correlation matrix with proper regularization
```

## Success Criteria (from Spec)

| Criterion | Target | Status |
|-----------|--------|--------|
| SC-001: Concentration reduction | 20% for correlated | Verified |
| SC-002: Update latency | < 1ms for 10 strategies | Verified |
| SC-006: No regression | Uncorrelated within 5% | Verified |

## References

- **Spec**: `specs/031-csrc-correlation/spec.md`
- **Plan**: `specs/031-csrc-correlation/plan.md`
- **Research**: Ledoit & Wolf (2004) "Honey, I Shrunk the Sample Covariance Matrix"
- **Tests**: `tests/unit/test_correlation_tracker.py`, `tests/integration/test_csrc_walk_forward.py`
