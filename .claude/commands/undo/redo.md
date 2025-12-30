---
allowed-tools: Bash, Read
---

# Undo Redo

Redo previously undone operations with TDD/Task context.

## Usage
```
/undo:redo [operation_id]
```

## Instructions

### 1. Check for Undone Operations
```bash
echo "🔄 Checking for redoable operations..."
ccundo list --all | grep -i "undone" || echo "No undone operations found"
```

### 2. Show Available Redo Operations
If no operation_id provided, show options:
```bash
echo ""
echo "📋 Available operations for redo:"
ccundo list --all | head -15
```

### 3. Preview Redo Operation
```bash
# Preview what will be redone
if [ -n "$ARGUMENTS" ]; then
    echo ""
    echo "🔍 Preview of redo operation:"
    ccundo preview "$ARGUMENTS"
else
    echo ""
    echo "🔍 Preview of most recent undone operation:"
    # Get most recent undone operation and preview it
    RECENT_UNDONE=$(ccundo list --all | grep -i "undone" | head -1 | awk '{print $1}')
    if [ -n "$RECENT_UNDONE" ]; then
        ccundo preview "$RECENT_UNDONE"
    else
        echo "No undone operations to preview"
    fi
fi
```

### 4. Check TDD/Task Context
Analyze context from redo preview:
- Look for test files (*.test.js, *.spec.*, test_*.py)
- Look for task references (#123, task_)
- Look for TDD phase implications

### 5. Get User Confirmation
```
🎯 Redo Confirmation:
   Operation: {operation_description}

⚠️  TDD Impact: {analyze_tdd_context}
📋 Task Impact: {analyze_task_context}

Continue with redo? (y/N)
```

### 6. Execute Redo
If confirmed:
```bash
# Execute redo operation
if [ -n "$ARGUMENTS" ]; then
    ccundo redo "$ARGUMENTS"
else
    # Redo most recent undone operation
    RECENT_UNDONE=$(ccundo list --all | grep -i "undone" | head -1 | awk '{print $1}')
    if [ -n "$RECENT_UNDONE" ]; then
        ccundo redo "$RECENT_UNDONE"
    else
        echo "❌ No operation to redo"
        exit 1
    fi
fi
```

### 7. Verify Post-Redo State
```bash
echo ""
echo "✅ Redo operation completed"
echo ""
echo "📊 Current session state:"
ccundo list | head -5
```

### 8. TDD Integration
If TDD context detected:
```bash
# Check if we should run tests
if ccundo list | grep -q "test\|spec"; then
    echo ""
    echo "🧪 TDD Context: Consider running tests to verify state"
    echo "💡 Use '/tdd:green' or appropriate test command"
fi
```

### 9. Task Integration
If task context detected:
```bash
# Check for task context
if git branch --show-current | grep -E "task|#[0-9]+" > /dev/null; then
    ISSUE_NUM=$(git branch --show-current | grep -oE '#?[0-9]+' | head -1)
    echo ""
    echo "📋 Task Context: Working on task $ISSUE_NUM"
    echo "💡 Consider updating task progress if needed"
fi
```

### 10. Error Handling
- If no undone operations: Suggest checking `/undo:list`
- If operation not found: List available operations
- If conflicts detected: Offer preview and resolution options