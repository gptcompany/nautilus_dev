"""
Human review prompt templates for HITL pipeline.

Provides structured prompts for each stage type.
"""

from dataclasses import dataclass, field

from pipeline.core.types import Confidence, StageResult, StageType


@dataclass
class PromptTemplate:
    """Template for human review prompts."""

    title: str
    summary: str
    details: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)

    def render(self) -> str:
        """Render prompt as formatted string."""
        lines = [
            f"# {self.title}",
            "",
            self.summary,
            "",
        ]

        if self.details:
            lines.append("## Details")
            for detail in self.details:
                lines.append(f"- {detail}")
            lines.append("")

        if self.risk_factors:
            lines.append("## Risk Factors")
            for risk in self.risk_factors:
                lines.append(f"- {risk}")
            lines.append("")

        if self.recommendations:
            lines.append("## Recommendations")
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        if self.questions:
            lines.append("## Questions to Consider")
            for q in self.questions:
                lines.append(f"- {q}")
            lines.append("")

        return "\n".join(lines)

    def render_compact(self) -> str:
        """Render as compact single-line string."""
        parts = [self.title, self.summary]
        if self.risk_factors:
            parts.append(f"Risks: {', '.join(self.risk_factors[:3])}")
        return " | ".join(parts)


class ApprovalPromptBuilder:
    """Builds approval prompts for different stages."""

    def __init__(self):
        """Initialize prompt builder."""
        self._stage_builders = {
            StageType.DATA: self._build_data_prompt,
            StageType.ALPHA: self._build_alpha_prompt,
            StageType.RISK: self._build_risk_prompt,
            StageType.EXECUTION: self._build_execution_prompt,
            StageType.MONITORING: self._build_monitoring_prompt,
        }

    def build(self, result: StageResult, pipeline_id: str) -> PromptTemplate:
        """
        Build approval prompt for stage result.

        Args:
            result: Stage result to build prompt for
            pipeline_id: Pipeline identifier

        Returns:
            PromptTemplate for human review
        """
        builder = self._stage_builders.get(result.stage, self._build_generic_prompt)
        return builder(result, pipeline_id)

    def _build_data_prompt(self, result: StageResult, pipeline_id: str) -> PromptTemplate:
        """Build prompt for DATA stage review."""
        output = result.output or {}

        details = [
            f"Source: {output.get('source', 'Unknown')}",
            f"Records: {output.get('record_count', 'N/A'):,}",
            f"Symbols: {output.get('symbols', [])}",
        ]

        risk_factors = []
        if output.get("record_count", 0) < 1000:
            risk_factors.append("Low record count - may affect model quality")
        if output.get("missing_data_pct", 0) > 5:
            risk_factors.append(f"Missing data: {output.get('missing_data_pct')}%")
        if output.get("quality_score", 1.0) < 0.8:
            risk_factors.append(f"Quality score: {output.get('quality_score')}")

        questions = [
            "Is the data source reliable and up-to-date?",
            "Are there any gaps in the data that could affect analysis?",
            "Is the sample size sufficient for the intended use?",
        ]

        return PromptTemplate(
            title=f"DATA Stage Review - {pipeline_id}",
            summary=f"Data validation completed with {result.confidence.name} confidence.",
            details=details,
            risk_factors=risk_factors,
            questions=questions,
            recommendations=self._get_confidence_recommendations(result.confidence),
        )

    def _build_alpha_prompt(self, result: StageResult, pipeline_id: str) -> PromptTemplate:
        """Build prompt for ALPHA stage review."""
        output = result.output or {}
        metrics = output.get("metrics", {})

        details = [
            f"Model Type: {output.get('alpha', {}).get('model_type', 'Unknown')}",
            f"Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}",
            f"Sortino Ratio: {metrics.get('sortino_ratio', 'N/A')}",
            f"Max Drawdown: {metrics.get('max_drawdown', 'N/A')}",
            f"Overfitting Score: {metrics.get('overfitting_score', 'N/A')}",
        ]

        risk_factors = []
        sharpe = metrics.get("sharpe_ratio", 0)
        if sharpe < 1.0:
            risk_factors.append(f"Low Sharpe ratio ({sharpe}) - may not justify risk")
        if metrics.get("overfitting_score", 0) > 0.3:
            risk_factors.append(f"High overfitting risk: {metrics.get('overfitting_score')}")
        if metrics.get("max_drawdown", 0) > 0.2:
            risk_factors.append(f"High max drawdown: {metrics.get('max_drawdown'):.1%}")

        questions = [
            "Is the alpha signal robust across different market conditions?",
            "Are the backtest assumptions realistic?",
            "Is there evidence of look-ahead bias or data snooping?",
        ]

        recommendations = self._get_confidence_recommendations(result.confidence)
        if sharpe < 0.5:
            recommendations.append("Consider rejecting - Sharpe ratio below minimum threshold")

        return PromptTemplate(
            title=f"ALPHA Stage Review - {pipeline_id}",
            summary=f"Alpha generation completed with {result.confidence.name} confidence.",
            details=details,
            risk_factors=risk_factors,
            questions=questions,
            recommendations=recommendations,
        )

    def _build_risk_prompt(self, result: StageResult, pipeline_id: str) -> PromptTemplate:
        """Build prompt for RISK stage review."""
        output = result.output or {}
        risk_metrics = output.get("risk_metrics", {})
        positions = output.get("positions", [])

        details = [
            f"VaR (95%): {risk_metrics.get('var_pct', 'N/A')}%",
            f"Leverage Used: {risk_metrics.get('leverage_used', 'N/A')}x",
            f"Position Count: {len(positions)}",
            f"Total Exposure: {risk_metrics.get('total_exposure_pct', 'N/A')}%",
        ]

        risk_factors = []
        leverage = risk_metrics.get("leverage_used", 0)
        if leverage > 2.0:
            risk_factors.append(f"High leverage ({leverage}x) - increased drawdown risk")
        var_pct = risk_metrics.get("var_pct", 0)
        if var_pct > 5:
            risk_factors.append(f"High VaR ({var_pct}%) - significant loss potential")
        if len(positions) > 10:
            risk_factors.append(f"Many positions ({len(positions)}) - complexity risk")

        questions = [
            "Are the position sizes appropriate for account size?",
            "Is the leverage within acceptable limits?",
            "Are stop-loss levels properly set?",
        ]

        # Risk stage always gets extra scrutiny
        recommendations = [
            "VERIFY: All safety limits are within CLAUDE.md specifications",
            "CHECK: Kill switch and daily loss limits are active",
        ]
        recommendations.extend(self._get_confidence_recommendations(result.confidence))

        return PromptTemplate(
            title=f"RISK Stage Review - {pipeline_id}",
            summary=f"Risk assessment completed with {result.confidence.name} confidence.",
            details=details,
            risk_factors=risk_factors,
            questions=questions,
            recommendations=recommendations,
        )

    def _build_execution_prompt(self, result: StageResult, pipeline_id: str) -> PromptTemplate:
        """Build prompt for EXECUTION stage review."""
        output = result.output or {}

        details = [
            f"Mode: {output.get('mode', 'Unknown')}",
            f"Dry Run: {output.get('dry_run', True)}",
            f"Orders Submitted: {output.get('orders_submitted', 0)}",
            f"Orders Filled: {output.get('orders_filled', 0)}",
            f"Avg Slippage: {output.get('avg_slippage_pct', 0):.3f}%",
            f"Total Commission: ${output.get('total_commission', 0):.2f}",
        ]

        risk_factors = []
        if output.get("mode") == "live" and not output.get("dry_run"):
            risk_factors.append("LIVE MODE - Real money at risk!")
        if output.get("avg_slippage_pct", 0) > 0.5:
            risk_factors.append(f"High slippage: {output.get('avg_slippage_pct')}%")
        rejected = output.get("orders_submitted", 0) - output.get("orders_filled", 0)
        if rejected > 0:
            risk_factors.append(f"{rejected} orders not filled")

        questions = [
            "Is this the correct execution mode (paper/live)?",
            "Are the order sizes and prices correct?",
            "Have all safety checks passed?",
        ]

        recommendations = []
        if output.get("mode") == "live":
            recommendations.append("CRITICAL: Verify account and API credentials")
            recommendations.append("CRITICAL: Confirm this is intentional live execution")
        recommendations.extend(self._get_confidence_recommendations(result.confidence))

        return PromptTemplate(
            title=f"EXECUTION Stage Review - {pipeline_id}",
            summary=f"Execution prepared with {result.confidence.name} confidence.",
            details=details,
            risk_factors=risk_factors,
            questions=questions,
            recommendations=recommendations,
        )

    def _build_monitoring_prompt(self, result: StageResult, pipeline_id: str) -> PromptTemplate:
        """Build prompt for MONITORING stage review."""
        output = result.output or {}
        alerts = output.get("alerts", {})

        details = [
            f"Metrics Tracked: {output.get('metrics', [])}",
            f"Alert - Drawdown: {alerts.get('drawdown_pct', 'N/A')}%",
            f"Alert - Daily Loss: {alerts.get('daily_loss_pct', 'N/A')}%",
            f"Dashboard: {'Enabled' if output.get('dashboard', {}).get('enabled') else 'Disabled'}",
            f"Discord: {'Configured' if output.get('notifications', {}).get('discord_webhook') else 'Not configured'}",
        ]

        risk_factors = []
        if not output.get("notifications", {}).get("discord_webhook"):
            risk_factors.append("No Discord alerts - may miss critical notifications")
        if alerts.get("drawdown_pct", 0) > 15:
            risk_factors.append(f"Drawdown alert threshold high: {alerts.get('drawdown_pct')}%")

        questions = [
            "Are alert thresholds appropriate for the strategy?",
            "Is there adequate notification coverage?",
            "Will someone be available to respond to alerts?",
        ]

        return PromptTemplate(
            title=f"MONITORING Stage Review - {pipeline_id}",
            summary=f"Monitoring configuration completed with {result.confidence.name} confidence.",
            details=details,
            risk_factors=risk_factors,
            questions=questions,
            recommendations=self._get_confidence_recommendations(result.confidence),
        )

    def _build_generic_prompt(self, result: StageResult, pipeline_id: str) -> PromptTemplate:
        """Build generic prompt for unknown stages."""
        output = result.output or {}

        details = [f"{k}: {v}" for k, v in list(output.items())[:5]]

        return PromptTemplate(
            title=f"{result.stage.value.upper()} Stage Review - {pipeline_id}",
            summary=f"Stage completed with {result.confidence.name} confidence.",
            details=details,
            risk_factors=[result.review_reason] if result.review_reason else [],
            questions=["Is this result acceptable?", "Should the pipeline proceed?"],
            recommendations=self._get_confidence_recommendations(result.confidence),
        )

    def _get_confidence_recommendations(self, confidence: Confidence) -> list[str]:
        """Get recommendations based on confidence level."""
        if confidence == Confidence.HIGH_CONFIDENCE:
            return ["Result meets quality thresholds - approval recommended"]
        elif confidence == Confidence.MEDIUM_CONFIDENCE:
            return [
                "Result is acceptable but review details before approving",
                "Consider additional validation if proceeding to live trading",
            ]
        elif confidence == Confidence.LOW_CONFIDENCE:
            return [
                "Result has quality issues - careful review required",
                "Rejection recommended unless issues are understood and acceptable",
            ]
        elif confidence == Confidence.CONFLICT:
            return [
                "Multiple validation sources disagree",
                "Manual investigation required before proceeding",
                "Consider re-running with adjusted parameters",
            ]
        else:  # UNSOLVABLE
            return [
                "Unable to determine result quality",
                "Investigation required before any action",
                "Consider rejecting and investigating the cause",
            ]


def build_approval_prompt(result: StageResult, pipeline_id: str) -> str:
    """
    Convenience function to build and render an approval prompt.

    Args:
        result: Stage result to build prompt for
        pipeline_id: Pipeline identifier

    Returns:
        Rendered prompt string
    """
    builder = ApprovalPromptBuilder()
    template = builder.build(result, pipeline_id)
    return template.render()


def build_compact_prompt(result: StageResult, pipeline_id: str) -> str:
    """
    Build compact single-line prompt.

    Args:
        result: Stage result to build prompt for
        pipeline_id: Pipeline identifier

    Returns:
        Compact prompt string
    """
    builder = ApprovalPromptBuilder()
    template = builder.build(result, pipeline_id)
    return template.render_compact()
