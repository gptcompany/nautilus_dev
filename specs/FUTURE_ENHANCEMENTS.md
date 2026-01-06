# Future Enhancements Index

> **Philosophy**: Add complexity ONLY when current approach shows problems in out-of-sample testing.
>
> This index tracks all future enhancement concepts (FE-XXX) across specifications. Each enhancement is documented with its trigger condition - the empirical evidence or problem that would justify implementing it.

## Purpose

- **Prevent premature optimization**: Implement enhancements only when triggered by real issues
- **Track enhancement readiness**: Link enhancements to observable conditions
- **Enable informed decisions**: Quick reference for "should we implement this?"
- **Maintain architecture coherence**: See relationships between enhancements across specs

## How to Use This Index

1. **When observing a problem**: Search triggers to find relevant enhancements
2. **Before implementing**: Check if enhancement already exists elsewhere
3. **When adding new FE**: Update this index with trigger condition
4. **During reviews**: Verify enhancements aren't implemented without triggers

## Enhancement Index

| ID | Spec | Concept | Trigger | Status |
|----|------|---------|---------|--------|
| FE-001 | 006 | Fitness Sharing (Niching) | Convergence to single solution | Documented |
| FE-002 | 006 | Island Model (Parallel Populations) | Single population stagnation | Documented |
| FE-003 | 006 | Adaptive Mutation Rates | Fixed mutation rates suboptimal | Documented |
| FE-004 | 006 | Lineage Pruning (Age-Based Selection) | Old lineages dominating | Documented |
| FE-001 | 007 | Multi-Objective Optimization | Trade-offs between metrics (Sharpe vs Drawdown) | Documented |
| FE-002 | 007 | Walk-Forward During Evolution | Current single-period validation insufficient | Documented |
| FE-003 | 007 | Probabilistic Sharpe Ratio | Traditional Sharpe assumes normality | Documented |
| FE-004 | 007 | Transaction Cost Modeling | Zero-fee backtests unrealistic | Documented |
| FE-001 | 008 | Multiple Evolvable Blocks | Single evolvable block limiting | Documented |
| FE-002 | 008 | State Machine Templates | Complex multi-state strategies | Documented |
| FE-003 | 008 | Feature Engineering Helpers | Hardcoded indicators | Documented |
| FE-004 | 008 | Risk-Aware Position Sizing | Fixed position sizing | Documented |
| FE-001 | 009 | Adaptive Mutation Rate Control | Fixed mutation rates suboptimal | Documented |
| FE-002 | 009 | Prompt Engineering Evolution | Static prompts limiting exploration | Documented |
| FE-003 | 009 | Ensemble Strategy Selection | Single best strategy fragile | Documented |
| FE-004 | 009 | Novelty Search | Exploitation-only search | Documented |
| FE-001 | 010 | Population Diversity Heatmap | Population convergence unclear | Documented |
| FE-002 | 010 | Mutation Success Attribution | Which mutations help? | Documented |
| FE-003 | 010 | Fitness Landscape Visualization | Where are we in search space? | Documented |
| FE-004 | 010 | Lineage Tree Visualization | How did we get here? | Documented |
| FE-005 | 010 | Overfitting Detection | Is this overfitting? | Documented |
| FE-001 | 020 | Anchored vs Rolling Walk-Forward | Rolling instability between windows | Documented |
| FE-002 | 020 | White's Reality Check | >20 strategy variants tested | Documented |
| FE-003 | 020 | Combinatorial Purged CV (CPCV) | 5 windows insufficient for confidence | Documented |
| FE-004 | 020 | Profit Factor Decay Analysis | Strategies pass WF but fail in live after N months | Documented |
| FE-001 | 031 | Kendall Correlation (P2) | Spearman assumes monotonic relationships | Documented |
| FE-002 | 031 | Power-Law Penalty Scaling | Linear penalties (correlation^2) insufficient | Documented |
| FE-003 | 031 | Tail Dependence (Copulas) | Joint extreme movements ignored | Documented |

## Detailed Enhancement Summaries

### Spec 006: Alpha-Evolve Core

**FE-001: Fitness Sharing (Niching)**
- **Purpose**: Maintain population diversity by penalizing similar solutions
- **Trigger**: Population converges to single solution type
- **Implementation**: Share fitness among similar strategies (genotype/phenotype distance)
- **Reference**: `specs/006-alpha-evolve-core/spec.md`

**FE-002: Island Model (Parallel Populations)**
- **Purpose**: Run multiple isolated populations with periodic migration
- **Trigger**: Single population shows stagnation
- **Implementation**: N parallel populations, migrate best strategies periodically
- **Reference**: `specs/006-alpha-evolve-core/spec.md`

**FE-003: Adaptive Mutation Rates**
- **Purpose**: Adjust mutation rates based on fitness improvement
- **Trigger**: Fixed mutation rates show suboptimal exploration/exploitation balance
- **Implementation**: Increase mutation when stagnant, decrease when improving
- **Reference**: `specs/006-alpha-evolve-core/spec.md`

