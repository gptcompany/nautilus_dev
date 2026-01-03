# Metodi Matematici per il Calcolo di Target di Prezzo
## Alternative al Point & Figure e Approcci Algoritmici

---

## 1. IL POINT & FIGURE: LOGICA SENZA GRAFICO

### Principio Fondamentale
Il P&F NON è solo un grafico - è un **metodo di misurazione dell'energia** accumulata in una fase di consolidamento.

**Legge di Causa ed Effetto (Wyckoff):**
> "La Causa (accumulo orizzontale) produce un Effetto (movimento di prezzo) proporzionale"

### Formula P&F Pura (Senza Grafico)

**VERTICAL COUNT (più semplice):**
```
Target = Box_Size × Reversal × Column_Length + Reference_Point

Esempio (Upside):
- Box Size: $1
- Reversal: 3
- Lunghezza colonna di breakout: 10 box
- Minimo della colonna: $50

Target = 1 × 3 × 10 + 50 = $80
```

**HORIZONTAL COUNT (Wyckoff):**
```
Target_UP = (Numero_Colonne × Box_Size × Reversal) + Minimo_Range
Target_DOWN = Massimo_Range - (Numero_Colonne × Box_Size × Reversal)

Esempio:
- Range di consolidamento: 15 colonne
- Box Size: $2
- Reversal: 3
- Minimo del range: $100

Target = (15 × 2 × 3) + 100 = $190
```

### Calcolo P&F Algoritmico (Solo Dati OHLC)

Per usare P&F senza grafico, serve solo:
1. **Determinare Box Size**: Tipicamente 1% del prezzo o ATR/3
2. **Contare i reversal**: Ogni cambio di direzione ≥ 3 box = 1 colonna
3. **Misurare la "causa"**: Numero di colonne nel consolidamento

```python
# Pseudo-algoritmo P&F senza grafico
def calcola_target_pnf(highs, lows, box_size, reversal=3):
    columns = 0
    direction = None
    
    for i in range(len(highs)):
        range_boxes = int((highs[i] - lows[i]) / box_size)
        if range_boxes >= reversal:
            columns += 1
    
    cause = columns * box_size * reversal
    return cause  # Da aggiungere al minimo o sottrarre dal massimo
```

---

## 2. ALTERNATIVE MATEMATICHE AL P&F

### 2.1 ATR PROJECTION (Average True Range)

**Logica:** La volatilità storica predice la volatilità futura

**Formula Base:**
```
Target_UP = Entry_Price + (ATR × Multiplier)
Target_DOWN = Entry_Price - (ATR × Multiplier)

Multiplier comuni:
- Conservativo: 1.5-2.0
- Normale: 2.0-3.0
- Aggressivo: 3.0-4.0
```

**Formula Avanzata (Proiezione Temporale):**
```
Target_Giornaliero = Open + (ATR_Daily × Direction × Probability_Factor)

Dove:
- Direction: +1 (long) o -1 (short)
- Probability_Factor: 
  - 68% probabilità → 1.0 ATR
  - 95% probabilità → 2.0 ATR
  - 99.7% probabilità → 3.0 ATR
```

**Vantaggi vs P&F:**
- Si adatta automaticamente alla volatilità
- Calcolo istantaneo (no costruzione grafico)
- Validità statistica misurabile

**Esempio Pratico:**
```
ATR(14) = $5
Entry = $100
Target 1σ (68%) = $100 + $5 = $105
Target 2σ (95%) = $100 + $10 = $110
Target 3σ (99.7%) = $100 + $15 = $115
```

---

### 2.2 MEASURED MOVE (AB=CD)

**Logica:** I mercati si muovono in onde simmetriche

**Formula:**
```
Target = C + (B - A)

Dove:
A = Inizio del primo impulso
B = Fine del primo impulso  
C = Fine del ritracciamento
```

**Varianti:**
```
Move_100% = C + (B - A) × 1.00    [Target classico]
Move_127% = C + (B - A) × 1.272   [Target esteso]
Move_162% = C + (B - A) × 1.618   [Target Fibonacci]
```

**Esempio:**
```
A (minimo) = $50
B (massimo primo impulso) = $70
C (fine ritracciamento) = $60

Target 100% = $60 + ($70 - $50) = $80
Target 127% = $60 + $20 × 1.272 = $85.44
Target 162% = $60 + $20 × 1.618 = $92.36
```

**Vantaggi vs P&F:**
- Più intuitivo visivamente
- Funziona in qualsiasi timeframe
- Non richiede parametri arbitrari (box size)

---

### 2.3 FIBONACCI EXTENSIONS

