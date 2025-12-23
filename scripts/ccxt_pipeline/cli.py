"""CLI interface for CCXT data pipeline.

Provides commands for fetching Open Interest, Funding Rates, and Liquidations
from multiple cryptocurrency exchanges.
"""

import asyncio
import signal
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from scripts.ccxt_pipeline.config import get_config
from scripts.ccxt_pipeline.fetchers import FetchOrchestrator, get_all_fetchers
from scripts.ccxt_pipeline.models import FundingRate, OpenInterest
from scripts.ccxt_pipeline.storage.parquet_store import ParquetStore
from scripts.ccxt_pipeline.utils.logging import setup_logging

console = Console()

# Global flag for graceful shutdown
_shutdown_requested = False


def _handle_sigint(signum: int, frame: Any) -> None:
    """Handle Ctrl+C for graceful shutdown."""
    global _shutdown_requested
    if _shutdown_requested:
        console.print("\n[red]Force quitting...[/red]")
        sys.exit(1)
    _shutdown_requested = True
    console.print("\n[yellow]Shutdown requested. Finishing current operation...[/yellow]")


def run_async(coro):
    """Run an async coroutine in a sync context with signal handling."""
    # Set up signal handler
    signal.signal(signal.SIGINT, _handle_sigint)

    # Create new event loop to avoid deprecation warning in Python 3.10+
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def parse_datetime(value: str | None) -> datetime | None:
    """Parse a datetime string in various formats."""
    if value is None:
        return None

    # Strip whitespace and treat empty/whitespace-only as None
    value = value.strip()
    if not value:
        return None

    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    raise click.BadParameter(
        f"Cannot parse date: {value}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format."
    )


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(debug: bool) -> None:
    """CCXT Data Pipeline - Multi-exchange derivative data fetcher."""
    level = "DEBUG" if debug else "INFO"
    setup_logging(level)