**FE-004: Lineage Pruning (Age-Based Selection)**
- **Purpose**: Prevent old lineages from dominating population
- **Trigger**: Old strategies dominate despite newer innovations
- **Implementation**: Penalize fitness by age, prune old lineages
- **Reference**: `specs/006-alpha-evolve-core/spec.md`

### Spec 007: Alpha-Evolve Evaluator

**FE-001: Multi-Objective Optimization**
- **Purpose**: Optimize multiple conflicting objectives (Sharpe vs Drawdown)
- **Trigger**: Single fitness function creates unacceptable trade-offs
- **Implementation**: Pareto frontier, NSGA-II selection
- **Reference**: `specs/007-alpha-evolve-evaluator/spec.md`

**FE-002: Walk-Forward Validation During Evolution**
- **Purpose**: Validate strategies on multiple periods during evolution
- **Trigger**: Single-period validation insufficient to prevent overfitting
- **Implementation**: Fitness = avg(performance across walk-forward windows)
- **Reference**: `specs/007-alpha-evolve-evaluator/spec.md`

**FE-003: Probabilistic Sharpe Ratio**
- **Purpose**: Account for non-normality in return distributions
- **Trigger**: Traditional Sharpe ratio misleading for skewed/fat-tailed returns
- **Implementation**: PSR = P(SR > threshold | skew, kurtosis, T)
- **Reference**: `specs/007-alpha-evolve-evaluator/spec.md`

**FE-004: Transaction Cost Modeling**
- **Purpose**: Include realistic trading costs in backtest
- **Trigger**: Zero-fee backtests unrealistic, strategies fail in live
- **Implementation**: Model slippage, commissions, spread, market impact
- **Reference**: `specs/007-alpha-evolve-evaluator/spec.md`

### Spec 008: Alpha-Evolve Templates

**FE-001: Multiple Evolvable Blocks**
- **Purpose**: Evolve entry, exit, and sizing independently
- **Trigger**: Single evolvable block too limiting for complex strategies
- **Implementation**: 3+ evolvable sections with independent mutation
- **Reference**: `specs/008-alpha-evolve-templates/spec.md`

**FE-002: State Machine Templates**
- **Purpose**: Support multi-state strategy logic (accumulation, distribution, etc.)
- **Trigger**: Complex strategies require state management
- **Implementation**: Define states, transitions, per-state logic templates
- **Reference**: `specs/008-alpha-evolve-templates/spec.md`

**FE-003: Feature Engineering Helpers**
- **Purpose**: Generate derived indicators from price data
- **Trigger**: Hardcoded indicators limiting strategy space
- **Implementation**: Feature generation functions (ratios, lags, rolling stats)
- **Reference**: `specs/008-alpha-evolve-templates/spec.md`

**FE-004: Risk-Aware Position Sizing**
- **Purpose**: Adaptive position sizing based on volatility/regime
- **Trigger**: Fixed position sizing underperforms
- **Implementation**: Kelly Criterion, volatility scaling, regime-aware sizing
- **Reference**: `specs/008-alpha-evolve-templates/spec.md`

### Spec 009: Alpha-Evolve Controller

**FE-001: Adaptive Mutation Rate Control**
- **Purpose**: Dynamically adjust mutation rates during evolution
- **Trigger**: Fixed rates show suboptimal performance
- **Implementation**: Increase rate when stagnant, decrease when improving
- **Reference**: `specs/009-alpha-evolve-controller/spec.md`

**FE-002: Prompt Engineering Evolution**
- **Purpose**: Evolve the mutation prompts themselves
- **Trigger**: Static prompts limit exploration quality
- **Implementation**: Meta-evolution of prompt templates
- **Reference**: `specs/009-alpha-evolve-controller/spec.md`

**FE-003: Ensemble Strategy Selection**
- **Purpose**: Deploy portfolio of uncorrelated strategies instead of single best
- **Trigger**: Single best strategy fragile to regime changes
- **Implementation**: Select top-N with low correlation, equal-weight or optimize
- **Reference**: `specs/009-alpha-evolve-controller/spec.md`

**FE-004: Novelty Search**
- **Purpose**: Reward behavioral novelty in addition to fitness
- **Trigger**: Exploitation-only search misses innovative solutions
- **Implementation**: Fitness = performance + novelty_bonus
- **Reference**: `specs/009-alpha-evolve-controller/spec.md`

### Spec 010: Alpha-Evolve Dashboard

**FE-001: Population Diversity Heatmap**
- **Purpose**: Visualize population diversity over time
- **Trigger**: Unclear if/when population converges
- **Implementation**: Heatmap of strategy similarity matrix per generation
- **Reference**: `specs/010-alpha-evolve-dashboard/spec.md`

**FE-002: Mutation Success Attribution**
- **Purpose**: Track which mutation types produce best strategies
- **Trigger**: Need to understand which mutations are effective
- **Implementation**: Bar chart of fitness delta by mutation type
- **Reference**: `specs/010-alpha-evolve-dashboard/spec.md`

**FE-003: Fitness Landscape Visualization**
- **Purpose**: 2D projection of strategy fitness landscape
- **Trigger**: Need to visualize search space position
- **Implementation**: PCA/t-SNE projection colored by fitness
- **Reference**: `specs/010-alpha-evolve-dashboard/spec.md`

