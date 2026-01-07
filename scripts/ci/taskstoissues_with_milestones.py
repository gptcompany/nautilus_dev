#!/usr/bin/env python3
"""Convert tasks.md to GitHub issues with milestone support.

Parses tasks.md, creates milestones per user story, and generates
GitHub issues with proper labels, assignments, and cross-references.

Usage:
    python taskstoissues_with_milestones.py --tasks-file specs/001/tasks.md --spec-dir specs/001
    python taskstoissues_with_milestones.py --tasks-file tasks.md --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Task:
    """Represents a single task from tasks.md."""

    id: str
    story: str
    description: str
    status: str  # "pending" or "completed"
    priority: str = "P2"
    markers: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class UserStory:
    """Represents a user story section."""

    id: str
    title: str
    description: str
    tasks: list[Task] = field(default_factory=list)


@dataclass
class SyncResult:
    """Results from sync operation."""

    milestones_created: int = 0
    milestones_existing: int = 0
    issues_created: int = 0
    issues_existing: int = 0
    issues_updated: int = 0
    errors: list[str] = field(default_factory=list)


def parse_tasks_file(file_path: Path) -> tuple[list[UserStory], list[Task]]:
    """Parse tasks.md and extract user stories and tasks."""
    content = file_path.read_text()
    lines = content.split("\n")

    user_stories: list[UserStory] = []
    all_tasks: list[Task] = []
    current_story: UserStory | None = None

    # Regex patterns
    story_pattern = re.compile(r"^###?\s*(US\d+)[:\s]+(.+)$")
    task_pattern = re.compile(
        r"^\s*-\s*\[([ X])\]\s*(T\d+)\s*(\[US\d+\])?\s*((?:\[[^\]]+\]\s*)*)\s*(.+)$"
    )
    file_pattern = re.compile(r"^\s+-\s*File:\s*`(.+)`$")

    for i, line in enumerate(lines, 1):
        # Check for user story header
        story_match = story_pattern.match(line)
        if story_match:
            story_id = story_match.group(1)
            story_title = story_match.group(2).strip()

            # Look for description in next lines
            description = ""
            for j in range(i, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if next_line and not next_line.startswith("#") and not next_line.startswith("-"):
                    description = next_line
                    break

            current_story = UserStory(
                id=story_id,
                title=story_title,
                description=description,
            )
            user_stories.append(current_story)
            continue

        # Check for task
        task_match = task_pattern.match(line)
        if task_match:
            status = "completed" if task_match.group(1) == "X" else "pending"
            task_id = task_match.group(2)
            story_ref = task_match.group(3) or ""
            markers_str = task_match.group(4) or ""
            description = task_match.group(5).strip()

            # Parse markers
            markers = re.findall(r"\[([^\]]+)\]", markers_str)
            priority = "P2"
            for marker in markers:
                if marker.startswith("P") and marker[1:].isdigit():
                    priority = marker
                    break

            # Determine story association
            story_id = ""
            if story_ref:
                story_id = story_ref.strip("[]")
            elif current_story:
                story_id = current_story.id

            task = Task(
                id=task_id,
                story=story_id,
                description=description,
                status=status,
                priority=priority,
                markers=markers,
                line_number=i,
            )

            all_tasks.append(task)
            if current_story:
                current_story.tasks.append(task)
            continue

        # Check for file reference (sub-item of task)
        file_match = file_pattern.match(line)
        if file_match and all_tasks:
            all_tasks[-1].files.append(file_match.group(1))

    return user_stories, all_tasks


def run_gh_command(args: list[str], check: bool = True) -> tuple[int, str, str]:
    """Run a gh CLI command and return result."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr
    except FileNotFoundError:
        return 1, "", "gh CLI not found"


def get_existing_milestones() -> dict[str, int]:
    """Get existing milestones and their numbers."""
    code, stdout, _ = run_gh_command(
        ["api", "repos/{owner}/{repo}/milestones", "-q", ".[].title,.number"],
        check=False,
    )
    if code != 0:
        return {}

    milestones = {}
    lines = stdout.strip().split("\n")
    for i in range(0, len(lines) - 1, 2):
        if lines[i] and lines[i + 1]:
            milestones[lines[i]] = int(lines[i + 1])
    return milestones


def get_existing_issues() -> dict[str, int]:
    """Get existing issues with task IDs in title."""
    code, stdout, _ = run_gh_command(
        ["issue", "list", "--state", "all", "--limit", "500", "--json", "number,title"],
        check=False,
    )
    if code != 0:
        return {}

    issues = {}
    try:
        data = json.loads(stdout) if stdout else []
        for issue in data:
            # Extract task ID from title
            match = re.search(r"(T\d+)", issue.get("title", ""))
            if match:
                issues[match.group(1)] = issue["number"]
    except json.JSONDecodeError:
        pass
    return issues


def create_milestone(story: UserStory, spec_dir: str, dry_run: bool = False) -> int | None:
    """Create a GitHub milestone for a user story."""
    title = f"{story.id}: {story.title}"
    description = f"{story.description}\n\nSpec: {spec_dir}"

    if dry_run:
        print(f"[DRY RUN] Would create milestone: {title}")
        return None

    code, stdout, stderr = run_gh_command(
        [
            "api",
            "repos/{owner}/{repo}/milestones",
            "--method",
            "POST",
            "-f",
            f"title={title}",
            "-f",
            "state=open",
            "-f",
            f"description={description}",
            "-q",
            ".number",
        ],
        check=False,
    )

    if code == 0 and stdout:
        return int(stdout.strip())
    return None


