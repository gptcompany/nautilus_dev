# Quickstart: Orderflow Indicators (Spec 025)

## Installation

```bash
# Activate nightly environment
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
```

## Module Structure

```
strategies/common/orderflow/
├── __init__.py           # Public exports
├── config.py             # VPINConfig, HawkesConfig, OrderflowConfig
├── trade_classifier.py   # TickRule, BVC, CloseVsOpen classifiers
├── vpin.py               # VPINIndicator, ToxicityLevel
├── hawkes_ofi.py         # HawkesOFI indicator
└── orderflow_manager.py  # Unified OrderflowManager
```

---

## 1. VPIN Toxicity Detection

VPIN (Volume-Synchronized Probability of Informed Trading) measures market toxicity by analyzing order flow imbalance across volume buckets.

### Basic Usage

```python
from strategies.common.orderflow import (
    VPINConfig,
    VPINIndicator,
    ToxicityLevel,
)

# Configure VPIN
config = VPINConfig(
    bucket_size=1000.0,           # Volume per bucket (contracts)
    n_buckets=50,                 # Rolling window size
    classification_method="tick_rule",  # or "bvc", "close_vs_open"
)

# Create indicator
vpin = VPINIndicator(config)

# In strategy on_bar:
def on_bar(self, bar: Bar) -> None:
    vpin.handle_bar(bar)

    if vpin.is_valid:  # True when n_buckets filled
        toxicity = vpin.value         # float in [0.0, 1.0]
        level = vpin.toxicity_level   # ToxicityLevel enum

        if level == ToxicityLevel.HIGH:
            self.log.warning(f"High toxicity: {toxicity:.3f}")
```

### Toxicity Levels

| Level | VPIN Range | Interpretation |
|-------|------------|----------------|
| `LOW` | < 0.3 | Safe to trade |
| `MEDIUM` | 0.3 - 0.7 | Trade with caution |
| `HIGH` | >= 0.7 | Reduce position or avoid |

### Getting Full Result

```python
result = vpin.get_result()
# VPINResult(
#     value=0.45,
#     toxicity=ToxicityLevel.MEDIUM,
#     bucket_count=52,
#     last_bucket_oi=0.38,  # Order imbalance of last bucket
#     is_valid=True
# )
```

---

## 2. Hawkes OFI (Order Flow Imbalance)

Hawkes processes model self-exciting point processes where past events increase future event probability. This captures order flow clustering.

### Basic Usage

```python
from strategies.common.orderflow import HawkesConfig, HawkesOFI

# Configure Hawkes
config = HawkesConfig(
    decay_rate=1.0,        # Exponential decay (beta)
    lookback_ticks=10000,  # Buffer size
    refit_interval=100,    # Refit every N ticks
    fixed_baseline=0.1,    # Baseline intensity (mu)
    fixed_excitation=0.5,  # Excitation (alpha < decay_rate)
)

# Create indicator
hawkes = HawkesOFI(config)

# In strategy on_bar:
def on_bar(self, bar: Bar) -> None:
    hawkes.handle_bar(bar)

    if hawkes.is_fitted:
        ofi = hawkes.ofi  # float in [-1.0, 1.0]

        if ofi > 0.5:
            self.log.info(f"Strong buy pressure: {ofi:.3f}")
        elif ofi < -0.5:
            self.log.info(f"Strong sell pressure: {ofi:.3f}")
```

### OFI Interpretation

| OFI Value | Interpretation |
|-----------|----------------|
| > 0.5 | Strong buy pressure |
| 0.0 to 0.5 | Moderate buy pressure |
| -0.5 to 0.0 | Moderate sell pressure |
| < -0.5 | Strong sell pressure |

### Getting Full Result

```python
result = hawkes.get_result()
# HawkesResult(
#     ofi=0.32,
#     buy_intensity=1.45,
#     sell_intensity=0.82,
#     branching_ratio=0.5,  # alpha/beta (must be < 1)
#     is_fitted=True
# )
```

---

## 3. OrderflowManager (Unified Interface)

Combines VPIN and Hawkes for comprehensive orderflow analysis.

### Basic Usage

