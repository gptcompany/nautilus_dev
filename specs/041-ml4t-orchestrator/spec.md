# Feature Specification: ML4T Orchestrator

**Feature Branch**: `041-ml4t-orchestrator`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "ML4TOrchestrator - Orchestration layer for ML4Trading-like pipeline. Connects existing blocks (meta_learning, labeling, orderflow, position_sizing) into training/inference/retrain loops. Uses Redis MessageBus (NautilusTrader native) for event communication. Manages model persistence, walk-forward retraining triggers, and confidence-based sizing integration with pipeline/stages/risk.py."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inference Loop for Position Sizing (Priority: P1) 🎯 MVP

A trader using NautilusTrader receives a primary signal from their strategy. The orchestrator intercepts this signal, extracts meta-features from current market state (volatility, momentum, regime), queries the trained meta-model for P(signal_correct), and provides confidence-adjusted position sizing to the risk stage.

**Why this priority**: This is the core value proposition - every trade benefits from meta-learning confidence adjustment. Without inference, the meta-learning pipeline provides no live value.

**Independent Test**: Can be fully tested by injecting a mock signal event and verifying that RiskStage receives enhanced alpha_output with meta_confidence, regime_weight, and toxicity values populated.

**Acceptance Scenarios**:

1. **Given** a trained meta-model exists and primary strategy emits BUY signal, **When** orchestrator receives the signal event, **Then** it extracts features, predicts confidence, and passes enriched signal to RiskStage within 10ms latency budget.
2. **Given** no trained meta-model exists (cold start), **When** orchestrator receives signal event, **Then** it uses default confidence (0.5) and logs warning about untrained model.
3. **Given** VPIN toxicity is HIGH (>0.7), **When** orchestrator calculates sizing inputs, **Then** toxicity penalty is applied reducing effective position size.

---

### User Story 2 - Training Loop for Meta-Model (Priority: P2)

A quant researcher wants to train the meta-model on historical data. The orchestrator coordinates: loading historical bars, generating triple-barrier labels, extracting meta-features, training the RandomForest meta-model, and running walk-forward validation. Results are persisted for later inference use.

**Why this priority**: Training must happen before inference provides value. However, training can be done offline/batch, while inference must be real-time.

**Independent Test**: Can be fully tested by providing historical bar data and verifying that a trained model file is produced with walk-forward validation metrics.

**Acceptance Scenarios**:

1. **Given** historical bar data for 6 months, **When** user triggers training, **Then** orchestrator generates labels, extracts features, trains model, and reports walk-forward accuracy.
2. **Given** insufficient data (< 1000 bars), **When** user triggers training, **Then** orchestrator returns error with minimum data requirements.
3. **Given** training completes successfully, **When** model is persisted, **Then** model can be loaded in a new session for inference.

---

### User Story 3 - Automatic Retraining Trigger (Priority: P3)

The system monitors live trading performance. When model accuracy degrades below threshold (e.g., hit rate drops 10% from baseline), or when sufficient new data accumulates, the orchestrator triggers background retraining without interrupting live inference.

**Why this priority**: Prevents model staleness but requires both inference and training loops to be working first.

**Independent Test**: Can be fully tested by simulating performance degradation metrics and verifying that retrain event is emitted.

**Acceptance Scenarios**:

1. **Given** live model has 60% accuracy baseline and current rolling accuracy drops to 50%, **When** orchestrator evaluates performance, **Then** retrain event is triggered.
2. **Given** retrain is triggered, **When** new model finishes training, **Then** old model continues serving inference until new model passes validation.
3. **Given** new model fails validation (accuracy < old model), **When** orchestrator evaluates, **Then** old model is retained and alert is logged.

---

### User Story 4 - Redis Message Bus Integration (Priority: P4)

The orchestrator publishes and subscribes to events via NautilusTrader's Redis MessageBus. This enables loose coupling between strategy signals, orchestrator processing, and risk stage consumption.

**Why this priority**: Provides clean architecture but system can work with direct method calls initially.

**Independent Test**: Can be tested by publishing a signal event to Redis and verifying orchestrator processes it and publishes enriched result.

**Acceptance Scenarios**:

1. **Given** strategy publishes SignalEvent to MessageBus, **When** orchestrator is subscribed, **Then** it processes event and publishes EnrichedSignalEvent.
2. **Given** MessageBus connection is lost, **When** orchestrator detects failure, **Then** it falls back to direct method invocation and logs warning.

---

### Edge Cases

- What happens when meta-model file is corrupted? → Fall back to default confidence with error log.
- How does system handle extreme market conditions (volatility spike)? → VPIN toxicity naturally reduces sizing.
- What if training data has class imbalance (90% winning trades)? → MetaModel already handles this with class weighting.
- What happens during model hot-swap (retrain completes)? → Atomic model reference swap to prevent inconsistent state.
- How are concurrent training requests handled? → Queue with single-worker to prevent resource contention.

## Requirements *(mandatory)*

### Functional Requirements

**Inference Loop:**
- **FR-001**: System MUST extract meta-features (volatility, momentum, regime, trend_strength) from current market state within 5ms (measured from raw bars input to feature dict output).
- **FR-002**: System MUST query meta-model for confidence prediction within 5ms.
- **FR-003**: System MUST pass enriched output (meta_confidence, regime_weight, toxicity) to RiskStage.
- **FR-004**: System MUST use default confidence (0.5) when meta-model is unavailable.

**Training Loop:**
- **FR-005**: System MUST generate triple-barrier labels from historical price data.
- **FR-006**: System MUST extract meta-features aligned with label timestamps.
- **FR-007**: System MUST train meta-model using walk-forward cross-validation.
- **FR-008**: System MUST persist trained model to disk in recoverable format.
- **FR-009**: System MUST report training metrics (accuracy, AUC, feature importance).

**Retraining Loop:**
- **FR-010**: System MUST monitor rolling accuracy of live predictions.
- **FR-011**: System MUST trigger retrain when accuracy drops below configurable threshold.
- **FR-012**: System MUST validate new model before replacing old model.
- **FR-013**: System MUST support configurable retrain interval (time-based or sample-based).

**Integration:**
- **FR-014**: System MUST integrate with existing pipeline/stages/risk.py via alpha_output.meta_output dict.
- **FR-015**: System MUST integrate with VPIN indicator for toxicity measurement.
- **FR-016**: System MUST support Redis MessageBus for event communication (with fallback to direct calls).

### Key Entities

- **ML4TOrchestrator**: Central coordinator managing training, inference, and retraining workflows.
- **OrchestratorConfig**: Configuration for thresholds, intervals, model paths, feature selection.
- **TrainingResult**: Output of training loop containing model, metrics, validation scores.
- **InferenceResult**: Output of inference containing confidence, factors, latency metadata.
- **RetrainTrigger**: Event indicating retrain should occur, with reason and priority.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Inference latency (signal received to enriched output) under 10ms for 99th percentile.
- **SC-002**: Training loop completes on 6 months of 1-minute bars (260K bars) in under 5 minutes.
- **SC-003**: Walk-forward validation achieves > 55% accuracy on out-of-sample data.
- **SC-004**: System handles 1000 signals/second throughput capacity (direct call processing, single-threaded design has no internal queue).
- **SC-005**: Model hot-swap during retrain causes zero dropped signals.
- **SC-006**: Cold start (no trained model) gracefully degrades to default confidence without errors.

## Assumptions

- Existing blocks (meta_learning, labeling, orderflow, position_sizing) are stable and tested.
- Redis is available and configured as per NautilusTrader MessageBus setup.
- Historical data is available in NautilusTrader catalog format or compatible bars.
- Model persistence uses pickle/joblib for sklearn RandomForest compatibility.
- Single-threaded inference is acceptable (no multi-model ensemble in v1).
- Retrain accuracy threshold default: 10% drop from baseline (configurable).

## Dependencies

- `strategies/common/meta_learning/` - MetaModel, feature_engineering, walk_forward
- `strategies/common/labeling/` - triple_barrier
- `strategies/common/orderflow/` - VPINIndicator, HawkesOFI
- `strategies/common/position_sizing/` - IntegratedSizer
- `pipeline/stages/risk.py` - RiskStage integration point
- `pipeline/core/` - PipelineState, types

## Out of Scope (v1)

- Multi-model ensemble selection
- Distributed training across nodes
- Real-time feature store (features computed on-demand)
- Automated hyperparameter optimization
- A/B testing of model variants
