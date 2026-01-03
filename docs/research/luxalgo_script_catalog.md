# LuxAlgo & Orderflow Scripts Catalog
## Categorized for NautilusTrader Conversion Priority

**Generated**: 2026-01-03
**Source**: TradingView LuxAlgo Library (283 scripts) + Community Scripts
**Purpose**: Priority selection for Spec 025/026 orderflow pipeline integration

---

## CATEGORY 1: LIQUIDITY DETECTION (HIGH PRIORITY)

Scripts that identify institutional liquidity pools, sweeps, and manipulation zones.

### 1.1 Liquidity Sweeps [LuxAlgo]
- **TradingView**: https://www.tradingview.com/script/JRqryeJ5-Liquidity-Sweeps-LuxAlgo/
- **Methodology**:
  - Wick-Based Sweeps: Wick pierces liquidity level, price reverses back (dotted lines)
  - Breakout & Retest Sweeps: Price closes through level, retests, forms opposite wick (dashed lines)
- **Parameters**: Swings Period, Detection Options (wick-only, outbreak-retest, both)
- **NautilusTrader Mapping**: `LiquiditySweepDetector` indicator with swing detection
- **Priority**: **A+** - Direct integration with Spec 025 liquidity analysis

### 1.2 Liquidity Grabs [Flux Charts]
- **TradingView**: https://www.tradingview.com/script/ZxHyWlMd-Liquidity-Grabs-Flux-Charts/
- **Methodology**:
  - Pivot Identification: Extreme wicks relative to surrounding bars
  - False Breakout Detection: Reversal after recent pivot break
  - Confirmation: Wick-to-body ratio > threshold (default 0.5)
- **Parameters**: Pivot Length, Wick-Body Ratio threshold
- **NautilusTrader Mapping**: `LiquidityGrabIndicator` with configurable pivot detection
- **Priority**: **A** - Complements LuxAlgo sweep detection

### 1.3 Liquidity Sniper V3 (ANTI-FAKEOUT) [corbinaem]
- **TradingView**: https://www.tradingview.com/script/7dNQa9Ig-Liquidity-Sniper-V3-ANTI-FAKEOUT/
- **Methodology**: 10-layer confirmation system:
  1. VWAP Reclaim
  2. Micro Break of Structure
  3. Displacement Analysis
  4. Relative Volume
  5. Mitigation Entries (Order Blocks, FVG)
  6. CVD Divergence
  7. SMT Divergence
  8. GARCH Volatility Filter
  9. Multi-Timeframe Alignment
  10. Early Invalidation Tracking (0.5R)
- **Liquidity Targets**: PDH/PDL, PWH/PWL, Equal Highs/Lows, HVN/LVN
- **Trade Scenarios**: S1 (Reversal), S2 (Continuation), S3 (Mean Reversion), S4 (Deep Sweep)
- **Priority**: **A+** - Most comprehensive liquidity strategy, requires decomposition

### 1.4 Volume Bubbles & Liquidity Heatmap [LuxAlgo]
- **TradingView**: https://www.tradingview.com/script/9B93ZOA5-Volume-Bubbles-Liquidity-Heatmap-LuxAlgo/
- **Methodology**: Visualizes volume intensity with configurable timeframes
- **Display Modes**: Total volume, Buy/Sell volume, Delta volume
- **Priority**: **B+** - Visualization component, useful for heatmap generation

---

## CATEGORY 2: VOLUME DELTA & CVD (HIGH PRIORITY)

Scripts measuring buying vs selling pressure through volume analysis.

### 2.1 Volume Delta Methods (Chart) [LuxAlgo]
- **TradingView**: https://www.tradingview.com/script/OhLE0vnH-Volume-Delta-Methods-Chart-LuxAlgo/
- **Methodology**:
  - Volume Delta: Buying volume - Selling volume (net demand per bar)
  - CVD: Cumulative Volume Delta for mid-to-long-term pressure
  - Polarity Methods: Bar Polarity (candle sentiment) or Buying/Selling Pressure (high/low data)
- **Chart Types**: Line, Area, Candlesticks
- **NautilusTrader Mapping**: `VolumeDelta`, `CumulativeVolumeDelta` indicators
- **Priority**: **A+** - Core orderflow component for Spec 025

### 2.2 Volume Delta Candles [LuxAlgo]
- **TradingView**: https://www.tradingview.com/script/BdlG9FNZ-Volume-Delta-Candles-LuxAlgo/
- **Methodology**: Displays delta percentage, highlights highest activity price levels
- **NautilusTrader Mapping**: Delta-colored bar rendering
- **Priority**: **A** - Visual confirmation layer

