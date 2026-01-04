# Adaptive Control Framework - Documento Finale

> **"La gabbia la creiamo noi, non il sistema"**

## I Cinque Pilastri

| Pilastro | Significato | Implementazione |
|----------|-------------|-----------------|
| **Probabilistico** | Distribuzioni, non predizioni | Thompson Sampling, Particle Filter, Entropy |
| **Non Lineare** | Power laws, non scaling lineare | Giller (signal^0.5), SOPS (tanh) |
| **Non Parametrico** | Adattivo ai dati, niente fisso | k_adaptive, λ_adaptive, thresholds dinamici |
| **Scalare** | Funziona a qualsiasi scala | O(1) filters, ratios invarianti |
| **Leggi Naturali** | Fibonacci, frattali, onde, flussi | Wave physics, Flow dynamics |

---

## Architettura Completa

```
                         TU (Review settimanale)
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              HARD LIMITS          KILL SWITCH
            (max DD -20%)         (daily loss -5%)
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    ┌─────────────────────┐
                    │   META-PORTFOLIO    │
                    │  (Thompson + Giller)│
                    └─────────┬───────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
      System A           System B           System C
    (VDD-based)        (Momentum)        (Mean Rev)
           │                  │                  │
           └──────────────────┼──────────────────┘
                              ▼
                    ┌─────────────────────┐
                    │   SIGNAL PIPELINE   │
                    │                     │
                    │  signal (raw)       │
                    │      │              │
                    │      ▼ SOPS         │
                    │  direction=tanh(k×s)│
                    │      │              │
                    │      ▼ GILLER       │
                    │  size=|dir|^0.5     │
                    │      │              │
                    │      ▼ TAPE SPEED   │
                    │  final=size×λ_weight│
                    └─────────────────────┘
```

---

## Moduli Creati

### Core (Usa questi)

| Modulo | Scopo | Complessità |
|--------|-------|-------------|
| `sops_sizing.py` | SOPS + Giller + TapeSpeed | ★☆☆ Semplice |
| `dsp_filters.py` | IIR, Kalman, O(1) filters | ★☆☆ Semplice |
| `luck_skill.py` | Lopez de Prado luck quantification | ★☆☆ Semplice |
| `meta_portfolio.py` | Thompson + Particle ensemble | ★★☆ Medio |

### Avanzati (Per dopo)

| Modulo | Scopo | Complessità |
|--------|-------|-------------|
| `meta_controller.py` | Orchestrazione polyvagal | ★★★ Complesso |
| `alpha_evolve_bridge.py` | Trigger evoluzione strategie | ★★★ Complesso |
| `flow_physics.py` | Market come fluido | ★★☆ Medio |
| `information_theory.py` | Entropy, SNR | ★★☆ Medio |

---

## Pipeline di Position Sizing

```python
from strategies.common.adaptive_control import SOPSGillerSizer

# Crea sizer
sizer = SOPSGillerSizer(base_size=1000.0)

# Ogni bar
size = sizer.calculate(
    signal=vdd_signal,        # Il tuo segnale VDD (-1 a +1)
    volatility=current_vol,    # Volatilità attuale
    tape_speed=trades_per_sec, # Velocità del tape
)

# size è già:
# - Bounded (SOPS)
# - Non-lineare (Giller)
# - Adattato a tape speed
```

---

## Tape Speed (λ Poisson)

```
VELOCITÀ DEL TAPE = TASSO DI ARRIVO ORDINI
═══════════════════════════════════════════

λ alto (fast tape):
├── Molti ordini/secondo
├── Alta attività
├── Momentum probabile
└── → Aumenta sizing se signal forte

λ basso (slow tape):
├── Pochi ordini/secondo
├── Bassa attività
├── Mean reversion probabile
└── → Riduci sizing, aspetta

FORMULA:
λ_smooth = α × trades_this_second + (1-α) × λ_prev
```

---

## Luck vs Skill (Lopez de Prado)

```python
from strategies.common.adaptive_control import TrackRecordAnalyzer

# Traccia performance
analyzer = TrackRecordAnalyzer(n_strategies_tested=10)

# Ogni giorno
analyzer.add_return(daily_return)

# Check periodico
print(analyzer.get_report())

# Output:
# PROBABILITY OF LUCK: 35%
# MIN TRACK RECORD: 18 months to prove skill
# VERDICT: UNCERTAIN
```

---

## Piano Operativo

### FASE 1: Paper Trading (3 mesi)

```python
# Sistema minimo
from strategies.common.adaptive_control import (
    SOPSGillerSizer,
    IIRRegimeDetector,
    TrackRecordAnalyzer,
)

class Phase1System:
    def __init__(self):
        self.sizer = SOPSGillerSizer(base_size=1000)
        self.regime = IIRRegimeDetector()
        self.luck = TrackRecordAnalyzer(n_strategies_tested=5)
        self.max_dd = 0.15  # HARD LIMIT

    def on_bar(self, bar, vdd_signal):
        # Hard stop
        if self.current_drawdown > self.max_dd:
            return 0

        # Regime
        regime = self.regime.update(bar.return_)
        regime_weight = 0.5 if regime == "unknown" else 1.0

        # Size
        size = self.sizer.calculate(
            signal=vdd_signal,
            volatility=bar.volatility,
            tape_speed=bar.trades_per_second,
        )

        return size * regime_weight
```

### FASE 2: Small Live (3 mesi)
- Stesso sistema
- 1-5% del capitale
- Raccogli dati REALI
- Verifica luck vs skill

### FASE 3: Scale Up (se skill > luck)
- Aggiungi MetaPortfolio
- Multi-system se necessario
- Incrementa capitale gradualmente

---

## Hard Limits (NON NEGOZIABILI)

```python
HARD_LIMITS = {
    "max_daily_loss": -0.05,      # -5% → STOP
    "max_weekly_loss": -0.10,     # -10% → STOP
    "max_drawdown": -0.20,        # -20% → STOP
    "max_position_pct": 0.10,     # Max 10% per trade
    "max_leverage": 3.0,          # Mai oltre 3x
    "min_cash": 0.20,             # 20% sempre liquido
}
```

---

## Riferimenti

- **Giller (2020)**: Adventures in Financial Data Science - Power law sizing
- **Lopez de Prado (2018)**: Advances in Financial ML - Luck quantification
- **Cover (1991)**: Universal Portfolios - Lambda system
- **Thompson (1933)**: Thompson Sampling - Bayesian selection
- **Almgren-Chriss (2001)**: Optimal Execution - Market impact

---

## File Structure

```
strategies/common/adaptive_control/
├── __init__.py                 # 55+ exports
├── sops_sizing.py             # ★ SOPS + Giller + TapeSpeed
├── dsp_filters.py             # ★ O(1) filters
├── luck_skill.py              # ★ Lopez de Prado
├── meta_portfolio.py          # Thompson + Particle ensemble
├── meta_controller.py         # Orchestrazione
├── alpha_evolve_bridge.py     # Evolution trigger
├── multi_dimensional_regime.py # Consensus detection
├── flow_physics.py            # Market as fluid
├── vibration_analysis.py      # Cycles, harmonics
├── universal_laws.py          # Fibonacci, Gann
├── information_theory.py      # Entropy, MI
├── particle_portfolio.py      # Particle filter
├── spectral_regime.py         # FFT regime
├── system_health.py           # Polyvagal health
├── pid_drawdown.py            # PID controller
└── regime_integration.py      # HMM + Spectral
```

---

**Inizia semplice. Prova skill. Scala solo se funziona.**
