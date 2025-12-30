---
name: pydantic-model-generator
description: Auto-generate Pydantic models from schema descriptions with type hints, validation rules, examples, and JSON schema export. 75% token savings (2,000->500).
---

# Pydantic Model Generator

Generate standardized Pydantic models for NautilusTrader configuration and data structures with complete type safety and validation.

## Quick Start

**User says**: "Create Pydantic model for StrategyConfig with instrument_id, ema_period, and risk_percent"

**Skill generates**:
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal

class StrategyConfig(BaseModel):
    """Configuration for trading strategy"""

    instrument_id: str = Field(
        ...,
        description="NautilusTrader instrument ID (e.g., BTCUSDT.BINANCE)",
        example="BTCUSDT.BINANCE"
    )
    ema_period: int = Field(
        default=20,
        description="EMA indicator period",
        ge=1,
        le=500,
        example=20
    )
    risk_percent: Decimal = Field(
        default=Decimal("0.02"),
        description="Risk per trade as decimal (0.02 = 2%)",
        ge=Decimal("0.001"),
        le=Decimal("0.10"),
        example=Decimal("0.02")
    )

    @field_validator('instrument_id')
    @classmethod
    def validate_instrument_id(cls, v: str) -> str:
        if '.' not in v:
            raise ValueError('instrument_id must be in format SYMBOL.VENUE')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "instrument_id": "BTCUSDT.BINANCE",
                "ema_period": 20,
                "risk_percent": "0.02"
            }
        }
    }
```

## Templates

### 1. Strategy Config Template
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from decimal import Decimal

class {StrategyName}Config(BaseModel):
    """Configuration for {StrategyName}"""

    instrument_id: str = Field(
        ...,
        description="NautilusTrader instrument ID"
    )
    order_type: Literal["MARKET", "LIMIT"] = Field(
        default="MARKET",
        description="Order type for entries"
    )
    # Indicator parameters
    {indicator}_period: int = Field(
        default={default},
        ge=1,
        le=500
    )
    # Risk parameters
    risk_percent: Decimal = Field(
        default=Decimal("0.02"),
        ge=Decimal("0.001"),
        le=Decimal("0.10")
    )
    max_position_size: Optional[Decimal] = Field(
        default=None,
        description="Maximum position size in base currency"
    )

    @field_validator('instrument_id')
    @classmethod
    def validate_instrument_id(cls, v: str) -> str:
        if '.' not in v:
            raise ValueError('instrument_id must be in format SYMBOL.VENUE')
        return v
```

### 2. Data Model Template
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class {ModelName}(BaseModel):
    """Data model for {description}"""

    timestamp: datetime = Field(
        ...,
        description="Event timestamp"
    )
    price: Decimal = Field(
        ...,
        description="Price in quote currency",
        ge=Decimal("0")
    )
    quantity: Decimal = Field(
        ...,
        description="Quantity in base currency",
        ge=Decimal("0")
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": "2025-01-01T00:00:00Z",
                "price": "100000.50",
                "quantity": "0.5"
            }
        }
    }
```

### 3. Backtest Config Template
```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from pathlib import Path

class BacktestConfig(BaseModel):
    """Configuration for backtesting"""

    catalog_path: Path = Field(
        ...,
        description="Path to Parquet data catalog"
    )
    start_date: datetime = Field(
        ...,
        description="Backtest start date"
    )
    end_date: datetime = Field(
        ...,
        description="Backtest end date"
    )
    instruments: List[str] = Field(
        ...,
        description="List of instrument IDs to trade"
    )
    initial_capital: Decimal = Field(
        default=Decimal("100000"),
        description="Initial account capital"
    )

    @field_validator('catalog_path')
    @classmethod
    def validate_catalog_path(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f'Catalog path does not exist: {v}')
        return v

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
```

### 4. WebSocket Message Template
```python
from pydantic import BaseModel, Field
from typing import Literal, Union
from datetime import datetime
from decimal import Decimal

class PriceUpdateMessage(BaseModel):
    """WebSocket price update message"""

    type: Literal["price_update"] = "price_update"
    instrument_id: str = Field(..., description="Instrument identifier")
    bid: Decimal = Field(..., description="Best bid price")
    ask: Decimal = Field(..., description="Best ask price")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OrderUpdateMessage(BaseModel):
    """WebSocket order update message"""

    type: Literal["order_update"] = "order_update"
    order_id: str = Field(..., description="Order identifier")
    status: str = Field(..., description="Order status")
    filled_qty: Decimal = Field(default=Decimal("0"))

