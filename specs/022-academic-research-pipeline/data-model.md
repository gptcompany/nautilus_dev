# Data Model: Academic Research Pipeline

**Spec**: 022-academic-research-pipeline
**Version**: 1.0

## Entity Schemas

### strategy__ Entity (NEW - academic_research)

```json
{
  "entity_type": "strategy__",
  "id_pattern": "strategy__{methodology}_{asset}_{year}",
  "example_id": "strategy__momentum_reversal_btc_2024",
  "schema": {
    "id": {
      "type": "string",
      "format": "strategy__{methodology}_{asset}_{year}",
      "description": "Canonical identifier",
      "required": true
    },
    "name": {
      "type": "string",
      "description": "Human-readable strategy name",
      "required": true
    },
    "source_paper": {
      "type": "string",
      "format": "source__{arxiv_id|doi}",
      "description": "Reference to paper entity",
      "required": true
    },
    "methodology": {
      "type": "object",
      "required": true,
      "properties": {
        "type": {
          "type": "string",
          "enum": ["momentum", "mean_reversion", "market_making", "arbitrage", "trend_following", "statistical_arbitrage"],
          "required": true
        },
        "entry_logic": {
          "type": "string",
          "description": "Natural language description of entry conditions",
          "required": true
        },
        "exit_logic": {
          "type": "string",
          "description": "Natural language description of exit conditions",
          "required": true
        },
        "position_sizing": {
          "type": "string",
          "enum": ["fixed", "volatility_scaled", "kelly", "equal_weight", "risk_parity"],
          "default": "fixed"
        },
        "risk_management": {
          "type": "string",
          "description": "Stop-loss, trailing stop, max drawdown rules",
          "required": true
        }
      }
    },
    "indicators": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "params": {"type": "object"}
        }
      },
      "description": "Technical indicators used"
    },
    "backtest_results": {
      "type": "object",
      "properties": {
        "period": {
          "type": "string",
          "format": "YYYY-YYYY",
          "example": "2020-2024"
        },
        "assets": {
          "type": "array",
          "items": {"type": "string"}
        },
        "sharpe_ratio": {"type": "number"},
        "max_drawdown": {"type": "number", "format": "decimal (0.15 = 15%)"},
        "annual_return": {"type": "number", "format": "decimal"},
        "win_rate": {"type": "number", "format": "decimal"},
        "profit_factor": {"type": "number"}
      }
    },
    "nautilus_mapping": {
      "type": "object",
      "description": "Mapping to NautilusTrader primitives",
      "properties": {
        "indicators": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Native Rust indicator class names",
          "example": ["ExponentialMovingAverage", "RelativeStrengthIndex"]
        },
        "order_types": {
          "type": "array",
          "items": {"type": "string"},
          "example": ["MARKET", "LIMIT", "STOP_MARKET"]
        },
        "events": {
          "type": "array",
          "items": {"type": "string"},
          "example": ["PositionOpened", "OrderFilled", "PositionClosed"]
        },
        "custom_indicators_needed": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Indicators not available in NautilusTrader"
        }
      }
    },
    "implementation_status": {
      "type": "string",
      "enum": ["researched", "specified", "implemented", "backtested", "deployed"],
      "default": "researched"
    },
    "observations": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Key insights from paper"
    },
    "created_at": {
      "type": "string",
      "format": "ISO 8601"
    },
    "updated_at": {
      "type": "string",
      "format": "ISO 8601"
    }
  }
}
```

### Example strategy__ Entity

```json
{
  "id": "strategy__momentum_reversal_crypto_2023",
  "name": "Crypto Momentum Reversal Strategy",
  "source_paper": "source__arxiv_2301.12345",
  "methodology": {
    "type": "momentum",
    "entry_logic": "Enter long when RSI crosses above 30 after being below 30 for 3+ bars, and price is above 50-day EMA",
    "exit_logic": "Exit when RSI crosses above 70, or trailing stop of 2% triggered, or 5-day holding period reached",
    "position_sizing": "volatility_scaled",
    "risk_management": "2% trailing stop, max 5% portfolio per position, 20% max drawdown circuit breaker"
  },
  "indicators": [
    {"name": "EMA", "params": {"period": 50}},
    {"name": "RSI", "params": {"period": 14}},
    {"name": "ATR", "params": {"period": 14}}
  ],
  "backtest_results": {
    "period": "2020-2023",
    "assets": ["BTC", "ETH", "SOL"],
    "sharpe_ratio": 1.8,
    "max_drawdown": 0.18,
    "annual_return": 0.45,
    "win_rate": 0.58,
    "profit_factor": 1.9
  },
  "nautilus_mapping": {
    "indicators": [
      "ExponentialMovingAverage",
      "RelativeStrengthIndex",
      "AverageTrueRange"
    ],
    "order_types": ["MARKET", "STOP_MARKET"],
    "events": ["PositionOpened", "PositionChanged", "PositionClosed"],
    "custom_indicators_needed": []
  },
  "implementation_status": "researched",
  "observations": [
    "Works best in trending markets",
    "Underperforms during consolidation",
    "Slippage significantly impacts returns at high frequency"
  ],
  "created_at": "2025-12-28T14:00:00Z",
  "updated_at": "2025-12-28T14:00:00Z"
}
```

---

## Relationship Types

### strategy__ Relationships

