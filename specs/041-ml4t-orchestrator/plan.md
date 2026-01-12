# Implementation Plan: ML4T Orchestrator

**Feature Branch**: `041-ml4t-orchestrator`
**Created**: 2026-01-12
**Status**: Draft
**Spec Reference**: `specs/041-ml4t-orchestrator/spec.md`

## Architecture Overview

The ML4TOrchestrator is a coordination layer that connects existing tested modules into training/inference/retrain loops. It acts as glue code, not new ML logic.

### System Context

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                      ML4TOrchestrator                       │
                    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
 SignalEvent ──────►│  │ InferenceLoop│  │TrainingLoop │  │ RetrainMonitor     │  │
 (Redis/Direct)     │  │             │  │             │  │                     │  │
                    │  │ extract()   │  │ train()     │  │ check_accuracy()    │  │
                    │  │ predict()   │  │ validate()  │  │ trigger_retrain()   │  │
                    │  │ enrich()    │  │ persist()   │  │                     │  │
                    │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
                    │         │                │                    │             │
                    │         ▼                ▼                    ▼             │
                    │  ┌──────────────────────────────────────────────────────┐   │
                    │  │                  Existing Blocks                      │   │
                    │  │  MetaModel | FeatureEngineering | VPIN | IntegratedSizer │
                    │  └──────────────────────────────────────────────────────┘   │
                    └─────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
                              EnrichedSignalEvent / alpha_output.meta_output
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │    RiskStage.execute()  │
                              │  (IntegratedSizer call) │
                              └─────────────────────────┘
```

### Component Diagram

```
pipeline/
├── orchestrator/                 # NEW - ML4T Orchestrator
│   ├── __init__.py
│   ├── orchestrator.py          # ML4TOrchestrator main class
│   ├── config.py                # OrchestratorConfig dataclass
│   ├── inference.py             # InferenceLoop - real-time prediction
│   ├── training.py              # TrainingLoop - batch training
│   ├── retrain.py               # RetrainMonitor - accuracy monitoring
│   ├── persistence.py           # Model save/load utilities
│   └── events.py                # SignalEvent, EnrichedSignalEvent
│
strategies/common/               # EXISTING - Already tested
├── meta_learning/
│   ├── meta_model.py           # MetaModel.fit(), predict_proba()
│   ├── feature_engineering.py  # extract_meta_features()
│   └── walk_forward.py         # walk_forward_train()
├── labeling/
│   └── triple_barrier.py       # generate labels
├── orderflow/
│   └── vpin.py                 # VPINIndicator.toxicity_level
└── position_sizing/
    └── integrated_sizing.py    # IntegratedSizer.calculate()
```

## Technical Decisions

### Decision 1: Orchestrator Placement

**Options Considered**:
1. **Option A**: Inside `pipeline/orchestrator/` (new module under pipeline)
   - Pros: Follows existing pipeline structure, integrates with stages
   - Cons: None significant
2. **Option B**: Inside `strategies/common/ml4t/` (with other common modules)
   - Pros: Near the blocks it coordinates
   - Cons: Violates separation (orchestration vs. computation)

**Selected**: Option A

**Rationale**: The orchestrator coordinates pipeline execution, fitting the pipeline/ hierarchy. Computation stays in strategies/common/.

---

### Decision 2: Model Persistence Format

**Options Considered**:
1. **Option A**: joblib (sklearn standard)
   - Pros: Native sklearn support, compression, fast
   - Cons: Python-version sensitive
2. **Option B**: pickle
   - Pros: Standard library
   - Cons: Slower, no compression

**Selected**: Option A (joblib)

**Rationale**: sklearn's recommended persistence format. Already used by MetaModel internally.

---

### Decision 3: Event Communication

**Options Considered**:
1. **Option A**: Redis MessageBus only
   - Pros: NautilusTrader native, µs latency
   - Cons: Single-node only
2. **Option B**: Direct method calls only
   - Pros: Simpler, no Redis dependency
   - Cons: Tight coupling
3. **Option C**: Hybrid (Redis primary, direct fallback)
   - Pros: Best of both, resilient
   - Cons: Slightly more complex

**Selected**: Option C (Hybrid)

**Rationale**: Redis for loose coupling when available; direct calls as fallback. Per spec FR-016.

---

### Decision 4: Inference Threading Model

**Options Considered**:
1. **Option A**: Single-threaded synchronous
   - Pros: Simple, no race conditions, predictable latency
   - Cons: Cannot parallelize
2. **Option B**: Async with asyncio
   - Pros: Better throughput for I/O-bound ops
   - Cons: More complex, MetaModel.predict is CPU-bound

**Selected**: Option A (Single-threaded)

**Rationale**: Per spec assumption "Single-threaded inference is acceptable". MetaModel.predict_proba() is CPU-bound (<5ms), not I/O-bound. Keep simple per KISS.

---

## Implementation Strategy

### Phase 1: Core Types & Config (P1 MVP Foundation)

**Goal**: Define all data structures needed by the orchestrator

**Deliverables**:
- [x] `pipeline/orchestrator/config.py` - OrchestratorConfig dataclass
- [x] `pipeline/orchestrator/events.py` - SignalEvent, EnrichedSignalEvent
- [x] `pipeline/orchestrator/__init__.py` - Package exports

**Dependencies**: None

**Files**:
```python
# config.py
@dataclass
class OrchestratorConfig:
    model_path: Path = Path("models/meta_model.joblib")
    default_confidence: float = 0.5
    retrain_accuracy_drop_threshold: float = 0.10  # 10% drop triggers retrain
    retrain_min_samples: int = 1000
    redis_enabled: bool = True
    inference_timeout_ms: int = 10
    feature_names: list[str] = field(default_factory=lambda: [
        "volatility", "momentum", "regime", "trend_strength"
    ])

