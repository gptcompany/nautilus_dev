"""
CacheConfig builder (T019).

Builds NautilusTrader CacheConfig with Redis backend.
"""

from __future__ import annotations

from nautilus_trader.config import CacheConfig, DatabaseConfig

from config.models import RedisConfig


def build_cache_config(
    redis_config: RedisConfig,
    *,
    tick_capacity: int = 10000,
    bar_capacity: int = 10000,
) -> CacheConfig:
    """
    Build CacheConfig with Redis backend.

    Parameters
    ----------
    redis_config : RedisConfig
        Redis connection configuration.
    tick_capacity : int, optional
        Tick data capacity (default: 10000).
    bar_capacity : int, optional
        Bar data capacity (default: 10000).

    Returns
    -------
    CacheConfig
        NautilusTrader cache configuration with Redis database.

    Notes
    -----
    - Uses msgpack encoding for 2-3x faster serialization than JSON
    - flush_on_start=False preserves cache for crash recovery
    - 100ms buffer interval balances latency vs I/O
    """
    return CacheConfig(
        database=DatabaseConfig(
            host=redis_config.host,
            port=redis_config.port,
            password=redis_config.password,
            timeout=redis_config.timeout,
        ),
        encoding="msgpack",
        timestamps_as_iso8601=True,
        buffer_interval_ms=100,
        flush_on_start=False,
        tick_capacity=tick_capacity,
        bar_capacity=bar_capacity,
    )
