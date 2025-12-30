---
allowed-tools: Bash, Read, Write
---

# Undo Rollback

Safely rollback to a specific operation or checkpoint with preview.

## Usage
```
/undo:rollback [operation_id]
```

## Instructions

### 1. Show Available Operations
If no operation_id provided, list operations:
```bash
echo "🔄 Available operations for rollback:"
ccundo list --all
```

### 2. Preview Rollback Changes
```bash
# Preview specific operation
ccundo preview $ARGUMENTS

# If no operation specified, preview latest
ccundo preview
```

### 3. Check TDD/Task Context
Analyze preview output for context:
- Look for test files (*.test.js, *.spec.*, test_*.py)
- Look for task references (#123, task_)
- Look for TDD phase markers (red_phase_, green_phase_)

### 4. Get User Confirmation
Show preview and ask:
```
🎯 Rollback Preview Summary:
   {summarize_ccundo_preview_output}

⚠️  TDD Context: {detected_context}
📋 Task Context: {detected_task_context}

Continue with rollback? (y/N)
```

### 5. Execute Rollback
If confirmed:
```bash
# Execute rollback (skip confirmation since we already confirmed)
ccundo undo $ARGUMENTS --yes
```

### 6. Verify Post-Rollback State
After rollback:
```bash
# Show current status
echo "✅ Rollback completed"
ccundo list | head -5

# If TDD context detected, run tests
if [detected_test_files]; then
    echo "🧪 Running tests to verify state..."
    # Run appropriate test command based on project
fi
```

### 7. TDD Integration Notes
- If rolling back in TDD context, explain which phase we're returning to
- Suggest next steps (run /tdd:green, /tdd:red, etc.)
- Warn if rollback breaks TDD workflow

### 8. Task Integration Notes
- If rolling back task-related work, mention task number
- Suggest updating task status if needed
- Preserve Epic context awareness