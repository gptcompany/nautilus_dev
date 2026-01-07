"""CLI for walk-forward validation."""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from scripts.alpha_evolve.walk_forward.config import WalkForwardConfig
from scripts.alpha_evolve.walk_forward.report import export_json, generate_report
from scripts.alpha_evolve.walk_forward.validator import WalkForwardValidator


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="walk-forward",
        description="Walk-forward validation for trading strategies",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a strategy using walk-forward analysis",
    )
    validate_parser.add_argument(
        "--strategy",
        required=True,
        type=Path,
        help="Path to strategy file",
    )
    validate_parser.add_argument(
        "--start",
        required=True,
        type=parse_date,
        help="Start date (YYYY-MM-DD)",
    )
    validate_parser.add_argument(
        "--end",
        required=True,
        type=parse_date,
        help="End date (YYYY-MM-DD)",
    )
    validate_parser.add_argument(
        "--train-months",
        type=int,
        default=6,
        help="Training window size in months (default: 6)",
    )
    validate_parser.add_argument(
        "--test-months",
        type=int,
        default=3,
        help="Test window size in months (default: 3)",
    )
    validate_parser.add_argument(
        "--step-months",
        type=int,
        default=3,
        help="Rolling step size in months (default: 3)",
    )
    validate_parser.add_argument(
        "--embargo-before",
        type=int,
        default=5,
        help="Pre-test embargo days (default: 5)",
    )
    validate_parser.add_argument(
        "--embargo-after",
        type=int,
        default=3,
        help="Post-test embargo days (default: 3)",
    )
    validate_parser.add_argument(
        "--min-robustness",
        type=float,
        default=60.0,
        help="Minimum robustness score (default: 60)",
    )
    validate_parser.add_argument(
        "--output",
        type=Path,
        help="Output file for report (default: stdout)",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of Markdown",
    )

    # Report command
    report_parser = subparsers.add_parser(
        "report",
        help="Generate report from validation results",
    )
    report_parser.add_argument(
        "--strategy",
        required=True,
        type=Path,
        help="Path to strategy file",
    )
    report_parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output file for report",
    )
    report_parser.add_argument(
        "--start",
        required=True,
        type=parse_date,
        help="Start date (YYYY-MM-DD)",
    )
    report_parser.add_argument(
        "--end",
        required=True,
        type=parse_date,
        help="End date (YYYY-MM-DD)",
    )

    return parser


async def run_validate(args: argparse.Namespace) -> int:
    """Run validation command."""
    # Read strategy code
    if not args.strategy.exists():
        print(f"Error: Strategy file not found: {args.strategy}", file=sys.stderr)
        return 1

    strategy_code = args.strategy.read_text()

    # Create config
    config = WalkForwardConfig(
        data_start=args.start,
        data_end=args.end,
        train_months=args.train_months,
        test_months=args.test_months,
        step_months=args.step_months,
        embargo_before_days=args.embargo_before,
        embargo_after_days=args.embargo_after,
        min_robustness_score=args.min_robustness,
    )

    # Import evaluator (would be from actual evaluator module)
    try:
        from scripts.alpha_evolve.evaluator import StrategyEvaluator

        evaluator = StrategyEvaluator()
    except ImportError:
        print("Warning: StrategyEvaluator not available, using mock", file=sys.stderr)
        from unittest.mock import AsyncMock

        from scripts.alpha_evolve.walk_forward.models import WindowMetrics

        evaluator = AsyncMock()
        evaluator.evaluate = AsyncMock(
            return_value=WindowMetrics(
                sharpe_ratio=1.0,
                calmar_ratio=2.0,
                max_drawdown=0.10,
                total_return=0.08,
                win_rate=0.55,
                trade_count=40,
            )
        )

    # Run validation
    validator = WalkForwardValidator(config, evaluator)
    result = await validator.validate(strategy_code)

    # Generate output
    if args.json:
        output = export_json(result)
    else:
        output = generate_report(result)

    # Write output
    if args.output:
        args.output.write_text(output)
        print(f"Report written to: {args.output}")
    else:
        print(output)

    # Return exit code based on pass/fail
    return 0 if result.passed else 1


async def run_report(args: argparse.Namespace) -> int:
    """Run report command (validates and generates report)."""
    # For now, report is same as validate with output
    args.json = False
    return await run_validate(args)


def main() -> int:
    """CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "validate":
        return asyncio.run(run_validate(args))
    elif args.command == "report":
        return asyncio.run(run_report(args))
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
