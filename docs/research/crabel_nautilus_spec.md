# Toby Crabel Method - NautilusTrader Implementation Specification

## Executive Summary

This specification outlines the implementation of Toby Crabel's short-term price patterns and Opening Range Breakout (ORB) methodology in NautilusTrader. Based on extensive statistical testing from 1970-1990 across multiple futures markets, the Crabel method demonstrates win rates of 60-81% for specific pattern combinations.

**Key Principle**: Markets alternate between contraction (consolidation) and expansion (trending) phases. Trading breakouts after contraction patterns yields significantly higher success rates (64% avg) compared to breakouts after expansion patterns (52% avg).

---

## 1. CONCEPTS TO IMPLEMENT

### 1.1 Core Pattern Detection

| Pattern | Description | Detection Logic |
|---------|-------------|-----------------|
| **NR4** | Narrowest range in 4 days | `range[0] < min(range[1:4])` |
| **NR7** | Narrowest range in 7 days | `range[0] < min(range[1:7])` |
| **Inside Day (ID)** | High/low within prior day | `high[0] < high[1] AND low[0] > low[1]` |
| **ID/NR4** | Inside Day + NR4 combo | Both conditions true |
| **Doji** | Open ≈ Close (indecision) | `abs(close - open) <= threshold` |
| **2-Bar NR** | Narrowest 2-day range in 20 days | `sum(range[0:2]) < min(sum(range[i:i+2]) for i in 1:19)` |
| **3-Bar NR** | Narrowest 3-day range in 20 days | `sum(range[0:3]) < min(sum(range[i:i+3]) for i in 1:19)` |
| **Bear Hook** | Open < prior low, close > prior close, NR | All three conditions |
| **Bull Hook** | Open > prior high, close < prior close, NR | All three conditions |
| **WS4/WS7** | Widest spread in 4/7 days | `range[0] > max(range[1:4])` or `range[1:7]` |

### 1.2 Entry Mechanisms

| Mechanism | Description | Calculation |
|-----------|-------------|-------------|
| **ORB** | Opening Range Breakout | Buy: `open + stretch`<br>Sell: `open - stretch` |
| **ORBP** | ORB Preference (directional) | Only one direction based on bias |
| **Stretch** | Entry distance from open | `mean([abs(open[i] - nearest_extreme[i]) for i in -10:0])` |

### 1.3 Daily Bias Calculation

**Inputs**:
- Last 4 closes direction (+/-)
- Today's open direction
- Range characteristics (NR/WS)

**Logic**: 5/6 directional indicators must align for strong bias.

---

## 2. IMPLEMENTATION PRIORITY (ROI-BASED RANKING)

### Tier 1: HIGHEST PRIORITY (70%+ Win Rate, Easy Implementation)

| Pattern | Win Rate | Ease | Frequency | Modern Market Fit | Priority Score |
|---------|----------|------|-----------|-------------------|----------------|
| **ID/NR4** | 70-81% | Medium | Rare (1/15 days) | Excellent (crypto volatility cycles) | **95/100** |
| **NR7** | 62-74% | Easy | ~1/15 days | Excellent (works in all conditions) | **90/100** |
| **2-Bar NR** | 60-79% | Medium | ~1/12 days | Good (multi-timeframe applicable) | **85/100** |

**Rationale**:
- ID/NR4 shows exceptional 81% win rate with 2.34:1 win/loss ratio in Bonds
- NR7 is the easiest to implement (simple range comparison)
- 2-Bar NR has highest Day 0 profitability (75-79%)

### Tier 2: HIGH PRIORITY (65%+ Win Rate, Moderate Implementation)

| Pattern | Win Rate | Ease | Frequency | Modern Market Fit | Priority Score |
|---------|----------|------|-----------|-------------------|----------------|
| **Doji + NR** | 61-76% | Easy | Moderate | Good (range-bound markets) | **75/100** |
| **Inside Day** | 60-76% | Easy | ~1/5 days | Excellent (frequent signals) | **80/100** |
| **Bear Hook** | 65-81% | Medium | Rare | Excellent (crypto dumps) | **70/100** |

**Rationale**:
- Inside Day occurs frequently enough for regular trading
- Doji + NR excels in beans/soybeans (applicable to agricultural crypto tokens)
- Bear Hook has 81% win rate in cattle, 70% in bonds (relevant for commodities)

