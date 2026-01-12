---
description: NautilusTrader nightly compatibility validation for plan.md
---

# /validate-plan - NT Nightly Compatibility Check

Validates plan.md for NautilusTrader nightly version compatibility.

**Config**: `.claude/validation/config.json` (anti-patterns, keywords, compatibility rules)

## Purpose

Ensures implementation plan uses compatible NT APIs and follows best practices.

## Load Config

```python
config = load(".claude/validation/config.json")
anti_patterns = config["anti_patterns"]
compatibility = config["compatibility_check"]
```

## Validation Checklist

1. **Extract NT Components** from plan.md:
   - Classes used (BacktestNode, Strategy, Indicator)
   - APIs called (ParquetDataCatalog, submit_order)
   - Data formats (Parquet schema, Bar types)

2. **Check Context7 for nightly compatibility**:
   ```
   mcp__context7__get-library-docs(library_name="nautilustrader")
   ```
   - Are all classes/APIs available in nightly?
   - Any breaking changes in recent commits?
   - Any deprecated features being used?

3. **Anti-Patterns Check**:
   - [ ] `df.iterrows()` usage (use vectorized ops)
   - [ ] Custom indicator implementations (use native Rust)
   - [ ] Memory-loading large datasets (use streaming)
   - [ ] Hardcoded paths (use config)

4. **File Path Validation**:
   - `strategies/production/` (not `strategies/deployed/`)
   - `config/cache/` (for Redis configs)
   - `tests/integration/` (for backtest tests)

## Output

Write validation report to `specs/{spec-id}/validation-plan.md`:

```markdown
# NT Compatibility Validation (Plan Phase)

**Date**: {timestamp}
**Spec**: {spec-id}
**NT Version**: v1.222.0 nightly

## Components Checked
| Component | Type | Status | Notes |
|-----------|------|--------|-------|
| BacktestNode | Class | ✅ OK | - |
| ParquetDataCatalog | API | ⚠️ WARN | Deprecated in v1.223 |

## Anti-Patterns
- [x] No df.iterrows() found
- [x] Using native indicators
- [ ] Memory loading detected in data_loader.py

## Verdict: PASS/WARNINGS/FAIL

### Issues Found
- {issue_1}

### Recommendations
- {rec_1}
```

## Verdict Handling

- **PASS**: Continue to Step 5 (tasks)
- **WARNINGS**: Show warnings, ask user to proceed or fix
- **FAIL**: Stop pipeline, show issues, offer fixes
