"""
API Contract: Patching System

This module defines the public interface for the EVOLVE-BLOCK patching system.
Implementation should match these signatures exactly.
"""

from typing import Dict, Any, Tuple


def apply_patch(parent_code: str, diff: Dict[str, Any]) -> str:
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

    Example:
        >>> parent = '''
        ... def strategy():
        ...     # === EVOLVE-BLOCK: logic ===
        ...     return 42
        ...     # === END EVOLVE-BLOCK ===
        ... '''
        >>> diff = {"blocks": {"logic": "return 100"}}
        >>> result = apply_patch(parent, diff)
        >>> "return 100" in result
        True
    """
    ...


def extract_blocks(code: str) -> Dict[str, str]:
    """
    Extract all EVOLVE-BLOCK sections from code.

    Args:
        code: Strategy code containing EVOLVE-BLOCK markers

    Returns:
        Dict mapping block names to their content

    Example:
        >>> code = '''
        ... # === EVOLVE-BLOCK: entry ===
        ... buy()
        ... # === END EVOLVE-BLOCK ===
        ... '''
        >>> blocks = extract_blocks(code)
        >>> "entry" in blocks
        True
    """
    ...


def validate_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate Python syntax of code.

    Args:
        code: Python code to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if syntax is correct
        - error_message: Empty string if valid, error details if invalid

    Example:
        >>> valid, msg = validate_syntax("x = 1")
        >>> valid
        True
        >>> valid, msg = validate_syntax("x = ")
        >>> valid
        False
    """
    ...
