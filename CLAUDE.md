# CLAUDE.md

> **PRODUCTION TRADING SYSTEM - HANDLES REAL MONEY**
>
> This system trades with REAL CAPITAL. Every code change can result in FINANCIAL LOSS.
>
> **NON-NEGOTIABLE RULES:**
> 1. **90% test coverage** for critical modules (risk/, recovery/, position_sizing/)
> 2. **NO shortcuts** - if unsure, ASK before implementing
> 3. **NO untested code** in production paths
> 4. **ALL safety limits are FIXED** - never make them adaptive
> 5. **Knight Capital lost $440M in 45 minutes** from a code bug - RESPECT THE RISK

---

## Project Overview
**NautilusTrader Documentation Hub** - High-performance algo trading (Python frontend + Rust core).

**Philosophy**: KISS + YAGNI + **PMW (Prove Me Wrong)** - Seek disconfirmation, not confirmation.

**Key Rules**: Native Rust indicators only | Parquet/DuckDB streaming | Black Box Design | No df.iterrows()

---

## Core Philosophy

### PMW: Prove Me Wrong
Before validating any system: search for **contradicting evidence**, failure stories, simpler alternatives.
```
1. COUNTER-EVIDENCE: arXiv critiques, practitioner failures, alternatives
2. SWOT: Strengths, Weaknesses, Opportunities, Threats
3. VERDICT: GO | WAIT | STOP
```
**Ref**: `specs/028-validation/session_prompt_swot.md`

### Adaptive Signals, Fixed Safety
**Four Pillars**: Probabilistic | Non-linear (power laws) | Non-parametric | Scale-invariant

```python
# Signal params: ADAPTIVE (data-driven)
alpha = 2.0 / (N + 1)       # From data characteristics
threshold = mean + 2 * std   # Dynamic

# Safety params: FIXED (prevent ruin - Knight Capital lost $440M)
MAX_LEVERAGE, MAX_POSITION_PCT = 3, 10    # NEVER adaptive
STOP_LOSS_PCT, DAILY_LOSS_LIMIT_PCT = 5, 2
KILL_SWITCH_DRAWDOWN = 15
```
**Ref**: `strategies/common/adaptive_control/`

---

## Tech Stack

**Environment**: Python 3.11+ | Nightly v1.222.0 | 128-bit precision
```bash
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
```

**Constraints**: V1 Wranglers only (V2 incompatible) | Stable catalogs incompatible with nightly

**Long processes**: Always `setsid cmd >> /tmp/log.log 2>&1 &`

### Stable vs Nightly
| Aspect | Stable | Nightly (US) |
|--------|--------|--------------|
| Release | Weeks/months | Daily |
| Breaking Changes | Rare | Frequent |
| Precision | 64-bit | 128-bit (Linux) |
| Schema | Stable | Evolves |

> **P5 "Leggi Naturali" REMOVED** (2026-01-05): PMW found ZERO evidence for Fibonacci/waves.
> Fractals (Mandelbrot) valid under P2. See `specs/028-validation/research_vs_repos_analysis.md`

---

## Known Issues (Discord)

| Adapter | Issue |
|---------|-------|
| Binance | ADL handling, Chinese tokens, STOP_MARKET needs Algo API |
| Bybit | No hedge mode, bar timestamp issues, 1-bar offset |
| IB | Reconciliation issues, tick request limits |

---

## Patterns

### Data (NO df.iterrows, NO in-memory loading)
```python
catalog = ParquetDataCatalog("./catalog")
for bar in catalog.bars(): process(bar)  # Streaming
```

### Strategy Template
```python
class MyStrategy(Strategy):
    def on_start(self):
        self.ema = ExponentialMovingAverage(period=20)  # Native Rust
    def on_data(self, data):
        self.ema.handle_bar(data)
        if self._signal(data): self._execute(data)
```

### Live Trading Warmup
```python
def on_start(self):
    self.request_bars(bar_type, start=now-timedelta(days=2), callback=self._warmup)
def on_historical_data(self, data):
    for bar in data.bars: self.ema.handle_bar(bar)
```

