#!/usr/bin/env python3
"""Checkpoint and rollback management for CI/CD pipeline.

Provides checkpoint creation before pipeline stages and rollback
capability on failure. Integrates with ccundo for comprehensive
undo support.

Usage:
    # Create checkpoint
    python rollback.py create --name "pre-backtest" --stage 4

    # List checkpoints
    python rollback.py list

    # Rollback to checkpoint
    python rollback.py rollback --checkpoint abc123

    # Cleanup old checkpoints
    python rollback.py cleanup --older-than 24h
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Default checkpoint directory
CHECKPOINT_DIR = Path.home() / ".ci_checkpoints"
RETENTION_HOURS = 24


@dataclass
class Checkpoint:
    """Represents a checkpoint snapshot."""

    id: str
    name: str
    stage: int
    timestamp: str
    git_sha: str
    branch: str
    files_changed: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "stage": self.stage,
            "timestamp": self.timestamp,
            "git_sha": self.git_sha,
            "branch": self.branch,
            "files_changed": self.files_changed,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Checkpoint:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            stage=data["stage"],
            timestamp=data["timestamp"],
            git_sha=data["git_sha"],
            branch=data["branch"],
            files_changed=data.get("files_changed", []),
            metadata=data.get("metadata", {}),
        )


def run_command(cmd: list[str], check: bool = True) -> tuple[int, str, str]:
    """Run a shell command and return result."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout.strip(), e.stderr.strip()
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"


def get_git_sha() -> str:
    """Get current git commit SHA."""
    code, stdout, _ = run_command(["git", "rev-parse", "HEAD"], check=False)
    return stdout[:12] if code == 0 else "unknown"


def get_git_branch() -> str:
    """Get current git branch."""
    code, stdout, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], check=False)
    return stdout if code == 0 else "unknown"


def get_changed_files() -> list[str]:
    """Get list of changed files."""
    code, stdout, _ = run_command(["git", "diff", "--name-only", "HEAD~1", "HEAD"], check=False)
    if code == 0 and stdout:
        return stdout.split("\n")
    return []


def generate_checkpoint_id() -> str:
    """Generate a unique checkpoint ID."""
    import hashlib

    timestamp = datetime.now().isoformat()
    git_sha = get_git_sha()
    data = f"{timestamp}_{git_sha}"
    return hashlib.sha256(data.encode()).hexdigest()[:12]


def create_checkpoint(
    name: str,
    stage: int,
    metadata: dict[str, Any] | None = None,
) -> Checkpoint:
    """Create a new checkpoint."""
    checkpoint_id = generate_checkpoint_id()
    checkpoint_path = CHECKPOINT_DIR / checkpoint_id

    # Create checkpoint directory
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_path.mkdir(exist_ok=True)

    # Create checkpoint object
    checkpoint = Checkpoint(
        id=checkpoint_id,
        name=name,
        stage=stage,
        timestamp=datetime.now().isoformat(),
        git_sha=get_git_sha(),
        branch=get_git_branch(),
        files_changed=get_changed_files(),
        metadata=metadata or {},
    )

    # Save checkpoint manifest
    manifest_path = checkpoint_path / "manifest.json"
    manifest_path.write_text(json.dumps(checkpoint.to_dict(), indent=2))

    # Create git stash for uncommitted changes
    code, stdout, _ = run_command(
        ["git", "stash", "push", "-m", f"checkpoint_{checkpoint_id}"], check=False
    )
    if code == 0 and "Saved working directory" in stdout:
        checkpoint.metadata["has_stash"] = True
        # Re-apply stash but keep it
        run_command(["git", "stash", "pop"], check=False)

    # Save ref to current commit
    ref_path = checkpoint_path / "git_ref"
    ref_path.write_text(checkpoint.git_sha)

    # Try to use ccundo if available
    code, _, _ = run_command(["ccundo", "checkpoint", name], check=False)
    if code == 0:
        checkpoint.metadata["ccundo_checkpoint"] = True

    # Update manifest with final metadata
    manifest_path.write_text(json.dumps(checkpoint.to_dict(), indent=2))

    print(f"Created checkpoint: {checkpoint_id}")
    print(f"  Name: {name}")
    print(f"  Stage: {stage}")
    print(f"  Git SHA: {checkpoint.git_sha}")

    return checkpoint


def list_checkpoints(verbose: bool = False) -> list[Checkpoint]:
    """List all checkpoints."""
    checkpoints: list[Checkpoint] = []

    if not CHECKPOINT_DIR.exists():
        return checkpoints

    for path in CHECKPOINT_DIR.iterdir():
        if path.is_dir():
            manifest = path / "manifest.json"
            if manifest.exists():
                try:
                    data = json.loads(manifest.read_text())
                    checkpoints.append(Checkpoint.from_dict(data))
                except (json.JSONDecodeError, KeyError):
                    pass

    # Sort by timestamp (newest first)
    checkpoints.sort(key=lambda c: c.timestamp, reverse=True)

    return checkpoints