# events.py
@dataclass
class SignalEvent:
    instrument_id: str
    signal: int  # -1, 0, 1
    timestamp: int  # nanoseconds
    bars: list[Bar]  # Recent bars for feature extraction

@dataclass
class EnrichedSignalEvent:
    signal_event: SignalEvent
    meta_confidence: float
    regime_weight: float
    toxicity: float
    latency_ns: int
```

---

### Phase 2: Inference Loop (P1 MVP Core)

**Goal**: Real-time signal enrichment with meta-learning confidence

**Deliverables**:
- [ ] `pipeline/orchestrator/inference.py` - InferenceLoop class
- [ ] Unit tests for inference loop
- [ ] Integration test with mock signals

**Dependencies**: Phase 1, existing MetaModel

**Key Implementation**:
```python
class InferenceLoop:
    """Real-time inference for signal enrichment."""

    def __init__(self, config: OrchestratorConfig):
        self._config = config
        self._model: MetaModel | None = None
        self._vpin: VPINIndicator | None = None

    def load_model(self, path: Path | None = None) -> bool:
        """Load persisted model. Returns False if not found."""

    def process_signal(self, event: SignalEvent) -> EnrichedSignalEvent:
        """Extract features, predict confidence, return enriched signal.

        Latency target: <10ms (99th percentile)
        """
        start = time.perf_counter_ns()

        # 1. Extract meta-features (target: <5ms)
        features = extract_meta_features(event.bars)

        # 2. Get model confidence (target: <5ms)
        if self._model and self._model.is_fitted:
            confidence = self._model.get_confidence(features)
        else:
            confidence = self._config.default_confidence
            logger.warning("Using default confidence - model not fitted")

        # 3. Get VPIN toxicity
        toxicity = self._get_toxicity(event.bars)

        # 4. Calculate regime weight (from features)
        regime_weight = self._calculate_regime_weight(features)

        latency = time.perf_counter_ns() - start

        return EnrichedSignalEvent(
            signal_event=event,
            meta_confidence=confidence,
            regime_weight=regime_weight,
            toxicity=toxicity,
            latency_ns=latency,
        )
```

---

### Phase 3: Training Loop (P2)

**Goal**: Offline batch training with walk-forward validation

**Deliverables**:
- [ ] `pipeline/orchestrator/training.py` - TrainingLoop class
- [ ] `pipeline/orchestrator/persistence.py` - Model save/load
- [ ] Unit tests for training loop
- [ ] Integration test with historical data

**Dependencies**: Phase 1, existing MetaModel, triple_barrier

**Key Implementation**:
```python
class TrainingLoop:
    """Batch training for meta-model."""

    def train(
        self,
        bars: list[Bar],
        labels: np.ndarray | None = None,
    ) -> TrainingResult:
        """Train meta-model on historical data.

        Args:
            bars: Historical bar data (min 1000 required)
            labels: Optional pre-computed labels. If None, generate via triple-barrier.

        Returns:
            TrainingResult with model, metrics, validation scores
        """
        if len(bars) < 1000:
            raise ValueError(f"Minimum 1000 bars required, got {len(bars)}")

        # 1. Generate labels if not provided
        if labels is None:
            labels = self._generate_labels(bars)

        # 2. Extract features aligned with labels
        features = self._extract_features(bars, labels)

        # 3. Train with walk-forward validation
        model, metrics = walk_forward_train(
            model=MetaModel(self._model_config),
            features=features,
            labels=labels,
        )

        return TrainingResult(
            model=model,
            accuracy=metrics["accuracy"],
            auc=metrics["auc"],
            feature_importance=model.feature_importances,
        )
