# Quickstart: Orderflow Indicators (Spec 025)

## Installation

```bash
# Activate nightly environment
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate

# Install tick library for Hawkes processes
uv pip install tick
```

## Basic Usage

### 1. VPIN Toxicity Detection

```python
from strategies.common.orderflow import VPINIndicator, VPINConfig

# Configure VPIN
config = VPINConfig(
    bucket_size=1000.0,      # 1000 contracts per bucket
    n_buckets=50,            # Rolling average over 50 buckets
    classification_method="tick_rule"
)

# Create indicator
vpin = VPINIndicator(config)

# In strategy on_bar:
def on_bar(self, bar: Bar) -> None:
    vpin.handle_bar(bar)

    if vpin.is_valid:
        toxicity = vpin.value  # 0.0 to 1.0
        level = vpin.toxicity_level  # LOW, MEDIUM, HIGH

        if level == ToxicityLevel.HIGH:
            self.log.warning(f"High toxicity detected: {toxicity:.2f}")
```

### 2. Hawkes OFI

```python
from strategies.common.orderflow import HawkesOFI, HawkesConfig

# Configure Hawkes
config = HawkesConfig(
    decay_rate=1.0,
    lookback_ticks=10000,
    refit_interval=100
)

# Create indicator
hawkes = HawkesOFI(config)

# In strategy on_bar:
def on_bar(self, bar: Bar) -> None:
    hawkes.handle_bar(bar)

    if hawkes.is_fitted:
        ofi = hawkes.ofi  # -1.0 to 1.0

        if ofi > 0.5:
            self.log.info("Strong buy pressure")
        elif ofi < -0.5:
            self.log.info("Strong sell pressure")
```

### 3. OrderflowManager (Unified)

```python
from strategies.common.orderflow import OrderflowManager, OrderflowConfig
from strategies.common.position_sizing import GillerSizer, GillerConfig

# Configure
orderflow_config = OrderflowConfig(
    vpin=VPINConfig(bucket_size=1000),
    hawkes=HawkesConfig(decay_rate=1.0),
    enable_vpin=True,
    enable_hawkes=True
)

giller_config = GillerConfig(
    base_size=1.0,
    exponent=0.5,
    min_size=0.1,
    max_size=5.0
)

# Create managers
orderflow = OrderflowManager(orderflow_config)
sizer = GillerSizer(giller_config)

# In strategy:
def on_bar(self, bar: Bar) -> None:
    # Update orderflow indicators
    orderflow.handle_bar(bar)

    # Get signal from your strategy logic
    signal = self.calculate_signal(bar)

    # Get regime weight (from Spec 024)
    regime_weight = self.regime_manager.regime_weight

    # Calculate position size with toxicity adjustment
    position_size = sizer.calculate(
        signal=signal,
        regime_weight=regime_weight,
        toxicity=orderflow.toxicity  # VPIN-based toxicity
    )

    # Use OFI for additional confirmation
    if orderflow.ofi > 0.3 and signal > 0:
        # OFI confirms bullish signal
        self.submit_order(position_size)
```

## Integration with Existing Components

### With RegimeManager (Spec 024)

```python
from strategies.common.regime_detection import RegimeManager
from strategies.common.orderflow import OrderflowManager
from strategies.common.position_sizing import GillerSizer

class MyStrategy(Strategy):
    def __init__(self, config):
        self.regime = RegimeManager(config.regime)
        self.orderflow = OrderflowManager(config.orderflow)
        self.sizer = GillerSizer(config.sizing)

    def on_bar(self, bar: Bar) -> None:
        # Update all components
        self.regime.update(bar)
        self.orderflow.handle_bar(bar)

        # Combined decision
        if self.regime.current_regime == RegimeType.TRENDING_UP:
            if self.orderflow.ofi > 0 and self.orderflow.toxicity < 0.5:
                signal = self.calculate_signal(bar)
                size = self.sizer.calculate(
                    signal=signal,
                    regime_weight=self.regime.regime_weight,
                    toxicity=self.orderflow.toxicity
                )
                self.enter_long(size)
```

## Configuration Reference

### VPINConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bucket_size` | float | 1000.0 | Volume per bucket |
| `n_buckets` | int | 50 | Rolling window size |
| `classification_method` | str | "tick_rule" | Trade classification method |
| `min_bucket_volume` | float | 100.0 | Minimum volume per bucket |

### HawkesConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `decay_rate` | float | 1.0 | Exponential decay (β) |
| `lookback_ticks` | int | 10000 | Buffer size |
| `refit_interval` | int | 100 | Refit every N ticks |
| `use_fixed_params` | bool | False | Use fixed vs fitted params |

## Testing

```bash
# Run orderflow tests
uv run pytest tests/test_vpin.py tests/test_hawkes_ofi.py -v

# Run with coverage
uv run pytest tests/test_*.py --cov=strategies/common/orderflow
```

## Troubleshooting

### tick library installation fails

```bash
# Try conda instead
conda install -c conda-forge tick

# Or use pure Python fallback (slower)
# Set in config: use_scipy_fallback=True
```

### VPIN always returns 0

- Check that enough bars have been processed (need n_buckets worth)
- Verify bucket_size is appropriate for your volume levels
- Check classification method is working (try "close_vs_open" for bars)

### Hawkes doesn't converge

- Increase lookback_ticks
- Use fixed_params mode with sensible defaults
- Check that events are not too sparse
