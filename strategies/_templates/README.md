# Strategy Templates

Base classes for all strategies. **DO NOT MODIFY** unless updating all strategies.

## Available Templates

| Template | Purpose |
|----------|---------|
| `base_strategy.py` | Standard strategy base class |
| `base_evolve.py` | Alpha-evolve compatible base |

## Usage

```python
from strategies._templates.base_strategy import BaseStrategy, BaseStrategyConfig

class MyStrategy(BaseStrategy):
    def __init__(self, config: MyStrategyConfig):
        super().__init__(config)
```
