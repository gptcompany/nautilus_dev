#!/usr/bin/env python3
"""Generate tasks.md from ImpactReport for breaking change fixes.

Converts ImpactReport JSON (from auto_update analyzer) to tasks.md format
compatible with SpecKit taskstoissues workflow.

Usage:
    python generate_fix_tasks.py --impact-file analysis.json --output tasks.md --version 1.223.0
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load_impact_report(file_path: Path) -> dict[str, Any]:
    """Load ImpactReport JSON from file."""
    with open(file_path) as f:
        data = json.load(f)

    # Handle nested structure
    if "impact_report" in data:
        return data["impact_report"]
    return data


def severity_to_priority(severity: str) -> str:
    """Map severity to task priority marker."""
    mapping = {
        "critical": "[P0]",
        "high": "[P1]",
        "medium": "[P2]",
        "low": "[P3]",
    }
    return mapping.get(severity.lower(), "[P2]")


def can_parallelize(change: dict, all_changes: list[dict]) -> bool:
    """Determine if a change can be fixed in parallel with others."""
    affected_files = set(change.get("affected_files", []))

    for other in all_changes:
        if other == change:
            continue
        other_files = set(other.get("affected_files", []))
        # If files overlap, cannot parallelize
        if affected_files & other_files:
            return False

    return True


def generate_tasks(
    impact_report: dict[str, Any],
    version: str,
) -> list[dict[str, Any]]:
    """Generate task list from impact report."""
    tasks = []
    task_id = 1

    breaking_changes = impact_report.get("breaking_changes", [])

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    breaking_changes.sort(
        key=lambda x: severity_order.get(x.get("severity", "medium").lower(), 2)
    )

    for change in breaking_changes:
        severity = change.get("severity", "medium")
        description = change.get("description", "Unknown change")
        change_type = change.get("type", "unknown")
        affected_files = change.get("affected_files", [])

        priority = severity_to_priority(severity)
        parallel = "[P]" if can_parallelize(change, breaking_changes) else ""

        # Determine if this needs algorithmic fix (mark with [E])
        evolve_marker = ""
        if any(
            kw in description.lower()
            for kw in ["algorithm", "calculation", "formula", "logic"]
        ):
            evolve_marker = "[E]"

        # Create main fix task
        task = {
            "id": f"T{task_id:03d}",
            "story": "[US1]",
            "markers": f"{priority} {parallel} {evolve_marker}".strip(),
            "description": f"Fix: {description}",
            "files": affected_files[:3],  # Limit to first 3 files
            "severity": severity,
            "type": change_type,
        }
        tasks.append(task)
        task_id += 1

        # Create test task for each fix
        test_task = {
            "id": f"T{task_id:03d}",
            "story": "[US1]",
            "markers": f"{priority} [P]",
            "description": f"Test: Verify fix for {description[:50]}...",
            "files": [],
            "severity": severity,
            "type": "test",
        }
        tasks.append(test_task)
        task_id += 1

    # Add final validation task
    tasks.append(
        {
            "id": f"T{task_id:03d}",
            "story": "[US1]",
            "markers": "[P1]",
            "description": f"Validate: Run full test suite against NT {version}",
            "files": [],
            "severity": "high",
            "type": "validation",
        }
    )

    return tasks


def format_tasks_md(
    tasks: list[dict[str, Any]],
    version: str,
    impact_report: dict[str, Any],
) -> str:
    """Format tasks as markdown."""
    lines = [
        f"# Fix Tasks: NautilusTrader {version} Breaking Changes",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        "",
        f"- Breaking Changes: {len(impact_report.get('breaking_changes', []))}",
        f"- Confidence Score: {impact_report.get('confidence_score', 'N/A')}%",
        f"- Total Tasks: {len(tasks)}",
        "",
        "## User Stories",
        "",
        "### US1: Fix Breaking Changes",
        "",
        "As a developer, I want all breaking changes from NT update to be fixed",
        "so that my strategies continue to work correctly.",
        "",
        "## Tasks",
        "",
    ]

    for task in tasks:
        markers = task["markers"]
        task_line = (
            f"- [ ] {task['id']} {task['story']} {markers} {task['description']}"
        )
        lines.append(task_line)

        # Add file references as sub-items
        for file_path in task.get("files", []):
            lines.append(f"  - File: `{file_path}`")

    lines.extend(
        [
            "",
            "## Legend",
            "",
            "- `[P0]` Critical priority",
            "- `[P1]` High priority",
            "- `[P2]` Medium priority",
            "- `[P3]` Low priority",
            "- `[P]` Can be parallelized",
            "- `[E]` Needs algorithmic/evolve approach",
            "",
            "---",
            "*Auto-generated by generate_fix_tasks.py*",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate tasks.md from ImpactReport")
    parser.add_argument(
        "--impact-file",
        type=Path,
        required=True,
        help="Path to ImpactReport JSON file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output path for tasks.md",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="unknown",
        help="NautilusTrader version",
    )

    args = parser.parse_args()

    # Load impact report
    impact_report = load_impact_report(args.impact_file)

    # Generate tasks
    tasks = generate_tasks(impact_report, args.version)

    # Format as markdown
    content = format_tasks_md(tasks, args.version, impact_report)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content)

    print(f"Generated {len(tasks)} tasks in {args.output}")


if __name__ == "__main__":
    main()
