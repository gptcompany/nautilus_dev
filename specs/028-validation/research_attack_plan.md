# Research Attack Plan: Five Pillars Reality Check

**Date**: 2026-01-04
**Author**: Claude (Validation Analysis)
**Status**: CRITICAL - Foundational Philosophy Validation
**Purpose**: Honest assessment of where we violate our own principles

---

## Executive Summary

**THE BRUTAL TRUTH**: Our "adaptive, non-parametric" system has **42 parameters**. We claim to follow natural laws but built an optimization engine. The Moroder+Dilla analogy is beautiful but **UNPROVEN**. We need to stop, measure, and decide if we're building science or fantasy.

**Current State**:
- ✅ **Philosophy**: Five Pillars are sound principles
- ⚠️ **Architecture**: 4.5/8 JFDS coverage (partial alignment)
- ❌ **Implementation**: 42 params violates P3 (Non Parametrico)
- ❌ **Validation**: Zero OOS evidence, zero baseline comparisons
- ❌ **Measurement**: Assuming superiority without proof

**Verdict**: **WAIT** - We need 2-4 weeks of empirical validation before any deployment.

---

## I. CONTRADDIZIONI IDENTIFICATE

### Contraddizione 1: "Non-Parametrico" con 42 Parametri

**Pilastro Violato**: P3 (Non Parametrico)

**La Filosofia Dice**:
> "Parameters adapt to data, not fixed parameters. Default values are STARTING POINTS, not gospel."

**La Realtà È**:
- SOPS: 8 parameters (k_base, k_adaptive, vol_lookback, smoothing_alpha, etc.)
- Thompson Sampling: 6 parameters (decay, min_samples, beta priors, etc.)
- Regime Detection: 8 parameters (FFT window, IIR cutoffs, spectral thresholds)
- Meta Portfolio: 15 parameters (activation thresholds, deactivation, PID gains)
- **TOTALE: ~42 parametri fissi o semi-adattivi**

**L'Evidenza Accademica**:
- Bailey: 3-5 parameters = safe budget
- DeMiguel: Need 3000 months for 25-asset optimization to beat 1/N
- **Noi**: 42 params, 60 months data = **14% del necessario**

**È Veramente Contraddittorio?**: **SÌ**

Molti parametri hanno valori di default fissi (es. PID gains: Kp=2.0, Ki=0.1, Kd=0.5). Non si adattano ai dati, si adattano solo quando *noi* li cambiamo dopo aver analizzato i risultati (= overfitting manuale).

**Azione Richiesta**:
1. Classificare parametri: FISSI vs ADATTIVI vs IBRIDI
2. Per ogni FISSO: Giustificare con teoria o misura empirica
3. Per ogni ADATTIVO: Provare che l'adattamento migliora OOS
4. **Target**: Ridurre a <10 parametri documentati

---

### Contraddizione 2: "Probabilistico" ma Deterministico in Pratica

**Pilastro Violato**: P1 (Probabilistico)

**La Filosofia Dice**:
> "Not predictions, but probability distributions."

**La Realtà È**:
- Thompson Sampling emette **punto stimato** (non distribuzione)
- Regime Detector emette **BULL/BEAR/SIDEWAYS** (non probabilità)
- Meta Controller prende **decisioni binarie** (trade/no trade)

**È Veramente Contraddittorio?**: **PARZIALE**

Thompson Sampling *mantiene* una distribuzione posteriore (Beta), ma l'output finale è un singolo valore. Regime detection potrebbe emettere P(BULL)=0.6, P(BEAR)=0.3, P(SIDEWAYS)=0.1, ma attualmente emette solo "BULL".

**Azione Richiesta**:
1. Modificare regime detection per emettere **probability vector**
2. Meta Controller usa **expected value** su distribuzione
3. Quantificare **uncertainty** in ogni decisione (es. confidence intervals)
4. Report metrics: Non solo Sharpe, ma **probabilità di Sharpe < 0.5**

---

### Contraddizione 3: "Leggi Naturali" senza Misure Empiriche

**Pilastro Violato**: P5 (Leggi Naturali)

