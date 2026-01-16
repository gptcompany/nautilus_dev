# Feature Specification: LOB Deep Learning Suite

**Feature Branch**: `044-lob-deep-learning`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "LOB Deep Learning Suite - SOTA limit order book analysis using deep learning models (TLOB, DeepLOB, TransLOB, HLOB). Replaces classical ML approach with attention-based transformers. Integrates with existing L2 orderbook data from Hyperliquid. P1-P4 compliant with probabilistic outputs and uncertainty quantification."

## Problem Statement

Limit Order Book (LOB) data provides critical microstructure information:

- **Order Flow Imbalance**: Buyer vs seller aggression
- **Price Discovery**: Where is the market heading?
- **Liquidity Depth**: Support/resistance levels
- **Informed Trading**: Detecting institutional flow

Current state analysis revealed:

**SGX-Full-OrderBook-Tick-Data-Trading-Strategy** (analyzed repo):
- Python 2 codebase (outdated)
- Classical ML: RandomForest, ExtraTrees, AdaBoost, GradientBoosting, SVM
- 2014 SGX futures data (decade old)
- Features: Rise ratio, Depth ratio (Bid/Ask weighted)
- **Verdict**: Educational value only, NOT SOTA

**SOTA Gap**: Deep learning models (2020-2024) achieve +15-25% F1 improvement over classical ML on LOB prediction tasks.

## SOTA Research Findings

| Model | Year | Architecture | Key Innovation | F1 vs DeepLOB |
|-------|------|--------------|----------------|---------------|
| **DeepLOB** | 2019 | CNN + LSTM | First deep LOB baseline | Baseline |
| **TransLOB** | 2022 | Transformer | Self-attention for LOB | +2.1% |
| **HLOB** | 2023 | Hierarchical CNN | Multi-scale aggregation | +2.5% |
| **TLOB** | 2025 | Dual-Attention Transformer | State-of-the-art | +3.7% |

### Cloned Reference Repositories (in /media/sam/1TB/)

