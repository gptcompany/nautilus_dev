# Feature Specification: Volatility Models Suite

**Feature Branch**: `043-volatility-models`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Volatility Models Suite - Implementation of stochastic volatility models for options pricing and vol forecasting. Includes Classical Heston, Rough Heston (SOTA), Rough Bergomi, and Neural SDE. Regime-switching parameters for P3 compliance. Integration with 042-deribit-options-data for calibration."

## Problem Statement

Options pricing and volatility forecasting require sophisticated models that capture:

- **Stochastic volatility**: Vol itself is random, not constant (BSM assumption)
- **Mean reversion**: Vol tends to revert to long-term average
- **Leverage effect**: Negative correlation between price and vol
- **Rough volatility**: Vol paths are rougher than Brownian motion (H ≈ 0.1)
- **Fat tails**: Extreme moves more frequent than Gaussian

Current state: No vol model infrastructure exists. IV metrics (spec 042) provide signals but not model-based pricing/forecasting.

## Four Pillars Alignment

| Pillar | Model | Implementation |
|--------|-------|----------------|
| P1 (Probabilistico) | All models | Output probability distributions, not point estimates |
| P2 (Non Lineare) | Rough Heston/Bergomi | Fractional BM captures power-law dynamics |
| P3 (Non Parametrico) | Neural SDE | Data-driven dynamics; Regime-switching for others |
| P4 (Scalare) | All models | Tenor-invariant formulations |

## Model Overview

| Model | Complexity | Calibration Time | Best For | SOTA Status |
|-------|------------|------------------|----------|-------------|
| **Classical Heston** | Low | ~1s | Baseline, >7d options | Standard |
| **Rough Heston** | Medium | ~10s | <7d options, vol forecasting | SOTA (2018) |
| **Rough Bergomi** | Medium-High | ~30s | Complex smile dynamics | SOTA (2018) |
| **Neural SDE** | High | ~5min training | Exotic, HFT | Cutting-edge |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classical Heston Calibration (Priority: P1) MVP

As a quant, I want to calibrate Classical Heston model from an IV surface so I can price vanilla options and have a baseline for comparison with advanced models.

**Why this priority**: Heston is the foundation - simple, well-understood, fast. All other models build on or compare against it.

**Independent Test**: Can be tested by calibrating to BTC options IV surface and verifying RMSE < 2% for ATM options.

**Acceptance Scenarios**:

1. **Given** an IV surface from Deribit (spec 042), **When** I run Heston calibration, **Then** I receive parameters (κ, θ, σ, ρ, v₀) with RMSE reported.
2. **Given** calibrated Heston params, **When** I price a vanilla call option, **Then** price matches market within 3% for ATM strikes.
3. **Given** regime state from RegimeEnsemble, **When** calibration runs, **Then** separate parameter sets are stored per regime (P3 compliance).
4. **Given** calibration fails to converge, **When** optimizer exceeds max iterations, **Then** best-so-far params returned with warning.

**Mathematical Formulation**:
```
dS_t = μS_t dt + √v_t S_t dW¹_t
dv_t = κ(θ - v_t)dt + σ√v_t dW²_t
Corr(dW¹, dW²) = ρ
```

---

### User Story 2 - Rough Heston Calibration (Priority: P1)

As a quant, I want to calibrate Rough Heston model so I can accurately price short-dated options (< 7 days) where classical Heston underperforms.

**Why this priority**: Rough Heston is SOTA for short-term vol. Critical for crypto where weekly options are popular.

**Independent Test**: Can be tested by comparing Rough vs Classical Heston fit on 1-day ATM options, expecting Rough to have lower RMSE.

**Acceptance Scenarios**:

1. **Given** an IV surface, **When** I run Rough Heston calibration, **Then** I receive params including Hurst exponent H (expected ~0.1 for crypto).
2. **Given** short-dated options (< 7 days), **When** I compare Classical vs Rough Heston RMSE, **Then** Rough Heston RMSE is at least 30% lower.
3. **Given** H is estimated from data, **When** I price options, **Then** short-term smile dynamics are captured accurately.

**Mathematical Formulation** (Gatheral, Jaisson, Rosenbaum 2018):
```
dS_t = √v_t S_t dW_t
v_t = v₀ + (1/Γ(H+½)) ∫₀ᵗ (t-s)^(H-½) κ(θ - v_s)ds + σ ∫₀ᵗ (t-s)^(H-½) √v_s dW̃_s
```
Where H ≈ 0.1 (Hurst exponent), Γ is gamma function.

---

### User Story 3 - Rough Bergomi Model (Priority: P2)

As a quant, I want to use Rough Bergomi model for complex smile dynamics so I can price barrier options and understand vol-of-vol behavior.

**Why this priority**: More flexible than Rough Heston for exotic payoffs, but harder to calibrate. Enhancement over baseline.

**Independent Test**: Can be tested by calibrating to full IV surface including wings and verifying smile shape is captured.

**Acceptance Scenarios**:

