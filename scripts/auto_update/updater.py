# NautilusTrader Auto-Update Pipeline - Updater

"""Update pyproject.toml and run uv sync."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


def update_pyproject_version(
    pyproject_path: Path,
    new_version: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update nautilus_trader version in pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml
        new_version: New version to set (e.g., "1.222.0")
        dry_run: If True, don't modify file

    Returns:
        Dict with success status, old_version, new_version

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
    """
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found: {pyproject_path}")

    content = pyproject_path.read_text()

    # Pattern: nautilus_trader>=1.221.0 or nautilus_trader[all]>=1.222.0
    pattern = r"(nautilus_trader(?:\[[^\]]+\])?[><=~!]+)(\d+\.\d+\.\d+)"
    match = re.search(pattern, content)

    if not match:
        return {
            "success": False,
            "error": "nautilus_trader dependency not found in pyproject.toml",
            "dry_run": dry_run,
        }

    old_version = match.group(2)
    prefix = match.group(1)

    # Replace version
    new_content = re.sub(
        pattern,
        f"{prefix}{new_version}",
        content,
    )

    if not dry_run:
        pyproject_path.write_text(new_content)

    return {
        "success": True,
        "old_version": old_version,
        "new_version": new_version,
        "dry_run": dry_run,
    }


def run_uv_sync(
    working_dir: Path,
    dry_run: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    """Run uv sync to update dependencies.

    Args:
        working_dir: Working directory for uv sync
        dry_run: If True, don't run uv sync
        timeout: Command timeout in seconds

    Returns:
        Dict with success status, stdout, stderr
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "command": None,
        }

    # Check if pyproject.toml exists
    pyproject = working_dir / "pyproject.toml"
    if not pyproject.exists():
        return {
            "success": False,
            "error": f"pyproject.toml not found in {working_dir}",
            "dry_run": False,
        }

    try:
        result = subprocess.run(
            ["uv", "sync"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "dry_run": False,
            "command": "uv sync",
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"uv sync timed out after {timeout}s",
            "dry_run": False,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "uv not found in PATH",
            "dry_run": False,
        }


def auto_update(
    version: str,
    pyproject_path: Path,
    working_dir: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Orchestrate full auto-update process.

    1. Update pyproject.toml version
    2. Run uv sync
    3. Return combined result

    Args:
        version: New version to update to
        pyproject_path: Path to pyproject.toml
        working_dir: Working directory
        dry_run: If True, don't make changes

    Returns:
        Dict with combined results
    """
    results = {
        "version": version,
        "dry_run": dry_run,
        "steps": [],
    }

    # Step 1: Update pyproject.toml
    update_result = update_pyproject_version(
        pyproject_path=pyproject_path,
        new_version=version,
        dry_run=dry_run,
    )
    results["steps"].append({"name": "update_pyproject", **update_result})

    if not update_result["success"]:
        results["success"] = False
        results["error"] = update_result.get("error", "Failed to update pyproject.toml")
        return results

    # Step 2: Run uv sync
    sync_result = run_uv_sync(
        working_dir=working_dir,
        dry_run=dry_run,
    )
    results["steps"].append({"name": "uv_sync", **sync_result})

    if not sync_result["success"]:
        results["success"] = False
        results["error"] = sync_result.get("error", "Failed to run uv sync")
        return results

    results["success"] = True
    return results
