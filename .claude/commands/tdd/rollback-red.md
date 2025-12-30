# TDD Rollback to Red Phase

Quick rollback to the last Red phase (failing tests) checkpoint.

## Command
`/tdd:rollback-red [--preview] [--auto-confirm]`

## Description
Specialized rollback command for TDD workflow that quickly returns to the last Red phase state. Automatically identifies the most recent checkpoint where tests were failing and implementation was minimal.

## Usage Context
- When Green phase implementation goes wrong
- When refactoring breaks existing functionality
- When you need to try a different implementation approach
- When current code is too complex and needs simplification

## Parameters
- `--preview`: Show what will be changed without executing
- `--auto-confirm`: Skip confirmation if rollback is safe

## TDD Phase Detection
Automatically identifies Red phase checkpoints by:
- Presence of failing tests
- Minimal or no implementation code
- Test coverage matches requirements
- No broken test infrastructure

## Smart Rollback Logic
1. Scan recent history for Red phase markers
2. Identify the most recent stable Red state
3. Verify tests will fail appropriately after rollback
4. Check no critical work will be lost
5. Execute rollback with TDD-specific validation

## Process
1. Analyze current TDD state and history
2. Find most recent Red phase checkpoint
3. Preview changes and impact on TDD workflow
4. Execute rollback using ccundo
5. Verify tests fail as expected
6. Update TDD phase tracking
7. Provide next-step guidance

## Example Usage

### Standard Rollback
```
/tdd:rollback-red

🔍 Analyzing TDD history...

Found Red phase checkpoint: "red_phase_issue_123" (8 minutes ago)

📋 Preview:
   - Will delete: src/auth.js (broken implementation)
   - Will revert: test/auth.test.js (to original failing tests)
   - Will restore: 5 failing test cases

⚠️  Impact:
   - 15 minutes of implementation work will be lost
   - Will return to Red phase (failing tests)
   - Ready to retry Green phase implementation

Continue? (Y/n) Y

✅ Rollback completed!
🔴 TDD State: Red phase (5 tests failing)
📝 Next: Run `/tdd:green` to implement solution
```

### Preview Mode
```
/tdd:rollback-red --preview

📊 Red Phase Rollback Analysis:

🎯 Target: red_phase_issue_123 (8 minutes ago)
   Context: Issue #123 - User Authentication
   State: 5 failing tests, no implementation

📁 Changes Preview:
   [DELETE] src/auth.js
     - function authenticateUser(username, password) {
     -   // Broken implementation with errors
     -   return false; // Always fails
     - }

   [REVERT] test/auth.test.js
     - Will restore original failing tests
     - Tests will fail as expected (Red phase)

🧪 Post-Rollback Test Status:
   ❌ test_valid_credentials_return_true
   ❌ test_invalid_credentials_return_false
   ❌ test_empty_credentials_throw_error
   ❌ test_sql_injection_prevention
   ❌ test_password_hashing_verification

✅ Analysis: Safe rollback to valid Red phase
```

### Auto-Confirm Mode
```
/tdd:rollback-red --auto-confirm

🔄 Auto-rollback to Red phase...
✅ Rollback completed automatically
🔴 TDD State: Red phase ready
📋 5 tests failing as expected
```

## Error Handling

### No Red Phase Found
```
❌ No Red phase checkpoint found

🔍 Analysis:
   - Current session has no clear Red phase markers
   - May be in initial development stage
   - Tests may not be properly structured

💡 Suggestions:
   1. Create tests first with `/tdd:spec-to-test`
   2. Run `/tdd:red` to establish Red phase
   3. Create manual checkpoint with `/undo:checkpoint red_baseline`
```

### Rollback Too Risky
```
⚠️  Rollback blocked: Too much work would be lost

🔍 Analysis:
   - Last Red phase was 4 hours ago
   - 23 file changes since then
   - Multiple issues worked on

💡 Alternatives:
   1. Use `/undo:list` to see other rollback options
   2. Create current checkpoint before rollback
   3. Fix current implementation instead of rolling back
```

### Tests Don't Fail After Rollback
```
❌ Post-rollback validation failed

🔍 Issue:
   - Rollback completed successfully
   - But tests are passing (not Red phase)
   - May indicate test infrastructure problems

💡 Next Steps:
   1. Check test file structure
   2. Verify test assertions are correct
   3. Run `/tdd:red` to diagnose test issues
```

## Integration with Other Commands
- Automatically updates task context in Taskmaster
- Preserves GitHub Issue progress tracking
- Works with `/tdd:green` for next implementation attempt
- Compatible with `/undo:checkpoint` for custom saves

## Success Metrics
- Tests fail after rollback (confirming Red phase)
- Implementation code removed or minimized
- Ready to restart Green phase
- TDD workflow integrity maintained

## Related Commands
- `/tdd:rollback-green` - Rollback to last Green phase
- `/tdd:rollback-stable` - Rollback to last stable state
- `/undo:rollback` - General rollback with more options
- `/tdd:red` - Establish new Red phase if needed