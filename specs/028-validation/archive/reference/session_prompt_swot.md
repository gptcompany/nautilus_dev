# SESSION PROMPT: SWOT Analysis & Cross-Validation
## Adaptive Control Framework - Scientific Validation

---

## CONTEXT

Abbiamo costruito un Adaptive Control Framework per trading algoritmico basato su:
- SOPS + Giller sizing (position sizing adattivo)
- Thompson Sampling / Particle Filter (portfolio allocation)
- IIR / Spectral regime detection
- 5 Pilastri filosofici (Probabilistico, Non-Lineare, Non-Parametrico, Scalare, Leggi Naturali)

**Validazione iniziale** (specs/028-validation/):
- gap_analysis.md: 3 HIGH, 5 MED gaps vs SOTA
- risk_analysis.md: 1 CRITICAL bug (API mismatch), 27 issues totali
- Verdetto: WAIT (fix bug + validate)

**PROBLEMA**: Possibile confirmation bias. Abbiamo cercato paper che CONFERMANO le nostre scelte.

**OBIETTIVO SESSIONE**: Cercare attivamente DISCONFERME e alternative più semplici.

---

## DOCUMENTI DA LEGGERE PRIMA

```
OBBLIGATORI (leggi PRIMA di iniziare):
- specs/028-validation/research_plan_swot.md     # Piano completo + REFERENCE CATALOG
- specs/028-validation/gap_analysis.md           # Gap esistenti (3 HIGH, 5 MED)
- specs/028-validation/risk_analysis.md          # 27 issues identificati
- docs/027-adaptive-control-framework.md         # Architettura attuale

CONTESTO RICERCA:
- docs/research/kelly-vs-giller-analysis.md      # Sizing comparison
- docs/research/adaptive-control-academic-review.md  # 25+ papers già analizzati
- docs/research/MEGA_SYNTHESIS_2026.md           # Sintesi cross-domain
- CLAUDE.md (sezione FUNDAMENTAL PHILOSOPHY)     # 5 Pilastri

CROSS-VALIDATION SOURCE (CRITICO):
- /media/sam/1TB/meta-labeling/README.md         # 4 paper JFDS
- /media/sam/1TB/meta-labeling/calibration_and_position_sizing/  # 6 sizing methods
- /media/sam/1TB/meta-labeling/Meta-labeling Architectures Diagrams*.jpg  # 8 architetture
```

### Reference Catalog Sections (in research_plan_swot.md)
- 1.1 Specifiche Feature (specs/027, specs/028)
- 1.2 Documentazione Architettura
- 1.3 Ricerca Accademica Prodotta
- 1.4 Meta-Labeling Repository (NUOVO)
- 1.5 Codice Implementato (17 moduli)
- 1.6 Risorse Community

---

## FASE 1: COUNTER-EVIDENCE SEARCH (Parallel Tasks)

### TASK A: Academic Critiques
**Agent**: Spawn con `/research` skill o paper-search MCP

```
QUERIES (eseguire tutte):
1. arxiv: "Kelly criterion practical limitations trading"
2. arxiv: "regime detection out of sample performance"
3. arxiv: "position sizing overfitting backtest"
4. arxiv: "Thompson sampling non-stationary bandits failure"
5. SSRN: "backtest overfitting deflated sharpe" (Bailey, Lopez de Prado)
6. semantic: "adaptive portfolio allocation criticism"

OUTPUT: counter_evidence_academic.md
- Per ogni paper critico: titolo, anno, claim principale, rilevanza per noi
- Severity: quanto invalida le nostre assunzioni? (HIGH/MED/LOW)
```

### TASK B: Practitioner Failures
**Agent**: WebSearch + WebFetch

```
QUERIES:
1. "algorithmic trading strategy failed live production"
2. "quant fund failure post mortem analysis"
3. "why my trading system failed"
4. "Quantopian strategy failure lessons"
5. "regime detection trading real world problems"

SOURCES TO CHECK:
- QuantConnect forum
- Elite Trader forum
- r/algotrading
- Risk.net
- Institutional Investor

OUTPUT: counter_evidence_practitioner.md
- Real failure stories
- Common failure patterns
- Lessons learned
```

