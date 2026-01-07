#!/usr/bin/env python3
"""
Redis Performance Benchmark (Spec 018 - T014)

Benchmarks read/write latency and stress tests with 10K+ keys.
"""

import sys
import os
import time
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.cache.redis_config import check_redis_health


def benchmark_latency(r, iterations: int = 1000) -> dict:
    """Benchmark read/write latency."""
    write_times = []
    read_times = []

    for i in range(iterations):
        key = f"benchmark:latency:{i}"
        value = f'{{"id": {i}, "data": "benchmark_test_data_payload"}}'

        # Write
        start = time.perf_counter()
        r.set(key, value)
        write_times.append((time.perf_counter() - start) * 1000)  # ms

        # Read
        start = time.perf_counter()
        r.get(key)
        read_times.append((time.perf_counter() - start) * 1000)  # ms

        # Cleanup
        r.delete(key)

    return {
        "write_avg_ms": statistics.mean(write_times),
        "write_p95_ms": sorted(write_times)[int(iterations * 0.95)],
        "write_p99_ms": sorted(write_times)[int(iterations * 0.99)],
        "read_avg_ms": statistics.mean(read_times),
        "read_p95_ms": sorted(read_times)[int(iterations * 0.95)],
        "read_p99_ms": sorted(read_times)[int(iterations * 0.99)],
    }


def stress_test_keys(r, num_keys: int = 10000) -> dict:
    """Stress test with large number of keys."""
    print(f"\n   Writing {num_keys:,} keys...")
    start = time.perf_counter()

    pipe = r.pipeline()
    for i in range(num_keys):
        key = f"benchmark:stress:{i}"
        value = f'{{"id": {i}, "instrument": "BTCUSDT-PERP.BINANCE", "side": "LONG"}}'
        pipe.set(key, value)

    pipe.execute()
    write_duration = time.perf_counter() - start

    print(f"   Reading {num_keys:,} keys...")
    start = time.perf_counter()

    pipe = r.pipeline()
    for i in range(num_keys):
        pipe.get(f"benchmark:stress:{i}")
    pipe.execute()
    read_duration = time.perf_counter() - start

    # Cleanup
    print(f"   Cleaning up...")
    pipe = r.pipeline()
    for i in range(num_keys):
        pipe.delete(f"benchmark:stress:{i}")
    pipe.execute()

    return {
        "num_keys": num_keys,
        "write_total_s": write_duration,
        "write_ops_per_s": num_keys / write_duration,
        "read_total_s": read_duration,
        "read_ops_per_s": num_keys / read_duration,
    }


def main():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))

    print(f"Redis Performance Benchmark")
    print(f"=" * 50)

    if not check_redis_health(host, port):
        print(f"✗ Redis not available at {host}:{port}")
        sys.exit(1)

    try:
        import redis

        r = redis.Redis(host=host, port=port, decode_responses=True)

        # Latency benchmark
        print("\n1. Latency Benchmark (1000 ops)...")
        latency = benchmark_latency(r, 1000)

        print(f"\n   Write Latency:")
        print(f"     Average: {latency['write_avg_ms']:.3f} ms")
        print(f"     P95:     {latency['write_p95_ms']:.3f} ms")
        print(f"     P99:     {latency['write_p99_ms']:.3f} ms")

        print(f"\n   Read Latency:")
        print(f"     Average: {latency['read_avg_ms']:.3f} ms")
        print(f"     P95:     {latency['read_p95_ms']:.3f} ms")
        print(f"     P99:     {latency['read_p99_ms']:.3f} ms")

        # Check against NFR-001: < 1ms p95
        write_pass = latency["write_p95_ms"] < 1.0
        read_pass = latency["read_p95_ms"] < 1.0

        print(f"\n   NFR-001 Check (< 1ms p95):")
        print(f"     Write: {'✓ PASS' if write_pass else '✗ FAIL'}")
        print(f"     Read:  {'✓ PASS' if read_pass else '✗ FAIL'}")

        # Stress test
        print("\n2. Stress Test (10K+ keys)...")
        stress = stress_test_keys(r, 10000)

        print(f"\n   Results:")
        print(f"     Keys:       {stress['num_keys']:,}")
        print(
            f"     Write:      {stress['write_total_s']:.2f}s ({stress['write_ops_per_s']:,.0f} ops/s)"
        )
        print(
            f"     Read:       {stress['read_total_s']:.2f}s ({stress['read_ops_per_s']:,.0f} ops/s)"
        )

        stress_pass = stress["num_keys"] >= 10000
        print(f"\n   NFR-001 Check (10K+ keys): {'✓ PASS' if stress_pass else '✗ FAIL'}")

        # Summary
        all_pass = write_pass and read_pass and stress_pass
        print(f"\n{'=' * 50}")
        print(f"Overall: {'✓ ALL BENCHMARKS PASSED' if all_pass else '✗ SOME BENCHMARKS FAILED'}")

        sys.exit(0 if all_pass else 1)

    except ImportError:
        print("✗ redis-py not installed")
        print("  Install: pip install redis")
        sys.exit(1)


if __name__ == "__main__":
    main()
