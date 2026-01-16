# Data Model: ML4T Orchestrator

**Feature Branch**: `041-ml4t-orchestrator`
**Created**: 2026-01-12

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ML4TOrchestrator                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │   InferenceLoop  │  │   TrainingLoop   │  │  RetrainMonitor  │      │
│  │                  │  │                  │  │                  │      │
│  │  - model: Meta   │  │  - model_cfg     │  │  - baseline_acc  │      │
│  │  - vpin: VPIN    │  │  - label_cfg     │  │  - rolling_acc   │      │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘      │
│           │                     │                     │                │
│           ▼                     ▼                     ▼                │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                     OrchestratorConfig                        │      │
│  │  model_path | retrain_threshold | redis_enabled | features   │      │
│  └──────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘

Events Flow:
┌─────────────┐         ┌──────────────────────┐         ┌──────────────┐
│ SignalEvent │ ──────► │ InferenceLoop.process │ ──────► │EnrichedSignal│
│             │         │                       │         │   Event      │
│ instrument  │         │ 1. extract_features() │         │ meta_conf    │
│ signal      │         │ 2. model.predict()    │         │ regime_wt    │
│ bars[]      │         │ 3. get_toxicity()     │         │ toxicity     │
└─────────────┘         └───────────────────────┘         └──────────────┘

Training Flow:
┌─────────────┐         ┌──────────────────────┐         ┌──────────────┐
│  Bar Data   │ ──────► │ TrainingLoop.train()  │ ──────► │TrainingResult│
│   (list)    │         │                       │         │              │
│             │         │ 1. generate_labels()  │         │ model        │
│             │         │ 2. extract_features() │         │ accuracy     │
│             │         │ 3. walk_forward()     │         │ auc          │
└─────────────┘         └───────────────────────┘         └──────────────┘
```

## Entities

### 1. OrchestratorConfig

**Description**: Configuration for the ML4T Orchestrator

**Source**: FR-004, FR-011, FR-013, FR-016

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass(frozen=True)
class OrchestratorConfig:
    """Immutable configuration for ML4TOrchestrator.

    Attributes:
        model_path: Path to persisted meta-model (joblib format)
        default_confidence: Confidence to use when model unavailable (FR-004)
        retrain_accuracy_drop_threshold: Drop threshold to trigger retrain (FR-011)
        retrain_min_samples: Minimum samples before retrain consideration
        retrain_interval_bars: Optional bar-count based retrain trigger (FR-013)
        redis_enabled: Enable Redis MessageBus (FR-016)
        redis_channel_signals: Channel for incoming signals
        redis_channel_enriched: Channel for enriched signals
        inference_timeout_ms: Maximum inference latency (SC-001)
        feature_names: Features to extract for prediction
    """
    model_path: Path = Path("models/meta_model.joblib")
    default_confidence: float = 0.5
    retrain_accuracy_drop_threshold: float = 0.10
    retrain_min_samples: int = 1000
    retrain_interval_bars: int | None = None
    redis_enabled: bool = True
    redis_channel_signals: str = "nautilus:signals"
    redis_channel_enriched: str = "nautilus:enriched_signals"
    inference_timeout_ms: int = 10
    feature_names: list[str] = field(default_factory=lambda: [
        "volatility", "momentum", "regime", "trend_strength"
    ])

    def __post_init__(self) -> None:
        """Validate config values."""
        if not 0.0 <= self.default_confidence <= 1.0:
            raise ValueError("default_confidence must be in [0, 1]")
        if not 0.0 < self.retrain_accuracy_drop_threshold <= 0.5:
            raise ValueError("retrain_accuracy_drop_threshold must be in (0, 0.5]")
        if self.retrain_min_samples < 100:
            raise ValueError("retrain_min_samples must be >= 100")
```

**Validation Rules**:
- `default_confidence` must be in [0, 1]
- `retrain_accuracy_drop_threshold` must be in (0, 0.5]
- `retrain_min_samples` must be >= 100
- `inference_timeout_ms` must be positive

---

### 2. SignalEvent

**Description**: Incoming signal from strategy to be enriched

**Source**: US1

```python
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar

@dataclass(frozen=True)
class SignalEvent:
    """Signal event from strategy requiring meta-learning enrichment.

    Attributes:
        instrument_id: Instrument identifier (e.g., "BTC-PERP.HYPERLIQUID")
        signal: Signal direction (-1=SELL, 0=FLAT, 1=BUY)
        timestamp: Event timestamp in nanoseconds
        bars: Recent bars for feature extraction (minimum 100)
    """
    instrument_id: str
    signal: int  # -1, 0, 1
    timestamp: int  # nanoseconds
    bars: list["Bar"]

    def __post_init__(self) -> None:
        """Validate event data."""
        if self.signal not in (-1, 0, 1):
            raise ValueError(f"signal must be -1, 0, or 1, got {self.signal}")
        if len(self.bars) < 100:
            raise ValueError(f"Minimum 100 bars required, got {len(self.bars)}")
```

**Validation Rules**:
- `signal` must be -1, 0, or 1
- `bars` must have at least 100 elements

---

### 3. EnrichedSignalEvent

**Description**: Signal enriched with meta-learning outputs for RiskStage

**Source**: US1, FR-003