### TASK C: Alternative Architectures
**Agent**: WebSearch + paper-search

```
QUERIES:
1. "risk parity vs adaptive allocation performance"
2. "equal weight portfolio beats optimization"
3. "simple trading systems outperform complex"
4. "1/N portfolio DeMiguel"
5. "trend following vs adaptive sizing"

OUTPUT: alternative_architectures.md
- Simpler alternatives that might work as well
- Evidence for/against complexity
- Benchmark comparisons
```

### TASK C2: Cross-Validation con Meta-Labeling JFDS
**Agent**: Explore agent o Read diretto

```
COMPARE ARCHITETTURE:
Leggere le 8 immagini in /media/sam/1TB/meta-labeling/Meta-labeling Architectures Diagrams*.jpg
e confrontare con la nostra architettura:

| JFDS Diagram | Nostro Equivalente | Match? | Gap |
|--------------|-------------------|--------|-----|
| 1. Primary Model Base | Strategie primarie | ✓ | - |
| 2. Full Meta-Labeling (M1→M2→M3) | Signal→SOPS→Giller | ✓ | No M2 ML |
| 3. Long/Short Separation | - | ❌ | Non implementato |
| 4. Iterative/Recursive | - | ❌ | Non implementato |
| 5. Regime-Conditioned | IIR + Spectral | ⚠️ | Modelli non separati per regime |
| 6. Ensemble Bagging | Particle Filter | ✓ | - |
| 7. Ensemble Features | Thompson Sampling | ✓ | - |
| 8. Inverse Meta-Labeling | - | ❌ | Avanzato, non implementato |

DOMANDE CRITICHE:
1. Dovremmo implementare Long/Short separation?
2. Regime-conditioned models aggiungerebbe valore?
3. Inverse meta-labeling è overkill o necessario?

OUTPUT: cross_validation_metalabeling.md
```

### TASK C3: Analisi Discord/Community Issues
**Agent**: nautilus-docs-specialist

```
SEARCH IN docs/discord/:
1. "position sizing" issues
2. "regime detection" problems
3. "live trading" failures
4. "backtest vs live" discrepancies
5. "Kelly" discussions

OUTPUT: community_issues_analysis.md
- Real problems encountered by users
- Workarounds used
- Relevance for our system
```

---

## FASE 2: BASELINE IMPLEMENTATION

### TASK D: Implement Simple Baselines
**Agent**: nautilus-coder (se implementazione) o Plan (se design)

```
BASELINES TO COMPARE:
1. Fixed Fractional: size = 2% * equity / risk
2. Equal Weight: 1/N allocation
3. Kelly Classic: f* = (p*b - q) / b
4. Volatility Targeting: size = target_vol / realized_vol

METRICS:
- Sharpe Ratio
- Max Drawdown
- Calmar Ratio
- Win Rate
- Profit Factor

OUTPUT: baseline_comparison.md
- Code snippets for each baseline
- Performance comparison table
- "Is our complexity justified?"
```

---

## FASE 3: STRESS TESTING

### TASK E: Scenario Analysis
**Agent**: alpha-debug o backtest-analyzer

```
SCENARIOS:
1. REGIME_ALWAYS_WRONG: Cosa succede se IIR detector sbaglia sempre?
2. CORRELATION_SPIKE: Tutte le strategie correlate a 0.9
3. LIQUIDITY_DROUGHT: Slippage 10x normale
4. EXCHANGE_OUTAGE: 1h senza dati
5. FLASH_CRASH: Gap -15% in 5 minuti
6. VOLATILITY_EXPLOSION: VIX da 15 a 80

PER OGNI SCENARIO:
- Comportamento atteso del sistema
- Fallback mechanisms
- Worst case loss estimate
- Mitigation possibile

OUTPUT: stress_test_scenarios.md
```

---

## FASE 4: SWOT SYNTHESIS

### TASK F: Consolidate SWOT
**Agent**: Tu (orchestrator)

