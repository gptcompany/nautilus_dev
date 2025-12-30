# NautilusTrader Auto-Update Pipeline - Git Operations

"""Git operations for creating branches, commits, and PRs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def git_create_branch(
    branch_name: str,
    base_branch: str = "master",
    working_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a new git branch.

    Args:
        branch_name: Name of new branch (e.g., "update/v1.222.0")
        base_branch: Branch to create from
        working_dir: Working directory
        dry_run: If True, don't create branch

    Returns:
        Dict with success status and branch info
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "branch_name": branch_name,
            "base_branch": base_branch,
        }

    try:
        # Checkout base branch
        subprocess.run(
            ["git", "checkout", base_branch],
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=True,
        )

        # Pull latest
        subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=working_dir,
            capture_output=True,
            text=True,
        )

        # Create and checkout new branch
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=working_dir,
            capture_output=True,
            text=True,
        )

        return {
            "success": result.returncode == 0,
            "dry_run": False,
            "branch_name": branch_name,
            "base_branch": base_branch,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "dry_run": False,
            "error": str(e),
        }


def git_commit_changes(
    message: str,
    working_dir: Path | None = None,
    dry_run: bool = False,
    files: list[str] | None = None,
) -> dict[str, Any]:
    """Commit staged changes.

    Args:
        message: Commit message
        working_dir: Working directory
        dry_run: If True, don't commit
        files: Specific files to add, or None for all

    Returns:
        Dict with success status
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "message": message,
        }

    try:
        # Add files
        if files:
            for file in files:
                subprocess.run(
                    ["git", "add", file],
                    cwd=working_dir,
                    check=True,
                    capture_output=True,
                )
        else:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=working_dir,
                check=True,
                capture_output=True,
            )

        # Commit
        commit_message = f"{message}\n\n\U0001f916 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=working_dir,
            capture_output=True,
            text=True,
        )

        return {
            "success": result.returncode == 0,
            "dry_run": False,
            "message": message,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "dry_run": False,
            "error": str(e),
        }


def git_push_branch(
    branch_name: str,
    remote: str = "origin",
    working_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Push branch to remote.

    Args:
        branch_name: Branch to push
        remote: Remote name
        working_dir: Working directory
        dry_run: If True, don't push

    Returns:
        Dict with success status
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "branch_name": branch_name,
            "remote": remote,
        }

    try:
        result = subprocess.run(
            ["git", "push", "-u", remote, branch_name],
            cwd=working_dir,
            capture_output=True,
            text=True,
        )

        return {
            "success": result.returncode == 0,
            "dry_run": False,
            "branch_name": branch_name,
            "remote": remote,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "dry_run": False,
            "error": str(e),
        }


def create_pr(
    title: str,
    body: str,
    base_branch: str = "master",
    head_branch: str | None = None,
    working_dir: Path | None = None,
    dry_run: bool = False,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a pull request using gh CLI.

    Args:
        title: PR title
        body: PR body
        base_branch: Base branch for PR
        head_branch: Head branch (default: current branch)
        working_dir: Working directory
        dry_run: If True, don't create PR
        labels: Labels to apply

    Returns:
        Dict with success status and PR URL
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "pr_url": None,
            "title": title,
        }

    try:
        cmd = [
            "gh",
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--base",
            base_branch,
        ]

        if head_branch:
            cmd.extend(["--head", head_branch])

        if labels:
            for label in labels:
                cmd.extend(["--label", label])

        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            # gh pr create returns the PR URL
            pr_url = result.stdout.strip()
            return {
                "success": True,
                "dry_run": False,
                "pr_url": pr_url,
                "title": title,
            }
        else:
            return {
                "success": False,
                "dry_run": False,
                "pr_url": None,
                "error": result.stderr,
            }

    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "dry_run": False,
            "error": str(e),
        }
    except FileNotFoundError:
        return {
            "success": False,
            "dry_run": False,
            "error": "gh CLI not found in PATH",
        }


def get_current_branch(working_dir: Path | None = None) -> str | None:
    """Get current git branch name.

    Args:
        working_dir: Working directory

    Returns:
        Branch name or None if not in a git repo
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=working_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def has_uncommitted_changes(working_dir: Path | None = None) -> bool:
    """Check if there are uncommitted changes.

    Args:
        working_dir: Working directory

    Returns:
        True if there are uncommitted changes
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=working_dir,
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
