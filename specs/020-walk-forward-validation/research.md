# Research: Walk-Forward Validation

**Feature**: Spec 020 - Walk-Forward Validation
**Date**: 2025-12-29
**Status**: Complete

## Summary

Walk-forward validation is a backtesting methodology that prevents overfitting by testing trading strategies on out-of-sample data in a rolling fashion. This research consolidates findings from academic papers to inform implementation decisions.

## Key Findings

### 1. The Overfitting Problem

**Decision**: Implement strict validation criteria
**Rationale**: Per arXiv:2512.12924, >90% of academic trading strategies fail when implemented with real capital. The gap between backtested and live performance is the primary challenge.

**Alternatives Considered**:
- Simple train/test split (insufficient for time series)
- K-fold cross-validation (violates temporal ordering)
- Monte Carlo simulation (computationally expensive)

### 2. Window Strategy: Rolling vs Anchored

**Decision**: Rolling (Sliding) Window
**Rationale**:
- Rolling windows better capture regime changes
- arXiv:2512.12924 used 34 independent test periods with rolling approach
- Prevents early data from dominating training

**Alternatives Considered**:
- Anchored (Expanding) Window: More data but early periods dominate
- Combinatorial Purged CV: More robust but O(n!) complexity

### 3. Purging (Embargo) Period

**Decision**: Configurable gap period (default 0, optional 1-5 days)
**Rationale**:
- Costa & Gebbie (2020) highlight data leakage via lagging indicators
- Serial correlation can artificially inflate performance
- Gap prevents information leakage for strategies with lookback periods

**Alternatives Considered**:
- No purging: Simpler but risks leakage
- Fixed 5-day purge: Conservative but loses data

### 4. Robustness Metrics

**Decision**: Composite score (Consistency 30% + Profitability 40% + Degradation 30%)
**Rationale**:
- Single metrics like Sharpe are insufficient (can be gamed)
- Multiple dimensions capture true robustness
- Weights based on practical trading priorities

**Alternatives Considered**:
- Deflated Sharpe Ratio: Adjusts for multiple testing but complex
- Simple win rate: Ignores magnitude of wins/losses
- Pure profitability %: Ignores consistency

## Academic Sources

### Primary Source: Lopez de Prado - "Advances in Financial Machine Learning" (2018)

**Title**: Advances in Financial Machine Learning

**Author**: Marcos Lopez de Prado

**Publisher**: Wiley

**ISBN**: 978-1-119-48208-6

**Key Chapters**:
- **Chapter 7**: Cross-Validation in Finance
  - Section 7.4: Purged K-Fold Cross-Validation (PKCV)
  - Section 7.4.3: Embargo (pre-test and post-test purging)
  - Key Finding: Standard CV overestimates performance by 50%+ due to serial correlation
- **Chapter 11**: Probability of Backtest Overfitting (PBO)
  - Combinatorial Symmetric Cross-Validation (CSCV)
  - Estimating false positive probability in strategy selection
  - Key Formula: PBO = P[median(IS) < median(OOS)]
- **Chapter 14**: Backtesting through Cross-Validation
  - Deflated Sharpe Ratio (DSR)
  - Adjusting for multiple testing and non-normality
  - Key Formula: DSR = Z⁻¹[Φ(SR) - ln(N)/√N]

**Critical Insights**:
1. **Purging**: Remove training observations whose labels overlap with test set due to serial correlation
2. **Embargo**: Add gap periods before AND after test windows to prevent leakage in both directions
3. **Multiple Testing Adjustment**: Use DSR to account for trying N different strategies/parameters
4. **Combinatorial Paths**: Test robustness by shuffling backtest period orderings

**Implementation Impact**:
- Default `embargo_before_days=5` (PKCV recommendation)
- New `embargo_after_days=3` (prevents next train contamination)
- Add DSR and PBO to validation metrics
- Use combinatorial simulation for robustness testing

---

### Secondary Source: arXiv:2512.12924 (2024)

**Title**: "Interpretable Hypothesis-Driven Trading: A Rigorous Walk-Forward Validation Framework for Market Microstructure Signals"