**FE-004: Lineage Tree Visualization**
- **Purpose**: Show genealogy of strategies
- **Trigger**: Need to understand evolutionary path
- **Implementation**: Tree diagram with fitness evolution along branches
- **Reference**: `specs/010-alpha-evolve-dashboard/spec.md`

**FE-005: Overfitting Detection**
- **Purpose**: Real-time alerts for train/test performance divergence
- **Trigger**: Need early warning of overfitting
- **Implementation**: Monitor train_sharpe / test_sharpe ratio over generations
- **Reference**: `specs/010-alpha-evolve-dashboard/spec.md`

### Spec 020: Walk-Forward Validation

**FE-001: Anchored vs Rolling Walk-Forward**
- **Purpose**: Support anchored walk-forward (training from start, growing window)
- **Trigger**: Rolling windows show instability, need more training data
- **Implementation**: Toggle between rolling vs anchored window generation
- **Trade-off**: Anchored uses more data but may include stale regimes
- **Reference**: `specs/020-walk-forward-validation/spec.md`

**FE-002: White's Reality Check (Multiple Testing)**
- **Purpose**: Correct for multiple testing when selecting best from N strategies
- **Trigger**: Testing >20 strategy variants increases false discovery rate
- **Implementation**: Bootstrap-based Reality Check for p-value correction
- **Reference**: White (2000) "A Reality Check for Data Snooping"
- **Reference**: `specs/020-walk-forward-validation/spec.md`

**FE-003: Combinatorial Purged Cross-Validation (CPCV)**
- **Purpose**: More robust validation using combinatorial train/test splits
- **Trigger**: 5 sequential windows insufficient for statistical confidence
- **Implementation**: C(N,K) combinations instead of sequential windows
- **Trade-off**: Computationally expensive (15x vs 5x) but more robust
- **Reference**: Lopez de Prado (2018) Ch. 7
- **Reference**: `specs/020-walk-forward-validation/spec.md`

**FE-004: Profit Factor Decay Analysis**
- **Purpose**: Detect strategy degradation over time
- **Trigger**: Strategies pass WF validation but fail in live after N months
- **Implementation**: Fit exponential decay to profit factor per window
- **Action**: If half_life < 6 months, flag for frequent re-evolution
- **Reference**: `specs/020-walk-forward-validation/spec.md`

### Spec 031: CSRC Correlation

**FE-001: Kendall Correlation (P2 Enhancement)**
- **Purpose**: Rank-based correlation robust to outliers
- **Trigger**: Spearman assumes monotonic relationships, Kendall more robust
- **Implementation**: Replace Spearman with Kendall tau in correlation penalty
- **Reference**: `specs/031-csrc-correlation/spec.md`

**FE-002: Power-Law Penalty Scaling**
- **Purpose**: Non-linear correlation penalties (inspired by Pillar 2)
- **Trigger**: Linear penalties (correlation^2) insufficient for high correlations
- **Implementation**: penalty ∝ correlation^α where α > 1
- **Reference**: `specs/031-csrc-correlation/spec.md`

**FE-003: Tail Dependence (Copulas)**
- **Purpose**: Measure correlation in extreme moves (tail risk)
- **Trigger**: Standard correlation ignores joint extreme events
- **Implementation**: Student-t copula or empirical tail dependence coefficient
- **Reference**: `specs/031-csrc-correlation/spec.md`

## Implementation Workflow

When implementing an enhancement:

1. **Verify Trigger**: Confirm the trigger condition has been observed in testing/production
2. **Create Spec Branch**: `git checkout -b enhance-<spec-id>-fe-<num>`
3. **Update Spec**: Add implementation details to spec.md
4. **Update This Index**: Change status to "In Progress"
5. **Implement**: Follow TDD workflow
6. **Test Trigger**: Verify enhancement solves the trigger condition
7. **Update Status**: Mark as "Implemented" with date and results

## Cross-References

### Related Implementations

- **luck_skill.py**: `strategies/common/adaptive_control/luck_skill.py`
  - Implements DSR (Deflated Sharpe Ratio) and PBO (Probability of Backtest Overfitting)
  - Related to FE-002 (020), FE-003 (007)
  - Linked to Spec 020 (Walk-Forward Validation)

### Spec Dependencies

- **Walk-Forward During Evolution** (FE-002 in 007) depends on **Walk-Forward Validation** (Spec 020)
- **Overfitting Detection** (FE-005 in 010) relates to **PBO/DSR** in luck_skill.py
- **Adaptive Mutation Rates** (FE-003 in 006, FE-001 in 009) - same concept, different specs

## Maintenance

- **Review Frequency**: Quarterly review to check if triggers have occurred
- **Updates**: Add new FE-XXX entries when creating new specs
- **Cleanup**: Archive implemented enhancements with outcome notes
- **Ownership**: Each spec owner maintains their FE entries

---

**Last Updated**: 2026-01-06
**Total Enhancements**: 27 documented, 0 in progress, 0 implemented
**Next Review**: 2026-04-06
