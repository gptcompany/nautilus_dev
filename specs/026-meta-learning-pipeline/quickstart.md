# Quickstart: Meta-Learning Pipeline (Spec 026)

**Date**: 2026-01-03
**Prerequisites**: Spec 024 (ML Regime Foundation), Spec 025 (Orderflow Indicators)

## Installation

```bash
# Activate nightly environment
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate

# Verify dependencies (already installed in nightly)
python -c "import numpy, scipy, sklearn; print('Dependencies OK')"
```

## Quick Examples

### 1. Triple Barrier Labeling

```python
from strategies.common.labeling import TripleBarrierLabeler, TripleBarrierConfig
import numpy as np

# Configure labeler
config = TripleBarrierConfig(
    pt_multiplier=2.0,    # Take profit = 2 * ATR
    sl_multiplier=1.0,    # Stop loss = 1 * ATR
    max_holding_bars=10,  # Maximum 10 bars holding
    atr_period=14,
)
labeler = TripleBarrierLabeler(config)

# Generate labels
prices = np.array([100, 101, 102, 101, 103, 105, 104, 106, 107, 108])
atr_values = np.full(len(prices), 2.0)  # Constant ATR for example
signals = np.array([0, 1, 0, 0, 1, 0, 0, -1, 0, 0])  # Entry signals

labels = labeler.apply(prices, atr_values, signals)
# labels: array([0, 1, 0, 0, 1, 0, 0, -1, 0, 0])
# +1 = take profit hit, -1 = stop loss hit, 0 = no signal or timeout
```

### 2. Meta-Model Training

```python
from strategies.common.meta_learning import MetaModel, MetaModelConfig
import numpy as np

# Configure meta-model
config = MetaModelConfig(
    n_estimators=100,
    max_depth=5,
    window_size=252,
)
meta_model = MetaModel(config)

# Prepare training data
n_samples = 500
n_features = 10
features = np.random.randn(n_samples, n_features)  # Your meta-features
primary_signals = np.random.choice([-1, 1], n_samples)  # Primary model output
true_labels = np.random.choice([-1, 0, 1], n_samples)  # From triple barrier

# Train meta-model
meta_model.fit(features, primary_signals, true_labels)

# Predict confidence
new_features = np.random.randn(10, n_features)
confidence = meta_model.predict_proba(new_features)
# confidence: array([0.65, 0.42, 0.78, ...]) - P(primary correct)
```

### 3. BOCD Regime Change Detection

```python
from strategies.common.regime_detection import BOCD, BOCDConfig
import numpy as np

# Configure BOCD
config = BOCDConfig(
    hazard_rate=1/250,  # Expect ~1 regime change per 250 bars
)
bocd = BOCD(config)

# Simulate returns stream
returns = np.concatenate([
    np.random.normal(0.001, 0.01, 100),   # Regime 1: Low vol
    np.random.normal(-0.002, 0.03, 100),  # Regime 2: High vol
    np.random.normal(0.001, 0.01, 100),   # Regime 3: Low vol again
])

# Process returns and detect changepoints
for i, ret in enumerate(returns):
    bocd.update(ret)

    if bocd.is_changepoint(threshold=0.8):
        print(f"Changepoint detected at bar {i}, P={bocd.get_changepoint_probability():.3f}")
        # Trigger model refitting here

# Output:
# Changepoint detected at bar 102, P=0.85
# Changepoint detected at bar 198, P=0.82
```

### 4. Integrated Position Sizing

```python
from strategies.common.position_sizing import IntegratedSizer, IntegratedSizingConfig

# Configure sizer
config = IntegratedSizingConfig(
    giller_exponent=0.5,      # Sub-linear scaling
    fractional_kelly=0.5,     # Half-Kelly
    min_size=0.01,
    max_size=1.0,
)
sizer = IntegratedSizer(config)

# Calculate position size with all factors
result = sizer.calculate(
    signal=0.8,               # Strong long signal
    meta_confidence=0.75,     # High meta-model confidence
    regime_weight=1.0,        # Neutral regime
    toxicity=0.2,             # Low VPIN toxicity
)

print(f"Final size: {result.final_size:.4f}")
print(f"Direction: {result.direction}")
print(f"Factor breakdown: {result.factors}")

# Output:
# Final size: 0.2683
# Direction: 1
# Factor breakdown: {
#     'signal': 0.8944,
#     'meta_confidence': 0.75,
#     'regime_weight': 1.0,
#     'toxicity_penalty': 0.8,
#     'kelly_fraction': 0.5
# }
```

## Full Pipeline Example

