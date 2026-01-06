---
description: Automated SpecKit pipeline orchestrator - from feature description to validated tasks with research and NT compatibility checks.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Overview

This skill automates the entire SpecKit workflow with intelligent decision-making and validation checkpoints:

1. `/speckit:specify` - Create specification
2. **DECISION**: Research needed? (domain complexity analysis)
3. `/research` - Academic paper search (if needed)
4. **PMW VALIDATION**: Prove Me Wrong analysis (counter-evidence + SWOT)
5. `/speckit:plan` - Create implementation plan
6. **VALIDATE**: NT nightly compatibility check
7. `/speckit:tasks` - Generate task breakdown
8. `/speckit:analyze` - Cross-validate artifacts
9. **VALIDATE**: Final NT compatibility check
10. **REPORT**: Summary with validation results

## Execution Flow

### Phase 1: Specification Creation

1. **Invoke `/speckit:specify`** with user input:
   ```
   Run: /speckit:specify $ARGUMENTS
   ```

2. **Wait for completion** - spec.md created and validated

3. **Extract feature context**:
   - Read spec.md to understand domain and technical needs
   - Identify key concepts for decision tree

### Phase 2: Research Decision (Intelligence Layer)

**DECISION TREE**: Analyze spec.md content for research signals.

**Research LIKELY NEEDED if spec contains**:
- **Domain keywords**: "adaptive", "regime", "sizing", "indicator", "signal", "threshold", "optimization", "machine learning", "ML", "AI"
- **Academic concepts**: "Sharpe ratio", "drawdown", "walk-forward", "cross-validation", "backtesting", "statistical"
- **Complex algorithms**: "Thompson Sampling", "Bayesian", "ensemble", "clustering", "factor model"
- **Trading methodology**: "momentum", "mean reversion", "arbitrage", "market making"

**Research LIKELY NOT NEEDED if spec contains**:
- **Infrastructure keywords**: "config", "logging", "CLI", "cache", "Redis", "graceful shutdown", "monitoring"
- **UI/UX work**: "dashboard", "chart", "visualization", "frontend", "React", "UI component"
- **DevOps/tooling**: "Docker", "deployment", "CI/CD", "testing framework", "linting"
- **Simple CRUD**: "create", "read", "update", "delete" (without complex logic)

**Implementation**:
```python
# Pseudo-code for decision logic
spec_content = read("spec.md").lower()

research_keywords = [
    "adaptive", "regime", "sizing", "indicator", "signal",
    "optimization", "machine learning", "sharpe", "drawdown",
    "thompson", "bayesian", "momentum", "mean reversion"
]

infrastructure_keywords = [
    "config", "logging", "cli", "cache", "redis",
    "monitoring", "docker", "deployment", "testing"
]

research_score = sum(1 for kw in research_keywords if kw in spec_content)
infra_score = sum(1 for kw in infrastructure_keywords if kw in spec_content)

if research_score >= 3 and research_score > infra_score:
    needs_research = True
elif research_score >= 1 and "baseline" in spec_content:
    needs_research = True  # Baseline validation ALWAYS needs research
else:
    needs_research = False
```

**Execute Decision**:
- If `needs_research == True`:
  1. Extract main topic from spec.md (look for Overview/Goals section)
  2. Run `/research {topic}`
  3. Wait for research.md to be generated
  4. Proceed to Phase 3

- If `needs_research == False`:
  1. Report: "Research phase skipped (infrastructure/simple feature)"
  2. Proceed to Phase 3 (skip PMW)

### Phase 2b: PMW Validation (Prove Me Wrong)

> **"Cerca attivamente disconferme, non conferme"**
> Reference: CLAUDE.md Validation Philosophy

**Purpose**: Before proceeding with implementation, actively search for counter-evidence that could invalidate the approach.

**PMW Protocol**:

1. **Counter-Evidence Search**:
   ```
   # Instead of searching "{topic} works"
   Search: "{topic} failure", "{topic} poor performance", "{topic} limitations"

   # Example queries:
   - "Thompson Sampling non-stationary failure"
   - "regime detection out of sample poor performance"
   - "position sizing overfitting backtest"
   ```

2. **Academic Critique Search**:
   - Search arXiv/SSRN for papers that CONTRADICT the approach
   - Look for failure stories in practitioner literature
   - Check for simpler alternatives that might work better

