# Future Enhancements Index

> **Philosophy**: Add complexity ONLY when current approach shows problems in out-of-sample testing.
>
> **ROI Formula**: `ROI = (Benefit × Pillar_Alignment) / Complexity`
> - ROI > 5 = MVP (implement now)
> - ROI 2-5 = KEEP (implement when triggered)
> - ROI 1-2 = CONDITIONAL (implement only if specific trigger observed)
> - ROI < 1 = REMOVED (not worth complexity)

## The 4 Pillars

| Pillar | Principle | FE Implication |
|--------|-----------|----------------|
| **P1** | Probabilistic | Must handle uncertainty, no determinism |
| **P2** | Non-linear (Power Laws) | Must scale non-linearly (fat tails, rare events) |
| **P3** | Non-parametric | No distribution assumptions (no Gaussian) |
| **P4** | Scale-invariant | Must work across multiple timeframes |

---

## MVP - Implement Immediately (ROI > 5)

These enhancements are critical and should be part of core functionality, not future work.

| ID | Spec | Enhancement | ROI | Pillars | Status |
|----|------|-------------|:---:|---------|--------|
| FE-005 | 010 | Overfitting Detection | **10.0** | P1+P2+P3+P4 | **Implemented** (2026-01-11) |
| FE-003 | 007 | Probabilistic Sharpe Ratio | **7.5** | P1+P2+P3 | **Implemented** (2026-01-11) |
| FE-003 | 009 | Ensemble Strategy Selection | **7.5** | P1+P2+P4 | **Implemented** (2026-01-11) |
| FE-004 | 007 | Transaction Cost Modeling | **5.0** | P2+P4 | **Implemented** (2026-01-11) |

---

## KEEP - Implement When Triggered (ROI 2-5)

| ID | Spec | Enhancement | ROI | Pillars | Trigger | Status |
|----|------|-------------|:---:|---------|---------|--------|
| FE-001 | 009 | Adaptive Mutation Rate Control | **4.0** | P1+P3 | Fixed rates suboptimal | Documented |
| FE-004 | 020 | Profit Factor Decay Analysis | **4.0** | P2+P4 | Strategies fail after N months | Documented |
| FE-003 | 031 | Tail Dependence (Copulas) | **3.75** | P1+P2+P3 | Joint extreme movements observed | Documented |
| FE-002 | 020 | White's Reality Check | **3.3** | P1+P3 | Testing >20 variants | Documented |
| FE-002 | 031 | Power-Law Penalty Scaling | **3.0** | P2 | Linear penalties insufficient | Documented |
| FE-001 | 006 | Fitness Sharing (Niching) | **2.7** | P1+P3 | Population convergence | Documented |
| FE-002 | 007 | Walk-Forward During Evolution | **2.4** | P1+P3+P4 | Single-period validation insufficient | Documented |

---

## CONDITIONAL - Only If Specific Trigger (ROI 1-2)

| ID | Spec | Enhancement | ROI | Trigger Condition |
|----|------|-------------|:---:|-------------------|
| FE-003 | 020 | Combinatorial Purged CV (CPCV) | 1.6 | >100 strategy variants tested |
| FE-004 | 006 | Lineage Pruning | 1.5 | Old lineages dominating population |
| FE-004 | 009 | Novelty Search | 1.5 | Exploitation-only search visible |
| FE-002 | 010 | Mutation Success Attribution | 1.5 | Need to debug mutation effectiveness |
| FE-001 | 020 | Anchored vs Rolling WF | 1.0 | Rolling windows show instability |
| FE-001 | 031 | Kendall Correlation | 1.0 | Non-monotonic relationships detected |
| FE-001 | 007 | Multi-Objective Optimization | 1.0 | Explicit Sharpe vs Drawdown trade-offs needed |

---

## REMOVED - Not Worth Complexity (ROI < 1)

These enhancements were analyzed and rejected due to low ROI or no pillar alignment.

| ID | Spec | Enhancement | ROI | Reason |
|----|------|-------------|:---:|--------|
| FE-003 | 008 | Feature Engineering Helpers | 0.75 | No pillar alignment, Rust indicators sufficient |
| FE-001 | 010 | Population Diversity Heatmap | 0.67 | Nice-to-have, not actionable |
| FE-002 | 006 | Island Model (Parallel Populations) | 0.6 | Complexity > benefit, mutation diversity sufficient |
| FE-001 | 008 | Multiple Evolvable Blocks | 0.5 | No pillar alignment, single block sufficient |
| FE-002 | 008 | State Machine Templates | 0.4 | No pillar alignment, extreme complexity |
| FE-002 | 009 | Prompt Engineering Evolution | 0.4 | Meta-meta-optimization (YAGNI) |
| FE-004 | 010 | Lineage Tree Visualization | 0.33 | No pillar alignment, not actionable |
| FE-003 | 010 | Fitness Landscape Visualization | 0.25 | PCA on strategies not meaningful |

---

## DUPLICATES/EXISTS - Removed from Index

| ID | Spec | Enhancement | Status |
|----|------|-------------|--------|
| FE-003 | 006 | Adaptive Mutation Rates | Duplicate of 009-FE-001 |
| FE-004 | 008 | Risk-Aware Position Sizing | Already in `strategies/common/adaptive_control/` |

---

## MVP Implementation Details

### 010-FE-005: Overfitting Detection (ROI 10.0)

**Purpose**: Real-time alerts for train/test performance divergence

