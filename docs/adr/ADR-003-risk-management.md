# ADR-003: Risk Management Philosophy

## Status

**Accepted**

## Date

2025-01-08

## Context

Production trading with real money requires robust risk management.
Knight Capital lost $440M in 45 minutes from a software bug.
We must prevent catastrophic losses while allowing adaptive strategies.

## Decision

Adopt **"Adaptive Signals, Fixed Safety"** philosophy:

```python
# ADAPTIVE: Signal parameters (data-driven)
alpha = 2.0 / (N + 1)       # Calculated from data
threshold = mean + 2 * std   # Dynamic from distribution

# FIXED: Safety parameters (NEVER adaptive - prevent ruin)
MAX_LEVERAGE = 3             # Hard limit
MAX_POSITION_PCT = 10        # Max 10% per position
STOP_LOSS_PCT = 5            # Per-trade stop
DAILY_LOSS_LIMIT_PCT = 2     # Daily circuit breaker
KILL_SWITCH_DRAWDOWN = 15    # Emergency shutdown
```

### Four Pillars of Signal Design

1. **Probabilistic**: Uncertainty quantified, no certainty claims
2. **Non-linear**: Power laws, not normal distributions
3. **Non-parametric**: Data-driven, not assumption-driven
4. **Scale-invariant**: Works across timeframes

### Safety Layers

| Layer | Trigger | Action |
|-------|---------|--------|
| Position limit | > 10% capital | Block trade |
| Trade stop | -5% from entry | Exit position |
| Daily limit | -2% daily P&L | Halt trading |
| Kill switch | -15% drawdown | Emergency exit all |

## Consequences

### Positive

- Maximum loss bounded
- Multiple safety layers (defense in depth)
- Signals can adapt without risking ruin
- Clear separation of concerns

### Negative

- May miss opportunities at boundaries
- Fixed limits may be suboptimal in calm markets
- Requires discipline to never "temporarily" relax limits

### Neutral

- All limits configurable per-strategy in config
- Limits enforced at multiple levels (strategy, engine, exchange)

## Alternatives Considered

### Fully Adaptive Limits

Dangerous: model error can cause catastrophic loss.

### Static Everything

Too rigid: can't adapt to market conditions.

### Kelly Criterion Only

Theoretically optimal but assumes known edge, which we don't have.

## References

- `strategies/common/adaptive_control/`
- Spec 011: Stop Loss Position Limits
- Spec 012: Circuit Breaker Drawdown
- Mandelbrot: The Misbehavior of Markets
