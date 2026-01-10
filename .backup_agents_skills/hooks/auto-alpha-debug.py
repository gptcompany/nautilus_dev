#!/usr/bin/env python3
"""
Stop Hook: Auto-spawn Alpha-Debug after implementation phases.

DEPRECATED (2026-01-08): Use Ralph Loop instead for mechanical debugging tasks.
See ADR-006 for migration details. Ralph provides:
- Unified loop mechanism (vs spawning separate agents)
- Circuit breakers and progress tracking
- Dynamic exit criteria

This hook will be removed after 30-day deprecation period.

Triggers when Claude stops after:
1. SpecKit implementation phases
2. Significant code changes (>20 lines modified)
3. Test failures that were fixed

Uses complexity analysis to determine optimal round count.

DUAL-SOURCE DETECTION:
- Primary: Uncommitted changes (git diff HEAD)
- Fallback: Last commit if recent (< MAX_COMMIT_AGE_MINUTES)
"""

# DEPRECATION WARNING
import os
import sys

_SHOW_DEPRECATION = os.environ.get("SUPPRESS_DEPRECATION_WARNINGS", "").lower() != "true"

import json
import os
import re
import subprocess
import time  # Used in get_last_commit_changes() for commit age check
from pathlib import Path

# FIX R4-B2: Maximum length for stop_reason to prevent DoS
MAX_STOP_REASON_LENGTH = 10000

# Configuration
MIN_LINES_CHANGED = 20  # Minimum lines to trigger
MIN_ROUNDS = 2
MAX_ROUNDS = 10
MAX_COMMIT_AGE_MINUTES = 5  # Only analyze commits within this window
ANALYZED_COMMITS_FILE = "analyzed_commits.json"  # Track already-analyzed commits
COOLDOWN_MINUTES = 10  # Minimum time between alpha-debug triggers
COOLDOWN_FILE = "alpha_debug_cooldown.json"  # Track last trigger time


# Files/patterns to EXCLUDE from triggering (config, docs, etc.)
EXCLUDE_PATTERNS = [
    ".claude/",  # Claude config
    ".git/",  # Git internals
    ".serena/",  # Serena config
    ".specify/",  # SpecKit config
    ".github/",  # GitHub config
    ".vscode/",  # VSCode config
    "node_modules/",  # Node modules
    "target/",  # Rust target
    "__pycache__/",  # Python cache
    "*.md",  # Documentation
    "*.json",  # Config files (but not package.json code changes)
    "*.yml",  # Config files
    "*.yaml",  # Config files
    "*.toml",  # Config files (but Cargo.toml triggers via .rs)
    "*.lock",  # Lock files
    "*.txt",  # Text files
    "*.log",  # Log files
    "*.csv",  # Data files
    "*.html",  # HTML (usually not logic)
    "*.css",  # Styles
    "CLAUDE.md",
    "README.md",
    "LICENSE",
    "Makefile",  # Build config
    "Dockerfile",  # Docker config
]

# Code file extensions that SHOULD trigger (programming languages)
CODE_EXTENSIONS = [
    # Python
    ".py",
    # Rust
    ".rs",
    # JavaScript/TypeScript
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".mjs",
    ".cjs",
    # Go
    ".go",
    # C/C++
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cc",
    ".cxx",
    # Java/Kotlin
    ".java",
    ".kt",
    ".kts",
    # Ruby
    ".rb",
    # PHP
    ".php",
    # Swift
    ".swift",
    # Scala
    ".scala",
    # Shell scripts (with logic)
    ".sh",
    ".bash",
    # SQL (stored procedures, migrations)
    ".sql",
]

# Directories that indicate code (boost priority)
CODE_DIRECTORIES = [
    "src/",
    "lib/",
    "scripts/",
    "tests/",
    "test/",
    "api/",
    "backend/",
    "frontend/",
    "core/",
    "pkg/",
    "cmd/",
    "internal/",
]

# SpecKit phase completion indicators
# FIX R6-B2: Removed "tasks.md" - too generic, causes false positives
SPECKIT_INDICATORS = [
    "speckit",
    "phase complete",
    "task complete",
    "implementation complete",
    "fase completata",
    "implementazione completata",
    "/speckit.implement",
    "completed tasks.md",  # More specific: require "completed" prefix
]

