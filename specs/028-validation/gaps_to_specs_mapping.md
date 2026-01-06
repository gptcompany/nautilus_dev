# Official Mapping: Gaps to Specs

**Created**: 2026-01-06
**Last Updated**: 2026-01-06
**Purpose**: Canonical mapping between gap_analysis.md gaps and spec numbers

---

## Gap Analysis Source

All gaps from: `specs/028-validation/gap_analysis.md`
Action items from: `specs/028-validation/action_items.md`

---

## Mapping Table

| Gap # | Gap Name | Criticality | Effort | Spec # | Spec Name | Status |
|-------|----------|-------------|--------|--------|-----------|--------|
| 1 | Level 3 Strategic Controller | HIGH | 12h | **033** | strategic-controller | SPECIFIED |
| 2 | CSRC Correlation-Aware Allocation | HIGH | 8h | **031** | csrc-correlation | SPECIFIED |
| 3 | ADTS Adaptive Discounting | HIGH | 6h | **032** | adts-discounting | SPECIFIED |
| 4 | Kelly Criterion Integration | MED | 4h | **034** | kelly-criterion | SPECIFIED |
| 5 | Transaction Cost Model | MED | 6h | **035** | transaction-cost | SPECIFIED |
| 6 | MAML Meta-Learning | MED | 16h | - | *not assigned* | DEFERRED |
| 7 | Walk-Forward OOS Integration | MED | 8h | (033) | *merged into 033* | MERGED |
| 8 | BOCD Regime Ensemble | MED | 8h | **036** | regime-ensemble | SPECIFIED |

---

## Additional Specs (Non-Gap Sources)

| Spec # | Spec Name | Source | Status |
|--------|-----------|--------|--------|
| 029 | baseline-validation | `baseline_comparison.md` | SPECIFIED |
| 030 | audit-trail | `risk_analysis.md` | IMPLEMENTED |
| 037 | long-short-separation | `cross_validation_metalabeling.md` (JFDS) | SPECIFIED |

---

## Timeline Alignment (from action_items.md)

### Day 0 (Critical Fixes)
- API fixes, NaN guards - *direct fixes, no spec needed*

### Week 1 (Paper Trading)
- spec-031 CSRC (8h) - HIGH
- spec-032 ADTS (6h) - HIGH

### Week 2-3 (Paper Trading)
- spec-033 Strategic Controller (12h) - HIGH
- spec-033 Walk-Forward Integration (8h) - merged
- spec-035 Transaction Cost (6h) - MED
- **spec-034 Kelly Criterion (4h) - MED** ← NEEDS CREATION

### Post Paper Trading
- spec-036 BOCD Regime (8h) - MED
- Gap #6 MAML (16h) - DEFERRED (only if evolution too slow)

---

## Notes

1. **Gap #4 (Kelly)** was omitted from original README.md - spec-034 now created
2. **Gap #6 (MAML)** intentionally deferred - only implement "if evolution too slow"
3. **Gap #7 (Walk-Forward)** merged into spec-033 as "OOS Integration" component
4. **spec-037** not from gap_analysis - from JFDS cross-validation research

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-01-06 | Initial mapping created | Claude |
| 2026-01-06 | Identified spec-034 missing | Claude |
| 2026-01-06 | spec-034-kelly-criterion created | Claude |
| 2026-01-06 | README.md aligned with all documents | Claude |
