#!/usr/bin/env python3
"""Analyze backtest failure logs and extract root cause.

Parses backtest log files to identify failure patterns, extract error
messages, and determine probable root causes for investigation.

Usage:
    python analyze_backtest_failure.py --log-files backtest.log --strategy MyStrategy
    python analyze_backtest_failure.py --log-files *.log --output analysis.json
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class FailurePattern:
    """A recognized failure pattern."""

    pattern: str
    failure_type: str
    severity: str
    description: str
    diagnostic_steps: list[str] = field(default_factory=list)


# Known failure patterns from backtest-analyzer knowledge
FAILURE_PATTERNS: list[FailurePattern] = [
    FailurePattern(
        pattern=r"InsufficientMargin|margin.*insufficient",
        failure_type="margin_error",
        severity="high",
        description="Insufficient margin for trade execution",
        diagnostic_steps=[
            "Check position sizing logic",
            "Verify account balance initialization",
            "Review leverage settings",
            "Check max position limits",
        ],
    ),
    FailurePattern(
        pattern=r"OrderRejected|order.*rejected",
        failure_type="order_rejection",
        severity="high",
        description="Order was rejected by exchange/engine",
        diagnostic_steps=[
            "Check order parameters (price, quantity)",
            "Verify instrument specification",
            "Check trading hours/market status",
            "Review risk checks",
        ],
    ),
    FailurePattern(
        pattern=r"DataError|data.*error|missing.*data",
        failure_type="data_error",
        severity="medium",
        description="Data quality or availability issue",
        diagnostic_steps=[
            "Verify data catalog path",
            "Check data time range coverage",
            "Validate instrument identifiers",
            "Check for gaps in data",
        ],
    ),
    FailurePattern(
        pattern=r"IndicatorError|indicator.*failed|NaN.*indicator",
        failure_type="indicator_error",
        severity="medium",
        description="Technical indicator calculation error",
        diagnostic_steps=[
            "Check indicator warmup period",
            "Verify input data validity",
            "Check for division by zero",
            "Validate indicator parameters",
        ],
    ),
    FailurePattern(
        pattern=r"TimeoutError|timeout|timed.*out",
        failure_type="timeout",
        severity="medium",
        description="Operation timed out",
        diagnostic_steps=[
            "Check system resources",
            "Verify network connectivity",
            "Review async operation handling",
            "Check for deadlocks",
        ],
    ),
    FailurePattern(
        pattern=r"KeyError|AttributeError|TypeError",
        failure_type="code_error",
        severity="high",
        description="Programming error in strategy code",
        diagnostic_steps=[
            "Check variable/attribute names",
            "Verify data structure types",
            "Review recent code changes",
            "Add defensive checks",
        ],
    ),
    FailurePattern(
        pattern=r"PositionError|position.*invalid|double.*entry",
        failure_type="position_error",
        severity="high",
        description="Invalid position state",
        diagnostic_steps=[
            "Check position tracking logic",
            "Verify entry/exit signal handling",
            "Review order fill handling",
            "Check for race conditions",
        ],
    ),
    FailurePattern(
        pattern=r"ConfigError|config.*invalid|missing.*config",
        failure_type="config_error",
        severity="medium",
        description="Configuration issue",
        diagnostic_steps=[
            "Verify strategy config parameters",
            "Check instrument configuration",
            "Validate venue settings",
            "Review environment variables",
        ],
    ),
    FailurePattern(
        pattern=r"Drawdown.*exceeded|max.*loss|risk.*limit",
        failure_type="risk_breach",
        severity="critical",
        description="Risk limit breached during backtest",
        diagnostic_steps=[
            "Review risk parameters",
            "Analyze losing trades",
            "Check stop loss implementation",
            "Verify position sizing",
        ],
    ),
    FailurePattern(
        pattern=r"AssertionError|assert.*failed",
        failure_type="assertion_error",
        severity="medium",
        description="Assertion failed in code",
        diagnostic_steps=[
            "Check the assertion condition",
            "Verify assumptions about data",
            "Review recent changes",
            "Add logging around assertion",
        ],
    ),
]


@dataclass
class ErrorInstance:
    """A specific error occurrence in logs."""

    message: str
    file_path: str = ""
    line_number: int = 0
    timestamp: str = ""
    context_lines: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Result of backtest failure analysis."""

    strategy: str
    failure_type: str
    severity: str
    root_cause: str
    errors: list[ErrorInstance] = field(default_factory=list)
    diagnostic_steps: list[str] = field(default_factory=list)
    log_files_analyzed: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.0


