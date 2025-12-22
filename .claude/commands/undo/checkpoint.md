---
allowed-tools: Bash, Read, Write
---

# Undo Checkpoint

Create a semantic reference point for easy rollback to current state.

## Usage
```
/undo:checkpoint [name]
```

## Instructions

### 1. Get Current Session State
```bash
echo "📋 Current session state:"
ccundo list | head -10
```

### 2. Generate Checkpoint Name
If no name provided, create context-aware name:
```bash
# Get current timestamp
TIMESTAMP=$(date +"%Y_%m_%d_%H_%M")

# Check for TDD context (look for test files in recent operations)
TDD_CONTEXT=""
if ccundo list | grep -q "test\|spec"; then
    TDD_CONTEXT="tdd_"
fi

# Check for Task context (look for task references)
ISSUE_CONTEXT=""
if git branch --show-current | grep -E "task|#[0-9]+" > /dev/null; then
    ISSUE_NUM=$(git branch --show-current | grep -oE '#?[0-9]+' | head -1)
    ISSUE_CONTEXT="task_${ISSUE_NUM}_"
fi

# Generate name if not provided
if [ -z "$ARGUMENTS" ]; then
    CHECKPOINT_NAME="${ISSUE_CONTEXT}${TDD_CONTEXT}checkpoint_${TIMESTAMP}"
else
    CHECKPOINT_NAME="$ARGUMENTS"
fi
```

### 3. Document Current State
Create checkpoint reference file:
```bash
# Create checkpoints directory if not exists
mkdir -p .claude/checkpoints

# Document current state
cat > ".claude/checkpoints/${CHECKPOINT_NAME}.md" << EOF
# Checkpoint: ${CHECKPOINT_NAME}

Created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Branch: $(git branch --show-current)

## Session State
$(ccundo list | head -20)

## Git Status
$(git status --porcelain)

## Recent Operations Context
$(ccundo list --all | head -5)
EOF
```

### 4. Show Checkpoint Summary
```bash
echo "✅ Checkpoint created: ${CHECKPOINT_NAME}"
echo ""
echo "📍 Context Information:"
echo "   Branch: $(git branch --show-current)"
echo "   Time: $(date)"
echo ""
echo "🔄 Session Operations:"
ccundo list | head -5
echo ""
echo "💡 To rollback to this point:"
echo "   1. Use '/undo:list' to find the operation ID from this time"
echo "   2. Use '/undo:rollback <operation_id>' to return here"
echo ""
echo "📁 Checkpoint details saved to: .claude/checkpoints/${CHECKPOINT_NAME}.md"
```

### 5. TDD Integration
If TDD context detected:
```bash
if echo "$CHECKPOINT_NAME" | grep -q "tdd"; then
    echo ""
    echo "🧪 TDD Context Detected:"
    echo "   This checkpoint can be used for TDD rollbacks"
    echo "   Consider using '/tdd:rollback-red' for quick TDD rollbacks"
fi
```

### 6. Task Integration
If task context detected:
```bash
if echo "$CHECKPOINT_NAME" | grep -q "task"; then
    echo ""
    echo "📋 Task Context Detected:"
    echo "   Issue: $(git branch --show-current | grep -oE '#?[0-9]+' | head -1)"
    echo "   This checkpoint is linked to current task work"
fi
```

### 7. Create Git Tag (Optional)
For important checkpoints:
```bash
# Ask user if they want to create git tag
echo ""
echo "Create git tag for easy reference? (y/N)"
read -r CREATE_TAG
if [ "$CREATE_TAG" = "y" ] || [ "$CREATE_TAG" = "Y" ]; then
    git tag "checkpoint-${CHECKPOINT_NAME}" -m "Checkpoint: ${CHECKPOINT_NAME}"
    echo "✅ Git tag created: checkpoint-${CHECKPOINT_NAME}"
fi
```