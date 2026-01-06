# AlphaEvolve Discovery Prompt

## EXTREME EDGE DISCOVERY PROTOCOL

### Obiettivo
Cerca informazioni all'ESTREMO della curva distributiva - non il consenso,
ma le code. Dove la probabilita e bassa ma l'insight e massimo.

### Parametri di Ricerca

**DISTRIBUZIONE TARGET**: p < 0.05 (tail della conoscenza)

**CERCA**:
- Idee che il 95% ignora ma il 5% geniale usa
- Connessioni cross-domain che nessuno ha fatto
- Fallimenti da cui nessuno ha estratto lezioni
- Pattern nascosti in plain sight
- Contraddizioni che rivelano verita profonde

**EVITA**:
- Consenso mainstream
- "Best practices" ripetute
- Tutorial standard
- Opinioni popolari

### Domande Generatrici

1. Cosa sanno i MIGLIORI che gli altri non sanno?
2. Quale FALLIMENTO contiene l'insight piu prezioso?
3. Quale CONNESSIONE tra domini diversi nessuno ha esplorato?
4. Cosa e OVVIO ma nessuno dice?
5. Dove il RUMORE nasconde il segnale?

### Output Atteso

Per ogni discovery:
- **INSIGHT**: [cosa hai trovato]
- **EDGE SCORE**: [quanto e estremo, 1-10]
- **CONNESSIONE**: [come si collega al nostro framework]
- **AZIONE**: [cosa possiamo derivare concretamente]

### Contesto

- **Framework**: Trading system P3-compliant (zero params fissi)
- **Ispirazione**: Dilla (timing derivato dal contesto, non quantizzato)
- **Obiettivo**: Derivare TUTTO dai dati, come un musicista sente il groove

### Fitness Function

```
fitness = (novelty * actionability * connection_strength) / mainstream_probability
```

Massimizza fitness. Cerca gli outlier.

---

## AVVERTENZE PER ME STESSA (Aggiunto 2026-01-05)

1. **Sii scettica** - Ogni risultato positivo nel backtest e sospetto
2. **Cerca disconferme** - Prima di validare, cerca chi dice che fallisce
3. **Baselines first** - Se 1/N batte il sistema complesso, usa 1/N
4. **Complexity debt** - Ogni parametro aggiunto e debito da pagare
5. **OOS is truth** - In-sample means nothing. Solo OOS conta.

---

## Update: Ricerca Disconfermante (2026-01-05)

### Probabilita Combinata di Successo: 1-3%

| Componente | P(Success) | Evidenza Contro |
|------------|------------|-----------------|
| Adaptive systems | 15% | Knight Capital ($440M loss), Flash Crash |
| Regime detection | 20% | HMM fails OOS, always late |
| Kelly criterion | 10% | Parameter error = ruin |
| Thompson Sampling | 25% | Assumes stationarity (false in markets) |
| Power law sizing | 5% | Zero independent validation |
| Entropy-based | 15% | Can't prevent overfitting |

### Fonti Chiave

- [Systemic failures in algorithmic trading (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8978471/)
- [Rage Against the Regimes (QuantConnect)](https://www.quantconnect.com/forum/discussion/14818/)
- [Kelly Criterion - QuantStart](https://www.quantstart.com/articles/Money-Management-via-the-Kelly-Criterion/)
- DeMiguel 2009: 1/N beats 14 optimization models

### Verdetto

Prima di procedere con P3 framework:
1. **Test baseline 1/N** vs sistema complesso
2. **Se 1/N vince OOS**: STOP, usa 1/N
3. **Parametri fissi di sicurezza**: max leverage, stop loss (non adattivi)