### Tier 3: MEDIUM PRIORITY (60%+ Win Rate, Complex Implementation)

| Pattern | Win Rate | Ease | Frequency | Modern Market Fit | Priority Score |
|---------|----------|------|-----------|-------------------|----------------|
| **NR4** | 60-68% | Easy | ~1/8 days | Good (baseline pattern) | **65/100** |
| **Bull Hook** | 55-78% | Medium | Rare | Medium (less reliable than Bear Hook) | **60/100** |
| **3-Bar NR** | Similar to 2-Bar | Hard | Very rare | Medium (insufficient historical data) | **55/100** |

**Rationale**:
- NR4 is foundational but superseded by NR7/ID/NR4
- Bull Hook less consistent across markets than Bear Hook
- 3-Bar NR lacks sufficient statistical evidence

### Tier 4: LOW PRIORITY (Complementary Tools)

| Feature | Purpose | Priority Score |
|---------|---------|----------------|
| **Early Entry (EE)** | Intraday momentum confirmation | **50/100** |
| **Upthrust/Spring** | False breakout detection | **45/100** |
| **Daily Bias** | Directional filter | **70/100** (important for ORBP) |
| **Stretch Calculation** | Entry point calibration | **85/100** (critical for ORB) |

---

## 3. CODE DESIGN

### 3.1 Pattern Detection: NR7 (Baseline Implementation)

```python
from nautilus_trader.indicators.base.indicator import Indicator
from nautilus_trader.model.data import Bar

class NR7Detector(Indicator):
    """
    Detects Narrow Range 7 pattern (narrowest range in 7 days).

    Inputs:
        - OHLC bars (daily timeframe recommended)

    Output:
        - Boolean: True if current bar is NR7
    """

    def __init__(self):
        super().__init__()
        self.period = 7
        self.ranges = []

    def handle_bar(self, bar: Bar):
        """Update with new bar data."""
        current_range = bar.high - bar.low
        self.ranges.append(current_range)

        if len(self.ranges) < self.period:
            self.value = False
            return

        # Keep only last 7 ranges
        if len(self.ranges) > self.period:
            self.ranges.pop(0)

        # NR7: current range is minimum of last 7 days
        self.value = current_range == min(self.ranges)

    @property
    def is_nr7(self) -> bool:
        return self.value
```

**Entry Logic**:
```python
def on_bar(self, bar: Bar):
    self.nr7_detector.handle_bar(bar)

    if self.nr7_detector.is_nr7:
        stretch = self.calculate_stretch()

        # Place buy stop above open + stretch
        buy_price = bar.open + stretch
        self.submit_order(
            order=self.order_factory.stop_market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.position_size,
                trigger_price=buy_price,
            )
        )

        # Place sell stop below open - stretch
        sell_price = bar.open - stretch
        self.submit_order(
            order=self.order_factory.stop_market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=self.position_size,
                trigger_price=sell_price,
            )
        )
```

**Stop Loss Calculation**:
```python
def on_order_filled(self, event: OrderFilled):
    """When one stop is hit, cancel the other and use it as stop loss."""
    if event.order_side == OrderSide.BUY:
        # Cancel sell stop, place new stop loss at open - stretch
        self.cancel_order(self.sell_stop_order)
        stop_loss_price = self.current_bar.open - self.stretch
        self.submit_order(
            order=self.order_factory.stop_market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=event.quantity,
                trigger_price=stop_loss_price,
            )
        )
```

---

### 3.2 Pattern Detection: ID/NR4 (Highest Win Rate)

```python
class InsideDayNR4Detector(Indicator):
    """
    Detects Inside Day + NR4 combination pattern.

    Outputs:
        - is_inside_day: Boolean
        - is_nr4: Boolean
        - is_id_nr4: Boolean (combo)
    """

    def __init__(self):
        super().__init__()
        self.bars = []

    def handle_bar(self, bar: Bar):
        self.bars.append(bar)

        if len(self.bars) < 5:  # Need 5 bars (current + 4 prior)
            return

        if len(self.bars) > 5:
            self.bars.pop(0)

        current = self.bars[-1]
        prior = self.bars[-2]

        # Inside Day check
        self.is_inside_day = (
            current.high < prior.high and
            current.low > prior.low
        )

        # NR4 check
        current_range = current.high - current.low
        prior_ranges = [b.high - b.low for b in self.bars[-5:-1]]
        self.is_nr4 = current_range < min(prior_ranges)

        # Combo check
        self.is_id_nr4 = self.is_inside_day and self.is_nr4
```

