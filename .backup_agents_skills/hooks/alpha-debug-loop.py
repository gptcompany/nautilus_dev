#!/usr/bin/env python3
"""
SubagentStop Hook: Alpha Debug Loop Controller

Controls when the alpha-debug subagent should continue or stop.
Implements AlphaEvolve-inspired iterative debugging cycles.

Stop conditions:
1. MAX_ROUNDS reached (default: 5)
2. ZERO bugs found in 2 consecutive rounds
3. Tests failing after fix attempt
4. Critical issue requiring human review
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime

# Configuration
# Dynamic MAX_ROUNDS: can be overridden via environment or systemMessage
MAX_ROUNDS = int(os.environ.get("ALPHA_DEBUG_MAX_ROUNDS", "5"))
STATE_FILE = (
    Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    / ".claude"
    / "stats"
    / "alpha_debug_state.json"
)


def load_state() -> dict:
    """Load persistent state across rounds."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, IOError) as e:
            # FIX B7: Don't swallow errors silently, log them
            import sys

            print(f"Warning: Could not load state file: {e}", file=sys.stderr)
    return {
        "current_round": 0,
        "consecutive_clean_rounds": 0,
        "total_bugs_found": 0,
        "total_bugs_fixed": 0,
        "started_at": datetime.now().isoformat(),
        "rounds": [],
        "max_rounds": MAX_ROUNDS,  # Store default max_rounds in state
    }


