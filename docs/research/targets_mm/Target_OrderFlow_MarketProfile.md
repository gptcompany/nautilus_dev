# Target di Prezzo con Order Flow e Market Profile
## Metodi Basati su Volume e Flusso degli Ordini

---

## PERCHÉ QUESTI METODI SONO PIÙ RIGOROSI

I metodi tradizionali (P&F, Fibonacci, ATR) sono basati solo sul **prezzo**.
Order Flow e Market Profile sono basati su **dati reali**:

| Metodo Tradizionale | Metodo Order Flow/Profile |
|---------------------|--------------------------|
| Geometria del prezzo | Transazioni reali |
| Pattern storici | Volume effettivo |
| Assunzioni statistiche | Comportamento istituzionale |
| Lagging | Near-real-time |

> "Il prezzo ti dice COSA è successo. Il volume ti dice PERCHÉ."

---

## 1. MARKET PROFILE (TPO)

### Concetti Chiave

**TPO (Time Price Opportunity)**: Ogni blocco rappresenta un periodo di 30 minuti 
in cui il prezzo ha scambiato a quel livello.

**POC (Point of Control)**: Il prezzo dove si è trascorso PIÙ TEMPO
- È il "fair value" percepito dal mercato
- Il prezzo tende a gravitare verso il POC
- Serve come **target naturale** per i trade

**Value Area (VA)**: Range che contiene il 70% dell'attività
- VAH (Value Area High): Limite superiore
- VAL (Value Area Low): Limite inferiore
- Funzionano come S/R dinamici

### Formula Value Area

```
1. Conta totale TPO nel profilo
2. Target VA = Totale × 70%
3. Parti dal POC (riga con più TPO)
4. Aggiungi righe sopra/sotto alternando (la più grande)
5. Fermati quando raggiungi 70%
```

### Target con Market Profile