# Union type for all message types
WebSocketMessage = Union[PriceUpdateMessage, OrderUpdateMessage]
```

## Usage Patterns

### Pattern 1: From Schema Description
```
User: "Create model for RiskConfig with max_drawdown (0-1), daily_loss_limit, and stop_trading_on_breach (bool)"

Skill:
1. Parse field descriptions
2. Infer validators (max_drawdown: 0-1 range)
3. Generate Field() with constraints
4. Add example data
5. Write to configs/risk_config.py
```

### Pattern 2: From Existing JSON
```
User: "Generate Pydantic model from this backtest result JSON: {...}"

Skill:
1. Parse JSON structure
2. Infer types from values
3. Generate model with Optional fields
4. Add validators for ranges/enums
5. Include original JSON as example
```

### Pattern 3: Strategy Configuration
```
User: "Create config model for EMA crossover strategy"

Skill:
1. Generate strategy-specific config
2. Add indicator period fields
3. Include risk parameters
4. Add instrument_id validator
```

## Field Type Mapping

| Description | Python Type | Validation |
|-------------|-------------|------------|
| "instrument_id" | `str` | `validator: contains '.'` |
| "price" | `Decimal` | `ge=Decimal("0")` |
| "timestamp" | `datetime` | `default_factory=datetime.utcnow` |
| "percentage 0-100" | `float` | `ge=0, le=100` |
| "percentage 0-1" | `Decimal` | `ge=0.0, le=1.0` |
| "period" | `int` | `ge=1, le=500` |
| "file path" | `Path` | `validator: path.exists()` |
| "optional field" | `Optional[T]` | `default=None` |
| "list of items" | `List[T]` | `default_factory=list` |
| "order type" | `Literal["MARKET", "LIMIT"]` | type checking |

## NautilusTrader-Specific Validators

### Instrument ID Validator
```python
@field_validator('instrument_id')
@classmethod
def validate_instrument_id(cls, v: str) -> str:
    """Validate NautilusTrader instrument ID format"""
    if '.' not in v:
        raise ValueError('instrument_id must be in format SYMBOL.VENUE')
    symbol, venue = v.rsplit('.', 1)
    valid_venues = ['BINANCE', 'BYBIT', 'OKX', 'INTERACTIVE_BROKERS']
    if venue not in valid_venues:
        raise ValueError(f'Unknown venue: {venue}')
    return v
```

### Position Size Validator
```python
@field_validator('position_size')
@classmethod
def validate_position_size(cls, v: Decimal) -> Decimal:
    """Validate position size is reasonable"""
    if v <= Decimal("0"):
        raise ValueError('Position size must be positive')
    if v > Decimal("1000000"):
        raise ValueError('Position size exceeds maximum')
    return v
```

### Date Range Validator
```python
@field_validator('end_date')
@classmethod
def validate_date_range(cls, v: datetime, info) -> datetime:
    """Validate end_date is after start_date"""
    if 'start_date' in info.data and v <= info.data['start_date']:
        raise ValueError('end_date must be after start_date')
    return v
```

## Output Format

**Generated model file**:
```python
"""
{Module} Configuration Models

Pydantic models for {description}.
Auto-generated by pydantic-model-generator Skill.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal, Union
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Model definitions here...

# JSON Schema export
if __name__ == "__main__":
    import json
    print(json.dumps({ModelName}.model_json_schema(), indent=2))
```

## Automatic Invocation

**Triggers**:
- "create pydantic model for [name]"
- "generate config model for [strategy]"
- "pydantic schema for [fields]"
- "strategy config model for [description]"
- "backtest config model"
- "model from json [data]"

**Does NOT trigger**:
- Complex business logic (use subagent)
- Database ORM models (different pattern)
- NautilusTrader internal models (use native)

## Token Savings

| Task | Without Skill | With Skill | Savings |
|------|--------------|------------|---------|
| Basic model (3 fields) | ~800 tokens | ~200 tokens | 75% |
| Model with validators | ~1,200 tokens | ~300 tokens | 75% |
| Strategy config | ~1,500 tokens | ~400 tokens | 73% |
| Backtest config | ~2,000 tokens | ~500 tokens | 75% |

**Average Savings**: 75% (2,000 -> 500 tokens)
