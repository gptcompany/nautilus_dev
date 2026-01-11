"""
Risk assessment stage implementation.

Handles position sizing, risk limits, and portfolio constraints.
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
class RiskConfig:
    """Configuration for risk stage."""

    # Position limits (FIXED - never adaptive per CLAUDE.md)
    max_position_pct: float = 10.0  # Max % of portfolio per position
    max_leverage: float = 3.0
    max_concentration: float = 0.3  # Max % in single asset

    # Loss limits (FIXED)
    stop_loss_pct: float = 5.0
    daily_loss_limit_pct: float = 2.0
    kill_switch_drawdown: float = 15.0

    # Risk metrics
    max_var_pct: float = 5.0  # Value at Risk
    min_diversification: float = 0.5

    # Custom
    custom_params: dict[str, Any] = field(default_factory=dict)


class RiskStage(AbstractStage):
    """
    Risk assessment and position sizing stage.

    Responsibilities:
        - Calculate position sizes
        - Validate risk limits
        - Check portfolio constraints
        - Apply safety limits (FIXED, never adaptive)

    Example:
        ```python
        stage = RiskStage()
        state = PipelineState.create(config={
            "max_leverage": 2.0,
            "stop_loss_pct": 3.0,
        })
        # Requires ALPHA stage result
        state.stage_results[StageType.ALPHA] = alpha_result
        result = await stage.execute(state)
        ```

    Safety Note:
        Per project guidelines, safety limits are FIXED and never adaptive.
        Knight Capital lost $440M in 45 minutes from adaptive limits.
    """

    def __init__(self, confidence_scorer: ConfidenceScorer | None = None):
        """
        Initialize risk stage.

        Args:
            confidence_scorer: Custom scorer, or default if None
        """
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()

    @property
    def stage_type(self) -> StageType:
        """Return stage type."""
        return StageType.RISK

    def validate_input(self, state: PipelineState) -> bool:
        """Validate inputs before execution."""
        # Requires ALPHA stage output
        if StageType.ALPHA not in state.stage_results:
            return False
        alpha_result = state.stage_results[StageType.ALPHA]
        return alpha_result.is_successful() and alpha_result.output is not None

    def get_dependencies(self) -> list[StageType]:
        """Risk depends on ALPHA stage."""
        return [StageType.ALPHA]

    def get_confidence_requirement(self) -> Confidence:
        """Risk stage requires HIGH confidence due to financial impact."""
        return Confidence.HIGH_CONFIDENCE

    async def execute(self, state: PipelineState) -> StageResult:
        """
        Execute risk assessment.

        Args:
            state: Pipeline state with ALPHA result

        Returns:
            StageResult with risk assessment
        """
        config = self._parse_config(state.config)
        alpha_result = state.stage_results[StageType.ALPHA]
        alpha_output = alpha_result.output

        try:
            # Calculate risk metrics
            risk_metrics = await self._calculate_risk_metrics(alpha_output, config)

            # Calculate position sizes
            positions = await self._calculate_positions(alpha_output, config)

            # Validate
            validations = self._validate_risk(risk_metrics, positions, config)

            # Score confidence
            confidence = self.confidence_scorer.score(validations)

            # Build metadata
            metadata = self._build_metadata(risk_metrics, positions, validations)

            # Risk stage should be extra cautious
            needs_review = confidence in (
                Confidence.LOW_CONFIDENCE,
                Confidence.CONFLICT,
            ) or not all(v.passed for v in validations)

            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.COMPLETED,
                confidence=confidence,
                output={"risk_metrics": risk_metrics, "positions": positions},
                metadata=metadata,
                needs_human_review=needs_review,
                review_reason=self._get_review_reason(risk_metrics, validations, confidence),
            )

        except Exception as e:
            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.FAILED,
                confidence=Confidence.UNSOLVABLE,
                output=None,
                metadata={"error": str(e)},
                needs_human_review=True,
                review_reason=f"Risk calculation failed: {e}",
            )

    def _parse_config(self, config: dict[str, Any]) -> RiskConfig:
        """Parse config dict into RiskConfig."""
        return RiskConfig(
            max_position_pct=config.get("max_position_pct", 10.0),
            max_leverage=config.get("max_leverage", 3.0),
            max_concentration=config.get("max_concentration", 0.3),
            stop_loss_pct=config.get("stop_loss_pct", 5.0),
            daily_loss_limit_pct=config.get("daily_loss_limit_pct", 2.0),
            kill_switch_drawdown=config.get("kill_switch_drawdown", 15.0),
            max_var_pct=config.get("max_var_pct", 5.0),
            min_diversification=config.get("min_diversification", 0.5),
            custom_params=config.get("risk_params", {}),
        )

    async def _calculate_risk_metrics(
        self,
        alpha_output: dict[str, Any],
        config: RiskConfig,
    ) -> dict[str, float]:
        """Calculate risk metrics."""
        alpha_metrics = alpha_output.get("metrics", {})

        # Placeholder calculations
        return {
            "var_pct": alpha_metrics.get("max_drawdown", 0.1) * 0.5,
            "expected_drawdown": alpha_metrics.get("max_drawdown", 0.15),
            "leverage_used": min(config.max_leverage, 1.5),
            "concentration": 0.2,
            "diversification_score": 0.7,
        }

    async def _calculate_positions(
        self,
        alpha_output: dict[str, Any],
        config: RiskConfig,
    ) -> list[dict[str, Any]]:
        """Calculate position sizes."""
        # Placeholder implementation
        return [
            {
                "symbol": "BTCUSDT",
                "size_pct": min(config.max_position_pct, 5.0),
                "leverage": 1.0,
                "stop_loss_pct": config.stop_loss_pct,
            }
        ]

    def _validate_risk(
        self,
        risk_metrics: dict[str, float],
        positions: list[dict[str, Any]],
        config: RiskConfig,
    ) -> list[ValidationResult]:
        """Validate risk constraints."""
        validations = []

        # VaR check
        var = risk_metrics.get("var_pct", 100)
        var_ok = var <= config.max_var_pct
        validations.append(
            create_validation_from_check(
                source="var_limit",
                passed=var_ok,
                score=1.0 - min(1.0, var / config.max_var_pct),
                message=f"VaR: {var:.2f}% (max: {config.max_var_pct}%)",
            )
        )

        # Leverage check
        leverage = risk_metrics.get("leverage_used", 0)
        leverage_ok = leverage <= config.max_leverage
        validations.append(
            create_validation_from_check(
                source="leverage_limit",
                passed=leverage_ok,
                score=1.0 - min(1.0, leverage / config.max_leverage),
                message=f"Leverage: {leverage:.1f}x (max: {config.max_leverage}x)",
            )
        )

        # Concentration check
        concentration = risk_metrics.get("concentration", 1.0)
        conc_ok = concentration <= config.max_concentration
        validations.append(
            create_validation_from_check(
                source="concentration_limit",
                passed=conc_ok,
                score=1.0 - min(1.0, concentration / config.max_concentration),
                message=f"Concentration: {concentration:.1%} (max: {config.max_concentration:.1%})",
            )
        )

        # Diversification check
        diversification = risk_metrics.get("diversification_score", 0)
        div_ok = diversification >= config.min_diversification
        validations.append(
            create_validation_from_check(
                source="diversification",
                passed=div_ok,
                score=min(1.0, diversification / config.min_diversification),
                message=f"Diversification: {diversification:.2f} (min: {config.min_diversification})",
            )
        )

        # Position size check
        for pos in positions:
            size = pos.get("size_pct", 0)
            size_ok = size <= config.max_position_pct
            validations.append(
                create_validation_from_check(
                    source=f"position_size_{pos.get('symbol', 'unknown')}",
                    passed=size_ok,
                    score=1.0 - min(1.0, size / config.max_position_pct),
                    message=f"{pos.get('symbol')}: {size:.1f}% (max: {config.max_position_pct}%)",
                )
            )

        return validations

    def _build_metadata(
        self,
        risk_metrics: dict[str, float],
        positions: list[dict[str, Any]],
        validations: list[ValidationResult],
    ) -> dict[str, Any]:
        """Build metadata dict."""
        return {
            "var_pct": risk_metrics.get("var_pct"),
            "leverage_used": risk_metrics.get("leverage_used"),
            "num_positions": len(positions),
            "total_exposure_pct": sum(p.get("size_pct", 0) for p in positions),
            "validations_passed": sum(1 for v in validations if v.passed),
            "validations_total": len(validations),
        }

    def _get_review_reason(
        self,
        risk_metrics: dict[str, float],
        validations: list[ValidationResult],
        confidence: Confidence,
    ) -> str | None:
        """Get review reason if needed."""
        if confidence == Confidence.HIGH_CONFIDENCE:
            failed = [v for v in validations if not v.passed]
            if not failed:
                return None

        failed = [v for v in validations if not v.passed]
        if failed:
            return f"Risk violations: {', '.join(v.source for v in failed)}"

        return "Risk metrics require review"
