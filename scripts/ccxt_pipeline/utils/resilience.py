"""Resilience utilities for CCXT data pipeline.

Production-grade retry and reconnection logic following CCXT best practices.
Reference: https://github.com/ccxt/ccxt/wiki/Manual#error-handling

Key patterns:
- Catch CCXT-specific exceptions (NetworkError, ExchangeError)
- Exponential backoff with jitter
- Force reconnection on connection errors
- Data validation before storage
"""

import asyncio
import random
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, TypeVar

import ccxt.async_support as ccxt

from scripts.ccxt_pipeline.utils.logging import get_logger

logger = get_logger("resilience")

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior.

    Follows CCXT community recommendations.

    Attributes:
        max_retries: Maximum retry attempts (default: 3).
        base_delay: Initial delay in seconds (default: 1.0).
        max_delay: Maximum delay cap in seconds (default: 30.0).
        exponential_base: Multiplier for exponential backoff (default: 2.0).
        jitter: Add randomness to prevent thundering herd (default: True).
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay with exponential backoff and optional jitter.

    Args:
        attempt: Zero-based attempt number.
        config: Retry configuration.

    Returns:
        Delay in seconds.
    """
    delay = config.base_delay * (config.exponential_base**attempt)
    delay = min(delay, config.max_delay)

    if config.jitter:
        # Add ±25% jitter to prevent thundering herd
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)

    return max(0.1, delay)  # Minimum 100ms


def is_retryable_error(error: Exception) -> bool:
    """Check if error is retryable (transient).

    CCXT Exception Hierarchy:
    - NetworkError: Connection issues, timeouts (RETRYABLE)
    - ExchangeNotAvailable: Exchange down (RETRYABLE with longer delay)
    - RateLimitExceeded: Too many requests (RETRYABLE with delay)
    - ExchangeError: API errors (usually NOT retryable)
    - AuthenticationError: Bad credentials (NOT retryable)

    Args:
        error: The exception to check.

    Returns:
        True if error is transient and worth retrying.
    """
    retryable_types = (
        ccxt.NetworkError,
        ccxt.ExchangeNotAvailable,
        ccxt.RequestTimeout,
        ccxt.RateLimitExceeded,
        ccxt.DDoSProtection,
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
    )
    return isinstance(error, retryable_types)


def needs_reconnection(error: Exception) -> bool:
    """Check if error requires full reconnection.

    Args:
        error: The exception to check.

    Returns:
        True if we should reconnect before retry.
    """
    # Connection-level errors need reconnection
    reconnect_types = (
        ccxt.NetworkError,
        ccxt.ExchangeNotAvailable,
        ConnectionError,
        ConnectionResetError,
    )

    # Also check error message for connection hints
    error_msg = str(error).lower()
    connection_keywords = ["not connected", "connection", "socket", "closed"]

    return isinstance(error, reconnect_types) or any(kw in error_msg for kw in connection_keywords)


async def retry_with_backoff(
    func: Callable[..., T],
    *args: Any,
    config: RetryConfig | None = None,
    reconnect_func: Callable[[], Any] | None = None,
    operation_name: str = "operation",
    **kwargs: Any,
) -> T:
    """Execute async function with retry and exponential backoff.

    Production-grade retry logic following CCXT best practices.

    Args:
        func: Async function to call.
        *args: Positional arguments for func.
        config: Retry configuration.
        reconnect_func: Optional async function to reconnect on connection errors.
        operation_name: Name for logging.
        **kwargs: Keyword arguments for func.

    Returns:
        Result from func.

    Raises:
        Exception: Last exception if all retries exhausted.
    """
    config = config or RetryConfig()
    last_error: Exception | None = None

    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)

        except Exception as e:
            last_error = e

            # Check if error is retryable
            if not is_retryable_error(e):
                logger.error(f"{operation_name}: Non-retryable error: {e}")
                raise

            # Check if we have retries left
            if attempt >= config.max_retries:
                logger.error(
                    f"{operation_name}: Max retries ({config.max_retries}) exceeded. "
                    f"Last error: {e}"
                )
                raise

            # Calculate delay
            delay = calculate_delay(attempt, config)

            # Extra delay for rate limits
            if isinstance(e, (ccxt.RateLimitExceeded, ccxt.DDoSProtection)):
                delay = max(delay, 5.0)  # Minimum 5s for rate limits
                logger.warning(f"{operation_name}: Rate limited, waiting {delay:.1f}s")

            logger.warning(
                f"{operation_name}: Attempt {attempt + 1}/{config.max_retries + 1} "
                f"failed: {e}. Retrying in {delay:.1f}s"
            )

            # Reconnect if needed
            if needs_reconnection(e) and reconnect_func:
                logger.info(f"{operation_name}: Forcing reconnection...")
                try:
                    if asyncio.iscoroutinefunction(reconnect_func):
                        await reconnect_func()
                    else:
                        reconnect_func()
                except Exception as reconnect_error:
                    logger.warning(f"Reconnection failed: {reconnect_error}")

            await asyncio.sleep(delay)

    # Should not reach here, but just in case
    if last_error:
        raise last_error
    raise RuntimeError(f"{operation_name}: Retry loop exited unexpectedly")


def with_retry(
    config: RetryConfig | None = None,
    operation_name: str | None = None,
):
    """Decorator for adding retry logic to async functions.

    Usage:
        @with_retry(config=RetryConfig(max_retries=5))
        async def fetch_data():
            return await exchange.fetch_open_interest(symbol)

    Args:
        config: Retry configuration.
        operation_name: Name for logging (defaults to function name).

    Returns:
        Decorated function with retry logic.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            name = operation_name or func.__name__
            return await retry_with_backoff(
                func, *args, config=config, operation_name=name, **kwargs
            )

        return wrapper

    return decorator


# Data validation utilities


def validate_open_interest(oi_value: float, symbol: str) -> bool:
    """Validate open interest value is sane.

    Args:
        oi_value: Open interest amount.
        symbol: Symbol for context.

    Returns:
        True if valid.
    """
    if oi_value is None or oi_value < 0:
        logger.warning(f"Invalid OI for {symbol}: {oi_value} (negative or None)")
        return False

    # BTC OI sanity check: typically 50K-500K BTC on Binance
    if "BTC" in symbol and (oi_value < 1000 or oi_value > 10_000_000):
        logger.warning(f"Suspicious OI for {symbol}: {oi_value}")
        # Don't reject, just warn - could be valid during extreme events

    return True


def validate_funding_rate(rate: float, symbol: str) -> bool:
    """Validate funding rate is sane.

    Args:
        rate: Funding rate value.
        symbol: Symbol for context.

    Returns:
        True if valid.
    """
    if rate is None:
        logger.warning(f"Null funding rate for {symbol}")
        return False

    # Funding rates typically -0.1% to +0.1% (extreme: ±1%)
    if abs(rate) > 0.01:  # 1%
        logger.warning(f"Extreme funding rate for {symbol}: {rate:.6f}")
        # Don't reject - can happen during high volatility

    return True


def validate_liquidation(quantity: float, price: float, symbol: str) -> bool:
    """Validate liquidation data is sane.

    Args:
        quantity: Liquidation quantity.
        price: Liquidation price.
        symbol: Symbol for context.

    Returns:
        True if valid.
    """
    if quantity is None or quantity <= 0:
        logger.warning(f"Invalid liquidation quantity for {symbol}: {quantity}")
        return False

    if price is None or price <= 0:
        logger.warning(f"Invalid liquidation price for {symbol}: {price}")
        return False

    return True