# Alpha-Evolve triggers (use alpha-evolve instead of alpha-debug)
# FIX B3: Made indicators more specific to reduce false positives
EVOLVE_INDICATORS = [
    "[E]",  # Explicit evolve marker (highest priority)
    "[evolve]",  # Alternative explicit marker
    "alpha-evolve",  # Direct reference
    "multi-implementation",  # Explicit multi-approach
    "explore alternatives",  # Explicit exploration request
    "multiple approaches",  # Explicit multi-approach
    "generate approaches",  # Explicit generation request
    "compare implementations",  # Explicit comparison
]

# Keywords that only trigger evolve if combined with implementation context
EVOLVE_CONTEXT_KEYWORDS = [
    "core algorithm",
    "critical implementation",
    "distance metric",
    "wasserstein",
    "from scratch",
    "new algorithm",
]


def should_exclude_file(filepath: str) -> bool:
    """Check if file should be excluded from triggering.

    FIX R1-B3: Removed redundant 'pattern in filepath_lower' check.
    fnmatch already handles exact matches.
    """
    import fnmatch

    filepath_lower = filepath.lower()

    for pattern in EXCLUDE_PATTERNS:
        if pattern.endswith("/"):
            # Directory pattern - check if path contains this directory
            # FIX R1-B4: Use path separator to avoid partial matches
            dir_name = pattern.rstrip("/")
            if f"/{dir_name}/" in f"/{filepath_lower}/" or filepath_lower.startswith(
                f"{dir_name}/"
            ):
                return True
        elif fnmatch.fnmatch(filepath_lower, pattern.lower()):
            return True
    return False


def is_code_file(filepath: str) -> bool:
    """Check if file is actual code that should trigger debugging.

    FIX R1-B4: Use path separators to avoid partial directory matches.
    """
    filepath_lower = filepath.lower()

    # Check if file has a code extension
    for ext in CODE_EXTENSIONS:
        if filepath_lower.endswith(ext):
            return True

    # Check if file is in a code directory (even without recognized extension)
    # FIX R1-B4: Use path separator to avoid "src" matching "resource"
    for code_dir in CODE_DIRECTORIES:
        dir_name = code_dir.rstrip("/")
        if f"/{dir_name}/" in f"/{filepath_lower}/" or filepath_lower.startswith(f"{dir_name}/"):
            return True

    return False


def get_git_changes() -> dict:
    """Analyze uncommitted changes, filtering out config files."""
    try:
        # Get list of changed files
        # FIX N4-B1: Handle encoding errors gracefully
        # FIX R6-B1, R6-B7: Check returncode to detect silent failures
        result_files = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            errors="replace",  # Replace invalid UTF-8 bytes
        )

        # Also check staged
        result_staged = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            timeout=5,
            errors="replace",
        )

        # FIX R6-B1: Check if git commands succeeded
        if result_files.returncode != 0 and result_staged.returncode != 0:
            # Both failed - likely not a git repo or git not available
            print("Warning: git diff failed (not a git repo?)", file=sys.stderr)
            return _empty_changes("uncommitted")

        all_files = set(
            result_files.stdout.strip().split("\n") + result_staged.stdout.strip().split("\n")
        )
        all_files.discard("")

        # Filter out excluded files, keep only code files
        code_files = [f for f in all_files if is_code_file(f) and not should_exclude_file(f)]

        if not code_files:
            # No code files changed, don't trigger
            return _empty_changes("uncommitted")

        # FIX B1: Use --numstat for accurate line counts (not --stat which truncates)
        # --numstat output: "additions\tdeletions\tfilename"
        result = subprocess.run(
            ["git", "diff", "--numstat", "--cached", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            errors="replace",
        )

        result2 = subprocess.run(
            ["git", "diff", "--numstat"],
            capture_output=True,
            text=True,
            timeout=5,
            errors="replace",
        )

        output = result.stdout + result2.stdout

        # Parse numstat: each line is "added\tdeleted\tfilename"
        lines_added = 0
        lines_deleted = 0
        files_changed = 0
        seen_files = set()  # Avoid double-counting

        for line in output.strip().split("\n"):
            if not line or "\t" not in line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                added_str, deleted_str, filename = parts[0], parts[1], parts[2]

                # FIX R2-B4: Handle renamed files (e.g., "old_name => new_name" or "{old => new}/file.py")
                if "=>" in filename:
                    # Extract the new filename from rename syntax
                    # Handles: "a => b", "{a => b}/file.py", "dir/{a => b}.py"
                    # Replace {old => new} with just new part
                    filename = re.sub(r"\{[^}]* => ([^}]*)\}", r"\1", filename)
                    # Replace "old => new" (full rename) with new part
                    if "=>" in filename:
                        filename = filename.split("=>")[-1].strip()

                # Skip if already counted (file in both staged and unstaged)
                if filename in seen_files:
                    continue
                seen_files.add(filename)

                # Only count if it's a code file
                if is_code_file(filename) and not should_exclude_file(filename):
                    files_changed += 1
                    # Handle binary files (shown as "-")
                    if added_str.isdigit():
                        lines_added += int(added_str)
                    if deleted_str.isdigit():
                        lines_deleted += int(deleted_str)

        return {
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "total_lines": lines_added + lines_deleted,
            "code_files": code_files,
            "source": "uncommitted",
        }
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError) as e:
        # FIX N1-B1: Don't swallow errors silently, log them
        print(f"Warning: git analysis failed: {e}", file=sys.stderr)
        return _empty_changes("uncommitted")


