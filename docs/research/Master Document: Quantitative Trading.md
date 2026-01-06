# Master Document: Quantitative Trading & Signal Processing

> **Versione**: 2.0 (2026-01-06)
> **Analisi di conformità**: Verificato contro i 4 Pilastri architetturali

---

## I Quattro Pilastri Fondamentali

Prima di applicare qualsiasi concetto di questo documento, verificare conformità con:

| Pilastro | Principio | Applicazione |
|----------|-----------|--------------|
| **P1 Probabilistico** | Non predizioni, ma distribuzioni di probabilità | Bayes, MCS, confidence intervals |
| **P2 Non Lineare** | Power laws, non scaling lineare (Giller, Mandelbrot) | Position sizing sub-lineare |
| **P3 Non Parametrico** | Adattivo ai dati, non parametri fissi | Rolling windows, online learning |
| **P4 Scalare** | Funziona a qualsiasi frequenza/asset/condizione | Ratios > valori assoluti |

---

## ADAPTIVE SIGNALS vs FIXED SAFETY

> **"La gabbia la creiamo noi, non il sistema"**
> **ECCETTO**: I parametri di safety NON sono una gabbia - sono protezione contro la rovina.

### Parametri dei Segnali (ADATTIVI)

```python
# SBAGLIATO: Parametri fissi creano "gabbie"
EMA_PERIOD = 20        # Perché 20? Perché non 19 o 21?
RSI_THRESHOLD = 70     # Arbitrario
IBS_THRESHOLD = 0.50   # Fisso

# CORRETTO: Parametri che si adattano ai dati
alpha = 2.0 / (N + 1)                    # Alpha da caratteristiche dati
threshold = mean + 2 * std               # Dinamico, data-driven
ibs_threshold = rolling_percentile(20)   # Adattivo alla distribuzione
```

### Parametri di Safety (FISSI - NON NEGOZIABILI)

```python
# CORRETTO: Parametri di safety FISSI per prevenire la rovina
# Riferimento: Knight Capital perse $440M in 45 min senza questi
MAX_LEVERAGE = 3              # MAI adattivo
MAX_POSITION_PCT = 10         # MAI adattivo (% del portfolio)
STOP_LOSS_PCT = 5             # MAI adattivo
DAILY_LOSS_LIMIT_PCT = 2      # MAI adattivo
KILL_SWITCH_DRAWDOWN = 15     # MAI adattivo (% trigger halt)
```

---

## 1. Fondamenta Statistiche e Probabilistiche

### Teorema di Bayes e Validazione del Segnale

> **Conformità Pilastri**: P1 (Probabilistico)
> **Status**: CONFORME

Analisi della reale capacità predittiva di un indicatore.

**Matrice di Confusione (Esempio Reale)**:
- True Positive Rate: 99%
- False Positive Rate: 20%
- Base Rate (Probabilità a priori P(R)): 9,6%

**Calcolo della Probabilità condizionata P(R|Signal)**:
```
P(Signal) = P(Signal|R) × P(R) + P(Signal|not R) × P(not R)
P(Signal) = 0.99 × 0.096 + 0.20 × 0.904 = 0.276
P(R|Signal) = [0.99 × 0.096] / 0.276 = 34,4%
```

**Conclusione**: Anche con un segnale accurato al 99%, se l'evento è raro, la probabilità reale è bassa.

**Prosecutor's Fallacy**: Non confondere P(Dati | Ipotesi) con P(Ipotesi | Dati).

### Monte Carlo Simulation (MCS)

> **Conformità Pilastri**: P1, P3
> **Status**: CONFORME

- Formulare variabili target e Fattori di Rischio.
- Specificare la distribuzione (Student-t, Cauchy, ecc.).
- Attenzione alla Multicollinearità e all'Autocorrelazione temporale.

---

## 2. Advanced Signal Processing

### Decomposizione (EMD & HHT)

> **Conformità Pilastri**: P3 (Non Parametrico)
> **Status**: CONFORME
> **Nota Implementativa**: Richiede librerie esterne (PyEMD), non nativo NautilusTrader

- **EMD**: Decompone la serie in oscillazioni a media zero (IMF).
- **TV-EMD (Time Varying)**:
  - Usa un filtro di Kalman per il VWAP.
  - Calcola il rapporto tra frequenze alte: `Ratio = HF1 / HF2`.
  - Serve a misurare la deviazione significativa dal rumore.

### Volume Clocks

> **Conformità Pilastri**: P4 (Scalare)
> **Status**: CONFORME
> **Nota Implementativa**: NautilusTrader supporta solo time-based bars nativamente

- **Problema**: Il tempo cronologico è fuorviante (spread e volatilità variabili).
- **Soluzione**: Usare "Volume Clocks" (barre a volume costante).
- **Relative Volume Bin**: Dividere il volume totale per la frequenza EMD (DHF) per ottenere una risposta fluida.

---

## 3. Strategie di Pattern Recognition

### k-NN Pattern Mining (Approccio Qusma)

> **Conformità Pilastri**: P1, P3
> **Status**: PARZIALMENTE CONFORME
> **Warning**: Il parametro `k` dovrebbe essere adattivo

- **Input** (11 numeri): Rendimenti G1-G2, G2-G3 e valori OHLC dei 3 giorni.
- **Metodo**: Trova i "k" pattern storici più simili (minima differenza quadrata).
- **Regola**: Se il rendimento medio futuro dei simili è > 0,2% -> LONG.

**Filtri**:
- IBS < 0.5 per Long.
- Leva = Target Annuale / (Volatilità 10gg × radice(252)).

