"""
Transaction Cost Modeling (MVP - ROI 5.0)

Realistic transaction cost modeling for backtests.

Zero-fee backtests are unrealistic. A strategy with Sharpe 2.0 in backtest
may have Sharpe 0.5 in live trading due to costs. This module provides:

- P2 (Non-linear): Slippage scales with sqrt(size) - power law behavior
- P4 (Scale-invariant): Different cost profiles for different timeframes

Cost components:
1. Commission: Fixed percentage of notional
2. Spread: Half bid-ask spread
3. Slippage: Market impact (scales non-linearly with size and volatility)

Reference:
- Almgren & Chriss (2000): "Optimal Execution of Portfolio Transactions"
- Kissell & Glantz (2003): "Optimal Trading Strategies"
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Exchange(Enum):
    """Supported exchanges with default cost profiles."""

    BINANCE_SPOT = "binance_spot"
    BINANCE_FUTURES = "binance_futures"
    BYBIT_FUTURES = "bybit_futures"
    HYPERLIQUID = "hyperliquid"
    GENERIC = "generic"


@dataclass
class CostProfile:
    """Transaction cost profile for an exchange/venue."""

    name: str
    commission_rate: float  # Percentage (e.g., 0.0004 = 4 bps)
    spread_bps: float  # Half spread in basis points
    slippage_base_bps: float  # Base slippage in basis points
    slippage_vol_sensitivity: float  # How much slippage increases with volatility
    slippage_size_exponent: float  # Power law exponent for size impact (typically 0.5)

    def __post_init__(self):
        if self.slippage_size_exponent <= 0:
            raise ValueError("slippage_size_exponent must be positive")


# Pre-configured cost profiles
COST_PROFILES: dict[Exchange, CostProfile] = {
    Exchange.BINANCE_SPOT: CostProfile(
        name="Binance Spot",
        commission_rate=0.001,  # 10 bps maker/taker
        spread_bps=1.0,
        slippage_base_bps=2.0,
        slippage_vol_sensitivity=1.0,
        slippage_size_exponent=0.5,
    ),
    Exchange.BINANCE_FUTURES: CostProfile(
        name="Binance Futures",
        commission_rate=0.0004,  # 4 bps maker/taker
        spread_bps=0.5,
        slippage_base_bps=1.5,
        slippage_vol_sensitivity=1.0,
        slippage_size_exponent=0.5,
    ),
    Exchange.BYBIT_FUTURES: CostProfile(
        name="Bybit Futures",
        commission_rate=0.0006,  # 6 bps
        spread_bps=0.5,
        slippage_base_bps=1.5,
        slippage_vol_sensitivity=1.0,
        slippage_size_exponent=0.5,
    ),
    Exchange.HYPERLIQUID: CostProfile(
        name="Hyperliquid",
        commission_rate=0.00025,  # 2.5 bps maker, 5 bps taker
        spread_bps=0.3,
        slippage_base_bps=1.0,
        slippage_vol_sensitivity=0.8,
        slippage_size_exponent=0.5,
    ),
    Exchange.GENERIC: CostProfile(
        name="Generic (Conservative)",
        commission_rate=0.001,  # 10 bps
        spread_bps=2.0,
        slippage_base_bps=3.0,
        slippage_vol_sensitivity=1.5,
        slippage_size_exponent=0.5,
    ),
}


@dataclass
class TransactionCost:
    """Breakdown of transaction costs."""

    total: float  # Total cost in base currency
    commission: float
    spread: float
    slippage: float
    notional: float  # Original notional value
    cost_bps: float  # Total cost in basis points


class TransactionCostModel:
    """
    Realistic transaction cost model.

    Includes:
    - Commission: Fixed percentage
    - Spread: Half bid-ask spread
    - Slippage: Market impact with power-law scaling

    Slippage formula (P2 alignment - power law):
        slippage = base_slippage * (volatility / ref_vol)^vol_sensitivity * (size / ref_size)^size_exponent

    The square root scaling (exponent=0.5) comes from market microstructure theory:
    - Almgren-Chriss model shows market impact ~ sqrt(participation rate)
    - This is empirically validated across many markets

    Usage:
        model = TransactionCostModel(exchange=Exchange.BINANCE_FUTURES)

        # Calculate cost for a trade
        cost = model.calculate(
            notional=10000,  # $10,000 trade
            volatility=0.02,  # 2% daily volatility
        )
        print(f"Total cost: ${cost.total:.2f} ({cost.cost_bps:.1f} bps)")

        # Adjust Sharpe ratio for costs
        gross_sharpe = 2.0
        net_sharpe = model.adjust_sharpe(
            gross_sharpe=gross_sharpe,
            avg_notional=10000,
            trades_per_year=500,
            volatility=0.02,
        )
        print(f"Net Sharpe after costs: {net_sharpe:.2f}")
    """

    def __init__(
        self,
        exchange: Exchange = Exchange.GENERIC,
        profile: CostProfile | None = None,
        reference_volatility: float = 0.02,  # 2% daily vol as reference
        reference_size: float = 10000,  # $10k as reference size
    ):
        """
        Args:
            exchange: Pre-configured exchange to use
            profile: Custom cost profile (overrides exchange)
            reference_volatility: Reference volatility for scaling
            reference_size: Reference size for scaling
        """
        self.profile = profile or COST_PROFILES[exchange]
        self.ref_vol = reference_volatility
        self.ref_size = reference_size

    def calculate(
        self,
        notional: float,
        volatility: float = 0.02,
        is_market_order: bool = True,
    ) -> TransactionCost:
        """
        Calculate transaction costs for a trade.

        Args:
            notional: Trade notional value in base currency
            volatility: Current volatility (daily, as decimal)
            is_market_order: Whether this is a market order (adds spread)

        Returns:
            TransactionCost with breakdown
        """
        if notional <= 0:
            return TransactionCost(
                total=0.0,
                commission=0.0,
                spread=0.0,
                slippage=0.0,
                notional=0.0,
                cost_bps=0.0,
            )

        # 1. Commission (linear)
        commission = notional * self.profile.commission_rate

        # 2. Spread (linear, only for market orders)
        spread = 0.0
        if is_market_order:
            spread = notional * self.profile.spread_bps / 10000

        # 3. Slippage (non-linear - P2 power law)
        # slippage = base * (vol/ref_vol)^sensitivity * (size/ref_size)^exponent
        vol_factor = (volatility / self.ref_vol) ** self.profile.slippage_vol_sensitivity
        size_factor = (notional / self.ref_size) ** self.profile.slippage_size_exponent

        slippage = notional * self.profile.slippage_base_bps / 10000 * vol_factor * size_factor

        total = commission + spread + slippage
        cost_bps = (total / notional) * 10000 if notional > 0 else 0.0

        return TransactionCost(
            total=total,
            commission=commission,
            spread=spread,
            slippage=slippage,
            notional=notional,
            cost_bps=cost_bps,
        )

    def adjust_sharpe(
        self,
        gross_sharpe: float,
        avg_notional: float,
        trades_per_year: int,
        volatility: float = 0.02,
        account_size: float = 100000,
    ) -> float:
        """
        Adjust gross Sharpe ratio for transaction costs.

        This is crucial for realistic backtest evaluation.

        Args:
            gross_sharpe: Sharpe ratio before costs
            avg_notional: Average trade notional
            trades_per_year: Number of trades per year
            volatility: Average volatility
            account_size: Account size for return calculation

        Returns:
            Net Sharpe ratio after costs
        """
        # Calculate total annual costs
        cost_per_trade = self.calculate(avg_notional, volatility)
        annual_costs = cost_per_trade.total * trades_per_year

        # Annual cost as % of account
        annual_cost_pct = annual_costs / account_size

        # Adjust Sharpe
        # SR = (Return - Risk_Free) / Vol
        # New_SR ≈ SR - (Annual_Cost% / Vol)
        # Assuming ~16% annual volatility (typical for crypto)
        annual_vol = 0.16

        sharpe_reduction = annual_cost_pct / annual_vol
        net_sharpe = gross_sharpe - sharpe_reduction

        return max(net_sharpe, -10.0)  # Cap at -10

    def get_breakeven_sharpe(
        self,
        avg_notional: float,
        trades_per_year: int,
        volatility: float = 0.02,
        account_size: float = 100000,
    ) -> float:
        """
        Calculate minimum gross Sharpe needed to break even after costs.

        A strategy with gross Sharpe below this is guaranteed to lose money.

        Args:
            avg_notional: Average trade notional
            trades_per_year: Number of trades per year
            volatility: Average volatility
            account_size: Account size

        Returns:
            Minimum gross Sharpe ratio to break even
        """
        return (
            self.adjust_sharpe(
                gross_sharpe=0.0,
                avg_notional=avg_notional,
                trades_per_year=trades_per_year,
                volatility=volatility,
                account_size=account_size,
            )
            * -1
        )  # Negate because we want the cost as positive Sharpe


class BacktestCostAdjuster:
    """
    Adjust backtest returns for transaction costs.

    Usage:
        adjuster = BacktestCostAdjuster(exchange=Exchange.BINANCE_FUTURES)

        # Adjust each trade's return
        adjusted_returns = []
        for trade in trades:
            adjusted = adjuster.adjust_return(
                gross_return=trade.return_pct,
                notional=trade.notional,
                volatility=trade.volatility,
            )
            adjusted_returns.append(adjusted)

        # Or adjust in batch
        adjusted = adjuster.adjust_returns_batch(
            gross_returns=[0.02, -0.01, 0.03],
            notionals=[10000, 15000, 8000],
            volatility=0.02,
        )
    """

    def __init__(
        self,
        exchange: Exchange = Exchange.GENERIC,
        include_entry: bool = True,
        include_exit: bool = True,
    ):
        """
        Args:
            exchange: Exchange cost profile to use
            include_entry: Include entry costs
            include_exit: Include exit costs
        """
        self.model = TransactionCostModel(exchange=exchange)
        self.include_entry = include_entry
        self.include_exit = include_exit

    def adjust_return(
        self,
        gross_return: float,
        notional: float,
        volatility: float = 0.02,
    ) -> float:
        """
        Adjust a single trade's return for costs.

        Args:
            gross_return: Gross return as decimal (e.g., 0.02 = 2%)
            notional: Trade notional value
            volatility: Current volatility

        Returns:
            Net return after costs
        """
        cost = self.model.calculate(notional, volatility)

        # Double cost if both entry and exit
        multiplier = (1 if self.include_entry else 0) + (1 if self.include_exit else 0)
        total_cost = cost.total * multiplier

        # Cost as return %
        cost_return = total_cost / notional if notional > 0 else 0.0

        return gross_return - cost_return

    def adjust_returns_batch(
        self,
        gross_returns: list[float],
        notionals: list[float],
        volatility: float = 0.02,
    ) -> list[float]:
        """
        Adjust multiple returns for costs.

        Args:
            gross_returns: List of gross returns
            notionals: List of notional values
            volatility: Volatility (same for all or list)

        Returns:
            List of net returns
        """
        if len(gross_returns) != len(notionals):
            raise ValueError("gross_returns and notionals must have same length")

        return [
            self.adjust_return(r, n, volatility)
            for r, n in zip(gross_returns, notionals, strict=True)
        ]

    def estimate_annual_drag(
        self,
        avg_notional: float,
        trades_per_year: int,
        volatility: float = 0.02,
        account_size: float = 100000,
    ) -> float:
        """
        Estimate annual performance drag from transaction costs.

        Args:
            avg_notional: Average trade notional
            trades_per_year: Expected trades per year
            volatility: Average volatility
            account_size: Account size

        Returns:
            Annual drag as percentage (e.g., 0.05 = 5% annual drag)
        """
        cost = self.model.calculate(avg_notional, volatility)

        # Entry + Exit per trade
        multiplier = (1 if self.include_entry else 0) + (1 if self.include_exit else 0)
        cost_per_trade = cost.total * multiplier

        annual_cost = cost_per_trade * trades_per_year
        return annual_cost / account_size


def get_recommended_profile(
    avg_trade_size: float,
    expected_vol: float = 0.02,
    is_crypto: bool = True,
) -> CostProfile:
    """
    Get recommended cost profile based on trading characteristics.

    More conservative for:
    - Larger trades (more slippage)
    - Higher volatility (more slippage)
    - Unknown markets

    Args:
        avg_trade_size: Average trade size in USD
        expected_vol: Expected daily volatility
        is_crypto: Whether trading crypto (vs tradfi)

    Returns:
        Recommended CostProfile
    """
    # Start with generic profile
    base = COST_PROFILES[Exchange.GENERIC]

    # Adjust for large trades
    if avg_trade_size > 100000:
        # More conservative slippage for large trades
        return CostProfile(
            name="Large Trade Conservative",
            commission_rate=base.commission_rate,
            spread_bps=base.spread_bps * 1.5,
            slippage_base_bps=base.slippage_base_bps * 2.0,
            slippage_vol_sensitivity=base.slippage_vol_sensitivity * 1.2,
            slippage_size_exponent=0.6,  # More aggressive size scaling
        )

    # Adjust for high volatility
    if expected_vol > 0.05:  # >5% daily vol
        return CostProfile(
            name="High Volatility Conservative",
            commission_rate=base.commission_rate,
            spread_bps=base.spread_bps * 2.0,
            slippage_base_bps=base.slippage_base_bps * 1.5,
            slippage_vol_sensitivity=1.5,
            slippage_size_exponent=base.slippage_size_exponent,
        )

    # Default based on market type
    if is_crypto:
        return COST_PROFILES[Exchange.BINANCE_FUTURES]
    else:
        return base
