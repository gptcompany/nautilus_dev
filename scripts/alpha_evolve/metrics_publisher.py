"""
Evolution Metrics Publisher - Syncs evolution data to QuestDB for Grafana dashboards.

Part of spec-010: Alpha-Evolve Grafana Dashboard
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from monitoring.client import MetricsClient
    from scripts.alpha_evolve.store import Program

from monitoring.models import EvolutionMetrics

logger = logging.getLogger("alpha_evolve.metrics_publisher")

MutationOutcome = Literal["success", "syntax_error", "runtime_error", "timeout", "seed"]


class EvolutionMetricsPublisher:
    """Publishes evolution metrics to QuestDB for Grafana dashboards.

    Provides event-driven sync after each evaluation, enabling real-time
    dashboard updates with minimal latency.

    Example:
        async with MetricsClient() as client:
            publisher = EvolutionMetricsPublisher(client)
            await publisher.publish_evaluation(program, "success", 1234.5)
    """

    def __init__(self, client: MetricsClient) -> None:
        """Initialize with existing MetricsClient.

        Args:
            client: QuestDB metrics client (from monitoring.client)
        """
        self._client = client

    async def publish_evaluation(
        self,
        program: Program,
        mutation_outcome: MutationOutcome = "success",
        mutation_latency_ms: float = 0.0,
    ) -> bool:
        """Publish strategy evaluation result to QuestDB.

        Args:
            program: Evaluated program with metrics
            mutation_outcome: Result of mutation attempt
            mutation_latency_ms: API call latency in milliseconds

        Returns:
            True if write succeeded, False otherwise
        """
        if program.metrics is None:
            logger.warning(f"Program {program.id[:8]} has no metrics, skipping publish")
            return False

        from typing import cast

        metrics = EvolutionMetrics(
            timestamp=datetime.now(UTC),
            program_id=program.id,
            experiment=program.experiment or "unknown",
            generation=program.generation,
            parent_id=program.parent_id,
            sharpe=program.metrics.sharpe_ratio,
            calmar=program.metrics.calmar_ratio,
            max_dd=abs(program.metrics.max_drawdown * 100),  # Convert to percentage
            cagr=program.metrics.cagr,
            total_return=program.metrics.total_return,
            trade_count=program.metrics.trade_count,
            win_rate=program.metrics.win_rate,
            # MVP fields (2026-01-11)
            psr=program.metrics.psr,
            net_sharpe=program.metrics.net_sharpe,
            mutation_outcome=mutation_outcome,
            mutation_latency_ms=mutation_latency_ms,
        )

        success = await self._client.write(cast(Any, metrics))
        if success:
            logger.debug(f"Published metrics for {program.id[:8]} (gen={program.generation})")
        else:
            logger.error(f"Failed to publish metrics for {program.id[:8]}")

        return success

    async def publish_seed(
        self,
        program: Program,
    ) -> bool:
        """Publish seed strategy to QuestDB.

        Args:
            program: Seed program (generation 0, no parent)

        Returns:
            True if write succeeded, False otherwise
        """
        return await self.publish_evaluation(
            program,
            mutation_outcome="seed",
            mutation_latency_ms=0.0,
        )

    async def publish_mutation_failure(
        self,
        experiment: str,
        outcome: MutationOutcome,
        latency_ms: float,
    ) -> bool:
        """Publish failed mutation for tracking.

        Args:
            experiment: Experiment name
            outcome: Failure type (syntax_error, runtime_error, timeout)
            latency_ms: API call latency

        Returns:
            True if write succeeded, False otherwise
        """
        # Create a minimal metrics record for failed mutations
        # Use placeholder values since we have no actual metrics
        # NOTE: generation=0 used for failures (Pydantic constraint ge=0)
        # Failures are distinguished by mutation_outcome field instead
        from typing import cast

        metrics = EvolutionMetrics(
            timestamp=datetime.now(UTC),
            program_id="failed-mutation",
            experiment=experiment,
            generation=0,  # Use 0 (Pydantic ge=0 constraint); outcome indicates failure
            parent_id=None,
            sharpe=0.0,
            calmar=0.0,
            max_dd=0.0,
            cagr=0.0,
            total_return=0.0,
            trade_count=None,
            win_rate=None,
            mutation_outcome=outcome,
            mutation_latency_ms=latency_ms,
        )

        success = await self._client.write(cast(Any, metrics))
        if success:
            logger.debug(f"Published mutation failure: {outcome} ({latency_ms:.0f}ms)")
        else:
            logger.error(f"Failed to publish mutation failure: {outcome}")

        return success


__all__ = ["EvolutionMetricsPublisher", "MutationOutcome"]