| Relationship | Source | Target | Description |
|--------------|--------|--------|-------------|
| `based_on` | strategy__ | source__ | Paper that defines the strategy |
| `uses_concept` | strategy__ | concept__ | Methods/algorithms used |
| `targets_asset` | strategy__ | domain__ | Asset class/market |
| `implemented_by` | strategy__ | code_repo__ | GitHub implementation |
| `evolved_from` | strategy__ | strategy__ | Parent strategy (for variations) |
| `competes_with` | strategy__ | strategy__ | Similar strategies for comparison |

### Example Relationships

```json
{
  "relationships": [
    {
      "source": "strategy__momentum_reversal_crypto_2023",
      "relation": "based_on",
      "target": "source__arxiv_2301.12345"
    },
    {
      "source": "strategy__momentum_reversal_crypto_2023",
      "relation": "uses_concept",
      "target": "concept__mean_reversion"
    },
    {
      "source": "strategy__momentum_reversal_crypto_2023",
      "relation": "targets_asset",
      "target": "domain__crypto_futures"
    }
  ]
}
```

---

## Synced Data Model (nautilus_dev)

### strategies.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Synced Strategies",
  "type": "object",
  "properties": {
    "synced_at": {
      "type": "string",
      "format": "ISO 8601"
    },
    "source": {
      "type": "string",
      "description": "Path to memory.json"
    },
    "strategies": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/strategy__"
      }
    },
    "count": {
      "type": "integer"
    }
  },
  "definitions": {
    "strategy__": {
      "type": "object",
      "description": "Subset of strategy__ entity relevant for nautilus_dev"
    }
  }
}
```

---

## NautilusTrader Indicator Mapping

### Native Indicators (Use These)

| Paper Term | NautilusTrader Class | Module |
|------------|---------------------|--------|
| EMA, Exponential MA | `ExponentialMovingAverage` | `nautilus_trader.indicators.average.ema` |
| SMA, Simple MA | `SimpleMovingAverage` | `nautilus_trader.indicators.average.sma` |
| RSI | `RelativeStrengthIndex` | `nautilus_trader.indicators.momentum.rsi` |
| MACD | `MovingAverageConvergenceDivergence` | `nautilus_trader.indicators.momentum.macd` |
| ATR | `AverageTrueRange` | `nautilus_trader.indicators.volatility.atr` |
| Bollinger Bands | `BollingerBands` | `nautilus_trader.indicators.volatility.bb` |
| Stochastic | `Stochastic` | `nautilus_trader.indicators.momentum.stoch` |
| ADX | `AverageDirectionalIndex` | `nautilus_trader.indicators.momentum.adx` |

### Order Type Mapping

| Paper Term | NautilusTrader Enum | Notes |
|------------|---------------------|-------|
| Market order | `OrderType.MARKET` | Immediate execution |
| Limit order | `OrderType.LIMIT` | Specified price |
| Stop loss | `OrderType.STOP_MARKET` | Use `reduce_only=True` |
| Stop limit | `OrderType.STOP_LIMIT` | Stop with limit price |
| Take profit | `OrderType.LIMIT` | Or `MARKET_IF_TOUCHED` |
| Trailing stop | `OrderType.TRAILING_STOP_MARKET` | Not all exchanges |

### Event Mapping

| Paper Concept | NautilusTrader Event | Handler Method |
|---------------|---------------------|----------------|
| Position opened | `PositionOpened` | `on_event()` |
| Position closed | `PositionClosed` | `on_event()` |
| Order filled | `OrderFilled` | `on_event()` |
| Stop triggered | `OrderFilled` | Check `order.type` |
| Bar received | `Bar` | `on_bar()` |
| Tick received | `QuoteTick`/`TradeTick` | `on_quote_tick()`/`on_trade_tick()` |

---

## Validation Rules

### strategy__ Entity Validation

```python
def validate_strategy_entity(entity: dict) -> bool:
    """Validate strategy__ entity before storage."""

    # Required fields
    required = ["id", "name", "source_paper", "methodology"]
    for field in required:
        if field not in entity:
            raise ValueError(f"Missing required field: {field}")

    # ID format
    if not entity["id"].startswith("strategy__"):
        raise ValueError("ID must start with 'strategy__'")

    # Methodology type
    valid_types = ["momentum", "mean_reversion", "market_making",
                   "arbitrage", "trend_following", "statistical_arbitrage"]
    if entity["methodology"]["type"] not in valid_types:
        raise ValueError(f"Invalid methodology type: {entity['methodology']['type']}")

    # Source paper reference
    if not entity["source_paper"].startswith("source__"):
        raise ValueError("source_paper must reference a source__ entity")

    # Backtest metrics range
    if "backtest_results" in entity:
        br = entity["backtest_results"]
        if br.get("max_drawdown", 0) > 1 or br.get("max_drawdown", 0) < 0:
            raise ValueError("max_drawdown must be between 0 and 1")
        if br.get("sharpe_ratio", 0) < -10 or br.get("sharpe_ratio", 0) > 10:
            raise ValueError("sharpe_ratio seems unrealistic")

    return True
```

---

## State Transitions

### implementation_status Flow

```
researched → specified → implemented → backtested → deployed
    │            │            │             │
    │            │            │             └── Live trading
    │            │            └── Working code, unit tests pass
    │            └── spec.md created via paper-to-strategy
    └── strategy__ entity created from paper
```

### Status Change Triggers

| From | To | Trigger |
|------|-----|---------|
| - | researched | Paper analyzed, entity created |
| researched | specified | paper-to-strategy skill executed |
| specified | implemented | alpha-evolve generates code |
| implemented | backtested | test-runner passes all tests |
| backtested | deployed | Manual approval for live trading |