**Entry Logic** (81% win rate in Bonds +16 ticks):
```python
def on_bar(self, bar: Bar):
    self.id_nr4_detector.handle_bar(bar)

    if self.id_nr4_detector.is_id_nr4:
        stretch = self.calculate_stretch()

        # HIGHER CONVICTION: Increase position size by 1.5x
        position_size = self.base_position_size * 1.5

        # Narrower stretch (more aggressive entry)
        buy_price = bar.open + (stretch * 0.8)  # 80% of normal stretch
        sell_price = bar.open - (stretch * 0.8)

        # Place orders with tighter stops (pattern has 2.34:1 win/loss)
        self.place_orb_orders(buy_price, sell_price, position_size)
```

---

### 3.3 Stretch Calculation

```python
class StretchCalculator:
    """
    Calculates the average distance from open to nearest extreme.

    Formula: Mean of last 10 days' (open - nearest_extreme)
    """

    def __init__(self, period: int = 10):
        self.period = period
        self.daily_stretches = []

    def calculate(self, bars: List[Bar]) -> float:
        """
        Calculate stretch from historical bars.

        Args:
            bars: List of daily bars (minimum 10)

        Returns:
            Average stretch value
        """
        if len(bars) < self.period:
            raise ValueError(f"Need at least {self.period} bars")

        for bar in bars[-self.period:]:
            # Distance from open to nearest extreme
            distance_to_high = abs(bar.high - bar.open)
            distance_to_low = abs(bar.low - bar.open)
            nearest_extreme_distance = min(distance_to_high, distance_to_low)
            self.daily_stretches.append(nearest_extreme_distance)

        return sum(self.daily_stretches) / len(self.daily_stretches)
```

---

### 3.4 Doji Detection

```python
class DojiDetector(Indicator):
    """
    Detects Doji patterns (open ≈ close).

    Thresholds per market (from Crabel):
        - Bonds: 5-8 ticks
        - S&P: 50 points
        - Beans: 3-5 cents
        - Crypto (BTC): 0.5% of price
    """

    def __init__(self, threshold: float):
        super().__init__()
        self.threshold = threshold

    def handle_bar(self, bar: Bar):
        """Check if bar is a doji."""
        body_size = abs(bar.close - bar.open)
        self.value = body_size <= self.threshold

    @property
    def is_doji(self) -> bool:
        return self.value
```

**Doji + NR Combination**:
```python
class DojiNRStrategy(Strategy):
    """
    Trade Doji + Narrow Range pattern.

    Stats: 76% win rate in Soybeans (Doji 5¢ + Range < 10¢)
    """

    def on_bar(self, bar: Bar):
        self.doji_detector.handle_bar(bar)

        is_doji = self.doji_detector.is_doji
        is_narrow_range = (bar.high - bar.low) < self.narrow_threshold

        if is_doji and is_narrow_range:
            # Bias: SELL preferred (67-76% vs 60-62% for BUY)
            stretch = self.calculate_stretch()
            sell_price = bar.open - stretch

            self.submit_order(
                order=self.order_factory.stop_market(
                    instrument_id=self.instrument_id,
                    order_side=OrderSide.SELL,
                    quantity=self.position_size,
                    trigger_price=sell_price,
                )
            )
```

---

### 3.5 Hook Day Detection

```python
class HookDayDetector(Indicator):
    """
    Detects Bear Hook and Bull Hook patterns.

    Bear Hook (SELL bias 65-81%):
        - Open < prior low
        - Close > prior close
        - Range < prior range

    Bull Hook (BUY bias 55-78%):
        - Open > prior high
        - Close < prior close
        - Range < prior range
    """

    def __init__(self):
        super().__init__()
        self.is_bear_hook = False
        self.is_bull_hook = False
        self.bars = []

    def handle_bar(self, bar: Bar):
        self.bars.append(bar)

        if len(self.bars) < 2:
            return

        if len(self.bars) > 2:
            self.bars.pop(0)

        current = self.bars[-1]
        prior = self.bars[-2]

        current_range = current.high - current.low
        prior_range = prior.high - prior.low

        # Bear Hook
        self.is_bear_hook = (
            current.open < prior.low and
            current.close > prior.close and
            current_range < prior_range
        )

        # Bull Hook
        self.is_bull_hook = (
            current.open > prior.high and
            current.close < prior.close and
            current_range < prior_range
        )
```

