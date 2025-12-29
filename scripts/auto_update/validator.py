# NautilusTrader Auto-Update Pipeline - Validator

"""Test runner and result parser for compatibility validation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from scripts.auto_update.models import TestResult


def run_pytest(
    working_dir: Path,
    test_paths: list[str] | None = None,
    markers: list[str] | None = None,
    dry_run: bool = False,
    timeout: int = 600,
    verbose: bool = False,
) -> dict[str, Any]:
    """Run pytest and capture results.

    Args:
        working_dir: Working directory for pytest
        test_paths: Specific test paths to run
        markers: Pytest markers to filter tests
        dry_run: If True, don't run tests
        timeout: Command timeout in seconds
        verbose: Enable verbose output

    Returns:
        Dict with success status, stdout, stderr, returncode
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "tests_run": 0,
            "stdout": "",
            "stderr": "",
        }

    # Build pytest command
    cmd = ["uv", "run", "pytest"]

    # Add test paths
    if test_paths:
        cmd.extend(test_paths)

    # Add markers
    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])

    # Add JSON output format
    cmd.extend(["--json-report", "--json-report-file=-"])

    # Add verbose flag
    if verbose:
        cmd.append("-v")

    try:
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "dry_run": False,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "dry_run": False,
            "error": f"pytest timed out after {timeout}s",
            "stdout": "",
            "stderr": "",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "dry_run": False,
            "error": "pytest not found in PATH",
            "stdout": "",
            "stderr": "",
        }


def parse_test_results(json_output: str) -> TestResult:
    """Parse pytest JSON output into TestResult model.

    Args:
        json_output: JSON string from pytest-json-report

    Returns:
        TestResult model with parsed data
    """
    if not json_output or not json_output.strip():
        return TestResult(
            passed=False,
            total_tests=0,
            failed_tests=0,
            skipped_tests=0,
            failed_test_names=[],
        )

    try:
        data = json.loads(json_output)
    except json.JSONDecodeError:
        return TestResult(
            passed=False,
            total_tests=0,
            failed_tests=0,
            skipped_tests=0,
            failed_test_names=[],
        )

    # Extract summary data
    summary = data.get("summary", {})
    total = summary.get("total", 0)
    failed = summary.get("failed", 0)
    skipped = summary.get("skipped", 0)
    errors = summary.get("error", 0)
    duration = data.get("duration", 0.0)

    # Combine failures and errors
    total_failures = failed + errors

    # Extract failure details
    failed_test_names = []
    tests = data.get("tests", [])
    for test in tests:
        if test.get("outcome") in ("failed", "error"):
            nodeid = test.get("nodeid", "unknown")
            failed_test_names.append(nodeid)

    # Determine if passed (no failures or errors)
    is_passed = total_failures == 0 and total > 0

    return TestResult(
        passed=is_passed,
        total_tests=total,
        failed_tests=total_failures,
        skipped_tests=skipped,
        failed_test_names=failed_test_names,
        duration_seconds=duration,
    )


def validate_update(
    working_dir: Path,
    test_paths: list[str] | None = None,
    markers: list[str] | None = None,
    dry_run: bool = False,
    timeout: int = 600,
) -> dict[str, Any]:
    """Run validation tests and determine if update can proceed.

    Args:
        working_dir: Working directory
        test_paths: Specific test paths
        markers: Pytest markers
        dry_run: If True, skip tests
        timeout: Test timeout

    Returns:
        Dict with success status, test_result, can_merge
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "test_result": TestResult(
                passed=True,
                total_tests=0,
                failed_tests=0,
                skipped_tests=0,
                failed_test_names=[],
            ),
            "can_merge": True,
        }

    # Run pytest
    pytest_result = run_pytest(
        working_dir=working_dir,
        test_paths=test_paths,
        markers=markers,
        dry_run=False,
        timeout=timeout,
    )

    # Parse results
    test_result = parse_test_results(pytest_result.get("stdout", ""))

    # Determine if can merge
    can_merge = test_result.passed

    return {
        "success": pytest_result["success"],
        "dry_run": False,
        "test_result": test_result,
        "can_merge": can_merge,
        "reason": "Tests passed" if can_merge else "Blocking: test failures detected",
        "pytest_returncode": pytest_result.get("returncode"),
        "stderr": pytest_result.get("stderr", ""),
    }


def format_test_report(test_result: TestResult) -> str:
    """Format TestResult as human-readable report.

    Args:
        test_result: TestResult model

    Returns:
        Formatted string report
    """
    # Build summary string
    summary = f"{test_result.passed_tests}/{test_result.total_tests} tests passed"
    if test_result.failed_tests:
        summary += f", {test_result.failed_tests} failed"
    if test_result.skipped_tests:
        summary += f", {test_result.skipped_tests} skipped"

    lines = [
        "## Test Results",
        "",
        f"**Status**: {'✅ PASSED' if test_result.passed else '❌ FAILED'}",
        f"**Summary**: {summary}",
        "",
    ]

    if test_result.failed_test_names:
        lines.append("### Failed Tests")
        lines.append("")
        for detail in test_result.failed_test_names[:10]:  # Limit to 10
            lines.append(f"- `{detail}`")
        if len(test_result.failed_test_names) > 10:
            lines.append(f"- ... and {len(test_result.failed_test_names) - 10} more")
        lines.append("")

    return "\n".join(lines)
