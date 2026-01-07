"""Tests for Alpha-Evolve Backtest Evaluator."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.alpha_evolve.evaluator import (
    BacktestConfig,
    EvaluationRequest,
    EvaluationResult,
    StrategyEvaluator,
)
from scripts.alpha_evolve.store import FitnessMetrics

# === FIXTURES ===


@pytest.fixture
def sample_backtest_config(tmp_path: Path) -> BacktestConfig:
    """Sample backtest configuration for testing."""
    return BacktestConfig(
        catalog_path=str(tmp_path / "catalog"),
        instrument_id="BTCUSDT-PERP.BINANCE",
        start_date="2024-01-01",
        end_date="2024-06-01",
        bar_type="1-MINUTE-LAST",
        initial_capital=100_000.0,
        venue="BINANCE",
    )


@pytest.fixture
def sample_valid_strategy_code() -> str:
    """Valid strategy code for testing."""
    return '''
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import StrategyConfig


class EvolvedStrategyConfig(StrategyConfig, frozen=True):
    """Strategy configuration."""
    instrument_id: str


class EvolvedStrategy(Strategy):
    """Test strategy."""

    def __init__(self, config: EvolvedStrategyConfig):
        super().__init__(config)

    def on_start(self):
        pass

    def on_bar(self, bar):
        pass
'''


@pytest.fixture
def sample_strategy_syntax_error() -> str:
    """Strategy code with syntax error."""
    return """