**Trading Logic**:
```python
def on_bar(self, bar: Bar):
    self.hook_detector.handle_bar(bar)

    if self.hook_detector.is_bear_hook:
        # SELL with high confidence (70-81% win rate)
        # Best: Cattle -50 pts (81%), Bonds -8 ticks (70%)
        stretch = self.calculate_stretch()
        sell_price = bar.open - stretch

        self.submit_order(
            order=self.order_factory.stop_market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=self.position_size * 1.2,  # Increase size
                trigger_price=sell_price,
            )
        )

    elif self.hook_detector.is_bull_hook:
        # BUY with moderate confidence (55-78% win rate)
        # Best: Cattle +25 pts (78%), Bonds +8 ticks (74%)
        stretch = self.calculate_stretch()
        buy_price = bar.open + stretch

        self.submit_order(
            order=self.order_factory.stop_market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.position_size,
                trigger_price=buy_price,
            )
        )
```

---

### 3.6 Two-Bar NR Detection

```python
class TwoBarNRDetector(Indicator):
    """
    Detects 2-Bar NR pattern (narrowest 2-day range in 20 days).

    Origin: Wyckoff's Last Point of Supply/Support concept
    Stats: 75-79% win rate on Day 0 (close of entry day)
    """

    def __init__(self, lookback: int = 20):
        super().__init__()
        self.lookback = lookback
        self.bars = []

    def handle_bar(self, bar: Bar):
        self.bars.append(bar)

        if len(self.bars) < self.lookback + 2:
            self.value = False
            return

        if len(self.bars) > self.lookback + 2:
            self.bars.pop(0)

        # Calculate current 2-day range
        current_2day_range = self._calculate_2day_range(-2, -1)

        # Compare with all prior 2-day ranges in lookback period
        is_narrowest = True
        for i in range(-self.lookback - 2, -2):
            prior_2day_range = self._calculate_2day_range(i, i + 1)
            if current_2day_range >= prior_2day_range:
                is_narrowest = False
                break

        self.value = is_narrowest

    def _calculate_2day_range(self, start_idx: int, end_idx: int) -> float:
        """Calculate combined range of 2 consecutive bars."""
        bars_slice = self.bars[start_idx:end_idx + 1]
        high_2day = max(b.high for b in bars_slice)
        low_2day = min(b.low for b in bars_slice)
        return high_2day - low_2day
```

**Exit Strategy** (Critical for 2-Bar NR):
```python
def on_bar(self, bar: Bar):
    self.two_bar_nr_detector.handle_bar(bar)

    if self.two_bar_nr_detector.value:
        # Place ORB orders
        stretch = self.calculate_stretch()
        self.place_orb_orders(bar.open + stretch, bar.open - stretch)

        # CRITICAL: Exit at close of Day 0 (76% win rate)
        # Day 1-5 win rates decline to 62-66%
        self.exit_at_close = True  # Flag to close position at EOD
```

---

### 3.7 Daily Bias Calculator

```python
class DailyBiasCalculator:
    """
    Calculate daily bias based on 5-day pattern analysis.

    Inputs:
        - Last 4 closes direction (+/-)
        - Today's open direction
        - Range characteristics (NR/WS)

    Output:
        - Bias: "STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"
    """

    def __init__(self):
        self.bias_scores = {
            "STRONG_BUY": 0,
            "BUY": 0,
            "NEUTRAL": 0,
            "SELL": 0,
            "STRONG_SELL": 0,
        }

    def calculate(self, bars: List[Bar]) -> str:
        """
        Calculate bias from last 5 bars.

        Rule: 5/6 directional indicators must align for strong bias.
        """
        if len(bars) < 5:
            return "NEUTRAL"

        directional_signals = []

        # Analyze last 4 closes
        for i in range(-5, -1):
            if bars[i].close > bars[i - 1].close:
                directional_signals.append(1)  # UP
            else:
                directional_signals.append(-1)  # DOWN

        # Today's open direction
        if bars[-1].open > bars[-2].close:
            directional_signals.append(1)  # UP
        else:
            directional_signals.append(-1)  # DOWN

        # Count signals
        up_count = sum(1 for s in directional_signals if s == 1)
        down_count = sum(1 for s in directional_signals if s == -1)

        # Strong bias: 5/6 or 6/6 alignment
        if up_count >= 5:
            return "STRONG_BUY"
        elif up_count == 4:
            return "BUY"
        elif down_count >= 5:
            return "STRONG_SELL"
        elif down_count == 4:
            return "SELL"
        else:
            return "NEUTRAL"
```