def _empty_changes(source: str = "unknown") -> dict:
    """Return empty changes dict."""
    return {
        "files_changed": 0,
        "lines_added": 0,
        "lines_deleted": 0,
        "total_lines": 0,
        "code_files": [],
        "source": source,
    }


def _get_analyzed_commits_path() -> Path:
    """Get path to analyzed commits tracking file."""
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    return project_dir / ".claude" / "stats" / ANALYZED_COMMITS_FILE


def is_commit_already_analyzed(commit_hash: str) -> bool:
    """Check if a commit was already analyzed to avoid re-triggering."""
    try:
        tracking_file = _get_analyzed_commits_path()
        if not tracking_file.exists():
            return False

        data = json.loads(tracking_file.read_text())
        return commit_hash in data.get("commits", [])
    except (OSError, json.JSONDecodeError):
        return False


def mark_commit_analyzed(commit_hash: str) -> None:
    """Mark a commit as analyzed to prevent re-triggering."""
    try:
        tracking_file = _get_analyzed_commits_path()
        tracking_file.parent.mkdir(parents=True, exist_ok=True)

        if tracking_file.exists():
            data = json.loads(tracking_file.read_text())
        else:
            data = {"commits": []}

        # Keep only last 50 commits to prevent file growth
        commits = data.get("commits", [])
        if commit_hash not in commits:
            commits.append(commit_hash)
            data["commits"] = commits[-50:]

        tracking_file.write_text(json.dumps(data, indent=2))
    except (OSError, json.JSONDecodeError, PermissionError) as e:
        print(f"Warning: Could not track analyzed commit: {e}", file=sys.stderr)


def _get_cooldown_path() -> Path:
    """Get path to cooldown tracking file."""
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    return project_dir / ".claude" / "stats" / COOLDOWN_FILE


def is_in_cooldown() -> tuple[bool, float]:
    """Check if we're still in cooldown period.

    Returns (is_in_cooldown, remaining_minutes).
    """
    try:
        cooldown_file = _get_cooldown_path()
        if not cooldown_file.exists():
            return False, 0

        data = json.loads(cooldown_file.read_text())
        last_trigger = data.get("last_trigger_time", 0)

        elapsed_minutes = (time.time() - last_trigger) / 60
        remaining = COOLDOWN_MINUTES - elapsed_minutes

        if remaining > 0:
            return True, remaining
        return False, 0
    except (OSError, json.JSONDecodeError, ValueError):
        return False, 0


def update_cooldown() -> None:
    """Update cooldown timestamp after triggering."""
    try:
        cooldown_file = _get_cooldown_path()
        cooldown_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "last_trigger_time": time.time(),
            "last_trigger_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        cooldown_file.write_text(json.dumps(data, indent=2))
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not update cooldown: {e}", file=sys.stderr)


