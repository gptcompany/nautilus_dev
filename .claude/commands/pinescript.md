# /pinescript - Convert TradingView Pine Script to NautilusTrader

Convert Pine Script strategies to NautilusTrader Python code.

## Usage

```
/pinescript <url>
/pinescript https://tradingview.com/script/ABC123

/pinescript
# Then paste Pine Script code when prompted
```

## What It Does

1. **Parse** Pine Script (v4/v5/v6)
2. **Extract** indicators, entry/exit conditions, risk management
3. **Map** Pine functions → NautilusTrader native Rust indicators
4. **Generate** complete strategy class with config
5. **Create** test file
6. **Output** conversion report

## Output Files

```
strategies/{strategy_name}/
├── {strategy_name}_strategy.py   # Main strategy
├── config.py                     # Configuration
├── README.md                     # Documentation
└── pine_source.txt               # Original code

tests/test_{strategy_name}.py     # Test file
```

## See Also

- Full documentation: `.claude/skills/pinescript-converter/SKILL.md`
- Indicator mapping: `docs/research/indicator_mapping.md`
