#!/usr/bin/env python3
"""
SubagentStop Hook: Unified Dispatcher

SubagentStop does NOT support matchers (unlike PreToolUse/PostToolUse).
This dispatcher reads context to determine which subagent completed
and routes to the appropriate handler.

Detection methods:
1. Check state files (.claude/stats/alpha_debug_state.json)
2. Parse transcript_path for subagent invocation
3. Check environment variables set by parent process
"""

import json
import os
import re
import sys
from pathlib import Path

# Import handlers (they're in the same directory)
HOOKS_DIR = Path(__file__).parent

# FIX R2-B1: Maximum bytes to read from transcript (1MB)
MAX_TRANSCRIPT_BYTES = 1024 * 1024


def safe_write_state(file_path: Path, state: dict) -> bool:
    """Write state file safely with error handling.

    FIX R2-B2: Handle mkdir errors gracefully.
    FIX R2-B3/R4-B3: Note - file locking not used as it adds complexity
    and state files are small/fast to write. Race conditions are unlikely
    in practice since subagents complete sequentially.
    FIX R7-B1: Use atomic write (tmp file + rename) to prevent corruption.

    Returns True if successful, False otherwise.
    """
    import tempfile

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # FIX R7-B1: Atomic write using temp file + rename
        # On POSIX, rename is atomic. On Windows, it may not be, but
        # it's still safer than direct write.
        fd, tmp_path = tempfile.mkstemp(
            dir=file_path.parent, prefix=".tmp_", suffix=".json"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(state, f, indent=2)
            # Atomic rename (POSIX)
            os.replace(tmp_path, file_path)
        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        return True
    except (OSError, IOError, PermissionError) as e:
        # Log error but don't crash
        print(f"Warning: Could not write state file {file_path}: {e}", file=sys.stderr)
        return False


def is_state_expired(state: dict, max_age_hours: int = 2) -> bool:
    """Check if state file is too old (stale from previous session).

    FIX N3-B1, N3-B2: State files shouldn't persist across sessions.
    FIX R10-B9: Handle clock skew (started_at in the future).
    """
    from datetime import datetime, timedelta

    started_at = state.get("started_at")
    if not started_at:
        return False  # No timestamp, assume fresh

    try:
        start_time = datetime.fromisoformat(started_at)
        now = datetime.now()

        # FIX R10-B9: If start_time is more than 1 hour in the future,
        # something is wrong (clock skew). Treat as expired.
        if start_time > now + timedelta(hours=1):
            return True  # Clock skew detected, expire this state

        expiry = start_time + timedelta(hours=max_age_hours)
        return now > expiry
    except (ValueError, TypeError):
        return False  # Invalid timestamp, assume fresh


def detect_subagent_type(input_data: dict) -> str:
    """
    Detect which subagent just completed.

    Returns: "alpha-debug" | "alpha-evolve" | "unknown"
    """
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))

    # Method 1: Check alpha-evolve state file FIRST (takes priority)
    # FIX R1-B2: Now actually created by auto-alpha-debug.py
    alpha_evolve_state = project_dir / ".claude" / "stats" / "alpha_evolve_state.json"
    if alpha_evolve_state.exists():
        try:
            state = json.loads(alpha_evolve_state.read_text())
            # FIX R1-B1: Use 'active' flag instead of current_round
            # FIX N3-B1/N3-B2: Check if state is expired
            if state.get("active", False) and not is_state_expired(state):
                return "alpha-evolve"
            elif is_state_expired(state):
                # Clean up stale state
                alpha_evolve_state.unlink(missing_ok=True)
        except (json.JSONDecodeError, IOError):
            pass

    # Method 2: Check if alpha-debug state file exists
    alpha_debug_state = project_dir / ".claude" / "stats" / "alpha_debug_state.json"
    if alpha_debug_state.exists():
        try:
            state = json.loads(alpha_debug_state.read_text())
            # FIX R1-B1: Use 'active' flag instead of current_round > 0
            # FIX N3-B1/N3-B2: Check if state is expired
            if state.get("active", False) and not is_state_expired(state):
                return "alpha-debug"
            elif is_state_expired(state):
                # Clean up stale state
                alpha_debug_state.unlink(missing_ok=True)
        except (json.JSONDecodeError, IOError):
            pass

    # Method 3: Parse transcript for subagent invocation
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            transcript = Path(transcript_path).resolve()
            # FIX R4-B1, R6-B3: Validate path is under project directory
            # Use is_relative_to() for proper path hierarchy check (not startswith)
            project_resolved = project_dir.resolve()
            try:
                # Python 3.9+ has is_relative_to(), fallback for older versions
                is_under_project = transcript.is_relative_to(project_resolved)
            except AttributeError:
                # Python 3.8 fallback: check if common path equals project
                try:
                    transcript.relative_to(project_resolved)
                    is_under_project = True
                except ValueError:
                    is_under_project = False
            if not is_under_project:
                pass  # Skip - path outside project
            elif transcript.exists():
                # FIX R2-B1: Only read last portion of transcript (tail)
                file_size = transcript.stat().st_size
                read_size = min(file_size, MAX_TRANSCRIPT_BYTES)
                with open(transcript, "rb") as f:
                    if file_size > MAX_TRANSCRIPT_BYTES:
                        f.seek(file_size - MAX_TRANSCRIPT_BYTES)
                    content = f.read(read_size).decode("utf-8", errors="ignore")
                # Look for Task tool invocation with subagent_type
                if (
                    '"subagent_type": "alpha-debug"' in content
                    or '"subagent_type":"alpha-debug"' in content
                ):
                    return "alpha-debug"
                if (
                    '"subagent_type": "alpha-evolve"' in content
                    or '"subagent_type":"alpha-evolve"' in content
                ):
                    return "alpha-evolve"
        except (IOError, OSError, ValueError):
            pass

    # Method 4: Check environment variable (if set by parent)
    env_subagent = os.environ.get("CURRENT_SUBAGENT_TYPE", "")
    if env_subagent in ("alpha-debug", "alpha-evolve"):
        return env_subagent

    return "unknown"


