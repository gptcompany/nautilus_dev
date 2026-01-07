"""
Pytest configuration and shared fixtures for NautilusTrader tests.

This file provides common fixtures used across all test modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path for test discovery
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pandas as pd
import pytest

if TYPE_CHECKING:
    pass


# =============================================================================
# Tearsheet Fixtures (T005, T006)
# =============================================================================


@pytest.fixture
def mock_portfolio_analyzer():
    """
    Create a mock PortfolioAnalyzer with realistic data.

    Returns a mock that simulates 1-year of daily trading data with:
    - 252 trading days
    - Realistic returns distribution
    - Standard performance statistics
    """
    analyzer = MagicMock()

    # Create realistic returns series (1-year daily)
    dates = pd.date_range("2023-01-01", periods=252, freq="D")
    returns = pd.Series(
        data=[0.001 * (i % 10 - 5) for i in range(252)],
        index=dates,
        name="returns",
    )
    analyzer.returns.return_value = returns

    # Mock PnL statistics
    analyzer.get_performance_stats_pnls.return_value = {
        "USDT": {
            "PnL (total)": 1500.50,
            "PnL (realized)": 1500.50,
            "PnL (unrealized)": 0.0,
        }
    }

    # Mock returns statistics
    analyzer.get_performance_stats_returns.return_value = {
        "Sharpe Ratio (252 days)": 1.25,
        "Sortino Ratio (252 days)": 1.85,
        "Calmar Ratio": 2.1,
        "Max Drawdown": -0.12,
        "Avg Drawdown": -0.05,
        "Daily Avg Return": 0.0005,
        "Daily Std Return": 0.015,
    }

    # Mock general statistics
    analyzer.get_performance_stats_general.return_value = {
        "Win Rate": 0.55,
        "Profit Factor": 1.8,
        "Total Trades": 150,
        "Avg Trade Duration": "2h 30m",
        "Avg Winner": 50.0,
        "Avg Loser": -30.0,
        "Largest Winner": 500.0,
        "Largest Loser": -200.0,
    }

    return analyzer


@pytest.fixture
def mock_backtest_engine(mock_portfolio_analyzer) -> MagicMock:
    """
    Create a mock BacktestEngine for testing.

    This fixture provides a mock engine with:
    - Portfolio with PortfolioAnalyzer
    - Cache with positions and orders
    - Trader interface

    Parameters
    ----------
    mock_portfolio_analyzer : MagicMock
        The mock analyzer fixture.

    Returns
    -------
    MagicMock
        Mock BacktestEngine.
    """
    engine = MagicMock()

    # Set up portfolio with analyzer
    engine.portfolio.analyzer = mock_portfolio_analyzer

    # Set up cache with empty collections
    engine.cache.positions.return_value = []
    engine.cache.positions_open.return_value = []
    engine.cache.positions_closed.return_value = []
    engine.cache.orders.return_value = []
    engine.cache.orders_open.return_value = []

    return engine


@pytest.fixture
def mock_engine_with_trades(mock_backtest_engine) -> MagicMock:
    """
    Create a mock BacktestEngine with trade data.

    Returns engine with 100 closed positions.
    """
    positions = []
    for i in range(100):
        position = MagicMock()
        position.is_closed = True
        position.realized_pnl = MagicMock()
        position.realized_pnl.as_double.return_value = 100.0 * (1 if i % 3 != 0 else -1)
        positions.append(position)

    mock_backtest_engine.cache.positions.return_value = positions
    mock_backtest_engine.cache.positions_closed.return_value = positions

    # Update stats to reflect trades
    mock_backtest_engine.portfolio.analyzer.get_performance_stats_general.return_value = {
        "Win Rate": 0.67,
        "Profit Factor": 2.0,
        "Total Trades": 100,
        "Avg Trade Duration": "4h 15m",
    }

    return mock_backtest_engine


@pytest.fixture
def mock_engine_zero_trades(mock_backtest_engine) -> MagicMock:
    """
    Create a mock BacktestEngine with zero trades.

    This is an edge case fixture for testing empty backtest handling.
    """
    mock_backtest_engine.cache.positions.return_value = []
    mock_backtest_engine.cache.positions_closed.return_value = []
    mock_backtest_engine.cache.orders.return_value = []

    mock_backtest_engine.portfolio.analyzer.get_performance_stats_general.return_value = {
        "Total Trades": 0,
        "Win Rate": 0.0,
        "Profit Factor": 0.0,
    }

    # Empty returns
    mock_backtest_engine.portfolio.analyzer.returns.return_value = pd.Series(
        dtype=float, name="returns"
    )

    return mock_backtest_engine


@pytest.fixture
def mock_engine_open_positions(mock_backtest_engine) -> MagicMock:
    """
    Create a mock BacktestEngine with open positions.

    This is an edge case fixture for testing the epoch bug workaround.
    """
    open_position = MagicMock()
    open_position.is_closed = False
    open_position.ts_closed = 0  # Epoch timestamp bug

    mock_backtest_engine.cache.positions_open.return_value = [open_position]

    return mock_backtest_engine


@pytest.fixture
def mock_engine_long_backtest(mock_portfolio_analyzer) -> MagicMock:
    """
    Create a mock BacktestEngine with 10+ years of data.

    This is an edge case fixture for testing ScatterGL handling.
    """
    engine = MagicMock()
    engine.portfolio.analyzer = mock_portfolio_analyzer

    # Override with 10+ years of data (2520 trading days)
    dates = pd.date_range("2010-01-01", periods=2520, freq="D")
    returns = pd.Series(
        data=[0.0005 * (i % 20 - 10) for i in range(2520)],
        index=dates,
        name="returns",
    )
    engine.portfolio.analyzer.returns.return_value = returns

    engine.cache.positions.return_value = []
    engine.cache.positions_open.return_value = []

    return engine


@pytest.fixture
def mock_engine_high_frequency(mock_portfolio_analyzer) -> MagicMock:
    """
    Create a mock BacktestEngine with high-frequency trading data.

    This is an edge case fixture for testing trade aggregation.
    """
    engine = MagicMock()
    engine.portfolio.analyzer = mock_portfolio_analyzer

    # 1000+ trades per day simulation
    positions = []
    for i in range(5000):  # ~5 days of 1000 trades/day
        position = MagicMock()
        position.is_closed = True
        position.realized_pnl = MagicMock()
        position.realized_pnl.as_double.return_value = 10.0 * (1 if i % 2 == 0 else -1)
        positions.append(position)

    engine.cache.positions.return_value = positions
    engine.cache.positions_closed.return_value = positions
    engine.cache.positions_open.return_value = []

    engine.portfolio.analyzer.get_performance_stats_general.return_value = {
        "Total Trades": 5000,
        "Win Rate": 0.50,
        "Profit Factor": 1.0,
    }

    return engine


# =============================================================================
# Pytest Configuration
# =============================================================================


# =============================================================================
# Recovery Fixtures (Spec 017)
# =============================================================================


@pytest.fixture
def recovery_config():
    """Create a default RecoveryConfig for testing."""
    from strategies.common.recovery.config import RecoveryConfig

    return RecoveryConfig(
        trader_id="TESTER-001",
        recovery_enabled=True,
        warmup_lookback_days=2,
        startup_delay_secs=10.0,
        max_recovery_time_secs=30.0,
        claim_external_positions=True,
    )


@pytest.fixture
def position_snapshot():
    """Create a sample PositionSnapshot for testing."""
    from decimal import Decimal

    from strategies.common.recovery.models import PositionSnapshot

    return PositionSnapshot(
        instrument_id="BTCUSDT-PERP.BINANCE",
        side="LONG",
        quantity=Decimal("1.5"),
        avg_entry_price=Decimal("42000.00"),
        unrealized_pnl=Decimal("500.00"),
        realized_pnl=Decimal("0.00"),
        ts_opened=1704067200000000000,  # 2024-01-01 00:00:00 UTC
        ts_last_updated=1704153600000000000,  # 2024-01-02 00:00:00 UTC
    )


@pytest.fixture
def recovery_state_pending():
    """Create a pending RecoveryState for testing."""
    from strategies.common.recovery.models import RecoveryState, RecoveryStatus

    return RecoveryState(
        status=RecoveryStatus.PENDING,
        positions_recovered=0,
        indicators_warmed=False,
        orders_reconciled=False,
    )


@pytest.fixture
def recovery_state_complete():
    """Create a completed RecoveryState for testing."""
    from strategies.common.recovery.models import RecoveryState, RecoveryStatus

    return RecoveryState(
        status=RecoveryStatus.COMPLETED,
        positions_recovered=2,
        indicators_warmed=True,
        orders_reconciled=True,
        ts_started=1704067200000000000,
        ts_completed=1704067205000000000,  # 5 seconds later
    )


@pytest.fixture
def mock_cache():
    """Create a mock NautilusTrader cache for testing."""
    cache = MagicMock()
    cache.positions.return_value = []
    cache.positions_open.return_value = []
    cache.orders_open.return_value = []
    cache.account.return_value = None
    return cache


@pytest.fixture
def mock_clock():
    """Create a mock clock for testing."""
    clock = MagicMock()
    clock.timestamp_ns.return_value = 1704153600000000000
    from datetime import datetime, timezone

    clock.utc_now.return_value = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    return clock


# =============================================================================
# Meta-Learning Fixtures (Spec 026)
# =============================================================================


@pytest.fixture
def sample_price_series():
    """Generate a synthetic price series for testing.

    Returns 500 bars of simulated price data with trend and noise.
    """
    import numpy as np

    np.random.seed(42)
    n = 500
    # Random walk with drift
    returns = np.random.normal(0.0002, 0.02, n)
    prices = 100 * np.exp(np.cumsum(returns))
    return prices.astype(np.float64)


@pytest.fixture
def sample_atr_values(sample_price_series):
    """Generate synthetic ATR values based on price series."""
    import numpy as np

    # Approximate ATR as 2% of price
    atr = sample_price_series * 0.02
    # Add some noise
    atr = atr * (1 + np.random.normal(0, 0.1, len(atr)))
    return np.abs(atr).astype(np.float64)


@pytest.fixture
def sample_signals():
    """Generate synthetic trading signals for testing."""
    import numpy as np

    np.random.seed(42)
    n = 500
    # Random signals: +1 (long), -1 (short), 0 (no signal)
    signals = np.random.choice([-1, 0, 1], size=n, p=[0.2, 0.6, 0.2])
    return signals.astype(np.int64)


@pytest.fixture
def sample_labels():
    """Generate synthetic triple barrier labels for testing."""
    import numpy as np

    np.random.seed(42)
    n = 500
    # Labels: +1 (take profit), -1 (stop loss), 0 (timeout)
    labels = np.random.choice([-1, 0, 1], size=n, p=[0.3, 0.2, 0.5])
    return labels.astype(np.int64)


@pytest.fixture
def sample_meta_features():
    """Generate synthetic features for meta-model testing.

    Returns (n_samples, n_features) array with 6 features:
    - volatility, volume_ratio, momentum, regime_state, signal_strength, drawdown
    """
    import numpy as np

    np.random.seed(42)
    n = 500
    features = np.column_stack(
        [
            np.random.uniform(0.01, 0.05, n),  # volatility
            np.random.uniform(0.5, 2.0, n),  # volume_ratio
            np.random.uniform(-0.1, 0.1, n),  # momentum
            np.random.randint(0, 3, n),  # regime_state
            np.random.uniform(0, 1, n),  # signal_strength
            np.random.uniform(-0.2, 0, n),  # drawdown
        ]
    )
    return features.astype(np.float64)


@pytest.fixture
def sample_returns():
    """Generate synthetic returns series for BOCD testing.

    Returns 1000 observations with two regime changes.
    """
    import numpy as np

    np.random.seed(42)
    # Regime 1: Low volatility (0-300)
    regime1 = np.random.normal(0.0001, 0.01, 300)
    # Regime 2: High volatility (300-700)
    regime2 = np.random.normal(-0.0002, 0.03, 400)
    # Regime 3: Medium volatility (700-1000)
    regime3 = np.random.normal(0.0001, 0.015, 300)
    return np.concatenate([regime1, regime2, regime3]).astype(np.float64)


@pytest.fixture
def triple_barrier_config():
    """Create default TripleBarrierConfig for testing."""
    from strategies.common.labeling.config import TripleBarrierConfig

    return TripleBarrierConfig(
        pt_multiplier=2.0,
        sl_multiplier=1.0,
        max_holding_bars=10,
        atr_period=14,
    )


@pytest.fixture
def meta_model_config():
    """Create default MetaModelConfig for testing."""
    from strategies.common.meta_learning.config import MetaModelConfig

    return MetaModelConfig(
        n_estimators=50,  # Reduced for faster tests
        max_depth=3,
        random_state=42,
    )


@pytest.fixture
def walk_forward_config():
    """Create default WalkForwardConfig for testing."""
    from strategies.common.meta_learning.config import WalkForwardConfig

    return WalkForwardConfig(
        train_window=100,  # Reduced for testing
        test_window=25,
        step_size=10,
        embargo_size=2,
    )


@pytest.fixture
def bocd_config():
    """Create default BOCDConfig for testing."""
    from strategies.common.regime_detection.config import BOCDConfig

    return BOCDConfig(
        hazard_rate=0.01,  # Higher for testing (expect changes more often)
        detection_threshold=0.5,  # Lower for testing
    )


@pytest.fixture
def integrated_sizing_config():
    """Create default IntegratedSizingConfig for testing."""
    from strategies.common.position_sizing.config import IntegratedSizingConfig

    return IntegratedSizingConfig(
        giller_exponent=0.5,
        fractional_kelly=0.5,
        min_size=0.01,
        max_size=1.0,
    )


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (may require external resources)",
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "visualization: mark test as requiring visualization extra")
    config.addinivalue_line("markers", "recovery: mark test as recovery module test (Spec 017)")
    config.addinivalue_line(
        "markers", "meta_learning: mark test as meta-learning pipeline test (Spec 026)"
    )