```python
"""Complete meta-learning pipeline with NautilusTrader."""

from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.indicators.atr import AverageTrueRange
import numpy as np

from strategies.common.labeling import TripleBarrierLabeler, TripleBarrierConfig
from strategies.common.meta_learning import MetaModel, MetaModelConfig
from strategies.common.regime_detection import BOCD, BOCDConfig, HMMRegimeFilter
from strategies.common.position_sizing import IntegratedSizer, IntegratedSizingConfig
from strategies.common.orderflow import VPINIndicator, VPINConfig


class MetaLearningStrategy(Strategy):
    """Strategy using full meta-learning pipeline."""

    def __init__(self, config):
        super().__init__(config)

        # Native Rust indicators
        self.ema_fast = ExponentialMovingAverage(period=20)
        self.ema_slow = ExponentialMovingAverage(period=50)
        self.atr = AverageTrueRange(period=14)

        # ML components
        self.hmm = HMMRegimeFilter(n_states=3)
        self.bocd = BOCD(BOCDConfig(hazard_rate=1/250))
        self.vpin = VPINIndicator(VPINConfig())
        self.meta_model = MetaModel(MetaModelConfig())
        self.sizer = IntegratedSizer(IntegratedSizingConfig())

        # State
        self._warmup_complete = False
        self._bars_since_refit = 0

    def on_start(self):
        """Initialize and warm up models."""
        # Request historical data
        self.request_bars(
            bar_type=self.bar_type,
            start=self.clock.utc_now() - timedelta(days=365),
            callback=self._on_historical_bars,
        )

    def _on_historical_bars(self, bars):
        """Train models on historical data."""
        # Extract features
        returns = self._calculate_returns(bars)
        volatility = self._calculate_volatility(bars)

        # Fit HMM regime filter
        self.hmm.fit(returns, volatility)

        # Generate triple barrier labels
        labeler = TripleBarrierLabeler(TripleBarrierConfig())
        prices = np.array([bar.close for bar in bars])
        atr_values = np.array([self._calculate_atr(bars, i) for i in range(len(bars))])
        primary_signals = self._generate_primary_signals(bars)
        labels = labeler.apply(prices, atr_values, primary_signals)

        # Train meta-model
        features = self._extract_meta_features(bars)
        self.meta_model.fit(features, primary_signals, labels)

        self._warmup_complete = True

    def on_bar(self, bar):
        """Process new bar with full pipeline."""
        # Update native indicators
        self.ema_fast.handle_bar(bar)
        self.ema_slow.handle_bar(bar)
        self.atr.handle_bar(bar)

        if not self._warmup_complete or not self.ema_fast.initialized:
            return

        # Calculate returns
        returns = self._calculate_current_returns(bar)

        # Update BOCD and check for regime change
        self.bocd.update(returns)
        if self.bocd.is_changepoint(threshold=0.8):
            self._trigger_refit()

        # Update VPIN
        self.vpin.handle_bar(bar)
        toxicity = self.vpin.value

        # Get regime weight from HMM
        volatility = self._calculate_current_volatility(bar)
        regime = self.hmm.predict(returns, volatility)
        regime_weight = self._regime_to_weight(regime)

        # Generate primary signal
        signal = self._generate_signal(bar)

        if signal == 0:
            return  # No trade

        # Get meta-model confidence
        features = self._extract_current_features(bar)
        meta_confidence = self.meta_model.predict_proba(features.reshape(1, -1))[0]

        # Calculate position size
        result = self.sizer.calculate(
            signal=signal,
            meta_confidence=meta_confidence,
            regime_weight=regime_weight,
            toxicity=toxicity,
        )

        # Submit order
        if abs(result.final_size) > 0.01:
            self._submit_order(result.direction, result.final_size)

    def _generate_signal(self, bar) -> float:
        """Generate primary trading signal."""
        if self.ema_fast.value > self.ema_slow.value:
            return 1.0  # Long signal
        elif self.ema_fast.value < self.ema_slow.value:
            return -1.0  # Short signal
        return 0.0

    def _regime_to_weight(self, regime) -> float:
        """Convert regime to position weight."""
        weights = {
            0: 1.2,   # Low vol - increase size
            1: 0.8,   # Medium vol - reduce slightly
            2: 0.4,   # High vol - reduce significantly
        }
        return weights.get(regime.state_idx, 0.8)

    def _trigger_refit(self):
        """Refit models on regime change."""
        # Implementation depends on data availability
        self._bars_since_refit = 0
```

## Common Patterns

### Pattern 1: Skip Low-Confidence Signals

```python
result = sizer.calculate(signal, meta_confidence, regime_weight, toxicity)

if result.meta_contribution < 0.3:
    # Low confidence - skip this trade
    continue
```

### Pattern 2: Regime-Conditional Trading

```python
if bocd.is_changepoint(threshold=0.8):
    # New regime detected
    # 1. Reduce current positions
    reduce_positions(factor=0.5)
    # 2. Pause new entries for confirmation
    pause_entries(bars=5)
    # 3. Refit models
    refit_models()
```

### Pattern 3: Toxicity Filter

```python
if vpin.toxicity_level == ToxicityLevel.HIGH:
    # High toxicity - avoid trading
    return None
elif vpin.toxicity_level == ToxicityLevel.MEDIUM:
    # Medium toxicity - reduce size
    result = sizer.calculate(signal, meta_confidence, regime_weight, toxicity=0.5)
else:
    # Low toxicity - normal sizing
    result = sizer.calculate(signal, meta_confidence, regime_weight, toxicity=0.0)
```

## Performance Tips

1. **Batch labeling**: Generate all triple barrier labels in one call (vectorized)
2. **Cache meta-model**: Don't retrain on every bar, use walk-forward with step size
3. **BOCD warm-up**: Let BOCD accumulate 50+ observations before acting on changepoints
4. **Feature caching**: Pre-compute features where possible to reduce inference latency

## Troubleshooting

### Meta-model returns 0.5 for all predictions

**Cause**: Insufficient training data or class imbalance
**Solution**:
- Ensure at least 252 training samples
- Check class balance: `np.bincount(meta_labels)`
- Consider oversampling minority class

### BOCD detects too many changepoints

**Cause**: Hazard rate too high or threshold too low
**Solution**:
- Reduce hazard rate: `hazard_rate = 1/500`
- Increase threshold: `is_changepoint(threshold=0.9)`

### Integrated size is always near zero

**Cause**: One factor is dominating with low value
**Solution**:
- Check individual contributions: `result.factors`
- Use default values for missing factors
- Verify meta-confidence is not always low

## Next Steps

1. Run tests: `uv run pytest tests/test_triple_barrier.py tests/test_meta_model.py tests/test_meta_walk_forward.py tests/test_bocd.py tests/test_integrated_sizing.py -v`
2. Backtest with historical data
3. Tune hyperparameters (walk-forward validation)
4. Monitor performance metrics (AUC, Sharpe, drawdown)
