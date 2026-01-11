#!/usr/bin/env python3
"""
Trading Risk Controls Module.

MANDATORY security layer for all trading operations.
Enforces position limits, loss limits, leverage caps, and withdrawal controls.

Usage:
    from trading.risk_controls import TradingRiskManager, RiskLimits

    # Initialize with custom limits
    limits = RiskLimits(
        max_position_pct=10.0,
        max_daily_loss_pct=3.0,
        max_leverage=3.0,
    )
    risk_manager = TradingRiskManager(limits=limits)

    # Check order before submission
    result = risk_manager.check_order(order)
    if not result.allowed:
        print(f"Order blocked: {result.reason}")

    # Auto-halt check
    if risk_manager.should_halt_trading():
        print("Trading halted due to risk limits")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RiskViolationType(Enum):
    """Types of risk limit violations."""

    POSITION_SIZE = "position_size_exceeded"
    DAILY_LOSS = "daily_loss_exceeded"
    LEVERAGE = "leverage_exceeded"
    ORDER_SIZE = "order_size_exceeded"
    ORDER_RATE = "order_rate_exceeded"
    WITHDRAWAL_NOT_WHITELISTED = "withdrawal_not_whitelisted"
    WITHDRAWAL_DELAY = "withdrawal_delay_required"
    TRADING_HALTED = "trading_halted"


@dataclass
class RiskLimits:
    """
    Risk limit configuration.

    All values can be overridden via environment variables.
    """

    # Position limits (% of equity)
    max_position_pct: float = field(
        default_factory=lambda: float(os.getenv("RISK_MAX_POSITION_PCT", "10.0"))
    )
    max_single_position_pct: float = field(
        default_factory=lambda: float(os.getenv("RISK_MAX_SINGLE_POSITION_PCT", "5.0"))
    )

    # Loss limits (% of equity)
    max_daily_loss_pct: float = field(
        default_factory=lambda: float(os.getenv("RISK_MAX_DAILY_LOSS_PCT", "3.0"))
    )
    max_weekly_loss_pct: float = field(
        default_factory=lambda: float(os.getenv("RISK_MAX_WEEKLY_LOSS_PCT", "10.0"))
    )

    # Leverage limits
    max_leverage: float = field(
        default_factory=lambda: float(os.getenv("RISK_MAX_LEVERAGE", "3.0"))
    )

    # Order limits
    max_order_value_usd: float = field(
        default_factory=lambda: float(os.getenv("RISK_MAX_ORDER_VALUE_USD", "100000"))
    )
    max_orders_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RISK_MAX_ORDERS_PER_MINUTE", "60"))
    )
    max_open_orders_per_symbol: int = field(
        default_factory=lambda: int(os.getenv("RISK_MAX_OPEN_ORDERS_PER_SYMBOL", "20"))
    )

    # Withdrawal controls
    withdrawal_whitelist_enabled: bool = field(
        default_factory=lambda: os.getenv("RISK_WITHDRAWAL_WHITELIST", "true").lower() == "true"
    )
    withdrawal_delay_hours_new_address: int = field(
        default_factory=lambda: int(os.getenv("RISK_WITHDRAWAL_DELAY_HOURS", "24"))
    )
    max_withdrawal_usd_per_day: float = field(
        default_factory=lambda: float(os.getenv("RISK_MAX_WITHDRAWAL_USD_DAY", "50000"))
    )

    # Auto-halt configuration
    auto_halt_on_loss_limit: bool = True
    halt_cooldown_hours: int = field(
        default_factory=lambda: int(os.getenv("RISK_HALT_COOLDOWN_HOURS", "4"))
    )


@dataclass
class RiskCheckResult:
    """Result of a risk check."""

    allowed: bool
    violation_type: RiskViolationType | None = None
    reason: str = ""
    current_value: float = 0.0
    limit_value: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def allowed_result(cls) -> RiskCheckResult:
        return cls(allowed=True)

    @classmethod
    def blocked(
        cls,
        violation_type: RiskViolationType,
        reason: str,
        current: float = 0.0,
        limit: float = 0.0,
        **metadata: Any,
    ) -> RiskCheckResult:
        return cls(
            allowed=False,
            violation_type=violation_type,
            reason=reason,
            current_value=current,
            limit_value=limit,
            metadata=metadata,
        )


@dataclass
class Order:
    """Order representation for risk checks."""

    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    price: float | None = None  # None for market orders
    order_type: str = "limit"
    leverage: float = 1.0

    @property
    def value_usd(self) -> float:
        """Estimated order value in USD."""
        if self.price:
            return self.quantity * self.price
        return 0.0  # Market orders need external price


@dataclass
class PortfolioState:
    """Current portfolio state for risk calculations."""

    equity: float
    total_position_value: float
    positions: dict[str, float] = field(default_factory=dict)  # symbol -> value
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    current_leverage: float = 1.0
    open_orders: dict[str, int] = field(default_factory=dict)  # symbol -> count
    recent_order_timestamps: list[datetime] = field(default_factory=list)


class TradingRiskManager:
    """
    Central risk management for trading operations.

    Enforces all configured limits and can automatically halt trading
    when critical limits are breached.
    """

    def __init__(
        self,
        limits: RiskLimits | None = None,
        on_violation: Any | None = None,  # Callback(RiskCheckResult)
    ):
        """
        Initialize risk manager.

        Args:
            limits: Risk limit configuration (uses defaults if not provided)
            on_violation: Optional callback for risk violations
        """
        self.limits = limits or RiskLimits()
        self.on_violation = on_violation

        # State tracking
        self._trading_halted = False
        self._halt_timestamp: datetime | None = None
        self._halt_reason: str = ""
        self._withdrawal_whitelist: set[str] = set()
        self._pending_whitelist: dict[str, datetime] = {}  # address -> added_at

        # Load whitelist from environment
        self._load_whitelist()

        logger.info(
            f"TradingRiskManager initialized: "
            f"max_position={self.limits.max_position_pct}%, "
            f"max_loss={self.limits.max_daily_loss_pct}%, "
            f"max_leverage={self.limits.max_leverage}x"
        )

    def _load_whitelist(self) -> None:
        """Load withdrawal whitelist from environment."""
        whitelist_str = os.getenv("WITHDRAWAL_WHITELIST_ADDRESSES", "")
        if whitelist_str:
            self._withdrawal_whitelist = {
                addr.strip().lower() for addr in whitelist_str.split(",") if addr.strip()
            }
            logger.info(f"Loaded {len(self._withdrawal_whitelist)} whitelisted addresses")

    # =========================================================================
    # Order Risk Checks
    # =========================================================================

    def check_order(self, order: Order, portfolio: PortfolioState) -> RiskCheckResult:
        """
        Check if an order is allowed under current risk limits.

        Args:
            order: The order to check
            portfolio: Current portfolio state

        Returns:
            RiskCheckResult indicating if order is allowed
        """
        # Check if trading is halted
        if self._trading_halted:
            if not self._can_resume_trading():
                return RiskCheckResult.blocked(
                    RiskViolationType.TRADING_HALTED,
                    f"Trading halted: {self._halt_reason}",
                )
            else:
                self._resume_trading()

        # Check order value limit
        if order.value_usd > self.limits.max_order_value_usd:
            return self._violation(
                RiskViolationType.ORDER_SIZE,
                f"Order value ${order.value_usd:,.2f} exceeds limit ${self.limits.max_order_value_usd:,.2f}",
                order.value_usd,
                self.limits.max_order_value_usd,
            )

        # Check position size after order
        new_position_pct = self._calculate_position_pct_after_order(order, portfolio)
        if new_position_pct > self.limits.max_position_pct:
            return self._violation(
                RiskViolationType.POSITION_SIZE,
                f"Position would be {new_position_pct:.1f}% of equity (limit: {self.limits.max_position_pct}%)",
                new_position_pct,
                self.limits.max_position_pct,
            )

        # Check single position concentration
        symbol_position_pct = self._calculate_symbol_position_pct(order, portfolio)
        if symbol_position_pct > self.limits.max_single_position_pct:
            return self._violation(
                RiskViolationType.POSITION_SIZE,
                f"Single position {order.symbol} would be {symbol_position_pct:.1f}% (limit: {self.limits.max_single_position_pct}%)",
                symbol_position_pct,
                self.limits.max_single_position_pct,
            )

        # Check leverage
        new_leverage = self._calculate_leverage_after_order(order, portfolio)
        if new_leverage > self.limits.max_leverage:
            return self._violation(
                RiskViolationType.LEVERAGE,
                f"Leverage would be {new_leverage:.1f}x (limit: {self.limits.max_leverage}x)",
                new_leverage,
                self.limits.max_leverage,
            )

        # Check order rate limit
        if not self._check_order_rate(portfolio):
            return self._violation(
                RiskViolationType.ORDER_RATE,
                f"Order rate exceeds {self.limits.max_orders_per_minute}/minute",
                len(portfolio.recent_order_timestamps),
                float(self.limits.max_orders_per_minute),
            )

        # Check open orders per symbol
        current_open = portfolio.open_orders.get(order.symbol, 0)
        if current_open >= self.limits.max_open_orders_per_symbol:
            return self._violation(
                RiskViolationType.ORDER_RATE,
                f"Open orders for {order.symbol} at limit ({current_open})",
                float(current_open),
                float(self.limits.max_open_orders_per_symbol),
            )

        return RiskCheckResult.allowed_result()

    def _calculate_position_pct_after_order(self, order: Order, portfolio: PortfolioState) -> float:
        """Calculate total position % after order executes."""
        if portfolio.equity <= 0:
            return 100.0  # Prevent division by zero

        # Estimate new total position value
        if order.side == "buy":
            new_total = portfolio.total_position_value + order.value_usd
        else:
            new_total = max(0, portfolio.total_position_value - order.value_usd)

        return (new_total / portfolio.equity) * 100

    def _calculate_symbol_position_pct(self, order: Order, portfolio: PortfolioState) -> float:
        """Calculate single symbol position % after order."""
        if portfolio.equity <= 0:
            return 100.0

        current_value = portfolio.positions.get(order.symbol, 0)
        if order.side == "buy":
            new_value = current_value + order.value_usd
        else:
            new_value = max(0, current_value - order.value_usd)

        return (new_value / portfolio.equity) * 100

    def _calculate_leverage_after_order(self, order: Order, portfolio: PortfolioState) -> float:
        """Calculate effective leverage after order."""
        if portfolio.equity <= 0:
            return 10.0  # Return high value to block

        # New total exposure
        if order.side == "buy":
            new_exposure = portfolio.total_position_value + (order.value_usd * order.leverage)
        else:
            new_exposure = portfolio.total_position_value

        return new_exposure / portfolio.equity

    def _check_order_rate(self, portfolio: PortfolioState) -> bool:
        """Check if order rate is within limits."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        recent_count = sum(1 for ts in portfolio.recent_order_timestamps if ts > one_minute_ago)

        return recent_count < self.limits.max_orders_per_minute

    # =========================================================================
    # P&L and Halt Checks
    # =========================================================================

    def check_pnl_limits(self, portfolio: PortfolioState) -> RiskCheckResult:
        """
        Check if P&L is within limits.

        Should be called periodically (e.g., every minute).
        """
        if portfolio.equity <= 0:
            return RiskCheckResult.allowed_result()

        # Check daily loss
        daily_loss_pct = (portfolio.daily_pnl / portfolio.equity) * 100
        if daily_loss_pct < -self.limits.max_daily_loss_pct:
            result = self._violation(
                RiskViolationType.DAILY_LOSS,
                f"Daily loss {daily_loss_pct:.2f}% exceeds limit {-self.limits.max_daily_loss_pct}%",
                abs(daily_loss_pct),
                self.limits.max_daily_loss_pct,
            )

            if self.limits.auto_halt_on_loss_limit:
                self._halt_trading(f"Daily loss limit breached: {daily_loss_pct:.2f}%")

            return result

        # Check weekly loss
        weekly_loss_pct = (portfolio.weekly_pnl / portfolio.equity) * 100
        if weekly_loss_pct < -self.limits.max_weekly_loss_pct:
            result = self._violation(
                RiskViolationType.DAILY_LOSS,
                f"Weekly loss {weekly_loss_pct:.2f}% exceeds limit {-self.limits.max_weekly_loss_pct}%",
                abs(weekly_loss_pct),
                self.limits.max_weekly_loss_pct,
            )

            if self.limits.auto_halt_on_loss_limit:
                self._halt_trading(f"Weekly loss limit breached: {weekly_loss_pct:.2f}%")

            return result

        return RiskCheckResult.allowed_result()

    def should_halt_trading(self, portfolio: PortfolioState | None = None) -> bool:
        """Check if trading should be halted."""
        if self._trading_halted:
            return not self._can_resume_trading()

        if portfolio:
            result = self.check_pnl_limits(portfolio)
            return not result.allowed

        return False

    def _halt_trading(self, reason: str) -> None:
        """Halt all trading."""
        self._trading_halted = True
        self._halt_timestamp = datetime.now()
        self._halt_reason = reason
        logger.critical(f"TRADING HALTED: {reason}")

    def _can_resume_trading(self) -> bool:
        """Check if trading can resume after halt."""
        if not self._halt_timestamp:
            return True

        cooldown = timedelta(hours=self.limits.halt_cooldown_hours)
        return datetime.now() > self._halt_timestamp + cooldown

    def _resume_trading(self) -> None:
        """Resume trading after halt."""
        logger.info(f"Trading resumed after halt: {self._halt_reason}")
        self._trading_halted = False
        self._halt_timestamp = None
        self._halt_reason = ""

    def force_resume_trading(self, reason: str = "manual override") -> None:
        """Force resume trading (manual override)."""
        logger.warning(f"Trading force resumed: {reason}")
        self._resume_trading()

    # =========================================================================
    # Withdrawal Controls
    # =========================================================================

    def check_withdrawal(
        self,
        address: str,
        amount_usd: float,
        daily_total_usd: float = 0.0,
    ) -> RiskCheckResult:
        """
        Check if a withdrawal is allowed.

        Args:
            address: Destination address
            amount_usd: Withdrawal amount in USD
            daily_total_usd: Total USD already withdrawn today

        Returns:
            RiskCheckResult
        """
        address_lower = address.lower()

        # Check whitelist
        if self.limits.withdrawal_whitelist_enabled:
            if address_lower not in self._withdrawal_whitelist:
                # Check if in pending whitelist
                if address_lower in self._pending_whitelist:
                    added_at = self._pending_whitelist[address_lower]
                    delay = timedelta(hours=self.limits.withdrawal_delay_hours_new_address)
                    if datetime.now() < added_at + delay:
                        remaining = (added_at + delay) - datetime.now()
                        return self._violation(
                            RiskViolationType.WITHDRAWAL_DELAY,
                            f"Address pending whitelist approval. {remaining.seconds // 3600}h remaining",
                            0,
                            float(self.limits.withdrawal_delay_hours_new_address),
                            address=address,
                        )
                    else:
                        # Promote to full whitelist
                        self._withdrawal_whitelist.add(address_lower)
                        del self._pending_whitelist[address_lower]
                else:
                    return self._violation(
                        RiskViolationType.WITHDRAWAL_NOT_WHITELISTED,
                        f"Address not whitelisted. Add and wait {self.limits.withdrawal_delay_hours_new_address}h",
                        0,
                        0,
                        address=address,
                    )

        # Check daily limit
        if daily_total_usd + amount_usd > self.limits.max_withdrawal_usd_per_day:
            return self._violation(
                RiskViolationType.ORDER_SIZE,
                f"Withdrawal would exceed daily limit ${self.limits.max_withdrawal_usd_per_day:,.2f}",
                daily_total_usd + amount_usd,
                self.limits.max_withdrawal_usd_per_day,
            )

        return RiskCheckResult.allowed_result()

    def add_to_whitelist(self, address: str, immediate: bool = False) -> None:
        """
        Add address to withdrawal whitelist.

        Args:
            address: Address to whitelist
            immediate: If True, skip delay period (use with caution)
        """
        address_lower = address.lower()

        if immediate:
            self._withdrawal_whitelist.add(address_lower)
            logger.warning(f"Address {address[:10]}... added to whitelist immediately")
        else:
            self._pending_whitelist[address_lower] = datetime.now()
            logger.info(
                f"Address {address[:10]}... added to pending whitelist. "
                f"Available in {self.limits.withdrawal_delay_hours_new_address}h"
            )

    def remove_from_whitelist(self, address: str) -> None:
        """Remove address from whitelist."""
        address_lower = address.lower()
        self._withdrawal_whitelist.discard(address_lower)
        self._pending_whitelist.pop(address_lower, None)
        logger.info(f"Address {address[:10]}... removed from whitelist")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _violation(
        self,
        violation_type: RiskViolationType,
        reason: str,
        current: float,
        limit: float,
        **metadata: Any,
    ) -> RiskCheckResult:
        """Create a violation result and trigger callback."""
        result = RiskCheckResult.blocked(violation_type, reason, current, limit, **metadata)

        logger.warning(f"Risk violation: {violation_type.value} - {reason}")

        if self.on_violation:
            try:
                self.on_violation(result)
            except Exception as e:
                logger.error(f"Error in violation callback: {e}")

        return result

    @property
    def is_trading_halted(self) -> bool:
        """Check if trading is currently halted."""
        return self._trading_halted

    @property
    def halt_info(self) -> dict[str, Any]:
        """Get information about current halt status."""
        return {
            "halted": self._trading_halted,
            "reason": self._halt_reason,
            "timestamp": self._halt_timestamp.isoformat() if self._halt_timestamp else None,
            "can_resume": self._can_resume_trading() if self._trading_halted else True,
        }

    def get_limits_summary(self) -> dict[str, Any]:
        """Get summary of current limits."""
        return {
            "max_position_pct": self.limits.max_position_pct,
            "max_single_position_pct": self.limits.max_single_position_pct,
            "max_daily_loss_pct": self.limits.max_daily_loss_pct,
            "max_weekly_loss_pct": self.limits.max_weekly_loss_pct,
            "max_leverage": self.limits.max_leverage,
            "max_order_value_usd": self.limits.max_order_value_usd,
            "max_orders_per_minute": self.limits.max_orders_per_minute,
            "max_open_orders_per_symbol": self.limits.max_open_orders_per_symbol,
            "withdrawal_whitelist_enabled": self.limits.withdrawal_whitelist_enabled,
            "withdrawal_delay_hours": self.limits.withdrawal_delay_hours_new_address,
            "max_withdrawal_usd_per_day": self.limits.max_withdrawal_usd_per_day,
        }


