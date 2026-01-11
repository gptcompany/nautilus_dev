"""
Execution stage implementation.

Handles order management, execution logic, and trade submission.
"""

from dataclasses import dataclass, field
from typing import Any

from pipeline.core.state import PipelineState
from pipeline.core.types import (
    Confidence,
    PipelineStatus,
    StageResult,
    StageType,
    ValidationResult,
)
from pipeline.hitl.confidence import ConfidenceScorer, create_validation_from_check
from pipeline.stages.base import AbstractStage


@dataclass
class ExecutionConfig:
    """Configuration for execution stage."""

    # Execution mode
    mode: str = "paper"  # paper | live | backtest

    # Order settings
    order_type: str = "MARKET"  # MARKET | LIMIT | STOP_MARKET
    time_in_force: str = "GTC"  # GTC | IOC | FOK

    # Slippage protection
    max_slippage_pct: float = 0.5
    use_twap: bool = False
    twap_duration_sec: int = 300

    # Rate limiting
    max_orders_per_minute: int = 10
    min_order_interval_sec: float = 1.0

    # Safety
    require_confirmation: bool = True
    dry_run: bool = True  # Default to dry run for safety

    # Exchange settings
    exchange: str = "BINANCE"
    account_id: str | None = None

    # Custom params
    custom_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Order:
    """Represents a trade order."""

    symbol: str
    side: str  # BUY | SELL
    quantity: float
    order_type: str = "MARKET"
    price: float | None = None
    stop_price: float | None = None
    time_in_force: str = "GTC"
    client_order_id: str | None = None


@dataclass
class ExecutionResult:
    """Result of order execution."""

    order: Order
    status: str  # PENDING | FILLED | PARTIAL | REJECTED | CANCELLED
    filled_qty: float = 0.0
    avg_price: float = 0.0
    commission: float = 0.0
    slippage_pct: float = 0.0
    exchange_order_id: str | None = None
    error: str | None = None