### TradingNode Config
```python
config = TradingNodeConfig(
    trader_id="TRADER-001",
    cache=CacheConfig(database=DatabaseConfig(host="localhost", port=6379), persist_account_events=True),
    exec_engine=LiveExecEngineConfig(reconciliation=True, reconciliation_startup_delay_secs=10.0),
)
```

**Redis**: `config/cache/docker-compose.redis.yml` | Docs: `docs/018-*.md`
**Shutdown**: `config/shutdown/GracefulShutdownHandler` | Docs: `docs/019-*.md`

---

## Repository Structure
```
nautilus_dev/
├── docs/{ARCHITECTURE.md, discord/, nautilus/, research/}
├── strategies/{production/, development/, evolved/, converted/, archive/, common/}
├── config/, scripts/, specs/
└── .claude/{agents/, commands/, skills/}
```
**Architecture**: See `docs/ARCHITECTURE.md` (auto-validated on commit)

---

## Agents & Skills

> **Context Optimization**: NEVER read large docs/logs directly - delegate to agents.
> Main context = orchestration only. Agents have their own context windows.

| Agent | Use For |
|-------|---------|
| nautilus-coder | Strategy implementation (Context7) |
| nautilus-docs-specialist | Doc search (delegate FIRST) |
| nautilus-data-pipeline-operator | Data pipeline management |
| nautilus-live-operator | Live trading operations |
| nautilus-visualization-renderer | Charts & dashboards |
| backtest-analyzer | Log analysis (chunked) |
| test-runner | Test execution (ALWAYS use) |
| tdd-guard | TDD enforcement (Red-Green-Refactor) |
| alpha-debug | Bug hunting (2-10 rounds, auto-triggered) |
| alpha-evolve | Multi-implementation generator ([E] marker) |
| alpha-visual | Visual validation with screenshots |
| strategy-researcher | Paper→spec conversion |

**Alpha-Debug Stop**: MAX_ROUNDS | 2 clean rounds | 95% confidence | Tests failing→human

| Skill | Savings |
|-------|---------|
| pytest-test-generator | 83% |
| github-workflow | 79% |
| pydantic-model-generator | 75% |
| paper-to-strategy | 70% |
| /research, /pinescript | 60-65% |

**Pre-Planning**: ALWAYS delegate to `nautilus-docs-specialist` first (Discord + Context7)

**Search Workflow**: Discord (bugs) → Context7 (API) → backtest-analyzer (logs) → alpha-debug (code)

---

## Development Rules

### NEVER
- `--no-verify` | `df.iterrows()` | Reimplement Rust indicators
- Create reports/docs unless requested | Execute tests directly (use agent)
- Adaptive safety limits | Lookahead bias | Partial implementations

### ALWAYS
- Search docs first (Context7, Discord) | Use native Rust indicators
- Run tests via test-runner agent | Use `uv` (not pip) | Format: `ruff check . && ruff format .`
- Verify library APIs before implementing | Fail fast on invalid config

### Spec vs Direct Fix
- `< 4h + existing code` -> Fix directly
- `> 4h + new module` -> `/speckit:specify` first

---

## Architecture Principles (Black Box - Eskil Steenberg)
- **Black Box Interfaces**: Clean APIs, hidden implementation
- **Everything Replaceable**: Don't understand it? Rewrite it
- **Constant Velocity**: 5 complete lines today > 1 line + future edits
- **Single Responsibility**: One strategy = one trading logic

## Code Style
- PEP 8, type hints, docstrings for public APIs
- Naming: `{Exchange}{Asset}{Strategy}Strategy` | `calculate_position_size()` not `calc_pos()`
- Functions <= 50 lines

**When Stuck**: Max 3 attempts per issue, then document and ask for help

## Error Handling
- **Fail fast**: Invalid config (symbols, sizes, API keys)
- **Retry 3x**: Transient errors (network, rate limits)
- **Degrade**: Optional features (fallback indicators)
- **No silent failures**: Always log or raise

## Edge Cases
Empty inputs | Extreme values | Invalid states | Concurrency

---

## Tone
Concise | Skeptical | Direct | Ask questions when unclear

**Remember**: Search docs first. Native Rust. No df.iterrows(). Test via agent.