**Logica:** Rapporti matematici naturali definiscono i target

**Formula (3 Punti - A, B, C):**
```
Extension_Level = C + (B - A) × Fib_Ratio

Livelli chiave:
- 100%: C + (B-A) × 1.000
- 127.2%: C + (B-A) × 1.272  
- 161.8%: C + (B-A) × 1.618  [Golden Ratio]
- 200%: C + (B-A) × 2.000
- 261.8%: C + (B-A) × 2.618
- 423.6%: C + (B-A) × 4.236
```

**Calcolo Senza Grafico:**
```python
def fibonacci_targets(swing_low, swing_high, retracement_low):
    move = swing_high - swing_low
    
    targets = {
        '100%': retracement_low + move * 1.000,
        '127%': retracement_low + move * 1.272,
        '162%': retracement_low + move * 1.618,
        '200%': retracement_low + move * 2.000,
        '262%': retracement_low + move * 2.618
    }
    return targets
```

**Esempio:**
```
Swing Low (A) = $100
Swing High (B) = $150 → Move = $50
Retracement Low (C) = $130

Target 100% = $130 + $50 = $180
Target 162% = $130 + $50 × 1.618 = $210.90
Target 262% = $130 + $50 × 2.618 = $260.90
```

---

### 2.4 STANDARD DEVIATION PROJECTION

**Logica:** Il prezzo si muove entro confini statistici prevedibili

**Formula (Canale di Regressione):**
```
Upper_Band = Linear_Regression + (StdDev × N)
Lower_Band = Linear_Regression - (StdDev × N)

Dove N = numero di deviazioni standard
```

**Formula ICT/SMC Standard Deviation:**
```
Target dalla "Manipulation Leg":

Livello -1 = Low + (High - Low) × (-1)
Livello -2 = Low + (High - Low) × (-2)
Livello -2.5 = Low + (High - Low) × (-2.5)
Livello -4 = Low + (High - Low) × (-4)
```

**Interpretazione Probabilistica:**
```
±1 StdDev → 68.27% del movimento rimane in questo range
±2 StdDev → 95.45% del movimento rimane in questo range
±3 StdDev → 99.73% del movimento rimane in questo range
```

**Vantaggi vs P&F:**
- Base statistica rigorosa
- Probabilità quantificabile
- Adattivo alla volatilità corrente

---

### 2.5 VOLATILITY PROJECTION (Range-Based)

**Logica:** Il range storico predice il range futuro

**Formula ADR (Average Daily Range):**
```
Target_UP = Open + ADR
Target_DOWN = Open - ADR

ADR = Media degli ultimi N giorni di (High - Low)
```

**Formula con Percentili:**
```
Target_Conservativo = Open + Range_25th_Percentile
Target_Medio = Open + Range_50th_Percentile (Mediana)
Target_Aggressivo = Open + Range_75th_Percentile
Target_Estremo = Open + Range_90th_Percentile
```

---

## 3. CONFRONTO METODI

| Metodo | Base Matematica | Richiede Grafico? | Adattivo? | Precisione |
|--------|----------------|-------------------|-----------|------------|
| **P&F Vertical** | Geometrica | No (solo dati) | No | Media |
| **P&F Horizontal** | Causa/Effetto | Consigliato | No | Alta (trend) |
| **ATR Projection** | Statistica | No | Sì | Media |
| **Measured Move** | Simmetria | No | No | Alta (pattern) |
| **Fibonacci** | Rapporti aurei | No | No | Alta |
| **Std Deviation** | Probabilistica | No | Sì | Alta |
| **ADR/Range** | Statistica | No | Sì | Media |

---

## 4. METODO IBRIDO CONSIGLIATO

### Formula Composita per Target

```
Target_Finale = Weighted_Average(T1, T2, T3, T4)

Dove:
T1 = ATR × 2 (peso 25%)
T2 = Measured Move 100% (peso 30%)
T3 = Fibonacci 161.8% (peso 25%)
T4 = 2 × StdDev projection (peso 20%)

Target = (T1 × 0.25) + (T2 × 0.30) + (T3 × 0.25) + (T4 × 0.20)
```

### Confluenza per Validazione

**Un target è FORTE quando:**
1. Almeno 3 metodi convergono entro 2% dello stesso livello
2. Il livello coincide con supporto/resistenza storico
3. È raggiungibile entro il range medio del timeframe

---

## 5. IMPLEMENTAZIONE ALGORITMICA P&F

### Calcolo P&F Count Senza Costruire il Grafico

