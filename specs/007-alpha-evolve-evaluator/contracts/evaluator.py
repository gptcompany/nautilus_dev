"""
Contract definitions for Alpha-Evolve Backtest Evaluator.

This module defines the public API for the evaluator component.
Implementation in scripts/alpha_evolve/evaluator.py must satisfy these contracts.

Feature: 007-alpha-evolve-evaluator
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.alpha_evolve.store import FitnessMetrics


# =============================================================================
# Data Transfer Objects
# =============================================================================


@dataclass
class BacktestConfig:
    """
    Configuration for backtest execution.

    Defines the data source, time range, and simulation parameters
    for running a strategy backtest.
    """

    catalog_path: str | Path
    """Path to ParquetDataCatalog directory."""

    instrument_id: str
    """Trading instrument in format SYMBOL.VENUE (e.g., BTCUSDT-PERP.BINANCE)."""

    start_date: str
    """Backtest start date in ISO 8601 format (e.g., 2024-01-01)."""

    end_date: str
    """Backtest end date in ISO 8601 format (e.g., 2024-06-01)."""

    bar_type: str = "1-MINUTE-LAST"
    """Bar aggregation specification (period-spec-price)."""

    initial_capital: float = 100_000.0
    """Starting account balance."""

    venue: str = "BINANCE"
    """Simulated exchange name."""

    oms_type: str = "NETTING"
    """Order management system type: NETTING or HEDGING."""

    account_type: str = "MARGIN"
    """Account type: CASH, MARGIN, or BETTING."""

    base_currency: str = "USDT"
    """Account base currency."""

    random_seed: int | None = 42
    """Random seed for reproducibility. None for non-deterministic."""


@dataclass
class EvaluationRequest:
    """
    Input for strategy evaluation.

    Contains the strategy code to evaluate and optional configuration overrides.
    """

    strategy_code: str
    """Python source code containing strategy and config classes."""

    strategy_class_name: str = "EvolvedStrategy"
    """Name of the Strategy subclass to instantiate."""

    config_class_name: str = "EvolvedStrategyConfig"
    """Name of the StrategyConfig subclass to instantiate."""

    backtest_config: BacktestConfig | None = None
    """Optional backtest configuration override. Uses evaluator default if None."""


@dataclass
class EvaluationResult:
    """
    Output from strategy evaluation.

    Contains either successful metrics or error information.
    """

    success: bool
    """True if backtest completed successfully."""

    metrics: FitnessMetrics | None
    """Extracted performance metrics, None if evaluation failed."""

    error: str | None
    """Error message if evaluation failed, None if successful."""

    error_type: str | None
    """
    Error classification if failed:
    - 'syntax': Invalid Python syntax
    - 'import': Module import failed
    - 'runtime': Exception during backtest
    - 'timeout': Evaluation exceeded time limit
    - 'data': Missing or invalid data
    """

    duration_ms: int
    """Total execution time in milliseconds."""

    trade_count: int = 0
    """Number of trades executed (0 if failed)."""


# =============================================================================
# Evaluator Contract
# =============================================================================


class IStrategyEvaluator(ABC):
    """
    Abstract contract for strategy evaluation.

    Implementations must provide both sync and async evaluation methods.
    """

    @abstractmethod
    def __init__(
        self,
        default_config: BacktestConfig,
        max_concurrent: int = 2,
        timeout_seconds: int = 300,
    ) -> None:
        """
        Initialize evaluator.

        Args:
            default_config: Default backtest configuration
            max_concurrent: Maximum concurrent evaluations (memory safety)
            timeout_seconds: Evaluation timeout in seconds
        """
        ...

    @abstractmethod
    async def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        """
        Evaluate strategy code asynchronously.

        Respects concurrency limits and timeout configuration.

        Args:
            request: Evaluation request with strategy code

        Returns:
            Evaluation result with metrics or error
        """
        ...

    @abstractmethod
    def evaluate_sync(self, request: EvaluationRequest) -> EvaluationResult:
        """
        Evaluate strategy code synchronously.

        Blocks until evaluation completes or times out.

        Args:
            request: Evaluation request with strategy code

        Returns:
            Evaluation result with metrics or error
        """
        ...


# =============================================================================
# Usage Examples
# =============================================================================


def example_usage() -> None:
    """Example usage of the evaluator contract."""
    # Example 1: Basic evaluation
    config = BacktestConfig(
        catalog_path="/path/to/catalog",
        instrument_id="BTCUSDT-PERP.BINANCE",
        start_date="2024-01-01",
        end_date="2024-06-01",
    )

    strategy_code = """
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import StrategyConfig

class EvolvedStrategyConfig(StrategyConfig, frozen=True):
    instrument_id: str

class EvolvedStrategy(Strategy):
    def __init__(self, config: EvolvedStrategyConfig):
        super().__init__(config)

    def on_start(self):
        pass

    def on_bar(self, bar):
        pass
"""

    request = EvaluationRequest(
        strategy_code=strategy_code,
        backtest_config=config,
    )

    # Sync usage
    # evaluator = StrategyEvaluator(default_config=config)
    # result = evaluator.evaluate_sync(request)

    # Async usage
    # result = await evaluator.evaluate(request)

    # Example 2: Error handling
    invalid_code = "def foo(:"  # Syntax error

    error_request = EvaluationRequest(strategy_code=invalid_code)
    # result = evaluator.evaluate_sync(error_request)
    # assert result.success is False
    # assert result.error_type == "syntax"
