#!/usr/bin/env python3
"""
Redis-based Distributed Rate Limiter.

Implements Token Bucket algorithm for rate limiting across distributed systems.
Supports multiple limit types: API, WebSocket, Trading, etc.

Usage:
    from security.rate_limiter import RateLimiter, RateLimitConfig

    # Initialize
    limiter = RateLimiter(redis_url="redis://localhost:6379")

    # Check rate limit
    result = limiter.check("api", client_ip="192.168.1.1")
    if not result.allowed:
        raise HTTPException(429, f"Rate limited. Retry after {result.retry_after}s")

    # Different limit types
    limiter.check("trading", user_id="user123")
    limiter.check("websocket", client_ip="192.168.1.1")
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import redis

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration for a specific limit type."""

    requests: int  # Max requests in window
    window_seconds: int  # Time window
    burst: int = 0  # Additional burst capacity

    @property
    def tokens_per_second(self) -> float:
        """Calculate token refill rate."""
        return self.requests / self.window_seconds


# Default rate limit configurations
DEFAULT_LIMITS = {
    "api": RateLimitConfig(requests=100, window_seconds=60, burst=10),
    "api_strict": RateLimitConfig(requests=20, window_seconds=60, burst=5),
    "websocket": RateLimitConfig(requests=50, window_seconds=10, burst=20),
    "trading": RateLimitConfig(requests=10, window_seconds=1, burst=5),
    "login": RateLimitConfig(requests=5, window_seconds=300, burst=0),
    "withdrawal": RateLimitConfig(requests=3, window_seconds=3600, burst=0),
}


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    remaining: int
    reset_at: float
    retry_after: int = 0
    limit_type: str = ""

    @property
    def headers(self) -> dict[str, str]:
        """Generate rate limit headers for HTTP response."""
        return {
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_at)),
            "X-RateLimit-Limit-Type": self.limit_type,
            **({"Retry-After": str(self.retry_after)} if not self.allowed else {}),
        }


class RateLimiter:
    """
    Redis-based distributed rate limiter using Token Bucket algorithm.

    Features:
    - Distributed across multiple instances via Redis
    - Multiple limit types with different configurations
    - Atomic operations with Lua scripts
    - Graceful degradation if Redis unavailable
    """

    # Lua script for atomic token bucket operation
    TOKEN_BUCKET_SCRIPT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local rate = tonumber(ARGV[2])
    local capacity = tonumber(ARGV[3])
    local requested = tonumber(ARGV[4])
    local ttl = tonumber(ARGV[5])

    local data = redis.call('HMGET', key, 'tokens', 'last_update')
    local tokens = tonumber(data[1]) or capacity
    local last_update = tonumber(data[2]) or now

    -- Refill tokens based on time elapsed
    local elapsed = now - last_update
    tokens = math.min(capacity, tokens + (elapsed * rate))

    local allowed = 0
    local new_tokens = tokens

    if tokens >= requested then
        new_tokens = tokens - requested
        allowed = 1
    end

    redis.call('HMSET', key, 'tokens', new_tokens, 'last_update', now)
    redis.call('EXPIRE', key, ttl)

    return {allowed, math.floor(new_tokens), now + ((capacity - new_tokens) / rate)}
    """

    def __init__(
        self,
        redis_url: str | None = None,
        limits: dict[str, RateLimitConfig] | None = None,
        prefix: str = "ratelimit:",
        fallback_allow: bool = True,
    ):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL. Uses REDIS_URL env var if not provided.
            limits: Custom rate limit configurations.
            prefix: Redis key prefix.
            fallback_allow: If True, allow requests when Redis is unavailable.
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.limits = {**DEFAULT_LIMITS, **(limits or {})}
        self.prefix = prefix
        self.fallback_allow = fallback_allow
        self._client: redis.Redis | None = None
        self._script_sha: str | None = None

    @property
    def client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis

                self._client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                # Load Lua script
                self._script_sha = self._client.script_load(self.TOKEN_BUCKET_SCRIPT)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                raise
        return self._client

    def check(
        self,
        limit_type: str,
        identifier: str | None = None,
        client_ip: str | None = None,
        user_id: str | None = None,
        cost: int = 1,
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limit.

        Args:
            limit_type: Type of limit to check (api, trading, etc.)
            identifier: Custom identifier. If not provided, uses client_ip or user_id.
            client_ip: Client IP address.
            user_id: User ID.
            cost: Number of tokens to consume (default 1).

        Returns:
            RateLimitResult with allowed status and metadata.
        """
        # Get config
        config = self.limits.get(limit_type)
        if not config:
            logger.warning(f"Unknown limit type: {limit_type}, allowing request")
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_at=time.time() + 60,
                limit_type=limit_type,
            )

        # Build identifier
        if not identifier:
            identifier = user_id or client_ip or "anonymous"

        key = f"{self.prefix}{limit_type}:{identifier}"
        capacity = config.requests + config.burst

        try:
            result = self.client.evalsha(
                self._script_sha,
                1,
                key,
                time.time(),
                config.tokens_per_second,
                capacity,
                cost,
                config.window_seconds * 2,  # TTL
            )

            allowed, remaining, reset_at = result
            retry_after = 0 if allowed else int(reset_at - time.time()) + 1

            return RateLimitResult(
                allowed=bool(allowed),
                remaining=int(remaining),
                reset_at=float(reset_at),
                retry_after=retry_after,
                limit_type=limit_type,
            )

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            if self.fallback_allow:
                return RateLimitResult(
                    allowed=True,
                    remaining=0,
                    reset_at=time.time() + 60,
                    limit_type=limit_type,
                )
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=time.time() + 60,
                retry_after=60,
                limit_type=limit_type,
            )

    def reset(self, limit_type: str, identifier: str) -> bool:
        """Reset rate limit for an identifier."""
        try:
            key = f"{self.prefix}{limit_type}:{identifier}"
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False

    def get_status(self, limit_type: str, identifier: str) -> dict:
        """Get current rate limit status without consuming tokens."""
        try:
            key = f"{self.prefix}{limit_type}:{identifier}"
            data = self.client.hgetall(key)
            config = self.limits.get(limit_type)

            if not data or not config:
                return {"tokens": config.requests if config else 0, "limited": False}

            tokens = float(data.get("tokens", config.requests))
            return {
                "tokens": int(tokens),
                "capacity": config.requests + config.burst,
                "limited": tokens < 1,
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {"error": str(e)}


# Convenience function for simple usage
_default_limiter: RateLimiter | None = None


def check_rate_limit(
    limit_type: str,
    identifier: str | None = None,
    client_ip: str | None = None,
    user_id: str | None = None,
) -> RateLimitResult:
    """
    Check rate limit using default limiter.

    Usage:
        result = check_rate_limit("api", client_ip=request.client.host)
        if not result.allowed:
            raise HTTPException(429, headers=result.headers)
    """
    global _default_limiter
    if _default_limiter is None:
        _default_limiter = RateLimiter()

    return _default_limiter.check(
        limit_type=limit_type,
        identifier=identifier,
        client_ip=client_ip,
        user_id=user_id,
    )
