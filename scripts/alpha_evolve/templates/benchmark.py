"""
Performance Benchmark for Alpha-Evolve Equity Tracking.

Measures the overhead of equity tracking in BaseEvolveStrategy.
Target: < 5% overhead compared to vanilla strategy.

Usage:
    python -m scripts.alpha_evolve.templates.benchmark

    # Or with custom parameters:
    python -m scripts.alpha_evolve.templates.benchmark --bars 50000 --runs 3
"""

from __future__ import annotations

import argparse
import statistics
import time
from decimal import Decimal
from typing import TYPE_CHECKING

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.indicators import ExponentialMovingAverage
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType, OmsType, OrderSide, TimeInForce
from nautilus_trader.model.identifiers import TraderId, Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.trading.strategy import Strategy

from scripts.alpha_evolve.templates.base import BaseEvolveConfig
from scripts.alpha_evolve.templates.momentum import (
    MomentumEvolveConfig,
    MomentumEvolveStrategy,
)

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar


# =============================================================================
# Vanilla Strategy (No Equity Tracking)
# =============================================================================


class VanillaMomentumConfig(BaseEvolveConfig, frozen=True):
    """Configuration for vanilla momentum strategy (no equity tracking)."""

    fast_period: int = 10
    slow_period: int = 30


class VanillaMomentumStrategy(Strategy):
    """
    Momentum strategy WITHOUT equity tracking.

    Used as baseline for performance comparison.
    Same logic as MomentumEvolveStrategy but no equity curve recording.
    """

    def __init__(self, config: VanillaMomentumConfig) -> None:
        """Initialize vanilla momentum strategy."""
        super().__init__(config)
        self.instrument = None
        self.fast_ema = ExponentialMovingAverage(config.fast_period)
        self.slow_ema = ExponentialMovingAverage(config.slow_period)

    def on_start(self) -> None:
        """Initialize strategy on start."""
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"Instrument not found: {self.config.instrument_id}")
            self.stop()
            return

        self.subscribe_bars(self.config.bar_type)
        self.register_indicator_for_bars(self.config.bar_type, self.fast_ema)
        self.register_indicator_for_bars(self.config.bar_type, self.slow_ema)

    def on_bar(self, bar: "Bar") -> None:
        """Handle bar - NO equity tracking."""
        if not self.indicators_initialized():
            return

        # Same logic as MomentumEvolveStrategy
        if self.fast_ema.value > self.slow_ema.value:
            if self.portfolio.is_flat(self.config.instrument_id):
                self._enter_long()

        elif self.fast_ema.value < self.slow_ema.value:
            if self.portfolio.is_net_long(self.config.instrument_id):
                self.close_all_positions(self.config.instrument_id)

    def _enter_long(self) -> None:
        """Submit market buy order."""
        if self.instrument is None:
            return

        order = self.order_factory.market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.config.trade_size),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)

    def on_stop(self) -> None:
        """Cleanup on strategy stop."""
        self.cancel_all_orders(self.config.instrument_id)
        self.close_all_positions(self.config.instrument_id)


# =============================================================================
# Benchmark Infrastructure
# =============================================================================


def create_engine() -> BacktestEngine:
    """Create a fresh backtest engine with test data."""
    config = BacktestEngineConfig(
        trader_id=TraderId("BENCHMARK-001"),
        logging=LoggingConfig(log_level="ERROR"),  # Minimize logging overhead
    )

    engine = BacktestEngine(config=config)

    # Add venue
    venue = Venue("BINANCE")
    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT,
        starting_balances=[Money(100_000, USDT)],
    )

    # Add instrument
    instrument = TestInstrumentProvider.btcusdt_binance()
    engine.add_instrument(instrument)

    return engine


def generate_bars(engine: BacktestEngine, num_bars: int) -> None:
    """Generate synthetic bar data for benchmark."""
    from nautilus_trader.test_kit.providers import TestDataProvider

    instrument = TestInstrumentProvider.btcusdt_binance()
    bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")

    # Get bars from test data provider
    provider = TestDataProvider()
    bars = None
    if num_bars > 10000:
        try:
            bars = provider.read_csv_bars("tests/test_data/binance/btcusdt-1min-2024.csv")
        except (FileNotFoundError, OSError) as e:
            print(f"  Warning: Could not read CSV bars: {e}")
            print("  Falling back to synthetic bar generation...")

    if bars is None:
        # Generate synthetic bars if no CSV available
        from datetime import datetime, timedelta

        from nautilus_trader.model.data import Bar

        bars = []
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        price = 50000.0

        for i in range(num_bars):
            # Simple random walk
            price += (i % 7 - 3) * 10  # Deterministic "random" walk
            ts = start_time + timedelta(minutes=i)
            ts_ns = int(ts.timestamp() * 1_000_000_000)

            # Use instrument's precision for price and quantity
            bar = Bar(
                bar_type=bar_type,
                open=instrument.make_price(price),
                high=instrument.make_price(price + 50),
                low=instrument.make_price(price - 50),
                close=instrument.make_price(price + 10),
                volume=instrument.make_qty(100.0),
                ts_event=ts_ns,
                ts_init=ts_ns,
            )
            bars.append(bar)

    engine.add_data(bars[:num_bars])