def analyze_log_file(log_path: Path) -> list[ErrorInstance]:
    """Analyze a single log file for errors."""
    errors: list[ErrorInstance] = []

    try:
        content = log_path.read_text(errors="ignore")
        lines = content.split("\n")
    except Exception:
        return errors

    # Error detection patterns
    error_patterns = [
        r"ERROR",
        r"CRITICAL",
        r"FATAL",
        r"Exception",
        r"Traceback",
        r"FAILED",
        r"Error:",
    ]

    combined_pattern = "|".join(error_patterns)

    for i, line in enumerate(lines):
        if re.search(combined_pattern, line, re.IGNORECASE):
            # Extract timestamp if present
            timestamp_match = re.search(
                r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})", line
            )
            timestamp = timestamp_match.group(1) if timestamp_match else ""

            # Extract file reference if present
            file_match = re.search(r'File "([^"]+)", line (\d+)', line)
            file_path = file_match.group(1) if file_match else ""
            line_num = int(file_match.group(2)) if file_match else 0

            # Get context (surrounding lines)
            context_start = max(0, i - 2)
            context_end = min(len(lines), i + 5)
            context = lines[context_start:context_end]

            error = ErrorInstance(
                message=line.strip(),
                file_path=file_path,
                line_number=line_num,
                timestamp=timestamp,
                context_lines=context,
            )
            errors.append(error)

    return errors


def classify_failure(errors: list[ErrorInstance]) -> tuple[str, str, str, list[str]]:
    """Classify the failure type based on error patterns."""
    # Combine all error messages
    all_messages = " ".join(e.message for e in errors)
    all_context = " ".join(" ".join(e.context_lines) for e in errors)
    combined = f"{all_messages} {all_context}"

    # Match against known patterns
    for pattern in FAILURE_PATTERNS:
        if re.search(pattern.pattern, combined, re.IGNORECASE):
            return (
                pattern.failure_type,
                pattern.severity,
                pattern.description,
                pattern.diagnostic_steps,
            )

    # Default unknown
    return (
        "unknown",
        "medium",
        "Unknown failure - manual investigation required",
        [
            "Review full backtest logs",
            "Check recent code changes",
            "Run with verbose logging",
            "Compare with last successful run",
        ],
    )


def extract_root_cause(errors: list[ErrorInstance]) -> str:
    """Extract the most likely root cause from errors."""
    if not errors:
        return "No errors found in logs"

    # Look for the first exception/error
    for error in errors:
        if "Traceback" in error.message or "Exception" in error.message:
            # Find the actual error message after traceback
            for ctx_line in reversed(error.context_lines):
                if re.match(r"\w+Error:", ctx_line) or re.match(
                    r"\w+Exception:", ctx_line
                ):
                    return ctx_line.strip()

        if "Error:" in error.message or "FAILED" in error.message:
            return error.message.strip()

    # Return first error message
    return errors[0].message.strip()[:200]


def analyze_backtest_failure(
    log_files: list[Path],
    strategy: str,
) -> AnalysisResult:
    """Analyze backtest failure from log files."""
    all_errors: list[ErrorInstance] = []
    analyzed_files: list[str] = []

    # Analyze each log file
    for log_file in log_files:
        if log_file.exists():
            errors = analyze_log_file(log_file)
            all_errors.extend(errors)
            analyzed_files.append(str(log_file))

    # Classify failure
    failure_type, severity, description, diagnostic_steps = classify_failure(all_errors)

    # Extract root cause
    root_cause = extract_root_cause(all_errors)

    # Calculate confidence based on match quality
    confidence = 0.5  # Base confidence
    if failure_type != "unknown":
        confidence = 0.8
    if all_errors:
        confidence += 0.1
    if len(all_errors) > 3:
        confidence = min(confidence, 0.7)  # Many errors = less certain

    return AnalysisResult(
        strategy=strategy,
        failure_type=failure_type,
        severity=severity,
        root_cause=root_cause or description,
        errors=all_errors[:10],  # Limit to first 10 errors
        diagnostic_steps=diagnostic_steps,
        log_files_analyzed=analyzed_files,
        confidence=confidence,
    )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze backtest failure logs")
    parser.add_argument(
        "--log-files",
        nargs="+",
        type=Path,
        required=True,
        help="Log files to analyze",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="unknown",
        help="Strategy name",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file for analysis results",
    )

    args = parser.parse_args()

    print(f"Analyzing {len(args.log_files)} log files for strategy: {args.strategy}")

    # Run analysis
    result = analyze_backtest_failure(args.log_files, args.strategy)

    # Print summary
    print()
    print("=== Analysis Summary ===")
    print(f"Failure Type: {result.failure_type}")
    print(f"Severity: {result.severity}")
    print(f"Root Cause: {result.root_cause}")
    print(f"Errors Found: {len(result.errors)}")
    print(f"Confidence: {result.confidence:.1%}")
    print()
    print("Diagnostic Steps:")
    for i, step in enumerate(result.diagnostic_steps, 1):
        print(f"  {i}. {step}")

    # Write output
    if args.output:
        output_data: dict[str, Any] = {
            "strategy": result.strategy,
            "failure_type": result.failure_type,
            "severity": result.severity,
            "root_cause": result.root_cause,
            "diagnostic_steps": result.diagnostic_steps,
            "confidence": result.confidence,
            "timestamp": result.timestamp,
            "log_files_analyzed": result.log_files_analyzed,
            "errors": [
                {
                    "message": e.message,
                    "file_path": e.file_path,
                    "line_number": e.line_number,
                    "timestamp": e.timestamp,
                }
                for e in result.errors
            ],
        }

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output_data, indent=2))
        print(f"\nAnalysis written to: {args.output}")


if __name__ == "__main__":
    main()
