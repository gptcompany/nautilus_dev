# Top 20 Pine Script Priority Conversion List
## NautilusTrader Orderflow Pipeline Integration

**Generated**: 2026-01-03
**Purpose**: Definitive priority list for `/pinescript` conversion to NautilusTrader
**Integration Target**: Spec 025 (Orderflow) + Spec 026 (Meta-Learning)

---

## TIER 1: CRITICAL (Convert Immediately)

### #1 Volume Delta Methods (Chart) [LuxAlgo]
- **URL**: https://www.tradingview.com/script/OhLE0vnH-Volume-Delta-Methods-Chart-LuxAlgo/
- **Category**: Volume Delta / CVD
- **Complexity**: Medium
- **Why Critical**: Core orderflow foundation - buying vs selling pressure
- **NautilusTrader Class**: `VolumeDelta`, `CumulativeVolumeDelta`
- **Integration**: Spec 025 Phase 1 - Volume Delta Core

### #2 CVD Divergence [TradingFinder]
- **URL**: https://www.tradingview.com/script/HvOAnchA-Cumulative-Volume-Delta-Divergence-TradingFinder-Periodic-EMA/
- **Category**: CVD Divergence
- **Complexity**: Medium
- **Why Critical**: Signal generation from CVD-price divergences
- **NautilusTrader Class**: `CVDDivergenceDetector`
- **Integration**: Spec 025 Phase 1 - Signal generation layer

### #3 Liquidity Sweeps [LuxAlgo]
- **URL**: https://www.tradingview.com/script/JRqryeJ5-Liquidity-Sweeps-LuxAlgo/
- **Category**: Liquidity Detection
- **Complexity**: Medium
- **Why Critical**: Manipulation/sweep detection for entry timing
- **NautilusTrader Class**: `LiquiditySweepDetector`
- **Integration**: Spec 025 Phase 2 - Liquidity Detection

### #4 Tape Speed Pulse [THEBUNKER27]
- **URL**: https://www.tradingview.com/script/ihy9IpZi-Tape-Speed-Pulse-Pace-Direction-v6-Climax/
- **Category**: Tape Reading
- **Complexity**: Medium
- **Why Critical**: Speed of tape / pace of tape implementation
- **NautilusTrader Class**: `TapeSpeedIndicator`, `ClimaxDetector`
- **Integration**: Spec 025 Phase 3 - Tape Reading

### #5 Smart Money Concepts (SMC) [LuxAlgo]
- **URL**: https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/
- **Category**: Market Structure / ICT
- **Complexity**: High
- **Why Critical**: TradingView's #1 indicator, comprehensive SMC
- **NautilusTrader Class**: `SMCIndicator` (modular: BOS, CHoCH, OB, FVG)
- **Integration**: Spec 025 Phase 2 - Structure Detection

---

## TIER 2: HIGH PRIORITY (Convert Second)

### #6 Delta Flow Profile [LuxAlgo]
- **URL**: https://www.tradingview.com/script/sPrmmJ1Z-Delta-Flow-Profile-LuxAlgo/
- **Category**: Volume Delta Profile
- **Complexity**: High
- **Why High**: Profile-based delta across price ranges
- **NautilusTrader Class**: `DeltaFlowProfile`
- **Integration**: Spec 025 - Volume Profile enhancement

### #7 Liquidity Grabs [Flux Charts]
- **URL**: https://www.tradingview.com/script/ZxHyWlMd-Liquidity-Grabs-Flux-Charts/
- **Category**: Liquidity Detection
- **Complexity**: Low
- **Why High**: Complements LuxAlgo sweep detection
- **NautilusTrader Class**: `LiquidityGrabIndicator`
- **Integration**: Spec 025 Phase 2 - Liquidity Detection

### #8 Market Structure Volume Distribution [LuxAlgo]
- **URL**: https://www.luxalgo.com/library/indicator/market-structure-volume-distribution/
- **Category**: SMC + Volume
- **Complexity**: High
- **Why High**: Links volume to structure events
- **NautilusTrader Class**: `MSVolumeDistribution`
- **Integration**: Spec 025 - Structure-volume correlation

### #9 Volume Delta Candles [LuxAlgo]
- **URL**: https://www.tradingview.com/script/BdlG9FNZ-Volume-Delta-Candles-LuxAlgo/
- **Category**: Volume Delta Visualization
- **Complexity**: Low
- **Why High**: Delta-colored bar rendering for confirmation
- **NautilusTrader Class**: `VolumeDeltaCandles`
- **Integration**: Visualization layer

### #10 Liquidity Sniper V3 (ANTI-FAKEOUT)
- **URL**: https://www.tradingview.com/script/7dNQa9Ig-Liquidity-Sniper-V3-ANTI-FAKEOUT/
- **Category**: Comprehensive Strategy
- **Complexity**: Very High
- **Why High**: 10-layer confirmation system - full strategy template
- **NautilusTrader Class**: `LiquiditySniperStrategy`
- **Integration**: Reference strategy implementation

---

## TIER 3: MEDIUM PRIORITY (Convert Third)

