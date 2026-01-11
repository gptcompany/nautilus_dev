# /pinescript - Convert TradingView Pine Script to NautilusTrader

Convert Pine Script strategies to NautilusTrader Python code.

## Usage

```
/pinescript <url>
/pinescript https://tradingview.com/script/ABC123

/pinescript
# Then paste Pine Script code when prompted
```

## Automatic Extraction

When given a TradingView URL, the skill **automatically extracts** the Pine Script source code using Playwright browser automation. It intercepts the `pine-facade.tradingview.com` API call that TradingView uses to load script content.

**Requirements**: `pip install playwright && playwright install chromium`

**Limitations**: Only works with open-source scripts. Protected/invite-only scripts require manual paste.

## What It Does

1. **Fetch** Pine Script from TradingView URL (automatic extraction)
2. **Parse** Pine Script (v4/v5/v6)
3. **Extract** indicators, entry/exit conditions, risk management
4. **Map** Pine functions → NautilusTrader native Rust indicators
5. **Generate** complete strategy class with config
6. **Create** test file
7. **Output** conversion report

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

- Indicator mapping: `docs/research/indicator_mapping.md`
