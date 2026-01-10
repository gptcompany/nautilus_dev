# /optimize - Prompt Refinement for NautilusTrader Development

Transform vague or incomplete prompts into precise, actionable specifications optimized for algorithmic trading development.

## Usage

```
/optimize <your prompt>
/optimize fix the strategy
/optimize add risk management
/optimize implement momentum indicator
```

## When to Use

- Prompt feels vague or underspecified
- Multiple interpretations possible
- Complex feature requiring clarification
- Before starting significant implementation work

## Refinement Process

Analyze the user's prompt through these lenses:

### 1. Domain Disambiguation

Identify which domain(s) the request touches:

| Domain | Indicators | Clarification Needed |
|--------|------------|---------------------|
| **Strategy Logic** | entry, exit, signal, position | Which instrument? Timeframe? |
| **Risk Management** | stop-loss, position size, drawdown | Fixed or adaptive limits? |
| **Data Pipeline** | bars, ticks, catalog, streaming | Data source? Format? |
| **Indicators** | EMA, RSI, custom calculation | Native Rust or Python? Parameters? |
| **Backtesting** | backtest, performance, metrics | Date range? Slippage model? |
| **Live Trading** | live, execution, reconciliation | Exchange? Paper or real? |

### 2. Specificity Analysis

For the prompt "$ARGUMENTS", identify:

**Missing Elements:**
- [ ] Target file(s) or module(s)
- [ ] Specific function/class names
- [ ] Input/output specifications
- [ ] Success criteria
- [ ] Edge cases to handle
- [ ] Integration points

**Ambiguous Terms:**
- "fix" → What's broken? Error message? Expected vs actual behavior?
- "improve" → Performance? Readability? Accuracy? By what metric?
- "add" → Where exactly? How should it integrate?
- "update" → What specifically changes? Backwards compatibility?

### 3. NautilusTrader Context

Apply project-specific knowledge:

```python
# Common clarifications needed:
- Indicator: Native Rust (nautilus_indicators) or Python wrapper?
- Data: V1 Wranglers only (V2 incompatible with nightly)
- Strategy: Inherits from Strategy base class?
- Testing: Unit tests + backtest with real market data?
- Precision: Using 128-bit Decimal (nightly) or 64-bit?
```

### 4. Mathematical Precision

For quantitative requests:

- Specify formulas explicitly (LaTeX or code)
- Define variable names and units
- State assumptions (e.g., returns distribution)
- Clarify discrete vs continuous calculations
- Identify numerical stability concerns

## Output Format

Generate a refined prompt with this structure:

```markdown
## Refined Request

### Objective
[One clear sentence describing the goal]

### Scope
- Target: [specific files/modules]
- Changes: [what will be modified]
- Constraints: [what must NOT change]

### Technical Specification
[Precise description with:
- Input/output types
- Algorithm or logic
- Error handling
- Edge cases]

### Success Criteria
1. [Measurable criterion 1]
2. [Measurable criterion 2]
3. [Test coverage requirement]

### Questions for User (if any)
- [Clarifying question 1]
- [Clarifying question 2]
```

## Examples

### Example 1: Vague Strategy Request

**Original:** "fix the momentum strategy"

**Refined:**
```markdown
## Refined Request

### Objective
Debug and fix the failing momentum strategy in `strategies/development/`.

### Scope
- Target: `strategies/development/momentum_*.py`
- Changes: Fix identified bugs while maintaining existing interface
- Constraints: No changes to position sizing or risk parameters

### Technical Specification
To diagnose, need to identify:
1. Error type: Runtime exception? Wrong signals? Performance issue?
2. Symptom: When does it fail? Specific market conditions?
3. Expected behavior: What should the strategy do?

### Success Criteria
1. All existing tests pass
2. Backtest completes without errors
3. Signal generation matches specification

### Questions for User
- What error message or unexpected behavior are you seeing?
- Which specific momentum strategy file?
- Do you have a failing test case?
```

### Example 2: Vague Indicator Request

**Original:** "add RSI indicator"

**Refined:**
```markdown
## Refined Request

### Objective
Integrate RSI (Relative Strength Index) indicator into [strategy name].

### Scope
- Target: [specific strategy file]
- Changes: Add RSI calculation and signal integration
- Constraints: Use native Rust indicator from nautilus_indicators

### Technical Specification
```python
from nautilus_trader.indicators.rsi import RelativeStrengthIndex

# Parameters needed:
period: int = 14  # Standard RSI period
overbought: float = 70.0  # Upper threshold
oversold: float = 30.0  # Lower threshold

# Integration point:
def on_bar(self, bar: Bar) -> None:
    self.rsi.handle_bar(bar)
    if self.rsi.value > overbought:
        # Signal logic here
```

### Success Criteria
1. RSI calculates correctly (verified against reference)
2. Signals generated at threshold crossings
3. Unit tests cover edge cases (insufficient data, extreme values)

### Questions for User
- Which strategy should use this RSI?
- What RSI period (default 14)?
- How should RSI signals integrate with existing logic?
```

### Example 3: Vague Risk Request

**Original:** "improve risk management"

**Refined:**
```markdown
## Refined Request

### Objective
Enhance risk management in [strategy/module] with specific improvements.

### Scope
- Target: `strategies/common/risk/` or specific strategy
- Changes: [depends on clarification]
- Constraints: Safety limits remain FIXED (not adaptive)

### Technical Specification
Risk management improvements could include:

| Aspect | Current | Proposed |
|--------|---------|----------|
| Position sizing | Fixed | Kelly criterion / volatility-scaled |
| Stop-loss | None/Fixed | ATR-based trailing |
| Exposure limits | None | Per-instrument + portfolio |
| Drawdown control | None | Daily loss limit + kill switch |

### Success Criteria
1. Backtest shows improved risk-adjusted returns
2. Maximum drawdown reduced by X%
3. No increase in catastrophic loss scenarios

### Questions for User
- Which specific aspect of risk management?
- Current pain point (large drawdowns? position sizing?)
- Target metrics (Sharpe, max drawdown, etc.)?
```

## Integration

After refinement:
1. User reviews and approves refined prompt
2. Use refined prompt for implementation
3. Refined prompt serves as mini-specification

## Notes

- This command does NOT execute the task, only refines the prompt
- User must explicitly proceed with the refined version
- For complex features, consider `/speckit:specify` instead
