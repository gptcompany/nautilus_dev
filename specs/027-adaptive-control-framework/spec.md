# Spec 027: Adaptive Control Trading Framework

**Status**: Draft
**Priority**: High
**Complexity**: Medium
**Dependencies**: NautilusTrader nightly, NumPy, SciPy, python-control (optional)

## Overview

Framework di **Systems Control e DSP** per trading algoritmico adattivo. Usa teoria del controllo (PID, Kalman, State Machines) e signal processing (FFT, Wavelets) con ispirazione dalle leggi naturali universali per la filosofia di design.

**Approccio**: Natural Laws come FILOSOFIA, Systems Control come IMPLEMENTAZIONE.

## Fondamento Scientifico

### Le Leggi Universali

| Sistema | Legge | Esponente | Applicazione Trading |
|---------|-------|-----------|---------------------|
| Biologia | Kleiber (Metabolismo ∝ Massa^0.75) | 0.75 | Position sizing |
| Lingua | Zipf (Frequenza ∝ Rango^-1) | -1.0 | Order flow distribution |
| Mercati | 1/f noise (PSD ∝ f^-α) | ~1.0 | Regime detection |
| Musica | Armonica (f_n = n × f_1) | integers | Multi-timeframe alignment |
| HRV | Pink noise in healthy systems | ~1.0 | System health |

### Citazioni Chiave

- **West (2017)**: "Scale" - Networks from cells to cities follow universal scaling laws
- **Mandelbrot (1963)**: Markets exhibit 1/f noise, not Gaussian random walks
- **Porges (2011)**: Polyvagal Theory - HRV reflects autonomic state

## Functional Requirements

### FR-1: System Health Monitor (SystemHRV)

Monitor continuo della "salute" dell'infrastruttura di trading.

```python
@dataclass
class SystemHRV:
    """Trading system vital signs - analogous to Heart Rate Variability."""

    # Latency metrics (like RR intervals)
    latency_mean_ms: float
    latency_std_ms: float
    latency_rmssd: float  # Root Mean Square of Successive Differences

    # PnL metrics (like heart rate coherence)
    pnl_volatility: float
    sharpe_rolling_30d: float
    max_drawdown_current: float

    # Strategy correlation (like HRV coherence)
    strategy_correlation_matrix: np.ndarray
    avg_inter_strategy_corr: float

    # System stress indicators
    order_rejection_rate: float
    slippage_ratio: float  # actual_fill / expected_fill
    reconnection_count_24h: int

    def health_state(self) -> Literal["VENTRAL", "SYMPATHETIC", "DORSAL"]:
        """Map system state to polyvagal states."""
        if self._is_optimal():
            return "VENTRAL"      # All systems nominal
        elif self._is_stressed():
            return "SYMPATHETIC"  # High alert, reduce risk
        else:
            return "DORSAL"       # Freeze, stop trading
```

**Acceptance Criteria**:
- [ ] Calcola metriche ogni 1 minuto
- [ ] Mantiene rolling window di 24h
- [ ] Emette alert su state change
- [ ] Espone via HTTP/WebSocket per Grafana

### FR-2: Power Law Position Sizing

Position sizing basato su Kleiber's Law: smaller accounts take proportionally more risk.

```python
def calculate_position_size_kleiber(
    equity: float,
    base_risk_pct: float = 0.01,
    reference_equity: float = 100_000,
    exponent: float = 0.75
) -> float:
    """
    Kleiber-inspired position sizing.

    Metabolismo ∝ Massa^0.75
    → Risk allocation ∝ Equity^0.75

    Result: €10k account risks 1.78% per trade
            €100k account risks 1.00% per trade
            €1M account risks 0.56% per trade
    """
    scaling_factor = (equity / reference_equity) ** exponent
    risk_pct = base_risk_pct * scaling_factor
    return equity * risk_pct
```

**Acceptance Criteria**:
- [ ] Integrato con NautilusTrader position sizing
- [ ] Configurabile exponent (default 0.75)
- [ ] Log ogni sizing decision con rationale

### FR-3: 1/f Noise Regime Detector

Rileva regime di mercato basandosi sullo slope spettrale.

```python
def detect_regime_spectral(
    returns: np.ndarray,
    window: int = 256
) -> Tuple[str, float]:
    """
    Analyze spectral slope to detect market regime.

    α ≈ 0: White noise → Mean reversion dominates
    α ≈ 1: Pink noise → Normal market (1/f)
    α ≈ 2: Brown noise → Trending market

    Returns: (regime_name, alpha_value)
    """
    freqs, psd = scipy.signal.welch(returns, fs=1.0, nperseg=window)

    # Fit log-log slope (exclude DC component)
    mask = freqs > 0
    log_f = np.log(freqs[mask])
    log_psd = np.log(psd[mask])

    slope, intercept = np.polyfit(log_f, log_psd, 1)
    alpha = -slope

    if alpha < 0.5:
        regime = "WHITE_NOISE"      # Mean reversion
    elif alpha < 1.5:
        regime = "PINK_NOISE"       # Normal (optimal)
    else:
        regime = "BROWN_NOISE"      # Trending

    return regime, alpha
```

