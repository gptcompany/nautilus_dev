"""
Alpha-Evolve CLI - Command-line interface for evolution management.

Provides commands to start, monitor, and manage evolution runs.

Part of spec-009: Alpha-Evolve Controller & CLI
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import click
from tqdm import tqdm

from scripts.alpha_evolve.config import EvolutionConfig
from scripts.alpha_evolve.controller import (
    EvolutionController,
    EvolutionProgress,
    EvolutionStatus,
    ProgressEvent,
    ProgressEventType,
    StopCondition,
)
from scripts.alpha_evolve.evaluator import BacktestConfig, StrategyEvaluator
from scripts.alpha_evolve.mutator import LLMMutator
from scripts.alpha_evolve.store import ProgramStore


# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_NOT_FOUND = 3
EXIT_STORE_ERROR = 5
EXIT_INTERRUPTED = 130


@click.group()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to config.yaml",
)
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path),
    default="./evolve.db",
    help="Path to SQLite database",
)
@click.pass_context
def evolve(ctx: click.Context, config_path: Path | None, db_path: Path) -> None:
    """Alpha-Evolve: Evolutionary strategy optimization."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path
    ctx.obj["db_path"] = db_path


@evolve.command()
@click.option("--seed", required=True, help='Seed strategy name (e.g., "momentum")')
@click.option("--iterations", default=50, type=int, help="Number of iterations")
@click.option("--experiment", default=None, help="Experiment name (auto-generated if not set)")
@click.option("--target-fitness", type=float, help="Stop when fitness >= target")
@click.option("--timeout", type=int, help="Max runtime in seconds")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.pass_context
def start(
    ctx: click.Context,
    seed: str,
    iterations: int,
    experiment: str | None,
    target_fitness: float | None,
    timeout: int | None,
    verbose: bool,
) -> None:
    """Start a new evolution run."""
    config_path = ctx.obj.get("config_path")
    db_path = ctx.obj["db_path"]

    # Generate experiment name if not provided
    if experiment is None:
        experiment = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        # Load configuration
        config = EvolutionConfig.load(config_path)
    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(EXIT_CONFIG_ERROR)

    # Initialize store
    try:
        store = ProgramStore(
            db_path,
            population_size=config.population_size,
            archive_size=config.archive_size,
        )
    except Exception as e:
        click.echo(f"Store error: {e}", err=True)
        sys.exit(EXIT_STORE_ERROR)

    # Create stop condition
    stop_condition = StopCondition(
        max_iterations=iterations,
        target_fitness=target_fitness,
        max_time_seconds=timeout,
    )

    # Create evaluator with default backtest config
    # Note: In production, this would come from config file
    backtest_config = BacktestConfig(
        catalog_path="/media/sam/1TB/data/catalog",
        instrument_id="BTCUSDT-PERP.BINANCE",
        start_date="2024-01-01",
        end_date="2024-06-01",
    )

    evaluator = StrategyEvaluator(
        default_config=backtest_config,
        max_concurrent=config.max_concurrent,
    )

    # Create controller
    controller = EvolutionController(
        config=config,
        store=store,
        evaluator=evaluator,
        mutator=LLMMutator(),
    )

    # Progress bar
    pbar = tqdm(total=iterations, desc="Evolution", unit="iter")

    def on_progress(event: ProgressEvent) -> None:
        if event.event_type == ProgressEventType.ITERATION_COMPLETE:
            pbar.update(1)
            if verbose:
                data = event.data
                click.echo(
                    f"  Iter {event.iteration}: "
                    f"best={data.get('best_fitness', 0):.4f}, "
                    f"pop={data.get('population_size', 0)}"
                )

    click.echo(f"Starting evolution: {experiment}")
    click.echo(f"  Seed: {seed}")
    click.echo(f"  Iterations: {iterations}")
    if target_fitness:
        click.echo(f"  Target fitness: {target_fitness}")

    try:
        result = asyncio.run(
            controller.run(
                seed_strategy=seed,
                experiment=experiment,
                iterations=iterations,
                stop_condition=stop_condition,
                on_progress=on_progress,
            )
        )
    except KeyboardInterrupt:
        pbar.close()
        click.echo("\nInterrupted by user")
        sys.exit(EXIT_INTERRUPTED)
    except Exception as e:
        pbar.close()
        click.echo(f"Evolution failed: {e}", err=True)
        sys.exit(EXIT_ERROR)

    pbar.close()

    # Print summary
    click.echo("\nEvolution complete!")
    click.echo(f"  Status: {result.status.value}")
    click.echo(f"  Iterations: {result.iterations_completed}")
    click.echo(f"  Duration: {result.elapsed_seconds:.1f}s")
    if result.best_strategy and result.best_strategy.metrics:
        m = result.best_strategy.metrics
        click.echo(f"  Best Calmar: {m.calmar_ratio:.4f}")
        click.echo(f"  Best Sharpe: {m.sharpe_ratio:.4f}")
    click.echo(f"  Mutations: {result.successful_mutations}/{result.total_mutations}")
    if result.stop_reason:
        click.echo(f"  Stop reason: {result.stop_reason}")


