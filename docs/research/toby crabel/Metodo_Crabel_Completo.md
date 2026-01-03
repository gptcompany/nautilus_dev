# IL METODO TOBY CRABEL
## Day Trading with Short Term Price Patterns and Opening Range Breakout
### Estratto e Sintesi Completa

---

## INDICE

1. [Introduzione e Framework](#1-introduzione-e-framework)
2. [Opening Range Breakout (ORB)](#2-opening-range-breakout-orb)
3. [Short Term Price Patterns](#3-short-term-price-patterns)
4. [Il Principio Contraction/Expansion](#4-il-principio-contractionexpansion)
5. [Pattern di Contrazione Chiave](#5-pattern-di-contrazione-chiave)
6. [Pattern Avanzati](#6-pattern-avanzati)
7. [Integrazione: Daily Bias](#7-integrazione-daily-bias)
8. [Statistiche e Tabelle di Riferimento](#8-statistiche-e-tabelle-di-riferimento)
9. [Applicazione Pratica](#9-applicazione-pratica)
10. [Glossario Essenziale](#10-glossario-essenziale)

---

## 1. INTRODUZIONE E FRAMEWORK

### Premessa Fondamentale
Il lavoro di Crabel si basa sulla ricerca di **tendenze di mercato tradabili**. L'approccio non cerca cause complete, ma identifica aspetti del price action che sono **statisticamente prevedibili**.

> *"Il mio scopo è sviluppare un framework per capire il mercato. Le statistiche possono fornire un'indicazione, ma possono essere integrate solo da una comprensione del mercato."*

### I Tre Pilastri del Sistema
1. **Opening Range Breakout (ORB)** - Tecnica di ingresso
2. **Short Term Price Patterns** - Analisi dei pattern
3. **Contraction/Expansion** - Principio fondamentale

---

## 2. OPENING RANGE BREAKOUT (ORB)

### Definizione
L'Opening Range Breakout è un trade preso ad un **ammontare predeterminato sopra o sotto l'opening range**.

### Meccanica Operativa

```
CALCOLO DELLO STRETCH:
1. Prendi gli ultimi 10 giorni
2. Per ogni giorno, calcola la differenza tra l'open e l'estremo più vicino all'open
3. Fai la media di queste differenze
4. Questo è lo STRETCH
```

### Esecuzione dell'ORB

| Azione | Descrizione |
|--------|-------------|
| **BUY STOP** | Piazzato a: Open + Stretch (sopra il massimo dell'opening range) |
| **SELL STOP** | Piazzato a: Open - Stretch (sotto il minimo dell'opening range) |
| **Posizione** | Il primo stop eseguito diventa la posizione |
| **Stop Protettivo** | L'altro stop diventa lo stop loss |

### ORBP (Opening Range Breakout Preference)
Quando c'è un **bias direzionale chiaro**, si entra solo in una direzione:
- Solo BUY stop O solo SELL stop
- Lo stop protettivo viene inserito DOPO l'entrata
- Se il mercato va prima verso lo stretch opposto, l'ORBP è annullato

### Condizioni Ideali per ORB

| Pattern | Efficacia |
|---------|-----------|
| Inside Day + NR4 | ⭐⭐⭐⭐⭐ Eccellente |
| NR7 | ⭐⭐⭐⭐⭐ Eccellente |
| NR4 | ⭐⭐⭐⭐ Molto buono |
| Inside Day | ⭐⭐⭐⭐ Molto buono |
| Doji + NR | ⭐⭐⭐⭐ Molto buono |
| Hook Day | ⭐⭐⭐ Buono |

---

## 3. SHORT TERM PRICE PATTERNS

### Concetto Base
Un **short term price pattern** è un'analisi del price action recente in termini di:
- Chiusure precedenti
- Aperture
- Dimensione del range
- Movimenti dall'open

### Notazione dei Pattern
- **(+)** = Chiusura UP rispetto al giorno precedente
- **(-)** = Chiusura DOWN rispetto al giorno precedente
- **Ultimo segno** = Direzione dell'open del giorno di entry

### Esempio Pattern (---)
```
Giorno 3: Chiusura DOWN (-)
Giorno 2: Chiusura DOWN (-)
Giorno 1: Open DOWN (-) → ENTRY
```

### Pattern Open-to-Close più Profittevoli (Bonds 1978-87)

| Pattern | Entry | % Profit |
|---------|-------|----------|
| (---) | BUY | 58% |
| (+++) | SELL | 61% |
| (--+) | SELL | 62% |
| (-++) | SELL | 63% |
| (+-+) | BUY | 60% |

---

## 4. IL PRINCIPIO CONTRACTION/EXPANSION

### Definizione Fondamentale

> *"Il principio di Contraction/Expansion definisce il fenomeno di mercato del cambiamento da un periodo di riposo a un periodo di movimento e ritorno a un periodo di riposo. Questo scambio tra le fasi di moto e riposo avviene costantemente, con una fase direttamente responsabile dell'esistenza dell'altra."*

### Implicazioni Operative

| Dopo... | Aspettarsi... | Strategia |
|---------|---------------|-----------|
| **CONTRAZIONE** (NR, ID) | ESPANSIONE | Seguire ORB aggressivamente |
| **ESPANSIONE** (WS) | CONTRAZIONE | NON seguire ORB, possibile fade |

### Risultati Statistici

```
CONTRAZIONE vs ESPANSIONE dopo ORB:

Trades dopo CONTRAZIONE (NR4/NR7):
- % media: 64%
- Profitti su 7,313 trades: $710,000

Trades dopo ESPANSIONE (WS4/WS7):
- % media: 52-54%
- Profitti su 7,524 trades: $102,000

→ PROFITTI 7x MAGGIORI dopo contrazioni!
```

### Trend Day
Definito come un giorno dove:
- Il range della prima ora comprende **meno del 10%** del range giornaliero
- OPPURE: nessuna area di trade dominante durante la sessione
- Apertura vicino a un estremo, chiusura sull'estremo opposto

---

## 5. PATTERN DI CONTRAZIONE CHIAVE

### 5.1 NR4 (Narrow Range 4)

**Definizione:** Il range giornaliero più stretto confrontato individualmente con ciascuno dei **3 giorni precedenti**.

```
Esempio NR4:
Giorno 4: Range = 50 punti
Giorno 3: Range = 45 punti
Giorno 2: Range = 42 punti
Giorno 1: Range = 30 punti ← NR4 (più stretto di 2,3,4)
```

**Statistiche NR4 + ORB:**

| Mercato | Entry Point | % Profit |
|---------|-------------|----------|
| Bonds | Open +16 tics | 64% |
| Bonds | Open -16 tics | 65% |
| Beans | Open +10¢ | 62% |
| Beans | Open -10¢ | 68% |
| S&P | Open +160 pts | 62% |
| Cattle | Open +50 pts | 63% |

---

### 5.2 NR7 (Narrow Range 7)

**Definizione:** Il range giornaliero più stretto confrontato individualmente con ciascuno dei **6 giorni precedenti**.

**Statistiche NR7 + ORB:**

| Mercato | Entry Point | % Profit |
|---------|-------------|----------|
| Bonds | Open +16 tics | 74% |
| Bonds | Open -16 tics | 64% |
| S&P | Open +160 pts | 67% |
| S&P | Open -160 pts | 60% |
| Beans | Open +10¢ | 66% |
| Beans | Open -10¢ | 71% |

---

### 5.3 Inside Day (ID)

**Definizione:** Un giorno con range completamente **dentro** il range del giorno precedente.
- High < High precedente
- Low > Low precedente

**Perché funziona:**
> *"Un Inside Day è contrazione. In un mercato One-Time Frame, una contrazione di 1 giorno è tutto ciò che serve per innescare un movimento direzionale."*

**Statistiche ID + ORB:**

| Mercato | Entry | % Any Day | % After ID |
|---------|-------|-----------|------------|
| Bonds +16 | BUY | 60% | **76%** |
| Bonds +8 | BUY | 55% | **74%** |
| Beans +10¢ | BUY | 60% | **70%** |
| Beans -10¢ | SELL | 63% | **76%** |

---

### 5.4 ID/NR4 (Inside Day + Narrow Range 4)

**Definizione:** Un Inside Day che è anche il range più stretto degli ultimi 4 giorni.

**IL PATTERN PIÙ POTENTE:**

| Mercato | Entry | % Profit | Win/Loss |
|---------|-------|----------|----------|
| Bonds +16 | BUY | **81%** | 2.34:1 |
| Bonds +8 | BUY | **80%** | 1.18:1 |
| Beans +5¢ | BUY | **71%** | 1.43:1 |
| Beans -10¢ | SELL | **78%** | 0.80:1 |
| Cattle -50 | SELL | **70%** | 1.05:1 |

---

### 5.5 Doji

**Definizione:** Un giorno in cui la differenza tra open e close è **molto piccola** (indica indecisione di mercato).

**Valori Doji per mercato:**
- **Bonds:** 5-8 tics
- **S&P:** 50 punti
- **Beans:** 3-5 cents
- **Cattle:** 25 punti

**Statistiche Doji + ORB:**

| Mercato | Entry | % Normal Day | % After Doji |
|---------|-------|--------------|--------------|
| Bonds -16 | SELL | 56% | **71%** |
| S&P -160 | SELL | 49% | **67%** |
| Beans -10¢ | SELL | 63% | **67%** |

---

### 5.6 Two Bar NR (2 Bar NR)

**Definizione:** Il range combinato di 2 giorni più stretto rispetto a qualsiasi periodo di 2 giorni negli ultimi **20 giorni**.

**Origine concettuale:**
> *"L'idea dietro questo pattern è originata dal Last Point of Supply/Support di Wyckoff - periodi di price action con range insolitamente stretti e basso volume, che si verificano appena prima di una fase di markup/markdown."*

**Statistiche 2 Bar NR:**

| Mercato | Entry | Day 0 | Day 1 | Day 2 | Day 5 |
|---------|-------|-------|-------|-------|-------|
| Bonds +16 | BUY | 76% | 62% | 56% | 56% |
| Bonds -8 | SELL | 75% | 66% | 64% | 64% |
| Euros +8 | BUY | 67% | 67% | 78% | 63% |
| S&P +160 | BUY | 75% | 61% | 64% | 61% |

---

### 5.7 Three Bar NR (3 Bar NR)

**Definizione:** Il range combinato di 3 giorni più stretto rispetto a qualsiasi periodo di 3 giorni negli ultimi **20 giorni**.

> *"Una contrazione di durata maggiore (3 Bar vs 2 Bar) può produrre indicazioni ancora più chiare in certi mercati."*

---

## 6. PATTERN AVANZATI

### 6.1 Early Entry (EE)

**Definizione:** Un grande movimento di prezzo in una direzione entro i **primi 5-10 minuti** dall'apertura.

#### Type 1 Early Entry
- Range della prima barra 5-min maggiore della media
- Open su un estremo, close sull'estremo opposto
- Seconda barra 5-min mostra uguale thrust

#### Type 2 Early Entry
- Range della prima barra 5-min **eccessivamente** grande
- Drift generale nella direzione del thrust
- Accelerazione dopo ulteriore accumulo

### Regola Fondamentale EE:
> *"Nessuna barra 5-min contro la direzione di EE dovrebbe avere un range maggiore della prima barra 5-min. Qualsiasi aumento indica possibile EE Failure."*

---

### 6.2 Bear Hook Day

**Definizione:**
- Open **sotto** il low del giorno precedente
- Close **sopra** la close del giorno precedente
- Range **più stretto** del giorno precedente

**Bias:** RIBASSISTA (13/16 test profittevoli come sell)

| Mercato | Entry | % Profit |
|---------|-------|----------|
| Bonds -8 | SELL | 70% |
| Bonds -16 | SELL | 65% |
| Cattle -50 | SELL | 81% |

---

### 6.3 Bull Hook Day

**Definizione:**
- Open **sopra** l'high del giorno precedente
- Close **sotto** la close del giorno precedente
- Range **più stretto** del giorno precedente

**Bias:** RIALZISTA (meno definito del Bear Hook)

| Mercato | Entry | % Profit |
|---------|-------|----------|
| Bonds +8 | BUY | 74% |
| Cattle +25 | BUY | 78% |
| S&P +160 | BUY | 64% |

---

### 6.4 Upthrust e Spring

**UPTHRUST:**
- Penetrazione sopra un pivot high (massimo precedente)
- Seguita da una chiusura **sotto** quel massimo
- Indica falso breakout rialzista → SELL

**SPRING:**
- Penetrazione sotto un pivot low (minimo precedente)
- Seguita da una chiusura **sopra** quel minimo
- Indica falso breakout ribassista → BUY

**Statistica Springs (S&P 1982-88):**
- 61% winning trades
- Avg Win: $1,190 | Avg Loss: $832

---

## 7. INTEGRAZIONE: DAILY BIAS

### Il Concetto di Daily Bias

> *"Se dovessi riassumere l'esito dei miei studi, sarebbe: Daily Bias. Questo non è inteso come tecnica meccanica, ma come strumento per analizzare le azioni del mercato."*

### I Tre Primari di Mercato Integrati

1. **DIREZIONE** → Close precedente + Open odierno
2. **MOMENTUM** → Dimensione del range (NR7/NR4/NR/WS/WS4/WS7)
3. **PRICE ACTION** → Movimento dall'open (ORB)

### Determinare il Daily Bias

**Step 1:** Controllare pattern 5 giorni (4 chiusure + direzione open)
**Step 2:** Controllare pattern 2 giorni (chiusura ieri + open oggi) con range
**Step 3:** Verificare coerenza: 5/6 pattern devono indicare stessa direzione

### Matrice Trend/Bias

| Trend | Bias | Strategia |
|-------|------|-----------|
| UP | UP | Entry AGGRESSIVO sull'open |
| DOWN | DOWN | Entry AGGRESSIVO sull'open |
| UP | DOWN | Comprare sui break in supporto |
| DOWN | UP | Vendere sui rally in resistenza |

### Regola per Entry sull'Open
> *"Entry sull'open è un play dinamico, riservato a bias e trend chiari. È anche utile quando il mercato sta completando un counter-move - è il punto dove il trend riprende con forza."*

---

## 8. STATISTICHE E TABELLE DI RIFERIMENTO

### Moves Away From the Open

**Principio:** Dopo un movimento definito dall'open, il mercato tende a chiudere nella direzione di quel movimento.

#### BONDS (1978-86)
| Move dall'Open | % Close > Open | % Close > 50% | % Close > Move |
|----------------|----------------|---------------|----------------|
| +8 tics | 75% | 79% | 55% |
| +16 tics | 88% | 88% | 60% |
| +32 tics | 96% | 92% | 58% |
| -8 tics | 78% | 79% | 56% |
| -16 tics | 89% | 88% | 56% |
| -32 tics | 96% | 93% | 53% |

#### S&P (1982-88)
| Move dall'Open | % Close > Open | % Close > 50% | % Close > Move |
|----------------|----------------|---------------|----------------|
| +80 pts | 76% | 68% | 55% |
| +160 pts | 88% | 79% | 58% |
| +300 pts | 93% | 86% | 63% |
| -80 pts | 73% | 64% | 49% |
| -160 pts | 84% | 72% | 49% |
| -300 pts | 91% | 76% | 49% |

#### SOYBEANS (1970-88)
| Move dall'Open | % Close > Open | % Close > 50% | % Close > Move |
|----------------|----------------|---------------|----------------|
| +5¢ | 81% | 79% | 56% |
| +10¢ | 90% | 84% | 60% |
| +15¢ | 93% | 88% | 60% |
| -5¢ | 80% | 82% | 58% |
| -10¢ | 90% | 87% | 63% |
| -15¢ | 94% | 90% | 62% |

---

### Tabella Comparativa Pattern

| Pattern | % Profitto Medio | Frequenza | Best Markets |
|---------|------------------|-----------|--------------|
| ID/NR4 | 70-81% | Raro | Bonds, Beans |
| NR7 | 62-74% | ~1/15 giorni | Tutti |
| NR4 | 60-68% | ~1/8 giorni | Tutti |
| Inside Day | 60-76% | ~1/5 giorni | S&P, Beans |
| Doji + NR | 65-76% | Moderato | Beans |
| 2 Bar NR | 60-76% | ~1/12 giorni | Eurodollars, Bonds |
| Bear Hook | 65-81% | Raro | Bonds, Cattle |

---

## 9. APPLICAZIONE PRATICA

### Checklist Pre-Market

```
□ 1. Identificare il TREND (1-day swings)
□ 2. Controllare il RANGE di ieri (NR7? NR4? WS7? WS4?)
□ 3. Verificare se ieri era INSIDE DAY
□ 4. Controllare pattern DOJI
□ 5. Calcolare lo STRETCH (media 10 giorni)
□ 6. Determinare DAILY BIAS (5-day + 2-day patterns)
□ 7. Preparare livelli ORB (Open ± Stretch)
```

### Regole di Gestione Posizione

**Stop Management:**
> *"In generale, gli stop dovrebbero essere mossi a breakeven entro 1 ora dall'entry. Un mercato con maggiore tendenza al trend dovrebbe avere meno di un'ora."*

**Per S&P:**
> *"L'S&P di solito non richiede più di 5-10 minuti prima che un chiaro getaway avvenga."*

### Criteri per Trade Ideale

1. ✅ Pattern di contrazione presente (ID, NR4, NR7)
2. ✅ Daily bias allineato con trend
3. ✅ Early Entry entro 10 minuti
4. ✅ Nessun aumento di momentum contro la posizione
5. ✅ Profitto visibile quasi istantaneamente

### Warning Signs

- ⚠️ Barre 5-min contro trade con range maggiore della prima barra
- ⚠️ Mercato che torna all'open dopo pattern 2-Bar NR
- ⚠️ ORB dopo expansion day (WS7)
- ⚠️ Terzo retracement nella stessa direzione

---

## 10. GLOSSARIO ESSENZIALE

| Termine | Definizione |
|---------|-------------|
| **ORB** | Opening Range Breakout - trade preso a livello predeterminato dall'open |
| **ORBP** | ORB Preference - ORB unidirezionale con bias chiaro |
| **Stretch** | Media delle distanze open-estremo più vicino (10 giorni) |
| **NR** | Narrow Range - range più stretto del giorno precedente |
| **NR4** | Range più stretto degli ultimi 4 giorni |
| **NR7** | Range più stretto degli ultimi 7 giorni |
| **WS** | Wide Spread - range più ampio del giorno precedente |
| **WS4** | Range più ampio degli ultimi 4 giorni |
| **WS7** | Range più ampio degli ultimi 7 giorni |
| **ID** | Inside Day - high/low dentro il range del giorno precedente |
| **Doji** | Open e close quasi uguali (indecisione) |
| **EE** | Early Entry - grande movimento nei primi 5-10 min |
| **Trend Day** | Prima ora < 10% del range, open/close su estremi opposti |
| **2 Bar NR** | Range 2 giorni più stretto degli ultimi 20 giorni |
| **Spring** | Falso breakout sotto supporto → segnale BUY |
| **Upthrust** | Falso breakout sopra resistenza → segnale SELL |
| **Bear Hook** | Open sotto low prec., close sopra close prec., range stretto |
| **Bull Hook** | Open sopra high prec., close sotto close prec., range stretto |
| **Daily Bias** | Direzione attesa basata su pattern storici |
| **Contraction** | Periodo di riposo/consolidamento (NR, ID) |
| **Expansion** | Periodo di movimento/trend (WS, Trend Day) |

---

## NOTE FINALI

### Filosofia di Crabel

> *"Non sono un system trader. La mia premessa è che il giudizio personale deve entrare nel trade e l'unico modo per farlo efficacemente è attraverso la pratica e l'integrazione logica della conoscenza di mercato disponibile."*

### Avvertenze

1. **Slippage e commissioni** non sono incluse nei test
2. I **pattern meccanici** non dovrebbero essere tradati ciecamente
3. Il **contesto di mercato** deve sempre essere considerato
4. Trend rimane il **primario** e supera tutti gli altri fattori

### Chiave del Successo

> *"Il trader ben allenato riconosce queste opportunità e fornisce la forza che porta il mercato in trend. È ironico che così poco interesse iniziale sia dato al movimento fuori da questo pattern."*

---

*Documento estratto e compilato dal libro "Day Trading with Short Term Price Patterns and Opening Range Breakout" di Toby Crabel (1990)*