**Authors**: Gagan Deep, Akash Deep, William Lamptey

**Key Contributions**:
- 34 independent test periods via rolling window
- Strict information set discipline (no lookahead)
- Natural language hypothesis explanations
- Realistic transaction costs and position constraints

**Results**:
- Annualized Return: 0.55%
- Sharpe Ratio: 0.33
- Max Drawdown: -2.76%
- Beta: 0.058 (market neutral)

**Critical Insight**: "Daily OHLCV-based microstructure signals require elevated information arrival and trading activity to function effectively." Strategy works in volatile markets (2020-2024) but underperforms in stable periods (2015-2019).

### Tertiary Source: Costa & Gebbie (2020)

**Title**: "Learning low-frequency temporal patterns for quantitative trading"

**DOI**: 10.1109/SSCI47803.2020.9308232

**Key Contributions**:
- CSCV (Combinatorially Symmetric Cross Validation)
- Probabilistic Sharpe Ratio
- Deflated Sharpe Ratio for multiple testing adjustment

**Methodology**:
- Stacked autoencoder for feature learning
- Online feedforward neural network
- RBM pre-training for weight initialization

### Additional Sources

| Paper | Method | Key Finding |
|-------|--------|-------------|
| LSTM Rolling Window CV (2023) | Rolling windows | Vanilla LSTM outperforms stacked/bidirectional |
| CryptoTradeMate (2025) | WFO + Purged CV | AI strategies outperform rule-based in volatile markets |

## Implementation Recommendations

### From Research to Code

1. **Window Parameters** (from arXiv:2512.12924):
   - Train period: 6 months minimum
   - Test period: 3 months (quarterly)
   - Step: 3 months (quarterly roll)
   - Total windows: 4-8 for 24-month dataset

2. **Pass/Fail Criteria** (derived from literature):
   - Robustness Score >= 60
   - At least 75% windows profitable
   - Test Sharpe >= 0.5 in majority
   - No window with drawdown > 30%

3. **Advanced Metrics** (Lopez de Prado, 2018):
   - **Deflated Sharpe Ratio (DSR)**: Adjusts for multiple testing (Ch. 14)
     - Formula: DSR = Z⁻¹[Φ(SR) - ln(N)/√N]
     - N = number of strategy trials/parameters tested
   - **Probability of Backtest Overfitting (PBO)**: Estimates false positive risk (Ch. 11)
     - Uses combinatorial path permutations
     - Threshold: PBO > 0.5 indicates likely overfitting
   - **Combinatorial Purged CV (CPCV)**: Generate multiple train/test splits for robustness

4. **Future Enhancements**:
   - Regime detection for adaptive windows
   - Dynamic embargo period based on indicator lookback
   - Parallel window evaluation for speed

## Gaps and Unknowns

| Area | Status | Resolution |
|------|--------|------------|
| Optimal window size | Researched | 6-month train, 3-month test per literature |
| Purge period necessity | Researched | Optional, dependent on indicator lookbacks |
| Parallel evaluation | Not researched | Implementation decision (async) |
| Regime-aware windows | Not implemented | Future enhancement |

## References

1. **Lopez de Prado, M. (2018)**. Advances in Financial Machine Learning. Wiley Finance. ISBN: 978-1-119-48208-6.
   - Chapter 7: Cross-Validation in Finance (Purged K-Fold CV, Embargo)
   - Chapter 11: The Probability of Backtest Overfitting (PBO, CSCV)
   - Chapter 14: Backtesting through Cross-Validation (Deflated Sharpe Ratio)

2. **Deep, G., Deep, A., & Lamptey, W. (2024)**. Interpretable Hypothesis-Driven Trading: A Rigorous Walk-Forward Validation Framework for Market Microstructure Signals. arXiv:2512.12924.

3. **Costa, J. D., & Gebbie, T. (2020)**. Learning low-frequency temporal patterns for quantitative trading. IEEE SSCI 2020. DOI:10.1109/SSCI47803.2020.9308232.

4. **Pardo, R. E. (1992)**. Design, Testing and Optimization of Trading Systems. John Wiley & Sons.
