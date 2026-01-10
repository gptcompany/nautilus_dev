# PineScript to NautilusTrader Converter

Convert TradingView Pine Script strategies to NautilusTrader Python strategies.

## Invocation

```
/pinescript <url_or_paste>
/pinescript https://tradingview.com/script/ABC123
/pinescript   # Then paste code
```

## Automatic Source Code Extraction

The skill includes an automated extractor that fetches Pine Script source code from TradingView URLs.

### How It Works

1. **Playwright browser automation** opens the TradingView script page
2. **Network interception** captures the `pine-facade.tradingview.com` API response
3. **JSON parsing** extracts the source code and metadata

### API Endpoint Discovered

TradingView loads script source via:
```
https://pine-facade.tradingview.com/pine-facade/get/PUB%3B{script_id}/{version}?no_4xx=true
```

### Extractor Script

```bash
# Usage
python scripts/pinescript_extractor.py <tradingview_url>

# Example
python scripts/pinescript_extractor.py https://www.tradingview.com/script/tMtleB1G-Liqudation-HeatMap-BigBeluga/

# Output: JSON with source code and metadata
{
  "success": true,
  "url": "https://...",
  "name": "Liquidation HeatMap [BigBeluga]",
  "source": "// Pine Script code...",
  "metadata": {
    "created": "2025-05-16T14:05:30.827152Z",
    "pine_version": 5,
    "kind": "study"
  }
}
```

### Requirements

```bash
pip install playwright
playwright install chromium
```

### Limitations

- **Open-source scripts only** - Protected/invite-only scripts cannot be extracted
- **Requires Playwright** - Headless browser needed for dynamic content
- **Rate limiting** - Don't abuse TradingView's servers

## Workflow

### Step 1: Input Acquisition

**Option A: URL (Automatic Extraction)**
```
/pinescript https://tradingview.com/script/ABC123
```
- Runs `scripts/pinescript_extractor.py` to fetch source code
- Falls back to manual paste if extraction fails

**Option B: Direct Paste**
```
/pinescript
> Paste your Pine Script code:
```

### Step 2: Parse Pine Script

Extract components:

```yaml
Metadata:
  name: "Strategy Name"
  version: pine_version (v4, v5, v6)
  type: strategy|indicator|library

Inputs:
  - name: length
    type: int
    default: 14
  - name: src
    type: source
    default: close

Indicators:
  - name: rsi
    function: ta.rsi(src, length)
  - name: ema_fast
    function: ta.ema(close, 9)
  - name: ema_slow
    function: ta.ema(close, 21)

Entry_Conditions:
  long: "ta.crossover(ema_fast, ema_slow) and rsi < 70"
  short: "ta.crossunder(ema_fast, ema_slow) and rsi > 30"

Exit_Conditions:
  long: "ta.crossunder(ema_fast, ema_slow)"
  short: "ta.crossover(ema_fast, ema_slow)"

Risk_Management:
  stop_loss: "strategy.exit(..., stop=...)"
  take_profit: "strategy.exit(..., limit=...)"
  position_size: "strategy.entry(..., qty=...)"
```

### Step 3: Map to NautilusTrader

Reference: `docs/research/indicator_mapping.md`

| Pine Script | NautilusTrader |
|-------------|----------------|
| `ta.ema(src, len)` | `ExponentialMovingAverage(period=len)` |
| `ta.sma(src, len)` | `SimpleMovingAverage(period=len)` |
| `ta.rsi(src, len)` | `RelativeStrengthIndex(period=len)` |
| `ta.macd(src, fast, slow, sig)` | `MovingAverageConvergenceDivergence(fast, slow, sig)` |
| `ta.atr(len)` | `AverageTrueRange(period=len)` |
| `ta.bbands(src, len, mult)` | `BollingerBands(period=len, k=mult)` |
| `ta.stoch(close, high, low, len)` | `Stochastics(period=len)` |
| `ta.crossover(a, b)` | `a.value > b.value and prev_a <= prev_b` |
| `ta.crossunder(a, b)` | `a.value < b.value and prev_a >= prev_b` |
| `strategy.entry("Long", ...)` | `self.submit_order(OrderSide.BUY, ...)` |
| `strategy.entry("Short", ...)` | `self.submit_order(OrderSide.SELL, ...)` |
| `strategy.close("Long")` | `self.close_position(PositionSide.LONG)` |
| `strategy.exit(..., stop=X)` | `OrderType.STOP_MARKET` |
| `strategy.exit(..., limit=X)` | `OrderType.LIMIT` |

