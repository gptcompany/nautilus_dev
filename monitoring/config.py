# monitoring.config - Configuration models
#
# T012: Create MonitoringConfig Pydantic model

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valid environment values - must match models.py validation
Environment = Literal["prod", "staging", "dev"]


class MonitoringConfig(BaseSettings):
    """Configuration for monitoring system.

    Can be loaded from environment variables with MONITORING_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="MONITORING_",
        env_file=".env",
    )

    # QuestDB connection
    questdb_host: str = Field(default="localhost", description="QuestDB hostname")
    questdb_http_port: int = Field(default=9000, description="QuestDB HTTP API port")
    questdb_ilp_port: int = Field(default=9009, description="QuestDB ILP port")

    # Environment
    env: Environment = Field(default="dev", description="Environment: prod, staging, dev")
    host: str = Field(default="localhost", description="This host's identifier")

    # Collection intervals (seconds)
    daemon_collect_interval: float = Field(
        default=10.0, description="Daemon metrics collection interval"
    )
    exchange_collect_interval: float = Field(
        default=5.0, description="Exchange status collection interval"
    )
    pipeline_collect_interval: float = Field(
        default=30.0, description="Pipeline metrics collection interval"
    )
    trading_collect_interval: float = Field(
        default=1.0, description="Trading metrics collection interval"
    )

    # Batching
    batch_size: int = Field(default=500, ge=1, le=10000, description="Batch size before flush")
    flush_interval: float = Field(
        default=5.0, ge=0.1, description="Max time between flushes (seconds)"
    )

    # Grafana (optional, for provisioning)
    grafana_url: str = Field(default="http://localhost:3000", description="Grafana URL")
    grafana_api_key: str | None = Field(
        default=None, description="Grafana API key for provisioning"
    )


# Alias for backward compatibility
MetricsClientConfig = MonitoringConfig


__all__ = ["MonitoringConfig", "MetricsClientConfig"]
