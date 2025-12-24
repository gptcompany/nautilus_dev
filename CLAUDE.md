# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NautilusTrader Documentation Hub** - A centralized repository for NautilusTrader documentation, Discord community knowledge, and trading strategy development resources.

**Key Principles**:
- High-performance algorithmic trading (Python frontend + Rust core)
- Black Box Design (Eskil Steenberg principles)
- Native Rust indicators (never reimplement)
- Parquet/DuckDB for data (streaming, not in-memory)

**Development Philosophy**: KISS (Keep It Simple) + YAGNI (You Ain't Gonna Need It)

## Tech Stack

> **Full Architecture Details**: See `docs/ARCHITECTURE.md` for wrangler compatibility, data pipeline, and storage locations.

**NautilusTrader**:
- **Python 3.11+** frontend with **Rust core** (100x faster than pure Python)
- **Parquet/DuckDB** for data (streaming, not in-memory)
- **Native Rust indicators** (EMA, RSI, etc.) - black boxes, never reimplement
- **Exchange adapters**: Binance, Bybit, OKX, Interactive Brokers
- **BacktestNode** (simulation), **TradingNode** (live execution)

**Nightly Environment** (v1.222.0):
```bash
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
```

**CRITICAL CONSTRAINTS** (verified 2025-12-24):
- Use **V1 Wranglers only** - V2 (PyO3) incompatible with BacktestEngine
- Use **128-bit precision** - Linux nightly default
- Stable catalogs **INCOMPATIBLE** with nightly (schema mismatch)

## Repository Organization

```
nautilus_dev/
├── CLAUDE.md                 # THIS FILE (dev guidelines)
├── docs/
│   ├── ARCHITECTURE.md       # Technical architecture (wranglers, data pipeline)
│   ├── api_reference/        # API documentation
│   ├── concepts/             # Core concepts
│   ├── developer_guide/      # Developer guides
│   ├── discord/              # Discord community knowledge (420K, 90-day window)
│   │   ├── questions.md      # Q&A patterns (2991 lines)
│   │   ├── help.md           # Help & troubleshooting (2825 lines)
│   │   ├── general.md        # General discussions (1203 lines)
│   │   ├── data.md           # Data management (695 lines)
│   │   ├── dev-rust.md       # Rust development (545 lines)
│   │   ├── performance.md    # Performance tips
│   │   ├── binance.md, bybit.md, okx.md, dydx.md  # Exchange-specific
│   │   └── visualization.md  # Visualization discussions (NEW)
│   ├── integrations/         # Exchange adapter docs
│   ├── nautilus/             # Changelog & version tracking
│   │   ├── nautilus-trader-changelog.md
│   │   └── nautilus-trader-changelog.json
│   └── tutorials/            # Tutorials
├── feeds/                    # Data feeds
├── context/                  # Context files
├── .claude/
│   ├── agents/               # Subagent definitions (11 agents)
│   ├── commands/             # Slash commands (SpecKit)
│   ├── skills/               # Token-saving skills (3)
│   └── settings.local.json   # Project settings
├── .specify/                 # SpecKit templates
│   ├── templates/            # spec, plan, tasks, checklist
│   └── memory/               # Project constitution
└── .serena/                  # Serena MCP config
```

## Agent Architecture

### Subagents (11)

| Agent | Responsibility |
|-------|----------------|
| nautilus-coder | Strategy implementation (Context7 for docs) |
| nautilus-docs-specialist | Documentation search workflow |
| nautilus-data-pipeline-operator | Data pipeline management |
| nautilus-live-operator | Live trading operations |
| nautilus-visualization-renderer | Trading charts & dashboards |
| backtest-analyzer | Log analysis with chunking strategy |
| test-runner | Test execution (ALWAYS use for tests) |
| tdd-guard | TDD enforcement (Red-Green-Refactor) |
| alpha-debug | Iterative bug hunting (auto-triggered) |
| alpha-evolve | Multi-implementation generator ([E] marker) |
| alpha-visual | Visual validation with screenshots |

### Skills (3)

| Skill | Purpose | Token Savings |
|-------|---------|---------------|
| pytest-test-generator | Test boilerplate | 83% |
| github-workflow | PR/Issue/Commit templates | 79% |
| pydantic-model-generator | Config models | 75% |

### Alpha-Debug (Auto-Triggered)

Finds bugs even when tests pass. Triggers automatically after implementation phases.

**Dynamic Rounds** (complexity-based): 2-10 rounds based on lines changed and files modified.

**Stop Conditions**:
1. MAX_ROUNDS reached
2. 2 consecutive clean rounds
3. Confidence >= 95%
4. Tests failing -> human intervention

### Pre-Planning Research (MANDATORY)

**BEFORE any `/speckit.plan`, implementation, or task execution**:

1. **Delegate to `nautilus-docs-specialist`** for comprehensive documentation search
2. **Search `docs/discord/`** for recent discussions on the topic
3. **Check `docs/nautilus/`** for version-specific breaking changes
4. **Use Context7** for official API documentation
5. **Document findings** in `research.md` before proceeding

**Always delegate first**:
```
Use Task tool with subagent_type='nautilus-docs-specialist' to:
- Search Discord for recent bugs/workarounds on the topic
- Check Context7 for API changes in nightly vs stable
- Verify schema/format changes in latest versions
```

```bash
# Manual search fallback
grep -r "wrangler\|ParquetDataCatalog" docs/discord/ --include="*.md"
grep -r "breaking\|deprecated" docs/nautilus/ --include="*.md"
```

**Why**: Discord contains real-world bugs, workarounds, and API changes not yet in official docs.

### Documentation & Code Analysis Workflow

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **Discord** (`docs/discord/`) | Community solutions | **FIRST** - Recent bugs, workarounds |
| **Context7 MCP** | NautilusTrader API docs | Official API reference |
| **backtest-analyzer** | Analyze backtest logs | Strategy review, performance analysis |
| **alpha-debug** | Hunt bugs in code | Edge cases, logic errors |
| **Serena MCP** | Search codebase | Find patterns, locate implementations |

**Analysis Workflow**:
1. **Discord first** (`docs/discord/`) - Check for recent issues/solutions
2. Use Context7 for official documentation
3. Use `backtest-analyzer` agent for log analysis (chunked processing)
4. Use `alpha-debug` agent for code bug hunting

## Architecture Principles

**Modular Black Box Design** (Eskil Steenberg principles):
- **Black Box Interfaces** - Strategy modules with clean APIs, hidden implementation
- **Everything Replaceable** - If you don't understand a module, rewrite it easily
- **Constant Velocity** - Write 5 complete lines today > edit 1 line tomorrow
- **Single Responsibility** - One strategy = one clear trading logic
- **Reusable Components** - Extract common patterns into utilities

## Development Principles

### KISS & YAGNI

- **Use native Rust indicators**: Never reimplement EMA, RSI, etc.
- **NO df.iterrows()** - Use vectorized operations or Rust wranglers
- **NO custom indicators** - Use `nautilus_trader.indicators`
- **Functions <= 50 lines** - Extract helpers if larger
- **Write Complete Code Once** - 5 clear lines today > 1 line + future edits

### Important Reminders

#### NEVER
- Use `--no-verify` to bypass commit hooks
- Use `df.iterrows()` (use vectorized operations)
- Reimplement native Rust indicators
- Create report/summary files unless requested
- Execute tests directly (use test-runner agent)

#### ALWAYS
- Search docs first (Context7, Discord)
- Use native Rust indicators
- Run tests via test-runner agent
- Use `uv` for dependencies (not `pip`)
- Format code (`ruff check . && ruff format .`)

## Code Style

- **Python**: PEP 8, type hints, docstrings for public APIs
- **Strategy naming**: `{Exchange}{Asset}{Strategy}Strategy` (e.g., `BinanceBTCMomentumStrategy`)
- **Descriptive names**: `calculate_position_size()` not `calc_pos()`

## NautilusTrader Patterns

**Data Management**:
```python
# YES: Streaming Parquet catalog
catalog = ParquetDataCatalog("./data/catalog")
bars = catalog.bars()  # Lazy loaded

# NO: Loading entire datasets into memory
df = pd.read_csv("huge_file.csv")  # Will crash on large files
```

**Strategy Template** (Black Box Design):
```python
from nautilus_trader.trading.strategy import Strategy

class MyStrategy(Strategy):
    """Black box strategy: Clear interface, hidden implementation"""

    def on_start(self):
        """Init: Subscribe to data, register indicators"""
        self.ema = ExponentialMovingAverage(period=20)  # Native Rust

    def on_data(self, data):
        """Handle ticks/bars - update indicators, check signals"""
        self.ema.handle_bar(data)
        if self._should_enter_long(data):
            self._enter_long_position(data)

    def _should_enter_long(self, data) -> bool:
        """Replaceable signal logic"""
        return self.ema.value > data.close

    def _enter_long_position(self, data):
        """Replaceable order execution logic"""
        self.submit_order(...)
```

## Development Workflow

**Quick Reference**:
```bash
# Activate nightly environment
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate

# TDD cycle
uv run pytest tests/test_module.py::test_new -v  # RED
# implement minimal code
uv run pytest tests/test_module.py::test_new -v  # GREEN
# refactor if needed
```

**Example Workflow**:
```
Task: Implement momentum strategy with risk management

1. Context7: "Show BacktestNode configuration parameters"
2. Discord: Grep "risk management" in docs/discord/
3. Serena: Search codebase for existing risk management utils
4. Implement strategy using black box design
5. alpha-debug: Analyze strategy.py for edge cases
6. TDD: test-runner agent for tests
```

**When Stuck**: Maximum 3 attempts per issue, then document and ask for help.

## Error Handling

**Trading Code Rules**:
- **Fail fast** on invalid config (bad symbols, negative sizes, missing API keys)
- **Log and retry** for transient errors (network, rate limits) - max 3 retries
- **Graceful degradation** for optional features (indicators missing -> use fallback)
- **NO silent failures** - Always surface errors via logging or exceptions

## Edge Cases

Always consider and handle:
- **Empty/null inputs** - Empty bars list, missing price fields, None values
- **Extreme values** - Huge position sizes, negative prices, zero volumes
- **Invalid states** - Start date > end date, sell before buy, duplicate orders
- **Concurrency** - Multiple strategies, simultaneous order fills

## Documentation Update Rules

**When implementing new features**:
1. **Update relevant docs** in `docs/` folder
2. **Keep CLAUDE.md small** (~300 lines max)
3. **Discord knowledge** goes to `docs/discord/`

## Changelog & Version Tracking

**Auto-updated files** (`docs/nautilus/`):
- `nautilus-trader-changelog.md` - Human-readable feed
- `nautilus-trader-changelog.json` - Machine-readable signal

**Check before NautilusTrader operations**:
- Current stable version
- Breaking changes (last 7 days)
- Nightly commits count

## Tone

- **Concise** - Short responses unless debugging complex strategies
- **Skeptical** - Question assumptions about market behavior
- **Direct** - No flattery, tell me when I'm wrong
- **Ask questions** - If strategy intent is unclear, ask before implementing

---

**Remember**: Search docs first. Use native Rust. No df.iterrows(). No report files. Test via agent.