```
TEMPLATE:

## STRENGTHS (con evidence)
| Strength | Evidence FOR | Evidence AGAINST | Net Assessment |
|----------|--------------|------------------|----------------|
| SOPS adaptive | Paper X | Paper Y | +/- |

## WEAKNESSES (quantificate)
| Weakness | Quantification | Impact | Mitigation |
|----------|----------------|--------|------------|
| 42 parameters | vs 3 for fixed frac | Overfitting risk | Reduce? |

## OPPORTUNITIES (con fattibilità)
| Opportunity | Effort | Expected Benefit | Risk |
|-------------|--------|------------------|------|
| Calibration | 4h | +10% Sharpe? | Low |

## THREATS (con probabilità)
| Threat | Probability | Impact | Mitigation |
|--------|-------------|--------|------------|
| Regime failure | 30%? | -20% DD | Fallback |

OUTPUT: swot_analysis.md
```

---

## FASE 5: FINAL VERDICT

### TASK G: Decision with Uncertainty
**Agent**: Tu

```
TEMPLATE:

## Confidence Assessment

| Component | Confidence | Basis |
|-----------|------------|-------|
| SOPS sizing | X% | N papers support, M against |
| Thompson allocation | X% | ... |
| Regime detection | X% | ... |
| Overall system | X% | ... |

## Decision Matrix

| Confidence | Action |
|------------|--------|
| <50% | STOP - Simplify radically |
| 50-65% | STOP - Need more research |
| 65-80% | WAIT - Fix identified gaps |
| >80% | GO - Paper trading |

## Final Verdict: [GO/WAIT/STOP]

Confidence: X% ± Y%
Key uncertainty: [cosa non sappiamo]
Recommended action: [specifica]
Fallback plan: [se fallisce]

OUTPUT: final_verdict.md
```

---

## REGOLE DI ESECUZIONE

### Delegation Strategy (Agent Mapping Specifico)

```python
# ═══════════════════════════════════════════════════════════
# FASE 1: PARALLEL RESEARCH (spawn tutti insieme)
# ═══════════════════════════════════════════════════════════

PARALLEL_TASKS_PHASE1 = {
    "TASK_A": {
        "description": "Academic critiques search",
        "subagent_type": "general-purpose",  # o usa /research skill
        "tools": ["mcp__paper-search-mcp__search_arxiv",
                  "mcp__paper-search-mcp__search_semantic",
                  "mcp__paper-search-mcp__search_ssrn"],
        "background": True,
        "output": "counter_evidence_academic.md"
    },
    "TASK_B": {
        "description": "Practitioner failures search",
        "subagent_type": "general-purpose",
        "tools": ["WebSearch", "WebFetch"],
        "background": True,
        "output": "counter_evidence_practitioner.md"
    },
    "TASK_C": {
        "description": "Alternative architectures",
        "subagent_type": "general-purpose",
        "tools": ["WebSearch", "mcp__paper-search-mcp__search_arxiv"],
        "background": True,
        "output": "alternative_architectures.md"
    },
    "TASK_C2": {
        "description": "Cross-validation meta-labeling",
        "subagent_type": "Explore",
        "tools": ["Read", "Glob"],
        "path": "/media/sam/1TB/meta-labeling/",
        "background": True,
        "output": "cross_validation_metalabeling.md"
    },
    "TASK_C3": {
        "description": "Discord community issues",
        "subagent_type": "nautilus-docs-specialist",
        "tools": ["Grep", "Read"],
        "path": "docs/discord/",
        "background": True,
        "output": "community_issues_analysis.md"
    }
}

# ═══════════════════════════════════════════════════════════
# FASE 2-5: SEQUENTIAL (dopo Phase 1 completata)
# ═══════════════════════════════════════════════════════════

SEQUENTIAL_TASKS = {
    "TASK_D": {
        "description": "Baseline implementation",
        "subagent_type": "nautilus-coder",
        "or": "Plan",
        "output": "baseline_comparison.md"
    },
    "TASK_E": {
        "description": "Stress test scenarios",
        "subagent_type": "alpha-debug",
        "or": "backtest-analyzer",
        "output": "stress_test_scenarios.md"
    },
    "TASK_F": {
        "description": "SWOT synthesis",
        "subagent_type": None,  # Tu (orchestrator)
        "output": "swot_analysis.md"
    },
    "TASK_G": {
        "description": "Final verdict",
        "subagent_type": None,  # Tu (orchestrator)
        "output": "final_verdict.md"
    }
}
```