**ORBP (ORB Preference) with Bias**:
```python
def on_bar(self, bar: Bar):
    bias = self.bias_calculator.calculate(self.bars)

    if bias == "STRONG_BUY":
        # Only place BUY stop (ORBP upside)
        stretch = self.calculate_stretch()
        buy_price = bar.open + stretch

        self.submit_order(
            order=self.order_factory.stop_market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.position_size * 1.5,  # Increase conviction
                trigger_price=buy_price,
            )
        )

        # Wait for entry before placing stop loss
        # If market hits opposite stretch first, cancel ORBP

    elif bias == "STRONG_SELL":
        # Only place SELL stop (ORBP downside)
        # ... similar logic
```

---

## 4. BACKTESTING REQUIREMENTS

### 4.1 Test Data Requirements

| Data Type | Specifications | Minimum History |
|-----------|----------------|-----------------|
| **Timeframe** | Daily bars (OHLC) | 1 year (250+ trading days) |
| **Markets** | Futures, Crypto, Forex | Multiple for validation |
| **Precision** | Tick-level for ORB entries | Intraday 5-min bars |
| **Quality** | Clean data (no gaps) | Verified OHLC consistency |

**Recommended Test Datasets**:
1. **Crypto**: BTC/USDT, ETH/USDT (2020-2025) - High volatility, 24/7 trading
2. **Futures**: ES (S&P 500), NQ (Nasdaq), GC (Gold) - Replicates original Crabel tests
3. **Forex**: EUR/USD, GBP/USD - Lower volatility, range-bound behavior

### 4.2 Performance Metrics

**Primary Metrics** (from Crabel research):
| Metric | Target | Calculation |
|--------|--------|-------------|
| **Win Rate** | 60%+ baseline, 70%+ for ID/NR4 | `winning_trades / total_trades` |
| **Win/Loss Ratio** | 1.0+ (breakeven), 2.0+ ideal | `avg_win / avg_loss` |
| **Gross Profit** | Positive after 100+ trades | `sum(all_trade_pnl)` |
| **Max Drawdown** | < 20% of capital | `max(peak - trough)` |

**Secondary Metrics**:
- **Sharpe Ratio**: > 1.5 (risk-adjusted returns)
- **Profit Factor**: > 1.5 (`gross_profit / gross_loss`)
- **Average Trade Duration**: < 1 day (Crabel is intraday system)
- **Frequency**: 1-2 trades per week per pattern (sustainable)

### 4.3 Look-Ahead Bias Prevention

**Critical Rules**:

1. **Pattern Detection**: Only use data available at market open
   ```python
   # WRONG: Uses close price before close time
   if is_nr7_at_open(bar):  # Can't know if NR7 until close!
       place_order()

   # CORRECT: Detect pattern on prior day's close
   if was_nr7_yesterday():
       place_orb_orders_today()
   ```

2. **Stretch Calculation**: Use only past 10 days (not including current day)
   ```python
   # CORRECT
   stretch = calculate_stretch(bars[-11:-1])  # Last 10 complete bars

   # WRONG
   stretch = calculate_stretch(bars[-10:])  # Includes current incomplete bar
   ```

3. **ORB Entry Timing**: Orders placed at market open, triggered intraday
   ```python
   def on_bar(self, bar: Bar):
       if bar.is_open():  # First tick of the day
           if self.detected_pattern_yesterday:
               self.place_orb_orders(bar.open)
   ```

