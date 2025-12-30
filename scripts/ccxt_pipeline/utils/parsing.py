"""Safe parsing utilities for CCXT API responses.

Handles edge cases where API returns explicit None values instead of missing keys.
The pattern `data.get("key", default)` returns None (not default) when key exists
with value None. These utilities provide None-safe conversions.

Usage in fetchers (Phase 7):
    from scripts.ccxt_pipeline.utils.parsing import safe_float, safe_int

    open_interest=safe_float(data.get("openInterestAmount")),
    open_interest_value=safe_float(data.get("openInterestValue")),

Warning:
    These utilities return 0.0/0/"" as defaults. This works for Pydantic fields
    with `ge=0` constraints but will FAIL validation for fields with `gt=0`
    constraints (e.g., Liquidation.quantity, price, value).

    For `gt=0` fields, either:
    1. Validate data before calling safe_float (skip invalid records)
    2. Use a positive default: safe_float(data, default=0.001)
    3. Use Optional[float] fields in the model
"""

import math
from typing import Any


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float, returning default if None or invalid.

    Args:
        value: Value to convert (can be None, str, int, float).
        default: Default value if conversion fails.

    Returns:
        Float value or default.

    Examples:
        >>> safe_float(123.45)
        123.45
        >>> safe_float("123.45")
        123.45
        >>> safe_float(None)
        0.0
        >>> safe_float(None, -1.0)
        -1.0
        >>> safe_float("invalid")
        0.0
    """
    if value is None:
        return default
    try:
        result = float(value)
        # Reject NaN and Inf - these cause silent bugs in trading calculations
        if not math.isfinite(result):
            return default
        return result
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convert value to int, returning default if None or invalid.

    Args:
        value: Value to convert (can be None, str, int, float).
        default: Default value if conversion fails.

    Returns:
        Integer value or default.

    Examples:
        >>> safe_int(123)
        123
        >>> safe_int("123")
        123
        >>> safe_int(123.9)
        123
        >>> safe_int(None)
        0
        >>> safe_int("invalid")
        0
    """
    if value is None:
        return default
    try:
        result = float(value)
        # Check for NaN/Inf before converting to int (int(inf) raises OverflowError)
        if not math.isfinite(result):
            return default
        return int(result)
    except (ValueError, TypeError, OverflowError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Convert value to string, returning default if None.

    Args:
        value: Value to convert.
        default: Default value if None.

    Returns:
        String value or default.

    Examples:
        >>> safe_str("hello")
        'hello'
        >>> safe_str(123)
        '123'
        >>> safe_str(None)
        ''
        >>> safe_str(None, "N/A")
        'N/A'
    """
    if value is None:
        return default
    return str(value)
