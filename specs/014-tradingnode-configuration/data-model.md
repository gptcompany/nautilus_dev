# Data Model: TradingNode Configuration

**Feature**: 014-tradingnode-configuration
**Date**: 2025-12-28

## Overview

This document defines the data models for the TradingNode configuration system. All models use Pydantic for validation and are designed to load values from environment variables.

---

## 1. Core Entities

### 1.1 ConfigEnvironment

Represents the deployment environment settings.

```python
from pydantic import BaseModel, Field
from typing import Literal

class ConfigEnvironment(BaseModel):
    """Core environment configuration."""

    trader_id: str = Field(
        ...,
        pattern=r"^[A-Z0-9-]+$",
        description="Unique trader identifier (e.g., PROD-TRADER-001)"
    )
    environment: Literal["LIVE", "SANDBOX"] = Field(
        default="SANDBOX",
        description="Trading environment"
    )

    # Validation
    @field_validator("trader_id")
    @classmethod
    def validate_trader_id(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 32:
            raise ValueError("trader_id must be 3-32 characters")
        return v
```

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| trader_id | str | Yes | - | Pattern: `^[A-Z0-9-]+$`, length 3-32 |
| environment | Literal | No | SANDBOX | LIVE or SANDBOX |

---

### 1.2 RedisConfig

Redis connection configuration.

```python
class RedisConfig(BaseModel):
    """Redis connection configuration."""

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    password: str | None = Field(default=None, description="Redis password")
    timeout: float = Field(default=2.0, ge=0.1, le=30.0, description="Connection timeout")
```

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| host | str | No | localhost | - |
| port | int | No | 6379 | 1-65535 |
| password | str | None | None | - |
| timeout | float | No | 2.0 | 0.1-30.0 |

---

### 1.3 LoggingSettings

Logging configuration.

```python
class LoggingSettings(BaseModel):
    """Logging configuration."""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Console log level"
    )
    log_level_file: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="DEBUG",
        description="File log level"
    )
    log_directory: str = Field(
        default="/var/log/nautilus",
        description="Log file directory"
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log file format"
    )
    max_size_mb: int = Field(default=100, ge=10, le=1000, description="Max log file size")
    max_backup_count: int = Field(default=10, ge=1, le=100, description="Max backup files")
```

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| log_level | Literal | No | INFO | DEBUG/INFO/WARNING/ERROR |
| log_level_file | Literal | No | DEBUG | DEBUG/INFO/WARNING/ERROR |
| log_directory | str | No | /var/log/nautilus | - |
| log_format | Literal | No | json | json or text |
| max_size_mb | int | No | 100 | 10-1000 |
| max_backup_count | int | No | 10 | 1-100 |

---

### 1.4 StreamingSettings

Data streaming configuration.

```python
class StreamingSettings(BaseModel):
    """Streaming/catalog configuration."""

    catalog_path: str = Field(
        default="/data/nautilus/catalog",
        description="Path to data catalog"
    )
    flush_interval_ms: int = Field(
        default=2000,
        ge=100,
        le=10000,
        description="Flush interval in milliseconds"
    )
    rotation_mode: Literal["NONE", "SIZE", "TIME"] = Field(
        default="SIZE",
        description="File rotation mode"
    )
    max_file_size_mb: int = Field(
        default=128,
        ge=16,
        le=1024,
        description="Max file size before rotation"
    )
```

**Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| catalog_path | str | No | /data/nautilus/catalog | - |
| flush_interval_ms | int | No | 2000 | 100-10000 |
| rotation_mode | Literal | No | SIZE | NONE/SIZE/TIME |
| max_file_size_mb | int | No | 128 | 16-1024 |

---

## 2. Exchange Credentials

### 2.1 ExchangeCredentials (Base)

```python
class ExchangeCredentials(BaseModel):
    """Base exchange credentials."""

    api_key: str = Field(..., min_length=16, description="API key")
    api_secret: str = Field(..., min_length=16, description="API secret")
    testnet: bool = Field(default=False, description="Use testnet")

    @field_validator("api_key", "api_secret")
    @classmethod
    def validate_not_placeholder(cls, v: str) -> str:
        if v.startswith("xxx") or v == "your_api_key":
            raise ValueError("Placeholder credentials not allowed")
        return v
```

---

### 2.2 BinanceCredentials

```python
class BinanceCredentials(ExchangeCredentials):
    """Binance-specific credentials."""

    account_type: Literal["SPOT", "USDT_FUTURES", "COIN_FUTURES"] = Field(
        default="USDT_FUTURES",
        description="Binance account type"
    )
    us: bool = Field(default=False, description="Use Binance.US endpoints")
```

**Additional Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| account_type | Literal | No | USDT_FUTURES | SPOT/USDT_FUTURES/COIN_FUTURES |
| us | bool | No | False | - |

---

### 2.3 BybitCredentials

```python
class BybitCredentials(ExchangeCredentials):
    """Bybit-specific credentials."""

    product_types: list[Literal["LINEAR", "INVERSE", "SPOT", "OPTION"]] = Field(
        default=["LINEAR"],
        description="Bybit product types"
    )
    demo: bool = Field(default=False, description="Use demo mode")

    @field_validator("product_types")
    @classmethod
    def validate_product_types(cls, v: list) -> list:
        if "SPOT" in v and len(v) > 1:
            raise ValueError("SPOT cannot be mixed with derivatives")
        return v
```