@evolve.command()
@click.argument("experiment", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--watch", is_flag=True, help="Continuously update")
@click.pass_context
def status(
    ctx: click.Context,
    experiment: str | None,
    as_json: bool,
    watch: bool,
) -> None:
    """Show evolution progress."""
    db_path = ctx.obj["db_path"]

    if not Path(db_path).exists():
        click.echo("No database found", err=True)
        sys.exit(EXIT_NOT_FOUND)

    store = ProgramStore(db_path)

    if experiment is None:
        # List all experiments
        _list_experiments(store, as_json)
        return

    # Get experiment info
    count = store.count(experiment)
    if count == 0:
        click.echo(f"Experiment not found: {experiment}", err=True)
        sys.exit(EXIT_NOT_FOUND)

    def display_status():
        top = store.top_k(k=1, metric="calmar", experiment=experiment)
        best = top[0] if top else None
        generation = best.generation if best else 0
        best_fitness = best.metrics.calmar_ratio if best and best.metrics else 0

        progress = EvolutionProgress(
            experiment=experiment,
            iteration=generation,
            generation=generation,
            best_fitness=best_fitness,
            best_strategy_id=best.id if best else None,
            population_size=store.count(experiment),
            elapsed_seconds=0,
            status=EvolutionStatus.COMPLETED,  # Assume completed for static view
        )

        if as_json:
            data = {
                "experiment": progress.experiment,
                "status": progress.status.value,
                "iteration": progress.iteration,
                "generation": progress.generation,
                "best_fitness": progress.best_fitness,
                "best_strategy_id": progress.best_strategy_id,
                "population_size": progress.population_size,
            }
            click.echo(json.dumps(data, indent=2))
        else:
            click.echo(f"Evolution Status: {experiment}")
            click.echo("=" * 50)
            click.echo(f"Status:       {progress.status.value}")
            click.echo(f"Generation:   {progress.generation}")
            click.echo(f"Best Fitness: {progress.best_fitness:.4f}")
            click.echo(f"Population:   {progress.population_size}")
            if progress.best_strategy_id:
                click.echo(f"Best ID:      {progress.best_strategy_id[:8]}...")

    if watch:
        try:
            while True:
                click.clear()
                display_status()
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        display_status()


@evolve.command()
@click.argument("experiment", required=False)
@click.option("-k", "--top-k", default=10, type=int, help="Number of strategies to show")
@click.option("--metric", default="calmar", help="Sort metric: calmar|sharpe|cagr")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--with-code", is_flag=True, help="Include strategy code")
@click.pass_context
def best(
    ctx: click.Context,
    experiment: str | None,
    top_k: int,
    metric: str,
    as_json: bool,
    with_code: bool,
) -> None:
    """Display top strategies from hall-of-fame."""
    db_path = ctx.obj["db_path"]

    if not Path(db_path).exists():
        click.echo("No database found", err=True)
        sys.exit(EXIT_NOT_FOUND)

    store = ProgramStore(db_path)

    strategies = store.top_k(k=top_k, metric=metric, experiment=experiment)

    if not strategies:
        click.echo("No strategies found", err=True)
        sys.exit(EXIT_NOT_FOUND)

    if as_json:
        data = []
        for s in strategies:
            item = {
                "id": s.id,
                "generation": s.generation,
                "experiment": s.experiment,
            }
            if s.metrics:
                item["calmar"] = s.metrics.calmar_ratio
                item["sharpe"] = s.metrics.sharpe_ratio
                item["max_drawdown"] = s.metrics.max_drawdown
                item["cagr"] = s.metrics.cagr
            if with_code:
                item["code"] = s.code
            data.append(item)
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Top {len(strategies)} Strategies (by {metric})")
        click.echo("=" * 70)
        click.echo(f"{'Rank':<5} {'ID':<10} {'Gen':<5} {'Calmar':<10} {'Sharpe':<10} {'MaxDD':<10}")
        click.echo("-" * 70)
        for i, s in enumerate(strategies, 1):
            m = s.metrics
            if m:
                click.echo(
                    f"{i:<5} {s.id[:8]:<10} {s.generation:<5} "
                    f"{m.calmar_ratio:<10.4f} {m.sharpe_ratio:<10.4f} "
                    f"{m.max_drawdown:<10.2%}"
                )
            else:
                click.echo(f"{i:<5} {s.id[:8]:<10} {s.generation:<5} (no metrics)")


@evolve.command()
@click.argument("strategy_id")
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output file path")
@click.option("--with-lineage", is_flag=True, help="Include parent chain as comments")
@click.pass_context
def export(
    ctx: click.Context,
    strategy_id: str,
    output: Path | None,
    with_lineage: bool,
) -> None:
    """Export strategy code to file."""
    db_path = ctx.obj["db_path"]

    if not Path(db_path).exists():
        click.echo("No database found", err=True)
        sys.exit(EXIT_NOT_FOUND)

    store = ProgramStore(db_path)

    # Find strategy (support partial ID match)
    strategy = store.get(strategy_id)
    if strategy is None:
        # Try prefix match
        for prog in store.top_k(k=1000, metric="calmar"):
            if prog.id.startswith(strategy_id):
                strategy = prog
                break

    if strategy is None:
        click.echo(f"Strategy not found: {strategy_id}", err=True)
        sys.exit(EXIT_NOT_FOUND)

    # Build output
    header_lines = [
        '"""',
        f"Evolved Strategy: {strategy.id}",
        f"Generation: {strategy.generation}",
        f"Parent: {strategy.parent_id or 'seed'}",
    ]

    if strategy.metrics:
        m = strategy.metrics
        header_lines.append(f"Fitness: Calmar={m.calmar_ratio:.4f}, Sharpe={m.sharpe_ratio:.4f}")

    if with_lineage:
        lineage = store.get_lineage(strategy.id)
        if len(lineage) > 1:
            header_lines.append("")
            header_lines.append("Lineage:")
            for ancestor in lineage[1:]:
                calmar = ancestor.metrics.calmar_ratio if ancestor.metrics else 0
                header_lines.append(
                    f"  <- {ancestor.id[:8]}... (gen {ancestor.generation}, calmar={calmar:.2f})"
                )

    header_lines.append('"""')
    header = "\n".join(header_lines)

    full_code = f"{header}\n\n{strategy.code}"

    # Output
    if output is None:
        output = Path(f"./{strategy.id[:8]}.py")

    output.write_text(full_code)
    click.echo(f"Exported to: {output}")


@evolve.command()
@click.argument("experiment", required=False)
@click.option("--force", is_flag=True, help="Immediate stop")
@click.pass_context
def stop(ctx: click.Context, experiment: str | None, force: bool) -> None:
    """Stop running evolution (placeholder)."""
    click.echo("Stop command: would signal running evolution to stop")
    click.echo("Note: This requires a running controller instance")
    # In a real implementation, this would signal via a shared flag or IPC


@evolve.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--active", is_flag=True, help="Show only active experiments")
@click.pass_context
def list_cmd(ctx: click.Context, as_json: bool, active: bool) -> None:
    """List all experiments."""
    db_path = ctx.obj["db_path"]

    if not Path(db_path).exists():
        click.echo("No database found", err=True)
        sys.exit(EXIT_NOT_FOUND)

    store = ProgramStore(db_path)
    _list_experiments(store, as_json)


@evolve.command()
@click.argument("experiment")
@click.option("--iterations", type=int, help="Additional iterations")
@click.pass_context
def resume(ctx: click.Context, experiment: str, iterations: int | None) -> None:
    """Resume a paused evolution."""
    db_path = ctx.obj["db_path"]

    if not Path(db_path).exists():
        click.echo("No database found", err=True)
        sys.exit(EXIT_NOT_FOUND)

    store = ProgramStore(db_path)

    count = store.count(experiment)
    if count == 0:
        click.echo(f"Experiment not found: {experiment}", err=True)
        sys.exit(EXIT_NOT_FOUND)

    click.echo(f"Resume functionality: would resume {experiment}")
    if iterations:
        click.echo(f"  Additional iterations: {iterations}")
    click.echo("Note: Resume requires controller state persistence (not yet implemented)")


def _list_experiments(store: ProgramStore, as_json: bool) -> None:
    """List all experiments in the store."""
    import sqlite3

    # Query distinct experiments
    with sqlite3.connect(store.db_path) as conn:
        cursor = conn.execute(
            """
            SELECT experiment, COUNT(*), MAX(calmar), MIN(created_at)
            FROM programs
            WHERE experiment IS NOT NULL
            GROUP BY experiment
            ORDER BY MIN(created_at) DESC
            """
        )
        experiments = cursor.fetchall()

    if not experiments:
        click.echo("No experiments found")
        return

    if as_json:
        data = []
        for exp_name, count, best_calmar, created_at in experiments:
            data.append(
                {
                    "name": exp_name,
                    "count": count,
                    "best_calmar": best_calmar,
                    "created_at": datetime.fromtimestamp(created_at).isoformat(),
                }
            )
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo("Experiments")
        click.echo("=" * 60)
        click.echo(f"{'Name':<25} {'Count':<8} {'Best':<10} {'Created':<20}")
        click.echo("-" * 60)
        for exp_name, count, best_calmar, created_at in experiments:
            created_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M")
            best_str = f"{best_calmar:.4f}" if best_calmar else "N/A"
            click.echo(f"{exp_name:<25} {count:<8} {best_str:<10} {created_str:<20}")


def main() -> None:
    """Entry point for CLI."""
    evolve()


if __name__ == "__main__":
    main()