4. **Stop Loss**: Must be from opposite ORB level, not hindsight optimization
   ```python
   # CORRECT: Use opposite stretch as stop (Crabel method)
   if filled_buy_at_open_plus_stretch:
       stop_loss = open_minus_stretch

   # WRONG: Optimize stop based on backtest results
   stop_loss = open - (stretch * 1.37)  # Curve-fitted!
   ```

### 4.4 Backtest Validation Framework

```python
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.backtest.engine import BacktestEngine

class CrabelBacktestValidator:
    """
    Validates Crabel pattern implementation against historical stats.

    Compares backtest results to Crabel's published statistics:
        - NR7 Bonds +16 ticks: Expected 74% win rate
        - ID/NR4 Bonds +16 ticks: Expected 81% win rate
        - 2-Bar NR Day 0 exit: Expected 75-79% win rate
    """

    def __init__(self, engine: BacktestEngine):
        self.engine = engine
        self.expected_stats = {
            "NR7_bonds_plus16": {"win_rate": 0.74, "trades": 81},
            "ID_NR4_bonds_plus16": {"win_rate": 0.81, "trades": 31},
            "TwoBarNR_day0": {"win_rate": 0.76, "trades": 34},
        }

    def validate(self, pattern_name: str, results: dict) -> bool:
        """
        Check if backtest results match expected Crabel statistics.

        Tolerance: ±5% win rate, ±20% trade count (market regime differences)
        """
        expected = self.expected_stats.get(pattern_name)
        if not expected:
            return True  # No validation data available

        win_rate_match = abs(results["win_rate"] - expected["win_rate"]) <= 0.05
        trade_count_reasonable = (
            results["total_trades"] >= expected["trades"] * 0.8 and
            results["total_trades"] <= expected["trades"] * 1.2
        )

        return win_rate_match and trade_count_reasonable
```

**Example Backtest Configuration**:
```python
config = BacktestEngineConfig(
    # Prevent look-ahead bias
    bypass_logging=False,  # Log all order placements

    # Realistic execution
    fill_model=FillModel.AUCTION,  # Market orders fill at open

    # Commission structure (futures-style)
    commission=Commission(
        commission_type=CommissionType.PER_TRADE,
        rate=Decimal("2.50"),  # $2.50 per contract
    ),

    # Slippage (0.5 ticks average)
    slippage=Slippage(
        slippage_type=SlippageType.FIXED,
        basis_points=Decimal("5"),
    ),
)
```

---

## 5. MODERN MARKET ADAPTATIONS

### 5.1 Crypto-Specific Adjustments