def handle_alpha_debug(input_data: dict, output: str) -> dict:
    """Handle alpha-debug subagent completion."""
    from datetime import datetime

    # Configuration
    MAX_ROUNDS = 5

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    STATE_FILE = project_dir / ".claude" / "stats" / "alpha_debug_state.json"

    # Load state with defaults
    # FIX N1-B3: Merge with defaults instead of full replacement
    default_state = {
        "current_round": 0,
        "consecutive_clean_rounds": 0,
        "total_bugs_found": 0,
        "total_bugs_fixed": 0,
        "started_at": datetime.now().isoformat(),
        "rounds": [],
        "max_rounds": MAX_ROUNDS,
        "active": True,
    }

    if STATE_FILE.exists():
        try:
            loaded = json.loads(STATE_FILE.read_text())
            # Merge loaded state with defaults (loaded takes priority)
            state = {**default_state, **loaded}
        except (json.JSONDecodeError, IOError):
            state = default_state
    else:
        state = default_state

    # FIX R9-B4: Validate and sanitize state values to prevent invalid state
    # Ensure numeric fields are non-negative integers
    for key in [
        "current_round",
        "consecutive_clean_rounds",
        "total_bugs_found",
        "total_bugs_fixed",
        "max_rounds",
    ]:
        if not isinstance(state.get(key), int) or state[key] < 0:
            state[key] = default_state[key]
    # Ensure rounds is a list
    if not isinstance(state.get("rounds"), list):
        state["rounds"] = []

    # Get max_rounds from state or check output for dynamic setting
    max_rounds_match = re.search(r"Setting MAX_ROUNDS\s*=\s*(\d+)", output)
    if max_rounds_match:
        state["max_rounds"] = int(max_rounds_match.group(1))
    session_max_rounds = state.get("max_rounds", MAX_ROUNDS)

    # Parse round results
    bugs_found = 0
    bugs_fixed = 0
    tests_passing = True
    needs_human_review = False

    bugs_match = re.search(r"[Bb]ugs?\s+found:?\s*(\d+)", output)
    if bugs_match:
        bugs_found = int(bugs_match.group(1))

    fixed_match = re.search(r"[Bb]ugs?\s+fixed:?\s*(\d+)", output)
    if fixed_match:
        bugs_fixed = int(fixed_match.group(1))

    if re.search(r"(FAIL|FAILED|ERROR)", output, re.IGNORECASE):
        if not re.search(r"0\s+failed", output, re.IGNORECASE):
            tests_passing = False

    if re.search(
        r"(BLOCKED|NEEDS\s+REVIEW|CRITICAL|human\s+review)", output, re.IGNORECASE
    ):
        needs_human_review = True

    # Check self-assessment
    self_stop_match = re.search(r"Decision:\s*(STOP|CONTINUE)", output, re.IGNORECASE)
    confidence_match = re.search(r"Confidence.*?:\s*(\d+)%", output)
    self_assessment_stop = (
        self_stop_match and self_stop_match.group(1).upper() == "STOP"
    )
    confidence = int(confidence_match.group(1)) if confidence_match else None

    # Increment round
    state["current_round"] += 1
    state["total_bugs_found"] += bugs_found
    state["total_bugs_fixed"] += bugs_fixed

    # Update consecutive clean rounds
    if bugs_found == 0:
        state["consecutive_clean_rounds"] += 1
    else:
        state["consecutive_clean_rounds"] = 0

    # Record round
    # FIX N2-B2: Limit rounds history to prevent unbounded growth
    MAX_ROUNDS_HISTORY = 20
    state["rounds"].append(
        {
            "round": state["current_round"],
            "timestamp": datetime.now().isoformat(),
            "bugs_found": bugs_found,
            "bugs_fixed": bugs_fixed,
            "tests_passing": tests_passing,
        }
    )
    # Keep only last N rounds to prevent memory issues
    if len(state["rounds"]) > MAX_ROUNDS_HISTORY:
        state["rounds"] = state["rounds"][-MAX_ROUNDS_HISTORY:]

    # Decide whether to continue
    continue_loop = True
    reason = ""

    if state["current_round"] >= session_max_rounds:
        continue_loop = False
        reason = f"Maximum rounds ({session_max_rounds}) reached"
    elif not tests_passing:
        continue_loop = False
        reason = "Tests failing - human intervention needed"
    elif needs_human_review:
        continue_loop = False
        reason = "Critical issue detected - needs human review"
    elif state["consecutive_clean_rounds"] >= 2:
        continue_loop = False
        reason = "Code is clean (2 consecutive rounds with 0 bugs)"
    elif self_assessment_stop and confidence and confidence >= 90:
        continue_loop = False
        reason = f"Self-assessment: STOP (confidence: {confidence}%)"
    elif confidence and confidence >= 95:
        continue_loop = False
        reason = f"High confidence ({confidence}%) - no more rounds needed"
    elif bugs_found > 0:
        reason = f"Found {bugs_found} bugs - continuing to verify fixes"
    elif state["consecutive_clean_rounds"] == 1:
        reason = "First clean round - running one more to confirm"
    else:
        reason = "Continuing bug hunt"

    # Save state
    # FIX R8-B2: Check if state write succeeded
    state_saved = safe_write_state(STATE_FILE, state)
    if not state_saved and continue_loop:
        # State save failed but we want to continue - warn in message
        print("Warning: Failed to save alpha-debug state", file=sys.stderr)

    # Build response
    if continue_loop:
        return {
            "continue": True,
            "systemMessage": f"""
=== ALPHA DEBUG ROUND {state["current_round"] + 1}/{session_max_rounds} ===
Previous round: {bugs_found} bugs found, {bugs_fixed} fixed
Total so far: {state["total_bugs_found"]} found, {state["total_bugs_fixed"]} fixed
Consecutive clean: {state["consecutive_clean_rounds"]}

Continue with next analysis round. Focus on different code areas than previous rounds.
""",
        }
    else:
        # Cleanup state file
        STATE_FILE.unlink(missing_ok=True)
        return {
            "continue": False,
            "stopReason": reason,
            "systemMessage": f"""
=== ALPHA DEBUG COMPLETE ===
Reason: {reason}

Final Statistics:
- Total rounds: {state["current_round"]}
- Total bugs found: {state["total_bugs_found"]}
- Total bugs fixed: {state["total_bugs_fixed"]}
- Success rate: {(state["total_bugs_fixed"] / max(1, state["total_bugs_found"]) * 100):.0f}%
""",
        }


