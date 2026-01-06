# Spec 028: Validation Phase

**Status**: VALIDATION COMPLETE - Specs Derived
**Date**: 2026-01-04 to 2026-01-06
**Methodology**: PMW (Prove Me Wrong) + SWOT Cross-Validation

## Purpose

This folder contains the **validation research** that produced the roadmap for specs 029-037.
It is NOT a spec itself, but the research foundation that identified gaps and requirements.

---

## Derived Specs (Implementation)

### Completed
- [x] **spec-029-baseline-validation** - From `baseline_comparison.md`
- [x] **spec-030-audit-trail** - From `risk_analysis.md` (audit requirements)

### To Create
- [ ] **spec-031-csrc-correlation** - From `gap_analysis.md` Gap #2 (8h)
- [ ] **spec-032-adts-discounting** - From `gap_analysis.md` Gap #3 (6h)
- [ ] **spec-033-strategic-controller** - From `gap_analysis.md` Gap #1 + WF integration (16h)
- [ ] **spec-035-transaction-cost** - From `gap_analysis.md` Gap #5 (6h)
- [ ] **spec-036-regime-ensemble** - From `gap_analysis.md` Gap #8 (8h)
- [ ] **spec-037-long-short-separation** - From `cross_validation_metalabeling.md` (4h)

---

## File Status

### ACTIVE (Source for future specs)
| File | Purpose | Used By |
|------|---------|---------|
| `gap_analysis.md` | Gap table with priorities | spec-031 to 036 |
| `action_items.md` | Specific fix tasks | Direct fixes |
| `final_verdict.md` | Decision tree, red lines | All specs |

### CONSUMED (Work completed)
| File | Purpose | Consumed By |
|------|---------|-------------|
| `baseline_comparison.md` | Baseline validation design | spec-029 |
| `research_plan_swot.md` | Research methodology | Executed |
| `research_attack_plan.md` | P5 validation plan | P5 removed from CLAUDE.md |

### REFERENCE (Keep for documentation)
| File | Purpose |
|------|---------|
| `counter_evidence_academic.md` | Academic critiques (DeMiguel, Bailey, etc.) |
| `counter_evidence_practitioner.md` | Failure case studies (LTCM, Knight, etc.) |
| `alternative_architectures.md` | 1/N vs complex analysis |
| `cross_validation_metalabeling.md` | JFDS alignment (4.5/8) |
| `community_issues_analysis.md` | Discord issues affecting our stack |
| `stress_test_scenarios.md` | Future stress test scenarios |
| `swot_analysis.md` | Complete SWOT synthesis |
| `risk_analysis.md` | 27 issues identified in codebase |
| `research_vs_repos_analysis.md` | Analysis that led to P5 removal |
| `dilla_framework_insight.md` | Creative insight (Moroder/Dilla) |
| `extreme_edge_discovery_report.md` | Edge case discovery |
| `extreme_edge_discovery_prompt.md` | Discovery protocol template |
| `session_prompt_swot.md` | SWOT session template |
| `executive_summary.md` | Quick summary (may need update) |

---

## Key Findings Summary

### Critical Gaps (from gap_analysis.md)
1. **Level 3 Strategic Controller** - No weekly review, evolution gates
2. **CSRC Correlation Penalty** - Over-allocation to correlated strategies
3. **ADTS Adaptive Discounting** - Uniform decay, not regime-adaptive

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
1. Read `gap_analysis.md` for the specific gap details
2. Check `final_verdict.md` for acceptance criteria
3. Reference `counter_evidence_*.md` for risks to address
4. Use `stress_test_scenarios.md` for test cases