### Step 4: Generate NautilusTrader Strategy

```python
# Auto-generated from Pine Script: {script_name}
# Source: {url}
# Converted: {date}

from decimal import Decimal
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.trading.strategy import Strategy

# Native Rust indicators
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.indicators.rsi import RelativeStrengthIndex


class {StrategyName}Config(StrategyConfig, frozen=True):
    """Configuration for {StrategyName}."""

    instrument_id: str
    bar_type: str
    # Pine Script inputs converted to config
    {config_params}


class {StrategyName}(Strategy):
    """
    {strategy_description}

    Converted from Pine Script: {script_name}
    Source: {url}

    Entry Logic:
        Long: {long_entry_description}
        Short: {short_entry_description}

    Exit Logic:
        Long: {long_exit_description}
        Short: {short_exit_description}
    """

    def __init__(self, config: {StrategyName}Config) -> None:
        super().__init__(config)

        # Configuration
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)

        # Indicators (Native Rust)
        {indicator_init}

        # State tracking
        self._prev_values: dict = {}

    def on_start(self) -> None:
        """Initialize strategy on start."""
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Instrument {self.instrument_id} not found")
            return

        self.subscribe_bars(self.bar_type)
        self.log.info(f"{self.__class__.__name__} started")

    def on_bar(self, bar: Bar) -> None:
        """Handle bar updates."""
        # Update indicators
        {indicator_updates}

        # Check if indicators initialized
        if not self._indicators_ready():
            return

        # Check entry conditions
        {entry_logic}

        # Check exit conditions
        {exit_logic}

        # Store previous values for crossover detection
        self._store_prev_values()

    def _indicators_ready(self) -> bool:
        """Check if all indicators are initialized."""
        return {indicators_ready_check}

    def _check_long_entry(self) -> bool:
        """Pine Script long entry condition."""
        {long_entry_condition}

    def _check_short_entry(self) -> bool:
        """Pine Script short entry condition."""
        {short_entry_condition}

    def _check_long_exit(self) -> bool:
        """Pine Script long exit condition."""
        {long_exit_condition}

    def _check_short_exit(self) -> bool:
        """Pine Script short exit condition."""
        {short_exit_condition}

    def _enter_long(self, bar: Bar) -> None:
        """Enter long position."""
        if self.portfolio.is_flat(self.instrument_id):
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=self.instrument.make_qty({position_size}),
                time_in_force=TimeInForce.GTC,
            )
            self.submit_order(order)
            self.log.info(f"LONG entry @ {bar.close}")

    def _enter_short(self, bar: Bar) -> None:
        """Enter short position."""
        if self.portfolio.is_flat(self.instrument_id):
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=self.instrument.make_qty({position_size}),
                time_in_force=TimeInForce.GTC,
            )
            self.submit_order(order)
            self.log.info(f"SHORT entry @ {bar.close}")

    def _exit_long(self, bar: Bar) -> None:
        """Exit long position."""
        position = self.portfolio.position(self.instrument_id)
        if position and position.is_long:
            self.close_position(position)
            self.log.info(f"LONG exit @ {bar.close}")

    def _exit_short(self, bar: Bar) -> None:
        """Exit short position."""
        position = self.portfolio.position(self.instrument_id)
        if position and position.is_short:
            self.close_position(position)
            self.log.info(f"SHORT exit @ {bar.close}")

    def _store_prev_values(self) -> None:
        """Store previous indicator values for crossover detection."""
        {store_prev_values}

    def on_stop(self) -> None:
        """Clean up on stop."""
        self.close_all_positions(self.instrument_id)
        self.cancel_all_orders(self.instrument_id)
        self.log.info(f"{self.__class__.__name__} stopped")
```

### Step 5: Generate Test File

