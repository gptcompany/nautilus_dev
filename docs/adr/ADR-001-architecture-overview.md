# ADR-001: NautilusTrader Architecture Choice

## Status

**Accepted**

## Date

2025-01-08

## Context

We need a high-performance algorithmic trading framework that supports:
- Multiple exchanges (Binance, Bybit, etc.)
- Real-time and historical data processing
- Backtesting with production parity
- Native performance for indicators

Options considered: Backtrader, Zipline, custom framework, NautilusTrader.

## Decision

Adopt **NautilusTrader (Nightly)** as the core trading framework.

Key reasons:
1. **Performance**: Rust core with Python bindings (100x faster than pure Python)
2. **Production parity**: Identical code runs in backtest and live
3. **Exchange support**: Native adapters for major crypto exchanges
4. **Active development**: Regular updates, responsive community

We use the **nightly** version for:
- 128-bit precision (critical for crypto)
- Latest exchange adapters
- Cutting-edge features

## Consequences

### Positive

- High performance for complex indicators
- Consistent behavior across backtest/live
- Strong typing and safety guarantees
- Active Discord community support

### Negative

- Nightly has breaking changes frequently
- Learning curve steeper than simpler frameworks
- Must track changelog and adapt to API changes
- V2 Wranglers incompatible (stuck on V1)

### Neutral

- Requires Linux for 128-bit precision
- Nightly catalogs incompatible with stable

## Alternatives Considered

### Backtrader

Simpler but abandoned, poor performance, no native exchange adapters.

### Custom Framework

More control but massive development effort, reinventing the wheel.

### Zipline

Good for equities, poor crypto support, unmaintained.

## References

- [NautilusTrader Docs](https://docs.nautilustrader.io)
- [Nightly Changelog](docs/nautilus/nautilus-trader-changelog.md)
- Discord: #nautilus-trader