**La Filosofia Dice**:
> "Fibonacci, fractals, wave physics, flow dynamics."

**La Realtà È**:
- FlowPhysics (Navier-Stokes): **EXPERIMENTAL** (nessuna validazione)
- VibrationAnalysis (harmonics): **EXPERIMENTAL** (nessuna validazione)
- UniversalLaws (Fibonacci, Gann): **EXPERIMENTAL** (CLAUDE.md warns "weak evidence")
- TapeSpeed (Poisson lambda): Theoretically sound, **ma non testato OOS**

**È Veramente Contraddittorio?**: **SÌ**

Non puoi invocare "leggi naturali" senza misurare se i mercati *effettivamente* seguono quelle leggi. Fibonacci è bello, ma i prezzi non sanno contare.

**Azione Richiesta**:
1. **Misura**: Fibonacci retracements predictano reversal meglio di random?
2. **Misura**: Vibration harmonics correlano con volatility spikes?
3. **Misura**: Navier-Stokes flow analogy batte simple momentum?
4. **Se NO**: Rimuovere o marcare come "speculativo, non per produzione"

---

### Contraddizione 4: Moroder+Dilla Analogy - Poetico ma Impreciso

**Pilastro Violato**: Nessuno (è un'analogia, non un pilastro)

**L'Analogia Dice**:
- Moroder (Disco) = Griglia temporale regolare, beat fisso → Trend following
- Dilla (Hip-hop) = Swing quantize, off-grid → Mean reversion

**La Realtà È**:
- Trend following ≠ "griglia regolare" (adapts to volatility, regime changes)
- Mean reversion ≠ "swing quantize" (ha propri criteri di timing)
- L'analogia è **metaforica**, non **matematica**

**È Utile?**: **SÌ, come comunicazione**, **NO come design principle**

**Azione Richiesta**:
- Mantenere analogia per spiegare concetti
- **NON usare** come giustificazione per scelte architetturali
- Validare componenti con **misure empiriche**, non con metafore

---

## II. COSA È VERAMENTE MISURABILE

### Metriche di Livello 1: Sempre Misurabili (No Assumptions)

| Metrica | Definizione | Perché È Oggettiva |
|---------|-------------|-------------------|
| **Raw Sharpe Ratio** | (Return - RFR) / StdDev | Matematicamente definito, nessun parametro |
| **Maximum Drawdown** | max(Peak - Trough) / Peak | Osservabile direttamente |
| **Win Rate** | #Wins / #Trades | Conteggio discreto |
| **Turnover** | Σ abs(Δposition) / T | Misura diretta |
| **Transaction Costs** | Turnover × spread/slippage | Osservabile via exchange API |
| **Calmar Ratio** | Return / MaxDD | Derivato da metriche L1 |

**Azione**: Riportare SEMPRE queste metriche per ogni esperimento.

---

### Metriche di Livello 2: Misurabili con Metodo (1 Assumption)

| Metrica | Assunzione | Perché È Comunque Utile |
|---------|------------|-------------------------|
| **Deflated Sharpe Ratio** | Selection bias via √(log N) | Bailey validated su dataset reali |
| **95% Confidence Interval** | Gaussian returns | Robustezza: usa bootstrap se necessario |
| **Kelly Fraction** | Stazionarietà di p, b | Valida per finestre brevi (90 giorni) |
| **Volatility (realized)** | Lookback window | Observable, parametro = window size |

**Azione**: Riportare L2 con **disclosure esplicita** dell'assunzione.

---

### Metriche di Livello 3: Non Misurabili (Multiple Assumptions)

| Metrica | Perché NON È Oggettiva | Alternative |
|---------|------------------------|-------------|
| **"Harmony" Score** | Arbitrary 0-100 scale | Usa correlation spike metric |
| **"Health" Polyvagal** | Ventral/Sympathetic thresholds arbitrari | Usa drawdown % + volatility ratio |
| **Regime "BULL/BEAR"** | Discrete labels su mercati continui | Usa probability vector |
| **"Flow Velocity"** | Navier-Stokes mapping non validato | Usa volume/price momentum |

**Azione**: **Eliminare** L3 metrics da produzione, **sostituire** con L1/L2.

---

### Test Empirici Obbligatori (Prima di Paper Trading)

| # | Test | Input | Output | Soglia GO/STOP |
|---|------|-------|--------|----------------|
| 1 | **Baseline Comparison** | SOPS vs 1/N vs Fixed 2% | Sharpe, MaxDD | Complex > Simple + 0.3 Sharpe |
| 2 | **Walk-Forward (12 windows)** | Expanding train, OOS test | Median OOS Sharpe | OOS > 0.5 × IS Sharpe |
| 3 | **Parameter Sensitivity** | ±5% ogni parametro | Δ Sharpe % | Nessun param con Δ > 20% |
| 4 | **Regime Conditional** | Performance in BULL/BEAR/SIDEWAYS | Sharpe per regime | Sharpe > 0 in tutti i regimi |
| 5 | **Transaction Cost Impact** | Turnover × 5 bps | Net Sharpe | Net > baseline |
| 6 | **Correlation Spike Stress** | Simulate ρ → 0.98 | MaxDD increase | DD < 2× normale |

**Red Line**: Se **qualsiasi test** fallisce → **STOP** e semplifica.

---

## III. IPOTESI DA TESTARE

### H1: Complessità Non Giustificata (DeMiguel Hypothesis)

**Ipotesi Nulla (H0)**: "Il nostro sistema a 42 parametri batte 1/N (0 parametri) OOS."

**Test Methodology**:
1. Split data: Train (2020-2022), Validate (2023), Test (2024)
2. Run Complex System su Train → Sharpe_C_train
3. Run 1/N su Train → Sharpe_1N_train
4. Test entrambi su Test set → Sharpe_C_test, Sharpe_1N_test
5. **Compute**: Δ = Sharpe_C_test - Sharpe_1N_test

**Decision Rule**:
- Se Δ < 0: **REJECT H0** → 1/N vince, semplifica
- Se 0 < Δ < 0.2: **REJECT H0** (robustness premium) → usa 1/N
- Se Δ > 0.3: **ACCEPT H0** → complessità giustificata

**Probabilità di Successo**: <25% (based on DeMiguel 2009 findings)

**Implicazioni se H1 Confermata**:
- Scrap 42-param system
- Deploy 1/N or simple trend (3 params)
- Save months of development time

---

### H2: OOS Sharpe Decay = 40-60% (Wiecki Hypothesis)

**Ipotesi Nulla (H0)**: "OOS Sharpe ≥ 60% del backtest Sharpe."

**Test Methodology**:
1. Backtest Sharpe (current): 1.85
2. Deflate per selection bias: 1.85 × 0.75 = 1.39
3. Walk-forward 12 windows → Median OOS Sharpe
4. **Compute**: Decay = 1 - (OOS / 1.39)

**Decision Rule**:
- Se Decay > 60%: **REJECT H0** → overfitting confermato
- Se 40% < Decay < 60%: **BORDERLINE** → ridurre parametri
- Se Decay < 40%: **ACCEPT H0** → sistema robusto

**Probabilità di Successo**: <30% (Wiecki: median = 50% decay)

**Implicazioni se H2 Confermata**:
- Expected OOS Sharpe = 1.39 × 0.4 = **0.56**
- Baseline (Fixed 2%) likely = **0.9**
- **Complex underperforms simple by -0.34 Sharpe**

---

### H3: Giller Scaling Superiore a Lineare (Power-Law Hypothesis)

**Ipotesi Nulla (H0)**: "signal^0.5 (Giller) > signal^1.0 (linear) OOS."

**Test Methodology**:
1. Test scaling exponents: {0.3, 0.5, 0.7, 1.0}
2. Run backtest con ognuno (same data)
3. Walk-forward validation → OOS Sharpe per exponent
4. **Compute**: Best exponent = argmax(OOS Sharpe)

**Decision Rule**:
- Se Best ≈ 0.5: **ACCEPT H0** → Giller validato
- Se Best ≠ 0.5: **REJECT H0** → usa empirical best
- Se Best = 1.0: **REJECT H0** → linear wins, no power law

**Probabilità di Successo**: 40% (niche method, limited validation)

**Implicazioni se H3 Confermata**:
- Giller scaling è overfitting, non natural law
- Sostituire con linear o empirical exponent
- Rimuovere "natural law" claim per sizing

---

### H4: Regime Detection Aggiunge Valore (Regime Hypothesis)

**Ipotesi Nulla (H0)**: "Sistema con regime detection > sistema senza regime detection."

**Test Methodology**:
1. **Version A**: Full system con IIR+Spectral regime detection
2. **Version B**: Same system, ma regime = "NORMAL" always (no detection)
3. Run entrambi su walk-forward 12 windows
4. **Compute**: Δ Sharpe = A_OOS - B_OOS

**Decision Rule**:
- Se Δ < 0: **REJECT H0** → rimuovi regime detection
- Se 0 < Δ < 0.1: **REJECT H0** (non vale la complessità)
- Se Δ > 0.2: **ACCEPT H0** → regime detection validated

**Probabilità di Successo**: 50% (regime detection ha mixed evidence)

**Implicazioni se H4 Confermata**:
- Rimuovere IIR, Spectral, Multi-dimensional
- Risparmio: ~20 parametri
- Simplify a simple volatility scaling

---

### H5: CSRC Previene Correlation Spikes (Correlation Hypothesis)

**Ipotesi Nulla (H0)**: "Sistema con CSRC < MaxDD durante correlation spike vs without."

**Test Methodology**:
1. Simulate correlation spike: ρ(strategies) → 0.98
2. **Version A**: Current system (no CSRC)
3. **Version B**: System con CSRC covariance penalty
4. **Compute**: MaxDD_A vs MaxDD_B durante spike

**Decision Rule**:
- Se MaxDD_B < 0.5 × MaxDD_A: **ACCEPT H0** → CSRC critico
- Se MaxDD_B < 0.75 × MaxDD_A: **ACCEPT H0** (improvement)
- Se MaxDD_B ≈ MaxDD_A: **REJECT H0** → CSRC inutile

**Probabilità di Successo**: 70% (Varlashova 2025 validated)

**Implicazioni se H5 Confermata**:
- Add CSRC (HIGH priority gap)
- Expect MaxDD reduction: -50% → -25% durante spike

---

## IV. PIANO DI RICERCA

### Settimana 1: Baseline Reality Check (4-6 gennaio)

**Obiettivo**: Sapere se la complessità è giustificata.

| Giorno | Task | Deliverable | Time | Owner |
|--------|------|-------------|------|-------|
| **Lun 6** | Implement Fixed Fractional (f=0.02) | `fixed_fractional_sizer.py` | 1h | Dev |
| **Lun 6** | Implement Equal Weight (1/N) | `equal_weight_allocator.py` | 30m | Dev |
| **Mar 7** | Implement Simple Trend (AQR style) | `simple_trend_system.py` | 4h | Dev |
| **Mar 7** | Implement Vol Targeting | `volatility_targeter.py` | 2h | Dev |
| **Mer 8** | Run all baselines + complex su same data | Backtest results CSV | 4h | Dev |
| **Gio 9** | Analyze results, compute DSR | Comparison report MD | 3h | Analyst |
| **Ven 10** | **GO/WAIT/STOP Decision Meeting** | Decision document | 2h | Team |

**Criteri di Successo**:
- ✅ Tutti i baselines implementati e testati
- ✅ Comparison report con Sharpe, MaxDD, Calmar, turnover
- ✅ Deflated Sharpe Ratio calcolato
- ✅ Decision: GO (complex wins by >0.3), WAIT (borderline), STOP (simple wins)

**Output Milestone**: `baseline_comparison_results.md` + GO/WAIT/STOP verdict

---

### Settimana 2: Validation Suite (13-17 gennaio)

**Obiettivo**: Validare robustezza del sistema (se WAIT/GO da Week 1).

| Giorno | Task | Deliverable | Time | Owner |
|--------|------|-------------|------|-------|
| **Lun 13** | Walk-forward setup (12 windows) | `walk_forward_config.json` | 2h | Dev |
| **Lun 13** | Run walk-forward backtest | OOS results per window | 6h | Compute |
| **Mar 14** | Parameter sensitivity analysis (42 params × ±5%) | Sensitivity matrix CSV | 8h | Compute |
| **Mer 15** | Regime-conditional testing (BULL/BEAR/SIDEWAYS) | Regime breakdown MD | 4h | Analyst |
| **Gio 16** | Transaction cost impact analysis | Net Sharpe with costs | 3h | Analyst |
| **Ven 17** | Synthesize validation report | `validation_report.md` | 4h | Analyst |
| **Ven 17** | **Second GO/WAIT/STOP Decision** | Final verdict | 2h | Team |

**Criteri di Successo**:
- ✅ Median OOS Sharpe > 0.7 (50% of IS)
- ✅ No parameter with >20% Sharpe sensitivity to ±5% change
- ✅ Positive Sharpe in all 3 regimes
- ✅ Net Sharpe (after costs) > baseline

**Output Milestone**: `validation_report.md` + GO/STOP verdict

---

### Settimana 3: Critical Gaps (20-24 gennaio)

**Obiettivo**: Chiudere HIGH priority gaps (se GO da Week 2).

| Giorno | Task | Deliverable | Time | Owner |
|--------|------|-------------|------|-------|
| **Lun 20** | Implement CSRC covariance penalty | `csrc_allocator.py` | 8h | Dev |
| **Mar 21** | Implement Long/Short separation (JFDS) | `dual_meta_model.py` | 12h | Dev |
| **Mer 22** | Test CSRC stress (correlation spike) | Stress test results | 4h | Analyst |
| **Gio 23** | Test Long/Short improvement | Sharpe delta | 4h | Analyst |
| **Ven 24** | Integrate + re-run validation suite | Updated validation report | 6h | Team |

**Criteri di Successo**:
- ✅ CSRC reduces correlation spike DD by >30%
- ✅ Long/Short improves Sharpe by >0.1
- ✅ No new bugs introduced

**Output Milestone**: `gap_closure_report.md` + Updated system

---

### Settimana 4: Paper Trading Prep (27-31 gennaio)

**Obiettivo**: Preparare sistema per paper trading (se GO da Week 3).

| Giorno | Task | Deliverable | Time | Owner |
|--------|------|-------------|------|-------|
| **Lun 27** | Fix API bug (alpha_evolve_bridge.py) | Bug fix commit | 2h | Dev |
| **Lun 27** | Add NaN input guards | Defensive coding PR | 3h | Dev |
| **Mar 28** | Implement kill switches | `circuit_breaker.py` | 4h | Dev |
| **Mer 29** | Paper trading config + monitoring | Config + Grafana dashboards | 6h | Ops |
| **Gio 30** | Dry-run paper trading (simulated) | Dry-run report | 4h | QA |
| **Ven 31** | **Paper Trading GO/NO-GO** | Launch decision | 2h | Team |

**Criteri di Successo**:
- ✅ Zero CRITICAL bugs
- ✅ Kill switches tested
- ✅ Monitoring functional
- ✅ Team confident in system behavior

**Output Milestone**: Paper trading launch or STOP decision

---

## V. CRITERI DI SUCCESSO/FALLIMENTO

### Livello 1: STOP Immediato (Red Lines)

Se **qualsiasi** di questi si verifica → **STOP ALL DEVELOPMENT**:

| # | Red Line | Misurato Come | Threshold |
|---|----------|---------------|-----------|
| R1 | **1/N beats complex OOS** | Sharpe_1N > Sharpe_Complex | ANY |
| R2 | **Fixed 2% beats complex after costs** | Net Sharpe_Fixed > Net Sharpe_Complex | ANY |
| R3 | **Parameter fragility** | Nessun param tolera ±5% senza >20% Sharpe drop | ANY param |
| R4 | **Negative Sharpe in any regime** | Sharpe(BULL/BEAR/SIDEWAYS) < 0 | ANY regime OOS |
| R5 | **Catastrophic OOS decay** | OOS Sharpe < 0.3 | Absolute |
| R6 | **Transaction cost erosion** | Net Sharpe < 0.5 | Absolute |

**Azione se R1-R6**: Abandon complex system, deploy simple baseline.

---

### Livello 2: WAIT (Fix Required)

Se **2+ di questi** si verificano → **WAIT, non lanciare**:

| # | Yellow Flag | Misurato Come | Threshold |
|---|-------------|---------------|-----------|
| Y1 | **Borderline OOS performance** | 0.3 < OOS Sharpe < 0.7 | Mid-range |
| Y2 | **Moderate parameter sensitivity** | 10-20% Sharpe drop su ±5% change | 5+ params |
| Y3 | **Regime instability** | Sharpe variance across regimes > 1.0 | Std(regime Sharpe) |
| Y4 | **High turnover** | Annual turnover > 300% | Computed |
| Y5 | **Wins by <0.2 Sharpe vs baseline** | Δ Sharpe = 0.1-0.2 | Marginal |

**Azione se Y1-Y5**: Fix issues (reduce params, add CSRC, tune), re-validate.

---

### Livello 3: GO (Conditional Launch)

Se **tutti** questi sono veri → **GO to paper trading**:

| # | Green Light | Misurato Come | Threshold |
|---|-------------|---------------|-----------|
| G1 | **Beats baselines convincingly** | Δ Sharpe > 0.3 vs best baseline | OOS |
| G2 | **Robust OOS performance** | OOS Sharpe > 0.7 | Median walk-forward |
| G3 | **Parameter stability** | All params tolerate ±5% con <10% Sharpe drop | All 42 params |
| G4 | **Regime consistency** | Sharpe > 0.3 in tutti i regimi | BULL/BEAR/SIDEWAYS |
| G5 | **Cost-adjusted positive** | Net Sharpe > 0.8 | After 5 bps costs |
| G6 | **Critical gaps closed** | CSRC + Long/Short implemented | Code review |
| G7 | **Zero CRITICAL bugs** | No API mismatches, no NaN crashes | QA pass |

**Azione se G1-G7**: Launch paper trading con tight risk limits (0.5% max position).

---

## VI. RISPOSTA ALLE DOMANDE CHIAVE

### 1. What is TRULY "non-parametric" vs what requires parameters?

**Truly Non-Parametric** (allineato con P3):
- ✅ **Volatility-adaptive K** (SOPS): k = f(realized_vol / baseline_vol)
- ✅ **Thompson Sampling** (Bayesian updates): α, β updated online
- ✅ **Particle Filter** (resampling): Weights updated based on performance
- ✅ **IIR Regime Detector** (O(1) filter): No lookback, recursive

**Requires Fixed Parameters** (violazione P3):
- ❌ PID gains (Kp=2.0, Ki=0.1, Kd=0.5): Hardcoded
- ❌ Regime thresholds (ventral=70, sympathetic=40): Arbitrary
- ❌ Spectral window (256 samples): Fixed lookback
- ❌ Giller exponent (0.5): Not empirically validated

**Verdict**: System is ~60% adaptive, ~40% parametric (non al 100% "non-parametric").

---

### 2. Is Moroder+Dilla direction correct or are we fooling ourselves?

**Correct**:
- ✅ Conceptually: Griglia (trend) vs swing (mean-reversion) è valido
- ✅ Comunicazione: Analogia aiuta spiegare concetti a non-tecnici

**Fooling Ourselves**:
- ❌ Non è una base di design: I mercati non "ascoltano" Moroder/Dilla
- ❌ Non sostituisce empirical validation: Metafore ≠ misure
- ❌ Rischio: Usare analogia per giustificare scelte non validate

**Verdict**: Mantenere come **analogia didattica**, NON come **principio architetturale**.

---

### 3. What can we MEASURE vs what are we ASSUMING?

**Possiamo Misurare** (L1 metrics):
- Sharpe, MaxDD, Win Rate, Turnover, Calmar
- OOS performance (walk-forward)
- Parameter sensitivity (±5% stress test)
- Transaction cost impact (turnover × spread)
- Correlation spike stress (simulate ρ → 0.98)

**Stiamo Assumendo** (unvalidated):
- Giller exponent = 0.5 è ottimale (no test)
- Regime detection aggiunge valore (no ablation study)
- Polyvagal health mapping è predittivo (no validation)
- Flow physics analogy vale (no empirical test)
- 42 params non overfittano (no walk-forward yet)

**Verdict**: **STOP ASSUMING, START MEASURING**. Run H1-H5 tests.

---

### 4. What is the MINIMUM viable system aligned with 5 Pillars?

**Minimal System** (5 params, allineato ai 5 Pillars):

```python
class MinimalAdaptiveSystem:
    """
    P1 Probabilistico: Thompson Sampling (Bayesian)
    P2 Non Lineare: Giller signal^0.5 (power-law)
    P3 Non Parametrico: Vol-adaptive sizing
    P4 Scalare: O(1) filters, no lookback
    P5 Leggi Naturali: ATR (price movement physics)
    """
    def __init__(self):
        self.target_vol = 0.10           # P3: Adaptive to realized vol (param 1)
        self.vol_lookback = 20           # P4: Fixed small lookback (param 2)
        self.giller_exponent = 0.5       # P2: Power-law (param 3)
        self.kelly_fraction = 0.25       # P1: Fractional Kelly (param 4)
        self.stop_pct = 0.02             # P5: Natural risk limit (param 5)

    def size(self, signal, equity, realized_vol, win_rate, payoff_ratio):
        # P1: Probabilistic Kelly
        f_kelly = (win_rate * payoff_ratio - (1 - win_rate)) / payoff_ratio
        f_kelly = max(0, min(0.5, f_kelly))

        # P2: Non-Linear Giller scaling
        signal_scaled = np.sign(signal) * (abs(signal) ** self.giller_exponent)

        # P3: Vol-adaptive
        vol_scale = self.target_vol / realized_vol if realized_vol > 0 else 1.0

        # Combine
        position_size = self.kelly_fraction * f_kelly * signal_scaled * vol_scale * equity

        # P5: Natural stop-loss
        return position_size if abs(position_size / equity) < self.stop_pct else 0
```

**Parameters**: 5 (vs 42 current)
**Expected Performance**: ~0.8-1.1 Sharpe (similar to simple baselines)
**Robustness**: HIGH (8x fewer params)

**Verdict**: Se validation fallisce, deploy questo invece del sistema a 42 params.

---

## VII. FINAL RECOMMENDATIONS

### Immediate (This Week)

1. ✅ **Implement baselines** (1/N, Fixed 2%, Simple Trend, Vol Target)
2. ✅ **Run comparative backtests** (same data, same costs)
3. ✅ **Compute Deflated Sharpe Ratio**
4. ✅ **GO/WAIT/STOP decision** (Fri Jan 10)

### If WAIT/GO (Week 2-4)

5. ✅ **Walk-forward validation** (12 windows)
6. ✅ **Parameter sensitivity** (42 params × ±5%)
7. ✅ **Add CSRC + Long/Short**
8. ✅ **Fix CRITICAL bugs**
9. ✅ **Paper trading prep**

### If STOP (Any Time)

10. ✅ **Deploy simple baseline** (1/N or Fixed 2% or Simple Trend)
11. ✅ **Archive complex system** for research
12. ✅ **Document lessons learned**

---

## VIII. ACCOUNTABILITY

**This plan commits to**:

1. **Measuring, not assuming**: Every claim validated empirically
2. **Baselines first**: No deployment without comparison to simple alternatives
3. **Red lines respected**: STOP if any R1-R6 triggered
4. **Honest reporting**: DSR, not raw Sharpe; OOS, not in-sample

**Success = Learning**, not defending our work.

**If simple beats complex**: We WIN by saving time and avoiding losses.
**If complex beats simple**: We WIN by validating our approach.

**Either way: We WIN by being HONEST.**

---

**Document Version**: 1.0
**Next Review**: Jan 10, 2026 (after baseline comparison)
**Status**: ACTIVE - Week 1 starting Jan 6

**Prepared by**: Claude (Validation Agent)
**Reviewed by**: [Pending]
**Approved for Execution**: [Pending]
