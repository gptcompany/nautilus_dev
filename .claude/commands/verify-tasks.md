# /verify-tasks - Auto-verify and Update tasks.md Files

Verifies task completion status by checking if referenced files/functions exist. Auto-updates `[ ]` to `[x]` when implementation is detected.

## Usage

```
/verify-tasks                    # Verify all specs
/verify-tasks spec-008           # Verify specific spec
/verify-tasks --dry-run          # Show changes without applying
/verify-tasks --commit           # Auto-commit updates
```

## Workflow

Execute the following steps:

### Step 1: Discover tasks.md Files

Find all tasks.md files:
```bash
find /media/sam/1TB/nautilus_dev/specs -name "tasks.md" -type f
```

If `$ARGUMENTS` contains a spec name (e.g., `spec-008`), filter to that spec only.

### Step 2: Parse Pending Tasks

For each tasks.md, extract tasks marked `[ ]` (pending):

```regex
^- \[ \] (T\d+).*?`([^`]+)`
```

This captures:
- Task ID (e.g., T045)
- File path or code reference (e.g., `scripts/alpha_evolve/templates/benchmark.py`)

### Step 3: Verify Implementation

For each pending task, check if the referenced artifact exists:

**File references** (contains `/` or ends with `.py`, `.rs`, `.json`):
- Use `Glob` or `Read` to verify file exists
- If file exists AND has substantial content (>10 lines), mark as implemented

**Function/class references** (e.g., `_extract_metrics()`):
- Use `Grep` to search for function definition in the spec's target directory
- If found, mark as implemented

**Test references** (starts with `test_` or `Write test`):
- Search in `tests/` directory for matching test function
- If test exists and is not skipped, mark as implemented

### Step 4: Generate Report

Output verification report:

```markdown
## Task Verification Report

### Spec: {spec_name}

| Task | Description | File/Function | Status | Action |
|------|-------------|---------------|--------|--------|
| T045 | Create benchmark script | `benchmark.py` | EXISTS | Mark [x] |
| T046 | Verify overhead < 5% | benchmark output | MANUAL | Skip |

### Summary
- Total pending: {count}
- Auto-verified: {verified_count}
- Manual review needed: {manual_count}

### Files to Update
- specs/008-alpha-evolve-templates/tasks.md (2 changes)
```

### Step 5: Apply Updates (unless --dry-run)

For each verified task:

1. Read the tasks.md file
2. Replace `- [ ] T{ID}` with `- [x] T{ID}`
3. Write updated file

Use the Edit tool:
```
old_string: "- [ ] T045"
new_string: "- [x] T045"
```

### Step 6: Commit Changes (if --commit)

```bash
git add specs/*/tasks.md
git commit -m "chore: Auto-verify completed tasks

Tasks verified by /verify-tasks command.
Implementation files confirmed to exist.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

## Verification Logic

### File Exists Check
```python
# If task mentions a file path
if "/" in reference or reference.endswith((".py", ".rs", ".json")):
    # Check if file exists and has content
    exists = glob(reference) or read(reference)
    implemented = exists and line_count > 10
```

### Function Exists Check
```python
# If task mentions a function/method
if reference.endswith("()") or "def " in task_description:
    func_name = extract_function_name(reference)
    # Search for definition
    grep_pattern = f"def {func_name}|async def {func_name}"
    implemented = grep_finds_match(pattern, target_dir)
```

### Test Exists Check
```python
# If task is about writing tests
if "test_" in reference or "Write test" in description:
    test_name = extract_test_name(reference)
    # Search in tests directory
    implemented = grep(f"def {test_name}", "tests/")
```

## Edge Cases

1. **Task without file reference**: Mark as MANUAL, skip auto-verify
2. **Multiple files in task**: Verify ALL files exist before marking complete
3. **Partial implementation**: Do NOT mark complete if file exists but function missing
4. **Deleted files**: If task marked [x] but file missing, WARN but don't change

## Examples

```
/verify-tasks
# Output:
## Task Verification Report
### Spec: 008-alpha-evolve-templates
- T045: benchmark.py EXISTS → Mark [x]
- T046: overhead check MANUAL → Skip

Updated: specs/008-alpha-evolve-templates/tasks.md (1 change)
```

```
/verify-tasks spec-004 --dry-run
# Shows what would change without applying
```

```
/verify-tasks --commit
# Verifies all specs and commits changes
```

## Integration

After running `/verify-tasks`, you can:
- Run `/speckit.analyze` to check cross-artifact consistency
- Run git push to share updated task status