### #11 Volume HeatMap Divergence [BigBeluga]
- **URL**: https://www.tradingview.com/script/3DTOFolH-Volume-HeatMap-Divergence-BigBeluga/
- **Category**: Volume Divergence
- **Complexity**: Medium
- **Why Medium**: Zone identification via volume normalization
- **NautilusTrader Class**: `VolumeDivergenceDetector`

### #12 Volume Bubbles & Liquidity Heatmap [LuxAlgo]
- **URL**: https://www.tradingview.com/script/9B93ZOA5-Volume-Bubbles-Liquidity-Heatmap-LuxAlgo/
- **Category**: Volume Visualization
- **Complexity**: Medium
- **Why Medium**: Heatmap visualization of liquidity
- **NautilusTrader Class**: `LiquidityHeatmap`

### #13 Money Flow Profile [LuxAlgo]
- **URL**: https://www.luxalgo.com/library/indicator/Money-Flow-Profile/
- **Category**: Money Flow
- **Complexity**: High
- **Why Medium**: Enhanced profile with sentiment
- **NautilusTrader Class**: `MoneyFlowProfile`

### #14 Market Structure Targets Model [LuxAlgo]
- **URL**: https://www.luxalgo.com/library/indicator/market-structure-targets-model/
- **Category**: SMC Targets
- **Complexity**: Medium
- **Why Medium**: Automated MSS/MSB targeting
- **NautilusTrader Class**: `MarketStructureTargets`

### #15 Pure Price Action Liquidity Sweeps [LuxAlgo]
- **URL**: https://www.luxalgo.com/library/indicator/liquidity-sweeps/
- **Category**: Price Action Sweeps
- **Complexity**: Low
- **Why Medium**: Volume-free sweep detection
- **NautilusTrader Class**: `PureActionSweepDetector`

---

## TIER 4: LOWER PRIORITY (Convert As Needed)

### #16 Order Blocks [LuxAlgo]
- **Category**: SMC Components
- **Complexity**: Medium
- **Why Lower**: Part of SMC indicator, can be extracted
- **NautilusTrader Class**: `OrderBlockDetector`

### #17 Fair Value Gaps (FVG) [LuxAlgo]
- **Category**: SMC Components
- **Complexity**: Low
- **Why Lower**: Part of SMC indicator, can be extracted
- **NautilusTrader Class**: `FairValueGapDetector`

### #18 Volume Profile [LuxAlgo]
- **Category**: Volume Profile
- **Complexity**: High
- **Why Lower**: NautilusTrader may have native implementation
- **NautilusTrader Class**: `VolumeProfile` (check native)

### #19 Break of Structure (BOS) Detector
- **Category**: SMC Components
- **Complexity**: Medium
- **Why Lower**: Extracted from SMC indicator
- **NautilusTrader Class**: `BreakOfStructure`

### #20 Change of Character (CHoCH) Detector
- **Category**: SMC Components
- **Complexity**: Medium
- **Why Lower**: Extracted from SMC indicator
- **NautilusTrader Class**: `ChangeOfCharacter`

---

## CONVERSION WORKFLOW

### Step 1: Fetch Pine Script
```bash
# Use /pinescript skill for complex scripts
/pinescript https://www.tradingview.com/script/OhLE0vnH-Volume-Delta-Methods-Chart-LuxAlgo/
```

### Step 2: Validate Conversion
```python
# Compare outputs between Pine Script and NautilusTrader implementation
# Use historical data for validation
```

### Step 3: Integration Testing
```bash
# Run with test-runner agent
uv run pytest tests/test_<indicator>.py -v
```

### Step 4: Integration with Pipeline
```python
# Add to Spec 025 orderflow pipeline
from strategies.common.orderflow import VolumeDelta, CVDDivergenceDetector
```

---

## SPEC 026 META-LEARNING FEATURES

Extracted features from converted indicators for meta-model:

| Indicator | Features |
|-----------|----------|
| Volume Delta | `delta_value`, `delta_direction`, `delta_momentum` |
| CVD Divergence | `divergence_type`, `divergence_strength`, `resolution_direction` |
| Liquidity Sweeps | `sweep_frequency`, `sweep_direction`, `sweep_magnitude` |
| Tape Speed | `pace_value`, `direction`, `climax_detected` |
| SMC | `structure_type`, `order_block_proximity`, `fvg_size` |

---

## ESTIMATED TIMELINE

| Tier | Scripts | Complexity | Est. Days |
|------|---------|------------|-----------|
| 1 | 5 | Medium-High | 5-7 |
| 2 | 5 | Medium-High | 5-7 |
| 3 | 5 | Medium | 3-5 |
| 4 | 5 | Low-Medium | 2-3 |

**Total**: ~20 scripts, ~15-22 days

---

## ACADEMIC VALIDATION

Each converted indicator should reference:

1. **VPIN Paper** (Easley et al. 2011) - Volume delta foundation
2. **Kyle (1985)** - Market microstructure
3. **Institutional Order Flow** (Campbell et al. 2005) - Tape reading
4. **Smart Money Literature** - ICT methodology

---

*Priority list based on: relevance to Spec 025/026, complexity, NautilusTrader integration potential*
*Sources: [LuxAlgo Library](https://www.luxalgo.com/library/), [TradingView](https://www.tradingview.com)*