@cli.command("fetch-oi")
@click.argument("symbol")
@click.option(
    "--exchange",
    "-e",
    multiple=True,
    help="Exchange(s) to fetch from. If not specified, fetches from all.",
)
@click.option(
    "--store",
    is_flag=True,
    help="Store fetched data to Parquet catalog.",
)
@click.option(
    "--from",
    "from_date",
    type=str,
    default=None,
    help="Start date for historical data (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).",
)
@click.option(
    "--to",
    "to_date",
    type=str,
    default=None,
    help="End date for historical data (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).",
)
@click.option(
    "--incremental",
    is_flag=True,
    help="Only fetch data newer than last stored timestamp.",
)
def fetch_oi(
    symbol: str,
    exchange: tuple[str, ...],
    store: bool,
    from_date: str | None,
    to_date: str | None,
    incremental: bool,
) -> None:
    """Fetch Open Interest for a symbol.

    Examples:

        # Current OI from all exchanges
        ccxt-cli fetch-oi BTCUSDT-PERP

        # Current OI from specific exchanges
        ccxt-cli fetch-oi BTCUSDT-PERP --exchange binance --exchange bybit

        # Store to Parquet
        ccxt-cli fetch-oi BTCUSDT-PERP --store

        # Historical OI for a date range
        ccxt-cli fetch-oi BTCUSDT-PERP --from 2025-01-01 --to 2025-01-31 --store

        # Incremental update (only new data)
        ccxt-cli fetch-oi BTCUSDT-PERP --store --incremental
    """
    global _shutdown_requested
    _shutdown_requested = False

    start = parse_datetime(from_date)
    end = parse_datetime(to_date)

    # If only start is given, use now as end
    if start and not end:
        end = datetime.now(timezone.utc)

    is_historical = start is not None

    async def _fetch():
        global _shutdown_requested
        config = get_config()
        exchanges = list(exchange) if exchange else None
        fetchers = get_all_fetchers(exchanges)
        orchestrator = FetchOrchestrator(fetchers)
        parquet_store = ParquetStore(config.catalog_path) if store else None

        try:
            if is_historical:
                console.print(
                    f"[bold]Fetching Historical OI for {symbol}[/bold] "
                    f"from {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}"
                )

                # Handle incremental mode - use minimum of all venue timestamps
                # to avoid skipping data for venues with older data
                actual_start = start
                if incremental and parquet_store:
                    venue_list = exchanges or ["BINANCE", "BYBIT", "HYPERLIQUID"]
                    last_timestamps = []
                    for venue in venue_list:
                        last_ts = parquet_store.get_last_timestamp(
                            OpenInterest, symbol.upper(), venue.upper()
                        )
                        if last_ts:
                            last_timestamps.append(last_ts)
                            console.print(f"[dim]Incremental: {venue} last data at {last_ts}[/dim]")
                    # Use minimum timestamp to ensure no data is skipped
                    if last_timestamps:
                        min_last_ts = min(last_timestamps)
                        if min_last_ts > start:
                            actual_start = min_last_ts + timedelta(milliseconds=1)
                            console.print(
                                f"[dim]Starting from {actual_start} (earliest needed)[/dim]"
                            )

                results = await orchestrator.fetch_open_interest_history(
                    symbol, actual_start, end, exchanges
                )

                # Collect all data
                all_oi_data = []
                for result in results:
                    if _shutdown_requested:
                        console.print("[yellow]Saving partial data before shutdown...[/yellow]")
                        break

                    if result.success and result.data:
                        if isinstance(result.data, list):
                            all_oi_data.extend(result.data)
                            console.print(
                                f"[green]{result.venue}[/green]: {len(result.data)} records"
                            )
                        else:
                            all_oi_data.append(result.data)
                    else:
                        error_msg = str(result.error)[:50] if result.error else "Unknown"
                        console.print(f"[red]{result.venue}[/red]: Error - {error_msg}")

                console.print(f"\n[bold]Total records:[/bold] {len(all_oi_data)}")

                # Store if requested
                if store and all_oi_data:
                    parquet_store.write(all_oi_data)
                    console.print(
                        f"[green]Stored {len(all_oi_data)} records to {config.catalog_path}[/green]"
                    )
            else:
                # Current OI fetch
                console.print(f"[bold]Fetching Current OI for {symbol}...[/bold]")

                results = await orchestrator.fetch_open_interest(symbol, exchanges)

                # Display results
                table = Table(title=f"Open Interest: {symbol}")
                table.add_column("Exchange", style="cyan")
                table.add_column("Open Interest", justify="right", style="green")
                table.add_column("Value (USD)", justify="right", style="yellow")
                table.add_column("Timestamp", style="dim")

                oi_data = []
                for result in results:
                    if result.success and result.data:
                        oi = result.data
                        oi_data.append(oi)
                        table.add_row(
                            result.venue,
                            f"{oi.open_interest:,.2f}",
                            f"${oi.open_interest_value:,.0f}",
                            oi.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        )
                    else:
                        error_msg = str(result.error) if result.error else "Unknown error"
                        table.add_row(
                            result.venue,
                            "[red]ERROR[/red]",
                            f"[red]{error_msg[:30]}...[/red]",
                            "-",
                        )

                console.print(table)

                # Store if requested
                if store and oi_data:
                    parquet_store.write(oi_data)
                    console.print(
                        f"[green]Stored {len(oi_data)} records to {config.catalog_path}[/green]"
                    )

        finally:
            await orchestrator.close_all()

    run_async(_fetch())


