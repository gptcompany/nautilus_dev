---
name: pine-to-nautilus
description: Migrazione indicatori Pine Script (TradingView) verso NautilusTrader. Usa questa skill quando l'utente vuole convertire indicatori Pine Script (inclusi quelli di Big Beluga, LuxAlgo, etc.) in indicatori Python, Cython o Rust per NautilusTrader. Supporta: (1) Analisi e parsing di codice Pine Script, (2) Conversione in Python Indicator per Nautilus, (3) Conversione in Rust per alte prestazioni, (4) Generazione di test di validazione, (5) Mappatura funzioni ta.* verso equivalenti Nautilus.
---

# Pine Script to NautilusTrader Migration Skill

## Workflow di Conversione

### Step 1: Analisi del Pine Script

Prima di convertire, analizzare il codice Pine per identificare:

1. **Versione Pine Script** (v4, v5, v6)
2. **Indicatori built-in usati** (ta.sma, ta.ema, ta.rsi, etc.)
3. **Variabili series** e loro dipendenze temporali
4. **Input parameters** e loro tipi
5. **Output** (plot, alertcondition, etc.)

### Step 2: Mappatura Funzioni

Consultare `references/pine_to_nautilus_mapping.md` per la mappatura completa.

Funzioni comuni:
- `ta.sma(src, len)` → `SimpleMovingAverage(period)`
- `ta.ema(src, len)` → `ExponentialMovingAverage(period)`
- `ta.rsi(src, len)` → `RelativeStrengthIndex(period)`
- `ta.atr(len)` → `AverageTrueRange(period)`
- `ta.crossover(a, b)` → logica custom `a > b and prev_a <= prev_b`
- `ta.crossunder(a, b)` → logica custom `a < b and prev_a >= prev_b`
- `nz(x, replacement)` → `x if x is not None else replacement`
- `na(x)` → `x is None`

### Step 3: Scegliere il Target

**Python** (default): Per prototyping, strategie non-HFT
**Cython**: Per prestazioni migliori, stesso workflow di Python  
**Rust**: Solo per indicatori critici in strategie HFT

### Step 4: Generare il Codice

Usare i template in `assets/templates/` come base.

### Step 5: Generare Test di Validazione

Sempre generare test che confrontano output con valori attesi da TradingView.

## Pattern Specifici Big Beluga

Gli indicatori di Big Beluga spesso usano:
- Smoothing multiplo (doppio/triplo EMA)
- Bande dinamiche basate su ATR
- Colori condizionali (tradurre in segnali numerici)
- Frecce/label (tradurre in enum di segnali)

## Output Atteso

Per ogni conversione, produrre:
1. File indicatore (`.py`, `.pyx`, o `.rs`)
2. File di test (`test_<indicator>.py`)
3. Documentazione inline
4. Note su eventuali differenze di comportamento

## Riferimenti

- `references/pine_to_nautilus_mapping.md` - Mappatura completa funzioni
- `references/nautilus_indicator_patterns.md` - Pattern comuni Nautilus
- `references/big_beluga_patterns.md` - Pattern specifici Big Beluga
- `assets/templates/` - Template base per Python/Cython/Rust
