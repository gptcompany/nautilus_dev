#!/usr/bin/env python3
"""Performance Benchmark for Orderflow Module (T043).

Tests:
1. VPIN update performance (< 5ms per bucket)
2. Hawkes refit performance (< 1s for 10K events)
"""

import random
import time
from typing import NamedTuple

# Add strategies to path
import sys

sys.path.insert(0, "/media/sam/1TB/nautilus_dev")

from strategies.common.orderflow.config import VPINConfig, HawkesConfig
from strategies.common.orderflow.vpin import VPINIndicator
from strategies.common.orderflow.hawkes_ofi import HawkesOFI
from strategies.common.orderflow.trade_classifier import (
    TradeClassification,
    TradeSide,
)


class BenchmarkResult(NamedTuple):
    """Benchmark result."""

    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    passed: bool
    threshold_ms: float


def generate_classifications(count: int, bucket_size: float = 1000.0) -> list[TradeClassification]:
    """Generate synthetic trade classifications.

    Args:
        count: Number of classifications to generate
        bucket_size: Average volume per classification

    Returns:
        List of TradeClassification objects
    """
    random.seed(42)  # Reproducible results
    classifications = []

    base_price = 100.0
    timestamp_ns = 1_000_000_000_000  # Start at 1 second

    for i in range(count):
        # Random price movement
        base_price += random.uniform(-0.5, 0.5)

        # Random volume (1% to 10% of bucket_size)
        volume = bucket_size * random.uniform(0.01, 0.10)

        # Random side
        side = random.choice([TradeSide.BUY, TradeSide.SELL])

        # Increment timestamp by 10-100ms
        timestamp_ns += random.randint(10_000_000, 100_000_000)

        classifications.append(
            TradeClassification(
                side=side,
                volume=volume,
                price=base_price,
                timestamp_ns=timestamp_ns,
                method="benchmark",
                confidence=1.0,
            )
        )

    return classifications


def benchmark_vpin_update(iterations: int = 1000, threshold_ms: float = 5.0) -> BenchmarkResult:
    """Benchmark VPIN update with N classifications.

    Requirement: < 5ms per bucket completion

    Args:
        iterations: Number of classifications to process
        threshold_ms: Maximum allowed time per bucket (ms)

    Returns:
        BenchmarkResult with timing data
    """
    print(f"\n[VPIN] Benchmarking with {iterations} classifications...")

    # Configure VPIN with reasonable bucket size
    config = VPINConfig(
        bucket_size=1000.0,  # 1000 contracts per bucket
        n_buckets=50,  # 50 buckets for rolling VPIN
        classification_method="tick_rule",
    )

    indicator = VPINIndicator(config)
    classifications = generate_classifications(iterations, bucket_size=1000.0)

    # Time the updates
    start = time.perf_counter()

    for classification in classifications:
        indicator.update(classification)

    end = time.perf_counter()

    total_time_ms = (end - start) * 1000
    buckets_completed = len(indicator._buckets)

    # Calculate average time per bucket
    if buckets_completed > 0:
        avg_time_per_bucket_ms = total_time_ms / buckets_completed
    else:
        avg_time_per_bucket_ms = total_time_ms

    passed = avg_time_per_bucket_ms < threshold_ms

    print(f"  - Total time: {total_time_ms:.3f} ms")
    print(f"  - Buckets completed: {buckets_completed}")
    print(f"  - Avg per bucket: {avg_time_per_bucket_ms:.3f} ms")
    print(f"  - VPIN value: {indicator.value:.4f}")
    print(f"  - Threshold: < {threshold_ms} ms/bucket")
    print(f"  - PASS: {passed}")

    return BenchmarkResult(
        name="VPIN Update",
        iterations=buckets_completed,
        total_time_ms=total_time_ms,
        avg_time_ms=avg_time_per_bucket_ms,
        passed=passed,
        threshold_ms=threshold_ms,
    )


