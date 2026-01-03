#!/usr/bin/env python3
"""Test and score BOCD implementation approaches.

This script evaluates three BOCD implementations on:
1. Correctness (tests pass)
2. Performance (<5ms per update)
3. Numerical stability (handles outliers)
4. Edge cases
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.common.regime_detection.config import BOCDConfig


def test_approach(module_name: str, approach_name: str) -> dict:
    """Test a single BOCD approach.

    Args:
        module_name: Full module path.
        approach_name: Name for display.

    Returns:
        Dictionary with test results.
    """
    results = {
        "name": approach_name,
        "tests_passed": 0,
        "tests_total": 0,
        "performance_ms": 0.0,
        "stability_score": 0,
        "edge_case_score": 0,
        "errors": [],
    }

    try:
        # Dynamic import
        module = __import__(module_name, fromlist=["BOCD"])
        BOCD = module.BOCD
    except Exception as e:
        results["errors"].append(f"Import error: {e}")
        return results

    config = BOCDConfig(hazard_rate=0.01, detection_threshold=0.5)

    # Test 1: Basic update
    try:
        bocd = BOCD(config)
        bocd.update(0.01)
        assert bocd.t == 1
        results["tests_passed"] += 1
    except Exception as e:
        results["errors"].append(f"Basic update: {e}")
    results["tests_total"] += 1

    # Test 2: Multiple updates track run length
    try:
        bocd = BOCD(config)
        for i in range(100):
            bocd.update(np.random.normal(0, 0.01))
        assert bocd.t == 100
        rld = bocd.get_run_length_distribution()
        assert len(rld) == 101
        results["tests_passed"] += 1
    except Exception as e:
        results["errors"].append(f"Multiple updates: {e}")
    results["tests_total"] += 1

    # Test 3: Probability bounds
    try:
        bocd = BOCD(config)
        for obs in [0.01, -0.02, 0.015, -0.01]:
            prob = bocd.update(obs)
            assert 0.0 <= prob <= 1.0, f"Prob out of bounds: {prob}"
        results["tests_passed"] += 1
    except Exception as e:
        results["errors"].append(f"Probability bounds: {e}")
    results["tests_total"] += 1

    # Test 4: Run length distribution sums to 1
    try:
        bocd = BOCD(config)
        np.random.seed(42)
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)
        rld = bocd.get_run_length_distribution()
        assert abs(np.sum(rld) - 1.0) < 1e-5, f"Sum: {np.sum(rld)}"
        results["tests_passed"] += 1
    except Exception as e:
        results["errors"].append(f"Distribution sum: {e}")
    results["tests_total"] += 1

    # Test 5: Run length distribution non-negative
    try:
        bocd = BOCD(config)
        np.random.seed(42)
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)
        rld = bocd.get_run_length_distribution()
        assert np.all(rld >= 0.0), "Negative probabilities found"
        results["tests_passed"] += 1
    except Exception as e:
        results["errors"].append(f"Non-negative: {e}")
    results["tests_total"] += 1

    # Test 6: is_changepoint with threshold
    try:
        bocd = BOCD(config)
        np.random.seed(42)
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)
        prob = bocd.get_changepoint_probability()
        result_high = bocd.is_changepoint(threshold=0.99)
        assert not result_high
        if prob > 0:
            result_low = bocd.is_changepoint(threshold=0.0)
            assert result_low
        results["tests_passed"] += 1
    except Exception as e:
        results["errors"].append(f"is_changepoint: {e}")
    results["tests_total"] += 1

    # Test 7: Reset clears state
    try:
        bocd = BOCD(config)
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)
        bocd.reset()
        assert bocd.t == 0
        rld = bocd.get_run_length_distribution()
        assert len(rld) == 1
        assert rld[0] == 1.0
        results["tests_passed"] += 1
    except Exception as e:
        results["errors"].append(f"Reset: {e}")
    results["tests_total"] += 1

    # Test 8: Detect synthetic regime change
    try:
        np.random.seed(42)
        regime1 = np.random.normal(0.0001, 0.01, 300)
        regime2 = np.random.normal(-0.0002, 0.03, 400)
        regime3 = np.random.normal(0.0001, 0.015, 300)
        sample_returns = np.concatenate([regime1, regime2, regime3])

        bocd = BOCD(config)
        changepoints_detected = []
        for i, ret in enumerate(sample_returns):
            bocd.update(ret)
            if bocd.is_changepoint(threshold=0.5):
                changepoints_detected.append(i)

        assert len(changepoints_detected) > 0
        results["tests_passed"] += 1
    except Exception as e:
        results["errors"].append(f"Regime detection: {e}")
    results["tests_total"] += 1

    # Test 9: Performance (<5ms per update)
    try:
        bocd = BOCD(config)
        # Warmup
        for obs in np.random.normal(0, 0.01, 100):
            bocd.update(obs)

        # Measure
        start = time.time()
        for _ in range(100):
            bocd.update(np.random.normal(0, 0.01))
        elapsed = (time.time() - start) / 100
        results["performance_ms"] = elapsed * 1000

        if elapsed < 0.005:
            results["tests_passed"] += 1
        else:
            results["errors"].append(f"Performance: {elapsed * 1000:.2f}ms > 5ms")
    except Exception as e:
        results["errors"].append(f"Performance: {e}")
    results["tests_total"] += 1

    # Test 10: Outlier handling (stability)
    try:
        bocd = BOCD(config)
        for obs in np.random.normal(0, 0.01, 50):
            bocd.update(obs)

        # Extreme outlier
        bocd.update(10.0)  # 1000 std devs

        prob = bocd.get_changepoint_probability()
        assert 0.0 <= prob <= 1.0
        rld = bocd.get_run_length_distribution()
        assert abs(np.sum(rld) - 1.0) < 1e-4
        results["stability_score"] = 10
        results["tests_passed"] += 1
    except Exception as e:
        results["errors"].append(f"Outlier handling: {e}")
        results["stability_score"] = 0
    results["tests_total"] += 1

    return results


def main():
    """Run tests on all approaches and display results."""
    print("=" * 70)
    print("BOCD IMPLEMENTATION COMPARISON")
    print("=" * 70)
    print()

    approaches = [
        ("strategies.common.regime_detection.bocd_approach_a", "Approach A: Standard"),
        (
            "strategies.common.regime_detection.bocd_approach_b",
            "Approach B: Vectorized",
        ),
        ("strategies.common.regime_detection.bocd_approach_c", "Approach C: Log-space"),
    ]

    all_results = []

    for module_name, name in approaches:
        print(f"\nTesting {name}...")
        results = test_approach(module_name, name)
        all_results.append(results)

        print(f"  Tests: {results['tests_passed']}/{results['tests_total']}")
        print(f"  Performance: {results['performance_ms']:.3f}ms")
        if results["errors"]:
            print(f"  Errors: {results['errors']}")

    # Calculate scores
    print("\n" + "=" * 70)
    print("FITNESS SCORES")
    print("=" * 70)
    print()
    print(
        f"{'Approach':<30} | {'Tests':<10} | {'Perf(ms)':<10} | {'Stability':<10} | {'TOTAL':<10}"
    )
    print("-" * 80)

    for r in all_results:
        test_score = r["tests_passed"] * 10 // max(r["tests_total"], 1)
        perf_score = (
            10 if r["performance_ms"] < 5 else max(0, 10 - int(r["performance_ms"]))
        )
        stability_score = r["stability_score"]
        total = test_score + perf_score + stability_score

        print(
            f"{r['name']:<30} | {test_score}/10     | {perf_score}/10     | "
            f"{stability_score}/10     | {total}/30"
        )

    # Winner
    print()
    winner = max(
        all_results,
        key=lambda r: r["tests_passed"] * 10
        + (10 if r["performance_ms"] < 5 else 0)
        + r["stability_score"],
    )
    print(f"WINNER: {winner['name']}")
    print()


if __name__ == "__main__":
    main()
