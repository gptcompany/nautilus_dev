# CLAUDE.md - Internal Agent Instructions

> Think carefully and implement the most concise solution that changes as little code as possible.

## USE SUB-AGENTS FOR CONTEXT OPTIMIZATION

### 1. Always use the backtest-analyzer sub-agent for log analysis.
The backtest-analyzer agent uses chunked processing to analyze large log files, identify errors, performance issues, and generate actionable insights.

### 2. Always use the alpha-debug sub-agent for bug hunting and code analysis.
The alpha-debug agent performs iterative rounds of analysis to find bugs, edge cases, and logic errors that tests might miss.

### 3. Always use the test-runner sub-agent to run tests and analyze the test results.
Using the test-runner agent ensures full test output is captured, main conversation stays clean, and context usage is optimized.

### 4. Always use the nautilus-coder for NautilusTrader-specific implementations.
The nautilus-coder knows best practices, native Rust implementations, and common pitfalls.

### 5. Always use the nautilus-visualization-renderer for trading charts and dashboards.
The visualization-renderer implements Canvas 2D/WebGL charts for equity curves, orderbook heatmaps, and real-time PnL dashboards.

## Philosophy

### Error Handling for Trading Systems

- **Fail fast** for invalid trading configurations (bad order sizes, invalid symbols)
- **Log and continue** for transient errors (network issues, rate limits)
- **Graceful degradation** when non-critical data feeds unavailable
- **User-friendly messages** with actionable guidance for traders

### Testing Trading Strategies

- Always use the test-runner agent to execute tests
- **Real market data** for backtests (never mock price data)
- Do not move on until current test passes
- Tests must be verbose for debugging strategy behavior
- **Minimum 80% coverage** for strategy code

## Tone and Behavior for Trading Development

- **Criticism welcome** - Tell me when trading logic is flawed
- **Be skeptical** - Question assumptions about market behavior
- **Be concise** - Short summaries unless debugging complex strategies
- **No flattery** - Direct technical feedback only
- **Ask questions** - If strategy intent is unclear, ask before implementing

## ABSOLUTE RULES FOR TRADING CODE:

- **NO PARTIAL IMPLEMENTATION** - Complete strategies only, no half-finished trading logic
- **NO SIMPLIFICATION** - No "simplified for now" in production trading code
- **NO CODE DUPLICATION** - Check existing strategies before writing new ones
- **NO DEAD CODE** - Remove unused strategies and indicators
- **IMPLEMENT TEST FOR EVERY STRATEGY** - Unit tests + backtest tests required
- **NO CHEATER TESTS** - Tests must use real market scenarios
- **NO INCONSISTENT NAMING** - Follow NautilusTrader conventions
- **NO OVER-ENGINEERING** - Simple readable strategies over complex abstractions
- **NO MIXED CONCERNS** - Separate strategy logic from data management
- **NO RESOURCE LEAKS** - Clean up connections, timers, event handlers
- **NO LOOKAHEAD BIAS** - Never use future data in backtests
- **FAIL FAST** - Validate all trading parameters early

## NautilusTrader-Specific Rules

### Data Wrangling
- **NEVER use df.iterrows()** - Use vectorized operations or Rust wranglers (100x faster)
- Use `ParquetDataCatalog` over CSV for performance
- Stream large datasets, never load entirely into memory

### Native Rust Usage
- **ALWAYS search Context7 and Discord BEFORE implementing**
- Use native Rust indicators (ExponentialMovingAverage, etc.)
- Prefer Rust implementations over Python equivalents
- Check docs for available native implementations

### Strategy Patterns
```python
# Good: Native Rust indicator
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
self.ema = ExponentialMovingAverage(period=20)

# Bad: Custom Python indicator
def calculate_ema(prices):
    # Custom implementation (100x slower)
    pass
```

## TDD Development Commands

### Core TDD Workflow
- `/tdd:cycle` - Complete TDD cycle (Red-Green-Refactor)
- `/tdd:cycle-safe` - Safe TDD with automatic rollback
- `/tdd:red` - Write failing tests (Red phase)
- `/tdd:green` - Implement solution (Green phase)
- `/tdd:refactor` - Improve code quality (Refactor phase)
- `/tdd:spec-to-test` - Convert strategy specs to tests

### TDD Integration with Spec-Kit
1. Use `/speckit.specify` to define strategy requirements
2. Use `/tdd:spec-to-test` to generate test cases
3. Follow `/tdd:cycle-safe` for safe implementation
4. Use `task-master complete` when done

### TDD Principles for Trading
- **Red**: Write failing tests for strategy behavior first
- **Green**: Write minimal code to pass tests
- **Refactor**: Improve code quality while maintaining tests
- **Coverage**: Maintain 80% minimum coverage
- **Traceability**: Link tests to strategy specifications

## Strategy Development Workflow

1. **Specification** (Spec-Kit):
   ```bash
   /speckit.constitution  # Trading rules and risk limits
   /speckit.specify       # Strategy specification
   /speckit.plan          # Implementation approach
   /speckit.tasks         # Task breakdown
   ```

2. **Task Management** (Taskmaster):
   ```bash
   task-master parse-prd  # Generate task structure
   task-master next       # Get next task
   ```

3. **Implementation** (TDD + CCUndo):
   ```bash
   /undo:checkpoint "before-feature"
   /tdd:cycle-safe        # Implement with safety
   task-master complete   # Mark done
   ```

4. **Documentation Search** (Context7/Discord):
   - "Show me NautilusTrader order types" → Context7
   - "How to implement stop loss in NautilusTrader" → Context7
   - "Analyze this backtest performance log" → backtest-analyzer agent

## NautilusTrader Data Structure

### NautilusTrader Changelog Files

**Signal File** (JSON - Machine-readable):
- Path: `docs/nautilus/nautilus-trader-changelog.json`
- Purpose: Structured data for automation/scripts
- Format: JSON with timestamps, versions, breaking_changes, open_issues
- Storage: Single file, always overwritten with latest data

**Feed File** (Markdown - Human-readable):
- Path: `docs/nautilus/nautilus-trader-changelog.md`
- Purpose: Formatted documentation for humans and agents
- Format: Markdown with sections, links, summaries
- Storage: Single file, always overwritten with latest data

**Generated by**: N8N workflow in `/media/sam/1TB/devteam1` (runs automatically)

## Important Instructions

- **NEVER create files** unless absolutely necessary
- **ALWAYS prefer editing** existing files to creating new ones
- **NEVER proactively create documentation** unless explicitly requested
- Do what has been asked; nothing more, nothing less
- Always search Context7 and Discord before implementing NautilusTrader features
