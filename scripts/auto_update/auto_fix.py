# NautilusTrader Auto-Update Pipeline - Auto-Fix

"""Apply simple regex-based fixes (import renames, method renames)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from scripts.auto_update.models import AffectedFile


def detect_fix_type(description: str) -> str | None:
    """Detect the type of fix needed based on breaking change description.

    Args:
        description: Breaking change description

    Returns:
        Fix type: 'import_rename', 'method_rename', or None if unknown
    """
    description_lower = description.lower()

    # Check for import/class rename patterns
    import_patterns = [
        r"renamed?\s+\w+\s+to\s+\w+",
        r"\w+\s+(?:has been\s+)?renamed?\s+to\s+\w+",
        r"class\s+\w+.*(?:renamed|now)",
        r"import.*(?:renamed|changed|now)",
    ]
    for pattern in import_patterns:
        if re.search(pattern, description_lower):
            # Check if it's specifically about methods
            if "method" in description_lower or "function" in description_lower:
                return "method_rename"
            return "import_rename"

    # Check for method rename patterns
    method_patterns = [
        r"method\s+\w+.*(?:renamed|now)",
        r"function\s+\w+.*(?:renamed|now)",
        r"\.\w+\(\).*(?:renamed|now|changed)",
    ]
    for pattern in method_patterns:
        if re.search(pattern, description_lower):
            return "method_rename"

    return None


def apply_import_rename(
    file_path: Path,
    old_name: str,
    new_name: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Apply import/class rename to a file.

    Args:
        file_path: Path to Python file
        old_name: Old class/import name
        new_name: New class/import name
        dry_run: If True, don't modify file

    Returns:
        Dict with success status and changes made
    """
    if not file_path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "dry_run": dry_run,
        }

    try:
        content = file_path.read_text()
        original_content = content

        # Use word boundary matching to avoid partial matches
        # Match the old name as a complete word
        pattern = rf"\b{re.escape(old_name)}\b"
        new_content = re.sub(pattern, new_name, content)

        # Count changes
        changes_made = len(re.findall(pattern, original_content))

        if not dry_run and new_content != original_content:
            file_path.write_text(new_content)

        return {
            "success": True,
            "dry_run": dry_run,
            "changes_made": changes_made,
            "file_path": str(file_path),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "dry_run": dry_run,
        }


def apply_method_rename(
    file_path: Path,
    old_name: str,
    new_name: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Apply method rename to a file.

    Args:
        file_path: Path to Python file
        old_name: Old method name
        new_name: New method name
        dry_run: If True, don't modify file

    Returns:
        Dict with success status and changes made
    """
    if not file_path.exists():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "dry_run": dry_run,
        }

    try:
        content = file_path.read_text()
        original_content = content

        # Match method calls with word boundaries
        # Handles self.method(), obj.method(), method()
        pattern = rf"\b{re.escape(old_name)}\b"
        new_content = re.sub(pattern, new_name, content)

        # Count changes
        changes_made = len(re.findall(pattern, original_content))

        if not dry_run and new_content != original_content:
            file_path.write_text(new_content)

        return {
            "success": True,
            "dry_run": dry_run,
            "changes_made": changes_made,
            "file_path": str(file_path),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "dry_run": dry_run,
        }


def auto_fix_files(
    affected_files: list[AffectedFile],
    fix_pattern: str,
    new_value: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Orchestrate auto-fixing of multiple files.

    Args:
        affected_files: List of AffectedFile objects
        fix_pattern: Pattern to find (old name)
        new_value: Replacement value (new name)
        dry_run: If True, don't modify files

    Returns:
        Dict with aggregate results
    """
    results = {
        "success": True,
        "dry_run": dry_run,
        "files_fixed": 0,
        "files_skipped": 0,
        "files_failed": 0,
        "total_changes": 0,
        "details": [],
    }

    for affected in affected_files:
        # Skip files not marked as auto-fixable
        if not affected.can_auto_fix:
            results["files_skipped"] += 1
            results["details"].append(
                {
                    "file": str(affected.path),
                    "status": "skipped",
                    "reason": "not_auto_fixable",
                }
            )
            continue

        # Apply fix based on fix type
        fix_type = affected.fix_type or "import_rename"

        if fix_type == "method_rename":
            fix_result = apply_method_rename(
                file_path=affected.path,
                old_name=fix_pattern,
                new_name=new_value,
                dry_run=dry_run,
            )
        else:  # Default to import_rename
            fix_result = apply_import_rename(
                file_path=affected.path,
                old_name=fix_pattern,
                new_name=new_value,
                dry_run=dry_run,
            )

        if fix_result["success"]:
            if fix_result.get("changes_made", 0) > 0:
                results["files_fixed"] += 1
                results["total_changes"] += fix_result.get("changes_made", 0)
            results["details"].append(
                {
                    "file": str(affected.path),
                    "status": "fixed",
                    "changes": fix_result.get("changes_made", 0),
                }
            )
        else:
            results["files_failed"] += 1
            results["success"] = False
            results["details"].append(
                {
                    "file": str(affected.path),
                    "status": "failed",
                    "error": fix_result.get("error"),
                }
            )

    return results


def extract_rename_from_description(description: str) -> tuple[str | None, str | None]:
    """Extract old and new names from a breaking change description.

    Args:
        description: Breaking change description

    Returns:
        Tuple of (old_name, new_name) or (None, None) if not extractable
    """
    # Common patterns:
    # "Renamed OldName to NewName"
    # "OldName has been renamed to NewName"
    # "Changed from old_method to new_method"

    patterns = [
        r"[Rr]ename[d]?\s+(\w+)\s+to\s+(\w+)",
        r"(\w+)\s+(?:has been\s+)?renamed?\s+to\s+(\w+)",
        r"[Cc]hanged?\s+(?:from\s+)?(\w+)\s+to\s+(\w+)",
        r"(\w+)\s+->\s+(\w+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            return match.group(1), match.group(2)

    return None, None
