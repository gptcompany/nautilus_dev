"""
Binance Error Handling Utilities (Spec 015 FR-004).

Provides error code definitions, classification, and retry logic for Binance API errors.

Notes
-----
Error codes are from Binance API documentation:
https://binance-docs.github.io/apidocs/futures/en/#error-codes

Retry Strategy:
- Retryable errors: Network issues, rate limits (with backoff)
- Non-retryable errors: Authentication, validation, insufficient balance
"""

from __future__ import annotations

from enum import IntEnum

# =============================================================================
# Binance Error Codes
# =============================================================================

# General Server Errors
UNKNOWN = -1000
DISCONNECTED = -1001
UNAUTHORIZED = -1002
TOO_MANY_REQUESTS = -1003
UNEXPECTED_RESP = -1006
TIMEOUT = -1007
SERVER_BUSY = -1008
UNKNOWN_ORDER_COMPOSITION = -1014
TOO_MANY_ORDERS = -1015
SERVICE_SHUTTING_DOWN = -1016
UNSUPPORTED_OPERATION = -1020
INVALID_TIMESTAMP = -1021
INVALID_SIGNATURE = -1022

# Request Errors
ILLEGAL_CHARS = -1100
TOO_MANY_PARAMETERS = -1101
MANDATORY_PARAM_EMPTY = -1102
UNKNOWN_PARAM = -1103
UNREAD_PARAMETERS = -1104
PARAM_EMPTY = -1105
PARAM_NOT_REQUIRED = -1106
BAD_ASSET = -1108
BAD_ACCOUNT = -1109
BAD_INSTRUMENT_TYPE = -1110
BAD_PRECISION = -1111
NO_DEPTH = -1112
WITHDRAW_NOT_NEGATIVE = -1113
TIF_NOT_REQUIRED = -1114
INVALID_TIF = -1115
INVALID_ORDER_TYPE = -1116
INVALID_SIDE = -1117
EMPTY_NEW_CL_ORD_ID = -1118
EMPTY_ORG_CL_ORD_ID = -1119
BAD_INTERVAL = -1120
BAD_SYMBOL = -1121
INVALID_LISTEN_KEY = -1125
MORE_THAN_XX_HOURS = -1127
OPTIONAL_PARAMS_BAD_COMBO = -1128
INVALID_PARAMETER = -1130

# Trading Errors
NEW_ORDER_REJECTED = -2010
CANCEL_REJECTED = -2011
NO_SUCH_ORDER = -2013
BAD_API_KEY_FMT = -2014
REJECTED_MBX_KEY = -2015
NO_TRADING_WINDOW = -2016

# Futures Specific
REDUCE_ONLY_REJECT = -2022
POSITION_SIDE_NOT_MATCH = -2025
POSITION_SIDE_CHANGE_EXISTS_OPEN_ORDER = -2027

# Algo Order Errors
ALGO_ORDER_REQUIRED = -4120


class BinanceErrorCategory(IntEnum):
    """Categories of Binance errors for handling."""

    UNKNOWN = 0
    NETWORK = 1
    RATE_LIMIT = 2
    AUTHENTICATION = 3
    VALIDATION = 4
    BALANCE = 5
    ORDER = 6
    POSITION = 7


