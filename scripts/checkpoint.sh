#!/bin/bash
# Create deployment checkpoint (git tag)
# Usage: ./scripts/checkpoint.sh [NAME]

set -e

NAME=${1:-"deploy-$(date +%Y%m%d-%H%M%S)"}

echo "Creating checkpoint: $NAME"

# Ensure clean state
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: Uncommitted changes exist"
    git status --short
fi

# Create tag
git tag -a "$NAME" -m "Deployment checkpoint: $NAME"

echo "Checkpoint created: $NAME"
echo "To rollback: ./scripts/rollback.sh $NAME"
