"""
Backtest Evaluator for Alpha-Evolve.

Enables dynamic strategy evaluation by:
- Loading strategy code from strings
- Running backtests via NautilusTrader's BacktestEngine
- Extracting standardized fitness metrics

Part of spec-007: Alpha-Evolve Backtest Evaluator
"""

from __future__ import annotations

import ast
import asyncio
import math
import sys
import time
import types
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nautilus_trader.backtest.engine import BacktestEngine
    from nautilus_trader.trading.strategy import Strategy

from scripts.alpha_evolve.store import FitnessMetrics


@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""

    catalog_path: str | Path
    instrument_id: str
    start_date: str  # ISO 8601
    end_date: str  # ISO 8601
    bar_type: str = "1-MINUTE-LAST"
    initial_capital: float = 100_000.0
    venue: str = "BINANCE"
    oms_type: str = "NETTING"
    account_type: str = "MARGIN"
    base_currency: str = "USDT"
    random_seed: int | None = 42  # For reproducibility


@dataclass
class EvaluationRequest:
    """Input for strategy evaluation."""

    strategy_code: str
    strategy_class_name: str = "EvolvedStrategy"
    config_class_name: str = "EvolvedStrategyConfig"
    backtest_config: BacktestConfig | None = None


@dataclass
class EvaluationResult:
    """Output from strategy evaluation."""

    success: bool
    metrics: FitnessMetrics | None = None
    error: str | None = None
    error_type: str | None = None  # "syntax", "import", "runtime", "timeout", "data"
    duration_ms: int = 0
    trade_count: int = 0


