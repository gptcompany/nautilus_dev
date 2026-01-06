Master Document: Quantitative Trading & Signal Processing (Versione Compatibile)
1. Fondamenta Statistiche e Probabilistiche
Teorema di Bayes e Validazione del Segnale
Analisi della reale capacità predittiva di un indicatore.

Matrice di Confusione (Esempio Reale):

True Positive Rate: 99%

False Positive Rate: 20%

Base Rate (Probabilità a priori P(R)): 9,6%

Calcolo della Probabilità condizionata P(R|Signal): P(Signal) = P(Signal|R) × P(R) + P(Signal|not R) × P(not R) P(Signal) = 0.99 × 0.096 + 0.20 × 0.904 = 0.276 P(R|Signal) = [0.99 × 0.096] / 0.276 = 34,4%

Conclusione: Anche con un segnale accurato al 99%, se l'evento è raro, la probabilità reale è bassa.

Prosecutor's Fallacy: Non confondere P(Dati | Ipotesi) con P(Ipotesi | Dati).

Monte Carlo Simulation (MCS)
Formulare variabili target e Fattori di Rischio.

Specificare la distribuzione (Student-t, Cauchy, ecc.).

Attenzione alla Multicollinearità e all'Autocorrelazione temporale.

2. Advanced Signal Processing
Decomposizione (EMD & HHT)
EMD: Decompone la serie in oscillazioni a media zero (IMF).

TV-EMD (Time Varying):

Usa un filtro di Kalman per il VWAP.

Calcola il rapporto tra frequenze alte: Ratio = HF1 / HF2.

Serve a misurare la deviazione significativa dal rumore.

Volume Clocks
Problema: Il tempo cronologico è fuorviante (spread e volatilità variabili).

Soluzione: Usare "Volume Clocks" (barre a volume costante).

Relative Volume Bin: Dividere il volume totale per la frequenza EMD (DHF) per ottenere una risposta fluida.

3. Strategie di Pattern Recognition
k-NN Pattern Mining (Approccio Qusma)
Input (11 numeri): Rendimenti G1-G2, G2-G3 e valori OHLC dei 3 giorni.

Metodo: Trova i "k" pattern storici più simili (minima differenza quadrata).

Regola: Se il rendimento medio futuro dei simili è > 0,2% -> LONG.

Filtri:

IBS < 0.5 per Long.

Leva = Target Annuale / (Volatilità 10gg × radice(252)).

Mean Reversion con IBS
Formula: IBS = (Close - Low) / (High - Low)

Setup:

Qusma: Long QQQ se IBS < 0.50 e RSI(3) < 10.

Adaptive: Long SPY se IBS < 0.45 (Exit > 0.75).

4. Identificazione Trend e Catastrofi
CUSCORE (Cumulative Score)
Per rilevare il cambio di pendenza (beta) del trend.

Formula: Q = Somma( (y_t - beta × t) × t )

Modifica Reattiva: beta_stimato = 0.25 × (EWMA_corrente - EWMA_4_periodi_fa)

Archetipo della Catastrofe
Accumulo lento (A-B-C) seguito da Salto (D).

Ingresso all'80° percentile della durata storica del trend.

5. Microstruttura e Order Book
Micro-Price: Variazione Mid-Price pesata sui volumi LOB.

Imbalance: Filtrare il trade se lo spostamento di prezzo > (Step × Commissioni).

Crypto: Monitorare Funding Rate, Open Interest e Liquidazioni.

6. Ottimizzazione (Machine Learning)
Funzione di Costo Regolarizzata (Tikhonov)
Serve per trovare la soglia (threshold) ottimale evitando l'overfitting.

Formula: Costo = Errore_Quadratico + lambda × (Penalità_Rugosità)

Minimizzando questa funzione si ottiene una curva di profitto stabile e non casuale.

Feature List
Trend Deviation: log(Close) / Prezzo_Filtrato

Velocity: Previsione regressione lineare a 1 step.

Variance Ratio: Varianza Breve / Varianza Lunga.

Hurst Exponent: Persistenza del trend.

Questa versione puoi copiarla e incollarla direttamente su Word o Google Docs e i simboli (come ×, beta, ecc.) rimarranno corretti.