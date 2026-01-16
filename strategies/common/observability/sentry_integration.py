"""
Sentry Integration for NautilusTrader
Error tracking and performance monitoring for production trading.

Usage:
    from strategies.common.observability.sentry_integration import init_sentry
    init_sentry()  # Call once at startup
"""

import logging
import os
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import - only load sentry if configured
_sentry_sdk = None
_initialized = False


def init_sentry(
    dsn: str | None = None,
    environment: str = "production",
    release: str | None = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
) -> bool:
    """
    Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN (or use SENTRY_DSN env var)
        environment: Environment name (production, staging, development)
        release: Release version (defaults to git commit)
        traces_sample_rate: Performance monitoring sample rate (0.0-1.0)
        profiles_sample_rate: Profiling sample rate (0.0-1.0)

    Returns:
        True if initialized successfully, False otherwise
    """
    global _sentry_sdk, _initialized

    if _initialized:
        return True

    dsn = dsn or os.environ.get("SENTRY_DSN")
    if not dsn:
        logger.info("Sentry DSN not configured - error tracking disabled")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Get release from git if not specified
        if release is None:
            try:
                import subprocess

                release = (
                    subprocess.check_output(
                        ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
                    )
                    .decode()
                    .strip()
                )
            except Exception:
                release = "unknown"

        # Configure logging integration
        logging_integration = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            integrations=[logging_integration],
            # Don't send PII
            send_default_pii=False,
            # Filter out sensitive data
            before_send=_filter_sensitive_data,  # type: ignore[arg-type]
        )

        _sentry_sdk = sentry_sdk
        _initialized = True

        logger.info(f"Sentry initialized: env={environment}, release={release}")
        return True

    except ImportError:
        logger.warning("sentry-sdk not installed - run: pip install sentry-sdk")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def _filter_sensitive_data(event: dict, hint: dict) -> dict | None:
    """Filter sensitive data before sending to Sentry."""
    # Remove API keys and secrets from breadcrumbs
    if "breadcrumbs" in event:
        for breadcrumb in event.get("breadcrumbs", {}).get("values", []):
            if "data" in breadcrumb:
                for key in list(breadcrumb["data"].keys()):
                    key_lower = key.lower()
                    if any(s in key_lower for s in ["key", "secret", "password", "token"]):
                        breadcrumb["data"][key] = "[FILTERED]"

    # Remove sensitive environment variables
    if "contexts" in event and "runtime" in event["contexts"]:
        runtime = event["contexts"]["runtime"]
        if "environment" in runtime:
            for key in list(runtime["environment"].keys()):
                key_lower = key.lower()
                if any(s in key_lower for s in ["key", "secret", "password", "token"]):
                    runtime["environment"][key] = "[FILTERED]"

    return event


def capture_exception(error: Exception, **context) -> str | None:
    """
    Capture an exception to Sentry.

    Args:
        error: The exception to capture
        **context: Additional context to attach

    Returns:
        Event ID if captured, None otherwise
    """
    if not _initialized or _sentry_sdk is None:
        return None

    with _sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        return _sentry_sdk.capture_exception(error)  # type: ignore[no-any-return]


def capture_message(message: str, level: str = "info", **context) -> str | None:
    """
    Capture a message to Sentry.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **context: Additional context to attach

    Returns:
        Event ID if captured, None otherwise
    """
    if not _initialized or _sentry_sdk is None:
        return None

    with _sentry_sdk.push_scope() as scope:
        for key, value in context.items():
            scope.set_extra(key, value)
        return _sentry_sdk.capture_message(message, level=level)  # type: ignore[no-any-return, arg-type]


def set_user(user_id: str, **extra) -> None:
    """Set user context for subsequent events."""
    if _initialized and _sentry_sdk is not None:
        _sentry_sdk.set_user({"id": user_id, **extra})


def set_tag(key: str, value: str) -> None:
    """Set a tag for subsequent events."""
    if _initialized and _sentry_sdk is not None:
        _sentry_sdk.set_tag(key, value)


def add_breadcrumb(message: str, category: str = "default", **data) -> None:
    """Add a breadcrumb for debugging."""
    if _initialized and _sentry_sdk is not None:
        _sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            data=data,
        )


def track_performance(name: str) -> Callable:
    """
    Decorator to track function performance.

    Usage:
        @track_performance("process_order")
        def process_order(order):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not _initialized or _sentry_sdk is None:
                return func(*args, **kwargs)

            with _sentry_sdk.start_transaction(op="function", name=name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Trading-specific helpers
def capture_trading_error(
    error: Exception,
    strategy_id: str | None = None,
    symbol: str | None = None,
    order_id: str | None = None,
) -> str | None:
    """Capture a trading-specific error with relevant context."""
    return capture_exception(
        error,
        strategy_id=strategy_id,
        symbol=symbol,
        order_id=order_id,
        error_type="trading_error",
    )


def capture_risk_event(
    event_type: str,
    message: str,
    pnl: float | None = None,
    drawdown: float | None = None,
    position_size: float | None = None,
) -> str | None:
    """Capture a risk management event."""
    return capture_message(
        message,
        level="warning",
        event_type=event_type,
        pnl=pnl,
        drawdown=drawdown,
        position_size=position_size,
    )