**Acceptance Criteria**:
- [ ] Calcola su rolling window configurabile
- [ ] Output compatibile con strategy signals
- [ ] Backtest validation su BTC 2020-2024

### FR-4: Harmonic Multi-Timeframe Analyzer

Analizza allineamento armonico tra timeframes (come consonanza musicale).

```python
def calculate_harmonic_alignment(
    signals: Dict[str, float]  # {"1m": 0.7, "5m": 0.3, "1h": -0.2}
) -> Tuple[float, str]:
    """
    Calculate harmonic alignment between timeframes.

    Musical consonance ratios: 1:2 (octave), 2:3 (fifth), 3:4 (fourth)

    In trading: Higher timeframe confirmation = stronger signal

    Returns: (alignment_score, interpretation)
    """
    # Weight higher timeframes more (like harmonic series 1/n)
    weights = {"1m": 1/4, "5m": 1/3, "15m": 1/2, "1h": 1, "4h": 2, "1d": 4}

    weighted_sum = sum(signals.get(tf, 0) * weights.get(tf, 1)
                       for tf in signals)
    total_weight = sum(weights.get(tf, 1) for tf in signals)

    alignment = weighted_sum / total_weight

    if abs(alignment) > 0.7:
        interp = "CONSONANT"    # Strong alignment
    elif abs(alignment) > 0.3:
        interp = "PARTIAL"      # Mixed signals
    else:
        interp = "DISSONANT"    # Conflicting signals

    return alignment, interp
```

**Acceptance Criteria**:
- [ ] Integrato con NautilusTrader indicator framework
- [ ] Supporta timeframes configurabili
- [ ] Emette signal strength multiplier

## Non-Functional Requirements

### NFR-1: Performance
- SystemHRV calculation < 10ms
- Spectral analysis < 50ms per window
- No memory leaks in 24h continuous operation

### NFR-2: Reliability
- Graceful degradation se dati mancanti
- Fallback a sizing conservativo se SystemHRV unavailable
- All state changes logged

### NFR-3: Observability
- Grafana dashboard per System Health
- Prometheus metrics export
- Alert integration (Telegram/Discord)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TradingNode                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Strategy   │  │  Strategy   │  │  Natural Laws       │  │
│  │     A       │  │     B       │  │  Framework          │  │
│  └──────┬──────┘  └──────┬──────┘  │                     │  │
│         │                │         │  ┌─────────────────┐│  │
│         │                │         │  │ SystemHRV       ││  │
│         │                │         │  │ Monitor         ││  │
│         │                │         │  └────────┬────────┘│  │
│         │                │         │           │         │  │
│         │                │         │  ┌────────▼────────┐│  │
│         │                │         │  │ Power Law       ││  │
│         │◄───────────────┼─────────┼──│ Position Sizer  ││  │
│         │                │         │  └────────┬────────┘│  │
│         │                │         │           │         │  │
│         │                │         │  ┌────────▼────────┐│  │
│         │◄───────────────┼─────────┼──│ Regime          ││  │
│         │                │         │  │ Detector (1/f)  ││  │
│         │                │         │  └────────┬────────┘│  │
│         │                │         │           │         │  │
│         │                │         │  ┌────────▼────────┐│  │
│         │◄───────────────┼─────────┼──│ Harmonic        ││  │
│         │                │         │  │ Analyzer        ││  │
│         │                │         │  └─────────────────┘│  │
│         │                │         └─────────────────────┘  │
│         ▼                ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Execution Engine                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
- [ ] `SystemHRV` dataclass and calculator
- [ ] Latency tracking integration
- [ ] Basic health state machine

### Phase 2: Position Sizing (Week 2)
- [ ] `KleiberPositionSizer` component
- [ ] Integration with existing RiskManager
- [ ] Unit tests with various equity levels

### Phase 3: Regime Detection (Week 3)
- [ ] `SpectralRegimeDetector` indicator
- [ ] Rolling window implementation
- [ ] Backtest on historical data

### Phase 4: Harmonic Analysis (Week 4)
- [ ] `HarmonicAlignmentIndicator`
- [ ] Multi-timeframe data subscription
- [ ] Signal integration with strategies

### Phase 5: Integration & Dashboard (Week 5)
- [ ] Full integration test
- [ ] Grafana dashboard
- [ ] Documentation

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Position sizing accuracy | ±2% of Kleiber calculation | Unit tests |
| Regime detection latency | < 50ms | Performance profiling |
| System health uptime | 99.9% | Monitoring |
| False positive regime changes | < 5% | Backtest validation |

## References

1. West, G. (2017). "Scale: The Universal Laws of Growth" - ISBN 978-1594205583
2. Mandelbrot, B. (1963). "The Variation of Certain Speculative Prices" - Journal of Business
3. Porges, S. (2011). "The Polyvagal Theory" - W.W. Norton
4. Lux, T. & Marchesi, M. (1999). "Scaling and criticality in a stochastic multi-agent model" - Nature
5. Kleiber, M. (1932). "Body size and metabolism" - Hilgardia

---

*Spec created: 2026-01-04*
*Framework: Natural Laws applied to algorithmic trading*