1. **Given** an IV surface with pronounced skew, **When** I calibrate Rough Bergomi, **Then** wing IVs (25-delta put/call) fit within 5%.
2. **Given** calibrated model, **When** I simulate vol paths, **Then** paths exhibit roughness consistent with H parameter.
3. **Given** time series of IV surfaces, **When** model is re-calibrated, **Then** parameter stability is within 20% day-over-day.

**Mathematical Formulation** (Bayer, Friz, Gatheral 2016):
```
dS_t = √v_t S_t dW_t
v_t = ξ₀(t) exp(η W̃^H_t - ½η²t^(2H))
```
Where W̃^H is fractional Brownian motion with Hurst H.

---

### User Story 4 - Neural SDE for Vol Dynamics (Priority: P3)

As a researcher, I want to use Neural SDE to learn volatility dynamics directly from data without assuming a parametric form, achieving P3 (non-parametric) compliance.

**Why this priority**: Most flexible model, fully data-driven. Requires more data and compute but captures complex dynamics that parametric models miss.

**Independent Test**: Can be tested by training on 6 months of IV data and validating on held-out month, comparing to Rough Heston baseline.

**Acceptance Scenarios**:

1. **Given** 6 months of daily IV surfaces, **When** I train Neural SDE, **Then** validation loss converges within 1000 epochs.
2. **Given** trained model, **When** I generate vol forecasts, **Then** forecast RMSE is competitive with Rough Heston (<10% worse or better).
3. **Given** market regime changes, **When** model is online-updated, **Then** adaptation occurs within 5 days of new data.

**Mathematical Formulation** (Kidger 2021):
```
dX_t = f_θ(X_t, t)dt + g_θ(X_t, t)dW_t
```
Where f_θ, g_θ are neural networks with parameters θ learned from data.

---

### User Story 5 - Vol Forecasting (Priority: P2)

As a trader, I want to use calibrated models to forecast future volatility so I can make informed position sizing decisions.

**Why this priority**: Practical application of all models - converts calibration into actionable signals.

**Independent Test**: Can be tested by generating 1-day vol forecasts and comparing against realized vol over 30 days.

**Acceptance Scenarios**:

1. **Given** calibrated model (any), **When** I request vol forecast for horizon T, **Then** I receive point estimate and confidence interval.
2. **Given** Rough Heston params, **When** I forecast 1-day vol, **Then** forecast beats naive (yesterday's vol) by 10%+ RMSE.
3. **Given** regime change detected, **When** forecast is generated, **Then** regime-appropriate params are used.

---

### User Story 6 - Model Comparison Dashboard (Priority: P3)

As a quant, I want to compare all models side-by-side so I can select the best model for my use case.

**Why this priority**: Meta-feature enabling informed model selection. Enhancement after core models work.

**Independent Test**: Can be tested by running all models on same IV surface and generating comparison report.

**Acceptance Scenarios**:

1. **Given** an IV surface, **When** I run model comparison, **Then** I receive RMSE, calibration time, and parameter stability for each model.
2. **Given** comparison results, **When** I view ranking, **Then** models are sorted by user-selected metric (RMSE, speed, stability).

---

### Edge Cases

- What if IV surface has missing strikes? → Interpolate before calibration, flag as synthetic.
- What if Hurst estimation gives H > 0.5? → Clamp to [0.05, 0.5], log warning (market may be unusual).
- What if Neural SDE overfits? → Early stopping on validation loss, regularization.
- What if calibration time exceeds budget? → Return best-so-far params with timeout flag.
- How to handle negative variance (Heston)? → Use Feller condition check, absorbing boundary at v=0.

## Requirements *(mandatory)*

### Functional Requirements

**Classical Heston:**
- **FR-001**: System MUST calibrate Heston params (κ, θ, σ, ρ, v₀) from IV surface.
- **FR-002**: System MUST price vanilla calls/puts using calibrated Heston via characteristic function.
- **FR-003**: System MUST support regime-switching parameters (P3 compliance).
- **FR-004**: System MUST validate Feller condition (2κθ > σ²) and warn if violated.

**Rough Heston:**
- **FR-005**: System MUST estimate Hurst exponent H from historical vol data.
- **FR-006**: System MUST calibrate Rough Heston params including H.
- **FR-007**: System MUST price options using fractional Riccati equations (Adams scheme).
- **FR-008**: System MUST provide vol forecast with uncertainty quantification.

**Rough Bergomi:**
- **FR-009**: System MUST calibrate Rough Bergomi params (ξ₀, η, H, ρ).
- **FR-010**: System MUST simulate vol paths using hybrid scheme (exact + Euler).
- **FR-011**: System MUST price via Monte Carlo with variance reduction.

**Neural SDE:**
- **FR-012**: System MUST train drift/diffusion networks from IV time series.
- **FR-013**: System MUST support online learning for regime adaptation.
- **FR-014**: System MUST provide uncertainty estimates via ensemble or dropout.
- **FR-015**: System MUST checkpoint models for resume after interruption.

**Common:**
- **FR-016**: System MUST integrate with IV surface from spec 042.
- **FR-017**: System MUST integrate with RegimeEnsemble for regime-aware calibration.
- **FR-018**: System MUST persist calibrated params to disk.
- **FR-019**: System MUST log calibration metrics (RMSE, time, iterations).
- **FR-020**: System MUST provide CLI and Python API for all operations.

### Key Entities

- **HestonParams**: Classical Heston parameters. Attributes: kappa, theta, sigma, rho, v0, regime_state, calibration_rmse.
- **RoughHestonParams**: Rough Heston parameters. Attributes: kappa, theta, sigma, rho, v0, H (Hurst), regime_state.
- **RoughBergomiParams**: Rough Bergomi parameters. Attributes: xi0_curve, eta, H, rho, regime_state.
- **NeuralSDEModel**: Trained neural network model. Attributes: drift_network, diffusion_network, training_loss, validation_loss.
- **VolForecast**: Volatility forecast output. Attributes: timestamp, horizon, point_estimate, lower_bound, upper_bound, model_used.
- **CalibrationResult**: Output of any calibration. Attributes: model_type, params, rmse, calibration_time_ms, converged, iterations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Classical Heston calibration RMSE < 2% for ATM, < 5% for 25-delta options.
- **SC-002**: Rough Heston calibration RMSE < 1.5% for ATM on <7 day options (30% improvement over Classical).
- **SC-003**: Rough Bergomi captures smile wings within 5% RMSE.
- **SC-004**: Neural SDE validation loss converges within 1000 epochs.
- **SC-005**: Classical Heston calibration completes in < 2 seconds.
- **SC-006**: Rough Heston calibration completes in < 15 seconds.
- **SC-007**: Vol forecast beats naive baseline by 10%+ RMSE over 30-day test.
- **SC-008**: Regime-switching params improve overall RMSE by 5%+ vs single-regime.

## Scope

### In Scope

- Classical Heston: calibration, pricing, regime-switching
- Rough Heston: calibration, pricing, Hurst estimation, vol forecasting
- Rough Bergomi: calibration, Monte Carlo pricing, path simulation
- Neural SDE: training, inference, online learning
- Integration with spec 042 (IV surface)
- Integration with spec 036 (RegimeEnsemble)
- CLI interface
- Python API

### Out of Scope

- SABR model (defer to future spec if needed)
- Jump-diffusion models (Merton, Bates)
- Multi-asset correlation models (Wishart)
- GPU acceleration (CPU sufficient for calibration frequency)
- Real-time streaming calibration (batch is sufficient)

## Assumptions

- IV surface data available from spec 042 implementation.
- RegimeEnsemble available from spec 036 implementation.
- Training data for Neural SDE: minimum 6 months of daily IV surfaces.
- Calibration frequency: daily or on-demand (not real-time).
- scipy.optimize sufficient for Heston calibration (no need for custom optimizers).

## Dependencies

- `specs/042-deribit-options-data/` - IV surface input
- `specs/036-regime-ensemble/` - Regime state for switching
- scipy - Optimization routines
- numpy - Numerical computation
- torch (optional) - Neural SDE training

## Technical Notes

### Classical Heston Characteristic Function

```python
def heston_char_func(u, params, T):
    """Heston characteristic function for pricing via FFT."""
    kappa, theta, sigma, rho, v0 = params
    d = np.sqrt((rho*sigma*1j*u - kappa)**2 + sigma**2*(1j*u + u**2))
    g = (kappa - rho*sigma*1j*u - d) / (kappa - rho*sigma*1j*u + d)
    C = kappa*theta/sigma**2 * ((kappa - rho*sigma*1j*u - d)*T - 2*np.log((1-g*np.exp(-d*T))/(1-g)))
    D = (kappa - rho*sigma*1j*u - d)/sigma**2 * (1-np.exp(-d*T))/(1-g*np.exp(-d*T))
    return np.exp(C + D*v0)
```

### Rough Heston Adams Scheme

For fractional Riccati equation, use Adams scheme from El Euch & Rosenbaum (2019):
- Discretize convolution integral
- Use predictor-corrector for stability
- Reference: `VolatilityIsMostlyRough` paper

### Neural SDE Architecture

```python
class NeuralSDE(nn.Module):
    def __init__(self, hidden_dim=64):
        self.drift_net = nn.Sequential(
            nn.Linear(2, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, 1)
        )
        self.diffusion_net = nn.Sequential(
            nn.Linear(2, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, 1), nn.Softplus()  # Ensure positive
        )
```

## References

1. Heston (1993) - "A Closed-Form Solution for Options with Stochastic Volatility"
2. Gatheral, Jaisson, Rosenbaum (2018) - "Volatility is Rough"
3. Bayer, Friz, Gatheral (2016) - "Pricing under Rough Volatility"
4. El Euch, Rosenbaum (2019) - "The characteristic function of rough Heston models"
5. Kidger (2021) - "On Neural Differential Equations" (PhD Thesis)
