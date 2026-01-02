# BigBeluga Indicators - Conversion Tracking

**Total Scripts**: 146 (BigBeluga profile)
**Found & Classified**: 79 scripts (combinazione di più fonti)
**Focus**: LEADING indicators (Orderflow, Volume, Liquidity, FVG, Structure)
**Excluded**: LAGGING indicators (RSI, MACD, oscillators, MAs)

## Data Sources

| Source | Scripts Found | Method |
|--------|---------------|--------|
| Explore Agent (Web Search) | 72 | Multi-query web search, URL extraction |
| TradingView API Scraper | 24 | API endpoint with descriptions |
| **Merged Total** | **79** | Deduplicated and classified |

**Note**: I rimanenti ~67 script probabilmente sono premium/esclusivi o varianti non indicizzate.

## TradingView API Discovery

**Endpoint**: `https://www.tradingview.com/api/v1/scripts/?page=X&per_page=24&by={USERNAME}`

Questo endpoint permette di:
- Fetchare script di un utente con paginazione
- Ottenere `scriptIdPart`, `scriptName`, `shortDescription`
- Usare per automatizzare il discovery di nuovi indicatori

**Note**: Il lazy loading della pagina profilo blocca a ~24 script visibili. Per tutti i 146 script, potrebbe essere necessario autenticarsi o usare endpoint diversi.

---

## Conversion Status Legend

- [ ] Not started
- [~] In progress
- [x] Completed
- [S] Skipped (LAGGING/Low priority)

---

## TIER S - Highest ROI (Convert First)

Leading indicators with unique edge, orderflow/liquidity-based.