### 2.3 CVD Divergence [TradingFinder]
- **TradingView**: https://www.tradingview.com/script/HvOAnchA-Cumulative-Volume-Delta-Divergence-TradingFinder-Periodic-EMA/
- **Methodology**:
  - Bullish Divergence: Price lower low + CVD higher low
  - Bearish Divergence: Price higher high + CVD lower high
- **CVD Modes**: Periodic, EMA
- **Parameters**: Divergence Fractal Period, CVD Period, Cumulative Mode
- **NautilusTrader Mapping**: `CVDDivergenceDetector` with EMA/Periodic modes
- **Priority**: **A+** - Key signal generator for orderflow strategies

### 2.4 Delta Flow Profile [LuxAlgo]
- **TradingView**: https://www.tradingview.com/script/sPrmmJ1Z-Delta-Flow-Profile-LuxAlgo/
- **Methodology**: Money flow tracking across price ranges over specified periods
- **Polarity Methods**: Bar Polarity, Bar Buying/Selling Pressure
- **NautilusTrader Mapping**: `DeltaFlowProfile` indicator
- **Priority**: **A** - Profile-based delta analysis

---

## CATEGORY 3: SMART MONEY CONCEPTS (MEDIUM-HIGH PRIORITY)

Scripts implementing ICT methodology for market structure analysis.

### 3.1 Smart Money Concepts (SMC) [LuxAlgo]
- **TradingView**: https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/
- **Features**:
  - Real-time market structure (Internal & Swing BOS/CHoCH)
  - Order Blocks (OB)
  - Premium & Discount Zones
  - Equal Highs/Lows
  - Fair Value Gaps (FVG)
- **Settings**: Market Structure Lookback (10-15 internal, 20-30 significant)
- **NautilusTrader Mapping**: `SMCIndicator` with modular components
- **Priority**: **A** - TradingView's #1 indicator, comprehensive SMC

### 3.2 Market Structure Targets Model [LuxAlgo]
- **Library**: https://www.luxalgo.com/library/indicator/market-structure-targets-model/
- **Methodology**: Automated MSS (Market Structure Shift) and MSB (Market Structure Break) targeting
- **NautilusTrader Mapping**: `MarketStructureTargets` for target calculation
- **Priority**: **B+** - Target calculation based on structure

### 3.3 Market Structure Volume Distribution [LuxAlgo]
- **Library**: https://www.luxalgo.com/library/indicator/market-structure-volume-distribution/
- **Features**:
  - Market structure highlighting
  - Grid levels
  - Volume profile per structure level (buy/sell differentiated)
- **NautilusTrader Mapping**: `MSVolumeDistribution` indicator
- **Priority**: **A** - Links volume to structure events

---

## CATEGORY 4: VOLUME PROFILES (MEDIUM PRIORITY)

Scripts for volume-at-price analysis and POC detection.

### 4.1 Volume Profile [LuxAlgo]
- **Library**: https://www.luxalgo.com/library/indicator/volume-profile/
- **Features**: POC (Point of Control), Value Area, Buy/Sell breakdown
- **NautilusTrader Mapping**: NautilusTrader native `VolumeProfile` exists
- **Priority**: **B** - Native implementation preferred

### 4.2 Money Flow Profile [LuxAlgo]
- **Library**: https://www.luxalgo.com/library/indicator/Money-Flow-Profile/
- **Methodology**: Money flow at price levels with sentiment analysis
- **NautilusTrader Mapping**: `MoneyFlowProfile` indicator
- **Priority**: **B+** - Enhanced profile with sentiment

---

## CATEGORY 5: TAPE READING & PACE (MEDIUM PRIORITY)

Scripts analyzing tape speed, pace, and execution dynamics.

### 5.1 Tape Speed Pulse (Pace + Direction) [THEBUNKER27]
- **TradingView**: https://www.tradingview.com/script/ihy9IpZi-Tape-Speed-Pulse-Pace-Direction-v6-Climax/
- **Methodology**:
  - Pace: Relative Volume (RVOL) vs recent average with EMA smoothing
  - Direction: Close-to-close comparison (uptick/downtick proxy)
  - Climax Detection: Buy/Sell exhaustion at surge + large wick + slowdown
- **Parameters**:
  - Pace Lookback: 20-30 bars
  - Smoothing EMA: 3-7 bars
  - Surge Threshold: 1.5-2.8x RVOL
  - Slowdown Drop %: 25-45%
- **NautilusTrader Mapping**: `TapeSpeedIndicator` with climax detection
- **Priority**: **A** - Direct mapping to Speed of Tape concept