3. **SWOT Assessment**:
   ```markdown
   **Strengths**: What actually works well?
   **Weaknesses**: Where are we vulnerable?
   **Opportunities**: What could we improve?
   **Threats**: What could make us fail?
   ```

4. **Mitigations Check**:
   - For each threat/weakness identified, verify spec addresses it
   - Document unaddressed risks

5. **Verdict**:
   - **GO**: Proceed with implementation (solid foundation)
   - **WAIT**: Fix identified issues before proceeding
   - **STOP**: Rethink the approach entirely

**Output**: Add PMW section to `research.md`:
```markdown
## PMW (Prove Me Wrong) Analysis

### Counter-Evidence Search
**Query**: "{disconfirmation query}"
**Findings**: [list of potential issues found]

### Mitigations in Spec
- [x] Mitigation 1 (addresses threat X)
- [ ] Mitigation 2 (NOT addressed - RISK)

### SWOT Assessment
**Strengths**: ...
**Weaknesses**: ...
**Opportunities**: ...
**Threats**: ...

### Verdict: GO/WAIT/STOP
```

**Handle PMW Results**:
- **GO**: Proceed to Phase 3
- **WAIT**:
  1. Present issues to user
  2. Update spec.md with mitigations
  3. Re-run PMW validation
- **STOP**:
  1. Present fundamental issues
  2. Recommend alternative approaches
  3. Ask user how to proceed

### Phase 3: Implementation Planning

1. **Invoke `/speckit:plan`**:
   ```
   Run: /speckit:plan
   ```

2. **Wait for completion** - plan.md created with research integration

### Phase 4: NT Nightly Validation (Checkpoint 1)

**Purpose**: Verify plan is compatible with NautilusTrader nightly before task generation.

**Delegate to subagent**:
```python
# Spawn nautilus-docs-specialist for validation
Task(
    subagent_type="nautilus-docs-specialist",
    prompt="""Validate plan.md for NautilusTrader nightly compatibility.

VALIDATION CHECKLIST:
1. Read: specs/{spec-id}/plan.md
2. Extract all NautilusTrader components mentioned:
   - Classes used (e.g., BacktestNode, Strategy, Indicator)
   - APIs called (e.g., ParquetDataCatalog, submit_order)
   - Data formats (e.g., Parquet schema, Bar types)
3. Check Context7 for nightly version compatibility:
   - Are all classes/APIs available in nightly?
   - Any breaking changes in recent nightly commits?
   - Any deprecated features being used?
4. Check docs/discord/ for community issues:
   - grep -r "{component_name}" docs/discord/
   - Recent bugs or workarounds?
5. Return VALIDATION REPORT:
   - ✅ PASS: All components compatible
   - ⚠️  WARNINGS: List any deprecations or known issues
   - ❌ FAIL: List incompatible components with alternatives

Be specific - quote plan sections and provide exact class/API names.
"""
)
```

**Handle validation results**:
- **PASS**: Proceed to Phase 5
- **WARNINGS**: Log warnings, ask user if they want to proceed or fix
- **FAIL**:
  1. Present incompatibilities to user
  2. Offer to update plan.md with alternatives
  3. Re-run validation after fixes
  4. Max 2 fix iterations, then ask user for manual review

### Phase 5: Task Generation

1. **Invoke `/speckit:tasks`**:
   ```
   Run: /speckit:tasks
   ```

2. **Wait for completion** - tasks.md created

### Phase 6: Cross-Artifact Analysis

1. **Invoke `/speckit:analyze`**:
   ```
   Run: /speckit:analyze
   ```

2. **Wait for analysis report**

3. **Handle findings**:
   - **CRITICAL issues**: STOP and report to user
   - **HIGH issues**: Recommend fixes before implementation
   - **MEDIUM/LOW**: Log for awareness, proceed

### Phase 7: Final NT Validation (Checkpoint 2)

**Purpose**: Verify tasks.md references valid NT components and file paths.