@cli.command("fetch-funding")
@click.argument("symbol")
@click.option(
    "--exchange",
    "-e",
    multiple=True,
    help="Exchange(s) to fetch from.",
)
@click.option(
    "--store",
    is_flag=True,
    help="Store fetched data to Parquet catalog.",
)
@click.option(
    "--from",
    "from_date",
    type=str,
    default=None,
    help="Start date for historical data (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).",
)
@click.option(
    "--to",
    "to_date",
    type=str,
    default=None,
    help="End date for historical data (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).",
)
@click.option(
    "--incremental",
    is_flag=True,
    help="Only fetch data newer than last stored timestamp.",
)
def fetch_funding(
    symbol: str,
    exchange: tuple[str, ...],
    store: bool,
    from_date: str | None,
    to_date: str | None,
    incremental: bool,
) -> None:
    """Fetch Funding Rate for a symbol.

    Examples:

        # Current funding rate from all exchanges
        ccxt-cli fetch-funding BTCUSDT-PERP

        # Current funding from specific exchange
        ccxt-cli fetch-funding BTCUSDT-PERP --exchange binance

        # Historical funding rates
        ccxt-cli fetch-funding BTCUSDT-PERP --from 2025-01-01 --to 2025-01-31 --store

        # Incremental update
        ccxt-cli fetch-funding BTCUSDT-PERP --store --incremental
    """
    global _shutdown_requested
    _shutdown_requested = False

    start = parse_datetime(from_date)
    end = parse_datetime(to_date)

    if start and not end:
        end = datetime.now(timezone.utc)

    is_historical = start is not None

    async def _fetch():
        global _shutdown_requested
        config = get_config()
        exchanges = list(exchange) if exchange else None
        fetchers = get_all_fetchers(exchanges)
        orchestrator = FetchOrchestrator(fetchers)
        parquet_store = ParquetStore(config.catalog_path) if store else None

        try:
            if is_historical:
                console.print(
                    f"[bold]Fetching Historical Funding Rates for {symbol}[/bold] "
                    f"from {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}"
                )

                # Handle incremental mode - use minimum of all venue timestamps
                # to avoid skipping data for venues with older data
                actual_start = start
                if incremental and parquet_store:
                    venue_list = exchanges or ["BINANCE", "BYBIT", "HYPERLIQUID"]
                    last_timestamps = []
                    for venue in venue_list:
                        last_ts = parquet_store.get_last_timestamp(
                            FundingRate, symbol.upper(), venue.upper()
                        )
                        if last_ts:
                            last_timestamps.append(last_ts)
                            console.print(f"[dim]Incremental: {venue} last data at {last_ts}[/dim]")
                    # Use minimum timestamp to ensure no data is skipped
                    if last_timestamps:
                        min_last_ts = min(last_timestamps)
                        if min_last_ts > start:
                            actual_start = min_last_ts + timedelta(milliseconds=1)
                            console.print(
                                f"[dim]Starting from {actual_start} (earliest needed)[/dim]"
                            )

                results = await orchestrator.fetch_funding_rate_history(
                    symbol, actual_start, end, exchanges
                )

                all_funding_data = []
                for result in results:
                    if _shutdown_requested:
                        console.print("[yellow]Saving partial data before shutdown...[/yellow]")
                        break

                    if result.success and result.data:
                        if isinstance(result.data, list):
                            all_funding_data.extend(result.data)
                            console.print(
                                f"[green]{result.venue}[/green]: {len(result.data)} records"
                            )
                        else:
                            all_funding_data.append(result.data)
                    else:
                        error_msg = str(result.error)[:50] if result.error else "Unknown"
                        console.print(f"[red]{result.venue}[/red]: Error - {error_msg}")

                console.print(f"\n[bold]Total records:[/bold] {len(all_funding_data)}")

                if store and all_funding_data:
                    parquet_store.write(all_funding_data)
                    console.print(
                        f"[green]Stored {len(all_funding_data)} records to {config.catalog_path}[/green]"
                    )
            else:
                console.print(f"[bold]Fetching Funding Rate for {symbol}...[/bold]")

                results = await orchestrator.fetch_funding_rate(symbol, exchanges)

                # Display results
                table = Table(title=f"Funding Rate: {symbol}")
                table.add_column("Exchange", style="cyan")
                table.add_column("Funding Rate", justify="right", style="green")
                table.add_column("Next Funding", style="yellow")
                table.add_column("Timestamp", style="dim")

                funding_data = []
                for result in results:
                    if result.success and result.data:
                        fr = result.data
                        funding_data.append(fr)
                        rate_pct = fr.funding_rate * 100
                        color = "green" if fr.funding_rate >= 0 else "red"
                        next_time = (
                            fr.next_funding_time.strftime("%H:%M:%S")
                            if fr.next_funding_time
                            else "-"
                        )
                        table.add_row(
                            result.venue,
                            f"[{color}]{rate_pct:+.4f}%[/{color}]",
                            next_time,
                            fr.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        )
                    else:
                        error_msg = str(result.error) if result.error else "Unknown error"
                        table.add_row(
                            result.venue,
                            "[red]ERROR[/red]",
                            f"[red]{error_msg[:20]}...[/red]",
                            "-",
                        )

                console.print(table)

                if store and funding_data:
                    parquet_store.write(funding_data)
                    console.print(
                        f"[green]Stored {len(funding_data)} records to {config.catalog_path}[/green]"
                    )

        finally:
            await orchestrator.close_all()

    run_async(_fetch())


