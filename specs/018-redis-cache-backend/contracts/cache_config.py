"""Redis Cache Backend Contracts (Spec 018)"""

from pydantic import BaseModel, Field

class RedisDatabaseConfig(BaseModel):
    """Redis connection configuration."""
    type: str = "redis"
    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    ssl: bool = False
    timeout: int = Field(default=2, ge=1, le=30)

class RedisCacheConfig(BaseModel):
    """NautilusTrader cache configuration for Redis."""
    database: RedisDatabaseConfig
    encoding: str = Field(default="msgpack", pattern="^(msgpack|json)$")
    timestamps_as_iso8601: bool = False
    persist_account_events: bool = True
    buffer_interval_ms: int = Field(default=100, ge=0, le=1000)
    use_trader_prefix: bool = True
    use_instance_id: bool = False
    flush_on_start: bool = False
    tick_capacity: int = Field(default=10_000, ge=0)
    bar_capacity: int = Field(default=10_000, ge=0)