**Implementation**:
```python
class OverfittingDetector:
    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold  # train_sharpe / test_sharpe ratio

    def check(self, train_sharpe: float, test_sharpe: float) -> bool:
        if test_sharpe <= 0:
            return True  # Definite overfit
        ratio = train_sharpe / test_sharpe
        return ratio > self.threshold
```

**Pillar Alignment**:
- P1: Probabilistic detection (ratio-based, not absolute)
- P2: Detects non-linear divergence (small train improvement → large test degradation)
- P3: No distribution assumptions
- P4: Works across all timeframes

---

### 007-FE-003: Probabilistic Sharpe Ratio (ROI 7.5)

**Purpose**: Account for non-normality in return distributions

**Implementation**:
```python
def probabilistic_sharpe_ratio(
    returns: np.ndarray,
    benchmark_sr: float = 0.0,
    annualization: int = 252
) -> float:
    """PSR = P(SR > benchmark | skew, kurtosis, T)"""
    sr = returns.mean() / returns.std() * np.sqrt(annualization)
    T = len(returns)
    skew = scipy.stats.skew(returns)
    kurt = scipy.stats.kurtosis(returns)

    # Standard error of Sharpe ratio
    se = np.sqrt((1 + 0.5 * sr**2 - skew * sr + (kurt - 3) / 4 * sr**2) / T)

    # Probability that true SR > benchmark
    psr = scipy.stats.norm.cdf((sr - benchmark_sr) / se)
    return psr
```

**Reference**: Bailey & Lopez de Prado (2012)

---

### 009-FE-003: Ensemble Strategy Selection (ROI 7.5)

**Purpose**: Deploy portfolio of uncorrelated strategies instead of single best

**Implementation**:
```python
def select_ensemble(
    strategies: list[Strategy],
    correlation_matrix: np.ndarray,
    n_select: int = 5,
    max_correlation: float = 0.3
) -> list[Strategy]:
    """Select top-N strategies with low pairwise correlation"""
    selected = [strategies[0]]  # Start with best

    for strategy in strategies[1:]:
        if len(selected) >= n_select:
            break
        # Check correlation with all selected
        idx = strategies.index(strategy)
        correlations = [correlation_matrix[idx, strategies.index(s)] for s in selected]
        if max(correlations) < max_correlation:
            selected.append(strategy)

    return selected
```

---

### 007-FE-004: Transaction Cost Modeling (ROI 5.0)

**Purpose**: Include realistic trading costs in backtest

**Implementation**:
```python
@dataclass
class TransactionCosts:
    commission_rate: float = 0.0004  # 4 bps
    slippage_bps: float = 2.0        # 2 bps base
    spread_bps: float = 1.0          # 1 bp half-spread

    def calculate(self, notional: float, volatility: float = 0.02) -> float:
        """Total cost = commission + slippage + spread"""
        commission = notional * self.commission_rate
        # Slippage scales with sqrt(notional) and volatility (P2: power law)
        slippage = notional * self.slippage_bps / 10000 * np.sqrt(volatility / 0.02)
        spread = notional * self.spread_bps / 10000
        return commission + slippage + spread
```

---

## Cross-References

### Existing Implementations

- **luck_skill.py**: `strategies/common/adaptive_control/luck_skill.py`
  - Implements DSR (Deflated Sharpe Ratio) and PBO
  - Related to 007-FE-003 (Probabilistic Sharpe)

### Spec Dependencies

- **Walk-Forward During Evolution** (007-FE-002) depends on **Walk-Forward Validation** (Spec 020)
- **Overfitting Detection** (010-FE-005) complements **PBO/DSR** in luck_skill.py

---

## Maintenance

- **Review Frequency**: Quarterly
- **ROI Re-evaluation**: When implementation complexity changes
- **Cleanup**: Archive implemented enhancements with outcome notes

---

**Last Updated**: 2026-01-11
**Analysis**: Round 2 with Pillar Alignment + ROI
**Total**: 4 MVP (all implemented), 7 KEEP, 7 CONDITIONAL, 8 REMOVED, 2 DUPLICATES
**Next Review**: 2026-04-11

## Implementation Locations

### Core Implementations

| MVP | Module | Location |
|-----|--------|----------|
| Overfitting Detection | `OverfittingDetector` | `strategies/common/adaptive_control/luck_skill.py` |
| Probabilistic Sharpe | `probabilistic_sharpe_ratio()` | `strategies/common/adaptive_control/luck_skill.py` |
| Ensemble Selection | `select_ensemble()`, `EnsembleSelector` | `strategies/common/adaptive_control/ensemble_selection.py` |
| Transaction Costs | `TransactionCostModel`, `CostProfile` | `strategies/common/adaptive_control/transaction_costs.py` |

### Alpha-Evolve Integration Points

| MVP | Integration | Location |
|-----|-------------|----------|
| PSR | `FitnessMetrics.psr` calculated during evaluation | `scripts/alpha_evolve/evaluator.py:386-395` |
| Transaction Costs | `FitnessMetrics.net_sharpe` (adjusted Sharpe) | `scripts/alpha_evolve/evaluator.py:397-416` |
| Overfitting Detection | `WalkForwardResult.overfit_*_count` | `scripts/alpha_evolve/walk_forward/validator.py:128-149` |
| All metrics | SQLite persistence with schema migration | `scripts/alpha_evolve/store.py:102-113` |

### Schema Updates

| Model | New Fields |
|-------|------------|
| `FitnessMetrics` | `psr`, `net_sharpe` |
| `WalkForwardResult` | `overfit_critical_count`, `overfit_warning_count` |
| SQLite `programs` table | `psr REAL`, `net_sharpe REAL` (auto-migrated) |
