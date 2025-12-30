# Strategies Directory

Organized structure for 100+ trading strategies.

## Directory Structure

```
strategies/
├── _templates/       # Base classes - DO NOT MODIFY directly
├── production/       # ✅ Deployed, stable strategies
├── development/      # 🔧 Work in progress
├── evolved/          # 🧬 Alpha-evolve output
├── converted/        # 📜 From /pinescript
├── archive/          # 📦 Deprecated strategies
│
├── common/           # Shared utilities (risk, sizing)
├── examples/         # Example implementations
├── hyperliquid/      # Exchange-specific strategies
└── binance2nautilus/ # Data pipeline utilities
```

## Workflow

```
/pinescript URL        → converted/{name}/
/research + implement  → development/{name}/
alpha-evolve           → evolved/gen_{N}/
Manual promotion       → production/{name}/
Deprecate             → archive/{name}/
```

## Strategy Lifecycle

1. **Created** → `development/` or `converted/`
2. **Tested** → Passes backtests, unit tests
3. **Evolved** → `evolved/` (if using alpha-evolve)
4. **Promoted** → `production/` (manual review)
5. **Deprecated** → `archive/` (keep history)

## Naming Convention

```
{methodology}_{asset}_{version}/
├── strategy.py           # Main strategy class
├── config.py             # Configuration
├── README.md             # Documentation
└── backtest_results/     # Performance data
```

Examples:
- `momentum_btc_v3/`
- `mean_reversion_eth_v1/`
- `ema_cross_multi_v2/`

## Commands

```bash
# Research → Development
/research momentum strategies
/speckit.specify spec-XXX
/speckit.implement spec-XXX

# TradingView → Converted
/pinescript https://tradingview.com/script/xyz

# Evolve strategy
# (uses strategies from any directory as seed)

# Promote to production
mv strategies/development/my_strat/ strategies/production/
```

## Testing

Each strategy should have tests in `tests/strategies/`:

```bash
pytest tests/strategies/test_momentum_btc_v3.py -v
```

## Deployment

```bash
# Deploy only production strategies
rsync -av strategies/production/ server:/opt/nautilus/strategies/

# Or specific strategy
rsync -av strategies/production/momentum_btc_v3/ server:/opt/nautilus/strategies/
```
