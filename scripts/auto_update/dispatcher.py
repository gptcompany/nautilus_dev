# NautilusTrader Auto-Update Pipeline - Dispatcher

"""Dispatch Claude Code agent for complex fixes."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from scripts.auto_update.models import ImpactReport


def build_task_prompt(
    impact_report: ImpactReport,
    custom_instructions: str | None = None,
) -> str:
    """Build task prompt for Claude Code agent.

    Args:
        impact_report: Impact analysis report
        custom_instructions: Optional custom instructions

    Returns:
        Formatted task prompt string
    """
    lines = [
        "# NautilusTrader Update Task",
        "",
        f"Update NautilusTrader from v{impact_report.previous_version} to v{impact_report.version}.",
        "",
        "## Breaking Changes",
        "",
    ]

    for bc in impact_report.breaking_changes:
        lines.append(f"- **[{bc.severity.value.upper()}]** {bc.description}")
        if bc.migration_guide:
            lines.append(f"  - Migration: {bc.migration_guide}")
        if bc.affected_pattern:
            lines.append(f"  - Pattern: `{bc.affected_pattern}`")

    lines.append("")
    lines.append("## Affected Files")
    lines.append("")

    if impact_report.affected_files:
        for af in impact_report.affected_files:
            line_str = ", ".join(map(str, af.line_numbers[:5]))
            if len(af.line_numbers) > 5:
                line_str += f" (+{len(af.line_numbers) - 5} more)"
            lines.append(f"- `{af.path}` (lines: {line_str})")
    else:
        lines.append("No files directly affected.")

    lines.append("")
    lines.append("## Analysis Summary")
    lines.append("")
    lines.append(f"- **Confidence Score**: {impact_report.confidence_score:.1f}/100")
    lines.append(f"- **Confidence Level**: {impact_report.confidence_level.value}")
    lines.append(f"- **Recommendation**: {impact_report.recommendation.value}")
    lines.append(f"- **Can Auto-Update**: {impact_report.can_auto_update}")

    lines.append("")
    lines.append("## Task")
    lines.append("")
    lines.append("1. Apply necessary code changes to handle breaking changes")
    lines.append("2. Update imports and method calls as needed")
    lines.append("3. Run tests to verify changes work correctly")
    lines.append("4. Commit changes with descriptive message")

    if custom_instructions:
        lines.append("")
        lines.append("## Additional Instructions")
        lines.append("")
        lines.append(custom_instructions)

    return "\n".join(lines)


def dispatch_claude_code(
    impact_report: ImpactReport,
    working_dir: Path,
    timeout: int = 1800,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Dispatch Claude Code CLI to handle complex fixes.

    Args:
        impact_report: Impact analysis report
        working_dir: Working directory for Claude Code
        timeout: Timeout in seconds
        dry_run: If True, don't spawn agent

    Returns:
        Dict with success status and agent info
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "agent_id": None,
            "prompt": build_task_prompt(impact_report),
        }

    prompt = build_task_prompt(impact_report)

    try:
        # Spawn Claude Code CLI with the task
        cmd = [
            "claude",
            "--print",  # Print output
            "-p",  # Prompt mode
            prompt,
        ]

        process = subprocess.Popen(
            cmd,
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        return {
            "success": True,
            "dry_run": False,
            "agent_id": str(process.pid),
            "pid": process.pid,
            "prompt": prompt,
        }

    except FileNotFoundError:
        return {
            "success": False,
            "dry_run": False,
            "error": "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code",
            "agent_id": None,
        }
    except Exception as e:
        return {
            "success": False,
            "dry_run": False,
            "error": str(e),
            "agent_id": None,
        }


def monitor_agent_completion(
    agent_id: str,
    timeout: int = 1800,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Monitor Claude Code agent completion.

    Args:
        agent_id: Agent/process ID to monitor
        timeout: Timeout in seconds
        dry_run: If True, return mock result

    Returns:
        Dict with completion status
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "status": "dry_run",
            "agent_id": agent_id,
        }

    try:
        # Check if process is still running
        # This is a simplified implementation - in production,
        # you'd use the Claude Code API or task tracking
        cmd = ["ps", "-p", str(agent_id)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            # Process still running
            return {
                "success": True,
                "dry_run": False,
                "status": "running",
                "agent_id": agent_id,
            }
        else:
            # Process completed
            return {
                "success": True,
                "dry_run": False,
                "status": "completed",
                "agent_id": agent_id,
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "dry_run": False,
            "status": "timeout",
            "error": f"Monitoring timed out after {timeout}s",
            "agent_id": agent_id,
        }
    except Exception as e:
        return {
            "success": False,
            "dry_run": False,
            "status": "error",
            "error": str(e),
            "agent_id": agent_id,
        }


def get_dispatch_result(
    impact_report: ImpactReport,
) -> dict[str, Any]:
    """Get dispatch result as structured data.

    Args:
        impact_report: Impact report to format

    Returns:
        Dict suitable for DispatchResult model
    """
    return {
        "dispatched": True,
        "agent_id": None,
        "task_prompt": build_task_prompt(impact_report),
        "completion_status": "pending",
        "changes_applied": [],
        "errors": [],
    }
