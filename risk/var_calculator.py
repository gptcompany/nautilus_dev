"""
Value at Risk (VaR) Calculator Module.

Provides multiple VaR calculation methods following industry standards:
- Historical VaR (percentile-based)
- Parametric VaR (assuming normal distribution)
- Conditional VaR / Expected Shortfall (CVaR)

Reference: Basel III framework, QuantLib methodology.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def calculate_historical_var(
    returns: np.ndarray,
    confidence: float = 0.95,
    portfolio_value: float | None = None,
) -> float:
    """
    Calculate Historical VaR using the percentile method.

    This is a non-parametric approach that makes no assumptions about
    the underlying distribution of returns.

    Args:
        returns: Array of historical returns (as decimals, e.g., 0.01 for 1%).
        confidence: Confidence level (default 95%).
        portfolio_value: Optional portfolio value to return VaR in currency units.

    Returns:
        VaR as a positive number (potential loss).
        If portfolio_value provided, returns currency amount; otherwise returns percentage.

    Example:
        >>> returns = np.array([-0.02, 0.01, -0.03, 0.02, -0.01, 0.03, -0.015])
        >>> var = calculate_historical_var(returns, confidence=0.95)
        >>> print(f"95% VaR: {var:.2%}")
    """
    if len(returns) == 0:
        return 0.0

    var_percentile = -np.percentile(returns, (1 - confidence) * 100)

    if portfolio_value is not None:
        return var_percentile * portfolio_value

    return var_percentile


def calculate_parametric_var(
    returns: np.ndarray,
    confidence: float = 0.95,
    portfolio_value: float | None = None,
) -> float:
    """
    Calculate Parametric VaR assuming normal distribution.

    Also known as Variance-Covariance VaR. Assumes returns follow
    a normal distribution and uses mean/std to estimate VaR.

    Args:
        returns: Array of historical returns (as decimals).
        confidence: Confidence level (default 95%).
        portfolio_value: Optional portfolio value to return VaR in currency units.

    Returns:
        VaR as a positive number (potential loss).

    Note:
        This method may underestimate tail risk for fat-tailed distributions.
        Consider using Historical VaR or CVaR for more conservative estimates.
    """
    if len(returns) == 0:
        return 0.0

    mu = np.mean(returns)
    sigma = np.std(returns, ddof=1)  # Sample std with Bessel's correction

    # Z-score for the given confidence level
    z_score = stats.norm.ppf(1 - confidence)

    var = -(mu + z_score * sigma)

    if portfolio_value is not None:
        return var * portfolio_value

    return var


def calculate_cvar(
    returns: np.ndarray,
    confidence: float = 0.95,
    portfolio_value: float | None = None,
) -> float:
    """
    Calculate Conditional VaR (Expected Shortfall).

    CVaR represents the expected loss given that the loss exceeds VaR.
    It's a coherent risk measure (unlike VaR) and better captures tail risk.

    Args:
        returns: Array of historical returns (as decimals).
        confidence: Confidence level (default 95%).
        portfolio_value: Optional portfolio value to return CVaR in currency units.

    Returns:
        CVaR as a positive number (expected loss beyond VaR).

    Note:
        CVaR is always >= VaR. It's recommended by Basel III for internal
        risk models as it better captures extreme tail events.
    """
    if len(returns) == 0:
        return 0.0

    var = calculate_historical_var(returns, confidence)
    # Get returns that exceed VaR (worst cases)
    tail_returns = returns[returns <= -var]

    if len(tail_returns) == 0:
        return var  # Fallback to VaR if no tail losses

    cvar = -np.mean(tail_returns)

    if portfolio_value is not None:
        return cvar * portfolio_value

    return cvar


def calculate_marginal_var(
    portfolio_returns: np.ndarray,
    position_returns: np.ndarray,
    confidence: float = 0.95,
) -> float:
    """
    Calculate Marginal VaR for a position within a portfolio.

    Measures how much VaR would change with a small increase in position size.
    Useful for position sizing and risk attribution.

    Args:
        portfolio_returns: Array of portfolio returns.
        position_returns: Array of individual position returns.
        confidence: Confidence level (default 95%).

    Returns:
        Marginal VaR contribution of the position.
    """
    if len(portfolio_returns) == 0 or len(position_returns) == 0:
        return 0.0

    portfolio_var = calculate_historical_var(portfolio_returns, confidence)
    correlation = np.corrcoef(portfolio_returns, position_returns)[0, 1]
    position_std = np.std(position_returns, ddof=1)
    portfolio_std = np.std(portfolio_returns, ddof=1)

    if portfolio_std == 0:
        return 0.0

    return portfolio_var * correlation * position_std / portfolio_std


def calculate_component_var(
    portfolio_returns: np.ndarray,
    position_returns: np.ndarray,
    position_weight: float,
    confidence: float = 0.95,
) -> float:
    """
    Calculate Component VaR for a position.

    Decomposes portfolio VaR into contributions from each position.
    Sum of all Component VaRs equals total portfolio VaR.

    Args:
        portfolio_returns: Array of portfolio returns.
        position_returns: Array of individual position returns.
        position_weight: Weight of position in portfolio (0-1).
        confidence: Confidence level (default 95%).

    Returns:
        Component VaR contribution of the position.
    """
    marginal_var = calculate_marginal_var(portfolio_returns, position_returns, confidence)
    return marginal_var * position_weight


def calculate_rolling_var(
    returns: np.ndarray,
    window: int = 30,
    confidence: float = 0.95,
) -> np.ndarray:
    """
    Calculate rolling VaR over a specified window.

    Useful for monitoring VaR evolution over time.

    Args:
        returns: Array of historical returns.
        window: Rolling window size in periods (default 30).
        confidence: Confidence level (default 95%).

    Returns:
        Array of rolling VaR values (NaN for initial window-1 periods).
    """
    n = len(returns)
    rolling_var = np.full(n, np.nan)

    for i in range(window - 1, n):
        window_returns = returns[i - window + 1 : i + 1]
        rolling_var[i] = calculate_historical_var(window_returns, confidence)

    return rolling_var


class VaRCalculator:
    """
    Comprehensive VaR calculator with multiple methods and caching.

    Example:
        >>> calculator = VaRCalculator(returns, confidence=0.95)
        >>> print(f"Historical VaR: {calculator.historical_var:.2%}")
        >>> print(f"Parametric VaR: {calculator.parametric_var:.2%}")
        >>> print(f"CVaR: {calculator.cvar:.2%}")
    """

    def __init__(
        self,
        returns: np.ndarray,
        confidence: float = 0.95,
        portfolio_value: float | None = None,
    ):
        """
        Initialize VaR calculator.

        Args:
            returns: Historical returns array.
            confidence: Confidence level for VaR calculations.
            portfolio_value: Optional portfolio value for currency-denominated VaR.
        """
        self.returns = np.asarray(returns)
        self.confidence = confidence
        self.portfolio_value = portfolio_value
        self._cache: dict[str, float] = {}

    @property
    def historical_var(self) -> float:
        """Historical VaR (cached)."""
        if "historical" not in self._cache:
            self._cache["historical"] = calculate_historical_var(
                self.returns, self.confidence, self.portfolio_value
            )
        return self._cache["historical"]

    @property
    def parametric_var(self) -> float:
        """Parametric VaR (cached)."""
        if "parametric" not in self._cache:
            self._cache["parametric"] = calculate_parametric_var(
                self.returns, self.confidence, self.portfolio_value
            )
        return self._cache["parametric"]

    @property
    def cvar(self) -> float:
        """Conditional VaR / Expected Shortfall (cached)."""
        if "cvar" not in self._cache:
            self._cache["cvar"] = calculate_cvar(
                self.returns, self.confidence, self.portfolio_value
            )
        return self._cache["cvar"]

    def summary(self) -> dict[str, float]:
        """Return all VaR metrics as a dictionary."""
        return {
            "historical_var": self.historical_var,
            "parametric_var": self.parametric_var,
            "cvar": self.cvar,
            "confidence": self.confidence,
            "n_observations": len(self.returns),
        }
