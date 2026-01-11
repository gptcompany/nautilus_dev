"""
Sentry Integration for NautilusTrader Strategies

Usage in strategies:
    from strategies.common.sentry_integration import init_sentry

    init_sentry()  # Call once at startup

Environment variables:
    SENTRY_DSN: Sentry project DSN
    SENTRY_ENVIRONMENT: development/staging/production
    SENTRY_TRACES_SAMPLE_RATE: 0.0-1.0 (default 0.1)
"""

import os
from collections.abc import Callable
from functools import wraps
from typing import Any

# Only import sentry if available
try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None


def init_sentry() -> bool:
    """
    Initialize Sentry SDK from environment variables.

    Returns:
        True if Sentry was initialized, False otherwise.
    """
    if not SENTRY_AVAILABLE:
        return False

    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return False

    environment = os.environ.get("SENTRY_ENVIRONMENT", "development")
    traces_sample_rate = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        send_default_pii=False,  # Don't send PII for trading system
        integrations=[
            LoggingIntegration(
                level=None,  # Capture all levels
                event_level=40,  # Only send ERROR+ as events
            ),
        ],
        # Filter out noisy errors
        before_send=_before_send,
    )

    return True


def _before_send(event: dict, hint: dict) -> dict | None:
    """Filter events before sending to Sentry."""
    # Skip connection errors (too noisy)
    if "exc_info" in hint:
        exc_type, exc_value, _ = hint["exc_info"]
        if exc_type.__name__ in ("ConnectionError", "TimeoutError", "ConnectionRefusedError"):
            return None

    return event


def capture_exception(error: Exception, **context: Any) -> str | None:
    """
    Capture an exception to Sentry with optional context.

    Args:
        error: The exception to capture
        **context: Additional context (strategy_id, instrument, etc.)

    Returns:
        Sentry event ID or None if not available
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.is_initialized():
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        return sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **context: Any) -> str | None:
    """
    Capture a message to Sentry.

    Args:
        message: The message to capture
        level: Log level (debug, info, warning, error, fatal)
        **context: Additional context

    Returns:
        Sentry event ID or None if not available
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.is_initialized():
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        return sentry_sdk.capture_message(message, level=level)


def set_trading_context(
    strategy_id: str | None = None,
    instrument: str | None = None,
    account: str | None = None,
) -> None:
    """
    Set trading-specific context for all subsequent Sentry events.

    Call this at strategy startup to tag all errors with strategy info.
    """
    if not SENTRY_AVAILABLE or not sentry_sdk.is_initialized():
        return

    if strategy_id:
        sentry_sdk.set_tag("strategy_id", strategy_id)
    if instrument:
        sentry_sdk.set_tag("instrument", instrument)
    if account:
        sentry_sdk.set_tag("account", account)


def sentry_span(operation: str) -> Callable:
    """
    Decorator to create a Sentry performance span.

    Usage:
        @sentry_span("calculate_signal")
        def calculate_signal(self, data):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not SENTRY_AVAILABLE or not sentry_sdk.is_initialized():
                return func(*args, **kwargs)

            with sentry_sdk.start_span(op=operation, description=func.__name__):
                return func(*args, **kwargs)

        return wrapper

    return decorator