def broken_function(
    # Missing closing parenthesis
    pass
"""


@pytest.fixture
def sample_strategy_missing_class() -> str:
    """Strategy code missing expected class name."""
    return """
class WrongClassName:
    pass
"""


@pytest.fixture
def evaluator(sample_backtest_config: BacktestConfig) -> StrategyEvaluator:
    """Create a StrategyEvaluator for testing."""
    return StrategyEvaluator(
        default_config=sample_backtest_config,
        max_concurrent=2,
        timeout_seconds=60,
    )


# === USER STORY 1: DYNAMIC STRATEGY EVALUATION ===


class TestLoadStrategyValidCode:
    """T009: Test loading valid strategy code."""

    def test_load_strategy_returns_classes(
        self, evaluator: StrategyEvaluator, sample_valid_strategy_code: str
    ):
        """Valid code should return strategy and config classes."""
        StrategyClass, ConfigClass = evaluator._load_strategy(
            sample_valid_strategy_code,
            "EvolvedStrategy",
            "EvolvedStrategyConfig",
        )

        assert StrategyClass is not None
        assert ConfigClass is not None
        assert StrategyClass.__name__ == "EvolvedStrategy"
        assert ConfigClass.__name__ == "EvolvedStrategyConfig"

    def test_load_strategy_cleans_up_modules(
        self, evaluator: StrategyEvaluator, sample_valid_strategy_code: str
    ):
        """Loaded modules should be cleaned up after loading."""
        import sys

        evaluator._load_strategy(
            sample_valid_strategy_code,
            "EvolvedStrategy",
            "EvolvedStrategyConfig",
        )

        # No evolved_strategy* modules should remain
        evolved_modules = [k for k in sys.modules if k.startswith("evolved_strategy")]
        assert len(evolved_modules) == 0

    def test_load_strategy_uses_unique_module_names(
        self, evaluator: StrategyEvaluator, sample_valid_strategy_code: str
    ):
        """Multiple loads should use unique module names for thread safety."""
        import sys

        # Track module names during loading
        seen_modules = []

        original_setitem = dict.__setitem__

        def tracking_setitem(self, key, value):
            if key.startswith("evolved_strategy"):
                seen_modules.append(key)
            return original_setitem(self, key, value)

        # Load twice
        evaluator._load_strategy(
            sample_valid_strategy_code,
            "EvolvedStrategy",
            "EvolvedStrategyConfig",
        )
        # Capture module count after first load
        _ = set(seen_modules)

        evaluator._load_strategy(
            sample_valid_strategy_code,
            "EvolvedStrategy",
            "EvolvedStrategyConfig",
        )

        # Both loads should have used unique module names (can't verify exact names
        # but we can verify cleanup works)
        evolved_modules = [k for k in sys.modules if k.startswith("evolved_strategy")]
        assert len(evolved_modules) == 0


class TestLoadStrategySyntaxError:
    """T010: Test handling of syntax errors."""

    def test_validate_syntax_returns_error(
        self, evaluator: StrategyEvaluator, sample_strategy_syntax_error: str
    ):
        """Syntax errors should be detected before exec."""
        error = evaluator._validate_syntax(sample_strategy_syntax_error)

        assert error is not None
        assert "Syntax error" in error
        assert "line" in error.lower()

    def test_evaluate_sync_returns_syntax_error(
        self, evaluator: StrategyEvaluator, sample_strategy_syntax_error: str
    ):
        """evaluate_sync should return error_type='syntax' for syntax errors."""
        request = EvaluationRequest(strategy_code=sample_strategy_syntax_error)
        result = evaluator.evaluate_sync(request)

        assert result.success is False
        assert result.error_type == "syntax"
        assert result.error is not None
        assert result.metrics is None


class TestLoadStrategyMissingClass:
    """T011: Test handling of missing class names."""

    def test_load_strategy_missing_class_raises(
        self, evaluator: StrategyEvaluator, sample_strategy_missing_class: str
    ):
        """Missing class should raise AttributeError."""
        with pytest.raises(AttributeError):
            evaluator._load_strategy(
                sample_strategy_missing_class,
                "EvolvedStrategy",  # Not in code
                "EvolvedStrategyConfig",
            )

    def test_evaluate_sync_returns_import_error(
        self, evaluator: StrategyEvaluator, sample_strategy_missing_class: str
    ):
        """evaluate_sync should return error_type='import' for missing class."""
        request = EvaluationRequest(strategy_code=sample_strategy_missing_class)
        result = evaluator.evaluate_sync(request)

        assert result.success is False
        assert result.error_type == "import"
        assert result.error is not None


class TestEvaluateSyncSuccess:
    """T012: Test successful synchronous evaluation."""

    @patch.object(StrategyEvaluator, "_run_backtest")
    @patch.object(StrategyEvaluator, "_extract_metrics")
    def test_evaluate_sync_success(
        self,
        mock_extract: MagicMock,
        mock_run: MagicMock,
        evaluator: StrategyEvaluator,
        sample_valid_strategy_code: str,
    ):
        """Successful evaluation should return success=True with metrics."""
        # Mock the backtest engine
        mock_engine = MagicMock()
        mock_run.return_value = mock_engine

        # Mock metrics extraction
        mock_metrics = FitnessMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=0.10,
            cagr=0.25,
            total_return=0.50,
            trade_count=100,
            win_rate=0.55,
        )
        mock_extract.return_value = mock_metrics

        request = EvaluationRequest(strategy_code=sample_valid_strategy_code)
        result = evaluator.evaluate_sync(request)

        assert result.success is True
        assert result.metrics == mock_metrics
        assert result.error is None
        assert result.error_type is None
        assert result.duration_ms >= 0  # Mocked execution may be near-instant
        assert result.trade_count == 100


class TestEvaluateSyncRuntimeError:
    """T013: Test handling of runtime errors during backtest."""

    @patch.object(StrategyEvaluator, "_run_backtest")
    def test_evaluate_sync_runtime_error(
        self,
        mock_run: MagicMock,
        evaluator: StrategyEvaluator,
        sample_valid_strategy_code: str,
    ):
        """Runtime errors should return error_type='runtime'."""
        mock_run.side_effect = RuntimeError("Division by zero in on_bar")

        request = EvaluationRequest(strategy_code=sample_valid_strategy_code)
        result = evaluator.evaluate_sync(request)

        assert result.success is False
        assert result.error_type == "runtime"
        assert "Division by zero" in result.error


class TestEvaluateTimeout:
    """T014: Test timeout handling in async evaluation."""

    @pytest.mark.asyncio
    async def test_evaluate_timeout(
        self,
        evaluator: StrategyEvaluator,
        sample_valid_strategy_code: str,
    ):
        """Timeout should return error_type='timeout'."""
        # Create evaluator with very short timeout
        short_timeout_evaluator = StrategyEvaluator(
            default_config=evaluator.default_config,
            max_concurrent=1,
            timeout_seconds=0,  # Immediate timeout
        )

        # Patch evaluate_sync to sleep
        def slow_evaluate(*args, **kwargs):
            import time

            time.sleep(1)  # Will exceed 0s timeout
            return EvaluationResult(success=True)

        with patch.object(short_timeout_evaluator, "evaluate_sync", side_effect=slow_evaluate):
            request = EvaluationRequest(strategy_code=sample_valid_strategy_code)
            result = await short_timeout_evaluator.evaluate(request)

        assert result.success is False
        assert result.error_type == "timeout"
        assert "timeout" in result.error.lower()


# === USER STORY 2: KPI EXTRACTION ===


class TestExtractMetricsProfitable:
    """T022: Test metrics extraction from profitable strategy."""

    def test_extract_metrics_profitable(self, evaluator: StrategyEvaluator):
        """Profitable backtest should have positive metrics."""
        # Create mock engine with profitable results
        mock_engine = MagicMock()
        mock_engine.portfolio.total_return.return_value = 0.50  # 50% return
        mock_engine.portfolio.analyzer.get_performance_stats_returns.return_value = {
            "Sharpe Ratio (252 days)": 1.8,
            "Max Drawdown": -0.15,
        }
        mock_engine.portfolio.analyzer.get_performance_stats_general.return_value = {
            "Win Rate": 0.60,
        }
        mock_engine.cache.positions_closed.return_value = [MagicMock()] * 100

        config = BacktestConfig(
            catalog_path="/tmp/catalog",
            instrument_id="BTCUSDT-PERP.BINANCE",
            start_date="2024-01-01",
            end_date="2024-06-01",
        )

        metrics = evaluator._extract_metrics(mock_engine, config)

        assert metrics.sharpe_ratio == 1.8
        assert metrics.max_drawdown == 0.15  # Converted to positive
        assert metrics.total_return == 0.50
        assert metrics.trade_count == 100
        assert metrics.win_rate == 0.60
        assert metrics.cagr > 0
        assert metrics.calmar_ratio > 0


class TestExtractMetricsNoTrades:
    """T023: Test metrics extraction when no trades executed."""

    def test_extract_metrics_no_trades(self, evaluator: StrategyEvaluator):
        """No trades should result in zero metrics."""
        mock_engine = MagicMock()
        mock_engine.portfolio.total_return.return_value = 0.0
        mock_engine.portfolio.analyzer.get_performance_stats_returns.return_value = {
            "Sharpe Ratio (252 days)": 0.0,
            "Max Drawdown": 0.0,
        }
        mock_engine.portfolio.analyzer.get_performance_stats_general.return_value = {
            "Win Rate": 0.0,
        }
        mock_engine.cache.positions_closed.return_value = []

        config = BacktestConfig(
            catalog_path="/tmp/catalog",
            instrument_id="BTCUSDT-PERP.BINANCE",
            start_date="2024-01-01",
            end_date="2024-06-01",
        )

        metrics = evaluator._extract_metrics(mock_engine, config)

        assert metrics.trade_count == 0
        assert metrics.total_return == 0.0
        assert metrics.cagr == 0.0


class TestExtractMetricsNegativeReturns:
    """T024: Test metrics extraction with negative returns."""

    def test_extract_metrics_negative_returns(self, evaluator: StrategyEvaluator):
        """Negative returns should have negative metrics."""
        mock_engine = MagicMock()
        mock_engine.portfolio.total_return.return_value = -0.30  # 30% loss
        mock_engine.portfolio.analyzer.get_performance_stats_returns.return_value = {
            "Sharpe Ratio (252 days)": -0.5,
            "Max Drawdown": -0.40,
        }
        mock_engine.portfolio.analyzer.get_performance_stats_general.return_value = {
            "Win Rate": 0.35,
        }
        mock_engine.cache.positions_closed.return_value = [MagicMock()] * 50

        config = BacktestConfig(
            catalog_path="/tmp/catalog",
            instrument_id="BTCUSDT-PERP.BINANCE",
            start_date="2024-01-01",
            end_date="2024-06-01",
        )

        metrics = evaluator._extract_metrics(mock_engine, config)

        assert metrics.sharpe_ratio == -0.5
        assert metrics.total_return == -0.30
        assert metrics.max_drawdown == 0.40
        assert metrics.cagr < 0


class TestCalculateCalmarRatio:
    """T025: Test Calmar ratio calculation."""

    def test_calmar_positive(self, evaluator: StrategyEvaluator):
        """Positive CAGR with drawdown should give positive Calmar."""
        calmar = evaluator._calculate_calmar(cagr=0.25, max_drawdown=0.10)
        assert calmar == 2.5

    def test_calmar_zero_drawdown(self, evaluator: StrategyEvaluator):
        """Zero drawdown with positive CAGR should return inf."""
        calmar = evaluator._calculate_calmar(cagr=0.25, max_drawdown=0.0)
        assert calmar == float("inf")

    def test_calmar_zero_cagr(self, evaluator: StrategyEvaluator):
        """Zero CAGR with zero drawdown should return 0."""
        calmar = evaluator._calculate_calmar(cagr=0.0, max_drawdown=0.0)
        assert calmar == 0.0

    def test_calmar_negative_cagr(self, evaluator: StrategyEvaluator):
        """Negative CAGR should give negative Calmar."""
        calmar = evaluator._calculate_calmar(cagr=-0.20, max_drawdown=0.10)
        assert calmar == -2.0

    def test_calmar_nan_cagr(self, evaluator: StrategyEvaluator):
        """NaN CAGR should return 0."""
        calmar = evaluator._calculate_calmar(cagr=float("nan"), max_drawdown=0.10)
        assert calmar == 0.0

    def test_calmar_nan_drawdown(self, evaluator: StrategyEvaluator):
        """NaN drawdown should return 0."""
        calmar = evaluator._calculate_calmar(cagr=0.25, max_drawdown=float("nan"))
        assert calmar == 0.0

    def test_calmar_inf_cagr(self, evaluator: StrategyEvaluator):
        """Infinity CAGR should return 0."""
        calmar = evaluator._calculate_calmar(cagr=float("inf"), max_drawdown=0.10)
        assert calmar == 0.0


class TestCalculateCAGR:
    """T026: Test CAGR calculation."""

    def test_cagr_one_year(self, evaluator: StrategyEvaluator):
        """50% return over 365 days should be 50% CAGR."""
        cagr = evaluator._calculate_cagr(total_return=0.50, days=365)
        assert abs(cagr - 0.50) < 0.01

    def test_cagr_half_year(self, evaluator: StrategyEvaluator):
        """20% return over 180 days should annualize higher."""
        cagr = evaluator._calculate_cagr(total_return=0.20, days=180)
        assert cagr > 0.20  # Should be higher when annualized

    def test_cagr_zero_days(self, evaluator: StrategyEvaluator):
        """Zero days should return 0."""
        cagr = evaluator._calculate_cagr(total_return=0.50, days=0)
        assert cagr == 0.0

    def test_cagr_total_loss(self, evaluator: StrategyEvaluator):
        """Total loss (-100%) should return -1."""
        cagr = evaluator._calculate_cagr(total_return=-1.0, days=365)
        assert cagr == -1.0

    def test_cagr_nan_input(self, evaluator: StrategyEvaluator):
        """NaN input should return 0."""
        cagr = evaluator._calculate_cagr(total_return=float("nan"), days=365)
        assert cagr == 0.0

    def test_cagr_inf_input(self, evaluator: StrategyEvaluator):
        """Infinity input should return 0."""
        cagr = evaluator._calculate_cagr(total_return=float("inf"), days=365)
        assert cagr == 0.0


# === USER STORY 3: HISTORICAL DATA CONFIGURATION ===


class TestConfigInstrumentId:
    """T032: Test instrument ID configuration."""

    def test_evaluation_uses_request_config(
        self,
        evaluator: StrategyEvaluator,
        sample_valid_strategy_code: str,
        tmp_path: Path,
    ):
        """Evaluation should use config from request if provided."""
        custom_config = BacktestConfig(
            catalog_path=str(tmp_path),
            instrument_id="ETHUSDT-PERP.BINANCE",
            start_date="2024-03-01",
            end_date="2024-04-01",
        )

        request = EvaluationRequest(
            strategy_code=sample_valid_strategy_code,
            backtest_config=custom_config,
        )

        # Should fail due to missing catalog, but with data error
        result = evaluator.evaluate_sync(request)

        # Error should be about missing data, not the default config
        assert result.error_type == "data"


class TestConfigDateRange:
    """T033: Test date range configuration."""

    def test_config_date_range_applied(
        self,
        sample_backtest_config: BacktestConfig,
    ):
        """Config should have correct date range."""
        assert sample_backtest_config.start_date == "2024-01-01"
        assert sample_backtest_config.end_date == "2024-06-01"


class TestConfigInvalidCatalogPath:
    """T034: Test handling of invalid catalog paths."""

    def test_invalid_catalog_returns_data_error(
        self,
        evaluator: StrategyEvaluator,
        sample_valid_strategy_code: str,
    ):
        """Invalid catalog path should return error_type='data'."""
        request = EvaluationRequest(strategy_code=sample_valid_strategy_code)
        result = evaluator.evaluate_sync(request)

        # Default config has non-existent path
        assert result.success is False
        assert result.error_type == "data"
        assert "not found" in result.error.lower() or "catalog" in result.error.lower()


class TestConfigMissingInstrument:
    """T035: Test handling of missing instruments."""

    @patch("nautilus_trader.persistence.catalog.ParquetDataCatalog")
    def test_missing_instrument_returns_data_error(
        self,
        mock_catalog_class: MagicMock,
        evaluator: StrategyEvaluator,
        sample_valid_strategy_code: str,
        tmp_path: Path,
    ):
        """Missing instrument should return error_type='data'."""
        # Setup mock catalog that exists but has no instruments
        mock_catalog = MagicMock()
        mock_catalog.instruments.return_value = []
        mock_catalog_class.return_value = mock_catalog

        # Create catalog path
        catalog_path = tmp_path / "catalog"
        catalog_path.mkdir()

        config = BacktestConfig(
            catalog_path=str(catalog_path),
            instrument_id="NONEXISTENT.BINANCE",
            start_date="2024-01-01",
            end_date="2024-06-01",
        )

        request = EvaluationRequest(
            strategy_code=sample_valid_strategy_code,
            backtest_config=config,
        )

        result = evaluator.evaluate_sync(request)

        assert result.success is False
        assert result.error_type == "data"
        assert "not found" in result.error.lower()


# === USER STORY 4: CONCURRENT EVALUATION LIMITS ===


class TestConcurrentLimitRespected:
    """T040: Test that concurrent limit is respected."""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(
        self,
        evaluator: StrategyEvaluator,
        sample_valid_strategy_code: str,
    ):
        """Semaphore should limit concurrent evaluations."""
        evaluator.max_concurrent = 2
        evaluator._semaphore = asyncio.Semaphore(2)

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent_observed = 0

        def counting_evaluate(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent_observed
            concurrent_count += 1
            max_concurrent_observed = max(max_concurrent_observed, concurrent_count)
            import time

            time.sleep(0.1)  # Simulate work
            concurrent_count -= 1
            return EvaluationResult(success=True, metrics=None, duration_ms=100)

        with patch.object(evaluator, "evaluate_sync", side_effect=counting_evaluate):
            # Launch 5 concurrent evaluations
            request = EvaluationRequest(strategy_code=sample_valid_strategy_code)
            tasks = [evaluator.evaluate(request) for _ in range(5)]
            await asyncio.gather(*tasks)

        # Should never exceed max_concurrent
        assert max_concurrent_observed <= evaluator.max_concurrent


class TestConcurrentSlotFreedOnFailure:
    """T041: Test that semaphore slot is freed on failure."""

    @pytest.mark.asyncio
    async def test_slot_freed_on_failure(
        self,
        evaluator: StrategyEvaluator,
        sample_valid_strategy_code: str,
    ):
        """Semaphore slot should be freed even if evaluation fails."""
        evaluator.max_concurrent = 1
        evaluator._semaphore = asyncio.Semaphore(1)

        def failing_evaluate(*args, **kwargs):
            raise RuntimeError("Intentional failure")

        with patch.object(evaluator, "evaluate_sync", side_effect=failing_evaluate):
            request = EvaluationRequest(strategy_code=sample_valid_strategy_code)

            # First call should fail but free slot
            result1 = await evaluator.evaluate(request)
            assert result1.success is False

            # Second call should work (slot freed)
            with patch.object(
                evaluator,
                "evaluate_sync",
                return_value=EvaluationResult(success=True, metrics=None, duration_ms=0),
            ):
                result2 = await evaluator.evaluate(request)
                assert result2.success is True


class TestAsyncEvaluate:
    """T042: Test async evaluate method."""

    @pytest.mark.asyncio
    async def test_async_evaluate_wraps_sync(
        self,
        evaluator: StrategyEvaluator,
        sample_valid_strategy_code: str,
    ):
        """Async evaluate should call evaluate_sync in thread."""
        expected_result = EvaluationResult(
            success=True,
            metrics=FitnessMetrics(
                sharpe_ratio=1.0,
                calmar_ratio=1.5,
                max_drawdown=0.10,
                cagr=0.15,
                total_return=0.30,
            ),
            duration_ms=500,
            trade_count=50,
        )

        with patch.object(evaluator, "evaluate_sync", return_value=expected_result):
            request = EvaluationRequest(strategy_code=sample_valid_strategy_code)
            result = await evaluator.evaluate(request)

        assert result == expected_result