1. **TLOB** (SOTA): `/media/sam/1TB/TLOB/`
   - Source: [github.com/LeonardoBerti00/TLOB](https://github.com/LeonardoBerti00/TLOB)
   - Dual-attention transformer (temporal + feature attention)
   - +3.7 F1 on FI-2010, +1.1 F1 on Bitcoin
   - Models: `models/tlob.py`, `models/deeplob.py`, `models/mlplob.py`

2. **LOBFrame** (Production): `/media/sam/1TB/LOBFrame/`
   - Source: [github.com/FinancialComputingUCL/LOBFrame](https://github.com/FinancialComputingUCL/LOBFrame)
   - UCL research framework with full pipeline
   - Models: DeepLOB, Transformer, iTransformer, LobTransformer, DLA, CNN1/2, TABL, AxialLOB, HLOB
   - Includes backtesting simulator and post-trading analysis

3. **DeepLOB** (Baseline): `/media/sam/1TB/DeepLOB-reference/`
   - Source: [github.com/zcakhaa/DeepLOB-Deep-Convolutional-Neural-Networks-for-Limit-Order-Books](https://github.com/zcakhaa/DeepLOB-Deep-Convolutional-Neural-Networks-for-Limit-Order-Books)
   - Original DeepLOB implementation (PyTorch + TensorFlow)
   - Reference for baseline comparison

## Four Pillars Alignment

| Pillar | Model | Implementation |
|--------|-------|----------------|
| P1 (Probabilistico) | All models | Output class probabilities, not hard labels |
| P2 (Non Lineare) | TLOB/TransLOB | Attention captures non-linear dependencies |
| P3 (Non Parametrico) | Neural nets | Learned representations, not fixed features |
| P4 (Scalare) | Multi-horizon | Predict 1, 5, 10, 20 tick horizons simultaneously |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - DeepLOB Baseline (Priority: P1) MVP

As a quant, I want to implement DeepLOB as a baseline model so I can benchmark against classical ML and have a foundation for advanced models.

**Why this priority**: DeepLOB is the established baseline (2019). All SOTA models compare against it. Required for proper benchmarking.

**Independent Test**: Train on 1 week of Hyperliquid L2 data, predict mid-price direction, compare F1 to random forest.

**Acceptance Scenarios**:

1. **Given** L2 orderbook snapshots (10 levels), **When** I train DeepLOB, **Then** model converges within 50 epochs with validation loss decreasing.
2. **Given** trained DeepLOB, **When** I predict mid-price direction, **Then** F1 score exceeds 60% on held-out test set.
3. **Given** same data, **When** I compare to RandomForest baseline, **Then** DeepLOB F1 is at least 10% higher.
4. **Given** prediction output, **When** I examine probabilities, **Then** I receive class probabilities (not just labels) for P1 compliance.

**Mathematical Formulation** (Zhang et al., 2019):
```
Input: X ∈ ℝ^(T×40)  # T timesteps, 10 bid + 10 ask levels × (price, volume)
CNN: Extract spatial features across price levels
LSTM: Capture temporal dependencies
Output: P(up | X), P(down | X), P(stationary | X)
```

---

### User Story 2 - TLOB State-of-the-Art (Priority: P1)

As a quant, I want to implement TLOB (dual-attention transformer) so I can achieve state-of-the-art LOB prediction accuracy.

**Why this priority**: TLOB is SOTA (2025), +3.7% F1 over DeepLOB. Critical for competitive edge.

**Independent Test**: Train TLOB on same data as US1, compare F1 scores directly.

**Acceptance Scenarios**:

1. **Given** same L2 data as DeepLOB, **When** I train TLOB, **Then** training completes with comparable time (within 2x).
2. **Given** trained TLOB, **When** I evaluate on test set, **Then** F1 exceeds DeepLOB by at least 2%.
3. **Given** attention weights, **When** I visualize them, **Then** model focuses on relevant price levels and time lags.
4. **Given** GPU available, **When** inference runs, **Then** prediction latency < 10ms per snapshot.

**Architecture** (Chen et al., 2025):
```
Temporal Attention: Attend across time dimension
Spatial Attention: Attend across price levels
Dual-attention: Combine both for rich representations
```

---

### User Story 3 - Multi-Horizon Prediction (Priority: P2)

As a trader, I want to predict price direction at multiple horizons (1, 5, 10, 20 ticks) so I can adapt my trading timeframe.

**Why this priority**: Different strategies need different horizons. P4 (Scalare) compliance requires multi-scale predictions.

**Independent Test**: Train single model with multi-task heads, verify each horizon improves vs single-horizon model.

**Acceptance Scenarios**:

1. **Given** multi-horizon model, **When** I request k=1 prediction, **Then** I receive direction probability for next tick.
2. **Given** multi-horizon model, **When** I request k=20 prediction, **Then** I receive direction probability for 20 ticks ahead.
3. **Given** horizon-specific F1 scores, **When** I compare, **Then** shorter horizons have higher accuracy (expected: k=1 > k=20).
4. **Given** prediction confidence, **When** confidence < 0.6, **Then** system flags as low-confidence (don't trade).

---

### User Story 4 - Uncertainty Quantification (Priority: P2)

As a risk manager, I want model predictions with uncertainty estimates so I can adjust position sizing based on confidence.

**Why this priority**: P1 (Probabilistico) requires uncertainty. Critical for risk-aware trading.

**Independent Test**: Implement MC Dropout or ensemble, verify uncertainty correlates with prediction errors.

**Acceptance Scenarios**:

1. **Given** model with MC Dropout, **When** I run 10 forward passes, **Then** I receive mean and std of predictions.
2. **Given** uncertainty estimate, **When** actual error is high, **Then** predicted uncertainty was also high (calibration).
3. **Given** ensemble of 5 models, **When** predictions disagree, **Then** uncertainty is high.
4. **Given** uncertainty output, **When** integrated with position sizing, **Then** high-uncertainty signals get smaller positions.

---

### User Story 5 - Hyperliquid L2 Integration (Priority: P2)

As a trader, I want to use real-time Hyperliquid L2 data for LOB prediction so I can generate actionable signals.

**Why this priority**: Integration with existing data pipeline (spec 001) provides immediate practical value.

**Independent Test**: Connect to live Hyperliquid WebSocket, feed L2 updates to trained model, receive predictions.

**Acceptance Scenarios**:

1. **Given** Hyperliquid L2 WebSocket feed, **When** model receives snapshot, **Then** prediction generated within 50ms.
2. **Given** 10-level orderbook update, **When** model processes, **Then** output includes direction, confidence, and uncertainty.
3. **Given** model prediction, **When** fed to strategy, **Then** signal is compatible with NautilusTrader event format.
4. **Given** data gap > 1 minute, **When** feed resumes, **Then** model resets state (LSTM hidden) before predicting.

---

### User Story 6 - Model Comparison Framework (Priority: P3)

As a researcher, I want to compare all LOB models on the same data so I can select the best model for my use case.

**Why this priority**: Meta-feature enabling informed model selection. Enhancement after core models work.

**Independent Test**: Run all models on held-out test week, generate comparison report.

**Acceptance Scenarios**:

1. **Given** test dataset, **When** I run comparison, **Then** I receive F1, precision, recall, latency for each model.
2. **Given** comparison results, **When** I view ranking, **Then** models sorted by user-selected metric.
3. **Given** computational budget, **When** I filter by latency < 20ms, **Then** only fast models shown.

---

### Edge Cases

- What if L2 has < 10 levels? → Pad with zeros, flag as incomplete.
- What if price gaps exist (no trades)? → Interpolate or mark as stale.
- What if model confidence always > 0.9? → Calibration issue, retrain with label smoothing.
- What if GPU OOM during training? → Reduce batch size, use gradient checkpointing.
- What if Hyperliquid changes L2 format? → Adapter layer to normalize input.

## Requirements *(mandatory)*

### Functional Requirements

**Data Pipeline:**
- **FR-001**: System MUST accept L2 orderbook snapshots with configurable depth (default 10 levels).
- **FR-002**: System MUST normalize prices to mid-price relative format (log returns).
- **FR-003**: System MUST handle missing levels by zero-padding.
- **FR-004**: System MUST support both historical (Parquet) and real-time (WebSocket) data sources.

**Models:**
- **FR-005**: System MUST implement DeepLOB architecture (CNN + LSTM).
- **FR-006**: System MUST implement TLOB architecture (dual-attention transformer).
- **FR-007**: System MUST support multi-horizon prediction (k=1, 5, 10, 20 ticks).
- **FR-008**: System MUST output class probabilities, not hard labels (P1 compliance).
- **FR-009**: System MUST provide uncertainty estimates via MC Dropout or ensemble.

**Training:**
- **FR-010**: System MUST support GPU training with mixed precision (FP16).
- **FR-011**: System MUST checkpoint models during training for resume.
- **FR-012**: System MUST log training metrics (loss, F1, precision, recall) per epoch.
- **FR-013**: System MUST implement early stopping on validation loss.

**Inference:**
- **FR-014**: System MUST provide batch and single-sample inference modes.
- **FR-015**: System MUST achieve inference latency < 10ms on GPU.
- **FR-016**: System MUST integrate with Hyperliquid L2 WebSocket feed.
- **FR-017**: System MUST emit predictions compatible with NautilusTrader events.

**Evaluation:**
- **FR-018**: System MUST compute F1, precision, recall per class and macro-averaged.
- **FR-019**: System MUST support model comparison across multiple metrics.
- **FR-020**: System MUST persist evaluation results for tracking over time.

### Key Entities

- **LOBSnapshot**: Single orderbook state. Attributes: timestamp, symbol, bids (list of price/volume), asks (list of price/volume), depth.
- **LOBSequence**: Time series of snapshots for model input. Attributes: snapshots (list), sequence_length, horizon.
- **LOBPrediction**: Model output. Attributes: timestamp, symbol, horizon, up_prob, down_prob, stationary_prob, confidence, uncertainty.
- **LOBModel**: Trained model artifact. Attributes: model_type (DeepLOB/TLOB), weights_path, training_metrics, validation_f1.
- **LOBComparisonResult**: Benchmark results. Attributes: model_name, f1, precision, recall, latency_ms, gpu_memory_mb.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: DeepLOB achieves F1 > 60% on Hyperliquid BTC-PERP test set.
- **SC-002**: TLOB achieves F1 at least 2% higher than DeepLOB on same data.
- **SC-003**: Inference latency < 10ms per prediction on NVIDIA GPU.
- **SC-004**: Training converges within 50 epochs for all models.
- **SC-005**: Uncertainty estimates are calibrated (high uncertainty correlates with errors).
- **SC-006**: Real-time predictions arrive within 50ms of L2 update.
- **SC-007**: Models improve over RandomForest baseline by at least 10% F1.
- **SC-008**: Multi-horizon predictions all exceed 55% F1.

## Scope

### In Scope

- DeepLOB implementation (baseline)
- TLOB implementation (SOTA)
- Multi-horizon prediction (k=1, 5, 10, 20)
- Uncertainty quantification (MC Dropout + ensemble)
- Hyperliquid L2 integration
- Model comparison framework
- GPU training support
- NautilusTrader event integration

### Out of Scope

- TransLOB, HLOB (defer to future spec if needed)
- Order flow imbalance (VPIN) - see spec 001
- Trade execution based on predictions
- Real-time model retraining
- Multi-asset correlation
- Market making strategies

## Assumptions

- L2 orderbook data available from Hyperliquid (spec 001 dependency).
- NVIDIA GPU available for training (CUDA 11.8+).
- PyTorch 2.0+ for model implementation.
- Sufficient historical data: minimum 1 month for training, 1 week for validation.
- Tick-level timestamps available (nanosecond precision not required, millisecond sufficient).

## Dependencies

- `specs/001-ccxt-data-pipeline/` - L2 orderbook data from Hyperliquid
- `pipeline/stages/alpha.py` - Integration point for signals
- PyTorch >= 2.0 - Model training/inference
- NumPy - Data preprocessing
- Pandas - Data manipulation

## Technical Notes

### DeepLOB Architecture (Zhang et al., 2019)

```python
class DeepLOB(nn.Module):
    def __init__(self, num_classes=3):
        # Inception-style CNN for spatial features
        self.conv1 = nn.Conv2d(1, 32, (1, 2), (1, 2))
        self.conv2 = nn.Conv2d(32, 32, (4, 1))
        self.conv3 = nn.Conv2d(32, 32, (4, 1))

        # LSTM for temporal features
        self.lstm = nn.LSTM(32, 64, num_layers=1, batch_first=True)

        # Classification head
        self.fc = nn.Linear(64, num_classes)
```

### TLOB Attention Mechanism (Chen et al., 2025)

```python
class DualAttention(nn.Module):
    def __init__(self, d_model):
        self.temporal_attn = nn.MultiheadAttention(d_model, 8)
        self.spatial_attn = nn.MultiheadAttention(d_model, 8)

    def forward(self, x):
        # x: (batch, time, levels, features)
        t_out = self.temporal_attn(x.flatten(2), ...)  # Attend across time
        s_out = self.spatial_attn(x.transpose(1, 2), ...)  # Attend across levels
        return t_out + s_out  # Combine
```

### Input Normalization

```python
def normalize_lob(snapshot, mid_price):
    """Normalize LOB to mid-price relative format."""
    prices = (snapshot.prices - mid_price) / mid_price  # Log-like relative
    volumes = snapshot.volumes / snapshot.volumes.sum()  # Proportion
    return np.concatenate([prices, volumes], axis=-1)
```

### Data Adapter: Hyperliquid → LOBFrame Format

**NOTE**: LOBFrame expects LOBSTER format (NASDAQ). Hyperliquid L2 requires adapter.

```python
# LOBSTER format (LOBFrame expects):
# [ask_price_1, ask_size_1, bid_price_1, bid_size_1, ..., ask_price_10, ask_size_10, bid_price_10, bid_size_10]
# Shape: (T, 40) for 10 levels

# Hyperliquid L2 format (spec 001):
# {"bids": [[price, size], ...], "asks": [[price, size], ...]}

def hyperliquid_to_lobster(snapshot: dict, num_levels: int = 10) -> np.ndarray:
    """Convert Hyperliquid L2 to LOBSTER format for LOBFrame/TLOB models."""
    row = []
    for i in range(num_levels):
        ask_price = snapshot["asks"][i][0] if i < len(snapshot["asks"]) else 0
        ask_size = snapshot["asks"][i][1] if i < len(snapshot["asks"]) else 0
        bid_price = snapshot["bids"][i][0] if i < len(snapshot["bids"]) else 0
        bid_size = snapshot["bids"][i][1] if i < len(snapshot["bids"]) else 0
        row.extend([ask_price, ask_size, bid_price, bid_size])
    return np.array(row)
```

**Task Coverage**: User Story 5 (Hyperliquid L2 Integration) covers this adapter implementation.

### Pipeline Integration: AlphaStage

**NOTE**: LOB predictions integrate with `pipeline/stages/alpha.py` as signal source.

```python
# pipeline/stages/alpha.py integration pattern
from pipeline.core.types import StageResult, Confidence

class LOBAlphaStage(AbstractStage):
    """LOB-based alpha generation using TLOB/DeepLOB predictions."""

    def __init__(self, model: nn.Module, threshold: float = 0.6):
        self.model = model
        self.threshold = threshold

    async def execute(self, state: PipelineState) -> StageResult:
        # Get L2 data from DATA stage
        l2_data = state.stage_results[StageType.DATA].output

        # Convert to model input
        lob_sequence = self._prepare_sequence(l2_data)

        # Get prediction with uncertainty
        with torch.no_grad():
            probs = self.model(lob_sequence)  # [up, down, stationary]
            confidence = probs.max().item()

        # Map to Confidence enum (P1 compliance)
        if confidence >= 0.8:
            conf_level = Confidence.HIGH_CONFIDENCE
        elif confidence >= self.threshold:
            conf_level = Confidence.MEDIUM_CONFIDENCE
        else:
            conf_level = Confidence.LOW_CONFIDENCE

        return StageResult(
            stage=StageType.ALPHA,
            confidence=conf_level,
            output={"direction": probs.argmax().item(), "probs": probs.tolist()},
            needs_human_review=(conf_level == Confidence.LOW_CONFIDENCE),
        )
```

**Task Coverage**: User Story 5 (FR-017) covers NautilusTrader event integration.

## References

1. Zhang et al. (2019) - "DeepLOB: Deep Convolutional Neural Networks for Limit Order Books"
2. Chen et al. (2025) - "TLOB: A Dual-Attention Transformer for Limit Order Book Prediction"
3. Lucchese et al. (2022) - "TransLOB: A Transformer-Based Deep Learning Model for LOB"
4. Briola et al. (2023) - "HLOB: A Hierarchical Model for Limit Order Book Prediction"
5. LOBFrame Documentation - UCL Computational Finance Group

## Classical ML Comparison (SGX Repo Analysis)

For reference, the analyzed classical ML approach (SGX repo) used:

| Aspect | Classical ML (SGX) | Deep Learning (TLOB) |
|--------|-------------------|----------------------|
| Features | Hand-crafted (Rise ratio, Depth ratio) | Learned end-to-end |
| Model | RandomForest, SVM | Transformer + Attention |
| Data | 2014 SGX futures | Modern crypto LOB |
| F1 Score | ~55% typical | ~65%+ (SOTA) |
| Latency | ~1ms | ~5-10ms (GPU) |
| P1 Compliance | Probability via RF | Native softmax |
| P3 Compliance | Fixed features | Learned representations |

**Verdict**: Deep learning models justify the additional complexity with +10-15% F1 improvement and better pillar alignment.