# Global singleton for convenience
_default_risk_manager: TradingRiskManager | None = None


def get_risk_manager() -> TradingRiskManager:
    """Get or create the default risk manager."""
    global _default_risk_manager
    if _default_risk_manager is None:
        _default_risk_manager = TradingRiskManager()
    return _default_risk_manager


def check_order(order: Order, portfolio: PortfolioState) -> RiskCheckResult:
    """Check order using default risk manager."""
    return get_risk_manager().check_order(order, portfolio)


def check_withdrawal(
    address: str, amount_usd: float, daily_total_usd: float = 0.0
) -> RiskCheckResult:
    """Check withdrawal using default risk manager."""
    return get_risk_manager().check_withdrawal(address, amount_usd, daily_total_usd)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create risk manager with custom limits
    limits = RiskLimits(
        max_position_pct=10.0,
        max_daily_loss_pct=3.0,
        max_leverage=3.0,
    )
    risk_manager = TradingRiskManager(limits=limits)

    # Print limits summary
    print("Risk Limits Configuration:")
    for key, value in risk_manager.get_limits_summary().items():
        print(f"  {key}: {value}")

    # Example order check
    order = Order(symbol="BTC-USD", side="buy", quantity=0.5, price=50000.0)
    portfolio = PortfolioState(
        equity=100000.0,
        total_position_value=5000.0,
        positions={"BTC-USD": 5000.0},
        daily_pnl=-1000.0,
    )

    result = risk_manager.check_order(order, portfolio)
    print(f"\nOrder check: {'ALLOWED' if result.allowed else 'BLOCKED'}")
    if not result.allowed:
        print(f"  Reason: {result.reason}")