**Additional Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| product_types | list[Literal] | No | ["LINEAR"] | Cannot mix SPOT with derivatives |
| demo | bool | No | False | - |

---

## 3. Configuration Factory Models

### 3.1 TradingNodeSettings

Complete settings model combining all configuration sections.

```python
class TradingNodeSettings(BaseModel):
    """Complete TradingNode settings."""

    # Core
    environment: ConfigEnvironment

    # Infrastructure
    redis: RedisConfig = Field(default_factory=RedisConfig)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    streaming: StreamingSettings = Field(default_factory=StreamingSettings)

    # Exchange credentials
    binance: BinanceCredentials | None = None
    bybit: BybitCredentials | None = None

    # Execution settings
    reconciliation_lookback_mins: int = Field(default=60, ge=60, le=1440)
    reconciliation_startup_delay_secs: float = Field(default=10.0, ge=10.0, le=60.0)

    # Rate limits
    max_order_submit_rate: str = Field(default="100/00:00:01")
    max_order_modify_rate: str = Field(default="100/00:00:01")

    @model_validator(mode="after")
    def validate_at_least_one_exchange(self) -> "TradingNodeSettings":
        if self.binance is None and self.bybit is None:
            raise ValueError("At least one exchange must be configured")
        return self
```

---

## 4. State Transitions

### 4.1 TradingNode Lifecycle

```
                    ┌─────────────┐
                    │  CREATED    │
                    └──────┬──────┘
                           │ build()
                           ▼
                    ┌─────────────┐
                    │  BUILDING   │
                    └──────┬──────┘
                           │ complete
                           ▼
                    ┌─────────────┐
                    │   BUILT     │
                    └──────┬──────┘
                           │ run()
                           ▼
                    ┌─────────────┐
                    │  STARTING   │◄────────────┐
                    └──────┬──────┘             │
                           │ connected          │ reconnect
                           ▼                    │
                    ┌─────────────┐             │
                    │  RUNNING    │─────────────┘
                    └──────┬──────┘
                           │ stop()
                           ▼
                    ┌─────────────┐
                    │  STOPPING   │
                    └──────┬──────┘
                           │ complete
                           ▼
                    ┌─────────────┐
                    │  STOPPED    │
                    └──────┬──────┘
                           │ dispose()
                           ▼
                    ┌─────────────┐
                    │  DISPOSED   │
                    └─────────────┘
```

---

## 5. Validation Rules

### 5.1 Environment Variables

| Variable | Required | Validation |
|----------|----------|------------|
| NAUTILUS_TRADER_ID | Yes | Pattern: `^[A-Z0-9-]+$` |
| NAUTILUS_ENVIRONMENT | No | LIVE or SANDBOX |
| REDIS_HOST | No | Valid hostname |
| REDIS_PORT | No | 1-65535 |
| BINANCE_API_KEY | If Binance | Min 16 chars, not placeholder |
| BINANCE_API_SECRET | If Binance | Min 16 chars, not placeholder |
| BYBIT_API_KEY | If Bybit | Min 16 chars, not placeholder |
| BYBIT_API_SECRET | If Bybit | Min 16 chars, not placeholder |

### 5.2 Cross-Field Validation

1. **At least one exchange**: Either Binance or Bybit credentials must be provided
2. **Bybit product types**: Cannot mix SPOT with derivative product types
3. **Reconciliation settings**: `reconciliation_lookback_mins >= 60` (enforced by NautilusTrader)
4. **Reconciliation delay**: `reconciliation_startup_delay_secs >= 10.0` (recommended minimum)

---

## 6. Entity Relationships

```
TradingNodeSettings
├── ConfigEnvironment (1:1)
├── RedisConfig (1:1)
├── LoggingSettings (1:1)
├── StreamingSettings (1:1)
├── BinanceCredentials (0..1)
└── BybitCredentials (0..1)

TradingNodeConfig (NautilusTrader native)
├── CacheConfig
│   └── DatabaseConfig (Redis)
├── LiveExecEngineConfig
├── LiveDataEngineConfig
├── LiveRiskEngineConfig
├── LoggingConfig
├── StreamingConfig
├── data_clients: dict[str, DataClientConfig]
└── exec_clients: dict[str, ExecClientConfig]
```

---

## 7. Example Usage

```python
from config import TradingNodeSettings
from config.factory import TradingNodeConfigFactory

# Load from environment
settings = TradingNodeSettings(
    environment=ConfigEnvironment(
        trader_id=os.environ["NAUTILUS_TRADER_ID"],
        environment=os.environ.get("NAUTILUS_ENVIRONMENT", "SANDBOX"),
    ),
    binance=BinanceCredentials(
        api_key=os.environ["BINANCE_API_KEY"],
        api_secret=os.environ["BINANCE_API_SECRET"],
        testnet=os.environ.get("BINANCE_TESTNET", "false").lower() == "true",
    ),
)

# Generate NautilusTrader config
config = TradingNodeConfigFactory.from_settings(settings)
```