**Threshold Calibration** (Crabel didn't test crypto):

| Pattern | Original (Bonds) | Crypto (BTC) | Crypto (ETH) |
|---------|------------------|--------------|--------------|
| **Doji** | 5-8 ticks | 0.3% of price | 0.5% of price |
| **Stretch** | 16 ticks ($500) | 1.5% ATR | 2.0% ATR |
| **ORB Entry** | Open ± 16 ticks | Open ± 1.5% | Open ± 2.0% |

**24/7 Trading**: Use daily close at 00:00 UTC or exchange-native daily bar.

### 5.2 High-Frequency Considerations

**Intraday ORB** (not in original Crabel, but natural extension):
- Apply NR7/ID/NR4 to 1-hour bars instead of daily
- Stretch calculation on 10-period 1H bars
- Entry on 5-min ORB breakout
- Exit within same 1-hour bar

### 5.3 Risk Management Enhancements

**Crabel Original** (minimal risk management):
- Stop loss: Opposite ORB level
- Move to breakeven: Within 1 hour (S&P: 5-10 minutes)

**Modern Enhancement**:
```python
class ModernCrabelRiskManager:
    """Enhanced risk management for Crabel patterns."""

    def __init__(self, max_risk_per_trade: float = 0.02):
        self.max_risk_pct = max_risk_per_trade  # 2% of capital

    def calculate_position_size(self, capital: float, entry: float,
                                stop: float) -> float:
        """
        Position size based on fixed percentage risk.

        Example:
            - Capital: $100,000
            - Entry: BTC $50,000
            - Stop: BTC $49,000 (2% move)
            - Max risk: $2,000 (2% of capital)
            - Position size: $2,000 / $1,000 = 2 BTC
        """
        risk_per_unit = abs(entry - stop)
        max_loss_amount = capital * self.max_risk_pct
        position_size = max_loss_amount / risk_per_unit
        return position_size

    def move_stop_to_breakeven(self, elapsed_minutes: int,
                              pattern: str) -> bool:
        """
        Determine if stop should move to breakeven.

        Crabel's rule: Within 1 hour (S&P: 5-10 min)
        Modern: Pattern-dependent + profit-based trigger
        """
        breakeven_time = {
            "ID_NR4": 15,  # High conviction, move fast
            "NR7": 30,
            "NR4": 60,
            "Doji": 60,
        }
        return elapsed_minutes >= breakeven_time.get(pattern, 60)
```

---

## 6. IMPLEMENTATION ROADMAP

### Phase 1: Core Patterns (Weeks 1-2)
- [ ] NR7 detector + ORB strategy
- [ ] Stretch calculator
- [ ] Backtest framework setup
- [ ] Validation against Crabel's Bonds NR7 stats (74% win rate target)

### Phase 2: High-Value Combos (Weeks 3-4)
- [ ] Inside Day detector
- [ ] ID/NR4 combo strategy
- [ ] Daily Bias calculator (for ORBP)
- [ ] Backtest validation (81% win rate target for ID/NR4)

### Phase 3: Advanced Patterns (Weeks 5-6)
- [ ] 2-Bar NR detector
- [ ] Hook Day detector
- [ ] Doji + NR combo
- [ ] Multi-pattern portfolio backtest

### Phase 4: Modern Enhancements (Weeks 7-8)
- [ ] Crypto-specific calibration
- [ ] Intraday ORB (1-hour bars)
- [ ] Enhanced risk management
- [ ] Live trading readiness (paper trading)

### Phase 5: Production (Week 9+)
- [ ] Multi-market deployment (BTC, ETH, ES, NQ)
- [ ] Real-time pattern monitoring dashboard
- [ ] Alert system for high-probability setups
- [ ] Continuous performance tracking vs Crabel benchmarks

---

## 7. EXPECTED RESULTS

### Statistical Benchmarks (From Crabel Research)

**Baseline (Any Day ORB)**:
- Win rate: 55-60%
- Profit factor: ~1.2
- Frequency: Daily opportunities

**After Pattern Filtering**:

| Pattern Applied | Win Rate Improvement | Profit Multiplier | Frequency |
|----------------|---------------------|-------------------|-----------|
| **NR7** | +10-15% | 3-5x baseline | ~1/15 days |
| **ID/NR4** | +20-25% | 7x baseline | ~1/20 days |
| **2-Bar NR** | +15-20% | 4-6x baseline | ~1/12 days |
| **Doji + NR** | +10-15% | 2-3x baseline | Moderate |

**Portfolio Expectation** (Trading all patterns):
- Overall win rate: 65-70%
- Profit factor: 2.0+
- Max drawdown: 15-20%
- Sharpe ratio: 1.5-2.0
- Trade frequency: 2-4 signals per week (per market)

**Modern Market Adjustment**: Expect 5-10% lower win rates than 1980s futures due to:
- Increased market efficiency
- Algorithmic competition
- Different volatility regimes
- 24/7 crypto markets (vs futures hours)

**Target: 60%+ win rate with 1.5+ profit factor = profitable system**

---

## 8. KEY IMPLEMENTATION NOTES

### 8.1 NautilusTrader-Specific Patterns

**Use Native Rust Indicators**:
```python
# WRONG: Custom Python range calculation
def calculate_range(high, low):
    return high - low

# CORRECT: Use built-in bar properties (Rust-optimized)
bar.range  # Already calculated in Rust
```

**Streaming Data Architecture**:
```python
# CORRECT: Process bars as they arrive
def on_bar(self, bar: Bar):
    self.pattern_detector.handle_bar(bar)
    if self.pattern_detector.value:
        self.place_orders()

# WRONG: Load all bars into memory
bars = load_all_historical_bars()  # OOM on large datasets
for bar in bars:
    process(bar)
```

### 8.2 Avoiding Common Pitfalls

**1. Pattern Detection Timing**:
- Detect pattern on Day N close
- Place orders on Day N+1 open
- Never use Day N+1 data for Day N analysis

**2. Overfitting Prevention**:
- Use Crabel's original thresholds (16 ticks, 160 pts, etc.)
- Only calibrate Doji/Stretch for new markets
- Validate with out-of-sample data (last 6 months held out)

**3. Execution Realism**:
- Include 0.5-1 tick slippage on ORB entries
- Model commission ($2.50/contract futures, 0.05% crypto)
- Account for partial fills on limit orders

**4. Edge Case Handling**:
```python
# Handle missing bars (holidays, halted trading)
if len(self.bars) < self.required_bars:
    self.log.warning("Insufficient data, skipping pattern check")
    return

# Handle extreme volatility (prevent blown stops)
if bar.range > self.median_range * 3:
    self.log.info("Extreme volatility detected, skipping ORB")
    return
```

---

## 9. GLOSSARY

| Term | Definition | NautilusTrader Equivalent |
|------|------------|---------------------------|
| **ORB** | Opening Range Breakout | `StopMarket` order at `open ± stretch` |
| **Stretch** | Avg distance open→extreme (10 days) | Custom indicator, calculated via `BarAggregator` |
| **NR4/NR7** | Narrowest range in 4/7 days | Custom `Indicator` subclass |
| **Inside Day** | Range within prior day | Boolean check: `bar.high < prior.high AND bar.low > prior.low` |
| **Doji** | Open ≈ Close | `abs(bar.close - bar.open) <= threshold` |
| **Daily Bias** | Directional tendency | Multi-bar pattern analysis (5-day window) |
| **ORBP** | ORB Preference (one direction) | Single `StopMarket` order (not bracketed) |
| **Contraction** | Consolidation (NR, ID) | Low volatility signal → trade breakout |
| **Expansion** | Trending (WS) | High volatility signal → avoid ORB or fade |

---

## 10. REFERENCES

**Primary Source**:
- Crabel, T. (1990). *Day Trading with Short Term Price Patterns and Opening Range Breakout*. Greenville, SC: Traders Press.

**Supporting Documents**:
- `/media/sam/1TB/nautilus_dev/docs/research/toby crabel/Metodo_Crabel_Completo.md`
- `/media/sam/1TB/nautilus_dev/docs/research/toby crabel/Crabel_Tabelle_Statistiche.md`

**NautilusTrader Documentation**:
- Strategy API: https://nautilustrader.io/docs/api_reference/trading
- Indicators: https://nautilustrader.io/docs/api_reference/indicators
- Backtesting: https://nautilustrader.io/docs/concepts/backtesting

**Modern Validations**:
- Pair trading journal articles validating NR patterns (2015-2020)
- Cryptocurrency volatility studies (2020-2025)
- Academic papers on opening range breakout efficacy

---

## APPENDIX A: Quick Start Checklist

```markdown
## Before Implementation:
- [ ] Read Metodo_Crabel_Completo.md (full methodology)
- [ ] Review Crabel_Tabelle_Statistiche.md (statistical tables)
- [ ] Understand contraction/expansion principle
- [ ] Identify target markets (crypto, futures, forex)

## Phase 1 MVP (NR7 + ORB):
- [ ] Implement NR7Detector indicator
- [ ] Implement StretchCalculator
- [ ] Create CrabelORBStrategy with NR7 filter
- [ ] Backtest on BTC/USDT daily (2020-2025)
- [ ] Validate: Win rate 62-67% (target from Crabel S&P stats)

## Phase 2 Enhancement (ID/NR4):
- [ ] Implement InsideDayNR4Detector
- [ ] Integrate with CrabelORBStrategy
- [ ] Backtest and compare to NR7-only
- [ ] Validate: Win rate 70-81% for ID/NR4 signals

## Phase 3 Production:
- [ ] Add DailyBiasCalculator for ORBP
- [ ] Implement risk management (2% max risk per trade)
- [ ] Deploy to paper trading
- [ ] Monitor for 2 weeks (minimum 10 trades)
- [ ] Go live with 1 contract/coin

## Success Criteria:
- [ ] Win rate: 60%+ (baseline), 70%+ (ID/NR4)
- [ ] Profit factor: 1.5+
- [ ] Max drawdown: < 20%
- [ ] Sharpe ratio: > 1.5
```

---

**Last Updated**: 2026-01-03
**Version**: 1.0
**Author**: Analysis of Toby Crabel methodology for NautilusTrader implementation