```python
from strategies.common.orderflow import (
    OrderflowConfig,
    OrderflowManager,
    VPINConfig,
    HawkesConfig,
    ToxicityLevel,
)

# Configure both indicators
config = OrderflowConfig(
    vpin=VPINConfig(bucket_size=1000, n_buckets=50),
    hawkes=HawkesConfig(decay_rate=1.0),
    enable_vpin=True,
    enable_hawkes=True,
)

# Create manager
orderflow = OrderflowManager(config)

# In strategy on_bar:
def on_bar(self, bar: Bar) -> None:
    orderflow.handle_bar(bar)

    if orderflow.is_valid:
        # Access both indicators via unified interface
        vpin = orderflow.vpin_value       # float [0.0, 1.0]
        toxicity = orderflow.toxicity     # ToxicityLevel enum
        ofi = orderflow.ofi               # float [-1.0, 1.0]

        # Example: Combine signals for position sizing
        if toxicity == ToxicityLevel.HIGH:
            position_scale = 0.5  # Reduce size in toxic conditions
        else:
            position_scale = 1.0

        if ofi > 0.3:
            self.log.info("OFI confirms bullish bias")
```

### Getting Full Result

```python
result = orderflow.get_result()
# OrderflowResult(
#     vpin_value=0.45,
#     toxicity=ToxicityLevel.MEDIUM,
#     ofi=0.32,
#     is_valid=True,
#     buy_intensity=1.45,
#     sell_intensity=0.82
# )
```

### Selective Enabling

```python
# VPIN only
config = OrderflowConfig(enable_vpin=True, enable_hawkes=False)

# Hawkes only
config = OrderflowConfig(enable_vpin=False, enable_hawkes=True)
```

---

## 4. Trade Classification

Three methods for classifying trades as BUY or SELL.

### TickRuleClassifier

Uses price movement direction. Best for tick data.

```python
from strategies.common.orderflow import (
    TickRuleClassifier,
    TradeSide,
    create_classifier,
)

# Create via factory
classifier = create_classifier("tick_rule")

# Or directly
classifier = TickRuleClassifier()

# Classify trades
result = classifier.classify(
    price=100.50,
    volume=10.0,
    timestamp_ns=1704067200_000_000_000,
    prev_price=100.45,  # Optional - uses internal state if None
)

print(result.side)        # TradeSide.BUY (price went up)
print(result.confidence)  # 1.0 (tick rule is binary)
print(result.method)      # "tick_rule"
```

### BVCClassifier (Bulk Volume Classification)

Uses close position in high-low range. Best for bar data.

```python
from strategies.common.orderflow import BVCClassifier

classifier = BVCClassifier()

result = classifier.classify(
    price=100.80,        # Close price
    volume=1000.0,
    timestamp_ns=1704067200_000_000_000,
    high=101.00,         # Bar high
    low=100.00,          # Bar low
)

# buy_ratio = (100.80 - 100.00) / (101.00 - 100.00) = 0.80
print(result.side)        # TradeSide.BUY (close near high)
print(result.confidence)  # 0.60 (abs(0.5 - 0.80) * 2)
```

### CloseVsOpenClassifier

Simple open/close comparison. Useful for bar data.

```python
from strategies.common.orderflow import CloseVsOpenClassifier

classifier = CloseVsOpenClassifier()

result = classifier.classify(
    price=100.80,        # Close price
    volume=1000.0,
    timestamp_ns=1704067200_000_000_000,
    open_price=100.50,   # Open price
)

print(result.side)        # TradeSide.BUY (close > open)
print(result.confidence)  # 1.0
```

### TradeSide Enum

```python
from strategies.common.orderflow import TradeSide

TradeSide.BUY      # Buyer-initiated (value: 1)
TradeSide.SELL     # Seller-initiated (value: -1)
TradeSide.UNKNOWN  # Cannot determine (value: 0)
```

---

## 5. Strategy Integration Example

Complete example integrating orderflow with a NautilusTrader strategy:

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import Bar

from strategies.common.orderflow import (
    OrderflowConfig,
    OrderflowManager,
    VPINConfig,
    HawkesConfig,
    ToxicityLevel,
)