@cli.command("stream-liquidations")
@click.argument("symbol")
@click.option(
    "--exchange",
    "-e",
    multiple=True,
    help="Exchange(s) to stream from.",
)
@click.option(
    "--store",
    is_flag=True,
    help="Store liquidations to Parquet catalog.",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress output (store only mode).",
)
def stream_liquidations(symbol: str, exchange: tuple[str, ...], store: bool, quiet: bool) -> None:
    """Stream real-time liquidation events.

    Streams liquidations from WebSocket connections with automatic reconnection.
    Use Ctrl+C to stop streaming gracefully.

    Examples:

        # Stream from all exchanges
        ccxt-cli stream-liquidations BTCUSDT-PERP

        # Stream from specific exchanges
        ccxt-cli stream-liquidations BTCUSDT-PERP -e binance -e bybit

        # Stream and store to Parquet
        ccxt-cli stream-liquidations BTCUSDT-PERP --store

        # Store only (quiet mode)
        ccxt-cli stream-liquidations BTCUSDT-PERP --store --quiet
    """
    global _shutdown_requested
    _shutdown_requested = False

    from scripts.ccxt_pipeline.models import Liquidation

    async def _stream():
        global _shutdown_requested
        config = get_config()
        exchanges = list(exchange) if exchange else None
        fetchers = get_all_fetchers(exchanges)
        orchestrator = FetchOrchestrator(fetchers)
        parquet_store = ParquetStore(config.catalog_path) if store else None

        # Buffer for batch writing
        liquidation_buffer: list[Liquidation] = []
        BUFFER_SIZE = 100  # Write to disk every N liquidations

        def on_liquidation(liq: Liquidation) -> None:
            """Callback for each liquidation event."""
            if not quiet:
                side_color = "red" if liq.side.value == "LONG" else "green"
                console.print(
                    f"[dim]{liq.timestamp.strftime('%H:%M:%S')}[/dim] "
                    f"[cyan]{liq.venue.value}[/cyan] {liq.symbol} "
                    f"[{side_color}]{liq.side.value}[/{side_color}] liquidated: "
                    f"{liq.quantity:.4f} @ ${liq.price:,.2f} "
                    f"([yellow]${liq.value:,.2f}[/yellow])"
                )

            if store:
                liquidation_buffer.append(liq)
                if len(liquidation_buffer) >= BUFFER_SIZE:
                    parquet_store.write(liquidation_buffer)
                    liquidation_buffer.clear()

        try:
            console.print(
                f"[bold]Streaming Liquidations for {symbol}[/bold] (Press Ctrl+C to stop)"
            )

            # Start streaming from all fetchers concurrently
            await orchestrator.stream_liquidations(symbol, on_liquidation, exchanges)

        except asyncio.CancelledError:
            console.print("[yellow]Stream cancelled[/yellow]")

        except KeyboardInterrupt:
            console.print("[yellow]Interrupted by user[/yellow]")

        finally:
            # Flush remaining buffer
            if store and liquidation_buffer:
                parquet_store.write(liquidation_buffer)
                console.print(
                    f"[green]Flushed {len(liquidation_buffer)} remaining liquidations[/green]"
                )

            await orchestrator.close_all()

    run_async(_stream())


@cli.group()
def daemon() -> None:
    """Daemon mode for continuous data collection."""
    pass