def get_checkpoint(checkpoint_id: str) -> Checkpoint | None:
    """Get a specific checkpoint by ID."""
    checkpoint_path = CHECKPOINT_DIR / checkpoint_id
    manifest = checkpoint_path / "manifest.json"

    if manifest.exists():
        try:
            data = json.loads(manifest.read_text())
            return Checkpoint.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def rollback_to_checkpoint(checkpoint_id: str, force: bool = False) -> bool:
    """Rollback to a specific checkpoint."""
    checkpoint = get_checkpoint(checkpoint_id)
    if not checkpoint:
        print(f"Error: Checkpoint not found: {checkpoint_id}")
        return False

    print(f"Rolling back to checkpoint: {checkpoint_id}")
    print(f"  Name: {checkpoint.name}")
    print(f"  Stage: {checkpoint.stage}")
    print(f"  Git SHA: {checkpoint.git_sha}")

    # Check for uncommitted changes
    code, stdout, _ = run_command(["git", "status", "--porcelain"], check=False)
    if stdout and not force:
        print("Error: Uncommitted changes exist. Use --force to override.")
        return False

    # Try ccundo first if checkpoint used it
    if checkpoint.metadata.get("ccundo_checkpoint"):
        code, _, _ = run_command(["ccundo", "rollback", checkpoint.name], check=False)
        if code == 0:
            print("Rolled back via ccundo")
            return True

    # Git-based rollback
    if checkpoint.git_sha and checkpoint.git_sha != "unknown":
        if force:
            # Hard reset to checkpoint commit
            code, _, stderr = run_command(
                ["git", "reset", "--hard", checkpoint.git_sha], check=False
            )
            if code != 0:
                print(f"Git reset failed: {stderr}")
                return False
            print(f"Reset to commit: {checkpoint.git_sha}")
        else:
            # Create a revert commit
            code, _, stderr = run_command(
                ["git", "revert", "--no-commit", f"{checkpoint.git_sha}..HEAD"],
                check=False,
            )
            if code != 0:
                print(f"Git revert failed: {stderr}")
                return False

            # Commit the revert
            run_command(
                [
                    "git",
                    "commit",
                    "-m",
                    f"Rollback to checkpoint {checkpoint_id} ({checkpoint.name})",
                ],
                check=False,
            )
            print("Created rollback commit")

    print("Rollback complete")
    return True


def cleanup_checkpoints(older_than_hours: int = RETENTION_HOURS) -> int:
    """Cleanup checkpoints older than specified hours."""
    cutoff = datetime.now() - timedelta(hours=older_than_hours)
    removed = 0

    checkpoints = list_checkpoints()
    for checkpoint in checkpoints:
        try:
            checkpoint_time = datetime.fromisoformat(checkpoint.timestamp)
            if checkpoint_time < cutoff:
                checkpoint_path = CHECKPOINT_DIR / checkpoint.id
                if checkpoint_path.exists():
                    shutil.rmtree(checkpoint_path)
                    removed += 1
                    print(f"Removed checkpoint: {checkpoint.id} ({checkpoint.name})")
        except ValueError:
            pass

    return removed


def delete_checkpoint(checkpoint_id: str) -> bool:
    """Delete a specific checkpoint."""
    checkpoint_path = CHECKPOINT_DIR / checkpoint_id
    if checkpoint_path.exists():
        shutil.rmtree(checkpoint_path)
        print(f"Deleted checkpoint: {checkpoint_id}")
        return True
    print(f"Checkpoint not found: {checkpoint_id}")
    return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Checkpoint and rollback management for CI/CD")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a checkpoint")
    create_parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Checkpoint name (e.g., pre-backtest)",
    )
    create_parser.add_argument(
        "--stage",
        type=int,
        default=0,
        help="Pipeline stage number",
    )
    create_parser.add_argument(
        "--metadata",
        type=str,
        help="JSON metadata to attach",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List checkpoints")
    list_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed information",
    )

    # Rollback command
    rollback_parser = subparsers.add_parser("rollback", help="Rollback to checkpoint")
    rollback_parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Checkpoint ID to rollback to",
    )
    rollback_parser.add_argument(
        "--force",
        action="store_true",
        help="Force rollback (discards uncommitted changes)",
    )

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup old checkpoints")
    cleanup_parser.add_argument(
        "--older-than",
        type=str,
        default="24h",
        help="Remove checkpoints older than (e.g., 24h, 7d)",
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a checkpoint")
    delete_parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Checkpoint ID to delete",
    )

    args = parser.parse_args()

    if args.command == "create":
        metadata = {}
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print("Warning: Invalid metadata JSON")

        checkpoint = create_checkpoint(args.name, args.stage, metadata)
        print(f"\nCheckpoint ID: {checkpoint.id}")

    elif args.command == "list":
        checkpoints = list_checkpoints(args.verbose)
        if not checkpoints:
            print("No checkpoints found")
            return

        print(f"Found {len(checkpoints)} checkpoint(s):\n")
        for cp in checkpoints:
            age = datetime.now() - datetime.fromisoformat(cp.timestamp)
            age_str = f"{age.seconds // 3600}h ago" if age.days == 0 else f"{age.days}d ago"

            print(f"  {cp.id}  [{cp.name}]")
            print(f"    Stage: {cp.stage} | Branch: {cp.branch} | {age_str}")
            if args.verbose:
                print(f"    SHA: {cp.git_sha}")
                print(f"    Time: {cp.timestamp}")
                if cp.files_changed:
                    print(f"    Files: {len(cp.files_changed)}")
            print()

    elif args.command == "rollback":
        success = rollback_to_checkpoint(args.checkpoint, args.force)
        exit(0 if success else 1)

    elif args.command == "cleanup":
        # Parse duration
        duration = args.older_than
        if duration.endswith("h"):
            hours = int(duration[:-1])
        elif duration.endswith("d"):
            hours = int(duration[:-1]) * 24
        else:
            hours = int(duration)

        removed = cleanup_checkpoints(hours)
        print(f"\nRemoved {removed} checkpoint(s)")

    elif args.command == "delete":
        success = delete_checkpoint(args.checkpoint)
        exit(0 if success else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
