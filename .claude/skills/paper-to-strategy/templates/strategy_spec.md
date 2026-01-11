# Strategy: {strategy_name}

## Source

- **Paper**: {paper_title}
- **Authors**: {authors}
- **ArXiv/DOI**: {paper_id}
- **Year**: {year}
- **Source Entity**: `{source_entity_id}`

## Problem Statement

{paper_abstract_summary}

## Trading Methodology

### Strategy Type

`{methodology_type}` (momentum|mean_reversion|market_making|arbitrage|trend_following|statistical_arbitrage)

### Entry Conditions

{entry_conditions}

### Exit Conditions

{exit_conditions}

### Position Sizing

{position_sizing_method}

### Risk Management

{risk_management_rules}

## Technical Implementation

### Indicators (Native NautilusTrader Rust)

```python
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.indicators.momentum.rsi import RelativeStrengthIndex
# Add other indicators as needed

class {StrategyClass}(Strategy):
    def __init__(self, config: {StrategyClass}Config):
        super().__init__(config)
        # Indicators from paper
{indicator_initialization}
```

### Strategy Skeleton

```python
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import Bar


class {StrategyClass}(Strategy):
    """
    {strategy_name} - Based on {paper_title}

    Methodology: {methodology_type}
    """

    def on_start(self) -> None:
        """Initialize indicators and subscribe to data."""
        self.subscribe_bars(self.bar_type)

    def on_bar(self, bar: Bar) -> None:
        """Process incoming bar data."""
        # Update indicators
{indicator_update_code}

        # Check entry conditions
        if self._should_enter():
            self._enter_position(bar)

        # Check exit conditions
        elif self._should_exit():
            self._exit_position()

    def _should_enter(self) -> bool:
        """Entry logic from paper."""
{entry_logic_code}

    def _should_exit(self) -> bool:
        """Exit logic from paper."""
{exit_logic_code}

    def _enter_position(self, bar: Bar) -> None:
        """Submit entry order with risk management."""
        # Position sizing
{position_sizing_code}

        # Submit order
        order = self.order_factory.market(
            instrument_id=self.instrument.id,
            order_side=OrderSide.BUY,
            quantity=position_size,
        )
        self.submit_order(order)

        # Stop loss
{stop_loss_code}

    def _exit_position(self) -> None:
        """Close position."""
        self.close_all_positions(self.instrument.id)
```

### Configuration

```python
from decimal import Decimal
from nautilus_trader.config import StrategyConfig


class {StrategyClass}Config(StrategyConfig):
    """Configuration for {StrategyClass}."""

    # Indicator parameters
{config_indicator_params}

    # Risk parameters
    stop_loss_pct: Decimal = Decimal("{stop_loss_default}")
    take_profit_pct: Decimal = Decimal("{take_profit_default}")
    max_position_pct: Decimal = Decimal("{max_position_default}")

    # Timeframe
    bar_type: str = "{default_bar_type}"
```

## Backtest Parameters (from Paper)

| Metric | Paper Value |
|--------|-------------|
| Period | {backtest_start} to {backtest_end} |
| Assets | {asset_list} |
| Sharpe Ratio | {sharpe_ratio} |
| Max Drawdown | {max_drawdown} |
| Annual Return | {annual_return} |
| Win Rate | {win_rate} |
| Profit Factor | {profit_factor} |

## NautilusTrader Mapping

### Indicators

| Paper Term | NautilusTrader Class | Parameters |
|------------|---------------------|------------|
{indicator_mapping_table}

### Order Types

| Paper Term | NautilusTrader | Notes |
|------------|----------------|-------|
{order_type_mapping_table}

### Events

| Paper Concept | NautilusTrader Event |
|---------------|---------------------|
{event_mapping_table}

## Custom Indicators Needed

{custom_indicators_section}

## Dependencies

- Spec 011 (Stop-Loss & Position Limits) - Risk management
- {exchange_spec} - Exchange adapter
- NautilusTrader nightly >= 1.222.0

## Implementation Notes

{implementation_notes}

## User Stories

### US1: Basic Implementation
**As a** trader,
**I want** to implement {strategy_name},
**So that** I can test the paper's methodology in backtests.

**Acceptance Criteria**:
- [ ] Strategy loads and initializes without errors
- [ ] Indicators calculate correctly (compare with paper examples)
- [ ] Entry/exit signals match paper logic
- [ ] Backtest runs without crashes

### US2: Risk Management
**As a** trader,
**I want** proper risk controls,
**So that** the strategy doesn't blow up my account.

**Acceptance Criteria**:
- [ ] Stop loss triggers at configured percentage
- [ ] Position sizing respects max allocation
- [ ] Max drawdown circuit breaker works

### US3: Validation
**As a** researcher,
**I want** to compare my results with the paper,
**So that** I know the implementation is correct.

**Acceptance Criteria**:
- [ ] Sharpe ratio within ±20% of paper value
- [ ] Max drawdown within ±20% of paper value
- [ ] Trade count approximately matches paper

## Next Steps

1. Run `/speckit.plan` to create implementation plan
2. Use `alpha-evolve` for multi-implementation generation
3. Backtest with `test-runner` agent
4. Compare results with paper claims

---

**Generated by**: paper-to-strategy skill via /research command
**Source Paper**: {paper_id}
**Entity ID**: `strategy__{methodology_type}_{asset_short}_{year}`