@daemon.command("start")
@click.option(
    "--symbol",
    "-s",
    multiple=True,
    default=["BTCUSDT-PERP", "ETHUSDT-PERP"],
    help="Trading symbol(s) to fetch.",
)
@click.option(
    "--exchange",
    "-e",
    multiple=True,
    help="Exchange(s) to fetch from. If not specified, uses all.",
)
@click.option(
    "--oi-interval",
    default=5,
    help="Open Interest fetch interval in minutes.",
)
@click.option(
    "--funding-interval",
    default=60,
    help="Funding rate fetch interval in minutes.",
)
def daemon_start(
    symbol: tuple[str, ...],
    exchange: tuple[str, ...],
    oi_interval: int,
    funding_interval: int,
) -> None:
    """Start the daemon for continuous data collection.

    Runs 24/7, fetching OI and funding at scheduled intervals,
    and streaming liquidations in real-time.

    Examples:

        # Start with defaults (BTC/ETH, all exchanges)
        ccxt-cli daemon start

        # Custom symbols and exchanges
        ccxt-cli daemon start -s BTCUSDT-PERP -s SOLUSDT-PERP -e binance -e bybit

        # Custom fetch intervals
        ccxt-cli daemon start --oi-interval 1 --funding-interval 30
    """
    global _shutdown_requested
    _shutdown_requested = False

    from scripts.ccxt_pipeline.scheduler.daemon import DaemonRunner

    async def _run_daemon():
        global _shutdown_requested

        runner = DaemonRunner(
            symbols=list(symbol),
            exchanges=list(exchange) if exchange else None,
            oi_interval_minutes=oi_interval,
            funding_interval_minutes=funding_interval,
        )

        console.print("[bold]Starting CCXT Pipeline Daemon[/bold]")
        console.print(f"  Symbols: {', '.join(symbol)}")
        console.print(f"  Exchanges: {', '.join(exchange) if exchange else 'all'}")
        console.print(f"  OI interval: {oi_interval} minutes")
        console.print(f"  Funding interval: {funding_interval} minutes")
        console.print("\n[dim]Press Ctrl+C to stop[/dim]\n")

        try:
            await runner.start()

            # Run until shutdown requested
            while not _shutdown_requested:
                await asyncio.sleep(1)

                # Periodically print status
                status = runner.get_status()
                if status["fetch_count"] > 0 and status["fetch_count"] % 10 == 0:
                    console.print(
                        f"[dim]Status: {status['fetch_count']} fetches, "
                        f"{status['error_count']} errors, "
                        f"{status['liquidation_count']} liquidations[/dim]"
                    )

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")

        finally:
            console.print("[dim]Shutting down daemon...[/dim]")
            await runner.stop()
            status = runner.get_status()
            console.print(
                f"\n[green]Daemon stopped.[/green] "
                f"Total: {status['fetch_count']} fetches, "
                f"{status['error_count']} errors, "
                f"{status['liquidation_count']} liquidations"
            )

    run_async(_run_daemon())


@daemon.command("status")
def daemon_status() -> None:
    """Show daemon status (if running in background).

    Note: Background daemon mode requires external process management.
    Use 'daemon start' for foreground operation.
    """
    console.print(
        "[yellow]Background daemon status requires external process manager.[/yellow]\n"
        "For foreground operation, use: ccxt-cli daemon start"
    )


@daemon.command("stop")
def daemon_stop() -> None:
    """Stop the running daemon.

    Note: Background daemon mode requires external process management (systemd, supervisor).
    For foreground operation, use Ctrl+C to stop.
    """
    console.print(
        "[yellow]Background daemon stop requires external process manager.[/yellow]\n"
        "For foreground operation, use Ctrl+C to stop the daemon."
    )


