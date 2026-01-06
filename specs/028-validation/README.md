# Spec 028: Validation Phase

**Status**: VALIDATION COMPLETE - Specs Derived
**Date**: 2026-01-04 to 2026-01-06
**Methodology**: PMW (Prove Me Wrong) + SWOT Cross-Validation
**Last Updated**: 2026-01-06

## Purpose

This folder contains the **validation research** that produced the roadmap for specs 029-037.
It is NOT a spec itself, but the research foundation that identified gaps and requirements.

---

## Derived Specs (Implementation)

**Official Mapping**: See `gaps_to_specs_mapping.md` for canonical gap-to-spec reference.

### Completed (Implemented)
- [x] **spec-029-baseline-validation** - From `baseline_comparison.md`
- [x] **spec-030-audit-trail** - From `risk_analysis.md` (audit requirements)

### Specified (Ready for Implementation)
- [x] **spec-031-csrc-correlation** - Gap #2: Correlation-Aware Allocation (8h)
- [x] **spec-032-adts-discounting** - Gap #3: Adaptive Thompson Sampling Decay (6h)
- [x] **spec-033-strategic-controller** - Gap #1 + #7: Level 3 Controller + WF Integration (16h)
- [x] **spec-034-kelly-criterion** - Gap #4: Kelly Criterion Portfolio Integration (4h)
- [x] **spec-035-transaction-cost** - Gap #5: Transaction Cost Model (6h)
- [x] **spec-036-regime-ensemble** - Gap #8: BOCD Regime Ensemble Voting (8h)
- [x] **spec-037-long-short-separation** - From `cross_validation_metalabeling.md` JFDS (4h)

### Deferred
- [ ] **Gap #6: MAML Meta-Learning** (16h) - Only if evolution too slow (post paper trading)

---

## Timeline Alignment (from action_items.md)

### Day 0 (Critical Fixes)
- Direct code fixes (API mismatch, NaN guards) - no spec needed

### Week 1 (Paper Trading Start)
- spec-031 CSRC Correlation (HIGH, 8h)
- spec-032 ADTS Discounting (HIGH, 6h)

### Week 2-3 (Paper Trading)
- spec-033 Strategic Controller (HIGH, 12h)
- spec-033 Walk-Forward Integration (merged, 8h)
- spec-034 Kelly Criterion (MED, 4h)
- spec-035 Transaction Cost (MED, 6h)

### Post Paper Trading
- spec-036 BOCD Regime Ensemble (MED, 8h)
- Gap #6 MAML (DEFERRED, 16h)

---

## File Status

### ACTIVE (Source for specs)
| File | Purpose | Used By |
|------|---------|---------|
| `gap_analysis.md` | 8 gaps with priorities | spec-031 to 036 |
| `gaps_to_specs_mapping.md` | Canonical gap→spec mapping | All specs |
| `action_items.md` | Concrete tasks and timeline | Implementation |
| `final_verdict.md` | Decision tree, red lines | All specs |

### CONSUMED (Work completed)
| File | Purpose | Consumed By |
|------|---------|-------------|
| `baseline_comparison.md` | Baseline validation design | spec-029 |
| `research_plan_swot.md` | Research methodology | Executed |
| `research_attack_plan.md` | P5 validation plan | P5 removed from CLAUDE.md |

### REFERENCE (Documentation)
| File | Purpose |
|------|---------|
| `counter_evidence_academic.md` | Academic critiques (DeMiguel, Bailey, etc.) |
| `counter_evidence_practitioner.md` | Failure case studies (LTCM, Knight, etc.) |
| `alternative_architectures.md` | 1/N vs complex analysis |
| `cross_validation_metalabeling.md` | JFDS alignment (4.5/8) - source for spec-037 |
| `community_issues_analysis.md` | Discord issues affecting our stack |
| `stress_test_scenarios.md` | Future stress test scenarios |
| `swot_analysis.md` | Complete SWOT synthesis |
| `risk_analysis.md` | 27 issues identified in codebase |
| `research_vs_repos_analysis.md` | Analysis that led to P5 removal |
| `dilla_framework_insight.md` | Creative insight (Moroder/Dilla) |
| `extreme_edge_discovery_report.md` | Edge case discovery |
| `extreme_edge_discovery_prompt.md` | Discovery protocol template |
| `session_prompt_swot.md` | SWOT session template |
| `executive_summary.md` | Quick summary |

---

## Key Findings Summary

### Critical Gaps Addressed (from gap_analysis.md)
| Gap # | Gap | Criticality | Spec |
|-------|-----|-------------|------|
| 1 | Level 3 Strategic Controller | HIGH | 033 |
| 2 | CSRC Correlation Penalty | HIGH | 031 |
| 3 | ADTS Adaptive Discounting | HIGH | 032 |
| 4 | Kelly Criterion | MED | 034 |
| 5 | Transaction Cost Model | MED | 035 |
| 6 | MAML Meta-Learning | MED | DEFERRED |
| 7 | Walk-Forward OOS Integration | MED | (in 033) |
| 8 | BOCD Regime Ensemble | MED | 036 |

### Verdict (from final_verdict.md)
- **Status**: WAIT (was 1 critical bug, now fixed)
- **Confidence**: 45% +/- 15%
- **Red Lines**: 1/N beats complex → STOP, turnover >500% → STOP

### Philosophy Updates (from research_vs_repos_analysis.md)
- P5 "Leggi Naturali" REMOVED - No academic evidence for Fibonacci/Gann
- Fractals (Mandelbrot) remain valid under P2 "Non Lineare"

---

## Usage

When creating new specs from this validation:
1. Check `gaps_to_specs_mapping.md` for canonical mapping
2. Read `gap_analysis.md` for the specific gap details
3. Check `final_verdict.md` for acceptance criteria
4. Reference `counter_evidence_*.md` for risks to address
5. Use `stress_test_scenarios.md` for test cases
6. Follow `action_items.md` for implementation timeline

---

## Revision History

| Date | Change |
|------|--------|
| 2026-01-04 | Initial validation research completed |
| 2026-01-05 | action_items.md finalized with timeline |
| 2026-01-06 | specs 031-037 created from gaps |
| 2026-01-06 | spec-034 added (was missing Gap #4) |
| 2026-01-06 | gaps_to_specs_mapping.md created |
| 2026-01-06 | README aligned with all documents |
