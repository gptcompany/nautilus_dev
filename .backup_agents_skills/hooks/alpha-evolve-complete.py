#!/usr/bin/env python3
"""
SubagentStop Hook: Alpha-Evolve Completion Handler

After alpha-evolve completes (selects best implementation),
this hook triggers alpha-debug for verification rounds.

The flow is:
1. alpha-evolve generates multiple approaches
2. alpha-evolve evaluates and selects best
3. This hook detects completion
4. Triggers alpha-debug for bug hunting on the winning implementation
"""

import json
import re
import sys

# Configuration
DEFAULT_DEBUG_ROUNDS = 3  # Fewer rounds since code was just evolved/validated


def parse_evolve_results(output: str) -> dict:
    """Extract results from alpha-evolve output."""
    results = {
        "approaches_generated": 0,
        "winner_selected": False,
        "winner_name": "",
        "winner_score": 0,
        "tests_passed": False,
        "file_written": "",
    }

    # Parse "Approaches generated: N"
    approaches_match = re.search(r"[Aa]pproaches?\s+generated:?\s*(\d+)", output)
    if approaches_match:
        results["approaches_generated"] = int(approaches_match.group(1))

    # Parse "Winner: Approach X" or "Selected: Approach X"
    winner_match = re.search(
        r"(?:Winner|Selected):?\s*(?:Approach\s+)?([A-Za-z]+)", output
    )
    if winner_match:
        results["winner_selected"] = True
        results["winner_name"] = winner_match.group(1)

    # Parse "score: N/40" or similar
    score_match = re.search(r"score:?\s*(\d+)/(\d+)", output, re.IGNORECASE)
    if score_match:
        results["winner_score"] = int(score_match.group(1))

    # Check if tests passed
    if re.search(r"Tests?:?\s*PASS", output, re.IGNORECASE):
        results["tests_passed"] = True

    # Parse "Implementation written to: path"
    file_match = re.search(r"[Ii]mplementation\s+written\s+to:?\s*(\S+)", output)
    if file_match:
        results["file_written"] = file_match.group(1)

    return results


def main():
    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Only handle alpha-evolve subagent
    agent_type = input_data.get("subagent_type", input_data.get("agent_type", ""))
    if agent_type != "alpha-evolve":
        # Not our subagent
        sys.exit(0)

    # Get subagent output
    output = input_data.get("output", input_data.get("result", ""))

    # Parse evolve results
    results = parse_evolve_results(output)

    # Only trigger debug if evolution was successful
    if not results["winner_selected"]:
        # Evolution didn't complete successfully, don't trigger debug
        response = {
            "continue": False,
            "systemMessage": """
=== ALPHA-EVOLVE INCOMPLETE ===
Could not detect a winning approach in the output.
Please review the alpha-evolve results manually.
""",
        }
        print(json.dumps(response))
        sys.exit(0)

    # Evolution successful - trigger alpha-debug
    response = {
        "continue": True,
        "systemMessage": f"""
=== ALPHA-EVOLVE COMPLETE - TRIGGERING DEBUG ===

Evolution Results:
- Approaches generated: {results["approaches_generated"]}
- Winner: {results["winner_name"]} (score: {results["winner_score"]})
- Tests: {"PASS" if results["tests_passed"] else "PENDING"}
- File: {results["file_written"]}

Now spawning alpha-debug with MAX_ROUNDS={DEFAULT_DEBUG_ROUNDS} for verification.

INSTRUCTION: Spawn **alpha-debug** subagent now with MAX_ROUNDS={DEFAULT_DEBUG_ROUNDS}.
Focus on the newly written implementation: {results["file_written"]}
Run iterative bug hunting to verify the evolved solution.

Start alpha-debug now.
""",
    }

    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