class StrategyEvaluator:
    """
    Evaluates strategy code via backtesting.

    Provides both synchronous and asynchronous evaluation methods.
    Uses asyncio.Semaphore to limit concurrent evaluations for memory safety.
    """

    def __init__(
        self,
        default_config: BacktestConfig,
        max_concurrent: int = 2,
        timeout_seconds: int = 300,
    ) -> None:
        """
        Initialize the evaluator.

        Args:
            default_config: Default backtest configuration
            max_concurrent: Maximum concurrent evaluations (memory safety)
            timeout_seconds: Timeout per evaluation in seconds
        """
        self.default_config = default_config
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self._semaphore = asyncio.Semaphore(max_concurrent)

    def _validate_syntax(self, code: str) -> str | None:
        """
        Validate Python syntax.

        Args:
            code: Python source code string

        Returns:
            Error message if invalid, None if valid
        """
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            return f"Syntax error at line {e.lineno}: {e.msg}"

    def _load_strategy(
        self,
        code: str,
        class_name: str,
        config_name: str,
    ) -> tuple[type, type]:
        """
        Dynamically load strategy and config classes from code string.

        Args:
            code: Python source code containing strategy definition
            class_name: Name of the strategy class
            config_name: Name of the config class

        Returns:
            Tuple of (StrategyClass, ConfigClass)

        Raises:
            ImportError: If required modules not available
            AttributeError: If class not found in code
        """

        # Create isolated module with unique name to avoid race conditions
        # when multiple threads call this method concurrently
        module_name = f"evolved_strategy_{uuid.uuid4().hex}"
        module = types.ModuleType(module_name)
        module.__file__ = "<dynamic>"

        # Add to sys.modules temporarily for relative imports
        sys.modules[module_name] = module

        try:
            # Execute code in module namespace
            exec(code, module.__dict__)

            # Extract classes
            strategy_class = getattr(module, class_name)
            config_class = getattr(module, config_name)

            return strategy_class, config_class
        finally:
            # Clean up
            if module_name in sys.modules:
                del sys.modules[module_name]

    def _configure_venue(self, config: BacktestConfig):
        """
        Configure venue for BacktestEngine.

        Args:
            config: Backtest configuration

        Returns:
            Configured BacktestVenueConfig
        """
        from nautilus_trader.backtest.config import BacktestVenueConfig
        from nautilus_trader.model.enums import AccountType, OmsType

        oms_type = OmsType[config.oms_type]
        account_type = AccountType[config.account_type]

        return BacktestVenueConfig(
            name=config.venue,
            oms_type=oms_type,
            account_type=account_type,
            base_currency=config.base_currency,
            starting_balances=[f"{config.initial_capital} {config.base_currency}"],
            bar_adaptive_high_low_ordering=True,
        )

    def _configure_data(self, config: BacktestConfig):
        """
        Load data from ParquetDataCatalog.

        Args:
            config: Backtest configuration

        Returns:
            Tuple of (instrument, bars)

        Raises:
            ValueError: If catalog path invalid or instrument not found
        """
        from nautilus_trader.model.identifiers import InstrumentId
        from nautilus_trader.persistence.catalog import ParquetDataCatalog

        catalog_path = Path(config.catalog_path)
        if not catalog_path.exists():
            raise ValueError(f"Catalog path not found: {catalog_path}")

        catalog = ParquetDataCatalog(str(catalog_path))

        # Parse instrument ID
        instrument_id = InstrumentId.from_str(config.instrument_id)

        # Get instrument
        instruments = catalog.instruments(instrument_ids=[str(instrument_id)])
        if not instruments:
            raise ValueError(f"Instrument not found: {config.instrument_id}")
        instrument = instruments[0]

        # Get bars
        bars = catalog.bars(
            instrument_ids=[str(instrument_id)],
            start=config.start_date,
            end=config.end_date,
        )
        if not bars:
            raise ValueError(
                f"No bars found for {config.instrument_id} "
                f"between {config.start_date} and {config.end_date}"
            )

        return instrument, bars

    def _run_backtest(
        self,
        strategy: Strategy,
        config: BacktestConfig,
    ) -> BacktestEngine:
        """
        Execute backtest with configured engine.

        Args:
            strategy: Instantiated strategy
            config: Backtest configuration

        Returns:
            BacktestEngine after run completion
        """
        from nautilus_trader.backtest.config import BacktestEngineConfig
        from nautilus_trader.backtest.engine import BacktestEngine

        # Load data
        instrument, bars = self._configure_data(config)

        # Configure engine
        engine_config = BacktestEngineConfig(
            trader_id="BACKTESTER-001",
            logging_bypass=True,  # Reduce logging overhead
        )

        engine = BacktestEngine(config=engine_config)

        # Add venue
        venue_config = self._configure_venue(config)
        engine.add_venue(
            venue=venue_config.name,
            oms_type=venue_config.oms_type,
            account_type=venue_config.account_type,
            base_currency=venue_config.base_currency,
            starting_balances=venue_config.starting_balances,
            bar_adaptive_high_low_ordering=venue_config.bar_adaptive_high_low_ordering,
        )

        # Add instrument and data
        engine.add_instrument(instrument)
        engine.add_data(bars)

        # Add strategy
        engine.add_strategy(strategy)

        # Run
        engine.run()

        return engine

    def _calculate_cagr(self, total_return: float, days: int) -> float:
        """
        Calculate Compound Annual Growth Rate.

        Args:
            total_return: Total return as decimal (e.g., 0.15 for 15%)
            days: Number of days in period

        Returns:
            CAGR as decimal
        """

        # Handle invalid inputs
        if days <= 0:
            return 0.0
        if math.isnan(total_return) or math.isinf(total_return):
            return 0.0
        if total_return <= -1:
            return -1.0  # Total loss

        years = days / 365.0
        return (1 + total_return) ** (1 / years) - 1

    def _calculate_calmar(self, cagr: float, max_drawdown: float) -> float:
        """
        Calculate Calmar Ratio.

        Args:
            cagr: Compound Annual Growth Rate
            max_drawdown: Maximum drawdown (positive value, e.g., 0.20 for 20%)

        Returns:
            Calmar ratio (CAGR / MaxDD)
        """

        # Handle NaN/Inf inputs
        if math.isnan(cagr) or math.isinf(cagr):
            return 0.0
        if math.isnan(max_drawdown) or math.isinf(max_drawdown):
            return 0.0
        if max_drawdown == 0:
            return 0.0 if cagr <= 0 else float("inf")
        return cagr / abs(max_drawdown)

    def _extract_metrics(self, engine: BacktestEngine, config: BacktestConfig) -> FitnessMetrics:
        """
        Extract fitness metrics from completed backtest.

        Args:
            engine: BacktestEngine after run completion
            config: Backtest configuration (for date range)

        Returns:
            FitnessMetrics with extracted values
        """

        # Get analyzer stats
        analyzer = engine.portfolio.analyzer
        stats_returns = analyzer.get_performance_stats_returns()
        stats_general = analyzer.get_performance_stats_general()

        # Get total return
        total_return = float(engine.portfolio.total_return())

        # Calculate days in period
        # Handle ISO dates with 'Z' suffix (Python 3.10 doesn't support it natively)
        start_str = config.start_date.replace("Z", "+00:00")
        end_str = config.end_date.replace("Z", "+00:00")
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
        days = (end - start).days

        # Extract Sharpe (default to 0 if not available)
        sharpe = stats_returns.get("Sharpe Ratio (252 days)", 0.0)
        if sharpe is None:
            sharpe = 0.0

        # Extract max drawdown (convert to positive value)
        max_dd = stats_returns.get("Max Drawdown", 0.0)
        if max_dd is None:
            max_dd = 0.0
        max_dd = abs(float(max_dd))

        # Calculate derived metrics
        cagr = self._calculate_cagr(total_return, days)
        calmar = self._calculate_calmar(cagr, max_dd)

        # Get trade count
        positions_closed = engine.cache.positions_closed()
        trade_count = len(positions_closed) if positions_closed else 0

        # Get win rate
        win_rate = stats_general.get("Win Rate", 0.0)
        if win_rate is None:
            win_rate = 0.0

        return FitnessMetrics(
            sharpe_ratio=float(sharpe),
            calmar_ratio=calmar,
            max_drawdown=max_dd,
            cagr=cagr,
            total_return=total_return,
            trade_count=trade_count,
            win_rate=float(win_rate),
        )

    def evaluate_sync(self, request: EvaluationRequest) -> EvaluationResult:
        """
        Evaluate strategy synchronously.

        Args:
            request: Evaluation request with strategy code

        Returns:
            EvaluationResult with success/error and metrics
        """
        start_time = time.time()

        # Use request config or default
        config = request.backtest_config or self.default_config

        # 1. Validate syntax
        if error := self._validate_syntax(request.strategy_code):
            return EvaluationResult(
                success=False,
                error=error,
                error_type="syntax",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # 2. Load strategy
        try:
            StrategyClass, ConfigClass = self._load_strategy(
                request.strategy_code,
                request.strategy_class_name,
                request.config_class_name,
            )
        except ImportError as e:
            return EvaluationResult(
                success=False,
                error=f"Import error: {e}",
                error_type="import",
                duration_ms=int((time.time() - start_time) * 1000),
            )
        except AttributeError as e:
            return EvaluationResult(
                success=False,
                error=f"Class not found: {e}",
                error_type="import",
                duration_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return EvaluationResult(
                success=False,
                error=f"Load error: {e}",
                error_type="import",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # 3. Instantiate strategy
        try:
            # Create config instance
            strategy_config = ConfigClass(
                strategy_id=request.strategy_class_name,
                instrument_id=config.instrument_id,
            )
            strategy = StrategyClass(config=strategy_config)
        except Exception as e:
            return EvaluationResult(
                success=False,
                error=f"Strategy instantiation error: {e}",
                error_type="runtime",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # 4. Run backtest
        engine = None
        try:
            engine = self._run_backtest(strategy, config)
        except ValueError as e:
            # Data errors (catalog not found, instrument not found, etc.)
            return EvaluationResult(
                success=False,
                error=str(e),
                error_type="data",
                duration_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return EvaluationResult(
                success=False,
                error=f"Runtime error: {e}",
                error_type="runtime",
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # 5. Extract metrics and cleanup
        try:
            metrics = self._extract_metrics(engine, config)
        except Exception as e:
            return EvaluationResult(
                success=False,
                error=f"Metrics extraction error: {e}",
                error_type="runtime",
                duration_ms=int((time.time() - start_time) * 1000),
            )
        finally:
            # Dispose engine to prevent resource leaks
            if engine is not None:
                try:
                    engine.dispose()
                except Exception:
                    pass  # Best-effort cleanup

        duration_ms = int((time.time() - start_time) * 1000)

        return EvaluationResult(
            success=True,
            metrics=metrics,
            duration_ms=duration_ms,
            trade_count=metrics.trade_count or 0,
        )

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        """
        Evaluate strategy asynchronously with concurrency limits.

        Uses semaphore to limit concurrent evaluations for memory safety.

        Args:
            request: Evaluation request with strategy code

        Returns:
            EvaluationResult with success/error and metrics
        """
        try:
            async with self._semaphore:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.evaluate_sync, request),
                    timeout=self.timeout_seconds,
                )
            return result
        except TimeoutError:
            return EvaluationResult(
                success=False,
                error=f"Evaluation timeout exceeded ({self.timeout_seconds}s)",
                error_type="timeout",
                duration_ms=self.timeout_seconds * 1000,
            )
        except Exception as e:
            return EvaluationResult(
                success=False,
                error=f"Evaluation error: {e}",
                error_type="runtime",
                duration_ms=0,
            )