### Ensemble dei Findings (FASE CRITICA)

```python
# ═══════════════════════════════════════════════════════════
# ENSEMBLE PHASE: Dopo che tutti i task hanno prodotto output
# ═══════════════════════════════════════════════════════════

ENSEMBLE_INPUTS = [
    "counter_evidence_academic.md",      # TASK A
    "counter_evidence_practitioner.md",  # TASK B
    "alternative_architectures.md",      # TASK C
    "cross_validation_metalabeling.md",  # TASK C2
    "community_issues_analysis.md",      # TASK C3
    "baseline_comparison.md",            # TASK D
    "stress_test_scenarios.md",          # TASK E
]

ENSEMBLE_PROCESS = """
1. LEGGI tutti i 7 output sopra
2. IDENTIFICA contraddizioni tra findings
3. PESO dei findings:
   - Academic papers: weight 0.3 (teoria)
   - Practitioner failures: weight 0.4 (pratica)
   - Community issues: weight 0.3 (real-world)
4. VOTA per ogni componente:
   - SOPS: support_count vs against_count
   - Thompson: support_count vs against_count
   - Regime detection: support_count vs against_count
   - Complessità giustificata: YES/NO/PARTIAL
5. SYNTHESIZE in swot_analysis.md
6. DECIDE in final_verdict.md con confidence interval
"""

ENSEMBLE_OUTPUT_TEMPLATE = """
## Ensemble Findings Summary

### Convergence Analysis
| Topic | Academic | Practitioner | Community | Consensus |
|-------|----------|--------------|-----------|-----------|
| SOPS  | +/-      | +/-          | +/-       | AGREE/DISAGREE |
| ...   | ...      | ...          | ...       | ...       |

### Contradictions Identified
1. [Paper X says Y, but practitioner Z found opposite]
2. ...

### Weighted Verdict
Component | Support | Against | Weight | Net Score
----------|---------|---------|--------|----------
SOPS      | N       | M       | 0.X    | +/-Y
...       | ...     | ...     | ...    | ...

### Confidence Adjustment
- Base confidence: X%
- Adjustment for contradictions: -Y%
- Final confidence: Z% ± W%
"""
```

### Anti-Pattern Avoidance

```
❌ NON cercare solo conferme
❌ NON ignorare paper critici
❌ NON assumere che complessità = meglio
❌ NON saltare i baseline semplici
❌ NON dichiarare confidence senza uncertainty

✅ Cerca attivamente disconferme
✅ Considera alternative più semplici
✅ Quantifica l'incertezza
✅ Ammetti quando non sai
✅ Sii pronto a buttare via componenti
```

### Output Structure

```
specs/028-validation/
│
├── [ESISTENTI]
├── research_plan_swot.md          # Piano completo + Reference Catalog
├── session_prompt_swot.md         # Questo prompt
├── gap_analysis.md                # Gap iniziale vs SOTA
├── risk_analysis.md               # Code review 27 issues
├── executive_summary.md           # Verdetto WAIT iniziale
├── action_items.md                # Priorità fix
│
├── [DA FASE 1 - PARALLEL]
├── counter_evidence_academic.md   # TASK A: Paper critici
├── counter_evidence_practitioner.md # TASK B: Failure stories
├── alternative_architectures.md   # TASK C: Simpler alternatives
├── cross_validation_metalabeling.md # TASK C2: vs 8 JFDS architectures
├── community_issues_analysis.md   # TASK C3: Discord/real-world
│
├── [DA FASE 2-5 - SEQUENTIAL]
├── baseline_comparison.md         # TASK D: Simple vs complex
├── stress_test_scenarios.md       # TASK E: 6 failure scenarios
│
├── [DA ENSEMBLE + VERDICT]
├── swot_analysis.md               # TASK F: 4 quadranti + ensemble
└── final_verdict.md               # TASK G: GO/WAIT/STOP + confidence
```

