#!/usr/bin/env python3
"""Generate diagnostic tasks from backtest failure analysis.

Converts analysis.json from analyze_backtest_failure.py into tasks.md
format suitable for SpecKit workflows and GitHub issue creation.

Usage:
    python generate_diagnostic_tasks.py --analysis-file analysis.json --output tasks.md
    python generate_diagnostic_tasks.py --analysis-file analysis.json --strategy MyStrategy
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def severity_to_priority(severity: str) -> str:
    """Map severity to priority marker."""
    mapping = {
        "critical": "[P0]",
        "high": "[P1]",
        "medium": "[P2]",
        "low": "[P3]",
    }
    return mapping.get(severity.lower(), "[P2]")


def generate_diagnostic_tasks(
    analysis: dict[str, Any],
    strategy: str,
) -> str:
    """Generate tasks.md from analysis results."""
    failure_type = analysis.get("failure_type", "unknown")
    severity = analysis.get("severity", "medium")
    root_cause = analysis.get("root_cause", "Unknown")
    diagnostic_steps = analysis.get("diagnostic_steps", [])
    errors = analysis.get("errors", [])
    confidence = analysis.get("confidence", 0.5)

    priority = severity_to_priority(severity)

    lines = [
        f"# Diagnostic Tasks: {strategy} Backtest Failure",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        "",
        f"- **Strategy**: {strategy}",
        f"- **Failure Type**: {failure_type}",
        f"- **Severity**: {severity}",
        f"- **Confidence**: {confidence:.0%}",
        "",
        "### Root Cause",
        "",
        f"> {root_cause}",
        "",
        "## User Stories",
        "",
        "### US1: Diagnose Root Cause",
        "",
        "As a developer, I want to understand the root cause of the backtest failure",
        "so that I can implement an appropriate fix.",
        "",
        "### US2: Implement Fix",
        "",
        "As a developer, I want to fix the identified issue",
        "so that the backtest runs successfully.",
        "",
        "### US3: Prevent Recurrence",
        "",
        "As a developer, I want to add safeguards",
        "so that this type of failure is caught earlier.",
        "",
        "## Tasks",
        "",
        "### Phase 1: Investigation",
        "",
    ]

    task_id = 1

    # Add diagnostic step tasks
    for step in diagnostic_steps:
        lines.append(f"- [ ] T{task_id:03d} [US1] {priority} {step}")
        task_id += 1

    # Add error analysis task if errors present
    if errors:
        lines.append("")
        lines.append(
            f"- [ ] T{task_id:03d} [US1] {priority} Analyze {len(errors)} error(s) in logs"
        )
        task_id += 1

        # Add specific error investigation tasks for first 3 errors
        for error in errors[:3]:
            message = error.get("message", "")[:60]
            file_path = error.get("file_path", "")
            if file_path:
                lines.append(f"  - File: `{file_path}`")
            lines.append(f"  - Error: {message}...")

    lines.extend(
        [
            "",
            "### Phase 2: Implementation",
            "",
            f"- [ ] T{task_id:03d} [US2] {priority} Implement fix based on diagnosis",
        ]
    )
    task_id += 1

    lines.append(f"- [ ] T{task_id:03d} [US2] [P2] Write unit test for fix")
    task_id += 1

    lines.append(f"- [ ] T{task_id:03d} [US2] [P2] Run backtest to verify fix")
    task_id += 1

    lines.extend(
        [
            "",
            "### Phase 3: Prevention",
            "",
            f"- [ ] T{task_id:03d} [US3] [P3] Add logging/monitoring for this failure mode",
        ]
    )
    task_id += 1

    lines.append(f"- [ ] T{task_id:03d} [US3] [P3] Update documentation if needed")
    task_id += 1

    # Add alpha-debug task for complex failures
    if failure_type in ["code_error", "position_error", "indicator_error"]:
        lines.append(
            f"- [ ] T{task_id:03d} [US3] [P2] [E] Run alpha-debug for deeper analysis"
        )
        task_id += 1

    lines.extend(
        [
            "",
            "## Error Details",
            "",
        ]
    )

    # Add error details section
    if errors:
        for i, error in enumerate(errors[:5], 1):
            message = error.get("message", "Unknown")
            file_path = error.get("file_path", "")
            line_num = error.get("line_number", 0)
            timestamp = error.get("timestamp", "")

            lines.append(f"### Error {i}")
            lines.append("")
            lines.append("```")
            lines.append(message)
            lines.append("```")
            if file_path:
                location = f"`{file_path}`"
                if line_num:
                    location += f" (line {line_num})"
                lines.append(f"- Location: {location}")
            if timestamp:
                lines.append(f"- Time: {timestamp}")
            lines.append("")
    else:
        lines.append("No specific errors extracted from logs.")
        lines.append("")

    lines.extend(
        [
            "## Legend",
            "",
            "- `[P0]` Critical priority - immediate attention",
            "- `[P1]` High priority - fix before merge",
            "- `[P2]` Medium priority - fix in this sprint",
            "- `[P3]` Low priority - nice to have",
            "- `[E]` Needs algorithmic/evolve approach",
            "",
            "---",
            "*Auto-generated by generate_diagnostic_tasks.py*",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate diagnostic tasks from failure analysis"
    )
    parser.add_argument(
        "--analysis-file",
        type=Path,
        required=True,
        help="Path to analysis.json",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="unknown",
        help="Strategy name",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for tasks.md",
    )

    args = parser.parse_args()

    if not args.analysis_file.exists():
        print(f"Error: Analysis file not found: {args.analysis_file}")
        exit(1)

    # Load analysis
    analysis = json.loads(args.analysis_file.read_text())

    # Use strategy from analysis if not provided
    strategy = args.strategy
    if strategy == "unknown" and "strategy" in analysis:
        strategy = analysis["strategy"]

    print(f"Generating diagnostic tasks for: {strategy}")

    # Generate tasks
    content = generate_diagnostic_tasks(analysis, strategy)

    # Write output
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content)
        print(f"Generated tasks.md: {args.output}")

        # Count tasks
        task_count = content.count("- [ ] T")
        print(f"Total tasks: {task_count}")
    else:
        print(content)


if __name__ == "__main__":
    main()
