# monitoring.collectors - Metrics collectors for different data sources
#
# Base interface and implementations for daemon, exchange, pipeline, trading collectors

from abc import ABC, abstractmethod


class BaseCollector[T](ABC):
    """Base class for metrics collectors.

    Collectors poll data sources and emit metrics to QuestDB via MetricsClient.
    Each collector handles a specific metrics table.
    """

    @abstractmethod
    async def collect(self) -> list[T]:
        """Collect metrics from data source.

        Returns:
            List of metrics objects ready for QuestDB ingestion.
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start periodic collection."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop collection and cleanup resources."""
        pass


__all__ = ["BaseCollector"]
