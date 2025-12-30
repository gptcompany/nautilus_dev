"""TradingNode Recovery Configuration (Spec 017).

Production configuration template for TradingNode with position recovery enabled.
Uses native NautilusTrader reconciliation and Redis cache persistence.
"""

from nautilus_trader.config import (
    CacheConfig,
    DatabaseConfig,
    LiveExecEngineConfig,
    TradingNodeConfig,
)


def create_recovery_enabled_config(
    trader_id: str = "TRADER-001",
    redis_host: str = "localhost",
    redis_port: int = 6379,
    reconciliation_delay_secs: float = 10.0,
) -> TradingNodeConfig:
    """Create TradingNode configuration with position recovery enabled.

    This configuration enables:
    - Redis cache persistence with msgpack encoding
    - Position and order state preservation across restarts
    - Automatic reconciliation with exchange on startup
    - External position claiming for strategies

    Args:
        trader_id: Unique identifier for the trader instance.
        redis_host: Redis server hostname.
        redis_port: Redis server port.
        reconciliation_delay_secs: Delay before reconciliation starts.

    Returns:
        TradingNodeConfig with recovery settings.

    Example:
        >>> config = create_recovery_enabled_config(
        ...     trader_id="TRADER-001",
        ...     redis_host="redis.internal",
        ...     reconciliation_delay_secs=15.0,
        ... )
        >>> node = TradingNode(config)
    """
    return TradingNodeConfig(
        trader_id=trader_id,
        # Redis cache - CRITICAL: flush_on_start=False preserves state
        cache=CacheConfig(
            database=DatabaseConfig(
                type="redis",
                host=redis_host,
                port=redis_port,
            ),
            encoding="msgpack",  # Faster than JSON
            timestamps_as_iso8601=True,
            buffer_interval_ms=100,  # Buffer writes for performance
            flush_on_start=False,  # CRITICAL: Preserve state across restarts
        ),
        # Execution engine with reconciliation enabled
        exec_engine=LiveExecEngineConfig(
            reconciliation=True,
            reconciliation_startup_delay_secs=reconciliation_delay_secs,
            generate_missing_orders=True,  # Generate synthetic orders for gaps
        ),
    )


# Default recovery-enabled configuration
DEFAULT_RECOVERY_CONFIG = create_recovery_enabled_config()