def create_issue(
    task: Task,
    spec_dir: str,
    milestone_num: int | None,
    dry_run: bool = False,
) -> int | None:
    """Create a GitHub issue for a task."""
    title = f"{task.id}: {task.description}"

    # Build body
    body_parts = [
        "## Task Details",
        "",
        f"**Task ID**: {task.id}",
        f"**User Story**: {task.story}",
        f"**Priority**: {task.priority}",
        "",
    ]

    if task.markers:
        body_parts.append(f"**Markers**: {', '.join(task.markers)}")
        body_parts.append("")

    if task.files:
        body_parts.append("### Files")
        for f in task.files:
            body_parts.append(f"- `{f}`")
        body_parts.append("")

    body_parts.extend(
        [
            "### Source",
            f"- Spec: `{spec_dir}/spec.md`",
            f"- Tasks: `{spec_dir}/tasks.md` (line {task.line_number})",
            "",
            "---",
            "*Auto-generated by Development Loop workflow*",
        ]
    )

    body = "\n".join(body_parts)

    # Determine labels
    labels = ["auto-generated", f"priority-{task.priority.lower()}"]
    if "E" in task.markers:
        labels.append("evolve")
    if "P" in task.markers:
        labels.append("parallelizable")

    if dry_run:
        print(f"[DRY RUN] Would create issue: {title}")
        print(f"  Labels: {labels}")
        if milestone_num:
            print(f"  Milestone: {milestone_num}")
        return None

    # Build command
    cmd = [
        "issue",
        "create",
        "--title",
        title,
        "--body",
        body,
    ]

    for label in labels:
        cmd.extend(["--label", label])

    if milestone_num:
        cmd.extend(["--milestone", str(milestone_num)])

    code, stdout, stderr = run_gh_command(cmd, check=False)

    if code == 0:
        # Extract issue number from URL
        match = re.search(r"/issues/(\d+)", stdout)
        if match:
            return int(match.group(1))
    else:
        print(f"Failed to create issue for {task.id}: {stderr}")

    return None


def sync_tasks_to_issues(
    stories: list[UserStory],
    tasks: list[Task],
    spec_dir: str,
    dry_run: bool = False,
) -> SyncResult:
    """Sync tasks to GitHub issues with milestones."""
    result = SyncResult()

    # Get existing milestones and issues
    existing_milestones = get_existing_milestones()
    existing_issues = get_existing_issues()

    # Create milestones for each user story
    milestone_map: dict[str, int | None] = {}

    for story in stories:
        milestone_title = f"{story.id}: {story.title}"

        if milestone_title in existing_milestones:
            milestone_map[story.id] = existing_milestones[milestone_title]
            result.milestones_existing += 1
            print(f"Milestone exists: {milestone_title}")
        else:
            milestone_num = create_milestone(story, spec_dir, dry_run)
            milestone_map[story.id] = milestone_num
            if milestone_num or dry_run:
                result.milestones_created += 1
                print(f"Created milestone: {milestone_title}")

    # Create issues for each pending task
    for task in tasks:
        if task.status == "completed":
            continue  # Skip completed tasks

        if task.id in existing_issues:
            result.issues_existing += 1
            print(f"Issue exists for {task.id}: #{existing_issues[task.id]}")
            continue

        milestone_num = milestone_map.get(task.story)
        issue_num = create_issue(task, spec_dir, milestone_num, dry_run)

        if issue_num or dry_run:
            result.issues_created += 1
            print(f"Created issue for {task.id}: #{issue_num}")

    return result


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert tasks.md to GitHub issues with milestones"
    )
    parser.add_argument(
        "--tasks-file",
        type=Path,
        required=True,
        help="Path to tasks.md file",
    )
    parser.add_argument(
        "--spec-dir",
        type=str,
        default="",
        help="Spec directory path (defaults to tasks-file parent)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making changes",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Write results to JSON file",
    )

    args = parser.parse_args()

    if not args.tasks_file.exists():
        print(f"Error: tasks file not found: {args.tasks_file}")
        exit(1)

    spec_dir = args.spec_dir or str(args.tasks_file.parent)

    print(f"Parsing: {args.tasks_file}")
    print(f"Spec dir: {spec_dir}")
    print(f"Dry run: {args.dry_run}")
    print()

    # Parse tasks
    stories, tasks = parse_tasks_file(args.tasks_file)

    print(f"Found {len(stories)} user stories and {len(tasks)} tasks")
    print()

    # Sync to GitHub
    result = sync_tasks_to_issues(stories, tasks, spec_dir, args.dry_run)

    # Print summary
    print()
    print("=== Sync Summary ===")
    print(f"Milestones created: {result.milestones_created}")
    print(f"Milestones existing: {result.milestones_existing}")
    print(f"Issues created: {result.issues_created}")
    print(f"Issues existing: {result.issues_existing}")

    if result.errors:
        print(f"Errors: {len(result.errors)}")
        for err in result.errors:
            print(f"  - {err}")

    # Write JSON output
    if args.output_json:
        output = {
            "milestones_created": result.milestones_created,
            "milestones_existing": result.milestones_existing,
            "issues_created": result.issues_created,
            "issues_existing": result.issues_existing,
            "issues_updated": result.issues_updated,
            "errors": result.errors,
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(output, indent=2))
        print(f"\nResults written to: {args.output_json}")


if __name__ == "__main__":
    main()