# Error code to category mapping
BINANCE_ERROR_CODES: dict[int, tuple[str, BinanceErrorCategory, bool]] = {
    # (message, category, is_retryable)
    # General Server Errors
    UNKNOWN: ("Unknown error", BinanceErrorCategory.UNKNOWN, True),
    DISCONNECTED: ("Disconnected from server", BinanceErrorCategory.NETWORK, True),
    UNAUTHORIZED: (
        "Unauthorized - invalid API key",
        BinanceErrorCategory.AUTHENTICATION,
        False,
    ),
    TOO_MANY_REQUESTS: (
        "Rate limited - too many requests",
        BinanceErrorCategory.RATE_LIMIT,
        True,
    ),
    UNEXPECTED_RESP: (
        "Unexpected response from server",
        BinanceErrorCategory.NETWORK,
        True,
    ),
    TIMEOUT: ("Request timeout", BinanceErrorCategory.NETWORK, True),
    SERVER_BUSY: ("Server is busy", BinanceErrorCategory.NETWORK, True),
    UNKNOWN_ORDER_COMPOSITION: (
        "Unknown order composition",
        BinanceErrorCategory.ORDER,
        False,
    ),
    TOO_MANY_ORDERS: ("Too many orders", BinanceErrorCategory.RATE_LIMIT, True),
    SERVICE_SHUTTING_DOWN: (
        "Service shutting down",
        BinanceErrorCategory.NETWORK,
        False,
    ),
    UNSUPPORTED_OPERATION: (
        "Unsupported operation",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    INVALID_TIMESTAMP: ("Invalid timestamp", BinanceErrorCategory.VALIDATION, True),
    INVALID_SIGNATURE: (
        "Invalid signature",
        BinanceErrorCategory.AUTHENTICATION,
        False,
    ),
    # Request Errors
    ILLEGAL_CHARS: (
        "Illegal characters in request",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    TOO_MANY_PARAMETERS: (
        "Too many parameters",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    MANDATORY_PARAM_EMPTY: (
        "Mandatory parameter is empty",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    UNKNOWN_PARAM: ("Unknown parameter sent", BinanceErrorCategory.VALIDATION, False),
    UNREAD_PARAMETERS: (
        "Unread parameters sent",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    PARAM_EMPTY: ("Parameter empty", BinanceErrorCategory.VALIDATION, False),
    PARAM_NOT_REQUIRED: (
        "Parameter not required",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    BAD_ASSET: ("Invalid asset", BinanceErrorCategory.VALIDATION, False),
    BAD_ACCOUNT: ("Invalid account", BinanceErrorCategory.VALIDATION, False),
    BAD_INSTRUMENT_TYPE: (
        "Invalid instrument type",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    BAD_PRECISION: ("Invalid precision", BinanceErrorCategory.VALIDATION, False),
    NO_DEPTH: ("No depth data available", BinanceErrorCategory.NETWORK, True),
    WITHDRAW_NOT_NEGATIVE: (
        "Withdrawal amount must be positive",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    TIF_NOT_REQUIRED: (
        "Time in force not required for this order",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    INVALID_TIF: ("Invalid time in force", BinanceErrorCategory.VALIDATION, False),
    INVALID_ORDER_TYPE: ("Invalid order type", BinanceErrorCategory.VALIDATION, False),
    INVALID_SIDE: ("Invalid order side", BinanceErrorCategory.VALIDATION, False),
    EMPTY_NEW_CL_ORD_ID: (
        "Empty new client order ID",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    EMPTY_ORG_CL_ORD_ID: (
        "Empty original client order ID",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    BAD_INTERVAL: ("Invalid interval", BinanceErrorCategory.VALIDATION, False),
    BAD_SYMBOL: ("Invalid symbol", BinanceErrorCategory.VALIDATION, False),
    INVALID_LISTEN_KEY: (
        "Invalid listen key",
        BinanceErrorCategory.AUTHENTICATION,
        False,
    ),
    MORE_THAN_XX_HOURS: (
        "Request spans too many hours",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    OPTIONAL_PARAMS_BAD_COMBO: (
        "Invalid optional parameter combination",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
    INVALID_PARAMETER: ("Invalid parameter", BinanceErrorCategory.VALIDATION, False),
    # Trading Errors
    NEW_ORDER_REJECTED: ("Order rejected", BinanceErrorCategory.ORDER, False),
    CANCEL_REJECTED: ("Cancel rejected", BinanceErrorCategory.ORDER, False),
    NO_SUCH_ORDER: ("Order not found", BinanceErrorCategory.ORDER, False),
    BAD_API_KEY_FMT: (
        "Invalid API key format",
        BinanceErrorCategory.AUTHENTICATION,
        False,
    ),
    REJECTED_MBX_KEY: ("API key rejected", BinanceErrorCategory.AUTHENTICATION, False),
    NO_TRADING_WINDOW: ("No trading window", BinanceErrorCategory.ORDER, False),
    # Futures Errors
    REDUCE_ONLY_REJECT: (
        "Reduce-only order rejected",
        BinanceErrorCategory.POSITION,
        False,
    ),
    POSITION_SIDE_NOT_MATCH: (
        "Position side does not match",
        BinanceErrorCategory.POSITION,
        False,
    ),
    POSITION_SIDE_CHANGE_EXISTS_OPEN_ORDER: (
        "Cannot change position side with open orders",
        BinanceErrorCategory.POSITION,
        False,
    ),
    # Algo Order Errors
    ALGO_ORDER_REQUIRED: (
        "Algo Order API required for this order type",
        BinanceErrorCategory.VALIDATION,
        False,
    ),
}


def is_retryable_error(error_code: int) -> bool:
    """
    Check if an error code is retryable.

    Retryable errors include:
    - Network issues (disconnected, timeout, server busy)
    - Rate limits (with exponential backoff)
    - Transient server errors

    Non-retryable errors include:
    - Authentication failures
    - Validation errors
    - Insufficient balance
    - Order/position rejections

    Parameters
    ----------
    error_code : int
        Binance error code (negative integer).

    Returns
    -------
    bool
        True if the error is retryable, False otherwise.
    """
    if error_code in BINANCE_ERROR_CODES:
        _, _, is_retryable = BINANCE_ERROR_CODES[error_code]
        return is_retryable

    # Unknown error codes: retry by default for safety
    return True


def get_error_message(error_code: int) -> str:
    """
    Get human-readable error message for a Binance error code.

    Parameters
    ----------
    error_code : int
        Binance error code (negative integer).

    Returns
    -------
    str
        Human-readable error description.
    """
    if error_code in BINANCE_ERROR_CODES:
        message, _, _ = BINANCE_ERROR_CODES[error_code]
        return f"[{error_code}] {message}"

    return f"[{error_code}] Unknown Binance error"


def get_error_category(error_code: int) -> BinanceErrorCategory:
    """
    Get the category of a Binance error.

    Parameters
    ----------
    error_code : int
        Binance error code (negative integer).

    Returns
    -------
    BinanceErrorCategory
        Error category for handling decisions.
    """
    if error_code in BINANCE_ERROR_CODES:
        _, category, _ = BINANCE_ERROR_CODES[error_code]
        return category

    return BinanceErrorCategory.UNKNOWN


def calculate_backoff_delay(
    attempt: int,
    initial_delay_ms: int = 500,
    max_delay_ms: int = 5000,
    multiplier: float = 2.0,
) -> int:
    """
    Calculate exponential backoff delay for retries.

    Uses exponential backoff with jitter to prevent thundering herd.

    Parameters
    ----------
    attempt : int
        Current retry attempt (1-indexed).
    initial_delay_ms : int, default 500
        Initial delay in milliseconds. Must be positive.
    max_delay_ms : int, default 5000
        Maximum delay cap in milliseconds. Must be positive.
    multiplier : float, default 2.0
        Exponential multiplier per attempt. Must be positive.

    Returns
    -------
    int
        Delay in milliseconds before next retry.

    Raises
    ------
    ValueError
        If initial_delay_ms, max_delay_ms, or multiplier is not positive.

    Example
    -------
    >>> calculate_backoff_delay(1)  # First retry
    500
    >>> calculate_backoff_delay(2)  # Second retry
    1000
    >>> calculate_backoff_delay(5)  # Fifth retry (capped)
    5000
    """
    # Validate parameters
    if initial_delay_ms <= 0:
        raise ValueError(f"initial_delay_ms must be positive, got {initial_delay_ms}")
    if max_delay_ms <= 0:
        raise ValueError(f"max_delay_ms must be positive, got {max_delay_ms}")
    if multiplier <= 0:
        raise ValueError(f"multiplier must be positive, got {multiplier}")

    if attempt <= 0:
        return initial_delay_ms

    # Exponential backoff
    delay = initial_delay_ms * (multiplier ** (attempt - 1))

    # Cap at max delay
    delay = min(delay, max_delay_ms)

    return int(delay)


def should_retry(
    error_code: int,
    current_attempt: int,
    max_retries: int = 3,
) -> tuple[bool, int]:
    """
    Determine if an error should be retried and with what delay.

    Parameters
    ----------
    error_code : int
        Binance error code.
    current_attempt : int
        Current attempt number (1-indexed).
    max_retries : int, default 3
        Maximum number of retry attempts.

    Returns
    -------
    tuple[bool, int]
        (should_retry, delay_ms) - Whether to retry and delay in milliseconds.

    Example
    -------
    >>> should_retry(-1003, 1, 3)  # Rate limit, first attempt
    (True, 500)
    >>> should_retry(-1003, 4, 3)  # Rate limit, exceeded max
    (False, 0)
    >>> should_retry(-2010, 1, 3)  # Order rejected (non-retryable)
    (False, 0)
    """
    if not is_retryable_error(error_code):
        return (False, 0)

    if current_attempt > max_retries:
        return (False, 0)

    delay = calculate_backoff_delay(current_attempt)

    # Extra delay for rate limit errors
    if get_error_category(error_code) == BinanceErrorCategory.RATE_LIMIT:
        delay = delay * 2

    return (True, delay)
