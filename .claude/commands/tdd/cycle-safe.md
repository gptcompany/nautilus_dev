# Safe TDD Cycle Command

Execute TDD cycle with automatic checkpointing and rollback protection.

## Command
`/tdd:cycle-safe [--auto-checkpoint] [--rollback-on-failure]`

## Description
Enhanced version of `/tdd:cycle` that includes automatic checkpoint creation and rollback capabilities. Provides safety net for TDD development by creating restore points at each phase.

## Safety Features
- Automatic checkpoint before each TDD phase
- Rollback capability if any phase fails
- Validation of TDD phase transitions
- Recovery suggestions when things go wrong
- Integration with ccundo for granular control

## Parameters
- `--auto-checkpoint`: Create checkpoints automatically (default: true)
- `--rollback-on-failure`: Auto-rollback if phase fails (default: prompt)

## Enhanced TDD Process

### Phase 1: Red (with Safety)
1. Create checkpoint: "pre_red_phase"
2. Generate or verify failing tests
3. Validate tests fail for correct reasons
4. Create checkpoint: "red_phase_complete"
5. If failure: Offer rollback options

### Phase 2: Green (with Safety)
1. Create checkpoint: "pre_green_phase"
2. Implement minimal code to pass tests
3. Validate all tests pass
4. Create checkpoint: "green_phase_complete"
5. If failure: Offer rollback to Red phase

### Phase 3: Refactor (with Safety)
1. Create checkpoint: "pre_refactor_phase"
2. Improve code quality
3. Validate tests still pass
4. Create checkpoint: "refactor_complete"
5. If failure: Offer rollback to Green phase

## Example Execution

### Successful Cycle
```
/tdd:cycle-safe

🔴 RED PHASE - Creating failing tests
📍 Checkpoint: pre_red_phase_issue_123
⚡ Running: /tdd:spec-to-test
✅ Tests generated: 5 failing tests
📍 Checkpoint: red_phase_complete_issue_123

🟢 GREEN PHASE - Implementing solution
📍 Checkpoint: pre_green_phase_issue_123
⚡ Implementing minimal solution...
✅ Implementation complete: All tests passing
📍 Checkpoint: green_phase_complete_issue_123

🔵 REFACTOR PHASE - Improving quality
📍 Checkpoint: pre_refactor_phase_issue_123
⚡ Refactoring for better code quality...
✅ Refactoring complete: Tests still passing
📍 Checkpoint: refactor_complete_issue_123

🎉 TDD Cycle Complete!
📊 Result: 5 tests passing, code quality improved
📍 Final checkpoint: tdd_cycle_complete_issue_123
```

### Cycle with Green Phase Failure
```
/tdd:cycle-safe

🔴 RED PHASE - Creating failing tests
📍 Checkpoint: pre_red_phase_issue_123
✅ Red phase complete: 5 failing tests

🟢 GREEN PHASE - Implementing solution
📍 Checkpoint: pre_green_phase_issue_123
⚡ Implementing solution...
❌ Implementation failed: 2 tests still failing

🛟 Recovery Options:
1. 🔄 Try different implementation approach
2. ⬅️  Rollback to Red phase (recommended)
3. 🔍 Debug current implementation
4. 📝 Update test requirements

? Select recovery action: 2

✅ Rolled back to Red phase
🔴 Ready to retry Green implementation
📍 Current state: red_phase_complete_issue_123
```

### Cycle with Refactor Failure
```
🔵 REFACTOR PHASE - Improving quality
📍 Checkpoint: pre_refactor_phase_issue_123
⚡ Refactoring...
❌ Refactor failed: Tests broken after changes

🛟 Recovery Options:
1. ⬅️  Rollback to Green phase (recommended)
2. 🔍 Debug refactoring changes
3. 🔄 Try different refactoring approach
4. 📋 Skip refactoring (keep Green state)

? Select recovery action: 1

✅ Rolled back to Green phase
🟢 All tests passing, ready to retry refactor
📍 Current state: green_phase_complete_issue_123
```

## Auto-Rollback Mode
```
/tdd:cycle-safe --rollback-on-failure

🔴 RED PHASE
✅ Complete

🟢 GREEN PHASE
❌ Failed: Tests still failing
🔄 Auto-rollback to Red phase...
✅ Restored to Red phase

💡 Suggestion: Review test requirements or try different approach
```

## Checkpoint Management
All checkpoints are automatically named with:
- Phase identifier (red/green/refactor)
- Issue number (if available)
- Timestamp
- Success/failure status

Example names:
- `red_phase_complete_issue_123_20240922_2045`
- `green_phase_failed_issue_123_20240922_2050`
- `refactor_complete_issue_123_20240922_2055`

## Error Recovery Strategies

### Red Phase Issues
- Tests don't fail: Suggest reviewing test logic
- No tests generated: Offer to run `/tdd:spec-to-test`
- Test syntax errors: Provide debugging guidance

### Green Phase Issues
- Tests still failing: Offer rollback to Red
- New tests breaking: Suggest implementation review
- Performance issues: Recommend profiling

### Refactor Phase Issues
- Tests breaking: Offer rollback to Green
- Code quality decrease: Suggest different approach
- Complexity increase: Recommend simplification

## Integration Benefits
- Works with existing `/tdd:*` commands
- Maintains Taskmaster task tracking
- Compatible with TDD-Guard enforcement
- Provides granular undo/redo capabilities
- Supports team collaboration through checkpoints

## Advanced Options
```
# Custom checkpoint naming
/tdd:cycle-safe --checkpoint-prefix="feature_auth"

# Skip specific phases
/tdd:cycle-safe --skip-refactor

# Dry run mode
/tdd:cycle-safe --dry-run

# Verbose logging
/tdd:cycle-safe --verbose
```

## Related Commands
- `/tdd:cycle` - Standard TDD cycle without safety features
- `/tdd:rollback-red` - Quick rollback to Red phase
- `/undo:checkpoint` - Manual checkpoint creation
- `/undo:list` - View all available rollback points