```python
@dataclass(frozen=True)
class EnrichedSignalEvent:
    """Signal event enriched with meta-learning outputs.

    Attributes:
        signal_event: Original signal event
        meta_confidence: Model's confidence in signal correctness [0, 1]
        regime_weight: Weight adjustment based on market regime [0, 1]
        toxicity: VPIN toxicity level [0, 1]
        latency_ns: Processing latency in nanoseconds
    """
    signal_event: SignalEvent
    meta_confidence: float
    regime_weight: float
    toxicity: float
    latency_ns: int

    def to_meta_output(self) -> dict:
        """Convert to alpha_output.meta_output format for RiskStage."""
        return {
            "confidence": self.meta_confidence,
            "regime_weight": self.regime_weight,
            "toxicity": self.toxicity,
        }
```

**State Transitions**: None (immutable event)

---

### 4. TrainingResult

**Description**: Output of training loop containing model and metrics

**Source**: US2, FR-007, FR-009

```python
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategies.common.meta_learning.meta_model import MetaModel

@dataclass(frozen=True)
class TrainingResult:
    """Result of meta-model training.

    Attributes:
        model: Trained MetaModel instance
        accuracy: Walk-forward out-of-sample accuracy
        auc: Area under ROC curve
        feature_importance: Dict of feature name to importance score
        n_samples: Number of samples used in training
        n_folds: Number of walk-forward folds
    """
    model: "MetaModel"
    accuracy: float
    auc: float
    feature_importance: dict[str, float]
    n_samples: int
    n_folds: int

    def meets_minimum_accuracy(self, threshold: float = 0.55) -> bool:
        """Check if accuracy meets SC-003 threshold."""
        return self.accuracy >= threshold
```

**Validation Rules**:
- `accuracy` must be in [0, 1]
- `auc` must be in [0, 1]

---

### 5. RetrainTrigger

**Description**: Event indicating retrain should occur

**Source**: US3, FR-010, FR-011

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class RetrainReason(Enum):
    """Reason for triggering retrain."""
    ACCURACY_DEGRADATION = "accuracy_degradation"
    SAMPLE_COUNT = "sample_count"
    TIME_INTERVAL = "time_interval"
    MANUAL = "manual"

@dataclass(frozen=True)
class RetrainTrigger:
    """Event indicating retrain should be triggered.

    Attributes:
        reason: Why retrain was triggered
        baseline_accuracy: Accuracy at model deployment
        current_accuracy: Current rolling accuracy
        accuracy_drop: Difference (baseline - current)
        timestamp: When trigger was detected
        priority: Urgency level (1=high, 3=low)
    """
    reason: RetrainReason
    baseline_accuracy: float
    current_accuracy: float
    accuracy_drop: float
    timestamp: datetime
    priority: int = 2  # 1=high, 2=medium, 3=low

    def should_interrupt_inference(self) -> bool:
        """Check if retrain should interrupt live inference."""
        return False  # Never interrupt per FR-012
```

**State Transitions**:
- Created → Queued → Processing → Completed/Failed

---

### 6. InferenceResult

**Description**: Result of single inference operation

**Source**: FR-001, FR-002, SC-001

```python
@dataclass(frozen=True)
class InferenceResult:
    """Result of inference operation with timing metadata.

    Attributes:
        meta_confidence: Model's confidence in signal [0, 1]
        regime_weight: Regime-based weight adjustment [0, 1]
        toxicity: VPIN toxicity level [0, 1]
        feature_extraction_ns: Time spent extracting features
        prediction_ns: Time spent in model.predict()
        total_latency_ns: Total end-to-end latency
        model_available: Whether model was loaded
    """
    meta_confidence: float
    regime_weight: float
    toxicity: float
    feature_extraction_ns: int
    prediction_ns: int
    total_latency_ns: int
    model_available: bool

    def exceeds_latency_budget(self, budget_ms: int = 10) -> bool:
        """Check if inference exceeded latency budget (SC-001)."""
        return self.total_latency_ns > budget_ms * 1_000_000
```

---

## Entity Relationships

```
OrchestratorConfig
    │
    ├──► InferenceLoop (1:1)
    │       │
    │       └──► processes SignalEvent
    │              │
    │              └──► produces EnrichedSignalEvent
    │
    ├──► TrainingLoop (1:1)
    │       │
    │       └──► produces TrainingResult
    │
    └──► RetrainMonitor (1:1)
            │
            └──► produces RetrainTrigger
```

## Integration with RiskStage

The `EnrichedSignalEvent.to_meta_output()` method produces a dict compatible with `RiskStage._calculate_positions()`:

```python
# In pipeline/stages/risk.py
meta_output = alpha_output.get("meta_output", {})
meta_confidence = meta_output.get("confidence", None)
regime_weight = meta_output.get("regime_weight", None)
toxicity = meta_output.get("toxicity", None)

# Passed to IntegratedSizer.calculate()
result = sizer.calculate(
    signal=signal_value,
    meta_confidence=meta_confidence,
    regime_weight=regime_weight,
    toxicity=toxicity,
)
```

## Persistence

| Entity | Storage | Format | Location |
|--------|---------|--------|----------|
| MetaModel | File | joblib | `models/meta_model.joblib` |
| OrchestratorConfig | Memory/File | Python dataclass | Constructor/YAML |
| TrainingResult | Memory | Python dataclass | In-memory only |
| RetrainTrigger | Memory | Python dataclass | In-memory queue |