def run_benchmark_with_equity(num_bars: int) -> tuple[float, int]:
    """
    Run backtest with equity tracking.

    Returns:
        Tuple of (execution_time_seconds, equity_points_recorded)
    """
    engine = create_engine()
    try:
        generate_bars(engine, num_bars)

        instrument = TestInstrumentProvider.btcusdt_binance()
        bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")

        config = MomentumEvolveConfig(
            instrument_id=instrument.id,
            bar_type=bar_type,
            trade_size=Decimal("0.1"),
            fast_period=10,
            slow_period=30,
        )
        strategy = MomentumEvolveStrategy(config)
        engine.add_strategy(strategy)

        start = time.perf_counter()
        engine.run()
        elapsed = time.perf_counter() - start

        equity_points = len(strategy.get_equity_curve())

        return elapsed, equity_points
    finally:
        engine.dispose()


def run_benchmark_no_equity(num_bars: int) -> float:
    """
    Run backtest without equity tracking.

    Returns:
        Execution time in seconds
    """
    engine = create_engine()
    try:
        generate_bars(engine, num_bars)

        instrument = TestInstrumentProvider.btcusdt_binance()
        bar_type = BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")

        config = VanillaMomentumConfig(
            instrument_id=instrument.id,
            bar_type=bar_type,
            trade_size=Decimal("0.1"),
            fast_period=10,
            slow_period=30,
        )
        strategy = VanillaMomentumStrategy(config)
        engine.add_strategy(strategy)

        start = time.perf_counter()
        engine.run()
        elapsed = time.perf_counter() - start

        return elapsed
    finally:
        engine.dispose()


def run_benchmark(num_bars: int = 10000, num_runs: int = 3) -> dict:
    """
    Run complete benchmark comparing equity tracking overhead.

    Args:
        num_bars: Number of bars to process per run (must be > 0)
        num_runs: Number of runs to average (must be > 0)

    Returns:
        Dictionary with benchmark results

    Raises:
        ValueError: If num_bars or num_runs is not positive
    """
    # Validate inputs
    if num_bars <= 0:
        raise ValueError(f"num_bars must be positive, got {num_bars}")
    if num_runs <= 0:
        raise ValueError(f"num_runs must be positive, got {num_runs}")

    print(f"\n{'=' * 60}")
    print("Alpha-Evolve Equity Tracking Benchmark")
    print(f"{'=' * 60}")
    print(f"Bars per run: {num_bars:,}")
    print(f"Number of runs: {num_runs}")
    print(f"{'=' * 60}\n")

    # Warmup run (discard)
    print("Warmup run...")
    try:
        run_benchmark_no_equity(min(1000, num_bars))
    except Exception as e:
        print(f"Warning: Warmup run failed: {e}")
        print("Continuing with benchmark...\n")

    # Run benchmarks
    times_with_equity = []
    times_no_equity = []
    equity_points = 0

    for i in range(num_runs):
        print(f"\nRun {i + 1}/{num_runs}:")

        try:
            # Run without equity tracking
            t_no_eq = run_benchmark_no_equity(num_bars)
            times_no_equity.append(t_no_eq)
            print(f"  No equity tracking: {t_no_eq:.4f}s")

            # Run with equity tracking
            t_eq, points = run_benchmark_with_equity(num_bars)
            times_with_equity.append(t_eq)
            equity_points = points
            print(f"  With equity tracking: {t_eq:.4f}s ({points:,} points)")
        except Exception as e:
            print(f"  Error in run {i + 1}: {e}")
            continue

    # Validate that we have data
    if not times_no_equity or not times_with_equity:
        print("\nError: No successful benchmark runs completed")
        return {
            "num_bars": num_bars,
            "num_runs": num_runs,
            "avg_time_no_equity_s": 0,
            "avg_time_with_equity_s": 0,
            "overhead_percent": 0,
            "equity_points": 0,
            "pass": False,
        }

    # Calculate statistics
    avg_no_eq = statistics.mean(times_no_equity)
    avg_with_eq = statistics.mean(times_with_equity)

    # Handle division by zero (theoretically possible if execution is instant)
    if avg_no_eq <= 0:
        print("\nError: Baseline timing is zero or negative, unable to calculate overhead")
        overhead = 0.0
    else:
        overhead = ((avg_with_eq - avg_no_eq) / avg_no_eq) * 100

    results = {
        "num_bars": num_bars,
        "num_runs": num_runs,
        "avg_time_no_equity_s": avg_no_eq,
        "avg_time_with_equity_s": avg_with_eq,
        "overhead_percent": overhead,
        "equity_points": equity_points,
        "pass": overhead < 5.0,
    }

    # Print results
    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")
    print(f"Average time (no equity):   {avg_no_eq:.4f}s")
    print(f"Average time (with equity): {avg_with_eq:.4f}s")
    print(f"Equity points recorded:     {equity_points:,}")
    print(f"Overhead:                   {overhead:.2f}%")
    print(f"{'=' * 60}")

    if overhead < 5.0:
        print(f"\n[PASS] Equity tracking overhead ({overhead:.2f}%) is below 5% threshold")
    else:
        print(f"\n[FAIL] Equity tracking overhead ({overhead:.2f}%) exceeds 5% threshold")

    return results


def main():
    """Run benchmark from command line."""
    parser = argparse.ArgumentParser(description="Benchmark equity tracking overhead")
    parser.add_argument(
        "--bars",
        type=int,
        default=10000,
        help="Number of bars per run (default: 10000)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of runs to average (default: 3)",
    )

    args = parser.parse_args()
    results = run_benchmark(num_bars=args.bars, num_runs=args.runs)

    # Exit with error code if benchmark fails
    exit(0 if results["pass"] else 1)


if __name__ == "__main__":
    main()
