# Quickstart: ML4T Orchestrator

**Branch**: `041-ml4t-orchestrator`

## TL;DR

```python
from pipeline.orchestrator import ML4TOrchestrator, OrchestratorConfig, SignalEvent

# Setup
orchestrator = ML4TOrchestrator(OrchestratorConfig())
orchestrator.start()

# Inference (real-time)
enriched = orchestrator.process_signal(SignalEvent(
    instrument_id="BTC-PERP.HYPERLIQUID",
    signal=1,
    timestamp=time.time_ns(),
    bars=recent_bars,
))

# Training (batch)
result = orchestrator.train(historical_bars)
print(f"Accuracy: {result.accuracy:.2%}")
```

## What It Does

**ML4TOrchestrator** connects existing meta-learning blocks into:
- **Inference Loop**: Enriches signals with confidence/toxicity (P1 MVP)
- **Training Loop**: Trains meta-model offline (P2)
- **Retrain Monitor**: Auto-retrains on accuracy drop (P3)
- **Redis Integration**: Pub/sub event communication (P4)

## Key APIs

| Method | Description | Latency Target |
|--------|-------------|----------------|
| `process_signal(event)` | Enrich signal with meta-learning | <10ms |
| `train(bars)` | Train meta-model on historical data | <5min/260K bars |
| `start()` | Load model, subscribe to Redis | N/A |
| `hot_swap_model(model)` | Atomically replace model | <1ms |

## Configuration

```python
OrchestratorConfig(
    model_path=Path("models/meta_model.joblib"),
    default_confidence=0.5,           # FR-004: cold start fallback
    retrain_accuracy_drop_threshold=0.10,  # FR-011: 10% drop triggers
    redis_enabled=True,               # FR-016: Redis pub/sub
)
```

## Files Created

```
pipeline/orchestrator/
├── orchestrator.py   # Main class
├── inference.py      # Real-time loop
├── training.py       # Batch training
├── retrain.py        # Accuracy monitor
├── config.py         # Configuration
├── events.py         # Event types
└── persistence.py    # Model save/load
```

## Dependencies (All Existing)

- `strategies/common/meta_learning/` - MetaModel, feature_engineering
- `strategies/common/orderflow/vpin.py` - VPINIndicator
- `strategies/common/position_sizing/` - IntegratedSizer
- `pipeline/stages/risk.py` - RiskStage integration

## Success Criteria

- [ ] Inference <10ms (p99)
- [ ] Training <5min for 260K bars
- [ ] Walk-forward accuracy >55%
- [ ] Cold start uses default confidence
- [ ] Model hot-swap = zero dropped signals
