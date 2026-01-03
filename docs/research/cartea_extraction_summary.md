# Cartea Market Making Extraction Summary

**Generated**: 2026-01-03
**Source PDF**: "Algorithmic and High-Frequency Trading" by Álvaro Cartea et al.
**Output File**: `cartea_mm_implementation.md` (32 KB, 1,185 lines)

---

## Extraction Statistics

### Chapters Processed
- **Chapter 2**: Primer on Market Microstructure (Pages 19-39)
  - 2.1 Market Making Theory
  - 2.1.1 Grossman-Miller Model
  - 2.1.2 Trading Costs
  - 2.1.3 Measuring Liquidity
  - 2.1.4 Market Making using Limit Orders
  - 2.3 Market Making with Informational Disadvantage
  - 2.3.1 Price Dynamics
  - 2.3.2 Price Sensitive Liquidity Traders

- **Chapter 10**: Market Making Models (Pages 246-272)
  - 10.2.1 Market Making with No Inventory Restrictions
  - 10.2.2 Market Making At-The-Touch
  - 10.2.3 Market Making Optimising Volume
  - 10.3 Utility Maximising Market Maker
  - 10.4 Market Making with Adverse Selection
  - 10.4.1 Impact of Market Orders on Midprice
  - 10.4.2 Short-Term-Alpha and Adverse Selection

### Key Mathematical Models Extracted

1. **Avellaneda-Stoikov Model**
   - Hamilton-Jacobi-Bellman equations
   - Optimal spread formulas
   - Reservation price calculation
   - Inventory risk adjustment

2. **Adverse Selection Models**
   - Price impact from order flow
   - Short-term alpha integration
   - Toxicity detection

3. **Utility Maximization**
   - Exponential utility framework
   - Risk-adjusted spread optimization

### Implementation Components

**Total Phases**: 5 (Basic MM → Full Avellaneda-Stoikov)

**Code Artifacts**:
- Strategy class template (200+ lines)
- Configuration examples
- Risk management framework
- Testing checklist

**Parameters Documented**: 8 key parameters with calibration guides
- γ (risk aversion)
- k (elasticity)
- σ (volatility)
- α (terminal penalty)
- T (session duration)
- etc.

---

## Document Structure

1. **Executive Summary** - High-level overview
2. **Market Making Theory** - Economics and microstructure
3. **Mathematical Models** - Full equations and derivations
4. **Implementation Roadmap** - 5-phase implementation plan
5. **NautilusTrader Integration** - Complete strategy code
6. **Data Requirements** - L1/L2/L3 data needs
7. **Risk Management** - Position limits, circuit breakers
8. **Testing Strategy** - Unit tests, backtests, live paper
9. **Advanced Extensions** - Multi-asset, ML enhancements
10. **Appendices** - Equations summary, parameter ranges

---

## Key Insights for NautilusTrader

### Native Rust Usage
- Use `ExponentialMovingAverage` for volatility (never reimplement)
- Use `OrderBook` native analytics (mid_price, spread)
- Use `AverageTrueRange` for volatility estimation

### Strategy Pattern
```python
class AvellanedaStoikovMM(Strategy):
    - on_start() → Subscribe to data feeds
    - on_quote_tick() → Update mid-price, refresh quotes
    - _calculate_reservation_price() → Inventory adjustment
    - _calculate_optimal_spread() → HJB solution
    - _refresh_quotes() → Cancel/replace quotes
    - on_order_filled() → Handle fills
```

### Critical Trade-offs
1. **Spread Width** ↔ **Fill Rate**
   - Tight spreads = more fills, less profit per trade
   - Wide spreads = fewer fills, more profit per trade

2. **Inventory Risk** ↔ **Profit Opportunity**
   - Zero inventory = no risk, but miss profit from spread
   - Non-zero inventory = capture spread, but exposed to adverse moves

3. **Adverse Selection** ↔ **Liquidity Provision**
   - Always quote = maximum liquidity, but toxic flow risk
   - Selective quoting = avoid toxicity, but lower fill rate

---

## Next Steps

### Immediate (Week 1)
- [ ] Implement Phase 1: Basic MM with fixed spreads
- [ ] Set up backtesting framework
- [ ] Calibrate parameters on historical data

### Short-term (Month 1)
- [ ] Implement Phase 2-3: Inventory risk + volatility
- [ ] Paper trading validation
- [ ] Build monitoring dashboard

### Medium-term (Quarter 1)
- [ ] Implement Phase 4-5: Adverse selection + full A-S model
- [ ] Multi-asset extension
- [ ] Production deployment (small size)

---

## References

**Primary Source**:
Cartea, Álvaro, Sebastian Jaimungal, and José Penalva. *Algorithmic and High-Frequency Trading.* Cambridge University Press, 2015.

**Related Papers**:
- Avellaneda & Stoikov (2008) - Original A-S model
- Guilbaud & Pham (2013) - Limit/Market order optimization
- Cartea & Jaimungal (2015) - Risk metrics for HFT

**NautilusTrader Docs**:
- Strategy Development Guide
- Order Book Analytics
- Backtesting Framework

---

## File Locations

**Main Output**:
```
/media/sam/1TB/nautilus_dev/docs/research/cartea_mm_implementation.md
```

**Source PDF**:
```
/media/sam/1TB/nautilus_dev/docs/research/books/Algorithmic and High-Frequency Trading (Mathematics, Finance -- Álvaro Cartea.pdf
```

**This Summary**:
```
/media/sam/1TB/nautilus_dev/docs/research/cartea_extraction_summary.md
```

---

**Extraction Complete**: All market making concepts from Cartea's book successfully extracted and mapped to NautilusTrader implementation.
