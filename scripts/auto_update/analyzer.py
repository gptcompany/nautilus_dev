# NautilusTrader Auto-Update Pipeline - Impact Analyzer

"""Analyze codebase for breaking change impact using grep patterns."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from scripts.auto_update.models import (
    AffectedFile,
    BreakingChange,
    ImpactReport,
    Severity,
)


def grep_codebase(
    pattern: str,
    source_dirs: list[Path],
    file_extensions: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search codebase for pattern matches using ripgrep.

    Args:
        pattern: Regex pattern to search for
        source_dirs: List of directories to search
        file_extensions: File extensions to include (default: .py)

    Returns:
        List of match dicts with path, line, content
    """
    if file_extensions is None:
        file_extensions = [".py"]

    results: list[dict[str, Any]] = []

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue

        matches = _grep_directory(source_dir, pattern, file_extensions)
        results.extend(matches)

    return results


def _grep_directory(
    directory: Path,
    pattern: str,
    file_extensions: list[str],
) -> list[dict[str, Any]]:
    """Run ripgrep on a single directory.

    Falls back to Python regex if rg not available.
    """
    # Try ripgrep first (faster)
    try:
        return _grep_with_ripgrep(directory, pattern, file_extensions)
    except FileNotFoundError:
        # rg not available, use Python fallback
        return _grep_with_python(directory, pattern, file_extensions)


def _grep_with_ripgrep(
    directory: Path,
    pattern: str,
    file_extensions: list[str],
) -> list[dict[str, Any]]:
    """Use ripgrep for fast searching."""
    cmd = [
        "rg",
        "--json",
        "--line-number",
        "--no-heading",
    ]

    # Add file type filters
    for ext in file_extensions:
        cmd.extend(["--glob", f"*{ext}"])

    cmd.extend([pattern, str(directory)])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Parse JSON output
    import json

    matches = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("type") == "match":
                match_data = data["data"]
                matches.append(
                    {
                        "path": Path(match_data["path"]["text"]),
                        "line": match_data["line_number"],
                        "content": match_data["lines"]["text"].strip(),
                    }
                )
        except json.JSONDecodeError:
            continue

    return matches


def _grep_with_python(
    directory: Path,
    pattern: str,
    file_extensions: list[str],
) -> list[dict[str, Any]]:
    """Python fallback for grep functionality."""
    results = []
    regex = re.compile(pattern)

    for ext in file_extensions:
        for file_path in directory.rglob(f"*{ext}"):
            try:
                content = file_path.read_text(encoding="utf-8")
                for line_num, line in enumerate(content.split("\n"), 1):
                    if regex.search(line):
                        results.append(
                            {
                                "path": file_path,
                                "line": line_num,
                                "content": line.strip(),
                            }
                        )
            except (UnicodeDecodeError, PermissionError):
                continue

    return results


def classify_severity(description: str) -> Severity:
    """Classify breaking change severity based on description.

    Classification rules:
    - CRITICAL: Import/module removal, base class changes
    - HIGH: Method removal, signature changes
    - MEDIUM: Deprecation, parameter changes
    - LOW: Type hints, minor API changes

    Args:
        description: Breaking change description

    Returns:
        Severity enum value
    """
    desc_lower = description.lower()

    # CRITICAL indicators
    critical_patterns = [
        r"removed.*module",
        r"removed.*import",
        r"removed\s+class\s+\w+\s*$",
        r"base class.*removed",
        r"base class.*changed",
        r"removed.*package",
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
        r"removed.*parameter",
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
        r"renamed",
    ]
    for pattern in medium_patterns:
        if re.search(pattern, desc_lower):
            return Severity.MEDIUM

    # Default to MEDIUM for unknown breaking changes
    return Severity.MEDIUM