**Total output files**: 9 nuovi + 6 esistenti = 15 files

---

## SUCCESS CRITERIA

```python
SESSION_SUCCESS = (
    # Fase 1: Counter-evidence
    len(counter_evidence_papers) >= 5 AND
    len(failure_stories) >= 3 AND
    len(simple_alternatives_compared) >= 3 AND
    metalabeling_crossval_complete AND          # TASK C2
    community_issues_analyzed AND                # TASK C3

    # Fase 2-3: Validation
    len(baselines_compared) >= 3 AND
    len(stress_scenarios_analyzed) >= 5 AND

    # Fase 4-5: Synthesis
    ensemble_findings_consolidated AND           # NUOVO
    contradictions_identified AND                # NUOVO
    swot_all_quadrants_filled AND
    confidence_interval_stated AND
    uncertainty_acknowledged AND
    decision_made_with_fallback_plan             # NUOVO
)
```

### Quantitative Thresholds

```python
MINIMUM_THRESHOLDS = {
    "counter_evidence_papers": 5,
    "failure_stories": 3,
    "alternatives_compared": 3,
    "metalabeling_diagrams_analyzed": 8,        # Tutti e 8
    "discord_searches": 5,
    "baselines": 4,                              # Fixed, Equal, Kelly, VolTarget
    "stress_scenarios": 6,
    "swot_cells_filled": 16,                     # 4x4 minimum
    "confidence_decimal_places": 1,              # Es: 72.5%
    "uncertainty_band": True,                    # Es: ±10%
}
```

---

## ESTIMATED TIME

| Phase | Tasks | Time | Parallel? |
|-------|-------|------|-----------|
| 1 | A, B, C, C2, C3 | 45 min | ✓ YES (5 agents) |
| 2 | D (baselines) | 30 min | Sequential |
| 3 | E (stress test) | 45 min | Sequential |
| 4 | F (SWOT + ensemble) | 45 min | Sequential |
| 5 | G (verdict) | 15 min | Sequential |
| **Total** | | **~3 hours** | |

---

## START COMMAND

```bash
# 1. Leggi i documenti obbligatori
Read specs/028-validation/research_plan_swot.md  # Reference Catalog completo
Read specs/028-validation/session_prompt_swot.md  # Questo prompt

# 2. Lancia FASE 1 in parallelo (5 Task agents)
Task(TASK_A, subagent="general-purpose", background=True)
Task(TASK_B, subagent="general-purpose", background=True)
Task(TASK_C, subagent="general-purpose", background=True)
Task(TASK_C2, subagent="Explore", background=True)
Task(TASK_C3, subagent="nautilus-docs-specialist", background=True)

# 3. Attendi completamento FASE 1
TaskOutput(TASK_A, block=True)
TaskOutput(TASK_B, block=True)
TaskOutput(TASK_C, block=True)
TaskOutput(TASK_C2, block=True)
TaskOutput(TASK_C3, block=True)

# 4. Esegui FASE 2-5 sequenzialmente
Execute TASK_D (baselines)
Execute TASK_E (stress test)
Execute TASK_F (SWOT + ensemble synthesis)
Execute TASK_G (final verdict)

# 5. Output finale
Write final_verdict.md con:
- Confidence: X% ± Y%
- Decision: GO/WAIT/STOP
- Key uncertainties
- Fallback plan
```

---

## CHECKLIST PRE-SESSIONE

```
[ ] Reference catalog letto e compreso
[ ] Meta-labeling repo accessibile (/media/sam/1TB/meta-labeling/)
[ ] 8 JFDS diagrams disponibili
[ ] Discord docs disponibili (docs/discord/)
[ ] Tutti gli agent types verificati disponibili
[ ] Tempo stimato ~3h disponibile
[ ] Mentalità: "prove me wrong" attiva
```
