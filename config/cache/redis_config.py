"""
Redis Cache Configuration Factory (Spec 018)

Production-ready CacheConfig for NautilusTrader TradingNode with:
- Environment variable loading
- Config validation
- Retry logic with exponential backoff
- Health check utilities
"""

from __future__ import annotations

import os
import socket
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nautilus_trader.config import CacheConfig


class RedisConfigError(Exception):
    """Raised when Redis configuration is invalid."""

    pass


class RedisConnectionError(Exception):
    """Raised when Redis connection fails after retries."""

    pass


def _safe_int(value: str, name: str, default: int) -> int:
    """Safely parse int from env var with clear error message."""
    try:
        return int(value)
    except ValueError:
        raise RedisConfigError(f"{name} must be an integer, got: {value!r}")


def validate_redis_config(
    host: str,
    port: int,
    encoding: str,
) -> None:
    """
    Validate Redis configuration parameters.

    Args:
        host: Redis host (hostname or IP)
        port: Redis port (1-65535)
        encoding: Serialization format (msgpack or json)

    Raises:
        RedisConfigError: If any parameter is invalid
    """
    # Validate host format (reject whitespace-only)
    if not host or not isinstance(host, str) or not host.strip():
        raise RedisConfigError("REDIS_HOST must be a non-empty string")

    # Validate port range
    if not isinstance(port, int) or port < 1 or port > 65535:
        raise RedisConfigError(f"REDIS_PORT must be 1-65535, got: {port}")

    # Validate encoding
    valid_encodings = ("msgpack", "json")
    if encoding not in valid_encodings:
        raise RedisConfigError(f"encoding must be one of {valid_encodings}, got: {encoding}")


def create_redis_cache_config(
    host: str | None = None,
    port: int | None = None,
    password: str | None = None,
    ssl: bool | None = None,
    timeout: int | None = None,
) -> "CacheConfig":
    """
    Create production Redis cache configuration.

    Loads from environment variables with fallback to defaults:
    - REDIS_HOST (default: localhost)
    - REDIS_PORT (default: 6379)
    - REDIS_PASSWORD (default: None)
    - REDIS_SSL (default: false)
    - REDIS_TIMEOUT (default: 2)

    Args:
        host: Override REDIS_HOST
        port: Override REDIS_PORT
        password: Override REDIS_PASSWORD
        ssl: Override REDIS_SSL
        timeout: Override REDIS_TIMEOUT

    Returns:
        CacheConfig configured for Redis with msgpack encoding

    Raises:
        RedisConfigError: If configuration is invalid
    """
    from nautilus_trader.common.config import DatabaseConfig
    from nautilus_trader.config import CacheConfig

    # Load from environment with overrides (explicit None check for port=0 case)
    _host = host if host is not None else os.getenv("REDIS_HOST", "localhost")
    _port = (
        port if port is not None else _safe_int(os.getenv("REDIS_PORT", "6379"), "REDIS_PORT", 6379)
    )
    _password = password if password is not None else (os.getenv("REDIS_PASSWORD") or None)
    _ssl = ssl if ssl is not None else os.getenv("REDIS_SSL", "false").lower() == "true"
    _timeout = (
        timeout
        if timeout is not None
        else _safe_int(os.getenv("REDIS_TIMEOUT", "2"), "REDIS_TIMEOUT", 2)
    )

    # Validate configuration
    validate_redis_config(_host, _port, "msgpack")

    return CacheConfig(
        database=DatabaseConfig(
            type="redis",
            host=_host,
            port=_port,
            password=_password,
            ssl=_ssl,
            timeout=_timeout,
        ),
        encoding="msgpack",
        timestamps_as_iso8601=False,
        persist_account_events=True,  # CRITICAL for recovery
        buffer_interval_ms=100,  # Batch writes
        use_trader_prefix=True,  # Namespace by trader
        use_instance_id=False,
        flush_on_start=False,  # Preserve state on restart
        tick_capacity=10_000,
        bar_capacity=10_000,
    )