```

---

### Phase 4: Retrain Monitor (P3)

**Goal**: Monitor live accuracy and trigger background retraining

**Deliverables**:
- [ ] `pipeline/orchestrator/retrain.py` - RetrainMonitor class
- [ ] Unit tests for accuracy monitoring
- [ ] Integration test for model hot-swap

**Dependencies**: Phase 2, Phase 3

**Key Implementation**:
```python
class RetrainMonitor:
    """Monitors prediction accuracy and triggers retraining."""

    def __init__(self, config: OrchestratorConfig):
        self._config = config
        self._baseline_accuracy: float | None = None
        self._rolling_correct: deque = deque(maxlen=1000)
        self._pending_retrain: bool = False

    def record_outcome(self, prediction: float, actual: int) -> None:
        """Record prediction outcome for accuracy tracking."""
        correct = (prediction > 0.5) == (actual == 1)
        self._rolling_correct.append(correct)

    def check_retrain_trigger(self) -> RetrainTrigger | None:
        """Check if retrain should be triggered."""
        if len(self._rolling_correct) < 100:
            return None  # Not enough samples

        current_accuracy = sum(self._rolling_correct) / len(self._rolling_correct)

        if self._baseline_accuracy is None:
            self._baseline_accuracy = current_accuracy
            return None

        accuracy_drop = self._baseline_accuracy - current_accuracy

        if accuracy_drop >= self._config.retrain_accuracy_drop_threshold:
            return RetrainTrigger(
                reason="accuracy_degradation",
                baseline=self._baseline_accuracy,
                current=current_accuracy,
                drop=accuracy_drop,
            )
        return None
```

---

### Phase 5: Main Orchestrator & Redis Integration (P4)

**Goal**: Unified orchestrator with Redis MessageBus support

**Deliverables**:
- [ ] `pipeline/orchestrator/orchestrator.py` - ML4TOrchestrator main class
- [ ] Redis pub/sub integration (with fallback)
- [ ] Full integration tests
- [ ] Documentation

**Dependencies**: Phase 2, 3, 4

**Key Implementation**:
```python
class ML4TOrchestrator:
    """Central coordinator for ML4T pipeline.

    Connects inference, training, and retrain loops.
    Supports Redis MessageBus with direct call fallback.
    """

    def __init__(self, config: OrchestratorConfig):
        self._config = config
        self._inference = InferenceLoop(config)
        self._training = TrainingLoop(config)
        self._retrain_monitor = RetrainMonitor(config)
        self._model_lock = threading.Lock()

    def start(self) -> None:
        """Start orchestrator (load model, subscribe to events)."""
        self._inference.load_model(self._config.model_path)
        if self._config.redis_enabled:
            self._subscribe_to_signals()

    def process_signal(self, event: SignalEvent) -> EnrichedSignalEvent:
        """Process signal event and return enriched result."""
        return self._inference.process_signal(event)

    def train(self, bars: list[Bar]) -> TrainingResult:
        """Train meta-model on historical data."""
        result = self._training.train(bars)
        self._save_model(result.model)
        return result

    def hot_swap_model(self, new_model: MetaModel) -> None:
        """Atomically replace model reference."""
        with self._model_lock:
            self._inference._model = new_model
```

---

## File Structure

```
pipeline/
├── orchestrator/
│   ├── __init__.py              # Package exports
│   ├── config.py                # OrchestratorConfig, TrainingResult, etc.
│   ├── events.py                # SignalEvent, EnrichedSignalEvent, RetrainTrigger
│   ├── inference.py             # InferenceLoop
│   ├── training.py              # TrainingLoop
│   ├── retrain.py               # RetrainMonitor
│   ├── persistence.py           # Model save/load utilities
│   └── orchestrator.py          # ML4TOrchestrator main class
tests/
├── unit/
│   └── pipeline/
│       └── orchestrator/
│           ├── test_config.py
│           ├── test_inference.py
│           ├── test_training.py
│           └── test_retrain.py
└── integration/
    └── test_orchestrator_integration.py
```

## API Design

### Public Interface

```python
from pipeline.orchestrator import (
    ML4TOrchestrator,
    OrchestratorConfig,
    SignalEvent,
    EnrichedSignalEvent,
    TrainingResult,
)

# Initialize
config = OrchestratorConfig(
    model_path=Path("models/meta_model.joblib"),
    redis_enabled=True,
)
orchestrator = ML4TOrchestrator(config)

# Start (load model, subscribe to Redis if enabled)
orchestrator.start()

