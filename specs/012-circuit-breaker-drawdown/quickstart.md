# Quickstart: Circuit Breaker (Max Drawdown)

## Overview

The Circuit Breaker provides portfolio-level drawdown protection by monitoring equity and enforcing graduated risk reduction as drawdown increases.

## Installation

The circuit breaker is part of the `risk` module:

```python
from risk import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerState
```

## Basic Usage

### 1. Create Configuration

```python
from decimal import Decimal
from risk import CircuitBreakerConfig

config = CircuitBreakerConfig(
    level1_drawdown_pct=Decimal("0.10"),   # 10% - WARNING
    level2_drawdown_pct=Decimal("0.15"),   # 15% - REDUCING
    level3_drawdown_pct=Decimal("0.20"),   # 20% - HALTED
    auto_recovery=False,                    # Require manual reset
)
```

### 2. Initialize Circuit Breaker

```python
from risk import CircuitBreaker

# In strategy
circuit_breaker = CircuitBreaker(
    config=config,
    portfolio=self.portfolio,
)
```

### 3. Check Before Trading

```python
def on_bar(self, bar: Bar) -> None:
    # Update circuit breaker state
    self.circuit_breaker.update()

    # Check if trading allowed
    if not self.circuit_breaker.can_open_position():
        self.log.warning(f"Circuit breaker: {self.circuit_breaker.state}")
        return  # Skip entry logic

    # Adjust position size
    size = base_size * self.circuit_breaker.position_size_multiplier()

    # Continue with entry logic...
```

## Integration with RiskManager (Spec 011)

The circuit breaker integrates seamlessly with the RiskManager:

```python
from risk import RiskManager, RiskConfig, CircuitBreaker, CircuitBreakerConfig

class MyStrategy(Strategy):
    def __init__(self, config: MyStrategyConfig) -> None:
        super().__init__(config)

        # Circuit breaker for portfolio-level protection
        self.circuit_breaker = CircuitBreaker(
            config=CircuitBreakerConfig(),
            portfolio=self.portfolio,
        )

        # Risk manager with circuit breaker reference
        self.risk_manager = RiskManager(
            config=config.risk,
            strategy=self,
            circuit_breaker=self.circuit_breaker,
        )

    def on_event(self, event: Event) -> None:
        # RiskManager now checks circuit breaker automatically
        self.risk_manager.handle_event(event)
```

## State Machine

```
ACTIVE ──▶ WARNING ──▶ REDUCING ──▶ HALTED
   ▲                                   │
   └─────── (recovery) ◀───────────────┘
```

| State | Condition | Entries Allowed | Size Multiplier |
|-------|-----------|-----------------|-----------------|
| ACTIVE | drawdown < 10% | Yes | 1.0 (100%) |
| WARNING | 10% ≤ drawdown < 15% | Yes | 0.5 (50%) |
| REDUCING | 15% ≤ drawdown < 20% | No | 0.0 |
| HALTED | drawdown ≥ 20% | No | 0.0 |

## Manual Reset

When `auto_recovery=False` (default), the circuit breaker requires manual reset after HALTED:

```python
# After drawdown recovers and trader reviews situation
if circuit_breaker.state == CircuitBreakerState.HALTED:
    # Verify drawdown has recovered
    if circuit_breaker.current_drawdown < config.recovery_drawdown_pct:
        circuit_breaker.reset()
        log.info("Circuit breaker reset to ACTIVE")
```

## Monitoring

Circuit breaker state is logged to QuestDB for Grafana dashboards:

```sql
SELECT timestamp, state, current_drawdown, peak_equity
FROM circuit_breaker_state
WHERE trader_id = 'TRADER-001'
ORDER BY timestamp DESC
LIMIT 100;
```

## Best Practices

1. **Always update before checking**: Call `update()` before `can_open_position()`
2. **Use with RiskManager**: Combines position-level (stop-loss) with portfolio-level protection
3. **Conservative thresholds**: Start with 10/15/20% and adjust based on strategy volatility
4. **Manual reset**: Keep `auto_recovery=False` for production to require human review
5. **Monitor alerts**: Set up Grafana alerts for LEVEL 2+ triggers

## Example: Complete Strategy

```python
from nautilus_trader.trading.strategy import Strategy
from risk import RiskManager, RiskConfig, CircuitBreaker, CircuitBreakerConfig

class ProtectedMomentumStrategy(Strategy):
    def __init__(self, config):
        super().__init__(config)

        # Portfolio-level protection
        self.circuit_breaker = CircuitBreaker(
            config=CircuitBreakerConfig(
                level1_drawdown_pct=Decimal("0.10"),
                level2_drawdown_pct=Decimal("0.15"),
                level3_drawdown_pct=Decimal("0.20"),
            ),
            portfolio=self.portfolio,
        )

        # Position-level protection
        self.risk_manager = RiskManager(
            config=RiskConfig(
                stop_loss_pct=Decimal("0.02"),
            ),
            strategy=self,
            circuit_breaker=self.circuit_breaker,
        )

    def on_start(self):
        self.subscribe_bars(self.bar_type)
        self.log.info(
            f"Started with circuit breaker thresholds: "
            f"{self.circuit_breaker.config.level1_drawdown_pct}/"
            f"{self.circuit_breaker.config.level2_drawdown_pct}/"
            f"{self.circuit_breaker.config.level3_drawdown_pct}"
        )

    def on_bar(self, bar):
        # Update circuit breaker
        self.circuit_breaker.update()

        # Log state if not ACTIVE
        if self.circuit_breaker.state != CircuitBreakerState.ACTIVE:
            self.log.warning(
                f"Circuit breaker: {self.circuit_breaker.state.value}, "
                f"drawdown: {self.circuit_breaker.current_drawdown:.2%}"
            )

        # Skip entries if not allowed
        if not self.circuit_breaker.can_open_position():
            return

        # Entry logic with adjusted size
        if self._should_enter():
            size = self.base_size * self.circuit_breaker.position_size_multiplier()
            self._submit_order(size)

    def on_event(self, event):
        self.risk_manager.handle_event(event)
```
