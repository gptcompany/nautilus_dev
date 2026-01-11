"""
Monitoring stage implementation.

Handles metrics collection, alerting, and dashboard configuration.
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
class MonitoringConfig:
    """Configuration for monitoring stage."""

    # Metrics to track
    metrics: list[str] = field(
        default_factory=lambda: [
            "pnl",
            "drawdown",
            "position_count",
            "leverage",
            "win_rate",
        ]
    )

    # Alert thresholds
    alert_drawdown_pct: float = 10.0
    alert_daily_loss_pct: float = 2.0
    alert_leverage: float = 2.5

    # Notification channels
    discord_webhook: str | None = None
    enable_console: bool = True

    # Dashboard
    dashboard_enabled: bool = True
    refresh_interval_sec: int = 60

    # Custom
    custom_params: dict[str, Any] = field(default_factory=dict)


class MonitoringStage(AbstractStage):
    """
    Monitoring and alerting stage.

    Responsibilities:
        - Configure metrics collection
        - Set up alert thresholds
        - Initialize dashboard
        - Validate monitoring coverage

    Example:
        ```python
        stage = MonitoringStage()
        state = PipelineState.create(config={
            "alert_drawdown_pct": 5.0,
            "discord_webhook": "https://discord.com/...",
        })
        result = await stage.execute(state)
        ```
    """

    def __init__(self, confidence_scorer: ConfidenceScorer | None = None):
        """
        Initialize monitoring stage.

        Args:
            confidence_scorer: Custom scorer, or default if None
        """
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()

    @property
    def stage_type(self) -> StageType:
        """Return stage type."""
        return StageType.MONITORING

    def validate_input(self, state: PipelineState) -> bool:
        """Validate inputs before execution."""
        # Monitoring can run independently but benefits from prior stages
        return True

    def get_dependencies(self) -> list[StageType]:
        """Monitoring has optional dependencies."""
        return []  # Optional: [StageType.RISK]

    async def execute(self, state: PipelineState) -> StageResult:
        """
        Execute monitoring setup.

        Args:
            state: Pipeline state

        Returns:
            StageResult with monitoring configuration
        """
        config = self._parse_config(state.config)

        try:
            # Build monitoring configuration
            monitoring_config = await self._build_monitoring_config(state, config)

            # Validate configuration
            validations = self._validate_config(monitoring_config, config)

            # Score confidence
            confidence = self.confidence_scorer.score(validations)

            # Build metadata
            metadata = self._build_metadata(monitoring_config, validations)

            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.COMPLETED,
                confidence=confidence,
                output=monitoring_config,
                metadata=metadata,
                needs_human_review=confidence == Confidence.LOW_CONFIDENCE,
                review_reason=self._get_review_reason(validations, confidence),
            )

        except Exception as e:
            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.FAILED,
                confidence=Confidence.UNSOLVABLE,
                output=None,
                metadata={"error": str(e)},
                needs_human_review=True,
                review_reason=f"Monitoring setup failed: {e}",
            )

    def _parse_config(self, config: dict[str, Any]) -> MonitoringConfig:
        """Parse config dict into MonitoringConfig."""
        return MonitoringConfig(
            metrics=config.get(
                "metrics",
                ["pnl", "drawdown", "position_count", "leverage", "win_rate"],
            ),
            alert_drawdown_pct=config.get("alert_drawdown_pct", 10.0),
            alert_daily_loss_pct=config.get("alert_daily_loss_pct", 2.0),
            alert_leverage=config.get("alert_leverage", 2.5),
            discord_webhook=config.get("discord_webhook"),
            enable_console=config.get("enable_console", True),
            dashboard_enabled=config.get("dashboard_enabled", True),
            refresh_interval_sec=config.get("refresh_interval_sec", 60),
            custom_params=config.get("monitoring_params", {}),
        )

    async def _build_monitoring_config(
        self,
        state: PipelineState,
        config: MonitoringConfig,
    ) -> dict[str, Any]:
        """Build monitoring configuration."""
        # Get risk thresholds from prior stage if available
        risk_result = state.stage_results.get(StageType.RISK)
        risk_output = risk_result.output if risk_result else None

        monitoring_config = {
            "pipeline_id": state.pipeline_id,
            "metrics": config.metrics,
            "alerts": {
                "drawdown_pct": config.alert_drawdown_pct,
                "daily_loss_pct": config.alert_daily_loss_pct,
                "leverage": config.alert_leverage,
            },
            "notifications": {
                "discord_webhook": config.discord_webhook,
                "console_enabled": config.enable_console,
            },
            "dashboard": {
                "enabled": config.dashboard_enabled,
                "refresh_interval_sec": config.refresh_interval_sec,
            },
        }

        # Add risk context if available
        if risk_output:
            risk_metrics = risk_output.get("risk_metrics", {})
            monitoring_config["risk_context"] = {
                "current_var": risk_metrics.get("var_pct"),
                "current_leverage": risk_metrics.get("leverage_used"),
            }

        return monitoring_config

    def _validate_config(
        self,
        monitoring_config: dict[str, Any],
        config: MonitoringConfig,
    ) -> list[ValidationResult]:
        """Validate monitoring configuration."""
        validations = []

        # Check notification channel configured
        has_notification = bool(config.discord_webhook or config.enable_console)
        validations.append(
            create_validation_from_check(
                source="notification_channel",
                passed=has_notification,
                score=1.0 if has_notification else 0.0,
                message="Notification channel configured"
                if has_notification
                else "No notification channel",
            )
        )

        # Check metrics coverage
        essential_metrics = {"pnl", "drawdown", "leverage"}
        configured_metrics = set(config.metrics)
        coverage = len(essential_metrics & configured_metrics) / len(essential_metrics)
        validations.append(
            create_validation_from_check(
                source="metrics_coverage",
                passed=coverage >= 0.8,
                score=coverage,
                message=f"Metrics coverage: {coverage:.0%}",
            )
        )

        # Check alert thresholds are reasonable
        thresholds_ok = (
            0 < config.alert_drawdown_pct <= 20
            and 0 < config.alert_daily_loss_pct <= 5
            and 0 < config.alert_leverage <= 5
        )
        validations.append(
            create_validation_from_check(
                source="alert_thresholds",
                passed=thresholds_ok,
                score=1.0 if thresholds_ok else 0.5,
                message="Alert thresholds within bounds"
                if thresholds_ok
                else "Alert thresholds may be too loose",
            )
        )

        return validations

    def _build_metadata(
        self,
        monitoring_config: dict[str, Any],
        validations: list[ValidationResult],
    ) -> dict[str, Any]:
        """Build metadata dict."""
        return {
            "metrics_count": len(monitoring_config.get("metrics", [])),
            "alerts_configured": bool(monitoring_config.get("alerts")),
            "dashboard_enabled": monitoring_config.get("dashboard", {}).get("enabled", False),
            "has_discord": bool(monitoring_config.get("notifications", {}).get("discord_webhook")),
            "validations_passed": sum(1 for v in validations if v.passed),
            "validations_total": len(validations),
        }

    def _get_review_reason(
        self,
        validations: list[ValidationResult],
        confidence: Confidence,
    ) -> str | None:
        """Get review reason if needed."""
        if confidence == Confidence.HIGH_CONFIDENCE:
            return None

        failed = [v for v in validations if not v.passed]
        if failed:
            return f"Monitoring issues: {', '.join(v.source for v in failed)}"

        return "Monitoring configuration needs review"