@cli.command("query")
@click.argument("data_type", type=click.Choice(["oi", "funding", "liquidations"]))
@click.argument("symbol")
@click.option(
    "--exchange",
    "-e",
    help="Filter by exchange (e.g., binance, bybit).",
)
@click.option(
    "--from",
    "start_date",
    help="Start date (YYYY-MM-DD).",
)
@click.option(
    "--to",
    "end_date",
    help="End date (YYYY-MM-DD).",
)
@click.option(
    "--limit",
    "-n",
    default=10,
    help="Number of records to display (default: 10).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format.",
)
def query_data(
    data_type: str,
    symbol: str,
    exchange: str | None,
    start_date: str | None,
    end_date: str | None,
    limit: int,
    output_format: str,
) -> None:
    """Query stored data from the Parquet catalog.

    DATA_TYPE: Type of data to query (oi, funding, liquidations)
    SYMBOL: Trading pair symbol (e.g., BTCUSDT-PERP)

    Examples:

        # Query recent OI data
        ccxt-cli query oi BTCUSDT-PERP

        # Query funding rates from specific exchange
        ccxt-cli query funding BTCUSDT-PERP -e binance

        # Query with date range
        ccxt-cli query oi BTCUSDT-PERP --from 2025-01-01 --to 2025-01-31

        # Output as JSON
        ccxt-cli query liquidations BTCUSDT-PERP --format json -n 100
    """
    import json

    from scripts.ccxt_pipeline.models import Liquidation

    config = get_config()
    store = ParquetStore(config.catalog_path)

    # Map data type to model class
    model_map = {
        "oi": OpenInterest,
        "funding": FundingRate,
        "liquidations": Liquidation,
    }
    model_class = model_map[data_type]

    # Query data
    venue = exchange.upper() if exchange else None
    records = store.read(model_class, symbol.upper(), venue)

    if not records:
        console.print(f"[yellow]No data found for {symbol}[/yellow]")
        return

    # Filter by date range if specified
    if start_date:
        start_dt = parse_datetime(start_date)
        if start_dt:
            records = [r for r in records if r["timestamp"] >= start_dt]

    if end_date:
        end_dt = parse_datetime(end_date)
        if end_dt:
            records = [r for r in records if r["timestamp"] <= end_dt]

    # Sort by timestamp descending (most recent first)
    records = sorted(records, key=lambda x: x["timestamp"], reverse=True)

    # Limit records
    records = records[:limit]

    if not records:
        console.print("[yellow]No data found for the specified criteria[/yellow]")
        return

    # Output based on format
    if output_format == "json":
        console.print(json.dumps(records, indent=2, default=str))

    elif output_format == "csv":
        if records:
            # Print header
            console.print(",".join(records[0].keys()))
            # Print rows
            for record in records:
                console.print(",".join(str(v) for v in record.values()))

    else:  # table format
        table = Table(title=f"{data_type.upper()} Data for {symbol}")

        # Add columns based on data type
        if data_type == "oi":
            table.add_column("Timestamp", style="dim")
            table.add_column("Exchange", style="cyan")
            table.add_column("OI", justify="right")
            table.add_column("OI Value", justify="right", style="green")

            for r in records:
                table.add_row(
                    r["timestamp"][:19]
                    if isinstance(r["timestamp"], str)
                    else str(r["timestamp"])[:19],
                    r["venue"],
                    f"{r['open_interest']:,.2f}",
                    f"${r['open_interest_value']:,.0f}",
                )

        elif data_type == "funding":
            table.add_column("Timestamp", style="dim")
            table.add_column("Exchange", style="cyan")
            table.add_column("Rate", justify="right")
            table.add_column("Annualized", justify="right", style="green")

            for r in records:
                rate = r["funding_rate"]
                annualized = rate * 3 * 365 * 100  # 8h funding * 3 * 365 days
                table.add_row(
                    r["timestamp"][:19]
                    if isinstance(r["timestamp"], str)
                    else str(r["timestamp"])[:19],
                    r["venue"],
                    f"{rate:.6f}",
                    f"{annualized:.2f}%",
                )

        else:  # liquidations
            table.add_column("Timestamp", style="dim")
            table.add_column("Exchange", style="cyan")
            table.add_column("Side", justify="center")
            table.add_column("Quantity", justify="right")
            table.add_column("Price", justify="right")
            table.add_column("Value", justify="right", style="yellow")

            for r in records:
                side_color = "red" if r["side"] == "LONG" else "green"
                table.add_row(
                    r["timestamp"][:19]
                    if isinstance(r["timestamp"], str)
                    else str(r["timestamp"])[:19],
                    r["venue"],
                    f"[{side_color}]{r['side']}[/{side_color}]",
                    f"{r['quantity']:.4f}",
                    f"${r['price']:,.2f}",
                    f"${r['value']:,.2f}",
                )

        console.print(table)
        console.print(f"\n[dim]Showing {len(records)} of {len(records)} records[/dim]")


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
