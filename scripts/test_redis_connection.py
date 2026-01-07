#!/usr/bin/env python3
"""
Redis Connection Test Script (Spec 018 - T007)

Tests Redis connectivity and reports status.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.cache.redis_config import (
    check_redis_health,
    wait_for_redis,
    RedisConnectionError,
)


def main():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))

    print(f"Testing Redis connection to {host}:{port}...")

    # Quick health check
    if check_redis_health(host, port):
        print("✓ Redis is reachable")
    else:
        print("✗ Redis is not reachable")
        print("\nAttempting with retry logic...")
        try:
            wait_for_redis(host, port, max_retries=3)
            print("✓ Redis became available")
        except RedisConnectionError as e:
            print(f"✗ {e}")
            sys.exit(1)

    # Test with redis-cli if available
    import subprocess

    try:
        result = subprocess.run(
            ["redis-cli", "-h", host, "-p", str(port), "ping"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and "PONG" in result.stdout:
            print("✓ redis-cli ping: PONG")
        else:
            print(f"⚠ redis-cli returned: {result.stdout.strip()}")
    except FileNotFoundError:
        print("⚠ redis-cli not installed (optional)")
    except subprocess.TimeoutExpired:
        print("⚠ redis-cli timed out")

    print("\n✓ Redis connection test passed")


if __name__ == "__main__":
    main()
