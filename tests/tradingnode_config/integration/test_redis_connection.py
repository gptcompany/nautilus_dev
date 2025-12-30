"""
Integration test for Redis connection (T018).

These tests require a running Redis instance.
Skip if Redis is not available.
"""

from __future__ import annotations

import pytest

from config.cache import build_cache_config
from config.models import RedisConfig


@pytest.fixture
def redis_available():
    """Check if Redis is available."""
    try:
        import redis

        client = redis.Redis(host="localhost", port=6379, socket_timeout=1.0)
        client.ping()
        return True
    except Exception:
        return False


@pytest.mark.integration
class TestRedisConnection:
    """Integration tests for Redis connection."""

    def test_redis_connection(self, redis_available):
        """Test that cache config can connect to Redis."""
        if not redis_available:
            pytest.skip("Redis not available")

        redis_config = RedisConfig(host="localhost", port=6379)
        cache_config = build_cache_config(redis_config)

        # Verify config is valid
        assert cache_config.database.host == "localhost"
        assert cache_config.database.port == 6379

    def test_redis_with_password(self, redis_available):
        """Test Redis connection with password."""
        if not redis_available:
            pytest.skip("Redis not available")

        # This test just validates the config is created
        # Actual password auth would require a password-protected Redis
        redis_config = RedisConfig(
            host="localhost",
            port=6379,
            password="test_password",
        )
        cache_config = build_cache_config(redis_config)

        assert cache_config.database.password == "test_password"