| Status | Indicator | Category | URL | Notes |
|--------|-----------|----------|-----|-------|
| [x] | Liquidation HeatMap | Liquidation | [Link](https://www.tradingview.com/script/tMtleB1G-Liqudation-HeatMap-BigBeluga/) | **CONVERTED** - strategies/converted/liquidation_heatmap/ |
| [ ] | DeltaFlow Volume Profile | Delta/Volume | [Link](https://www.tradingview.com/script/JUWuAXdx-DeltaFlow-Volume-Profile-BigBeluga/) | Delta %, buyer/seller dominance, POC band |
| [ ] | Dynamic Liquidity Depth | Liquidity | [Link](https://www.tradingview.com/script/PuHTBcww-Dynamic-Liquidity-Depth-BigBeluga/) | Stop-loss simulation, buy/sell side liquidity |
| [ ] | FVG Order Blocks | FVG/OB | [Link](https://www.tradingview.com/script/xy4EFLtD-FVG-Order-Blocks-BigBeluga/) | FVG with strength %, retest signals, dynamic OB |
| [ ] | Supply and Demand Zones | Institutional | [Link](https://www.tradingview.com/script/I0o8N7VW-Supply-and-Demand-Zones-BigBeluga/) | Volume-weighted S/D, tested vs untested logic |
| [ ] | Open Interest/Volume/Liquidations Suite | Orderflow | [Link](https://www.tradingview.com/script/ZtJjXcEH-Open-Intrest-Volume-Liquidations-Suite-BigBeluga/) | OI, CVD, Delta OI, Liquidations |

---

## TIER A - High ROI (Convert Next)

Volume-based, actionable, good edge.

| Status | Indicator | Category | URL | Notes |
|--------|-----------|----------|-----|-------|
| [ ] | Volumatic Fair Value Gaps | FVG/Volume | [Link](https://www.tradingview.com/script/OfR2t6z5-Volumatic-Fair-Value-Gaps-BigBeluga/) | FVG with buy/sell volume split, 10x LTF sampling |
| [ ] | Dynamic Liquidity HeatMap Profile | Liquidity | [Link](https://www.tradingview.com/script/qWvJ0jlj-Dynamic-Liquidity-HeatMap-Profile-BigBeluga/) | Stop-loss clusters, POC liquidity magnet |
| [ ] | Open Liquidity Heatmap | Liquidity | [Link](https://www.tradingview.com/script/U8Ee0pyN-Open-Liquidity-Heatmap-BigBeluga/) | Accumulated resting liquidity |
| [ ] | Liquidity Heatmap | Liquidity | [Link](https://www.tradingview.com/script/6NDgpGap/) | Long/short liquidity, leverage autopilot |
| [ ] | Volume Profile Area | Volume | [Link](https://www.tradingview.com/script/zuWnRE9o-Volume-Profile-Area-BigBeluga/) | Nested profiles, VA precision, dual profiles |
| [ ] | Multi-Layer Volume Profile | Volume | [Link](https://www.tradingview.com/script/5QtH3KYD-Multi-Layer-Volume-Profile-BigBeluga/) | 4 depth layers, overlapping POCs |
| [ ] | Delta Volume Profile | Delta | [Link](https://www.tradingview.com/script/N9nYtXh3-Delta-Volume-Profile-BigBeluga/) | Delta distribution per price level |
| [ ] | Price Action Smart Money Concepts | SMC | [Link](https://www.tradingview.com/script/jvNJYfbL-Price-Action-Smart-Money-Concepts-BigBeluga/) | FVG, OB, Breakers, BOS, CHoCH |
| [ ] | Volume Order Blocks | OB/Volume | [Link](https://www.tradingview.com/script/5CpArShF-Volume-Order-Blocks-BigBeluga/) | Volume-based order block detection |
| [ ] | Liquidity Spectrum Visualizer | Liquidity | [Link](https://www.tradingview.com/script/tizR9Gzw-Liquidity-Spectrum-Visualizer-BigBeluga/) | Volume bubbles + VP |
| [ ] | Trend Pivots Profile | Volume | [Link](https://www.tradingview.com/script/YNtbyDfo-Trend-Pivots-Profile-BigBeluga/) | VP at pivots, LTF volume data |

---

## TIER B - Medium-High ROI (Optional)

Solid indicators, less unique but useful.

| Status | Indicator | Category | URL | Notes |
|--------|-----------|----------|-----|-------|
| [ ] | Volume Range Map | Volume | [Link](https://www.tradingview.com/script/T1v7pEfn-Volume-Range-Map-BigBeluga/) | POC per S/D zone |
| [ ] | VWAP Volume Profile | VWAP | [Link](https://www.tradingview.com/script/4v1ExKvr-VWAP-Volume-Profile-BigBeluga/) | Volume vs VWAP direction |
| [ ] | Quadro Volume Profile | Volume | [Link](https://www.tradingview.com/script/E8IylgRU-Quadro-Volume-Profile-BigBeluga/) | 4-quadrant volume segmentation |
| [ ] | HTF Frequency Zone | Structure | [Link](https://www.tradingview.com/script/nBVfUKcx-HTF-Frequency-Zone-BigBeluga/) | POC frequency HTF, D/W/M |
| [ ] | Volume HeatMap Divergence | Volume | [Link](https://www.tradingview.com/script/3DTOFolH-Volume-HeatMap-Divergence-BigBeluga/) | Normalized volume overlay, divergence |
| [ ] | Low Volatility Profiles | Volume | [Link](https://www.tradingview.com/script/9anGnOxj-Low-Volatility-Profiles-BigBeluga/) | ADX compression + VP breakout |
| [ ] | Volume Delta | Delta | [Link](https://www.tradingview.com/script/VwekskUt-Volume-Delta-BigBeluga/) | Buy vs Sell volume % |
| [ ] | Directional Imbalance Index | Imbalance | [Link](https://www.tradingview.com/script/WSvRZ0j0-Directional-Imbalance-Index-BigBeluga/) | HH/LL counting |
| [ ] | Regime Filter | Trend/Volume | [Link](https://www.tradingview.com/script/Ye1fljXO-Regime-Filter-BigBeluga/) | Dual-factor regime detection |
| [ ] | Consolidation Range | Structure | [Link](https://www.tradingview.com/script/XVVEY0F3-Consolidation-Range-BigBeluga/) | ADX compression, volume delta |
| [ ] | Volatility Breaker Blocks | OB | [Link](https://www.tradingview.com/script/pvRFnK8O-Volatility-Breaker-Blocks-BigBeluga/) | Volatility-based breaker detection |
| [ ] | Choch Pattern Levels | SMC | [Link](https://www.tradingview.com/script/WVwxrsY3-Choch-Pattern-Levels-BigBeluga/) | Change of character patterns |

---

## TIER C - Medium ROI (Lower Priority)

Market structure, less unique.

| Status | Indicator | Category | URL | Notes |
|--------|-----------|----------|-----|-------|
| [ ] | Market Core | Multi | [Link](https://www.tradingview.com/script/0lVREggj-Market-Core-BigBeluga/) | FVG + OB, generalist |
| [ ] | Pivot Levels | S/R | [Link](https://www.tradingview.com/script/h5TO1j8H-Pivot-Levels-BigBeluga/) | Multi-sensitivity pivot detection |
| [ ] | Multi Pivot Trend | Pivot | [Link](https://www.tradingview.com/script/rJwBlmLw-Multi-Pivot-Trend-BigBeluga/) | Trend via pivot breaks |
| [ ] | Swing Traces | Swing | [Link](https://www.tradingview.com/script/lqiLrVxM-Swing-Traces-BigBeluga/) | Fading traces from swing points |
| [ ] | Fractals Trend | S/R | [Link](https://www.tradingview.com/script/aU8krboM-Fractals-Trend-BigBeluga/) | Fractal-based S/R |
| [ ] | Pivot Trend Flow | Pivot | [Link](https://www.tradingview.com/script/ghjmECM4-Pivot-Trend-Flow-BigBeluga/) | Adaptive pivot band |
| [ ] | High Volume Points | Volume | [Link](https://www.tradingview.com/script/tCVDlpdV-High-Volume-Points-BigBeluga/) | High-volume pivots |
| [ ] | Liquidity Zones | Liquidity | [Link](https://www.tradingview.com/script/7d2zeIlZ-Liquidity-Zones-BigBeluga/) | Pivot-based liquidity |
| [ ] | Liquidity Location Detector | Liquidity | [Link](https://www.tradingview.com/script/y6ymQYfx-Liquidity-Location-Detector-BigBeluga/) | Volume concentration |
| [ ] | Angle Market Structure | Structure | [Link](https://www.tradingview.com/script/llHSdjyH-Angle-Market-Structure-BigBeluga/) | Breakout/breakdown detection |
| [ ] | Fractal Support and Resistance | S/R | [Link](https://www.tradingview.com/script/13y7If97-Fractal-Support-and-Resistance-BigBeluga/) | Fractal-based levels |
| [ ] | Higher Time Frame Support/Resistance | S/R | [Link](https://www.tradingview.com/script/1dCsFTMq-Higher-Time-Frame-Support-Resistance-BigBeluga/) | MTF pivot levels |
| [ ] | Pivot Channel Breaks | Structure | [Link](https://www.tradingview.com/script/Esore3IT-Pivot-Channel-Breaks-BigBeluga/) | Dynamic channel breakouts |
| [ ] | Price Map Profile | Volume | [Link](https://www.tradingview.com/script/VTQ4fiLW-Price-Map-Profile-BigBeluga/) | Activity distribution |
| [ ] | Market Trend Levels Detector | Structure | [Link](https://www.tradingview.com/script/elXkIOoM-Market-Trend-Levels-Detector-BigBeluga/) | EMA-based trend levels |
| [ ] | Range Breakout | Structure | [Link](https://www.tradingview.com/script/WogNpPBX-Range-Breakout-BigBeluga/) | ATR-based breakout signals |
| [ ] | Low Volatility Range Breaks | Structure | [Link](https://www.tradingview.com/script/5LF1dxmk-Low-Volatility-Range-Breaks-BigBeluga/) | Low vol breakout anticipation |
| [ ] | Gradient Range | Structure | [Link](https://www.tradingview.com/script/6jAT3TT6-Gradient-Range-BigBeluga/) | Range visualization |
| [ ] | Volumatic Support/Resistance Levels | S/R | [Link](https://www.tradingview.com/script/F2OH2WQT-Volumatic-Support-Resistance-Levels-BigBeluga/) | Volume-weighted bands |
| [ ] | Volumatic S/R Levels | S/R | [Link](https://www.tradingview.com/script/mJDb2Lto-Volumatic-S-R-Levels-BigBeluga/) | Volume-weighted S/R |
| [ ] | BigBeluga - Smart Money Concepts | SMC | [Link](https://www.tradingview.com/script/WTNPnxsp-BigBeluga-Smart-Money-Concepts/) | Comprehensive SMC |
| [ ] | DonAlt - Smart Money Toolkit | SMC | [Link](https://www.tradingview.com/script/jG8Ch07t-DonAlt-Smart-Money-Toolkit-BigBeluga/) | Institutional activity |
| [ ] | Bitcoin Cycle | Heatmap | [Link](https://www.tradingview.com/script/TLJlX4S6-Bitcoin-Cycle-BigBeluga/) | Accumulation/distribution zones |
| [ ] | Volumatic Variable Index Dynamic Average | Volume | [Link](https://www.tradingview.com/script/llhVjhA5-Volumatic-Variable-Index-Dynamic-Average-BigBeluga/) | Volume-based averaging |

---

## SKIPPED - LAGGING Indicators

These are excluded from conversion priority (oscillators, RSI, MACD, MAs).

| Status | Indicator | Category | URL | Reason |
|--------|-----------|----------|-----|--------|
| [S] | Ultimate MACD Suite | MACD | [Link](https://www.tradingview.com/script/ZGKfhFOQ-Ultimate-MACD-Suite-BigBeluga/) | LAGGING - Momentum oscillator |
| [S] | Ultimate RSI Suite | RSI | [Link](https://www.tradingview.com/script/XRIcobAF-Ultimate-RSI-Suite-BigBeluga/) | LAGGING - Momentum oscillator |
| [S] | Nautilus Oscillator | Oscillator | [Link](https://www.tradingview.com/script/1odom906-Nautilus-Oscillator-BigBeluga/) | LAGGING - Multi-faceted oscillator |
| [S] | MTF Oscillator Stack | Oscillator | [Link](https://www.tradingview.com/script/1UOFIjxw-MTF-Oscillator-Stack-BigBeluga/) | LAGGING - RSI/MFI/Stoch RSI |
| [S] | DSL Oscillator | Oscillator | [Link](https://www.tradingview.com/script/bVMgRGq8-DSL-Oscillator-BigBeluga/) | LAGGING - RSI hybrid |
| [S] | Aroon Oscillator | Oscillator | [Link](https://www.tradingview.com/script/dI6UrTRB-Aroon-Oscillator-BigBeluga/) | LAGGING - Trend strength |
| [S] | Smooth Price Oscillator | Oscillator | [Link](https://www.tradingview.com/script/khcRd2as-Smooth-Price-Oscillator-BigBeluga/) | LAGGING - SuperSmoother |
| [S] | Momentum Index | Momentum | [Link](https://www.tradingview.com/script/USCjtOVV-Momentum-Index-BigBeluga/) | LAGGING - Delta-based |
| [S] | Log Regression Oscillator Channel | Oscillator | [Link](https://www.tradingview.com/script/eR9y7zmm-Log-Regression-Oscillator-Channel-BigBeluga/) | LAGGING - Log trend |
| [S] | Commodity Trend Reactor | Oscillator | [Link](https://www.tradingview.com/script/zDr01ngU-Commodity-Trend-Reactor-BigBeluga/) | LAGGING - CCI-based |
| [S] | RSI Volatility Suppression Zones | RSI | [Link](https://www.tradingview.com/script/M9icblKI-RSI-Volatility-Suppression-Zones-BigBeluga/) | LAGGING - RSI variant |
| [S] | Trend Step Channel | Trend | [Link](https://www.tradingview.com/script/DJ5w3CE6-Trend-Step-Channel-BigBeluga/) | LAGGING - ATR channel |
| [S] | Target Trend | Trend | [Link](https://www.tradingview.com/script/QoUmKd1H-Target-Trend-BigBeluga/) | LAGGING - SMA bands |
| [S] | HTF Trend Tracker | Trend | [Link](https://www.tradingview.com/script/VnQqHDsI-HTF-Trend-Tracker-BigBeluga/) | LAGGING - HTF trend |
| [S] | Deviation Trend Profile | Trend | [Link](https://www.tradingview.com/script/6Wr1CEuo-Deviation-Trend-Profile-BigBeluga/) | LAGGING - StdDev zones |
| [S] | Volatility Gaussian Bands | Volatility | [Link](https://www.tradingview.com/script/ZRD7xSGy-Volatility-Gaussian-Bands-BigBeluga/) | LAGGING - Gaussian filter |
| [S] | Bollinger Bands Regression Forecast | Volatility | [Link](https://www.tradingview.com/script/HQFrNtJg-Bollinger-Bands-Regression-Forecast-BigBeluga/) | LAGGING - BB variant |
| [S] | Fibonacci Bands | Fibonacci | [Link](https://www.tradingview.com/script/KMzbEIJy-Fibonacci-Bands-BigBeluga/) | LAGGING - Fib-based |
| [S] | Elliott Wave | Pattern | [Link](https://www.tradingview.com/script/eMiCcp3x-Elliott-Wave-BigBeluga/) | LAGGING - Wave counting |
| [S] | Trend Counter | Trend | [Link](https://www.tradingview.com/script/J6PkxvTK-Trend-Counter-BigBeluga/) | LAGGING - Bar counting |
| [S] | Top G Indicator | Pattern | [Link](https://www.tradingview.com/script/JOE1tYTo-Top-G-indicator-BigBeluga/) | LAGGING - Extremes |
| [S] | Wolfe Waves | Pattern | [Link](https://www.tradingview.com/script/gGDIZlWJ-Wolfe-Waves-BigBeluga/) | LAGGING - Wave pattern |
| [S] | Historical Returns | Analysis | [Link](https://www.tradingview.com/script/zlt9WGV1-Historical-Returns-BigBeluga/) | Analysis tool, not trading |
| [S] | Market Echo Screener | Screener | [Link](https://www.tradingview.com/script/ahB814di-Market-Echo-Screener-BigBeluga/) | Multi-asset screener |
| [S] | Strategy Builder v1.0.0 | Strategy | [Link](https://www.tradingview.com/script/L3HLSoVv-Strategy-Builder-v1-0-0-BigBeluga/) | Full strategy, not indicator |
| [S] | Comprehensive Trading Toolkit | Multi | [Link](https://www.tradingview.com/script/MJym5paR-Comprehensive-Trading-Toolkit-BigBeluga/) | RSI divergences, mixed |

---

## Summary Statistics

| Tier | Count | Converted | Remaining |
|------|-------|-----------|-----------|
| S (Highest ROI) | 6 | 1 | 5 |
| A (High ROI) | 11 | 0 | 11 |
| B (Medium-High) | 12 | 0 | 12 |
| C (Medium) | 24 | 0 | 24 |
| **LEADING Total** | **53** | **1** | **52** |
| Skipped (LAGGING) | 26 | - | - |
| **Grand Total** | **79** | **1** | **52** |

---

## Data Requirements

| Indicator Type | Data Needed | Accuracy |
|----------------|-------------|----------|
| Volume Profile | Bar volume (OHLCV) | High |
| Delta indicators | Bid/ask data OR close vs open heuristic | Medium |
| Liquidation | Pivots + ATR | High |
| FVG/Order Blocks | OHLCV | High |
| S/D Zones | Volume + consecutive candles | High |

---

## NautilusTrader Mapping Notes

- **FVG detection**: Custom implementation (no native)
- **Volume Profile**: Custom (no native VP in Nautilus)
- **Delta calculation**: Tick-level data for accuracy, or heuristic
- **Liquidation zones**: Pivot + ATR (already implemented)
- **Order Blocks**: Custom detection logic needed

---

## Conversion Workflow

1. **Extract Pine Script** via `scripts/pinescript_extractor.py`
2. **Analyze logic** and identify NautilusTrader equivalents
3. **Create indicator** in `strategies/converted/{name}/`
4. **Create strategy** using indicator signals
5. **Write tests** using test-runner agent
6. **Update this file** marking [x] completed

---

*Generated: 2026-01-02*
*Source: TradingView BigBeluga (146 total, 79 classified)*
*Pipeline: /pinescript command with pinescript-converter agent (opus)*