class ExecutionStage(AbstractStage):
    """
    Order execution stage.

    Responsibilities:
        - Generate orders from risk-adjusted positions
        - Validate orders against safety limits
        - Execute orders (paper/live/backtest)
        - Track fills and slippage

    Example:
        ```python
        stage = ExecutionStage()
        state = PipelineState.create(config={
            "mode": "paper",
            "order_type": "MARKET",
            "max_slippage_pct": 0.3,
        })
        result = await stage.execute(state)
        ```
    """

    def __init__(self, confidence_scorer: ConfidenceScorer | None = None):
        """
        Initialize execution stage.

        Args:
            confidence_scorer: Custom scorer, or default if None
        """
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()

    @property
    def stage_type(self) -> StageType:
        """Return stage type."""
        return StageType.EXECUTION

    def validate_input(self, state: PipelineState) -> bool:
        """Validate inputs before execution."""
        # Requires RISK stage output with positions
        if StageType.RISK not in state.stage_results:
            return False
        risk_result = state.stage_results[StageType.RISK]
        if not risk_result.is_successful():
            return False
        # Need positions to execute
        positions = risk_result.output.get("positions", []) if risk_result.output else []
        return len(positions) > 0 or state.config.get("allow_empty_execution", False)

    def get_dependencies(self) -> list[StageType]:
        """Execution depends on RISK stage."""
        return [StageType.RISK]

    def get_confidence_requirement(self) -> Confidence:
        """Execution requires HIGH confidence from prior stages."""
        return Confidence.HIGH_CONFIDENCE

    async def execute(self, state: PipelineState) -> StageResult:
        """
        Execute orders based on risk-adjusted positions.

        Args:
            state: Pipeline state with RISK result

        Returns:
            StageResult with execution results
        """
        config = self._parse_config(state.config)
        risk_result = state.stage_results[StageType.RISK]

        try:
            # Get positions from risk stage
            positions = risk_result.output.get("positions", [])

            # Generate orders from positions
            orders = self._generate_orders(positions, config)

            # Pre-execution validation
            pre_validations = self._pre_validate_orders(orders, config)
            if not all(v.passed for v in pre_validations):
                return StageResult(
                    stage=self.stage_type,
                    status=PipelineStatus.FAILED,
                    confidence=Confidence.LOW_CONFIDENCE,
                    output={
                        "orders": [],
                        "errors": [v.message for v in pre_validations if not v.passed],
                    },
                    metadata={
                        "validations_failed": len([v for v in pre_validations if not v.passed])
                    },
                    needs_human_review=True,
                    review_reason="Pre-execution validation failed",
                )

            # Execute orders
            execution_results = await self._execute_orders(orders, config)

            # Post-execution validation
            post_validations = self._post_validate_execution(execution_results, config)

            # Combine validations
            all_validations = pre_validations + post_validations

            # Score confidence
            confidence = self.confidence_scorer.score(all_validations)

            # Build output
            output = self._build_output(orders, execution_results, config)

            # Build metadata
            metadata = self._build_metadata(execution_results, all_validations)

            # Execution ALWAYS needs review in live mode
            needs_review = config.mode == "live" or confidence in (
                Confidence.LOW_CONFIDENCE,
                Confidence.CONFLICT,
            )

            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.COMPLETED,
                confidence=confidence,
                output=output,
                metadata=metadata,
                needs_human_review=needs_review,
                review_reason=self._get_review_reason(execution_results, config, confidence),
            )

        except Exception as e:
            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.FAILED,
                confidence=Confidence.UNSOLVABLE,
                output=None,
                metadata={"error": str(e)},
                needs_human_review=True,
                review_reason=f"Execution failed: {e}",
            )

    def _parse_config(self, config: dict[str, Any]) -> ExecutionConfig:
        """Parse config dict into ExecutionConfig."""
        return ExecutionConfig(
            mode=config.get("execution_mode", config.get("mode", "paper")),
            order_type=config.get("order_type", "MARKET"),
            time_in_force=config.get("time_in_force", "GTC"),
            max_slippage_pct=config.get("max_slippage_pct", 0.5),
            use_twap=config.get("use_twap", False),
            twap_duration_sec=config.get("twap_duration_sec", 300),
            max_orders_per_minute=config.get("max_orders_per_minute", 10),
            min_order_interval_sec=config.get("min_order_interval_sec", 1.0),
            require_confirmation=config.get("require_confirmation", True),
            dry_run=config.get("dry_run", True),
            exchange=config.get("exchange", "BINANCE"),
            account_id=config.get("account_id"),
            custom_params=config.get("execution_params", {}),
        )

    def _generate_orders(
        self,
        positions: list[dict[str, Any]],
        config: ExecutionConfig,
    ) -> list[Order]:
        """Generate orders from risk-adjusted positions."""
        orders = []

        for pos in positions:
            symbol = pos.get("symbol", "UNKNOWN")
            target_qty = pos.get("target_quantity", 0)
            current_qty = pos.get("current_quantity", 0)
            delta = target_qty - current_qty

            if abs(delta) < 1e-8:
                continue  # No change needed

            order = Order(
                symbol=symbol,
                side="BUY" if delta > 0 else "SELL",
                quantity=abs(delta),
                order_type=config.order_type,
                price=pos.get("limit_price"),
                stop_price=pos.get("stop_price"),
                time_in_force=config.time_in_force,
                client_order_id=f"{symbol}_{pos.get('strategy', 'default')}",
            )
            orders.append(order)

        return orders

    def _pre_validate_orders(
        self,
        orders: list[Order],
        config: ExecutionConfig,
    ) -> list[ValidationResult]:
        """Validate orders before execution."""
        validations = []

        # Check order count
        order_count_ok = len(orders) <= config.max_orders_per_minute
        validations.append(
            create_validation_from_check(
                source="order_count",
                passed=order_count_ok,
                score=1.0 if order_count_ok else 0.3,
                message=f"Order count: {len(orders)} (max: {config.max_orders_per_minute})",
            )
        )

        # Check for valid quantities
        all_valid_qty = all(o.quantity > 0 for o in orders)
        validations.append(
            create_validation_from_check(
                source="order_quantities",
                passed=all_valid_qty,
                score=1.0 if all_valid_qty else 0.0,
                message="All orders have valid quantities"
                if all_valid_qty
                else "Invalid order quantities",
            )
        )

        # Check dry run mode for safety
        if config.mode == "live" and not config.dry_run:
            validations.append(
                create_validation_from_check(
                    source="live_mode_check",
                    passed=False,  # Always flag live non-dry-run
                    score=0.5,
                    message="LIVE MODE with dry_run=False - requires confirmation",
                )
            )
        else:
            validations.append(
                create_validation_from_check(
                    source="execution_mode",
                    passed=True,
                    score=1.0,
                    message=f"Mode: {config.mode} (dry_run={config.dry_run})",
                )
            )

        return validations

    async def _execute_orders(
        self,
        orders: list[Order],
        config: ExecutionConfig,
    ) -> list[ExecutionResult]:
        """Execute orders based on mode."""
        results = []

        for order in orders:
            if config.mode == "paper" or config.dry_run:
                # Paper trading / dry run - simulate fill
                result = self._simulate_fill(order, config)
            elif config.mode == "backtest":
                # Backtest mode - instant fill at expected price
                result = self._backtest_fill(order, config)
            else:
                # Live mode - would call exchange API
                # For now, just simulate (safety first)
                result = self._simulate_fill(order, config)

            results.append(result)

        return results

    def _simulate_fill(self, order: Order, config: ExecutionConfig) -> ExecutionResult:
        """Simulate order fill for paper trading."""
        import random

        # Simulate slippage
        slippage = random.uniform(0, config.max_slippage_pct / 100)
        base_price = order.price or 100.0  # Default price if not set

        if order.side == "BUY":
            avg_price = base_price * (1 + slippage)
        else:
            avg_price = base_price * (1 - slippage)

        return ExecutionResult(
            order=order,
            status="FILLED",
            filled_qty=order.quantity,
            avg_price=avg_price,
            commission=order.quantity * avg_price * 0.001,  # 0.1% commission
            slippage_pct=slippage * 100,
            exchange_order_id=f"SIM_{order.client_order_id}",
        )

    def _backtest_fill(self, order: Order, config: ExecutionConfig) -> ExecutionResult:
        """Fill order for backtesting (no slippage)."""
        base_price = order.price or 100.0

        return ExecutionResult(
            order=order,
            status="FILLED",
            filled_qty=order.quantity,
            avg_price=base_price,
            commission=order.quantity * base_price * 0.001,
            slippage_pct=0.0,
            exchange_order_id=f"BT_{order.client_order_id}",
        )

    def _post_validate_execution(
        self,
        results: list[ExecutionResult],
        config: ExecutionConfig,
    ) -> list[ValidationResult]:
        """Validate execution results."""
        validations = []

        if not results:
            validations.append(
                create_validation_from_check(
                    source="execution_results",
                    passed=True,
                    score=1.0,
                    message="No orders to execute",
                )
            )
            return validations

        # Check fill rate
        filled = sum(1 for r in results if r.status == "FILLED")
        fill_rate = filled / len(results) if results else 0
        validations.append(
            create_validation_from_check(
                source="fill_rate",
                passed=fill_rate >= 0.9,
                score=fill_rate,
                message=f"Fill rate: {fill_rate:.0%} ({filled}/{len(results)})",
            )
        )

        # Check slippage
        if filled > 0:
            avg_slippage = sum(r.slippage_pct for r in results if r.status == "FILLED") / filled
            slippage_ok = avg_slippage <= config.max_slippage_pct
            validations.append(
                create_validation_from_check(
                    source="slippage",
                    passed=slippage_ok,
                    score=1.0 - (avg_slippage / config.max_slippage_pct)
                    if config.max_slippage_pct > 0
                    else 1.0,
                    message=f"Avg slippage: {avg_slippage:.3f}% (max: {config.max_slippage_pct}%)",
                )
            )

        # Check for errors
        errors = [r for r in results if r.error]
        validations.append(
            create_validation_from_check(
                source="execution_errors",
                passed=len(errors) == 0,
                score=1.0 if not errors else 0.0,
                message=f"Errors: {len(errors)}" if errors else "No execution errors",
            )
        )

        return validations

    def _build_output(
        self,
        orders: list[Order],
        results: list[ExecutionResult],
        config: ExecutionConfig,
    ) -> dict[str, Any]:
        """Build output dict."""
        return {
            "mode": config.mode,
            "dry_run": config.dry_run,
            "orders_submitted": len(orders),
            "orders_filled": sum(1 for r in results if r.status == "FILLED"),
            "total_commission": sum(r.commission for r in results),
            "avg_slippage_pct": (
                sum(r.slippage_pct for r in results) / len(results) if results else 0
            ),
            "executions": [
                {
                    "symbol": r.order.symbol,
                    "side": r.order.side,
                    "quantity": r.filled_qty,
                    "avg_price": r.avg_price,
                    "status": r.status,
                    "slippage_pct": r.slippage_pct,
                }
                for r in results
            ],
        }

    def _build_metadata(
        self,
        results: list[ExecutionResult],
        validations: list[ValidationResult],
    ) -> dict[str, Any]:
        """Build metadata dict."""
        return {
            "orders_total": len(results),
            "orders_filled": sum(1 for r in results if r.status == "FILLED"),
            "orders_rejected": sum(1 for r in results if r.status == "REJECTED"),
            "total_volume": sum(
                r.filled_qty * r.avg_price for r in results if r.status == "FILLED"
            ),
            "validations_passed": sum(1 for v in validations if v.passed),
            "validations_total": len(validations),
        }

    def _get_review_reason(
        self,
        results: list[ExecutionResult],
        config: ExecutionConfig,
        confidence: Confidence,
    ) -> str | None:
        """Get review reason if needed."""
        if confidence == Confidence.HIGH_CONFIDENCE and config.mode != "live":
            return None

        reasons = []

        if config.mode == "live":
            reasons.append("LIVE execution mode")

        if not config.dry_run:
            reasons.append("dry_run=False")

        rejected = sum(1 for r in results if r.status == "REJECTED")
        if rejected > 0:
            reasons.append(f"{rejected} orders rejected")

        errors = [r for r in results if r.error]
        if errors:
            reasons.append(f"{len(errors)} execution errors")

        return "; ".join(reasons) if reasons else "Execution requires review"