### Mean Reversion con IBS

> **Conformità Pilastri**: P4 (Scalare - ratio)
> **Status**: NON CONFORME - Soglie fisse
> **Azione Richiesta**: Convertire a soglie dinamiche

**Formula**: `IBS = (Close - Low) / (High - Low)`

**Setup Originale** (PROBLEMATICO):
- Qusma: Long QQQ se `IBS < 0.50` e `RSI(3) < 10`.
- Adaptive: Long SPY se `IBS < 0.45` (Exit > 0.75).

**Setup Corretto** (ADATTIVO):
```python
# Invece di soglie fisse:
ibs_threshold = rolling_percentile(ibs_series, window=20, percentile=30)
rsi_threshold = rolling_mean(rsi_series, 20) - 2 * rolling_std(rsi_series, 20)

# Entry: IBS < ibs_threshold AND RSI < rsi_threshold
```

---

## 4. Identificazione Trend e Catastrofi

### CUSCORE (Cumulative Score)

> **Conformità Pilastri**: P1 (Test statistico)
> **Status**: CONFORME

Per rilevare il cambio di pendenza (beta) del trend.

**Formula**: `Q = Somma( (y_t - beta × t) × t )`

**Modifica Reattiva**:
```
beta_stimato = 0.25 × (EWMA_corrente - EWMA_4_periodi_fa)
```

> **Warning**: Il coefficiente `0.25` è fisso. Considerare rendere adattivo:
> ```python
> decay_factor = adaptive_decay(volatility_regime)
> beta_stimato = decay_factor × (EWMA_corrente - EWMA_lag)
> ```

### Archetipo della Catastrofe

> **Conformità Pilastri**: P2 (Non Lineare)
> **Status**: RICHIEDE VALIDAZIONE PMW
> **PMW Query**: "catastrophe theory financial markets criticism failures"

- Accumulo lento (A-B-C) seguito da Salto (D).
- Ingresso all'80° percentile della durata storica del trend.

**Nota PMW**: La teoria della catastrofe (Thom, 1972) è matematica pura. L'applicazione ai mercati finanziari è contestata - cercare disconferme prima di implementare.

---

## 5. Microstruttura e Order Book

> **Conformità Pilastri**: P4 (Scalare), P1 (Probabilistico)
> **Status**: CONFORME
> **Implementabile**: Direttamente con NautilusTrader live adapters

- **Micro-Price**: Variazione Mid-Price pesata sui volumi LOB.
- **Imbalance**: Filtrare il trade se lo spostamento di prezzo > (Step × Commissioni).
- **Crypto**: Monitorare Funding Rate, Open Interest e Liquidazioni.

---

## 6. Ottimizzazione (Machine Learning)

### Funzione di Costo Regolarizzata (Tikhonov)

> **Conformità Pilastri**: Anti-overfitting
> **Status**: CONFORME

Serve per trovare la soglia (threshold) ottimale evitando l'overfitting.

**Formula**: `Costo = Errore_Quadratico + lambda × (Penalità_Rugosità)`

Minimizzando questa funzione si ottiene una curva di profitto stabile e non casuale.

### Feature List

> **Conformità Pilastri**: P2, P4
> **Status**: CONFORME

| Feature | Formula | Pilastro |
|---------|---------|----------|
| Trend Deviation | `log(Close) / Prezzo_Filtrato` | P4 (ratio) |
| Velocity | Previsione regressione lineare a 1 step | P2 |
| Variance Ratio | `Varianza_Breve / Varianza_Lunga` | P4 (ratio), P2 (test non-linearità) |
| Hurst Exponent | Persistenza del trend | P2 (Mandelbrot) |

---

## Analisi di Conformità ai Pilastri (2026-01-06)

### Riepilogo

| Sezione | Conformità | Note |
|---------|------------|------|
| 1. Bayes/MCS | 100% | Allineato perfettamente con P1 |
| 2. EMD/Volume Clocks | 90% | Richiede implementazione esterna |
| 3. Pattern Recognition | 60% | **Soglie fisse da convertire** |
| 4. CUSCORE/Catastrofi | 70% | Coefficienti fissi + PMW needed |
| 5. Microstruttura | 95% | Implementabile direttamente |
| 6. ML Features | 85% | Hurst validato (Mandelbrot) |
| **Safety Parameters** | **0%** | **CRITICO - MANCANTI** |

### Azioni Richieste

1. **CRITICO**: Aggiungere Safety Parameters (fatto sopra)
2. **ALTA**: Convertire soglie IBS/RSI in dinamiche
3. **MEDIA**: Rendere coefficiente CUSCORE adattivo
4. **BASSA**: Validare PMW per teoria catastrofi

### Formule da Estrarre (per RAG-Anything)

Questo documento contiene le seguenti formule da indicizzare:

```latex
% Bayes
P(R|Signal) = \frac{P(Signal|R) \times P(R)}{P(Signal)}

% IBS
IBS = \frac{Close - Low}{High - Low}

% CUSCORE
Q = \sum_{t} (y_t - \beta \times t) \times t

% Tikhonov
Cost = \|error\|^2 + \lambda \times \|roughness\|^2

% Hurst (da papers)
H = \frac{\log(R/S)}{\log(n)}

% Kelly Criterion (implicito nel sizing)
f^* = \frac{bp - q}{b}
```

---

## Changelog

- **2026-01-06 v2.0**: Aggiunta analisi conformità pilastri, sezione Safety Parameters, note PMW
- **Originale**: Versione compatibile Word/Google Docs