**Delegate to subagent**:
```python
# Spawn nautilus-docs-specialist for final validation
Task(
    subagent_type="nautilus-docs-specialist",
    prompt="""Final NautilusTrader validation for tasks.md.

VALIDATION CHECKLIST:
1. Read: specs/{spec-id}/tasks.md
2. Extract all task file paths:
   - strategies/*, config/*, tests/*
3. Verify file paths match NT project structure:
   - strategies/production/ (not strategies/deployed/)
   - config/cache/ (for Redis configs)
   - tests/integration/ (for backtest tests)
4. Check for common anti-patterns:
   - df.iterrows() usage
   - Custom indicator implementations (should use native Rust)
   - Memory-loading large datasets (should use streaming)
5. Return VALIDATION REPORT:
   - ✅ PASS: All tasks follow NT best practices
   - ⚠️  WARNINGS: List any anti-patterns with fixes
   - ❌ FAIL: List violations requiring task updates

Focus on NautilusTrader-specific issues, not general Python style.
"""
)
```

**Handle validation results**:
- **PASS**: Proceed to Phase 8
- **WARNINGS**: Log warnings, offer to fix in tasks.md
- **FAIL**:
  1. Present violations to user
  2. Offer to update tasks.md
  3. Re-run validation
  4. Max 2 fix iterations

### Phase 8: Final Report

Generate comprehensive summary report:

```markdown
# SpecKit Pipeline Report

**Feature**: {feature_name}
**Branch**: {branch_name}
**Generated**: {timestamp}

## Pipeline Execution Summary

| Phase | Status | Duration | Notes |
|-------|--------|----------|-------|
| Specification | ✅ COMPLETE | 2m 15s | 3 clarifications resolved |
| Research Decision | ✅ EXECUTED | 30s | Research triggered (domain: adaptive sizing) |
| Academic Research | ✅ COMPLETE | 5m 20s | 8 papers found, 3 relevant |
| Implementation Plan | ✅ COMPLETE | 3m 45s | Research integrated |
| NT Validation 1 | ✅ PASS | 1m 30s | All components compatible |
| Task Generation | ✅ COMPLETE | 2m 10s | 42 tasks generated |
| Cross-Artifact Analysis | ⚠️  WARNINGS | 1m 20s | 2 MEDIUM issues (see below) |
| NT Validation 2 | ✅ PASS | 1m 15s | Best practices followed |

**Total Time**: 17m 25s

## Research Summary

**Topic**: {research_topic}
**Papers Found**: {count}
**Key Findings**:
- {finding_1}
- {finding_2}
- {finding_3}

**Papers Downloaded**: {list_of_pdfs}

## Validation Results

### NT Compatibility Check 1 (Post-Plan)
- ✅ All NautilusTrader APIs compatible with nightly
- ⚠️  1 deprecation warning: {warning}

### Cross-Artifact Analysis
- **Requirements Coverage**: 95% (38/40 requirements have tasks)
- **Critical Issues**: 0
- **High Issues**: 0
- **Medium Issues**: 2
  - M1: Terminology drift between spec and plan ({details})
  - M2: Missing non-functional test coverage for performance

### NT Compatibility Check 2 (Post-Tasks)
- ✅ All file paths follow NT structure
- ✅ No anti-patterns detected
- ⚠️  1 optimization suggestion: {suggestion}

## Generated Artifacts

- **Specification**: `specs/{spec-id}/spec.md`
- **Research**: `specs/{spec-id}/research.md` (if applicable)
- **Plan**: `specs/{spec-id}/plan.md`
- **Tasks**: `specs/{spec-id}/tasks.md`
- **Analysis Report**: (shown above)

## Next Steps

1. **Review warnings** above before proceeding
2. **Run implementation**:
   ```bash
   /speckit:implement
   ```
3. **Monitor progress** with task-master

## Quality Gates Passed

- [x] Spec validation complete
- [x] Research integrated (if applicable)
- [x] NT nightly compatibility verified
- [x] No critical cross-artifact issues
- [x] All tasks follow NT best practices

---

**Pipeline Status**: READY FOR IMPLEMENTATION ✅
```

**Report output**:
- Display in conversation
- Save to `specs/{spec-id}/pipeline-report.md` for reference

## Error Handling

**If any phase fails**:
1. **Stop pipeline** immediately
2. **Report failure** with exact error
3. **Provide recovery options**:
   - Retry current phase
   - Skip phase (if non-critical)
   - Manual intervention required
4. **Save progress** - don't lose completed phases

