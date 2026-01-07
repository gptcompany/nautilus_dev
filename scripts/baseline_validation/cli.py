"""CLI interface for baseline validation.

Commands:
    run     - Run walk-forward validation
    report  - Generate validation report
    compare - Compare specific contenders

Usage:
    $ python -m scripts.baseline_validation.cli run --mock
    $ python -m scripts.baseline_validation.cli run --config config.yaml
    $ python -m scripts.baseline_validation.cli report --input results.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import click
import yaml  # type: ignore[import-untyped]

from scripts.baseline_validation.comparison_validator import ComparisonValidator
from scripts.baseline_validation.config_models import BaselineValidationConfig
from scripts.baseline_validation.report import (
    create_report_from_validation_run,
    export_to_json,
    generate_markdown_report,
)
from scripts.baseline_validation.report_models import ValidationReport

if TYPE_CHECKING:
    pass


@click.group()
@click.version_option(version="0.1.0", prog_name="baseline-validation")
def cli() -> None:
    """Baseline Validation Tool - PMW (Prove Me Wrong) validation framework.

    Compare adaptive sizing against simple baselines using walk-forward validation.
    """
    pass


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="YAML config file")
@click.option("--mock", is_flag=True, help="Use mock data instead of real backtest")
@click.option("--seed", "-s", type=int, default=42, help="Random seed for reproducibility")
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format",
)
def run(
    config: str | None,
    mock: bool,
    seed: int,
    output: str | None,
    format: str,
) -> None:
    """Run walk-forward validation.

    Examples:
        $ baseline-validation run --mock
        $ baseline-validation run --config myconfig.yaml
        $ baseline-validation run --mock --output results.json --format json
    """
    # Load config
    if config:
        cfg = _load_config(config)
    else:
        cfg = BaselineValidationConfig.default()

    cfg.seed = seed

    # Create validator and run
    validator = ComparisonValidator(cfg)

    click.echo(f"Running validation with seed={seed}...")
    click.echo(f"  Train: {cfg.validation.train_months} months")
    click.echo(f"  Test: {cfg.validation.test_months} months")
    click.echo(f"  Contenders: {list(validator.contenders.keys())}")
    click.echo()

    if mock:
        result = validator.run_mock(seed=seed)
    else:
        result = validator.run()

    # Generate report
    report = create_report_from_validation_run(result)

    # Output
    if format == "json":
        output_content = export_to_json(report)
    elif format == "markdown":
        output_content = generate_markdown_report(report)
    else:
        output_content = _format_text_output(report)

    if output:
        Path(output).write_text(output_content)
        click.echo(f"Results written to {output}")
    else:
        click.echo(output_content)


@cli.command()
@click.option("--input", "-i", type=click.Path(exists=True), help="JSON results file")
@click.option("--output", "-o", type=click.Path(), help="Output file for report")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "text"]),
    default="markdown",
    help="Report format",
)
def report(
    input: str | None,
    output: str | None,
    format: str,
) -> None:
    """Generate validation report from saved results.

    Examples:
        $ baseline-validation report --input results.json
        $ baseline-validation report --input results.json --output report.md
    """
    if not input:
        click.echo("Error: --input is required for report generation", err=True)
        raise SystemExit(1)

    # Load results
    with open(input) as f:
        data = json.load(f)

    report_obj = ValidationReport.model_validate(data)

    # Generate report
    if format == "markdown":
        content = generate_markdown_report(report_obj)
    else:
        content = _format_text_output(report_obj)

    if output:
        Path(output).write_text(content)
        click.echo(f"Report written to {output}")
    else:
        click.echo(content)


@cli.command()
@click.option("--contenders", "-c", multiple=True, help="Contenders to compare")
@click.option("--config", type=click.Path(exists=True), help="YAML config file")
@click.option("--mock", is_flag=True, help="Use mock data")
def compare(
    contenders: tuple[str, ...],
    config: str | None,
    mock: bool,
) -> None:
    """Compare specific contenders.

    Examples:
        $ baseline-validation compare --contenders adaptive --contenders fixed
        $ baseline-validation compare -c adaptive -c buyhold --mock
    """
    # Load config
    if config:
        cfg = _load_config(config)
    else:
        cfg = BaselineValidationConfig.default()

    # Filter contenders if specified
    if contenders:
        # Disable non-specified contenders
        for ctype in cfg.contenders:
            if ctype not in contenders:
                cfg.contenders[ctype].enabled = False

    # Run comparison
    validator = ComparisonValidator(cfg)

    click.echo(f"Comparing: {list(validator.contenders.keys())}")

    if mock:
        result = validator.run_mock()
    else:
        result = validator.run()

    # Display comparison
    report = create_report_from_validation_run(result)
    click.echo()
    click.echo(_format_text_output(report))


def _load_config(config_path: str) -> BaselineValidationConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Path to YAML config file.

    Returns:
        BaselineValidationConfig instance.
    """
    with open(config_path) as f:
        data = yaml.safe_load(f)

    # Start with defaults and override
    config = BaselineValidationConfig.default()

    # B1 fix: Handle empty YAML file (returns None)
    if not data:
        return config

    # Update validation settings
    if "validation" in data:
        for key, value in data["validation"].items():
            if hasattr(config.validation, key):
                setattr(config.validation, key, value)

    # Update other settings
    if "seed" in data:
        config.seed = data["seed"]

    if "success_criteria" in data:
        for key, value in data["success_criteria"].items():
            if hasattr(config.success_criteria, key):
                setattr(config.success_criteria, key, value)

    return config


def _format_text_output(report: ValidationReport) -> str:
    """Format report as plain text.

    Args:
        report: ValidationReport to format.

    Returns:
        Plain text representation.
    """
    lines = [
        "=" * 60,
        "BASELINE VALIDATION REPORT",
        "=" * 60,
        "",
        f"Verdict: {report.verdict.value}",
        f"Confidence: {report.confidence:.0%}",
        "",
        "Recommendation:",
        f"  {report.recommendation}",
        "",
        "-" * 60,
        "CONTENDER COMPARISON",
        "-" * 60,
        "",
    ]

    # Add contender metrics
    for name, summary in report.contender_summaries.items():
        lines.extend(
            [
                f"{name.upper()}:",
                f"  Avg Sharpe: {summary.avg_sharpe:.3f}",
                f"  Std Sharpe: {summary.std_sharpe:.3f}",
                f"  Max Drawdown: {summary.max_drawdown:.1%}",
                f"  Win Rate: {summary.win_rate:.1%}",
                f"  Total Trades: {summary.total_trades}",
                "",
            ]
        )

    lines.extend(
        [
            "-" * 60,
            f"Windows: {report.window_count}",
            f"Data Range: {report.data_start.date()} to {report.data_end.date()}",
            "=" * 60,
        ]
    )

    return "\n".join(lines)


# Entry point
if __name__ == "__main__":
    cli()