# Inference (direct call)
event = SignalEvent(
    instrument_id="BTC-PERP.HYPERLIQUID",
    signal=1,  # BUY
    timestamp=time.time_ns(),
    bars=recent_bars,
)
enriched = orchestrator.process_signal(event)

# Training (batch)
result = orchestrator.train(historical_bars)
print(f"Walk-forward accuracy: {result.accuracy:.2%}")

# Check retrain trigger
orchestrator.retrain_monitor.record_outcome(prediction=0.65, actual=1)
trigger = orchestrator.retrain_monitor.check_retrain_trigger()
if trigger:
    orchestrator.train(new_bars)
```

### Configuration

```python
@dataclass
class OrchestratorConfig:
    # Model settings
    model_path: Path = Path("models/meta_model.joblib")
    default_confidence: float = 0.5

    # Retrain settings
    retrain_accuracy_drop_threshold: float = 0.10
    retrain_min_samples: int = 1000
    retrain_interval_bars: int | None = None  # Optional time-based trigger

    # Redis settings
    redis_enabled: bool = True
    redis_channel_signals: str = "nautilus:signals"
    redis_channel_enriched: str = "nautilus:enriched_signals"

    # Performance settings
    inference_timeout_ms: int = 10

    # Feature settings
    feature_names: list[str] = field(default_factory=lambda: [
        "volatility", "momentum", "regime", "trend_strength"
    ])
```

## Testing Strategy

### Unit Tests
- [x] Test OrchestratorConfig validation
- [ ] Test SignalEvent/EnrichedSignalEvent serialization
- [ ] Test InferenceLoop.process_signal() latency (<10ms)
- [ ] Test InferenceLoop cold start (no model → default confidence)
- [ ] Test TrainingLoop.train() with minimum data check
- [ ] Test TrainingLoop walk-forward validation metrics
- [ ] Test RetrainMonitor accuracy tracking
- [ ] Test RetrainMonitor trigger conditions
- [ ] Test model hot-swap atomicity

### Integration Tests
- [ ] Test full inference pipeline (signal → enriched)
- [ ] Test full training pipeline (bars → persisted model)
- [ ] Test retrain flow (accuracy drop → new model)
- [ ] Test Redis pub/sub integration
- [ ] Test Redis fallback to direct calls
- [ ] Test RiskStage integration via alpha_output.meta_output

### Performance Tests
- [ ] Benchmark inference latency (target: <10ms p99)
- [ ] Benchmark training time (target: <5min for 260K bars)
- [ ] Benchmark throughput (target: 1000 signals/sec)

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Model loading fails silently | High | Low | Add explicit validation on start(), log warnings |
| Inference exceeds 10ms budget | Medium | Medium | Pre-warm model, lazy VPIN init, profile critical path |
| Redis connection drops mid-inference | Medium | Medium | Graceful fallback to direct calls per FR-016 |
| Model hot-swap race condition | High | Low | Use threading.Lock for atomic swap |
| Training data too small | Medium | Medium | Validate minimum 1000 bars before training |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.222.0 (nightly)
- joblib >= 1.3.0 (model persistence)
- redis >= 4.0 (optional, for MessageBus)

### Internal Dependencies (EXISTING - Already Tested)
- `strategies/common/meta_learning/meta_model.py` - MetaModel class
- `strategies/common/meta_learning/feature_engineering.py` - extract_meta_features()
- `strategies/common/meta_learning/walk_forward.py` - walk_forward_train()
- `strategies/common/labeling/triple_barrier.py` - label generation
- `strategies/common/orderflow/vpin.py` - VPINIndicator
- `strategies/common/position_sizing/integrated_sizing.py` - IntegratedSizer
- `pipeline/stages/risk.py` - RiskStage (integration point)

## Constitution Check

### Pillar Alignment
- **P1 Probabilistico**: Uses confidence intervals (meta_confidence), not point predictions
- **P2 Non Lineare**: IntegratedSizer applies signal^0.5 scaling
- **P3 Non Parametrico**: Thresholds are configurable; safety limits remain FIXED
- **P4 Scalare**: Works at any frequency via configurable feature extraction

### Safety Parameters
- All safety limits (MAX_LEVERAGE, STOP_LOSS, etc.) remain in IntegratedSizer
- Orchestrator DOES NOT modify safety parameters - only passes meta_output
- Model confidence is BOUNDED [0, 1] - cannot bypass risk limits

### KISS Compliance
- Single-threaded inference (simplest option)
- Glue code only - no new ML algorithms
- Uses existing tested blocks

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Inference latency <10ms (p99)
- [ ] Training <5 minutes for 260K bars
- [ ] Cold start gracefully degrades to default confidence
- [ ] Model hot-swap causes zero dropped signals
- [ ] Documentation updated
- [ ] Code review approved
