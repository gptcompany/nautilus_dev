"""CLI for Binance to NautilusTrader data conversion.

Provides commands for converting, updating, validating, and checking status
of data conversion between Binance CSV and NautilusTrader ParquetDataCatalog.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import cast

import click
from tqdm import tqdm

from .catalog import CatalogWriter
from .config import ConverterConfig
from .converters.aggtrades import AggTradesConverter, get_aggtrades_date_range
from .converters.base import BaseConverter
from .converters.funding import FundingRateConverter
from .converters.klines import KlinesConverter
from .converters.trades import TradesConverter
from .instruments import get_instrument, list_supported_symbols
from .state import load_state, save_state
from .validate import validate_catalog


@click.group()
@click.option(
    "--source-dir",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Source CSV directory (default: from config)",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output catalog path (default: from config)",
)
@click.pass_context
def cli(ctx: click.Context, source_dir: Path | None, output_dir: Path | None) -> None:
    """Binance to NautilusTrader v1.222.0 Data Converter.

    Convert Binance historical CSV data to NautilusTrader ParquetDataCatalog format.
    """
    config = ConverterConfig()
    if source_dir:
        config = ConverterConfig(source_dir=source_dir, output_dir=config.output_dir)
    if output_dir:
        config = ConverterConfig(source_dir=config.source_dir, output_dir=output_dir)

    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@cli.command()
@click.argument("symbol", type=str)
@click.argument("data_type", type=click.Choice(["klines", "trades", "funding"]))
@click.option("--timeframe", "-t", default="1m", help="Timeframe for klines (1m, 5m, 15m)")
@click.option("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", type=str, default=None, help="End date (YYYY-MM-DD)")
@click.option("--chunk-size", type=int, default=100_000, help="Rows per chunk")
@click.option("--dry-run", is_flag=True, help="Simulate without writing")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def convert(
    ctx: click.Context,
    symbol: str,
    data_type: str,
    timeframe: str,
    start_date: str | None,
    end_date: str | None,
    chunk_size: int,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Convert Binance CSV data to NautilusTrader catalog.

    SYMBOL: Trading symbol (e.g., BTCUSDT, ETHUSDT)
    DATA_TYPE: Data type to convert (klines, trades, funding)
    """
    config: ConverterConfig = ctx.obj["config"]
    config = ConverterConfig(
        source_dir=config.source_dir,
        output_dir=config.output_dir,
        chunk_size=chunk_size,
    )

    # Validate symbol
    if symbol not in list_supported_symbols():
        click.echo(f"Error: Unsupported symbol: {symbol}", err=True)
        click.echo(f"Supported symbols: {', '.join(list_supported_symbols())}", err=True)
        sys.exit(2)

    # Load state
    state = load_state(config.output_dir)

    if verbose:
        click.echo(f"Source: {config.source_dir}")
        click.echo(f"Output: {config.output_dir}")
        click.echo(f"Symbol: {symbol}")
        click.echo(f"Data type: {data_type}")

    if data_type == "klines":
        _convert_klines(config, state, symbol, timeframe, dry_run, verbose)
    elif data_type == "trades":
        _convert_trades(config, state, symbol, dry_run, verbose)
    elif data_type == "funding":
        _convert_funding(config, state, symbol, dry_run, verbose)

    # Save state
    if not dry_run:
        save_state(state, config.output_dir)