**Example error handling**:
```
Phase 4: NT Validation FAILED
Error: BacktestNode.run() deprecated in nightly v1.223.0

Recovery Options:
1. Update plan.md to use BacktestNode.execute() instead
2. Skip validation and proceed (NOT RECOMMENDED)
3. Manual review of plan.md

Your choice: _
```

## Operating Principles

### Context Efficiency
- **Delegate to subagents** for all file analysis (never read docs in main context)
- **Use skills** for complex workflows (research, validation)
- **Progressive disclosure** - load artifacts only when needed
- **Parallel execution** - run independent validations in parallel

### Quality Assurance
- **Multiple validation checkpoints** prevent issues before implementation
- **NT-specific checks** ensure compatibility with nightly version
- **Cross-artifact validation** ensures consistency
- **Research integration** grounds plans in academic evidence

### User Experience
- **Clear progress indicators** at each phase
- **Actionable warnings** with fix suggestions
- **Transparent decision-making** (explain why research triggered)
- **Comprehensive final report** for documentation

## Usage Examples

### Example 1: Trading Strategy (Research Triggered)

```
User: /spec-pipeline Implement Thompson Sampling for adaptive position sizing

Pipeline:
1. ✅ Specify: spec.md created
2. 🔍 Research: TRIGGERED (keywords: "Thompson Sampling", "adaptive", "sizing")
   - Topic: "Thompson Sampling non-stationary bandits position sizing"
   - Papers: 8 found, 3 relevant
3. ✅ Plan: research.md integrated into plan.md
4. ✅ NT Validation 1: PASS
5. ✅ Tasks: 42 tasks generated
6. ✅ Analyze: No critical issues
7. ✅ NT Validation 2: PASS
8. 📊 Report: READY FOR IMPLEMENTATION
```

### Example 2: Infrastructure Feature (Research Skipped)

```
User: /spec-pipeline Add Redis cache backend for TradingNode state persistence

Pipeline:
1. ✅ Specify: spec.md created
2. ⏭️  Research: SKIPPED (infrastructure feature)
3. ✅ Plan: plan.md created
4. ✅ NT Validation 1: PASS
5. ✅ Tasks: 18 tasks generated
6. ✅ Analyze: 1 MEDIUM issue (terminology drift)
7. ✅ NT Validation 2: PASS
8. 📊 Report: READY FOR IMPLEMENTATION
```

### Example 3: Baseline Validation (Always Research)

```
User: /spec-pipeline Validate adaptive sizing against fixed 2% baseline

Pipeline:
1. ✅ Specify: spec.md created
2. 🔍 Research: TRIGGERED (keyword: "baseline" → academic validation)
   - Topic: "baseline validation portfolio optimization out of sample"
   - Papers: 12 found, 5 relevant (DeMiguel 2009, Bailey 2014)
3. ✅ Plan: DSR, PBO metrics integrated
4. ⚠️  NT Validation 1: WARNING (1 deprecation)
   - Fixed: Updated plan to use new API
5. ✅ Tasks: 38 tasks generated
6. ⚠️  Analyze: 2 MEDIUM issues
7. ✅ NT Validation 2: PASS
8. 📊 Report: READY FOR IMPLEMENTATION
```

## Requirements

**Skills**:
- `/speckit:specify` - Specification creation
- `/speckit:plan` - Implementation planning
- `/speckit:tasks` - Task generation
- `/speckit:analyze` - Cross-artifact validation
- `/research` - Academic paper search

**Subagents**:
- `nautilus-docs-specialist` - NT nightly validation

**Prerequisites**:
- `.specify/` directory exists
- Constitution.md exists (for spec creation)
- NautilusTrader nightly environment active

## Notes

- **This skill is the recommended entry point** for all new features
- **Replaces manual workflow** of running each skill separately
- **Saves time** by automating decisions and validations
- **Ensures quality** through multiple checkpoints
- **Documents process** with comprehensive final report

## Integration with Existing Workflows

**Before spec-pipeline**:
```bash
/speckit:specify "my feature"
# ... wait ...
# ... decide if research needed ...
/research "my topic"  # maybe?
# ... wait ...
/speckit:plan
# ... wait ...
# ... manually check NT compatibility ...
/speckit:tasks
# ... wait ...
/speckit:analyze
# ... wait ...
# ... manually verify tasks ...
```

**After spec-pipeline**:
```bash
/spec-pipeline "my feature"
# ✅ All done, ready to implement
```