def calculate_confidence(
    breaking_changes: list[BreakingChange],
    affected_files: list[AffectedFile],
    days_since_release: int = 3,
) -> float:
    """Calculate confidence score for safe update.

    Scoring factors:
    - Age (30%): Wait 24-72h after release for stability
    - Breaking Changes (40%): Severity and count
    - Affected Files (30%): Number and complexity

    Args:
        breaking_changes: List of breaking changes
        affected_files: List of affected files
        days_since_release: Days since version was released

    Returns:
        Confidence score 0-100
    """
    # Base score
    score = 100.0

    # === Age Factor (30%) ===
    # Fresh releases are riskier
    if days_since_release < 1:
        score -= 20  # Very fresh, wait
    elif days_since_release < 3:
        score -= 10  # Still new
    elif days_since_release < 7:
        score -= 5  # Reasonably stable
    # else: no penalty, well tested

    # === Breaking Changes Factor (40%) ===
    for bc in breaking_changes:
        if bc.severity == Severity.CRITICAL:
            score -= 70  # Critical = major penalty, blocks update
        elif bc.severity == Severity.HIGH:
            score -= 25
        elif bc.severity == Severity.MEDIUM:
            score -= 12
        else:  # LOW
            score -= 5

    # === Affected Files Factor (30%) ===
    num_files = len(affected_files)
    if num_files > 10:
        score -= 25
    elif num_files > 5:
        score -= 15
    elif num_files > 2:
        score -= 10
    elif num_files > 0:
        score -= 5

    # Count total affected lines
    total_lines = sum(len(af.line_numbers) for af in affected_files)
    if total_lines > 50:
        score -= 10
    elif total_lines > 20:
        score -= 5

    # Clamp to 0-100
    return max(0.0, min(100.0, score))


def generate_impact_report(
    version: str,
    previous_version: str | None,
    breaking_changes: list[BreakingChange],
    affected_files: list[AffectedFile],
    days_since_release: int = 3,
) -> ImpactReport:
    """Generate complete impact analysis report.

    Args:
        version: Target version
        previous_version: Current version
        breaking_changes: List of breaking changes
        affected_files: List of affected files from grep
        days_since_release: Days since version was released

    Returns:
        ImpactReport with confidence scoring and recommendation
    """
    # Calculate totals
    total_affected_lines = sum(len(af.line_numbers) for af in affected_files)

    # Calculate confidence score
    confidence_score = calculate_confidence(
        breaking_changes=breaking_changes,
        affected_files=affected_files,
        days_since_release=days_since_release,
    )

    # Create report (model validator will set confidence_level and recommendation)
    return ImpactReport(
        version=version,
        previous_version=previous_version,
        breaking_changes=breaking_changes,
        affected_files=affected_files,
        total_affected_lines=total_affected_lines,
        confidence_score=confidence_score,
    )


def analyze_breaking_change_impact(
    breaking_change: BreakingChange,
    source_dirs: list[Path],
) -> list[AffectedFile]:
    """Find all files affected by a single breaking change.

    Args:
        breaking_change: Breaking change to analyze
        source_dirs: Directories to search

    Returns:
        List of affected files with line numbers
    """
    if not breaking_change.affected_pattern:
        return []

    matches = grep_codebase(
        pattern=breaking_change.affected_pattern,
        source_dirs=source_dirs,
    )

    # Group matches by file
    files_map: dict[Path, list[int]] = {}
    for match in matches:
        path = match["path"]
        line = match["line"]
        if path not in files_map:
            files_map[path] = []
        files_map[path].append(line)

    # Create AffectedFile objects
    affected_files = []
    for path, lines in files_map.items():
        # Determine if auto-fix is possible
        can_fix, fix_type = _can_auto_fix(breaking_change)

        affected_files.append(
            AffectedFile(
                path=path,
                line_numbers=sorted(lines),
                breaking_change=breaking_change,
                can_auto_fix=can_fix,
                fix_type=fix_type,
            )
        )

    return affected_files


def _can_auto_fix(breaking_change: BreakingChange) -> tuple[bool, str | None]:
    """Determine if a breaking change can be auto-fixed.

    Returns:
        Tuple of (can_fix, fix_type)
    """
    desc_lower = breaking_change.description.lower()

    # Method renames can be auto-fixed
    if "use" in desc_lower and "instead" in desc_lower:
        if "method" in desc_lower or "function" in desc_lower:
            return True, "method_rename"
        if "import" in desc_lower:
            return True, "import_rename"

    # Parameter renames might be auto-fixable
    if "renamed" in desc_lower and "parameter" in desc_lower:
        return True, "parameter_rename"

    # Default: cannot auto-fix
    return False, None
