# Implementation Plan: Baseline Validation (Spec 029)

**Feature Branch**: `029-baseline-validation`
**Created**: 2026-01-05
**Status**: Draft
**Estimated Effort**: 24-32 hours
**Dependencies**: Existing walk-forward infrastructure, adaptive control modules

---

## Executive Summary

This plan implements a rigorous validation framework to answer a fundamental question:
**Does our complex adaptive system (~60 parameters) outperform simple baselines (~3 parameters) in out-of-sample testing?**

Based on DeMiguel et al. (2009), simple 1/N strategies beat 14 optimization models OOS. Our validation must prove the adaptive system provides statistically significant edge (Sharpe > Baseline + 0.2) to justify deployment complexity.

---

## PMW Philosophy: Why This Validation is Critical

> **"Cerca attivamente disconferme, non conferme"** (PMW - Prove Me Wrong)

This spec exists because **we do not assume the adaptive system works**. Academic research suggests:

- **DeMiguel 2009**: 1/N beats 14 optimization models OOS
- **70% of ML strategies fail within 6 months** (industry data)
- **~60 parameters = ~60 opportunities for overfitting**

### Expected Outcomes (Honest Assessment)

| Outcome | Probability | Action |
|---------|-------------|--------|
| Adaptive wins (Sharpe +0.2, DSR >0.5) | **30%** | Deploy with monitoring |
| Fixed 2% wins | **50%** | Simplify system, abandon Spec-027 complexity |
| Inconclusive | **20%** | Extend test period or refine approach |

### What Happens If Fixed 2% Wins?

If validation shows Fixed 2% outperforms the adaptive stack:

1. **Archive** `strategies/common/adaptive_control/` (don't delete - learning)
2. **Simplify** to Fixed Fractional sizing (3 params)
3. **Redirect effort** to alpha generation, not position sizing complexity
4. **Document** lessons learned in PMW validation report

This is **not failure** - it's the scientific method applied to trading systems.

---

## Research Summary

### Key Academic Sources

1. **DeMiguel, Garlappi, Uppal (2009)** - "Optimal Versus Naive Diversification"
   - 1/N portfolio beats 14 optimization models OOS
   - Estimation window needed: ~3000 months for 25 assets
   - [SSRN Paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=911512)

2. **Bailey & Lopez de Prado (2014)** - "The Deflated Sharpe Ratio"
   - DSR corrects for selection bias and multiple testing
   - Uses skewness, kurtosis, and number of trials
   - [SSRN Paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)

3. **Lopez de Prado (2018)** - "Advances in Financial Machine Learning"
   - Chapter 11: Probability of Backtest Overfitting (PBO)
   - Chapter 12: Combinatorial Purged Cross-Validation (CPCV)
   - Chapter 14: Deflated Sharpe Ratio implementation

4. **2024 Research on Walk-Forward vs CPCV**
   - [ScienceDirect Study](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110)
   - Finding: CPCV superior to Walk-Forward in false discovery prevention
   - Walk-Forward has "increased temporal variability and weaker stationarity"

### Key Findings

| Topic | Finding | Implication |
|-------|---------|-------------|
| **1/N vs Optimized** | 1/N beats 14 models OOS | Simple baselines are strong competitors |
| **DSR** | Accounts for multiple testing, skewness, kurtosis | Must implement for valid comparison |
| **CPCV vs Walk-Forward** | CPCV has lower PBO, better stability | Consider CPCV upgrade path |
| **Statistical Significance** | t-stat ~3.0 = 1% false positive | Sharpe + 0.2 is reasonable threshold |
| **70% ML Failure** | Most strategies fail in 6 months | Deep OOS validation mandatory |

---

## Architecture Decision Records (ADRs)

### ADR-001: Validation Method Selection

**Context**: Choose between Walk-Forward, CPCV, or hybrid approach.

**Options**:
1. **Walk-Forward Only** (current infrastructure)
   - Pro: Already implemented, simpler
   - Con: Higher temporal variability, weaker false discovery prevention

2. **CPCV Only** 
   - Pro: Superior statistical properties, lower PBO
   - Con: High computational cost, not yet implemented

3. **Walk-Forward + PBO/DSR** (recommended)
   - Pro: Leverages existing infrastructure, adds key Lopez de Prado metrics
   - Con: Not as robust as full CPCV

**Decision**: Option 3 - Walk-Forward with enhanced metrics.

**Rationale**: 
- Existing walk-forward infrastructure is solid (validator.py, metrics.py)
- DSR and PBO already implemented in metrics.py
- CPCV can be added as future enhancement (FR-011 optional)

---

### ADR-002: Contender Implementation Strategy

**Context**: How to implement the three contenders.

**Options**:
1. **Separate Strategy Classes** - One NautilusTrader Strategy per contender
2. **Configurable Sizer** - Single strategy with pluggable position sizer
3. **Sizing Adapter Pattern** - Wrapper around existing sizers

**Decision**: Option 2 - Configurable Sizer.

**Rationale**:
- Ensures identical signal generation across contenders
- Only position sizing differs - isolates the comparison variable
- Reuses existing code (GillerSizer, SOPS classes)
- Easier to add new contenders

**Implementation** (aligned with NautilusTrader `PositionSizer` base class):
```python
from decimal import Decimal
from nautilus_trader.model.objects import Price, Money, Quantity
from nautilus_trader.risk.sizing import PositionSizer, FixedRiskSizer

class AdaptiveSizer(PositionSizer):
    """Contender A: SOPS + Giller + Thompson adaptive sizing."""

    def __init__(self, instrument, sops_sizer, giller_exponent: float = 0.5):
        super().__init__(instrument)
        self._sops = sops_sizer
        self._giller_exp = giller_exponent

    def calculate(
        self,
        entry: Price,
        stop_loss: Price,
        equity: Money,
        risk: Decimal,
        commission_rate: Decimal = Decimal(0),
        exchange_rate: Decimal = Decimal(1),
        hard_limit: Decimal | None = None,
        unit_batch_size: Decimal = Decimal(1),
        units: int = 1,
    ) -> Quantity:
        """Calculate position size using adaptive SOPS+Giller logic."""
        signal = self._sops.get_signal()
        adjusted_risk = risk * Decimal(str(abs(signal) ** self._giller_exp))
        # Use native FixedRiskSizer calculation with adjusted risk
        base_sizer = FixedRiskSizer(self.instrument)
        return base_sizer.calculate(entry, stop_loss, equity, adjusted_risk)

class FixedFractionalSizer(PositionSizer):
    """Contender B: Fixed 2% risk per trade (uses native FixedRiskSizer)."""

    def __init__(self, instrument, risk_pct: float = 0.02):
        super().__init__(instrument)
        self._base_sizer = FixedRiskSizer(instrument)
        self._risk_pct = Decimal(str(risk_pct))

    def calculate(self, entry: Price, stop_loss: Price, equity: Money, **kwargs) -> Quantity:
        return self._base_sizer.calculate(entry, stop_loss, equity, self._risk_pct, **kwargs)

class BuyAndHoldSizer(PositionSizer):
    """Contender C: Full allocation, no rebalancing."""

    def calculate(self, entry: Price, stop_loss: Price, equity: Money, **kwargs) -> Quantity:
        # Full equity allocation
        size = equity.as_decimal() / entry.as_decimal()
        return self.instrument.make_qty(size)
```

**Note**: All sizers now extend `nautilus_trader.risk.sizing.PositionSizer` for API compatibility.

---

### ADR-003: Statistical Significance Threshold

**Context**: Define when adaptive system "wins" over baseline.

**Options**:
1. **Sharpe > Baseline** - Any positive difference
2. **Sharpe > Baseline + 0.2** - Meaningful edge threshold
3. **p-value < 0.05** - Traditional hypothesis test
4. **Combined**: Sharpe + 0.2 AND DSR > 0.5 AND PBO < 0.5

**Decision**: Option 4 - Combined criteria.

**Rationale**:
- Sharpe + 0.2 threshold from research_vs_repos_analysis.md
- DSR > 0.5 ensures skill > luck after multiple testing adjustment
- PBO < 0.5 ensures strategy is not overfit
- Multiple criteria reduce false positives

**Success Criteria**:
```python
def determine_verdict(adaptive: ValidationResult, fixed: ValidationResult) -> str:
    sharpe_edge = adaptive.avg_test_sharpe - fixed.avg_test_sharpe > 0.2
    dsr_skill = adaptive.deflated_sharpe_ratio > 0.5
    not_overfit = adaptive.probability_backtest_overfitting < 0.5
    lower_drawdown = adaptive.worst_drawdown < fixed.worst_drawdown
    
    if sharpe_edge and dsr_skill and not_overfit:
        return "GO" if lower_drawdown else "GO_WITH_CAUTION"
    elif fixed.avg_test_sharpe > adaptive.avg_test_sharpe:
        return "STOP"  # Simple beats complex
    else:
        return "WAIT"  # Inconclusive
```

---

### ADR-004: Walk-Forward Window Configuration

**Context**: Optimal window sizes for 10-year BTC dataset.

**Research-Based Defaults**:
- Train: 12 months (captures multiple market regimes)
- Test: 1 month (OOS period)
- Step: 1 month (rolling)
- Embargo: 5 days before, 3 days after (Lopez de Prado PKCV)

**Calculation**:
- 10 years = 120 months
- 12 windows minimum required
- With 12m train + 1m test + 8 days embargo: ~13 months per initial window
- Remaining 107 months / 1 month step = ~107 additional steps
- Total: ~80+ windows for statistical power

**Configuration**:
```python
baseline_config = WalkForwardConfig(
    data_start=datetime(2015, 1, 1),
    data_end=datetime(2025, 1, 1),
    train_months=12,
    test_months=1,
    step_months=1,
    embargo_before_days=5,
    embargo_after_days=3,
    min_windows=12,
    min_profitable_windows_pct=0.50,  # Relaxed for baselines
    min_test_sharpe=0.0,  # Allow negative for comparison
    max_drawdown_threshold=0.50,  # Relaxed
    min_robustness_score=40.0,  # Relaxed
)
```

---

## Implementation Plan

### Phase 1: Contender Framework (8h)

**Task 1.1: Create Contender Sizer Protocol** (2h)
- File: `scripts/baseline_validation/sizers.py`
- Define `ContenderSizer` protocol
- Implement `FixedFractionalSizer` (Fixed 2%)
- Implement `BuyAndHoldSizer`
- Implement `AdaptiveSizer` (wrapper around SOPS+Giller+Thompson)

**Task 1.2: Create Baseline Strategy Wrapper** (3h)
- File: `scripts/baseline_validation/baseline_strategy.py`
- Generic strategy that accepts any `ContenderSizer`
- Uses same signal generation for all contenders
- Signal: Simple momentum (EMA crossover) - NOT the point of comparison

**Task 1.3: Create Contender Registry** (1h)
- File: `scripts/baseline_validation/registry.py`
- Registry pattern for contender discovery
- Easy to add new contenders

**Task 1.4: Unit Tests** (2h)
- File: `tests/test_baseline_validation/test_sizers.py`
- Test each sizer in isolation
- Test signal sign preservation
- Test edge cases (zero signal, extreme values)

---

### Phase 2: Comparison Runner (8h)

**Task 2.1: Extend WalkForwardValidator for Multi-Contender** (3h)
- File: `scripts/baseline_validation/comparison_validator.py`
- Run same windows for all contenders
- Collect `ContenderResult` per contender

**Task 2.2: Create Comparison Metrics** (2h)
- File: `scripts/baseline_validation/comparison_metrics.py`
- Relative Sharpe difference
- Win/Loss ratio between contenders
- Statistical significance (t-test on OOS returns)
- DSR comparison

**Task 2.3: Implement Verdict Logic** (2h)
- File: `scripts/baseline_validation/verdict.py`
- GO/WAIT/STOP determination
- Confidence levels
- Recommendation generator

**Task 2.4: Integration Tests** (1h)
- File: `tests/test_baseline_validation/test_comparison.py`
- End-to-end comparison test with mock data
- Verify verdict logic

---

### Phase 3: Reporting (6h)

**Task 3.1: Create Report Models** (1h)
- File: `scripts/baseline_validation/report_models.py`
- Pydantic models for report structure
- JSON serialization for persistence

**Task 3.2: Create Report Generator** (3h)
- File: `scripts/baseline_validation/report.py`
- Markdown report with comparison table
- Metrics breakdown per contender
- GO/WAIT/STOP recommendation with justification
- Charts: equity curves, Sharpe distribution

**Task 3.3: Create CLI Interface** (2h)
- File: `scripts/baseline_validation/cli.py`
- Click-based CLI
- Commands: `run`, `report`, `compare`
- Config from YAML file

---

### Phase 4: Integration with Existing Infrastructure (4h)

**Task 4.1: Connect to ParquetDataCatalog** (2h)
- Load BTC historical data from catalog
- Handle data gaps and validation

**Task 4.2: Connect to BacktestEngine** (1h)
- Implement `StrategyEvaluator` protocol
- Run backtests for each window/contender

**Task 4.3: Connect to Adaptive Control Stack** (1h)
- Wire up SOPS + Giller + Thompson for Contender A
- Ensure all parameters are configurable

---

### Phase 5: Documentation & Validation (4h)

**Task 5.1: Create Usage Guide** (1h)
- File: `docs/029-baseline-validation-guide.md`
- Quick start, configuration, interpretation

**Task 5.2: Run Initial Validation** (2h)
- Execute on available BTC data
- Document initial results
- Identify any issues

**Task 5.3: Create Runbook** (1h)
- File: `docs/029-baseline-validation-runbook.md`
- How to interpret results
- When to re-run validation
- Troubleshooting

---

## File Structure

```
scripts/baseline_validation/
├── __init__.py
├── sizers.py              # Task 1.1: ContenderSizer protocol + implementations
├── baseline_strategy.py   # Task 1.2: Generic strategy wrapper
├── registry.py            # Task 1.3: Contender registry
├── comparison_validator.py # Task 2.1: Multi-contender validator
├── comparison_metrics.py  # Task 2.2: Relative metrics
├── verdict.py             # Task 2.3: GO/WAIT/STOP logic
├── report_models.py       # Task 3.1: Report data models
├── report.py              # Task 3.2: Report generator
├── cli.py                 # Task 3.3: CLI interface
└── config/
    └── default.yaml       # Default configuration

tests/test_baseline_validation/
├── __init__.py
├── test_sizers.py         # Task 1.4
├── test_comparison.py     # Task 2.4
└── conftest.py            # Fixtures

docs/
├── 029-baseline-validation-guide.md   # Task 5.1
└── 029-baseline-validation-runbook.md # Task 5.3
```

---

## Configuration Schema

```yaml
# config/baseline_validation.yaml
validation:
  data_start: "2015-01-01"
  data_end: "2025-01-01"
  train_months: 12
  test_months: 1
  step_months: 1
  embargo_before_days: 5
  embargo_after_days: 3
  min_windows: 12

contenders:
  adaptive:
    name: "SOPS+Giller+Thompson"
    enabled: true
    config:
      sops_k_base: 1.0
      giller_exponent: 0.5
      thompson_decay: 0.99
  
  fixed:
    name: "Fixed 2%"
    enabled: true
    config:
      risk_pct: 0.02
      max_positions: 10
      stop_loss_pct: 0.05
  
  buyhold:
    name: "Buy & Hold"
    enabled: true
    config:
      allocation_pct: 1.0

success_criteria:
  sharpe_edge: 0.2           # Adaptive must beat Fixed by this
  min_dsr: 0.5               # Deflated Sharpe > 0.5 (skill > luck)
  max_pbo: 0.5               # PBO < 0.5 (not overfit)
  max_drawdown: 0.30         # Max acceptable drawdown

output:
  report_dir: "reports/baseline_validation"
  format: ["markdown", "json"]
```

---

## Dependencies

### Existing Infrastructure (Reuse)

| Module | Path | Purpose |
|--------|------|---------|
| `WalkForwardValidator` | `scripts/alpha_evolve/walk_forward/validator.py` | Core validation loop |
| `WalkForwardConfig` | `scripts/alpha_evolve/walk_forward/config.py` | Configuration model |
| `metrics.py` | `scripts/alpha_evolve/walk_forward/metrics.py` | DSR, PBO, robustness |
| `models.py` | `scripts/alpha_evolve/walk_forward/models.py` | Window, WindowResult |
| `GillerSizer` | `strategies/common/position_sizing/giller_sizing.py` | Giller power law |
| `SOPS` | `strategies/common/adaptive_control/sops_sizing.py` | SOPS + TapeSpeed |
| `ParticlePortfolio` | `strategies/common/adaptive_control/particle_portfolio.py` | Thompson Sampling |

### New Dependencies (None Required)

All functionality can be implemented with existing standard library + NautilusTrader.

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Insufficient data | Low | High | Verify catalog has 10+ years BTC |
| Adaptive wins by luck | Medium | High | DSR + PBO checks |
| Walk-forward temporal bias | Medium | Medium | Consider CPCV upgrade |
| Inconsistent transaction costs | Low | Medium | Apply same costs to all |
| Regime-dependent results | Medium | Medium | Document regime breakdown |

---

## Success Metrics

### Validation Passes If:

1. **Minimum Data**: 80+ OOS windows generated
2. **All Contenders Run**: No NaN/Inf in any result
3. **Statistical Validity**: DSR calculated for all contenders
4. **Clear Verdict**: GO/WAIT/STOP determined with >80% confidence

### Expected Outcomes:

| Outcome | Probability | Action |
|---------|-------------|--------|
| Adaptive wins (Sharpe + 0.2) | 30% | Deploy with monitoring |
| Fixed 2% wins | 50% | Simplify system |
| Inconclusive | 20% | Extend test period or refine |

---

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Contender Framework | 2 days | None |
| Phase 2: Comparison Runner | 2 days | Phase 1 |
| Phase 3: Reporting | 1.5 days | Phase 2 |
| Phase 4: Integration | 1 day | Phase 3 |
| Phase 5: Documentation | 0.5 days | Phase 4 |
| **Total** | **7 days** | |

---

## Future Enhancements (Out of Scope)

1. **FR-011**: CPCV implementation for superior false discovery prevention
2. **FR-012**: Multi-asset validation (ETH, SOL, etc.)
3. **FR-013**: Real-time streaming validation
4. **FR-014**: Monte Carlo simulation for confidence intervals
5. **FR-015**: Automated re-validation on new data

---

## References

### Academic Papers
- [DeMiguel et al. 2009 - 1/N Portfolio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=911512)
- [Bailey & Lopez de Prado 2014 - Deflated Sharpe Ratio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
- [Bailey et al. 2015 - Probability of Backtest Overfitting](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253)
- [2024 Study - CPCV vs Walk-Forward](https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110)

### Implementation Resources
- [skfolio CombinatorialPurgedCV](https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html)
- [QuantBeckman CPCV Tutorial](https://www.quantbeckman.com/p/with-code-combinatorial-purged-cross)
- [DSR Python Implementation](https://medium.com/balaena-quant-insights/deflated-sharpe-ratio-dsr-33412c7dd464)

### Internal Documentation
- [PMW Validation Analysis](../028-validation/research_vs_repos_analysis.md)
- [Walk-Forward Infrastructure](../../scripts/alpha_evolve/walk_forward/)
- [Adaptive Control Stack](../../strategies/common/adaptive_control/)

---

*Generated: 2026-01-05*
*Methodology: PMW (Prove Me Wrong) - Seek disconfirmation, not confirmation*