```python
# tests/test_{strategy_name_lower}.py

import pytest
from nautilus_trader.backtest.node import BacktestNode
from strategies.{strategy_name_lower} import {StrategyName}, {StrategyName}Config


class Test{StrategyName}:
    """Tests for {StrategyName} converted from Pine Script."""

    def test_config_creation(self):
        """Test strategy configuration."""
        config = {StrategyName}Config(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            {test_config_params}
        )
        assert config.instrument_id == "BTCUSDT-PERP.BINANCE"

    def test_indicator_initialization(self):
        """Test indicators initialize correctly."""
        # Test implementation
        pass

    def test_entry_conditions(self):
        """Test entry logic matches Pine Script."""
        # Test implementation
        pass

    def test_exit_conditions(self):
        """Test exit logic matches Pine Script."""
        # Test implementation
        pass
```

### Step 6: Output

Create files:
```
strategies/{strategy_name_lower}/
├── __init__.py
├── {strategy_name_lower}_strategy.py    # Main strategy
├── config.py                             # Configuration
├── README.md                             # Documentation
└── pine_source.txt                       # Original Pine Script

tests/
└── test_{strategy_name_lower}.py         # Tests
```

Output report:
```markdown
## Pine Script Conversion Report

**Source**: {url}
**Strategy**: {strategy_name}
**Converted**: {date}

### Indicators Mapped

| Pine Script | NautilusTrader | Status |
|-------------|----------------|--------|
| ta.ema(close, 9) | ExponentialMovingAverage(9) | ✅ Native |
| ta.rsi(close, 14) | RelativeStrengthIndex(14) | ✅ Native |

### Entry/Exit Logic

**Long Entry**: {description}
**Long Exit**: {description}
**Short Entry**: {description}
**Short Exit**: {description}

### Files Created
- `strategies/{name}/{name}_strategy.py`
- `strategies/{name}/config.py`
- `tests/test_{name}.py`

### Manual Review Needed
- [ ] Verify position sizing logic
- [ ] Check stop-loss/take-profit levels
- [ ] Validate indicator parameters
- [ ] Run backtest comparison

### Next Steps
1. Review generated code
2. Run tests: `pytest tests/test_{name}.py -v`
3. Backtest: Use BacktestNode with catalog data
4. Compare with TradingView results
```

## Pine Script Function Reference

### Indicators

| Pine v5 | NautilusTrader | Notes |
|---------|----------------|-------|
| `ta.sma()` | `SimpleMovingAverage` | Native Rust |
| `ta.ema()` | `ExponentialMovingAverage` | Native Rust |
| `ta.wma()` | `WeightedMovingAverage` | Native Rust |
| `ta.rsi()` | `RelativeStrengthIndex` | Native Rust |
| `ta.macd()` | `MovingAverageConvergenceDivergence` | Native Rust |
| `ta.atr()` | `AverageTrueRange` | Native Rust |
| `ta.adx()` | `AverageDirectionalIndex` | Native Rust |
| `ta.bbands()` | `BollingerBands` | Native Rust |
| `ta.stoch()` | `Stochastics` | Native Rust |
| `ta.cci()` | `CommodityChannelIndex` | Native Rust |
| `ta.obv()` | `OnBalanceVolume` | Native Rust |
| `ta.vwap()` | `VolumeWeightedAveragePrice` | Native Rust |
| `ta.supertrend()` | ⚠️ Custom needed | Not native |
| `ta.ichimoku()` | ⚠️ Custom needed | Not native |

### Strategy Functions

| Pine v5 | NautilusTrader |
|---------|----------------|
| `strategy.entry("id", direction)` | `submit_order()` |
| `strategy.close("id")` | `close_position()` |
| `strategy.exit("id", stop=, limit=)` | `submit_order()` with bracket |
| `strategy.cancel("id")` | `cancel_order()` |
| `strategy.position_size` | `portfolio.position().quantity` |
| `strategy.position_avg_price` | `portfolio.position().avg_px_open` |

## Error Handling

| Issue | Action |
|-------|--------|
| Unsupported indicator | Flag for custom implementation |
| Pine v3/v4 syntax | Attempt auto-upgrade to v5 |
| Complex logic | Add [MANUAL REVIEW] markers |
| External libraries | Document dependency |

## Examples

```bash
# Convert from URL
/pinescript https://www.tradingview.com/script/xyz/EMA-Crossover-Strategy

# Convert pasted code
/pinescript
# Then paste:
//@version=5
strategy("EMA Cross", overlay=true)
fast = ta.ema(close, 9)
slow = ta.ema(close, 21)
if ta.crossover(fast, slow)
    strategy.entry("Long", strategy.long)
if ta.crossunder(fast, slow)
    strategy.close("Long")
```
