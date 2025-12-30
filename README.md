# NautilusTrader Development Environment

Professional development environment for algorithmic trading with NautilusTrader.

## Quick Start

```bash
cd /media/sam/1TB/nautilus_dev

# Verify setup
python -c "import nautilus_trader; print(nautilus_trader.__version__)"
specify check
claude-self-reflect status

# Start developing
/speckit.constitution    # Define trading principles
/speckit.specify         # Specify strategy
/tdd:cycle-safe          # Implement with TDD
```

## Project Structure

```
nautilus_dev/
├── strategies/          # Trading strategies
├── backtests/          # Backtest configurations
├── data/               # Historical and live data
├── tests/              # Strategy tests
├── notebooks/          # Analysis notebooks
└── .claude/            # Development tools
    ├── agents/         # Specialized AI agents
    ├── commands/       # Slash commands
    │   ├── tdd/       # TDD workflow
    │   ├── undo/      # Rollback system
    │   └── speckit/   # Spec-driven development
    └── context/        # Project context
```

## Available Tools

### Spec-Kit (8 commands)
Specification-driven development workflow:
- `/speckit.constitution` - Trading principles
- `/speckit.specify` - Strategy specification
- `/speckit.plan` - Implementation plan
- `/speckit.tasks` - Task breakdown
- `/speckit.implement` - Execute tasks
- `/speckit.clarify`, `/speckit.analyze`, `/speckit.checklist`

### TDD-Guard (7 commands)
Test-driven development for strategies:
- `/tdd:cycle` - Complete Red-Green-Refactor
- `/tdd:cycle-safe` - Safe TDD with rollback
- `/tdd:red`, `/tdd:green`, `/tdd:refactor`
- `/tdd:spec-to-test` - Generate tests from specs

### CCUndo (5 commands)
Safe experimentation with rollback:
- `/undo:checkpoint "name"` - Create checkpoint
- `/undo:list` - List checkpoints
- `/undo:preview` - Preview changes
- `/undo:rollback` - Rollback to checkpoint
- `/undo:redo` - Redo last rollback

### MCP Servers (6 configured)

**Claude Reflect** - Perfect memory:
- Search past strategy discussions
- Find similar trading patterns
- 🔒 100% local, no external APIs

**Taskmaster** - Task management:
- Strategy development lifecycle
- Dependency tracking
- Progress dashboards

**Serena** - Code navigation:
- Semantic search in strategies
- Symbol navigation
- Find implementations

**Context7** - NautilusTrader API docs:
- Quick lookups (order types, config params)
- API reference, single topic queries
- Cannot chain with other MCP tools

**Gemini** - Analyze YOUR code:
- Strategy code review (2M context)
- Backtest log analysis
- Complex logic edge cases
- Pass files with @ syntax
- Cannot chain with other MCP tools

**Scraping Tools** - Web extraction:
- Firecrawl - When Context7 lacks pages
- Playwright - Interactive examples
- YouTube - Video tutorials

**Database** - Data analysis:
- DuckDB queries
- Parquet catalog access
- Performance metrics

## Specialized Agents

- **nautilus-trader-expert**: NautilusTrader best practices
- **nautilus-docs-specialist**: Documentation search
- **test-runner**: Execute tests and backtests
- **test-generator**: Generate test cases
- **code-analyzer**: Strategy logic analysis
- **file-analyzer**: Summarize backtest results

## Development Workflow

1. **Define Strategy**:
   ```bash
   /speckit.constitution  # Trading rules
   /speckit.specify       # Strategy details
   /speckit.plan          # Technical approach
   /speckit.tasks         # Break into tasks
   ```

2. **Implement with TDD**:
   ```bash
   task-master parse-prd
   task-master next
   /undo:checkpoint "before-implementation"
   /tdd:cycle-safe
   ```

3. **Search Documentation**:
   - Context7: "Show me NautilusTrader order types"
   - Gemini: "Analyze this backtest log"
   - Claude Reflect: "Find slippage modeling discussions"

4. **Complete and Test**:
   ```bash
   task-master complete
   /tdd:cycle-safe
   ```

## Key Principles

### NautilusTrader Best Practices

- ✅ **ALWAYS search Context7/Gemini before implementing**
- ✅ **Use native Rust implementations** (100x faster)
- ❌ **NEVER use df.iterrows()** for data wrangling
- ✅ **Use ParquetDataCatalog** over CSV
- ✅ **Test everything** - Unit tests + backtests
- ❌ **No lookahead bias** - Never use future data

### Code Quality

- Complete implementations only
- No code duplication
- Test for every strategy
- 80% minimum coverage
- No resource leaks
- Fail fast on invalid configs

## Resources

**Official Documentation**:
- [NautilusTrader Docs](https://nautilustrader.io)
- [Strategy Examples](https://docs.nautilustrader.io/latest/examples/strategies/)
- [NautilusTrader GitHub](https://github.com/nautechsystems/nautilus_trader)

**Community Knowledge** (`docs/discord/`):
- Real-world solutions from experienced traders
- Common issues and workarounds
- Strategy implementation discussions
- Performance optimization tips

---

**Ready to trade? Start with `/speckit.constitution` to define your trading principles.**