def create_debug_cache_config(
    host: str | None = None,
    port: int | None = None,
) -> "CacheConfig":
    """
    Create debug Redis cache configuration with JSON encoding.

    JSON encoding is human-readable for debugging but slower than msgpack.

    Args:
        host: Override REDIS_HOST
        port: Override REDIS_PORT

    Returns:
        CacheConfig configured for Redis with JSON encoding
    """
    from nautilus_trader.common.config import DatabaseConfig
    from nautilus_trader.config import CacheConfig

    _host = host if host is not None else os.getenv("REDIS_HOST", "localhost")
    _port = (
        port if port is not None else _safe_int(os.getenv("REDIS_PORT", "6379"), "REDIS_PORT", 6379)
    )

    validate_redis_config(_host, _port, "json")

    return CacheConfig(
        database=DatabaseConfig(
            type="redis",
            host=_host,
            port=_port,
        ),
        encoding="json",  # Human-readable for debugging
        timestamps_as_iso8601=True,  # Readable timestamps
        persist_account_events=True,
        buffer_interval_ms=100,
        use_trader_prefix=True,
        flush_on_start=False,
    )


def check_redis_health(
    host: str | None = None,
    port: int | None = None,
    timeout: float = 2.0,
) -> bool:
    """
    Check if Redis is reachable.

    Args:
        host: Redis host (default: from env)
        port: Redis port (default: from env)
        timeout: Connection timeout in seconds (must be positive)

    Returns:
        True if Redis is reachable, False otherwise
    """
    _host = host if host is not None else os.getenv("REDIS_HOST", "localhost")
    _port = port if port is not None else int(os.getenv("REDIS_PORT", "6379"))
    _timeout = max(0.1, timeout)  # Ensure positive timeout

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(_timeout)
        result = sock.connect_ex((_host, _port))
        return result == 0
    except (OSError, socket.error):
        return False
    finally:
        sock.close()


def build_cache_config(
    redis_config: object,
    tick_capacity: int = 10_000,
    bar_capacity: int = 10_000,
) -> "CacheConfig":
    """
    Build CacheConfig from a RedisConfig object (T017).

    Wrapper around create_redis_cache_config for object-based API.

    Args:
        redis_config: RedisConfig instance with host, port, password, timeout
        tick_capacity: Max tick capacity in cache (default: 10,000)
        bar_capacity: Max bar capacity in cache (default: 10,000)

    Returns:
        CacheConfig configured for Redis with msgpack encoding
    """
    from nautilus_trader.common.config import DatabaseConfig
    from nautilus_trader.config import CacheConfig

    host = getattr(redis_config, "host", "localhost")
    port = getattr(redis_config, "port", 6379)
    password = getattr(redis_config, "password", None)
    timeout = getattr(redis_config, "timeout", 2)

    validate_redis_config(host, port, "msgpack")

    return CacheConfig(
        database=DatabaseConfig(
            type="redis",
            host=host,
            port=port,
            password=password,
            timeout=timeout,
        ),
        encoding="msgpack",
        timestamps_as_iso8601=True,  # Readable timestamps for debugging
        buffer_interval_ms=100,
        flush_on_start=False,  # Preserve state on restart
        tick_capacity=tick_capacity,
        bar_capacity=bar_capacity,
    )


def wait_for_redis(
    host: str | None = None,
    port: int | None = None,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 32.0,
) -> None:
    """
    Wait for Redis to become available with exponential backoff.

    Args:
        host: Redis host
        port: Redis port
        max_retries: Maximum retry attempts (default: 5)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 32.0)

    Raises:
        RedisConnectionError: If Redis is not available after max_retries
    """
    _host = host if host is not None else os.getenv("REDIS_HOST", "localhost")
    _port = port if port is not None else int(os.getenv("REDIS_PORT", "6379"))
    _max_retries = max(1, max_retries)  # At least 1 attempt
    _base_delay = max(0.1, base_delay)  # Minimum 0.1s delay

    delay = _base_delay
    for attempt in range(1, _max_retries + 1):
        if check_redis_health(_host, _port):
            return

        if attempt < _max_retries:
            print(f"Redis not available, retry {attempt}/{max_retries} in {delay:.1f}s")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)

    raise RedisConnectionError(
        f"Redis at {_host}:{_port} not available after {max_retries} retries"
    )
