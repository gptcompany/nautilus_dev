# NautilusTrader Auto-Update Pipeline - Changelog Parser

"""Parse N8N-generated changelog.json and extract version/breaking change info."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from scripts.auto_update.models import BreakingChange, ChangelogData, Severity


def load_changelog_json(path: Path) -> dict[str, Any]:
    """Load changelog JSON from file.

    Args:
        path: Path to changelog.json file

    Returns:
        Raw JSON data as dictionary

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if not path.exists():
        raise FileNotFoundError(f"Changelog file not found: {path}")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_changelog(source: Path | dict[str, Any]) -> ChangelogData:
    """Parse changelog data from file path or dict.

    Args:
        source: Path to changelog.json or raw dict

    Returns:
        Parsed ChangelogData model

    Raises:
        FileNotFoundError: If path does not exist
        json.JSONDecodeError: If file is not valid JSON
        ValidationError: If data doesn't match ChangelogData schema
    """
    if isinstance(source, Path):
        data = load_changelog_json(source)
    else:
        data = source

    return ChangelogData.model_validate(data)


def extract_breaking_changes(changelog: ChangelogData) -> list[BreakingChange]:
    """Extract and classify breaking changes from changelog.

    Parses the breaking_changes strings and:
    1. Assigns severity based on change type
    2. Generates grep patterns for codebase search
    3. Extracts migration hints if present

    Args:
        changelog: Parsed changelog data

    Returns:
        List of BreakingChange models with patterns and severity
    """
    if not changelog.breaking_changes:
        return []

    result: list[BreakingChange] = []

    for description in changelog.breaking_changes:
        severity = _classify_severity(description)
        pattern = _generate_grep_pattern(description)
        migration = _extract_migration_guide(description)

        result.append(
            BreakingChange(
                description=description,
                affected_pattern=pattern,
                severity=severity,
                migration_guide=migration,
            )
        )

    return result


def _classify_severity(description: str) -> Severity:
    """Classify breaking change severity based on description.

    Classification rules:
    - CRITICAL: Import/module removal, base class changes
    - HIGH: Method removal, signature changes
    - MEDIUM: Deprecation, parameter changes
    - LOW: Type hints, minor API changes
    """
    desc_lower = description.lower()

    # CRITICAL indicators
    critical_patterns = [
        r"removed.*module",
        r"removed.*import",
        r"removed.*class\s+\w+\s*$",  # Removed class entirely
        r"base class.*removed",
        r"base class.*changed",
    ]
    for pattern in critical_patterns:
        if re.search(pattern, desc_lower):
            return Severity.CRITICAL

    # HIGH indicators
    high_patterns = [
        r"removed.*method",
        r"removed.*function",
        r"removed deprecated",
        r"signature.*changed",
        r"no longer.*accepts",
    ]
    for pattern in high_patterns:
        if re.search(pattern, desc_lower):
            return Severity.HIGH

    # MEDIUM indicators
    medium_patterns = [
        r"deprecated",
        r"parameter.*renamed",
        r"parameter.*required",
        r"default.*changed",
        r"changed.*signature",
    ]
    for pattern in medium_patterns:
        if re.search(pattern, desc_lower):
            return Severity.MEDIUM

    # Default to MEDIUM for unknown breaking changes
    return Severity.MEDIUM


def _generate_grep_pattern(description: str) -> str:
    """Generate grep pattern from breaking change description.

    Extracts identifiers and generates regex patterns for codebase search.
    """
    # Look for quoted identifiers like `Strategy.on_tick`
    backtick_match = re.findall(r"`([^`]+)`", description)

    if backtick_match:
        # Use the first identifier found
        identifier = backtick_match[0]

        # Check if it's a method call pattern
        if "." in identifier:
            parts = identifier.split(".")
            method_name = parts[-1]
            # Pattern: def method_name( or .method_name(
            if method_name.startswith("on_"):
                return rf"def {method_name}\("
            elif "from_" in method_name or "to_" in method_name:
                return rf"\.{method_name}\(|{method_name}\("
            else:
                return rf"\.{method_name}\(|def {method_name}\("

        # Check if it's an import pattern
        elif "import" in description.lower():
            return rf"from .* import .*{identifier}|import .*{identifier}"

        # Generic identifier pattern
        else:
            return re.escape(identifier)

    # No backtick identifier found - try to extract from text
    # Look for CamelCase or snake_case identifiers
    camel_match = re.findall(r"\b([A-Z][a-zA-Z]+(?:\.[a-z_]+)?)\b", description)
    if camel_match:
        return camel_match[0]

    # Fallback: empty pattern (manual review needed)
    return ""


def _extract_migration_guide(description: str) -> str | None:
    """Extract migration hint from breaking change description.

    Looks for patterns like:
    - "use X instead"
    - "replace with Y"
    - "migrate to Z"
    """
    # Pattern: use X instead
    use_instead = re.search(r"use\s+`?([^`]+)`?\s+instead", description, re.IGNORECASE)
    if use_instead:
        replacement = use_instead.group(1)
        return f"Replace with {replacement}"

    # Pattern: replace with X
    replace_with = re.search(r"replace\s+with\s+`?([^`]+)`?", description, re.IGNORECASE)
    if replace_with:
        replacement = replace_with.group(1)
        return f"Replace with {replacement}"

    # Pattern: migrate to X
    migrate_to = re.search(r"migrate\s+to\s+`?([^`]+)`?", description, re.IGNORECASE)
    if migrate_to:
        replacement = migrate_to.group(1)
        return f"Migrate to {replacement}"

    return None


def detect_update_available(
    current_version: str,
    changelog_version: str,
) -> dict[str, Any]:
    """Check if an update is available by comparing versions.

    Args:
        current_version: Currently installed version (e.g., "1.221.0" or "v1.221.0")
        changelog_version: Latest version from changelog (e.g., "v1.222.0")

    Returns:
        Dict with:
        - update_available: bool
        - current_version: str (normalized)
        - latest_version: str (normalized)
    """
    current = _normalize_version(current_version)
    latest = _normalize_version(changelog_version)

    current_tuple = _parse_version_tuple(current)
    latest_tuple = _parse_version_tuple(latest)

    return {
        "update_available": latest_tuple > current_tuple,
        "current_version": current,
        "latest_version": latest,
    }


def _normalize_version(version: str) -> str:
    """Normalize version string by stripping 'v' prefix."""
    return version.lstrip("v").strip()


def _parse_version_tuple(version: str) -> tuple[int, ...]:
    """Parse version string into comparable tuple.

    Handles versions like "1.221.0" or "1.222.0-nightly".
    """
    # Strip any suffix like -nightly, -rc1, etc.
    base_version = version.split("-")[0]

    parts = []
    for part in base_version.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            # Non-numeric part, treat as 0
            parts.append(0)

    # Pad to at least 3 parts
    while len(parts) < 3:
        parts.append(0)

    return tuple(parts)


def get_current_version(pyproject_path: Path) -> str | None:
    """Extract current nautilus_trader version from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        Version string if found, None otherwise
    """
    if not pyproject_path.exists():
        return None

    content = pyproject_path.read_text()

    # Pattern: nautilus_trader>=1.221.0 or nautilus_trader[all]>=1.222.0
    pattern = r"nautilus_trader(?:\[[^\]]+\])?[><=~!]+(\d+\.\d+\.\d+)"
    match = re.search(pattern, content)

    if match:
        return match.group(1)

    return None