def get_last_commit_changes() -> dict:
    """
    Analyze the last commit if it's recent enough.

    FALLBACK: Used when no uncommitted changes exist.
    Only triggers if:
    1. Commit is within MAX_COMMIT_AGE_MINUTES
    2. Commit hasn't been analyzed before
    3. Commit contains code files
    """
    try:
        # Get timestamp and hash of last commit
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct %H"],  # Unix timestamp + hash
            capture_output=True,
            text=True,
            timeout=5,
            errors="replace",
        )

        if result.returncode != 0 or not result.stdout.strip():
            return _empty_changes("last_commit")

        parts = result.stdout.strip().split(" ", 1)
        if len(parts) != 2:
            return _empty_changes("last_commit")

        commit_time = int(parts[0])
        commit_hash = parts[1]

        # Check age
        current_time = time.time()
        age_minutes = (current_time - commit_time) / 60

        if age_minutes > MAX_COMMIT_AGE_MINUTES:
            print(
                f"Last commit too old ({age_minutes:.1f} min > {MAX_COMMIT_AGE_MINUTES} min)",
                file=sys.stderr,
            )
            return _empty_changes("last_commit")

        # Check if already analyzed
        if is_commit_already_analyzed(commit_hash):
            print(f"Commit {commit_hash[:8]} already analyzed", file=sys.stderr)
            return _empty_changes("last_commit")

        # Get files changed in last commit
        result_files = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            errors="replace",
        )

        if result_files.returncode != 0:
            return _empty_changes("last_commit")

        all_files = set(result_files.stdout.strip().split("\n"))
        all_files.discard("")

        # Filter to code files only
        code_files = [f for f in all_files if is_code_file(f) and not should_exclude_file(f)]

        if not code_files:
            return _empty_changes("last_commit")

        # Get line counts with numstat
        result_stats = subprocess.run(
            ["git", "diff", "--numstat", "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            errors="replace",
        )

        lines_added = 0
        lines_deleted = 0
        files_changed = 0

        for line in result_stats.stdout.strip().split("\n"):
            if not line or "\t" not in line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                added_str, deleted_str, filename = parts[0], parts[1], parts[2]

                # Handle renames
                if "=>" in filename:
                    filename = re.sub(r"\{[^}]* => ([^}]*)\}", r"\1", filename)
                    if "=>" in filename:
                        filename = filename.split("=>")[-1].strip()

                if is_code_file(filename) and not should_exclude_file(filename):
                    files_changed += 1
                    if added_str.isdigit():
                        lines_added += int(added_str)
                    if deleted_str.isdigit():
                        lines_deleted += int(deleted_str)

        return {
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "total_lines": lines_added + lines_deleted,
            "code_files": code_files,
            "source": "last_commit",
            "commit_hash": commit_hash,
            "commit_age_minutes": round(age_minutes, 1),
        }

    except (
        subprocess.TimeoutExpired,
        subprocess.SubprocessError,
        OSError,
        ValueError,
    ) as e:
        print(f"Warning: last commit analysis failed: {e}", file=sys.stderr)
        return _empty_changes("last_commit")


def calculate_optimal_rounds(changes: dict) -> int:
    """
    Calculate optimal rounds based on code complexity.

    Euristica:
    - < 50 lines: 2 rounds (quick verification)
    - 50-100 lines: 3 rounds (standard)
    - 100-200 lines: 4 rounds (moderate)
    - 200-400 lines: 5-6 rounds (complex)
    - 400-600 lines: 7-8 rounds (major)
    - > 600 lines: 9-10 rounds (massive)
    """
    total = changes["total_lines"]
    files = changes["files_changed"]

    # Base calculation from lines
    if total < 50:
        base = 2
    elif total < 100:
        base = 3
    elif total < 200:
        base = 4
    elif total < 400:
        base = 5
    elif total < 600:
        base = 7
    else:
        base = 9

    # Adjust for file spread (more files = more integration risk)
    file_factor = min(2, files // 4)  # +1 round per 4 files, max +2

    optimal = base + file_factor
    return max(MIN_ROUNDS, min(MAX_ROUNDS, optimal))


def should_trigger_alpha_debug(stop_reason: str, changes: dict) -> tuple[bool, str]:
    """Decide if alpha-debug should be spawned.

    NOTE: stop_reason is always empty (Stop hooks don't receive it).
    Trigger logic is based ENTIRELY on git changes.
    """

    # MUST have code files changed (not just config)
    code_files = changes.get("code_files", [])
    if not code_files:
        return False, "No code files changed (only config/docs)"

    # Check if there are meaningful changes
    if changes["total_lines"] < MIN_LINES_CHANGED:
        return (
            False,
            f"Only {changes['total_lines']} lines changed (min: {MIN_LINES_CHANGED})",
        )

    # Trigger conditions based on git changes only:

    # 1. Significant code changes (50+ lines)
    if changes["total_lines"] >= 50:
        return (
            True,
            f"Significant code changes: {changes['total_lines']} lines in {len(code_files)} files",
        )

    # 2. Multiple code files changed (2+)
    if len(code_files) >= 2:
        return True, f"Multiple code files changed: {len(code_files)}"

    # 3. Single file with 20+ lines changed
    if changes["total_lines"] >= MIN_LINES_CHANGED:
        return True, f"Code changes: {changes['total_lines']} lines in {code_files[0]}"

    return False, "No trigger conditions met"


def should_use_alpha_evolve(stop_reason: str) -> tuple[bool, str]:
    """Check if we should use alpha-evolve instead of alpha-debug.

    NOTE: stop_reason is always empty (Stop hooks don't receive it).
    Alpha-evolve auto-trigger is effectively disabled.
    Use [E] marker in tasks for explicit alpha-evolve activation.
    """
    stop_lower = stop_reason.lower() if stop_reason else ""

    # Check explicit evolve indicators (high confidence)
    for indicator in EVOLVE_INDICATORS:
        if indicator.lower() in stop_lower:
            return True, f"Evolve indicator detected: '{indicator}'"

    # FIX B3: Check context keywords only if "implement" is also present
    # This prevents triggering on casual mentions of "algorithm" etc.
    implementation_words = ["implement", "create", "build", "develop", "write"]
    has_implementation_context = any(w in stop_lower for w in implementation_words)

    if has_implementation_context:
        for keyword in EVOLVE_CONTEXT_KEYWORDS:
            if keyword.lower() in stop_lower:
                return True, f"Evolve context: '{keyword}' + implementation"

    return False, ""


def create_state_file(state_type: str, max_rounds: int = 5) -> bool:
    """Create state file to enable SubagentStop dispatcher detection.

    FIX R3-B1, R3-B2, R5-B2: State files must exist BEFORE subagent spawns.
    FIX N1-B2: Use proper error handling for file operations.

    Returns True if successful, False otherwise.
    """
    from datetime import datetime

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    stats_dir = project_dir / ".claude" / "stats"

    try:
        stats_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create stats directory: {e}", file=sys.stderr)
        return False

    if state_type == "alpha-debug":
        state_file = stats_dir / "alpha_debug_state.json"
        state = {
            "current_round": 0,
            "consecutive_clean_rounds": 0,
            "total_bugs_found": 0,
            "total_bugs_fixed": 0,
            "max_rounds": max_rounds,
            "started_at": datetime.now().isoformat(),
            "rounds": [],
            "active": True,  # FIX R1-B1: Use 'active' flag instead of current_round > 0
        }
    elif state_type == "alpha-evolve":
        state_file = stats_dir / "alpha_evolve_state.json"
        state = {
            "started_at": datetime.now().isoformat(),
            "active": True,
            "debug_rounds_after": max_rounds,
        }
    else:
        return False

    try:
        state_file.write_text(json.dumps(state, indent=2))
        return True
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not write state file {state_file}: {e}", file=sys.stderr)
        return False


def main():
    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # ==========================================================================
    # KILL SWITCH CHECK: Manual override to disable alpha-debug
    # Create .claude/SKIP_ALPHA_DEBUG in project root to disable
    # ==========================================================================
    kill_switch_paths = [
        Path.cwd() / ".claude" / "SKIP_ALPHA_DEBUG",
        Path.cwd() / "SKIP_ALPHA_DEBUG",
    ]
    for kill_switch in kill_switch_paths:
        if kill_switch.exists():
            print(
                f"Alpha-debug disabled by kill switch: {kill_switch}",
                file=sys.stderr,
            )
            print(json.dumps({"continue": False}))
            sys.exit(0)

    # ==========================================================================
    # COOLDOWN CHECK: Prevent infinite loops by enforcing minimum time between triggers
    # ==========================================================================
    in_cooldown, remaining = is_in_cooldown()
    if in_cooldown:
        print(
            f"Alpha-debug in cooldown ({remaining:.1f} min remaining). Skipping.",
            file=sys.stderr,
        )
        print(json.dumps({"continue": False}))
        sys.exit(0)

    # NOTE: Stop hooks don't receive stop_reason - we rely entirely on git changes
    # The stop_reason field doesn't exist in Stop hook input schema
    stop_reason = ""  # Always empty - trigger logic uses git changes only

    # ==========================================================================
    # DUAL-SOURCE DETECTION: Try uncommitted first, then fallback to last commit
    # ==========================================================================

    # PRIMARY: Analyze uncommitted changes
    changes = get_git_changes()
    should_trigger, trigger_reason = should_trigger_alpha_debug(stop_reason, changes)

    # FALLBACK: If no uncommitted changes, check last commit
    if not should_trigger:
        print("No uncommitted changes, checking last commit...", file=sys.stderr)
        changes = get_last_commit_changes()
        should_trigger, trigger_reason = should_trigger_alpha_debug(stop_reason, changes)

        if should_trigger:
            trigger_reason = f"[LAST COMMIT] {trigger_reason}"

    if not should_trigger:
        # Let Claude stop normally
        print(json.dumps({"continue": False}))
        sys.exit(0)

    # Mark commit as analyzed (if source is last_commit)
    if changes.get("source") == "last_commit" and changes.get("commit_hash"):
        mark_commit_analyzed(changes["commit_hash"])

    # Check if we should use alpha-evolve instead of alpha-debug
    use_evolve, evolve_reason = should_use_alpha_evolve(stop_reason)

    # Calculate optimal rounds
    optimal_rounds = calculate_optimal_rounds(changes)

    # Build source info for message
    source = changes.get("source", "unknown")
    source_info = f"Source: {source}"
    if source == "last_commit":
        commit_hash = changes.get("commit_hash", "")[:8]
        commit_age = changes.get("commit_age_minutes", 0)
        source_info = f"Source: last commit ({commit_hash}, {commit_age} min ago)"

    if use_evolve:
        # FIX R3-B2: Create state file BEFORE spawning subagent
        # FIX R8-B1: Check if state file creation succeeded
        state_created = create_state_file("alpha-evolve", optimal_rounds)
        state_warning = (
            ""
            if state_created
            else "\n⚠️ Warning: State file creation failed - dispatcher may not detect subagent completion.\n"
        )

        # Use Alpha-Evolve for complex/algorithmic tasks
        response = {
            "continue": True,
            "systemMessage": f"""
=== AUTO ALPHA-EVOLVE TRIGGERED ===
Reason: {evolve_reason}
Trigger: {trigger_reason}
{source_info}{state_warning}

Changes detected:
- Files: {changes["files_changed"]}
- Lines: {changes["total_lines"]} (+{changes["lines_added"]}/-{changes["lines_deleted"]})
- Code files: {", ".join(changes.get("code_files", [])[:5])}

INSTRUCTION: Spawn the **alpha-evolve** subagent now.

Alpha-Evolve will:
1. Read SpecKit context (spec.md, plan.md, tasks.md)
2. Generate 3 different implementation approaches
3. Evaluate each with tests + performance + quality
4. Select the best approach (or create ensemble)
5. Write the winning implementation

After Alpha-Evolve completes, Alpha-Debug will run {optimal_rounds} verification rounds.

Start alpha-evolve now.
""",
        }
    else:
        # FIX R3-B1: Create state file BEFORE spawning subagent
        # FIX R8-B1: Check if state file creation succeeded
        state_created = create_state_file("alpha-debug", optimal_rounds)
        state_warning = (
            ""
            if state_created
            else "\n⚠️ Warning: State file creation failed - dispatcher may not detect subagent completion.\n"
        )

        # Standard Alpha-Debug for simpler tasks
        response = {
            "continue": True,
            "systemMessage": f"""
=== AUTO ALPHA-DEBUG TRIGGERED ===
Reason: {trigger_reason}
{source_info}{state_warning}

Changes detected:
- Files: {changes["files_changed"]}
- Lines: {changes["total_lines"]} (+{changes["lines_added"]}/-{changes["lines_deleted"]})

Calculated optimal rounds: {optimal_rounds}
(Based on complexity: {changes["total_lines"]} lines across {changes["files_changed"]} files)

INSTRUCTION: Spawn the alpha-debug subagent now with MAX_ROUNDS={optimal_rounds}.
Focus on the recently modified files. Run iterative bug hunting until:
1. {optimal_rounds} rounds complete, OR
2. 2 consecutive clean rounds (0 bugs found)

Start alpha-debug now.
""",
        }

    # Update cooldown to prevent infinite loops
    update_cooldown()

    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
