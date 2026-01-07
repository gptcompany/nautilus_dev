#!/usr/bin/env python3
"""Convert alpha-debug findings to tasks.md and GitHub issues.

Parses alpha-debug output from log files or stdin, extracts bug findings,
and converts them to tasks.md format suitable for SpecKit workflows.
Optionally creates GitHub issues directly.

Usage:
    # From log file
    python alpha_debug_to_tasks.py --input debug.log --output specs/bugs/tasks.md

    # From stdin (pipe from alpha-debug)
    cat debug_output.txt | python alpha_debug_to_tasks.py --output tasks.md

    # Create GitHub issues directly
    python alpha_debug_to_tasks.py --input debug.log --create-issues
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class BugFinding:
    """Represents a bug found by alpha-debug."""

    id: str
    round_number: int
    category: str  # A: Logic, B: Edge, C: Integration, D: Smell
    severity: str  # critical, high, medium, low
    description: str
    file_path: str = ""
    line_number: int = 0
    fix_applied: bool = False
    fix_description: str = ""
    hypothesis: str = ""
    verification: str = ""


@dataclass
class AlphaDebugReport:
    """Parsed alpha-debug session report."""

    session_id: str
    timestamp: str
    total_rounds: int
    bugs_found: list[BugFinding] = field(default_factory=list)
    bugs_fixed: int = 0
    final_confidence: float = 0.0
    stop_reason: str = ""
    target_files: list[str] = field(default_factory=list)


def parse_alpha_debug_output(content: str) -> AlphaDebugReport:
    """Parse alpha-debug output and extract findings."""
    report = AlphaDebugReport(
        session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
        timestamp=datetime.now().isoformat(),
        total_rounds=0,
    )

    bug_id = 1
    current_round = 0
    current_hypotheses: list[str] = []

    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Parse round header
        round_match = re.match(r"=+\s*ROUND\s+(\d+)/(\d+)\s*=+", line)
        if round_match:
            current_round = int(round_match.group(1))
            report.total_rounds = max(report.total_rounds, int(round_match.group(2)))
            i += 1
            continue

        # Parse hypotheses section
        if line.startswith("[HYPOTHESIZE]"):
            current_hypotheses = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("["):
                hyp_line = lines[i].strip()
                # Look for numbered hypotheses
                hyp_match = re.match(r"[-*\d.]+\s*(.+)", hyp_line)
                if hyp_match:
                    current_hypotheses.append(hyp_match.group(1))
                i += 1
            continue

        # Parse bug findings
        bug_patterns = [
            (r"BUG\s*FOUND[:\s]+(.+)", "high"),
            (r"ISSUE[:\s]+(.+)", "medium"),
            (r"POTENTIAL\s*BUG[:\s]+(.+)", "medium"),
            (r"ERROR[:\s]+(.+)", "high"),
            (r"FIX(?:ED)?[:\s]+(.+)", "medium"),
        ]

        for pattern, default_severity in bug_patterns:
            bug_match = re.match(pattern, line, re.IGNORECASE)
            if bug_match:
                description = bug_match.group(1).strip()

                # Determine category
                category = determine_category(description)

                # Determine severity
                severity = determine_severity(description, default_severity)

                # Try to extract file path and line
                file_path, line_num = extract_location(description, lines, i)

                finding = BugFinding(
                    id=f"BUG{bug_id:03d}",
                    round_number=current_round,
                    category=category,
                    severity=severity,
                    description=description,
                    file_path=file_path,
                    line_number=line_num,
                    hypothesis=current_hypotheses[0] if current_hypotheses else "",
                )

                report.bugs_found.append(finding)
                bug_id += 1
                break

        # Parse score section
        if line.startswith("[SCORE]"):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("="):
                score_line = lines[i].strip()

                bugs_found_match = re.search(
                    r"Bugs\s*found[:\s]+(\d+)", score_line, re.I
                )
                if bugs_found_match:
                    pass  # Already tracking individually

                bugs_fixed_match = re.search(
                    r"Bugs\s*fixed[:\s]+(\d+)", score_line, re.I
                )
                if bugs_fixed_match:
                    report.bugs_fixed = int(bugs_fixed_match.group(1))

                confidence_match = re.search(
                    r"Confidence[:\s]+(\d+(?:\.\d+)?)", score_line, re.I
                )
                if confidence_match:
                    report.final_confidence = float(confidence_match.group(1))

                i += 1
            continue

        # Parse stop reason
        stop_patterns = [
            r"STOP(?:PING)?[:\s]+(.+)",
            r"MAX\s*ROUNDS\s*REACHED",
            r"CLEAN\s*ROUNDS[:\s]+(\d+)",
            r"CONFIDENCE[:\s]+(\d+)%?\s*>=\s*(\d+)",
        ]

        for pattern in stop_patterns:
            stop_match = re.search(pattern, line, re.I)
            if stop_match:
                report.stop_reason = line
                break

        i += 1

    return report


def determine_category(description: str) -> str:
    """Determine bug category from description."""
    desc_lower = description.lower()

    # Category A: Logic Errors
    logic_keywords = [
        "off-by-one",
        "incorrect",
        "wrong",
        "logic",
        "comparison",
        "null",
        "none",
        "division",
        "calculation",
    ]
    if any(kw in desc_lower for kw in logic_keywords):
        return "A"

    # Category B: Edge Cases
    edge_keywords = [
        "empty",
        "boundary",
        "edge",
        "zero",
        "negative",
        "overflow",
        "underflow",
        "unicode",
    ]
    if any(kw in desc_lower for kw in edge_keywords):
        return "B"

    # Category C: Integration Issues
    integration_keywords = [
        "api",
        "integration",
        "type",
        "mismatch",
        "race",
        "resource",
        "leak",
        "connection",
    ]
    if any(kw in desc_lower for kw in integration_keywords):
        return "C"

    # Category D: Code Smells
    smell_keywords = [
        "unused",
        "duplicate",
        "complexity",
        "naming",
        "import",
        "dead code",
    ]
    if any(kw in desc_lower for kw in smell_keywords):
        return "D"

    return "A"  # Default to logic


def determine_severity(description: str, default: str) -> str:
    """Determine bug severity from description."""
    desc_lower = description.lower()

    if any(kw in desc_lower for kw in ["critical", "crash", "data loss", "security"]):
        return "critical"
    if any(kw in desc_lower for kw in ["error", "exception", "fail", "broken"]):
        return "high"
    if any(kw in desc_lower for kw in ["warning", "potential", "might"]):
        return "medium"
    if any(kw in desc_lower for kw in ["minor", "cosmetic", "style"]):
        return "low"

    return default


def extract_location(
    description: str, lines: list[str], current_idx: int
) -> tuple[str, int]:
    """Try to extract file path and line number from context."""
    # Check description for file:line pattern
    file_match = re.search(r"([a-zA-Z0-9_/.-]+\.py)(?::(\d+))?", description)
    if file_match:
        return file_match.group(1), int(file_match.group(2) or 0)

    # Check nearby lines for file references
    for offset in range(-5, 6):
        idx = current_idx + offset
        if 0 <= idx < len(lines):
            line = lines[idx]
            file_match = re.search(
                r"File[:\s]+[`'\"]?([a-zA-Z0-9_/.-]+\.py)[`'\"]?", line
            )
            if file_match:
                line_match = re.search(r"line\s+(\d+)", line, re.I)
                return file_match.group(1), int(
                    line_match.group(1) if line_match else 0
                )

    return "", 0


def severity_to_priority(severity: str) -> str:
    """Map severity to priority marker."""
    mapping = {
        "critical": "[P0]",
        "high": "[P1]",
        "medium": "[P2]",
        "low": "[P3]",
    }
    return mapping.get(severity, "[P2]")


def category_to_label(category: str) -> str:
    """Map category to human-readable label."""
    mapping = {
        "A": "Logic Error",
        "B": "Edge Case",
        "C": "Integration Issue",
        "D": "Code Smell",
    }
    return mapping.get(category, "Unknown")


def generate_tasks_md(report: AlphaDebugReport) -> str:
    """Generate tasks.md from alpha-debug report."""
    lines = [
        "# Bug Fix Tasks from Alpha-Debug",
        "",
        f"Generated: {report.timestamp}",
        f"Session: {report.session_id}",
        "",
        "## Summary",
        "",
        f"- Total Rounds: {report.total_rounds}",
        f"- Bugs Found: {len(report.bugs_found)}",
        f"- Bugs Fixed: {report.bugs_fixed}",
        f"- Final Confidence: {report.final_confidence}%",
        f"- Stop Reason: {report.stop_reason}",
        "",
        "## User Stories",
        "",
        "### US1: Fix Alpha-Debug Findings",
        "",
        "As a developer, I want all bugs identified by alpha-debug to be fixed",
        "so that the codebase is more robust and reliable.",
        "",
        "## Tasks",
        "",
    ]

    # Sort bugs by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_bugs = sorted(
        report.bugs_found,
        key=lambda b: severity_order.get(b.severity, 2),
    )

    for i, bug in enumerate(sorted_bugs, 1):
        priority = severity_to_priority(bug.severity)
        category_label = category_to_label(bug.category)
        status = "[X]" if bug.fix_applied else "[ ]"

        task_line = f"- {status} T{i:03d} [US1] {priority} [{category_label}] Fix: {bug.description}"
        lines.append(task_line)

        if bug.file_path:
            lines.append(
                f"  - File: `{bug.file_path}`"
                + (f" (line {bug.line_number})" if bug.line_number else "")
            )

        if bug.hypothesis:
            lines.append(f"  - Hypothesis: {bug.hypothesis[:100]}...")

    lines.extend(
        [
            "",
            "## Legend",
            "",
            "- `[P0]` Critical priority",
            "- `[P1]` High priority",
            "- `[P2]` Medium priority",
            "- `[P3]` Low priority",
            "",
            "### Categories",
            "",
            "- `[Logic Error]` Category A: Off-by-one, comparisons, null checks",
            "- `[Edge Case]` Category B: Empty inputs, boundary values",
            "- `[Integration Issue]` Category C: API contracts, type mismatches",
            "- `[Code Smell]` Category D: Unused code, complexity",
            "",
            "---",
            "*Auto-generated by alpha_debug_to_tasks.py*",
        ]
    )

    return "\n".join(lines)


def create_github_issue(
    bug: BugFinding, spec_dir: str, dry_run: bool = False
) -> int | None:
    """Create a GitHub issue for a bug finding."""
    title = f"BUG-{bug.id}: {bug.description[:60]}..."

    body_parts = [
        "## Bug Finding from Alpha-Debug",
        "",
        f"**ID**: {bug.id}",
        f"**Category**: {category_to_label(bug.category)}",
        f"**Severity**: {bug.severity}",
        f"**Round**: {bug.round_number}",
        "",
        "### Description",
        bug.description,
        "",
    ]

    if bug.file_path:
        body_parts.extend(
            [
                "### Location",
                f"- File: `{bug.file_path}`",
                f"- Line: {bug.line_number}" if bug.line_number else "",
                "",
            ]
        )

    if bug.hypothesis:
        body_parts.extend(
            [
                "### Hypothesis",
                bug.hypothesis,
                "",
            ]
        )

    body_parts.extend(
        [
            "### Source",
            f"- Spec: `{spec_dir}`",
            "",
            "---",
            "*Auto-generated by alpha_debug_to_tasks.py*",
        ]
    )

    body = "\n".join(body_parts)

    labels = [
        "bug",
        "alpha-debug",
        f"severity-{bug.severity}",
        f"category-{bug.category.lower()}",
    ]

    if dry_run:
        print(f"[DRY RUN] Would create issue: {title}")
        return None

    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                ",".join(labels),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            # Extract issue number from URL
            match = re.search(r"/issues/(\d+)", result.stdout)
            if match:
                return int(match.group(1))
    except Exception as e:
        print(f"Failed to create issue: {e}")

    return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert alpha-debug findings to tasks.md and GitHub issues"
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Input file (alpha-debug log). If not provided, reads from stdin.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for tasks.md",
    )
    parser.add_argument(
        "--create-issues",
        action="store_true",
        help="Create GitHub issues for each bug",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Write parsed report to JSON file",
    )
    parser.add_argument(
        "--spec-dir",
        type=str,
        default="specs/bugs",
        help="Spec directory for issue references",
    )

    args = parser.parse_args()

    # Read input
    if args.input:
        if not args.input.exists():
            print(f"Error: Input file not found: {args.input}")
            sys.exit(1)
        content = args.input.read_text()
    else:
        content = sys.stdin.read()

    if not content.strip():
        print("Error: No input provided")
        sys.exit(1)

    # Parse alpha-debug output
    print("Parsing alpha-debug output...")
    report = parse_alpha_debug_output(content)

    print(f"Found {len(report.bugs_found)} bugs in {report.total_rounds} rounds")

    # Generate tasks.md
    if args.output:
        tasks_content = generate_tasks_md(report)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(tasks_content)
        print(f"Generated tasks.md: {args.output}")

    # Create GitHub issues
    if args.create_issues:
        print(f"Creating GitHub issues (dry_run={args.dry_run})...")
        created = 0
        for bug in report.bugs_found:
            if not bug.fix_applied:  # Only create issues for unfixed bugs
                issue_num = create_github_issue(bug, args.spec_dir, args.dry_run)
                if issue_num:
                    created += 1
                    print(f"  Created issue #{issue_num} for {bug.id}")
        print(f"Created {created} issues")

    # Write JSON report
    if args.output_json:
        json_data: dict[str, Any] = {
            "session_id": report.session_id,
            "timestamp": report.timestamp,
            "total_rounds": report.total_rounds,
            "bugs_found": len(report.bugs_found),
            "bugs_fixed": report.bugs_fixed,
            "final_confidence": report.final_confidence,
            "stop_reason": report.stop_reason,
            "findings": [
                {
                    "id": bug.id,
                    "round": bug.round_number,
                    "category": bug.category,
                    "severity": bug.severity,
                    "description": bug.description,
                    "file_path": bug.file_path,
                    "line_number": bug.line_number,
                    "fix_applied": bug.fix_applied,
                }
                for bug in report.bugs_found
            ],
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(json_data, indent=2))
        print(f"JSON report: {args.output_json}")


if __name__ == "__main__":
    main()
