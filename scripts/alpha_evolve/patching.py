"""
EVOLVE-BLOCK patching system for surgical code mutations.

Provides functionality to:
- Extract named blocks from strategy code
- Apply patches (full replacement or surgical block replacement)
- Validate Python syntax of patched code
"""

import ast
import re
from typing import Any

# Regex pattern for EVOLVE-BLOCK markers
# Matches:
#   # === EVOLVE-BLOCK: <name> ===
#   <body>
#   # === END EVOLVE-BLOCK ===
BLOCK_RE = re.compile(
    r"(?P<head>^[ \t]*# === EVOLVE-BLOCK:\s*(?P<name>[\w-]+).*?$\n)"  # head with name (supports hyphens)
    r"(?P<body>.*?)"  # body (lazy match)
    r"(?P<tail>^[ \t]*# === END EVOLVE-BLOCK.*?$)",  # tail
    re.M | re.S,  # Multiline + Dotall
)


def apply_patch(parent_code: str, diff: dict[str, Any]) -> str:
    """
    Apply a mutation patch to strategy code.

    Args:
        parent_code: Original strategy code with EVOLVE-BLOCK markers
        diff: Mutation specification, one of:
            - {"code": "..."}: Full code replacement
            - {"blocks": {"name": "..."}}: Surgical block replacement

    Returns:
        Patched code as string

    Raises:
        ValueError: If EVOLVE-BLOCK markers are malformed or missing
    """
    # Full code replacement
    if "code" in diff:
        return cast(str, diff["code"])

    # Surgical block replacement
    if "blocks" not in diff:
        return parent_code

    blocks_to_replace = diff["blocks"]
    result = parent_code

    for block_name, new_body in blocks_to_replace.items():
        result = _replace_block(result, block_name, new_body)

    return result


def _replace_block(code: str, block_name: str, new_body: str) -> str:
    """Replace a specific block's content while preserving markers."""
    # Find all blocks
    matches = list(BLOCK_RE.finditer(code))

    # Find matching block
    target_match = None
    for match in matches:
        if match.group("name") == block_name:
            target_match = match
            break

    if target_match is None:
        raise ValueError(f"EVOLVE-BLOCK '{block_name}' not found or malformed markers")

    # Detect indentation from the marker line
    head = target_match.group("head")
    indent = len(head) - len(head.lstrip())
    indent_str = head[:indent]

    # Add indentation to new body lines
    indented_body = _indent_code(new_body, indent_str)

    # Reconstruct the block (normalize trailing newlines)
    start, end = target_match.span()
    head_line = target_match.group("head")
    tail_line = target_match.group("tail")

    new_block = head_line + indented_body.rstrip("\n") + "\n" + tail_line
    result = code[:start] + new_block + code[end:]

    return result


def _indent_code(code: str, indent_str: str) -> str:
    """
    Add indentation to each line of code.

    First dedents the code to remove any existing indentation,
    then applies the target indentation. This ensures consistent
    indentation regardless of whether the input uses tabs or spaces.
    """
    # First dedent to normalize
    dedented = _dedent_body(code)
    lines = dedented.split("\n")
    indented_lines = []
    for line in lines:
        if line.strip():  # Non-empty line
            indented_lines.append(indent_str + line)
        else:  # Empty line
            indented_lines.append("")
    return "\n".join(indented_lines)


def extract_blocks(code: str) -> dict[str, str]:
    """
    Extract all EVOLVE-BLOCK sections from code.

    Args:
        code: Strategy code containing EVOLVE-BLOCK markers

    Returns:
        Dict mapping block names to their content (without indentation)
    """
    blocks = {}
    for match in BLOCK_RE.finditer(code):
        name = match.group("name")
        body = match.group("body")
        # Strip common leading whitespace from body
        blocks[name] = _dedent_body(body)
    return blocks


def _dedent_body(body: str) -> str:
    """Remove common leading whitespace from body."""
    lines = body.split("\n")
    # Filter out empty lines for indent calculation
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return body.strip()

    # Find minimum indent
    min_indent = min(len(line) - len(line.lstrip()) for line in non_empty)

    # Remove that indent from all lines
    dedented = []
    for line in lines:
        if line.strip():
            dedented.append(line[min_indent:])
        else:
            dedented.append("")

    return "\n".join(dedented).strip()


def validate_syntax(code: str) -> tuple[bool, str]:
    """
    Validate Python syntax of code.

    Args:
        code: Python code to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if syntax is correct
        - error_message: Empty string if valid, error details if invalid
    """
    if not code.strip():
        return True, ""

    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