def _convert_klines(
    config: ConverterConfig,
    state,
    symbol: str,
    timeframe: str,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Convert klines data."""
    converter = KlinesConverter(
        symbol=symbol,
        timeframe=timeframe,
        config=config,
        state=state,
    )

    # Discover files
    files = converter.get_pending_files()
    if not files:
        click.echo("No new files to process")
        return

    click.echo(f"Found {len(files)} files to process")

    if dry_run:
        for f in files[:10]:
            click.echo(f"  Would process: {f.name}")
        if len(files) > 10:
            click.echo(f"  ... and {len(files) - 10} more")
        return

    # Initialize catalog and write instrument
    catalog = CatalogWriter(config.output_dir)
    instrument = get_instrument(symbol)
    catalog.write_instrument(instrument)

    # Process files with progress bar
    total_bars = 0
    with tqdm(files, desc=f"Converting {symbol} {timeframe}", unit="file") as pbar:
        for file_path in pbar:
            bars = converter.process_file(file_path)
            if bars:
                catalog.write_bars(bars)
                total_bars += len(bars)
                converter.mark_processed(
                    file_path=file_path,
                    record_count=len(bars),
                    first_ts=bars[0].ts_event,
                    last_ts=bars[-1].ts_event,
                )
            pbar.set_postfix(bars=total_bars)

    click.echo(f"Converted {total_bars:,} bars from {len(files)} files")


def _convert_trades(
    config: ConverterConfig,
    state,
    symbol: str,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Convert trades data with chunked processing."""
    converter = TradesConverter(
        symbol=symbol,
        config=config,
        state=state,
    )

    # Discover files
    files = converter.get_pending_files()
    if not files:
        click.echo("No new files to process")
        return

    click.echo(f"Found {len(files)} files to process")

    if dry_run:
        for f in files[:10]:
            click.echo(f"  Would process: {f.name}")
        if len(files) > 10:
            click.echo(f"  ... and {len(files) - 10} more")
        return

    # Initialize catalog and write instrument
    catalog = CatalogWriter(config.output_dir)
    instrument = get_instrument(symbol)
    catalog.write_instrument(instrument)

    # Process files with chunked processing
    total_ticks = 0
    with tqdm(files, desc=f"Converting {symbol} trades", unit="file") as pbar:
        for file_path in pbar:
            file_ticks = 0
            first_ts = None
            last_ts = None

            # Process in chunks for memory efficiency
            for ticks in converter.process_file_chunked(file_path):
                if ticks:
                    catalog.write_ticks(ticks)
                    file_ticks += len(ticks)
                    if first_ts is None:
                        first_ts = ticks[0].ts_event
                    last_ts = ticks[-1].ts_event

            if file_ticks > 0 and first_ts and last_ts:
                converter.mark_processed(
                    file_path=file_path,
                    record_count=file_ticks,
                    first_ts=first_ts,
                    last_ts=last_ts,
                )
            total_ticks += file_ticks
            pbar.set_postfix(ticks=f"{total_ticks:,}")

    click.echo(f"Converted {total_ticks:,} trade ticks from {len(files)} files")


def _convert_funding(
    config: ConverterConfig,
    state,
    symbol: str,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Convert funding rate data."""
    converter = FundingRateConverter(
        symbol=symbol,
        config=config,
        state=state,
    )

    # Discover files
    files = converter.get_pending_files()
    if not files:
        click.echo("No new files to process")
        return

    click.echo(f"Found {len(files)} files to process")

    if dry_run:
        for f in files[:10]:
            click.echo(f"  Would process: {f.name}")
        if len(files) > 10:
            click.echo(f"  ... and {len(files) - 10} more")
        return

    # Initialize catalog and write instrument
    catalog = CatalogWriter(config.output_dir)
    instrument = get_instrument(symbol)
    catalog.write_instrument(instrument)

    # Process files with progress bar
    total_rates = 0
    with tqdm(files, desc=f"Converting {symbol} funding", unit="file") as pbar:
        for file_path in pbar:
            rates = converter.process_file(file_path)
            if rates:
                catalog.write_funding_rates(rates)
                total_rates += len(rates)
                converter.mark_processed(
                    file_path=file_path,
                    record_count=len(rates),
                    first_ts=rates[0].ts_event,
                    last_ts=rates[-1].ts_event,
                )
            pbar.set_postfix(rates=total_rates)

    click.echo(f"Converted {total_rates:,} funding rates from {len(files)} files")


@cli.command()
@click.argument("symbol", type=str, required=False)
@click.option("--force", is_flag=True, help="Reprocess already converted files")
@click.pass_context
def update(ctx: click.Context, symbol: str | None, force: bool) -> None:
    """Incremental update - process only new files since last run.

    SYMBOL: Specific symbol to update, or all if omitted
    """
    config: ConverterConfig = ctx.obj["config"]
    state = load_state(config.output_dir)

    symbols = [symbol] if symbol else list_supported_symbols()

    for sym in symbols:
        click.echo(f"\nUpdating {sym}...")

        # Update klines (all timeframes)
        for tf in config.timeframes:
            converter = KlinesConverter(sym, tf, config, state if not force else None)
            pending = converter.get_pending_files()
            if pending:
                click.echo(f"  {tf}: {len(pending)} new files")
                # Process similar to convert command...

        # Update trades
        converter_trades: BaseConverter = TradesConverter(sym, config, state if not force else None)
        pending = converter_trades.get_pending_files()
        if pending:
            click.echo(f"  trades: {len(pending)} new files")

        # Update funding rates
        converter_funding: BaseConverter = FundingRateConverter(
            sym, config, state if not force else None
        )
        pending = converter_funding.get_pending_files()
        if pending:
            click.echo(f"  funding: {len(pending)} new files")

    save_state(state, config.output_dir)
    click.echo("\nUpdate complete")


@cli.command("validate")
@click.argument("catalog_path", type=click.Path(exists=True, path_type=Path))
@click.option("--quick", is_flag=True, help="Skip full data integrity check")
@click.option("--backtest-test", is_flag=True, help="Run BacktestEngine compatibility test")
@click.option("--json-output", "json_out", is_flag=True, help="Output as JSON")
@click.pass_context
def validate_cmd(
    ctx: click.Context,
    catalog_path: Path,
    quick: bool,
    backtest_test: bool,
    json_out: bool,
) -> None:
    """Validate catalog integrity and BacktestEngine compatibility.

    CATALOG_PATH: Path to NautilusTrader catalog
    """
    result = validate_catalog(
        catalog_path,
        run_backtest_test=backtest_test,
    )

    if json_out:
        output = {
            "is_valid": result.is_valid,
            "catalog_path": result.catalog_path,
            "instruments": result.instruments,
            "bar_counts": result.bar_counts,
            "tick_counts": result.tick_counts,
            "schema_version": result.schema_version,
            "backtest_compatible": result.backtest_compatible,
            "errors": result.errors,
            "warnings": result.warnings,
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo("Catalog Validation Report")
        click.echo("=" * 50)
        click.echo(f"Path: {result.catalog_path}")
        click.echo()
        click.echo(f"Instruments: {len(result.instruments)}")
        for inst in result.instruments:
            click.echo(f"  - {inst}")
        click.echo()
        click.echo("Bars:")
        for bar_type, count in result.bar_counts.items():
            click.echo(f"  - {bar_type}: {count:,}")
        click.echo()
        if result.tick_counts:
            click.echo("Trade Ticks:")
            for inst, count in result.tick_counts.items():
                click.echo(f"  - {inst}: {count:,}")
            click.echo()
        click.echo(f"Schema: {result.schema_version}")
        if result.backtest_compatible is not None:
            status = "COMPATIBLE" if result.backtest_compatible else "INCOMPATIBLE"
            click.echo(f"BacktestEngine: {status}")
        click.echo()
        if result.errors:
            click.echo("Errors:")
            for err in result.errors:
                click.echo(f"  - {err}")
        if result.warnings:
            click.echo("Warnings:")
            for warn in result.warnings:
                click.echo(f"  - {warn}")
        click.echo()
        status = "VALID" if result.is_valid else "INVALID"
        click.echo(f"Status: {status}")

    sys.exit(0 if result.is_valid else 5)


@cli.command()
@click.option("--json-output", "json_out", is_flag=True, help="Output as JSON")
@click.pass_context
def status(ctx: click.Context, json_out: bool) -> None:
    """Show conversion progress and catalog statistics."""
    config: ConverterConfig = ctx.obj["config"]
    state = load_state(config.output_dir)

    if json_out:
        output: dict = {
            "source_dir": str(config.source_dir),
            "catalog_path": str(config.output_dir),
            "symbols": {},
        }
        for symbol, data_types in state.symbols.items():
            output["symbols"][symbol] = {}
            data_types_dict: dict = cast(dict, data_types)
            for data_type, sym_state in data_types_dict.items():
                output["symbols"][symbol][data_type] = {
                    "files_processed": len(sym_state.files),
                    "total_records": sym_state.total_records,
                    "last_updated": sym_state.last_updated,
                }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo("Conversion Status")
        click.echo("=" * 50)
        click.echo(f"Source: {config.source_dir}")
        click.echo(f"Catalog: {config.output_dir}")
        click.echo()

        if not state.symbols:
            click.echo("No conversions recorded yet.")
            return

        for symbol, data_types in state.symbols.items():
            click.echo(f"{symbol}:")
            for data_type, sym_state in data_types.items():
                files = len(sym_state.files)
                records = sym_state.total_records
                click.echo(f"  {data_type}: {files} files, {records:,} records")
            click.echo()

        if state.updated_at:
            click.echo(f"Last update: {state.updated_at}")


@cli.command()
@click.argument("symbol", type=str)
@click.option("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", type=str, default=None, help="End date (YYYY-MM-DD)")
@click.option("--chunk-size", type=int, default=50_000, help="Rows per chunk (default 50k)")
@click.option("--dry-run", is_flag=True, help="Simulate without writing")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def aggtrades(
    ctx: click.Context,
    symbol: str,
    start_date: str | None,
    end_date: str | None,
    chunk_size: int,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Convert Binance aggTrades CSV to NautilusTrader catalog.

    Memory-optimized conversion for large datasets (100GB+).
    Use --start-date and --end-date to convert subsets.

    SYMBOL: Trading symbol (e.g., BTCUSDT, ETHUSDT)

    Examples:
        # Convert last 6 months
        python -m strategies.binance2nautilus.cli aggtrades BTCUSDT --start-date 2025-07-01

        # Convert specific range
        python -m strategies.binance2nautilus.cli aggtrades BTCUSDT --start-date 2025-01-01 --end-date 2025-06-30
    """
    config: ConverterConfig = ctx.obj["config"]

    # Validate symbol
    if symbol not in list_supported_symbols():
        click.echo(f"Error: Unsupported symbol: {symbol}", err=True)
        click.echo(f"Supported symbols: {', '.join(list_supported_symbols())}", err=True)
        sys.exit(2)

    # Parse dates
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

    # Show date range info
    min_date, max_date = get_aggtrades_date_range(symbol, config.source_dir)
    if min_date and max_date:
        click.echo(f"Available data: {min_date.date()} to {max_date.date()}")
    if start_dt or end_dt:
        click.echo(
            f"Converting: {start_dt.date() if start_dt else 'start'} to {end_dt.date() if end_dt else 'end'}"
        )

    # Load state
    state = load_state(config.output_dir)

    if verbose:
        click.echo(f"Source: {config.source_dir}")
        click.echo(f"Output: {config.output_dir}")
        click.echo(f"Symbol: {symbol}")
        click.echo(f"Chunk size: {chunk_size:,}")

    # Initialize converter
    converter = AggTradesConverter(
        symbol=symbol,
        config=config,
        state=state,
        start_date=start_dt,
        end_date=end_dt,
        chunk_size=chunk_size,
    )

    # Discover files
    files = converter.get_pending_files()
    if not files:
        click.echo("No new files to process")
        return

    click.echo(f"Found {len(files)} files to process")

    if dry_run:
        for f in files[:10]:
            click.echo(f"  Would process: {f.name}")
        if len(files) > 10:
            click.echo(f"  ... and {len(files) - 10} more")
        return

    # Initialize catalog and write instrument
    catalog = CatalogWriter(config.output_dir)
    instrument = get_instrument(symbol)
    catalog.write_instrument(instrument)

    # Process files - collect all ticks per file before writing to avoid interval overlap
    total_ticks = 0
    with tqdm(files, desc=f"Converting {symbol} aggTrades", unit="file") as pbar:
        for file_path in pbar:
            file_ticks_list = []
            first_ts = None
            last_ts = None

            # Collect all ticks from this file (chunked reading, but accumulate before write)
            for ticks in converter.process_file_chunked(file_path):
                if ticks:
                    file_ticks_list.extend(ticks)
                    if first_ts is None:
                        first_ts = ticks[0].ts_event
                    last_ts = ticks[-1].ts_event

            # Write all ticks from this file at once to avoid interval overlap
            if file_ticks_list:
                catalog.write_ticks(file_ticks_list)
                converter.mark_processed(
                    file_path=file_path,
                    record_count=len(file_ticks_list),
                    first_ts=cast(int, first_ts),
                    last_ts=cast(int, last_ts),
                )
                total_ticks += len(file_ticks_list)
                # Explicit cleanup
                del file_ticks_list

            pbar.set_postfix(ticks=f"{total_ticks:,}")

    # Save state
    save_state(state, config.output_dir)

    click.echo(f"Converted {total_ticks:,} trade ticks from {len(files)} files")


def main() -> None:
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
