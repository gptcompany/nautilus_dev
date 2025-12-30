"""Performance profiling for concurrent exchange fetching.

T072: Benchmark script to measure concurrent fetching performance.
"""

import asyncio
import time
from statistics import mean, stdev

from scripts.ccxt_pipeline.fetchers import FetchOrchestrator, get_all_fetchers
from scripts.ccxt_pipeline.utils.logging import setup_logging


async def benchmark_concurrent_fetch(
    symbol: str = "BTCUSDT-PERP",
    iterations: int = 5,
) -> dict:
    """Benchmark concurrent OI fetching from all exchanges.

    Args:
        symbol: Symbol to fetch.
        iterations: Number of iterations to run.

    Returns:
        Dictionary with benchmark results.
    """
    setup_logging("INFO")
    print(f"\n{'=' * 60}")
    print("CCXT Pipeline Concurrent Fetch Benchmark")
    print(f"{'=' * 60}")
    print(f"Symbol: {symbol}")
    print(f"Iterations: {iterations}")
    print(f"{'=' * 60}\n")

    fetchers = get_all_fetchers()
    orchestrator = FetchOrchestrator(fetchers)

    try:
        # Warm-up connection
        print("Warming up connections...")
        await orchestrator.connect_all()

        # Benchmark iterations
        timings: list[float] = []
        success_count = 0
        error_count = 0

        for i in range(iterations):
            start = time.perf_counter()
            results = await orchestrator.fetch_open_interest(symbol)
            elapsed = time.perf_counter() - start
            timings.append(elapsed)

            successes = sum(1 for r in results if r.success)
            errors = len(results) - successes
            success_count += successes
            error_count += errors

            print(f"  Iteration {i + 1}: {elapsed:.3f}s ({successes}/{len(results)} success)")

        print(f"\n{'=' * 60}")
        print("RESULTS")
        print(f"{'=' * 60}")
        print(f"Total iterations: {iterations}")
        print(f"Mean time: {mean(timings):.3f}s")
        if len(timings) > 1:
            print(f"Std dev: {stdev(timings):.3f}s")
        print(f"Min time: {min(timings):.3f}s")
        print(f"Max time: {max(timings):.3f}s")
        print(
            f"Success rate: {success_count}/{success_count + error_count} ({100 * success_count / (success_count + error_count):.1f}%)"
        )
        print(f"{'=' * 60}\n")

        return {
            "iterations": iterations,
            "mean_time_s": mean(timings),
            "std_dev_s": stdev(timings) if len(timings) > 1 else 0,
            "min_time_s": min(timings),
            "max_time_s": max(timings),
            "success_rate": success_count / (success_count + error_count),
            "total_successes": success_count,
            "total_errors": error_count,
        }

    finally:
        await orchestrator.close_all()


async def benchmark_sequential_vs_concurrent(symbol: str = "BTCUSDT-PERP") -> dict:
    """Compare sequential vs concurrent fetching.

    Args:
        symbol: Symbol to fetch.

    Returns:
        Dictionary with comparison results.
    """
    setup_logging("WARNING")  # Suppress info logs
    print(f"\n{'=' * 60}")
    print("Sequential vs Concurrent Comparison")
    print(f"{'=' * 60}\n")

    fetchers = get_all_fetchers()

    # Sequential benchmark
    print("Running sequential fetch...")
    seq_start = time.perf_counter()
    for fetcher in fetchers:
        await fetcher.connect()
        try:
            await fetcher.fetch_open_interest(symbol)
        except Exception:
            pass
        await fetcher.close()
    seq_time = time.perf_counter() - seq_start
    print(f"  Sequential time: {seq_time:.3f}s")

    # Concurrent benchmark
    print("Running concurrent fetch...")
    orchestrator = FetchOrchestrator(fetchers)
    conc_start = time.perf_counter()
    await orchestrator.fetch_open_interest(symbol)
    conc_time = time.perf_counter() - conc_start
    await orchestrator.close_all()
    print(f"  Concurrent time: {conc_time:.3f}s")

    speedup = seq_time / conc_time if conc_time > 0 else 0
    print(f"\n{'=' * 60}")
    print(f"SPEEDUP: {speedup:.2f}x faster with concurrent fetching")
    print(f"{'=' * 60}\n")

    return {
        "sequential_time_s": seq_time,
        "concurrent_time_s": conc_time,
        "speedup_factor": speedup,
    }


if __name__ == "__main__":
    import sys

    print("Starting CCXT Pipeline Performance Benchmark")
    print("This requires active internet connection to exchanges.\n")

    try:
        # Run main benchmark
        results = asyncio.run(benchmark_concurrent_fetch(iterations=3))

        # Run comparison benchmark
        comparison = asyncio.run(benchmark_sequential_vs_concurrent())

        print("\n" + "=" * 60)
        print("BENCHMARK COMPLETE")
        print("=" * 60)

        # Summary
        if comparison["speedup_factor"] >= 2.0:
            print("✓ Concurrent fetching provides significant speedup")
        elif comparison["speedup_factor"] >= 1.2:
            print("✓ Concurrent fetching provides moderate speedup")
        else:
            print("⚠ Concurrent fetching speedup is minimal")

        if results["success_rate"] >= 0.9:
            print("✓ High success rate (>90%)")
        else:
            print("⚠ Low success rate - check network/API issues")

    except KeyboardInterrupt:
        print("\nBenchmark interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nBenchmark failed: {e}")
        print("Note: This benchmark requires active internet and exchange access.")
        sys.exit(1)