def save_state(state: dict):
    """Persist state for next round."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def parse_round_results(output: str) -> dict:
    """Extract metrics from subagent output."""
    results = {
        "bugs_found": 0,
        "bugs_fixed": 0,
        "tests_passing": True,
        "needs_human_review": False,
    }

    # Parse "Bugs found: N" pattern
    bugs_match = re.search(r"[Bb]ugs?\s+found:?\s*(\d+)", output)
    if bugs_match:
        results["bugs_found"] = int(bugs_match.group(1))

    # Parse "Bugs fixed: N" pattern
    fixed_match = re.search(r"[Bb]ugs?\s+fixed:?\s*(\d+)", output)
    if fixed_match:
        results["bugs_fixed"] = int(fixed_match.group(1))

    # Check test status
    if re.search(r"(FAIL|FAILED|ERROR)", output, re.IGNORECASE):
        if not re.search(r"0\s+failed", output, re.IGNORECASE):
            results["tests_passing"] = False

    # Check for human review needed
    if re.search(
        r"(BLOCKED|NEEDS\s+REVIEW|CRITICAL|human\s+review)", output, re.IGNORECASE
    ):
        results["needs_human_review"] = True

    return results


def should_continue(
    state: dict, round_results: dict, max_rounds: int, extra: dict = None
) -> tuple[bool, str]:
    """Determine if another round should run."""
    extra = extra or {}

    # Condition 1: Max rounds reached (FIX B6: use parameter instead of global)
    if state["current_round"] >= max_rounds:
        return False, f"Maximum rounds ({max_rounds}) reached"

    # Condition 2: Tests failing
    if not round_results["tests_passing"]:
        return False, "Tests failing - human intervention needed"

    # Condition 3: Needs human review
    if round_results["needs_human_review"]:
        return False, "Critical issue detected - needs human review"

    # Condition 4: Two consecutive clean rounds
    if state["consecutive_clean_rounds"] >= 2:
        return False, "Code is clean (2 consecutive rounds with 0 bugs)"

    # Condition 5: Self-assessment says STOP with high confidence
    if extra.get("self_assessment_stop") and extra.get("confidence", 0) >= 90:
        return False, f"Self-assessment: STOP (confidence: {extra['confidence']}%)"

    # Condition 6: Very high confidence even without explicit STOP
    confidence = extra.get("confidence")
    if confidence is not None and confidence >= 95:
        return (
            False,
            f"High confidence ({confidence}%) - no more rounds needed",
        )

    # Continue if bugs were found (more work to do)
    if round_results["bugs_found"] > 0:
        return (
            True,
            f"Found {round_results['bugs_found']} bugs - continuing to verify fixes",
        )

    # First clean round - do one more to confirm
    if state["consecutive_clean_rounds"] == 1:
        return True, "First clean round - running one more to confirm"

    # Default: continue
    return True, "Continuing bug hunt"


def main():
    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No valid JSON, let subagent continue default behavior
        sys.exit(0)

    # Only handle alpha-debug subagent
    agent_type = input_data.get("subagent_type", input_data.get("agent_type", ""))
    if agent_type != "alpha-debug":
        # Not our subagent, defer to default checkpoint behavior
        sys.exit(0)

    # Get subagent output
    output = input_data.get("output", input_data.get("result", ""))

    # Load state
    state = load_state()

    # FIX B6: Use state-based max_rounds instead of global mutation
    # Check for dynamic MAX_ROUNDS in output (from complexity assessment)
    max_rounds_match = re.search(r"Setting MAX_ROUNDS\s*=\s*(\d+)", output)
    if max_rounds_match:
        state["max_rounds"] = int(max_rounds_match.group(1))
    elif "max_rounds" not in state:
        state["max_rounds"] = MAX_ROUNDS  # Use default

    # Use state's max_rounds for this session
    session_max_rounds = state["max_rounds"]

    # Check for self-assessment decision
    self_stop_match = re.search(r"Decision:\s*(STOP|CONTINUE)", output, re.IGNORECASE)
    confidence_match = re.search(r"Confidence.*?:\s*(\d+)%", output)

    round_results_extra = {
        "self_assessment_stop": self_stop_match
        and self_stop_match.group(1).upper() == "STOP",
        "confidence": int(confidence_match.group(1)) if confidence_match else None,
    }

    # Increment round counter
    state["current_round"] += 1

    # Parse this round's results
    round_results = parse_round_results(output)

    # Update statistics
    state["total_bugs_found"] += round_results["bugs_found"]
    state["total_bugs_fixed"] += round_results["bugs_fixed"]

    # Update consecutive clean rounds
    if round_results["bugs_found"] == 0:
        state["consecutive_clean_rounds"] += 1
    else:
        state["consecutive_clean_rounds"] = 0

    # Record this round
    state["rounds"].append(
        {
            "round": state["current_round"],
            "timestamp": datetime.now().isoformat(),
            **round_results,
        }
    )

    # Decide whether to continue (FIX B6: pass session_max_rounds)
    continue_loop, reason = should_continue(
        state, round_results, session_max_rounds, round_results_extra
    )

    # Save state
    save_state(state)

    # Build response
    response = {
        "continue": continue_loop,
        "stopReason": None if continue_loop else reason,
    }

    if continue_loop:
        # Inject context for next round (FIX B6: use session_max_rounds)
        response["systemMessage"] = f"""
=== ALPHA DEBUG ROUND {state["current_round"] + 1}/{session_max_rounds} ===
Previous round: {round_results["bugs_found"]} bugs found, {round_results["bugs_fixed"]} fixed
Total so far: {state["total_bugs_found"]} found, {state["total_bugs_fixed"]} fixed
Consecutive clean: {state["consecutive_clean_rounds"]}

Continue with next analysis round. Focus on different code areas than previous rounds.
"""
    else:
        # Final summary
        response["systemMessage"] = f"""
=== ALPHA DEBUG COMPLETE ===
Reason: {reason}

Final Statistics:
- Total rounds: {state["current_round"]}
- Total bugs found: {state["total_bugs_found"]}
- Total bugs fixed: {state["total_bugs_fixed"]}
- Success rate: {(state["total_bugs_fixed"] / max(1, state["total_bugs_found"]) * 100):.0f}%

State saved to: {STATE_FILE}
"""
        # Reset state for next alpha-debug session
        STATE_FILE.unlink(missing_ok=True)

    # Output response
    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
