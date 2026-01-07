"""Test fixtures for adaptive_control tests."""
import numpy as np
import pytest


@pytest.fixture
def simple_returns():
    """Simple returns for basic testing."""
    return [0.01, -0.02, 0.015, -0.01, 0.02, -0.015, 0.01, 0.02, -0.01, 0.005]


@pytest.fixture
def trending_returns():
    """Returns with strong trend (brown noise)."""
    np.random.seed(42)
    trend = np.linspace(0, 0.1, 100)
    noise = np.random.normal(0, 0.005, 100)
    prices = 100 * np.exp(np.cumsum(trend + noise))
    returns = np.diff(prices) / prices[:-1]
    return returns.tolist()


@pytest.fixture
def mean_reverting_returns():
    """Returns with mean reversion (white noise)."""
    np.random.seed(42)
    return np.random.normal(0, 0.01, 100).tolist()


@pytest.fixture
def volatile_returns():
    """High volatility returns."""
    np.random.seed(42)
    base = np.random.normal(0, 0.05, 100)
    # Add volatility spikes
    base[20:25] *= 3
    base[50:55] *= 3
    base[80:85] *= 3
    return base.tolist()


@pytest.fixture
def low_volatility_returns():
    """Low volatility returns."""
    np.random.seed(42)
    return np.random.normal(0, 0.002, 100).tolist()