def benchmark_hawkes_refit(events: int = 10000, threshold_ms: float = 1000.0) -> BenchmarkResult:
    """Benchmark Hawkes refit with N events.

    Requirement: < 1 second (1000ms) for 10K events

    Args:
        events: Number of events to process before refit
        threshold_ms: Maximum allowed refit time (ms)

    Returns:
        BenchmarkResult with timing data
    """
    print(f"\n[Hawkes] Benchmarking with {events} events...")

    # Configure Hawkes with large refit interval (to manually trigger refit)
    config = HawkesConfig(
        decay_rate=1.0,
        lookback_ticks=events,  # Keep all events
        refit_interval=events + 1000,  # Don't auto-refit
        use_fixed_params=True,
        fixed_baseline=0.1,
        fixed_excitation=0.5,
    )

    indicator = HawkesOFI(config)
    classifications = generate_classifications(events)

    # First, populate the indicator with events
    print(f"  - Populating with {events} events...")
    for classification in classifications:
        indicator.update(classification)

    # Now benchmark the refit
    print(f"  - Timing refit...")
    start = time.perf_counter()

    indicator.refit()

    end = time.perf_counter()

    refit_time_ms = (end - start) * 1000
    passed = refit_time_ms < threshold_ms

    print(f"  - Refit time: {refit_time_ms:.3f} ms")
    print(f"  - Buy times in buffer: {len(indicator._buy_times)}")
    print(f"  - Sell times in buffer: {len(indicator._sell_times)}")
    print(f"  - OFI value: {indicator.ofi:.4f}")
    print(f"  - Threshold: < {threshold_ms} ms")
    print(f"  - PASS: {passed}")

    return BenchmarkResult(
        name="Hawkes Refit",
        iterations=1,
        total_time_ms=refit_time_ms,
        avg_time_ms=refit_time_ms,
        passed=passed,
        threshold_ms=threshold_ms,
    )


def benchmark_hawkes_update(events: int = 10000, threshold_ms: float = 0.1) -> BenchmarkResult:
    """Benchmark Hawkes update (single event).

    Tests the per-update overhead.

    Args:
        events: Number of events to process
        threshold_ms: Maximum allowed time per update (ms)

    Returns:
        BenchmarkResult with timing data
    """
    print(f"\n[Hawkes Update] Benchmarking with {events} events...")

    config = HawkesConfig(
        decay_rate=1.0,
        lookback_ticks=events,
        refit_interval=events + 1000,  # Don't auto-refit during benchmark
        use_fixed_params=True,
    )

    indicator = HawkesOFI(config)
    classifications = generate_classifications(events)

    start = time.perf_counter()

    for classification in classifications:
        indicator.update(classification)

    end = time.perf_counter()

    total_time_ms = (end - start) * 1000
    avg_time_ms = total_time_ms / events
    passed = avg_time_ms < threshold_ms

    print(f"  - Total time: {total_time_ms:.3f} ms")
    print(f"  - Avg per event: {avg_time_ms:.4f} ms")
    print(f"  - Threshold: < {threshold_ms} ms/event")
    print(f"  - PASS: {passed}")

    return BenchmarkResult(
        name="Hawkes Update",
        iterations=events,
        total_time_ms=total_time_ms,
        avg_time_ms=avg_time_ms,
        passed=passed,
        threshold_ms=threshold_ms,
    )


def main():
    """Run all benchmarks."""
    print("=" * 60)
    print("ORDERFLOW MODULE PERFORMANCE BENCHMARK (T043)")
    print("=" * 60)

    results = []

    # Benchmark 1: VPIN update with 1000 classifications
    results.append(benchmark_vpin_update(iterations=1000, threshold_ms=5.0))

    # Benchmark 2: Hawkes refit with 10000 events
    results.append(benchmark_hawkes_refit(events=10000, threshold_ms=1000.0))

    # Bonus: Hawkes per-update performance
    results.append(benchmark_hawkes_update(events=10000, threshold_ms=0.1))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.name}: {r.avg_time_ms:.4f} ms (threshold: {r.threshold_ms} ms)")
        if not r.passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL BENCHMARKS PASSED")
    else:
        print("SOME BENCHMARKS FAILED")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