class OrderflowStrategy(Strategy):
    """Strategy using VPIN and Hawkes OFI for trade filtering."""

    def __init__(self, config):
        super().__init__(config)

        # Initialize orderflow manager
        orderflow_config = OrderflowConfig(
            vpin=VPINConfig(
                bucket_size=1000.0,
                n_buckets=50,
                classification_method="bvc",  # BVC for bars
            ),
            hawkes=HawkesConfig(
                decay_rate=1.0,
                lookback_ticks=10000,
            ),
            enable_vpin=True,
            enable_hawkes=True,
        )
        self.orderflow = OrderflowManager(orderflow_config)

    def on_bar(self, bar: Bar) -> None:
        # Update orderflow indicators
        self.orderflow.handle_bar(bar)

        # Wait for valid readings
        if not self.orderflow.is_valid:
            return

        # Get orderflow signals
        toxicity = self.orderflow.toxicity
        ofi = self.orderflow.ofi

        # Example: Only trade in low toxicity with OFI confirmation
        if toxicity == ToxicityLevel.LOW:
            if ofi > 0.3:
                self._enter_long(bar)
            elif ofi < -0.3:
                self._enter_short(bar)
        elif toxicity == ToxicityLevel.HIGH:
            self.log.warning(
                f"High toxicity ({self.orderflow.vpin_value:.3f}), "
                "avoiding new positions"
            )

    def _enter_long(self, bar: Bar) -> None:
        # Position entry logic
        pass

    def _enter_short(self, bar: Bar) -> None:
        # Position entry logic
        pass

    def on_reset(self) -> None:
        self.orderflow.reset()
```

---

## Configuration Reference

### VPINConfig

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `bucket_size` | float | 1000.0 | > 0 | Volume per bucket |
| `n_buckets` | int | 50 | 10-200 | Rolling window size |
| `classification_method` | str | "tick_rule" | tick_rule, bvc, close_vs_open | Trade classifier |
| `min_bucket_volume` | float | 100.0 | >= 0 | Min volume per bucket |

### HawkesConfig

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `decay_rate` | float | 1.0 | > 0 | Exponential decay (beta) |
| `lookback_ticks` | int | 10000 | 100-100000 | Buffer size |
| `refit_interval` | int | 100 | >= 10 | Refit every N ticks |
| `use_fixed_params` | bool | False | - | Use fixed vs fitted params |
| `fixed_baseline` | float | 0.1 | >= 0 | Baseline intensity (mu) |
| `fixed_excitation` | float | 0.5 | < decay_rate | Excitation (alpha) |

### OrderflowConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vpin` | VPINConfig | VPINConfig() | VPIN configuration |
| `hawkes` | HawkesConfig | HawkesConfig() | Hawkes configuration |
| `enable_vpin` | bool | True | Enable VPIN |
| `enable_hawkes` | bool | True | Enable Hawkes OFI |

---

## Testing

```bash
# Run all orderflow tests
uv run pytest tests/test_orderflow/ -v

# Run specific tests
uv run pytest tests/test_orderflow/test_vpin.py -v
uv run pytest tests/test_orderflow/test_hawkes_ofi.py -v
uv run pytest tests/test_orderflow/test_trade_classifier.py -v

# With coverage
uv run pytest tests/test_orderflow/ --cov=strategies/common/orderflow
```

---

## Troubleshooting

### VPIN always returns 0.0

- **Cause**: Not enough buckets accumulated
- **Fix**: Wait for `vpin.is_valid` to be True (requires n_buckets completed)
- **Check**: `vpin.get_result().bucket_count` to see progress

### Hawkes OFI returns 0.0

- **Cause**: Model not yet fitted
- **Fix**: Wait for `hawkes.is_fitted` to be True
- **Check**: Ensure `refit_interval` ticks have been processed

### Classification returns UNKNOWN

- **TickRule**: First trade has no previous price reference
- **BVC**: Missing high/low values, or high == low
- **CloseVsOpen**: Missing open_price

### Hawkes branching ratio error

- **Cause**: `fixed_excitation >= decay_rate`
- **Fix**: Ensure `alpha < beta` for stationarity (e.g., excitation=0.5, decay=1.0)