### 5.2 NinjaTrader Speed of Tape (Reference)
```python
# From nuovi link risorse.md - NinjaTrader reference implementation
Calculate = Calculate.OnEachTick
pace = 0
i = 0
while i < CurrentBar:
    ts = Time[0] - Time[i]
    if ts.TotalSeconds < period:
        pace += Bars.BarsPeriod.Value
    else:
        break
    i += 1
```
- **NautilusTrader Mapping**: `SpeedOfTape` with tick-level calculation
- **Priority**: **A** - Foundational tape reading component

---

## CATEGORY 6: DIVERGENCE DETECTION (MEDIUM PRIORITY)

Scripts for identifying price-indicator divergences.

### 6.1 Volume HeatMap Divergence [BigBeluga]
- **TradingView**: https://www.tradingview.com/script/3DTOFolH-Volume-HeatMap-Divergence-BigBeluga/
- **Methodology**:
  - Volume Normalization: 0-100% scale via percentile ranking
  - Bullish Divergence: Price lower low + Volume higher low
  - Bearish Divergence: Price higher high + Volume lower high
- **Parameters**: Divergence Range, Pivot Detection Distance
- **NautilusTrader Mapping**: `VolumeDivergenceDetector`
- **Priority**: **B+** - Zone identification via volume divergence

---

## PRIORITY MATRIX

### Tier 1: CRITICAL (Convert First)
| Script | Category | Reason |
|--------|----------|--------|
| Volume Delta Methods | CVD | Core orderflow, Spec 025 foundation |
| CVD Divergence | CVD | Signal generation for entries/exits |
| Liquidity Sweeps | Liquidity | Key manipulation detection |
| Liquidity Sniper V3 | Liquidity | Comprehensive strategy template |
| Tape Speed Pulse | Tape | Speed of tape implementation |

### Tier 2: HIGH (Convert Second)
| Script | Category | Reason |
|--------|----------|--------|
| Smart Money Concepts | SMC | Market structure analysis |
| Delta Flow Profile | CVD | Profile-based delta |
| Liquidity Grabs | Liquidity | Complements sweep detection |
| Market Structure Volume Distribution | SMC | Volume-structure link |

### Tier 3: MEDIUM (Convert Third)
| Script | Category | Reason |
|--------|----------|--------|
| Volume HeatMap Divergence | Divergence | Zone identification |
| Volume Bubbles & Liquidity Heatmap | Liquidity | Visualization |
| Money Flow Profile | Profile | Enhanced profile |
| Market Structure Targets | SMC | Target calculation |

---

## ACADEMIC PAPER REFERENCES

Papers supporting the methodologies used in these scripts:

1. **VPIN (Volume-Synchronized Probability of Informed Trading)**
   - Easley, López de Prado, O'Hara (2011)
   - "The Microstructure of the Flash Crash: Flow Toxicity, Liquidity Crashes"
   - 419 citations - THE foundational paper for toxicity detection

2. **Institutional Order Flow**
   - Campbell, Vuolteenaho, Ramadorai (2005)
   - "Caught on Tape: Institutional Order Flow and Stock Returns"
   - Links tape reading to institutional activity

3. **Market Microstructure**
   - Kyle (1985) - Continuous auctions and insider trading
   - Glosten-Milgrom (1985) - Bid-ask spread and informed traders

---

## INTEGRATION PATH WITH SPEC 025/026

### Spec 025: Orderflow Pipeline
```
Phase 1: Volume Delta Core
├── VolumeDelta indicator (from Volume Delta Methods)
├── CumulativeVolumeDelta indicator (CVD)
└── DeltaDivergenceDetector (from CVD Divergence)

Phase 2: Liquidity Detection
├── LiquiditySweepDetector (from Liquidity Sweeps)
├── LiquidityGrabIndicator (from Flux Charts)
└── LiquidityPool tracker (PDH/PDL/PWH/PWL)

Phase 3: Tape Reading
├── TapeSpeedIndicator (from Tape Speed Pulse)
├── PaceOfTape (RVOL-based)
└── ClimaxDetector (buy/sell exhaustion)
```

### Spec 026: Meta-Learning Integration
```
Feature Engineering from:
├── CVD divergence features
├── Liquidity sweep frequency
├── Tape speed regime
└── Delta flow profile metrics

Labels from:
├── Sweep success/failure outcomes
├── Divergence resolution direction
└── Climax reversal effectiveness
```

---

## NEXT STEPS

1. **Phase 3**: Select top 20 scripts from this catalog for conversion priority
2. **Phase 4**: Use `/pinescript` skill to convert priority scripts
3. **Phase 5**: Integrate converted indicators into Spec 025/026 pipeline
4. **Validation**: Backtest converted indicators against original Pine Script results

---

*Catalog compiled from TradingView LuxAlgo Library and community research*
*Sources: luxalgo.com, tradingview.com, academic papers via paper-search-mcp*