def handle_alpha_evolve(input_data: dict, output: str) -> dict:
    """Handle alpha-evolve subagent completion."""

    DEFAULT_DEBUG_ROUNDS = 3

    # Parse evolve results
    approaches_generated = 0
    winner_selected = False
    winner_name = ""
    winner_score = 0
    tests_passed = False
    file_written = ""

    # FIX R2-B5: More flexible regex patterns for evolve output parsing
    # FIX R5-B4: Support multiple output formats (markdown tables, plain text)
    approaches_match = re.search(r"[Aa]pproaches?\s*(?:generated)?:?\s*(\d+)", output)
    if approaches_match:
        approaches_generated = int(approaches_match.group(1))

    # Multiple patterns for winner detection
    winner_patterns = [
        r"(?:Winner|Selected|Best|Chosen):?\s*(?:Approach\s+)?([A-Za-z0-9_-]+)",
        r"Approach\s+([A-Za-z0-9_-]+)\s+(?:wins|selected|chosen)",
        r"(?:Using|Implementing)\s+(?:Approach\s+)?([A-Za-z0-9_-]+)",
        r"\*\*([A-Za-z0-9_-]+)\*\*\s+(?:wins|selected)",  # Markdown bold
    ]
    for pattern in winner_patterns:
        winner_match = re.search(pattern, output, re.IGNORECASE)
        if winner_match:
            winner_selected = True
            winner_name = winner_match.group(1)
            break

    score_match = re.search(r"score:?\s*(\d+)\s*/\s*(\d+)", output, re.IGNORECASE)
    if score_match:
        winner_score = int(score_match.group(1))

    if re.search(r"Tests?:?\s*(?:all\s+)?PASS", output, re.IGNORECASE):
        tests_passed = True

    # Multiple patterns for file written
    file_patterns = [
        r"[Ii]mplementation\s+written\s+to:?\s*(\S+)",
        r"[Ww]rote\s+(?:to\s+)?(\S+\.py)",
        r"[Cc]reated\s+(\S+\.py)",
        r"[Ff]ile:?\s*(\S+\.py)",
    ]
    for pattern in file_patterns:
        file_match = re.search(pattern, output)
        if file_match:
            file_written = file_match.group(1)
            break

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    evolve_state = project_dir / ".claude" / "stats" / "alpha_evolve_state.json"

    # FIX R6-B5: Don't delete state file until we know we can proceed
    if not winner_selected:
        # Still cleanup evolve state on failure
        evolve_state.unlink(missing_ok=True)
        return {
            "continue": False,
            "systemMessage": """
=== ALPHA-EVOLVE INCOMPLETE ===
Could not detect a winning approach in the output.
Please review the alpha-evolve results manually.
""",
        }

    # Create alpha-debug state to signal next subagent
    # FIX R1-B1: Include 'active' flag for detection
    # FIX R6-B6: Include 'started_at' for expiry tracking
    # FIX R7-B5: Write debug state BEFORE deleting evolve state
    #            If write fails, evolve state remains for retry
    from datetime import datetime

    debug_state = project_dir / ".claude" / "stats" / "alpha_debug_state.json"
    write_success = safe_write_state(
        debug_state,
        {
            "current_round": 0,
            "consecutive_clean_rounds": 0,
            "total_bugs_found": 0,
            "total_bugs_fixed": 0,
            "max_rounds": DEFAULT_DEBUG_ROUNDS,
            "rounds": [],
            "triggered_by": "alpha-evolve",
            "active": True,  # FIX R1-B1: Enable detection
            "started_at": datetime.now().isoformat(),  # FIX R6-B6: Enable expiry
        },
    )

    # FIX R7-B5: Only cleanup evolve state if debug state was written successfully
    if write_success:
        evolve_state.unlink(missing_ok=True)
    else:
        # Keep evolve state so we can retry
        print(
            "Warning: Failed to create debug state, keeping evolve state",
            file=sys.stderr,
        )

    return {
        "continue": True,
        "systemMessage": f"""
=== ALPHA-EVOLVE COMPLETE - TRIGGERING DEBUG ===

Evolution Results:
- Approaches generated: {approaches_generated}
- Winner: {winner_name} (score: {winner_score})
- Tests: {"PASS" if tests_passed else "PENDING"}
- File: {file_written}

Now spawning alpha-debug with MAX_ROUNDS={DEFAULT_DEBUG_ROUNDS} for verification.

INSTRUCTION: Spawn **alpha-debug** subagent now with MAX_ROUNDS={DEFAULT_DEBUG_ROUNDS}.
Focus on the newly written implementation: {file_written}
Run iterative bug hunting to verify the evolved solution.

Start alpha-debug now.
""",
    }


def handle_unknown(input_data: dict) -> dict:
    """Handle unknown subagent - just let it complete normally."""
    return {"continue": False}


def main():
    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No valid JSON, let subagent continue default behavior
        print(json.dumps({"continue": False}))
        sys.exit(0)

    # Skip if stop_hook_active (prevent infinite loops)
    if input_data.get("stop_hook_active", False):
        print(json.dumps({"continue": False}))
        sys.exit(0)

    # Get any output that might be available
    # FIX N1-B4: Validate output is a string
    output = input_data.get("output", input_data.get("result", ""))
    if not isinstance(output, str):
        output = str(output) if output else ""

    # Detect subagent type
    subagent_type = detect_subagent_type(input_data)

    # Dispatch to appropriate handler
    if subagent_type == "alpha-debug":
        response = handle_alpha_debug(input_data, output)
    elif subagent_type == "alpha-evolve":
        response = handle_alpha_evolve(input_data, output)
    else:
        response = handle_unknown(input_data)

    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