**80% Rule (Regola dell'80%)**:
```
SE prezzo apre FUORI dalla Value Area del giorno precedente
E rientra nella VA entro 2 barre da 30 min

ALLORA: 80% probabilità di raggiungere l'ALTRO estremo della VA

Target LONG: Se entra da VAL → Target = VAH
Target SHORT: Se entra da VAH → Target = VAL
```

**Target da Poor Highs/Lows**:
```
Poor High/Low = Estremo con pochi TPO (1-2 lettere)
→ Il mercato tornerà a testare questo livello

Target = Poor High o Poor Low non ancora testato
```

**Target da Single Prints**:
```
Single Print = Gap nel profilo (movimento rapido senza tempo)
→ Rappresenta inefficienza che il mercato tende a colmare

Target = Area dei Single Prints più vicina
```

### Tipo di Giornata e Target Atteso

| Tipo Giornata | Caratteristiche | Target Atteso |
|--------------|-----------------|---------------|
| **Normal** | IB ampio, poco range extension | Target = Estremi IB |
| **Trend** | IB stretto, POC migra | Target = Estensione 1.5-2× IB |
| **Double Distribution** | Due VA separate | Target = Nuova VA |
| **Neutral** | Simmetrico, nessuna direzione | Target = POC |

### Formule Pratiche

**Target da Initial Balance (IB)**:
```
IB = Range delle prime 2 ore (o primo ora)

Target_UP = IB_High + (IB_Range × 0.5)  [Prima estensione]
Target_UP = IB_High + (IB_Range × 1.0)  [Seconda estensione]

Target_DOWN = IB_Low - (IB_Range × 0.5)
Target_DOWN = IB_Low - (IB_Range × 1.0)
```

**Measured Move da Trading Range**:
```
Simile a P&F Horizontal Count:

Target = VA_Width × Multiplier + Breakout_Point

Multiplier tipico: 1.0 - 1.5
```

---

## 2. VOLUME PROFILE

### Differenza da Market Profile

| Market Profile (TPO) | Volume Profile |
|---------------------|----------------|
| Misura TEMPO a ogni prezzo | Misura VOLUME a ogni prezzo |
| Mostra dove il prezzo è stato accettato | Mostra dove si è effettivamente scambiato |
| POC = più tempo | VPOC = più volume |

### Concetti Chiave

**VPOC (Volume Point of Control)**: Prezzo con MASSIMO volume
- "Fulcro" del sentiment di mercato
- Se prezzo > VPOC → Bias bullish
- Se prezzo < VPOC → Bias bearish

**HVN (High Volume Node)**: Picchi nel profilo volume
- Prezzo ATTRAE verso HVN (alta gravità)
- Agiscono come S/R forti
- Prezzo tende a consolidare intorno agli HVN

**LVN (Low Volume Node)**: Valli nel profilo volume
- Prezzo PASSA VELOCEMENTE attraverso LVN (bassa gravità)
- Movimento rapido quando raggiunto
- Breakout facili, ma anche reversal rapidi

### Target con Volume Profile

**Target = VPOC Non Testato (Naked VPOC)**:
```
VPOC delle sessioni precedenti che non è stato ritestato

Regola: Il prezzo tende a tornare ai Naked VPOC

Target = VPOC più vicino non ancora toccato
```

**Target da Distribution Block**:
```
1. Identifica HVN (blocco di distribuzione)
2. Identifica LVN ai bordi
3. Se prezzo rompe HVN:
   
   Target = Prossimo HVN attraverso LVN
   (Il prezzo "salta" attraverso LVN verso prossimo HVN)
```

**Target POC Stacked**:
```
POC di più sessioni allineati allo stesso livello
= S/R MOLTO forte

Target per reversal o breakout significativo
```

### Formula Pratica

**Value Area Target**:
```
# Se prezzo esce dalla VA
Exit_Level = VAH o VAL (punto di uscita)
Target_Minimo = 0.5 × (VAH - VAL) oltre Exit_Level
Target_Esteso = 1.0 × (VAH - VAL) oltre Exit_Level
```

---

## 3. ORDER FLOW (FOOTPRINT CHARTS)

### Componenti Fondamentali

**Delta**: Differenza tra volume Buy e Sell
```
Delta = Ask_Volume - Bid_Volume

Delta Positivo → Buyers dominanti
Delta Negativo → Sellers dominanti
```

**Cumulative Delta (CVD)**: Delta accumulato nel tempo
```
CVD_rising + Price_rising = Trend sano
CVD_falling + Price_rising = DIVERGENZA (reversal warning)
```

**Imbalance**: Squilibrio significativo Buy/Sell
```
Imbalance Ratio tipico: 3:1 o superiore

Ask:Bid = 300:100 → Imbalance Buy (3:1)
Bid:Ask = 400:80 → Imbalance Sell (5:1)
```

**Stacked Imbalances**: Imbalance su più livelli consecutivi
```
= Momentum istituzionale forte
= Conferma direzione breakout
```

### Pattern Order Flow per Target

**1. ABSORPTION (Target Reversal)**
```
Pattern: Alto volume a un livello SENZA movimento di prezzo

Interpretazione: 
- Ordini limit stanno "assorbendo" ordini market aggressivi
- Indica presenza istituzionale
- Probabile reversal

Target: Estremo opposto del range recente
Stop: Sotto/sopra zona di absorption
```

**2. EXHAUSTION (Target Reversal)**
```
Pattern: Volume spike all'estremo CON prezzo che stalla

Interpretazione:
- "Ultimo respiro" del movimento
- Buyers/sellers esauriti

Target: Ritracciamento al POC o VWAP
```

**3. BREAKOUT CONFIRMATION (Target Continuation)**
```
Breakout VALIDO:
- Delta allineato con direzione
- Imbalances stacked nella direzione del breakout
- CVD in aumento

Target: Prossimo HVN o LVN
```

**4. DELTA DIVERGENCE (Target Reversal)**
```
Pattern: 
- Prezzo fa nuovi High
- Delta NON fa nuovi High (o è negativo)

Target: Ritorno al POC/VPOC precedente
Alta probabilità di reversal
```

### Formula Delta-Based Target

```python
def order_flow_target(entry, delta_direction, recent_range):
    """
    Target basato su Order Flow
    """
    if delta_direction == 'strong':
        # Delta allineato con prezzo = target esteso
        target = entry + recent_range * 1.5
    elif delta_direction == 'divergent':
        # Delta divergente = target conservativo
        target = entry + recent_range * 0.5
    elif delta_direction == 'absorption':
        # Absorption = reversal target
        target = entry - recent_range * 0.75
    
    return target
```

---

## 4. VWAP CON STANDARD DEVIATION BANDS

### Perché VWAP è Speciale

**VWAP** = Volume Weighted Average Price
- È il "fair value" ponderato per volume
- Usato da istituzionali per benchmark esecuzione
- Prezzo naturalmente gravita verso VWAP

```
VWAP = Σ(Prezzo × Volume) / Σ(Volume)
```

### Standard Deviation Bands

```
Band +1σ = VWAP + 1 × StdDev
Band +2σ = VWAP + 2 × StdDev
Band +3σ = VWAP + 3 × StdDev

Band -1σ = VWAP - 1 × StdDev
Band -2σ = VWAP - 2 × StdDev
Band -3σ = VWAP - 3 × StdDev
```

### Interpretazione Probabilistica

| Banda | Significato | Probabilità Reversal |
|-------|------------|---------------------|
| ±1σ | Range normale | Bassa (continua) |
| ±2σ | Estensione significativa | Media (watch) |
| ±3σ | Estremo statistico | Alta (reversal likely) |
| Oltre ±3σ | Evento raro | Molto alta |

### Target con VWAP Bands

**Target Mean Reversion**:
```
SE prezzo tocca Band +2σ o oltre:
   Target = VWAP (ritorno alla media)
   
SE prezzo tocca Band -2σ o sotto:
   Target = VWAP (ritorno alla media)
```

**Target Trend Following**:
```
SE prezzo rompe sopra +1σ con volume:
   Target 1 = Band +2σ
   Target 2 = Band +3σ
   Stop = VWAP
```

**Target Scalping**:
```
Trade DENTRO le bande:
   Buy @ Band -1σ → Target = VWAP
   Sell @ Band +1σ → Target = VWAP
```

### Anchored VWAP

Ancora più potente: VWAP ancorato a eventi specifici

```
Anchor Points:
- Earnings release
- Major high/low
- Gap fill
- News event

Target = Banda di deviazione dall'Anchored VWAP
```

---

## 5. CALCOLO ALGORITMICO

### Python Implementation

```python
import numpy as np
import pandas as pd

class OrderFlowTargets:
    """
    Calcolo target basato su Order Flow e Volume Profile
    """
    
    def __init__(self, df):
        """
        df: DataFrame con columns:
        - open, high, low, close
        - volume
        - bid_volume, ask_volume (se disponibili)
        """
        self.df = df
    
    # ========== VWAP E BANDE ==========
    
    def calculate_vwap_bands(self, anchor_bar=0):
        """
        Calcola VWAP con Standard Deviation Bands
        """
        df = self.df.iloc[anchor_bar:].copy()
        
        # VWAP
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['tp_volume'] = df['typical_price'] * df['volume']
        df['cum_tp_volume'] = df['tp_volume'].cumsum()
        df['cum_volume'] = df['volume'].cumsum()
        df['vwap'] = df['cum_tp_volume'] / df['cum_volume']
        
        # Standard Deviation
        df['tp_sq_volume'] = df['typical_price']**2 * df['volume']
        df['cum_tp_sq_volume'] = df['tp_sq_volume'].cumsum()
        df['variance'] = (df['cum_tp_sq_volume'] / df['cum_volume']) - df['vwap']**2
        df['std'] = np.sqrt(np.maximum(df['variance'], 0))
        
        # Bands
        current_vwap = df['vwap'].iloc[-1]
        current_std = df['std'].iloc[-1]
        
        return {
            'vwap': current_vwap,
            'std': current_std,
            'band_1_upper': current_vwap + current_std,
            'band_1_lower': current_vwap - current_std,
            'band_2_upper': current_vwap + 2 * current_std,
            'band_2_lower': current_vwap - 2 * current_std,
            'band_3_upper': current_vwap + 3 * current_std,
            'band_3_lower': current_vwap - 3 * current_std,
        }
    
    # ========== VOLUME PROFILE ==========
    
    def calculate_volume_profile(self, num_bins=50):
        """
        Calcola Volume Profile e identifica POC, HVN, LVN
        """
        price_min = self.df['low'].min()
        price_max = self.df['high'].max()
        
        # Crea bins di prezzo
        bins = np.linspace(price_min, price_max, num_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        # Calcola volume per bin (approssimazione)
        volume_profile = np.zeros(num_bins)
        
        for idx, row in self.df.iterrows():
            # Distribuisci volume uniformemente nel range della candela
            bar_low = row['low']
            bar_high = row['high']
            bar_volume = row['volume']
            
            for i, (bin_low, bin_high) in enumerate(zip(bins[:-1], bins[1:])):
                # Overlap tra candela e bin
                overlap_low = max(bar_low, bin_low)
                overlap_high = min(bar_high, bin_high)
                
                if overlap_high > overlap_low:
                    overlap_ratio = (overlap_high - overlap_low) / (bar_high - bar_low + 0.0001)
                    volume_profile[i] += bar_volume * overlap_ratio
        
        # Trova POC (Volume Point of Control)
        poc_idx = np.argmax(volume_profile)
        poc_price = bin_centers[poc_idx]
        
        # Trova Value Area (70% del volume)
        total_volume = volume_profile.sum()
        target_volume = total_volume * 0.70
        
        # Espandi da POC
        va_indices = [poc_idx]
        current_volume = volume_profile[poc_idx]
        low_idx, high_idx = poc_idx - 1, poc_idx + 1
        
        while current_volume < target_volume:
            low_vol = volume_profile[low_idx] if low_idx >= 0 else 0
            high_vol = volume_profile[high_idx] if high_idx < num_bins else 0
            
            if low_vol >= high_vol and low_idx >= 0:
                va_indices.append(low_idx)
                current_volume += low_vol
                low_idx -= 1
            elif high_idx < num_bins:
                va_indices.append(high_idx)
                current_volume += high_vol
                high_idx += 1
            else:
                break
        
        val_price = bin_centers[min(va_indices)]
        vah_price = bin_centers[max(va_indices)]
        
        # Identifica HVN e LVN
        mean_vol = volume_profile.mean()
        std_vol = volume_profile.std()
        
        hvn_threshold = mean_vol + std_vol
        lvn_threshold = mean_vol - 0.5 * std_vol
        
        hvn = bin_centers[volume_profile > hvn_threshold]
        lvn = bin_centers[volume_profile < lvn_threshold]
        
        return {
            'poc': poc_price,
            'vah': vah_price,
            'val': val_price,
            'hvn': list(hvn),
            'lvn': list(lvn),
            'volume_profile': dict(zip(bin_centers, volume_profile))
        }
    
    # ========== DELTA E ORDER FLOW ==========
    
    def calculate_delta(self):
        """
        Calcola Delta se bid/ask volume disponibili
        """
        if 'bid_volume' not in self.df.columns:
            # Stima delta da price action
            self.df['delta'] = np.where(
                self.df['close'] > self.df['open'],
                self.df['volume'] * 0.6,  # Bias buy
                -self.df['volume'] * 0.6  # Bias sell
            )
        else:
            self.df['delta'] = self.df['ask_volume'] - self.df['bid_volume']
        
        self.df['cum_delta'] = self.df['delta'].cumsum()
        
        return {
            'current_delta': self.df['delta'].iloc[-1],
            'cum_delta': self.df['cum_delta'].iloc[-1],
            'delta_ma': self.df['delta'].rolling(10).mean().iloc[-1]
        }
    
    # ========== TARGET COMPOSITO ==========
    
    def get_targets(self, current_price, direction='long'):
        """
        Calcola tutti i target basati su Order Flow
        
        Returns target ordinati per probabilità
        """
        vwap_data = self.calculate_vwap_bands()
        profile_data = self.calculate_volume_profile()
        
        targets = []
        
        if direction == 'long':
            # Target VWAP
            if current_price < vwap_data['vwap']:
                targets.append({
                    'level': vwap_data['vwap'],
                    'type': 'VWAP',
                    'probability': 'high',
                    'description': 'Return to VWAP'
                })
            
            targets.append({
                'level': vwap_data['band_1_upper'],
                'type': 'VWAP +1σ',
                'probability': 'high',
                'description': 'First standard deviation'
            })
            
            targets.append({
                'level': vwap_data['band_2_upper'],
                'type': 'VWAP +2σ',
                'probability': 'medium',
                'description': 'Extended move'
            })
            
            # Target Volume Profile
            targets.append({
                'level': profile_data['vah'],
                'type': 'VAH',
                'probability': 'high',
                'description': 'Value Area High'
            })
            
            targets.append({
                'level': profile_data['poc'],
                'type': 'POC',
                'probability': 'very_high',
                'description': 'Point of Control - strongest target'
            })
            
            # HVN come target
            for hvn in profile_data['hvn']:
                if hvn > current_price:
                    targets.append({
                        'level': hvn,
                        'type': 'HVN',
                        'probability': 'medium',
                        'description': 'High Volume Node'
                    })
        
        else:  # Short
            if current_price > vwap_data['vwap']:
                targets.append({
                    'level': vwap_data['vwap'],
                    'type': 'VWAP',
                    'probability': 'high',
                    'description': 'Return to VWAP'
                })
            
            targets.append({
                'level': vwap_data['band_1_lower'],
                'type': 'VWAP -1σ',
                'probability': 'high',
                'description': 'First standard deviation'
            })
            
            targets.append({
                'level': profile_data['val'],
                'type': 'VAL',
                'probability': 'high',
                'description': 'Value Area Low'
            })
        
        # Ordina per distanza da prezzo corrente
        targets.sort(key=lambda x: abs(x['level'] - current_price))
        
        return targets


# ========== USO SEMPLIFICATO ==========

def quick_orderflow_targets(high, low, close, volume, 
                            current_price, direction='long'):
    """
    Calcolo rapido senza DataFrame completo
    """
    # VWAP approssimato
    typical_price = (high + low + close) / 3
    
    # Range come proxy di volatilità
    range_size = high - low
    
    # Target semplificati
    if direction == 'long':
        return {
            'target_1_conservative': current_price + range_size * 0.5,
            'target_2_normal': current_price + range_size * 1.0,
            'target_3_extended': current_price + range_size * 1.5,
            'vwap_proxy': typical_price,
            'stop_suggestion': current_price - range_size * 0.5
        }
    else:
        return {
            'target_1_conservative': current_price - range_size * 0.5,
            'target_2_normal': current_price - range_size * 1.0,
            'target_3_extended': current_price - range_size * 1.5,
            'vwap_proxy': typical_price,
            'stop_suggestion': current_price + range_size * 0.5
        }
```

---

## 6. TABELLA COMPARATIVA FINALE

| Metodo | Dato Base | Target Type | Migliore Per |
|--------|-----------|-------------|--------------|
| **Market Profile POC** | Tempo | Mean Reversion | Range days |
| **Market Profile VA** | Tempo | Breakout/S&R | Trend days |
| **Volume Profile VPOC** | Volume | S/R dinamico | Tutti i mercati |
| **Volume Profile HVN** | Volume | Consolidation target | Swing trading |
| **Volume Profile LVN** | Volume | Breakout target | Momentum |
| **Order Flow Delta** | Bid/Ask | Confirmation | Day trading |
| **Order Flow Absorption** | Bid/Ask | Reversal | Scalping |
| **VWAP** | Volume | Institutional target | Intraday |
| **VWAP Bands** | Volume + Stats | Probabilistic | All timeframes |

---

## 7. WORKFLOW RACCOMANDATO

### Pre-Market

1. Identifica **POC e VA** del giorno precedente
2. Marca **Naked VPOC** non testati
3. Nota **HVN/LVN** significativi
4. Calcola **VWAP Bands** attese

### Durante il Trading

1. Osserva dove si forma il **POC intraday**
2. Monitora **Delta** per conferma direzione
3. Cerca **Absorption** ai livelli chiave
4. Usa **VWAP ±2σ** come target estremi

### Target Selection

```
Target Priority (dal più affidabile):

1. Naked VPOC (se presente) → 85% hit rate
2. Previous Day POC → 80% hit rate
3. VAH/VAL → 75% hit rate
4. VWAP → 70% hit rate
5. HVN → 65% hit rate
6. VWAP ±1σ → 68% hit rate
7. VWAP ±2σ → 95% contenimento
```

---

## CONCLUSIONE

I metodi basati su **Order Flow** e **Volume Profile** sono più rigorosi perché:

1. **Dati reali**: Basati su transazioni effettive, non pattern geometrici
2. **Comportamento istituzionale**: Riflettono dove i "big players" operano
3. **Probabilità misurabili**: VWAP bands hanno probabilità statistiche note
4. **Adattivi**: Si aggiornano in tempo reale con nuovi dati

**Raccomandazione**: Combina Volume Profile (per S/R) + VWAP Bands (per target) + Delta (per timing) per un sistema completo.

---

## 8. METODI QUANTITATIVI AVANZATI (Microstruttura)

Questi metodi sono i **più rigorosi** perché basati su:
- Modelli matematici peer-reviewed
- Dati tick-by-tick reali
- Teoria dell'informazione e probabilità

### 8.1 VPIN (Volume-Synchronized Probability of Informed Trading)

**Autori**: Easley, Lopez de Prado, O'Hara (2012)
**Validazione**: Ha predetto il Flash Crash del 2010 un'ora prima

**Concetto**: Misura la probabilità che il flusso di ordini contenga 
informazione privata ("flow toxicity").

```
VPIN = |Buy_Volume - Sell_Volume| / Total_Volume

Calcolato su "volume buckets" (non tempo)
```

**Formula completa**:
```
VPIN = (1/n) × Σ |V_buy(τ) - V_sell(τ)| / V_bucket

Dove:
- n = numero di buckets (tipicamente 50)
- V_bucket = volume fisso per bucket
- τ = indice del bucket in volume-time
```

**Interpretazione per Target**:
```
VPIN Alto (>0.5) → Alta probabilità di movimento direzionale
VPIN Basso (<0.3) → Mercato in equilibrio, range-bound

Se VPIN ↑ + Delta positivo → Target UP
Se VPIN ↑ + Delta negativo → Target DOWN

Target Distance = f(VPIN, ATR)
Più alto VPIN = movimento più ampio atteso
```

**Bulk Volume Classification** (per calcolare Buy/Sell):
```python
def bulk_volume_classification(price_change, volume, sigma):
    """
    Classifica volume come buy/sell usando distribuzione normale
    """
    z = price_change / sigma
    buy_fraction = norm.cdf(z)
    
    return {
        'buy_volume': volume * buy_fraction,
        'sell_volume': volume * (1 - buy_fraction)
    }
```

---

### 8.2 Kyle's Lambda (λ)

**Autore**: Albert Kyle (1985) - Modello fondamentale di microstruttura
**Paper**: "Continuous Auctions and Insider Trading"

**Concetto**: Misura l'impatto del prezzo per unità di order flow.
È una misura **inversa** della liquidità.

```
ΔP = λ × Order_Imbalance

Dove:
- ΔP = variazione di prezzo
- λ = Kyle's Lambda (price impact coefficient)
- Order_Imbalance = Buy_Volume - Sell_Volume
```

**Stima empirica**:
```
λ = Cov(ΔP, OI) / Var(OI)

Dove OI = Order Imbalance
```

**Target basato su Kyle's Lambda**:
```
Expected_Move = λ × Expected_Order_Flow

Se conosci l'order flow atteso (da VPIN o imbalance):
Target = Entry + (λ × Predicted_Imbalance)
```

**Interpretazione**:
```
λ alto → Mercato illiquido, piccoli ordini muovono molto il prezzo
λ basso → Mercato liquido, serve molto volume per muovere il prezzo

Target = Entry + (Observed_Imbalance × λ × Confidence_Factor)
```

---

### 8.3 Order Book Imbalance (OBI)

**Concetto**: Misura lo squilibrio tra domanda e offerta nel book.

```
OBI = (Bid_Volume - Ask_Volume) / (Bid_Volume + Ask_Volume)

Range: [-1, +1]
+1 = Solo bid (massimo bullish)
-1 = Solo ask (massimo bearish)
0 = Equilibrio
```

**Weighted Order Book Imbalance** (più sofisticato):
```python
def weighted_obi(bids, asks, levels=10, decay=0.5):
    """
    OBI pesato per distanza dal mid-price
    Livelli vicini pesano di più
    """
    bid_weight = sum(b['size'] * (decay ** i) for i, b in enumerate(bids[:levels]))
    ask_weight = sum(a['size'] * (decay ** i) for i, a in enumerate(asks[:levels]))
    
    return (bid_weight - ask_weight) / (bid_weight + ask_weight)
```

**Predittività**:
```
Studi mostrano: OBI predice direzione del prossimo tick con 55-60% accuracy
(Sembra poco, ma è MOLTO in HFT)

OBI > 0.3 → Bias UP nel prossimo minuto
OBI < -0.3 → Bias DOWN nel prossimo minuto
```

**Target da OBI**:
```
Se |OBI| > threshold:
    Direction = sign(OBI)
    Magnitude = |OBI| × ATR × Sensitivity
    Target = Current_Price + (Direction × Magnitude)
```

---

### 8.4 Market Depth Skew

**Concetto**: Asimmetria della profondità del book a vari livelli di prezzo.

```
Depth_Skew = Σ(Bid_Depth[i]) / Σ(Ask_Depth[i])

Per i = 1 to N livelli di prezzo
```

**Formula avanzata con decadimento**:
```python
def depth_skew(bids, asks, levels=20):
    """
    Calcola skew pesato per distanza
    """
    mid = (bids[0]['price'] + asks[0]['price']) / 2
    
    bid_score = 0
    ask_score = 0
    
    for i, (b, a) in enumerate(zip(bids[:levels], asks[:levels])):
        # Peso inversamente proporzionale alla distanza
        bid_dist = mid - b['price']
        ask_dist = a['price'] - mid
        
        bid_score += b['size'] / (1 + bid_dist)
        ask_score += a['size'] / (1 + ask_dist)
    
    return bid_score / ask_score if ask_score > 0 else float('inf')
```

**Interpretazione**:
```
Skew > 1.5 → Supporto forte, bias UP
Skew < 0.67 → Resistenza forte, bias DOWN
Skew ≈ 1.0 → Equilibrio

Target = Livello dove Skew si normalizza
```

---

### 8.5 Price Impact Function

**Concetto**: Relazione non-lineare tra size dell'ordine e movimento del prezzo.

**Forma empirica** (Square-root law):
```
ΔP = σ × √(Q/V) × sign(Q)

Dove:
- σ = volatilità giornaliera
- Q = size dell'ordine
- V = volume giornaliero medio
```

**Implicazione per Target**:
```
Se conosci il volume "in arrivo" (da order flow):

Expected_Move = σ × √(Expected_Volume / ADV)
Target = Entry ± Expected_Move
```

**Modello di Almgren-Chriss** (esecuzione ottimale):
```
Temporary_Impact = η × (Q/τ)
Permanent_Impact = γ × Q

Total_Impact = η × velocity + γ × total_size
```

---

### 8.6 Liquidity Imbalance Ratio (LIR)

```
LIR = (Best_Bid_Size - Best_Ask_Size) / (Best_Bid_Size + Best_Ask_Size)

Predittivo del prossimo movimento tick-by-tick
```

**Studi accademici** (Cont, Stoikov, Talreja 2010):
```
P(uptick | LIR > 0) ≈ 0.52-0.58
P(downtick | LIR < 0) ≈ 0.52-0.58

Non sembra molto, ma:
- È statisticamente significativo
- Compounded su migliaia di trade = edge misurabile
```

---

### 8.7 Absorption Rate

**Concetto**: Velocità con cui il mercato "assorbe" ordini aggressivi.

```
Absorption_Rate = Volume_Consumed / Time_Elapsed

A un livello di prezzo specifico
```

**Interpretazione**:
```
Alto Absorption + Prezzo stabile = Istituzionali accumulano/distribuiscono
→ Probabile reversal dopo che finiscono

Basso Absorption + Prezzo che si muove = Breakout genuino
→ Target esteso in direzione del movimento
```

**Formula**:
```python
def absorption_rate(trades, price_level, tolerance=0.01):
    """
    Calcola rate di assorbimento a un livello
    """
    relevant_trades = [t for t in trades 
                       if abs(t['price'] - price_level) / price_level < tolerance]
    
    if not relevant_trades:
        return 0
    
    total_volume = sum(t['volume'] for t in relevant_trades)
    time_span = relevant_trades[-1]['time'] - relevant_trades[0]['time']
    
    return total_volume / time_span if time_span > 0 else float('inf')
```

---

## 9. IMPLEMENTAZIONE PYTHON AVANZATA

```python
import numpy as np
from scipy.stats import norm
from typing import List, Dict, Tuple

class MicrostructureTargets:
    """
    Calcolo target basato su modelli di microstruttura
    """
    
    def __init__(self, trades: List[Dict], orderbook: Dict):
        """
        Args:
            trades: Lista di trade con 'price', 'volume', 'time'
            orderbook: Dict con 'bids' e 'asks' (liste di {price, size})
        """
        self.trades = trades
        self.orderbook = orderbook
    
    # ========== VPIN ==========
    
    def calculate_vpin(self, bucket_size: float = None, n_buckets: int = 50):
        """
        Calcola VPIN (Volume-Synchronized PIN)
        """
        if bucket_size is None:
            total_volume = sum(t['volume'] for t in self.trades)
            bucket_size = total_volume / n_buckets
        
        # Calcola sigma per BVC
        prices = [t['price'] for t in self.trades]
        returns = np.diff(np.log(prices))
        sigma = np.std(returns) if len(returns) > 1 else 0.01
        
        # Crea buckets
        buckets = []
        current_bucket = {'buy': 0, 'sell': 0, 'volume': 0}
        
        for i, trade in enumerate(self.trades):
            # Bulk Volume Classification
            if i > 0:
                price_change = trade['price'] - self.trades[i-1]['price']
                z = price_change / (sigma * self.trades[i-1]['price'])
                buy_frac = norm.cdf(z)
            else:
                buy_frac = 0.5
            
            current_bucket['buy'] += trade['volume'] * buy_frac
            current_bucket['sell'] += trade['volume'] * (1 - buy_frac)
            current_bucket['volume'] += trade['volume']
            
            # Bucket pieno?
            if current_bucket['volume'] >= bucket_size:
                buckets.append(current_bucket.copy())
                current_bucket = {'buy': 0, 'sell': 0, 'volume': 0}
        
        # Calcola VPIN
        if len(buckets) < n_buckets:
            n_buckets = len(buckets)
        
        if n_buckets == 0:
            return 0
        
        recent_buckets = buckets[-n_buckets:]
        imbalances = [abs(b['buy'] - b['sell']) for b in recent_buckets]
        volumes = [b['volume'] for b in recent_buckets]
        
        vpin = sum(imbalances) / sum(volumes) if sum(volumes) > 0 else 0
        
        return vpin
    
    # ========== Kyle's Lambda ==========
    
    def estimate_kyle_lambda(self, window: int = 100):
        """
        Stima Kyle's Lambda (price impact per unità di order flow)
        """
        if len(self.trades) < window:
            return None
        
        # Calcola returns e order imbalance
        prices = [t['price'] for t in self.trades[-window:]]
        volumes = [t['volume'] for t in self.trades[-window:]]
        
        # Stima direzione (usando price change)
        returns = np.diff(prices)
        
        # Order imbalance (signed volume)
        signed_volumes = []
        for i in range(1, len(prices)):
            direction = np.sign(prices[i] - prices[i-1])
            signed_volumes.append(volumes[i] * direction)
        
        # Regressione: ΔP = λ × OI
        if len(signed_volumes) < 10:
            return None
        
        cov = np.cov(returns, signed_volumes)[0, 1]
        var = np.var(signed_volumes)
        
        lambda_kyle = cov / var if var > 0 else 0
        
        return lambda_kyle
    
    # ========== Order Book Imbalance ==========
    
    def order_book_imbalance(self, levels: int = 10, weighted: bool = True):
        """
        Calcola Order Book Imbalance
        """
        bids = self.orderbook.get('bids', [])[:levels]
        asks = self.orderbook.get('asks', [])[:levels]
        
        if not bids or not asks:
            return 0
        
        if weighted:
            # Peso decrescente per livelli più lontani
            bid_score = sum(b['size'] * (0.8 ** i) for i, b in enumerate(bids))
            ask_score = sum(a['size'] * (0.8 ** i) for i, a in enumerate(asks))
        else:
            bid_score = sum(b['size'] for b in bids)
            ask_score = sum(a['size'] for a in asks)
        
        total = bid_score + ask_score
        if total == 0:
            return 0
        
        return (bid_score - ask_score) / total
    
    # ========== Depth Skew ==========
    
    def depth_skew(self, levels: int = 20):
        """
        Calcola Depth Skew (ratio bid/ask depth)
        """
        bids = self.orderbook.get('bids', [])[:levels]
        asks = self.orderbook.get('asks', [])[:levels]
        
        if not bids or not asks:
            return 1.0
        
        mid = (bids[0]['price'] + asks[0]['price']) / 2
        
        bid_weighted = 0
        ask_weighted = 0
        
        for b in bids:
            dist = (mid - b['price']) / mid
            bid_weighted += b['size'] / (1 + dist * 100)
        
        for a in asks:
            dist = (a['price'] - mid) / mid
            ask_weighted += a['size'] / (1 + dist * 100)
        
        return bid_weighted / ask_weighted if ask_weighted > 0 else float('inf')
    
    # ========== Target Composito ==========
    
    def get_microstructure_target(self, current_price: float, atr: float):
        """
        Calcola target usando tutti i segnali di microstruttura
        """
        vpin = self.calculate_vpin()
        lambda_k = self.estimate_kyle_lambda()
        obi = self.order_book_imbalance()
        skew = self.depth_skew()
        
        # Determina direzione
        direction_signals = []
        
        if obi > 0.1:
            direction_signals.append(1)
        elif obi < -0.1:
            direction_signals.append(-1)
        
        if skew > 1.2:
            direction_signals.append(1)
        elif skew < 0.8:
            direction_signals.append(-1)
        
        if not direction_signals:
            return None
        
        direction = np.sign(np.mean(direction_signals))
        
        # Calcola magnitude
        confidence = abs(np.mean(direction_signals))
        vpin_factor = 1 + vpin  # VPIN alto = movimento più ampio
        
        # Target base su ATR
        base_move = atr * 1.5 * vpin_factor * confidence
        
        target = current_price + (direction * base_move)
        
        return {
            'target': target,
            'direction': 'long' if direction > 0 else 'short',
            'confidence': confidence,
            'vpin': vpin,
            'obi': obi,
            'skew': skew,
            'lambda': lambda_k
        }


# ========== FUNZIONI RAPIDE ==========

def quick_vpin(prices: List[float], volumes: List[float], 
               n_buckets: int = 50) -> float:
    """
    Calcolo rapido VPIN senza oggetti
    """
    trades = [{'price': p, 'volume': v} for p, v in zip(prices, volumes)]
    
    total_vol = sum(volumes)
    bucket_size = total_vol / n_buckets
    
    sigma = np.std(np.diff(np.log(prices))) if len(prices) > 1 else 0.01
    
    buckets = []
    current = {'buy': 0, 'sell': 0, 'vol': 0}
    
    for i in range(len(prices)):
        if i > 0:
            z = (prices[i] - prices[i-1]) / (sigma * prices[i-1])
            buy_frac = norm.cdf(z)
        else:
            buy_frac = 0.5
        
        current['buy'] += volumes[i] * buy_frac
        current['sell'] += volumes[i] * (1 - buy_frac)
        current['vol'] += volumes[i]
        
        if current['vol'] >= bucket_size:
            buckets.append(current.copy())
            current = {'buy': 0, 'sell': 0, 'vol': 0}
    
    if not buckets:
        return 0
    
    imb = sum(abs(b['buy'] - b['sell']) for b in buckets)
    vol = sum(b['vol'] for b in buckets)
    
    return imb / vol if vol > 0 else 0


def quick_obi(bid_sizes: List[float], ask_sizes: List[float]) -> float:
    """
    Calcolo rapido Order Book Imbalance
    """
    bid_sum = sum(s * (0.8 ** i) for i, s in enumerate(bid_sizes))
    ask_sum = sum(s * (0.8 ** i) for i, s in enumerate(ask_sizes))
    
    total = bid_sum + ask_sum
    return (bid_sum - ask_sum) / total if total > 0 else 0
```

---

## 10. GERARCHIA DI RIGORE

Dal **meno** al **più** rigoroso:

| Livello | Metodo | Dato Base | Validazione |
|---------|--------|-----------|-------------|
| 1 | Fibonacci, P&F | Prezzo | Pattern storici |
| 2 | ATR, Measured Move | Prezzo + Statistiche | Volatilità |
| 3 | Market Profile | Tempo × Prezzo | Auction theory |
| 4 | Volume Profile | Volume × Prezzo | Distribuzione volume |
| 5 | VWAP Bands | Volume × Prezzo + Stats | Deviazione standard |
| 6 | Order Flow (Delta) | Bid/Ask volume | Real-time |
| 7 | **OBI, Depth Skew** | Order book live | Microstructure |
| 8 | **VPIN** | Trade classification | Academic papers |
| 9 | **Kyle's Lambda** | Price impact regression | Nobel-level theory |

**Raccomandazione finale**:
- Retail trader: Livelli 3-6 sono sufficienti
- Prop trader: Livelli 5-8
- Quant/HFT: Livelli 7-9 con ML

---

*Documento complementare a "Target di Prezzo - Metodi Matematici"*
*Riferimenti: Steidlmayer, Dalton, Easley, O'Hara, Kyle, Lopez de Prado*
