# Pipeline Profiles

Profile-based pipeline configuration that integrates ML features from `strategies/common/`.

## Overview

The pipeline supports three complexity levels:

| Profile | Features | Use Case |
|---------|----------|----------|
| **BASIC** | DATA → ALPHA → RISK → EXECUTION → MONITORING | Rule-based strategies |
| **ML_LITE** | + Regime Detection + Giller Sizing | Hybrid strategies (80/20 benefit) |
| **ML_FULL** | + Walk-Forward + Triple Barrier + Meta-Labeling | ML-based strategies |

## Quick Start

```python
from pipeline.profiles import PipelineProfile, create_pipeline

# Simple: use preset
pipeline = create_pipeline(PipelineProfile.ML_LITE)

# Custom: modify configuration
from pipeline.profiles.config import ProfileConfig

config = ProfileConfig(profile=PipelineProfile.ML_FULL)
config.regime.hmm_n_regimes = 4  # Override defaults
config.walk_forward.train_window = 504  # 2 years

pipeline = create_pipeline(config)
```

## Profiles

### BASIC

Standard orchestration pipeline for rule-based strategies.

```python
pipeline = create_pipeline(PipelineProfile.BASIC)
```

**Features:**
- Linear position sizing
- No ML features
- Minimal complexity

**Use for:** Simple momentum, mean-reversion, any rule-based logic.

### ML_LITE

Enhanced pipeline with regime awareness and sub-linear sizing.

```python
pipeline = create_pipeline(PipelineProfile.ML_LITE)
```

**Features (in addition to BASIC):**
- **HMM Regime Detection**: Identifies trending/ranging/volatile markets
- **GMM Volatility Clustering**: Low/medium/high volatility classification
- **Giller Sub-linear Sizing**: `position = signal^0.5` prevents over-betting
- **Regime-weighted positions**: Reduces exposure in unfavorable regimes

**Use for:** Rule-based strategies that benefit from regime awareness, hybrid strategies.

**Reference:** `strategies/common/regime_detection/`

### ML_FULL

Full ML pipeline following Lopez de Prado / Jansen patterns.

```python
pipeline = create_pipeline(PipelineProfile.ML_FULL)
```

**Features (in addition to ML_LITE):**
- **Walk-Forward Validation**: Prevents overfitting with proper train/test splits
- **Triple Barrier Labeling**: AFML-style TP/SL/time barriers
- **Meta-Labeling**: Bet sizing based on model confidence
- **Embargo/Purging**: Proper validation gap between train and test

**Use for:** ML-based strategies, research, when rigorous validation is required.

**References:**
- Lopez de Prado: "Advances in Financial Machine Learning"
- Jansen: "Machine Learning for Algorithmic Trading"
- `strategies/common/meta_learning/`
- `strategies/common/labeling/`

## Configuration

### From YAML

```python
from pipeline.profiles.config import ProfileConfig

config = ProfileConfig.from_yaml(Path("pipeline/profiles/presets/ml_full.yaml"))
pipeline = create_pipeline(config)
```

### Save to YAML

```python
config = ProfileConfig(profile=PipelineProfile.ML_LITE)
config.regime.lookback_bars = 504
config.to_yaml(Path("my_config.yaml"))
```

### Configuration Sections

```yaml
profile: ML_FULL

regime:
  enabled: true
  hmm_n_regimes: 3         # Number of HMM states
  gmm_n_clusters: 3        # Number of volatility clusters
  lookback_bars: 252       # ~1 year for estimation
  refit_interval: 20       # Refit every N bars

sizing:
  method: integrated       # linear, giller, integrated
  giller_exponent: 0.5     # Sub-linear exponent
  max_position_pct: 10.0   # Max position size
  regime_weight_enabled: true

walk_forward:
  enabled: true
  train_window: 252        # Training period
  test_window: 63          # Test period
  step_size: 21            # Step between windows
  embargo_size: 5          # Gap to prevent leakage
  min_windows: 4           # Minimum windows required

triple_barrier:
  enabled: true
  take_profit_atr: 2.0     # TP at N x ATR
  stop_loss_atr: 2.0       # SL at N x ATR
  max_holding_bars: 20     # Max holding period
  atr_period: 14           # ATR calculation period

meta_label:
  enabled: true
  model_type: random_forest  # random_forest, xgboost, lightgbm
  min_confidence: 0.5        # Skip below threshold
  retrain_interval: 100      # Retrain every N bars

custom:
  # Profile-specific parameters
  min_sharpe_per_window: 0.5
```

## Feature Integration

The profiles integrate with existing ML modules in `strategies/common/`:

| Feature | Module | Profile |
|---------|--------|---------|
| HMM Regime | `regime_detection/hmm_filter.py` | ML_LITE+ |
| GMM Clustering | `regime_detection/gmm_clustering.py` | ML_LITE+ |
| BOCD | `regime_detection/bocd.py` | ML_LITE+ |
| Giller Sizing | `position_sizing/giller_sizing.py` | ML_LITE+ |
| Walk-Forward | `meta_learning/walk_forward.py` | ML_FULL |
| Triple Barrier | `labeling/triple_barrier.py` | ML_FULL |
| Meta-Model | `meta_learning/meta_model.py` | ML_FULL |

## Preset Files

- `presets/basic.yaml` - BASIC profile defaults
- `presets/ml_lite.yaml` - ML_LITE profile defaults
- `presets/ml_full.yaml` - ML_FULL profile defaults

## Architecture

```
pipeline/profiles/
├── __init__.py          # Public API
├── config.py            # ProfileConfig, dataclasses
├── factory.py           # create_pipeline, ProfiledStages
├── presets/
│   ├── basic.yaml
│   ├── ml_lite.yaml
│   └── ml_full.yaml
└── README.md            # This file
```

### Stage Factory

The `create_pipeline` function creates profile-appropriate stages:

```python
def create_stages(config: ProfileConfig) -> list[AbstractStage]:
    stages = [DataStage()]

    if config.profile >= PipelineProfile.ML_LITE:
        stages.append(ProfiledAlphaStage(config))  # With ML features
        stages.append(ProfiledRiskStage(config))   # With Giller sizing
    else:
        stages.append(AlphaStage())
        stages.append(RiskStage())

    stages.extend([ExecutionStage(), MonitoringStage()])
    return stages
```

### ProfiledAlphaStage

Conditionally enables ML features:

```python
class ProfiledAlphaStage(AlphaStage):
    def _init_ml_features(self):
        if config.regime.enabled:
            self._regime_manager = RegimeManager(...)
        if config.walk_forward.enabled:
            self._walk_forward = WalkForwardSplitter(...)
        if config.triple_barrier.enabled:
            self._triple_barrier = TripleBarrierLabeler(...)
        if config.meta_label.enabled:
            self._meta_model = MetaModel(...)
```

## Best Practices

1. **Start with BASIC**: Validate your strategy logic first
2. **Graduate to ML_LITE**: Add regime awareness once BASIC works
3. **Use ML_FULL for research**: Rigorous validation before production
4. **Production**: ML_LITE is often sufficient (80/20 rule)

## Requirements

For ML_LITE+:
- `strategies/common/regime_detection/` modules
- `strategies/common/position_sizing/` modules

For ML_FULL:
- `strategies/common/meta_learning/` modules
- `strategies/common/labeling/` modules
- Sufficient historical data (2+ years recommended)
