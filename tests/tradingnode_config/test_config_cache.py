"""
Unit tests for CacheConfig builder (T017).

TDD: RED phase - tests written before implementation.
"""

from __future__ import annotations


from config.cache import build_cache_config
from config.models import RedisConfig


class TestBuildCacheConfig:
    """Tests for build_cache_config function."""

    def test_returns_cache_config(self):
        """build_cache_config should return a CacheConfig instance."""
        redis_config = RedisConfig()
        cache_config = build_cache_config(redis_config)

        # Should return proper CacheConfig
        assert cache_config is not None

    def test_uses_redis_host(self):
        """CacheConfig should use provided Redis host."""
        redis_config = RedisConfig(host="redis.example.com")
        cache_config = build_cache_config(redis_config)

        assert cache_config.database.host == "redis.example.com"

    def test_uses_redis_port(self):
        """CacheConfig should use provided Redis port."""
        redis_config = RedisConfig(port=6380)
        cache_config = build_cache_config(redis_config)

        assert cache_config.database.port == 6380

    def test_uses_redis_password(self):
        """CacheConfig should use provided Redis password."""
        redis_config = RedisConfig(password="secret123")
        cache_config = build_cache_config(redis_config)

        assert cache_config.database.password == "secret123"

    def test_uses_redis_timeout(self):
        """CacheConfig should use provided Redis timeout."""
        redis_config = RedisConfig(timeout=5.0)
        cache_config = build_cache_config(redis_config)

        assert cache_config.database.timeout == 5.0

    def test_uses_msgpack_encoding(self):
        """CacheConfig should use msgpack encoding for performance."""
        redis_config = RedisConfig()
        cache_config = build_cache_config(redis_config)

        assert cache_config.encoding == "msgpack"

    def test_timestamps_as_iso8601(self):
        """CacheConfig should use ISO8601 timestamps for readability."""
        redis_config = RedisConfig()
        cache_config = build_cache_config(redis_config)

        assert cache_config.timestamps_as_iso8601 is True

    def test_flush_on_start_false(self):
        """CacheConfig should NOT flush on start for crash recovery."""
        redis_config = RedisConfig()
        cache_config = build_cache_config(redis_config)

        assert cache_config.flush_on_start is False

    def test_buffer_interval_ms(self):
        """CacheConfig should have 100ms buffer interval."""
        redis_config = RedisConfig()
        cache_config = build_cache_config(redis_config)

        assert cache_config.buffer_interval_ms == 100

    def test_tick_capacity(self):
        """CacheConfig should have appropriate tick capacity."""
        redis_config = RedisConfig()
        cache_config = build_cache_config(redis_config)

        assert cache_config.tick_capacity == 10000

    def test_bar_capacity(self):
        """CacheConfig should have appropriate bar capacity."""
        redis_config = RedisConfig()
        cache_config = build_cache_config(redis_config)

        assert cache_config.bar_capacity == 10000

    def test_custom_capacities(self):
        """build_cache_config should allow custom capacities."""
        redis_config = RedisConfig()
        cache_config = build_cache_config(
            redis_config,
            tick_capacity=50000,
            bar_capacity=20000,
        )

        assert cache_config.tick_capacity == 50000
        assert cache_config.bar_capacity == 20000