```python
import pandas as pd
import numpy as np

def calculate_pnf_target(df, box_size=None, reversal=3):
    """
    Calcola target P&F senza costruire il grafico
    df: DataFrame con colonne 'high', 'low', 'close'
    """
    
    # Auto box size se non specificato (1% del prezzo medio)
    if box_size is None:
        box_size = df['close'].mean() * 0.01
    
    # Identifica i punti di inversione
    columns = []
    current_direction = None
    column_count = 0
    
    for i in range(1, len(df)):
        move = df['close'].iloc[i] - df['close'].iloc[i-1]
        boxes_moved = abs(move) / box_size
        
        if boxes_moved >= reversal:
            new_direction = 1 if move > 0 else -1
            
            if new_direction != current_direction:
                column_count += 1
                current_direction = new_direction
    
    # Calcola il "cause"
    range_high = df['high'].max()
    range_low = df['low'].min()
    
    cause = column_count * box_size * reversal
    
    # Target
    target_up = range_low + cause
    target_down = range_high - cause
    
    return {
        'columns': column_count,
        'cause': cause,
        'target_up': target_up,
        'target_down': target_down,
        'box_size': box_size
    }

def calculate_all_targets(entry, swing_high, swing_low, 
                          retracement_end, atr):
    """
    Calcola tutti i target con metodi multipli
    """
    
    move = swing_high - swing_low
    
    targets = {
        # ATR Based
        'atr_1x': entry + atr,
        'atr_2x': entry + (atr * 2),
        'atr_3x': entry + (atr * 3),
        
        # Measured Move
        'measured_100': retracement_end + move,
        'measured_127': retracement_end + (move * 1.272),
        'measured_162': retracement_end + (move * 1.618),
        
        # Fibonacci Extensions
        'fib_100': retracement_end + move,
        'fib_162': retracement_end + (move * 1.618),
        'fib_262': retracement_end + (move * 2.618),
        
        # Range Based
        'range_100': entry + (swing_high - swing_low),
        'range_200': entry + (2 * (swing_high - swing_low))
    }
    
    # Trova confluenze
    all_values = list(targets.values())
    clusters = find_clusters(all_values, tolerance=0.02)
    
    targets['confluences'] = clusters
    
    return targets

def find_clusters(values, tolerance=0.02):
    """
    Trova i livelli dove più target convergono
    """
    values = sorted(values)
    clusters = []
    current_cluster = [values[0]]
    
    for v in values[1:]:
        if abs(v - current_cluster[-1]) / current_cluster[-1] <= tolerance:
            current_cluster.append(v)
        else:
            if len(current_cluster) >= 2:
                clusters.append({
                    'level': np.mean(current_cluster),
                    'strength': len(current_cluster)
                })
            current_cluster = [v]
    
    return clusters
```

---

## 6. REGOLE OPERATIVE

### Quando Usare Quale Metodo

| Condizione di Mercato | Metodo Preferito |
|----------------------|------------------|
| **Trend forte** | Fibonacci Extensions, Measured Move |
| **Range/Consolidamento** | P&F Horizontal, StdDev Channels |
| **Alta volatilità** | ATR Projection (si adatta) |
| **Bassa volatilità** | P&F Vertical, Range-based |
| **Breakout** | P&F + ATR combinati |
| **Ritracciamento** | Fibonacci + Measured Move |

### Validazione Target

Un target è **valido** quando:

1. ✅ Almeno 2 metodi convergono entro 1-2%
2. ✅ È raggiungibile con volatilità normale (entro 3 ATR)
3. ✅ Non viola livelli strutturali maggiori
4. ✅ Risk/Reward risultante ≥ 2:1

---

## 7. CONCLUSIONE

### P&F Senza Grafico: È Possibile?

**SÌ**, la logica P&F può essere applicata algoritmicamente:

1. **Input necessari**: Serie OHLC, Box Size, Reversal
2. **Output**: Numero di colonne, Cause, Target proiettato
3. **Limitazione**: Perde alcune sfumature visive ma mantiene la matematica

### Alternative Più Valide al P&F

1. **Fibonacci Extensions** - Più universale, stesso livello di precisione
2. **ATR Projection** - Più adattivo, base statistica solida
3. **Measured Move** - Più intuitivo, validità empirica forte
4. **Standard Deviation** - Più rigoroso matematicamente

### Raccomandazione Finale

> **Usa un approccio multi-metodo**: calcola 3-4 target con metodi diversi, 
> cerca le confluenze, e usa quelle come target primari. Questo è più 
> robusto di qualsiasi singolo metodo, incluso il P&F tradizionale.

---

*Documento creato per integrazione con metodologia Crabel*
*Riferimenti: Wyckoff, du Plessis, Dorsey, Wilder*
