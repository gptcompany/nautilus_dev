#!/usr/bin/env python3
"""Bidirectional sync between tasks.md and GitHub Issues.

Keeps tasks.md checkboxes and GitHub Issues in sync:
- Completed tasks [X] → Close matching Issues
- Closed Issues → Mark [X] in tasks.md

Usage:
    python scripts/sync_tasks_issues.py              # Sync all specs
    python scripts/sync_tasks_issues.py spec-040     # Sync specific spec
    python scripts/sync_tasks_issues.py --dry-run    # Preview changes
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def run_gh(args: list[str], check: bool = True) -> str:
    """Run GitHub CLI command and return output."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=check,
    )
    return result.stdout.strip()


def get_repo_issues(spec_label: str | None = None) -> list[dict]:
    """Get all issues from the repository."""
    query = "is:issue"
    if spec_label:
        query += f" label:{spec_label}"

    try:
        output = run_gh(
            [
                "issue",
                "list",
                "--search",
                query,
                "--state",
                "all",
                "--json",
                "number,title,state,labels",
                "--limit",
                "500",
            ]
        )
        return json.loads(output) if output else []
    except subprocess.CalledProcessError:
        return []


def parse_tasks_md(path: Path) -> dict[str, dict[str, str | bool]]:
    """Parse tasks.md and return task info by ID."""
    tasks: dict[str, dict[str, str | bool]] = {}
    if not path.exists():
        return tasks

    content = path.read_text()
    # Match: - [X] T001 or - [ ] T001
    pattern = r"^- \[([xX ])\] (T\d+)\s+(.+)$"

    for match in re.finditer(pattern, content, re.MULTILINE):
        checkbox, task_id, description = match.groups()
        tasks[task_id] = {
            "id": task_id,
            "completed": checkbox.upper() == "X",
            "description": description.strip(),
            "line": match.group(0),
        }

    return tasks


def extract_task_id_from_issue(title: str) -> str | None:
    """Extract task ID from issue title like '[T001] Description'."""
    match = re.match(r"\[(T\d+)\]", title)
    return match.group(1) if match else None


def sync_spec(spec_dir: Path, dry_run: bool = False) -> dict:
    """Sync a single spec's tasks.md with GitHub Issues."""
    spec_name = spec_dir.name
    tasks_path = spec_dir / "tasks.md"

    if not tasks_path.exists():
        return {"spec": spec_name, "skipped": True, "reason": "No tasks.md"}

    # Get spec number for label
    spec_match = re.match(r"(\d+)-", spec_name)
    spec_label = f"spec-{spec_match.group(1)}" if spec_match else None

    # Parse local tasks
    tasks = parse_tasks_md(tasks_path)
    if not tasks:
        return {"spec": spec_name, "skipped": True, "reason": "No tasks found"}

    # Get GitHub issues
    issues = get_repo_issues(spec_label)
    issue_by_task = {}
    for issue in issues:
        task_id = extract_task_id_from_issue(issue["title"])
        if task_id:
            issue_by_task[task_id] = issue

    issues_closed: list[str] = []
    tasks_marked_complete: list[str] = []

    # Sync: Completed tasks → Close issues
    for task_id, task in tasks.items():
        if task["completed"] and task_id in issue_by_task:
            issue = issue_by_task[task_id]
            if issue["state"] == "OPEN":
                if not dry_run:
                    run_gh(["issue", "close", str(issue["number"])])
                issues_closed.append(f"#{issue['number']} ({task_id})")

    # Sync: Closed issues → Mark tasks complete
    content = tasks_path.read_text()
    modified = False

    for task_id, issue in issue_by_task.items():
        if issue["state"] == "CLOSED" and task_id in tasks:
            task = tasks[task_id]
            if not task["completed"]:
                # Update checkbox in content
                old_line = str(task["line"])
                new_line = old_line.replace("- [ ]", "- [X]")
                content = content.replace(old_line, new_line)
                tasks_marked_complete.append(task_id)
                modified = True

    if modified and not dry_run:
        tasks_path.write_text(content)

    return {
        "spec": spec_name,
        "issues_closed": issues_closed,
        "tasks_marked_complete": tasks_marked_complete,
    }


def main():
    parser = argparse.ArgumentParser(description="Sync tasks.md with GitHub Issues")
    parser.add_argument("spec", nargs="?", help="Specific spec to sync (e.g., spec-040)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    specs_dir = Path("specs")
    if not specs_dir.exists():
        print("Error: specs/ directory not found")
        sys.exit(1)

    # Find specs to sync
    if args.spec:
        spec_dirs = list(specs_dir.glob(f"*{args.spec}*"))
    else:
        spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir() and re.match(r"\d{3}-", d.name)]

    if not spec_dirs:
        print(f"No specs found matching: {args.spec or 'all'}")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Syncing {len(spec_dirs)} spec(s)...\n")

    total_closed = 0
    total_marked = 0

    for spec_dir in sorted(spec_dirs):
        result = sync_spec(spec_dir, dry_run=args.dry_run)

        if result.get("skipped"):
            continue

        issues_closed = result.get("issues_closed", [])
        tasks_marked = result.get("tasks_marked_complete", [])

        if issues_closed or tasks_marked:
            print(f"### {result['spec']}")
            if issues_closed:
                print(f"  Issues closed: {', '.join(issues_closed)}")
                total_closed += len(issues_closed)
            if tasks_marked:
                print(f"  Tasks marked [X]: {', '.join(tasks_marked)}")
                total_marked += len(tasks_marked)
            print()

    print(f"Summary: {total_closed} issues closed, {total_marked} tasks marked complete")

    if args.dry_run:
        print("\n[DRY RUN] No changes applied. Run without --dry-run to apply.")


if __name__ == "__main__":
    main()
