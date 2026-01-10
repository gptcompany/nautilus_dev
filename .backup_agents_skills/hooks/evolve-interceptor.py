#!/usr/bin/env python3
"""
PreToolUse Hook: Intercept Write/Edit for [E] tasks.

When Claude attempts to write code for a task marked with [E],
this hook blocks the operation and instructs Claude to spawn
alpha-evolve instead for multi-implementation exploration.

Flow:
1. Intercept Write/Edit/MultiEdit operations
2. Check if target file corresponds to a [E] task in tasks.md
3. If yes AND alpha-evolve not already active → block and instruct
4. If alpha-evolve is active → allow (it's doing its job)
"""

import json
import os
import re
import sys
from pathlib import Path

# State file created by auto-alpha-debug.py when spawning alpha-evolve
EVOLVE_STATE_FILE = "alpha_evolve_state.json"


def get_project_dir() -> Path:
    """Get the project directory from environment."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))


def is_evolve_active() -> bool:
    """Check if alpha-evolve is currently running."""
    state_file = get_project_dir() / ".claude" / "stats" / EVOLVE_STATE_FILE

    if not state_file.exists():
        return False

    try:
        data = json.loads(state_file.read_text())
        return data.get("active", False)
    except (OSError, json.JSONDecodeError):
        return False


def find_all_evolve_tasks() -> list[dict]:
    """Find ALL [E] marked tasks across all specs.

    Returns list of {file: str, task: str, spec: str} dicts.
    Checks all specs, not just the most recent one.
    """
    specs_dir = get_project_dir() / "specs"

    if not specs_dir.exists():
        return []

    tasks_files = list(specs_dir.glob("*/tasks.md"))
    if not tasks_files:
        return []

    all_evolve_tasks = []

    for tasks_file in tasks_files:
        try:
            content = tasks_file.read_text()
            spec_name = tasks_file.parent.name

            # Find lines with [E] marker that are unchecked
            for line in content.split("\n"):
                if "[E]" in line and "- [ ]" in line:
                    # Extract file path from task description
                    match = re.search(
                        r"[`\"']([^`\"']+\.(?:py|js|ts|tsx|rs|go|java|rb|php|swift|scala|c|cpp|h))[`\"']",
                        line,
                    )
                    if match:
                        file_path = match.group(1)
                        all_evolve_tasks.append(
                            {
                                "file": file_path,
                                "task": line.strip(),
                                "spec": spec_name,
                            }
                        )
        except (OSError, PermissionError):
            continue

    return all_evolve_tasks


def file_matches_task(file_path: str, task_file: str) -> bool:
    """Check if the file being written matches a task's target file."""
    file_path_lower = file_path.lower()
    task_file_lower = task_file.lower()

    # Exact match
    if file_path_lower.endswith(task_file_lower):
        return True

    # Basename match
    file_basename = Path(file_path).name.lower()
    task_basename = Path(task_file).name.lower()
    if file_basename == task_basename:
        return True

    # Partial path match (task_file is suffix of file_path)
    if task_file_lower in file_path_lower:
        return True

    return False


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({}))
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only intercept Write/Edit/MultiEdit
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        print(json.dumps({}))
        sys.exit(0)

    # If alpha-evolve is already active, allow the write
    if is_evolve_active():
        print(json.dumps({}))
        sys.exit(0)

    # Get the file being written
    file_path = tool_input.get("file_path", "")
    if not file_path:
        print(json.dumps({}))
        sys.exit(0)

    # Get ALL [E] tasks from ALL specs
    all_evolve_tasks = find_all_evolve_tasks()
    if not all_evolve_tasks:
        print(json.dumps({}))
        sys.exit(0)

    # Check if file matches any [E] task
    matching_task = None
    for task in all_evolve_tasks:
        if file_matches_task(file_path, task["file"]):
            matching_task = task
            break

    if not matching_task:
        # Not an [E] task, allow the write
        print(json.dumps({}))
        sys.exit(0)

    # Block the write and instruct to use alpha-evolve
    spec_dir = matching_task["spec"]
    response = {
        "decision": "block",
        "reason": f"""
╔══════════════════════════════════════════════════════════════════╗
║  [E] TASK DETECTED - SPAWN ALPHA-EVOLVE                         ║
╚══════════════════════════════════════════════════════════════════╝

Target file: {file_path}
Spec: {spec_dir}

Matching [E] task:
{matching_task["task"]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[E] tasks require MULTI-IMPLEMENTATION EXPLORATION.

Instead of writing directly, spawn the **alpha-evolve** subagent:

```
Use Task tool with subagent_type="alpha-evolve"
```

Alpha-Evolve will:
1. Read spec context from {spec_dir}/
2. Generate 3 different implementation approaches
3. Test each approach for correctness
4. Evaluate performance and code quality
5. Select best approach (or create ensemble)
6. Write the winning implementation

DO NOT write directly to this file.
Spawn alpha-evolve now with this task context.
""",
    }

    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
