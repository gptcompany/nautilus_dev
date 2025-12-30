---
name: pytest-test-generator
description: Generate pytest test templates for NautilusTrader strategies and modules following TDD patterns. Automatically creates RED phase tests with async fixtures, coverage markers, and integration test stubs.
---

# Pytest Test Generator

Generate standardized pytest tests for NautilusTrader strategies and modules following strict TDD discipline.

## Quick Start

**User says**: "Generate tests for MomentumStrategy"

**Skill generates**:
```python
# tests/test_momentum_strategy.py
import pytest
from nautilus_trader.test_kit.stubs.data import TestDataStubs
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from strategies.momentum_strategy import MomentumStrategy, MomentumConfig

@pytest.fixture
def strategy():
    """Fixture for MomentumStrategy"""
    config = MomentumConfig(
        instrument_id="BTCUSDT.BINANCE",
        ema_period=20,
    )
    strategy = MomentumStrategy(config=config)
    yield strategy

def test_on_start_initializes_indicators(strategy):
    """Test strategy initialization"""
    strategy.on_start()
    assert strategy.ema is not None
    assert strategy.ema.period == 20

def test_on_bar_updates_indicator(strategy):
    """Test bar processing"""
    strategy.on_start()
    bar = TestDataStubs.bar_5decimal()
    strategy.on_bar(bar)
    assert strategy.ema.count == 1
```

## Templates

### 1. Strategy Test Template
```python
import pytest
from nautilus_trader.test_kit.stubs.data import TestDataStubs
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from strategies.{module} import {StrategyClass}, {ConfigClass}

@pytest.fixture
def strategy():
    """Fixture for {StrategyClass}"""
    config = {ConfigClass}(
        instrument_id="{instrument_id}",
        # Add config parameters
    )
    strategy = {StrategyClass}(config=config)
    yield strategy

def test_on_start_initializes_indicators(strategy):
    """Test that on_start properly initializes all indicators"""
    strategy.on_start()
    # Assert indicators are initialized
    assert strategy.{indicator} is not None

def test_on_bar_updates_indicators(strategy):
    """Test that on_bar updates indicators correctly"""
    strategy.on_start()
    bar = TestDataStubs.bar_5decimal()
    strategy.on_bar(bar)
    assert strategy.{indicator}.count == 1

def test_signal_generation(strategy):
    """Test signal generation logic"""
    strategy.on_start()
    # Setup state for signal
    signal = strategy._calculate_signal()
    assert signal is not None
```

### 2. Indicator Test Template
```python
import pytest
from nautilus_trader.test_kit.stubs.data import TestDataStubs
from indicators.{module} import {IndicatorClass}

@pytest.fixture
def indicator():
    """Fixture for {IndicatorClass}"""
    return {IndicatorClass}(period={period})

def test_indicator_initialization(indicator):
    """Test indicator initializes correctly"""
    assert indicator.period == {period}
    assert not indicator.initialized

def test_indicator_handle_bar(indicator):
    """Test indicator processes bars"""
    bar = TestDataStubs.bar_5decimal()
    indicator.handle_bar(bar)
    assert indicator.count == 1

def test_indicator_value_after_warmup(indicator):
    """Test indicator value after warmup period"""
    for _ in range({period}):
        bar = TestDataStubs.bar_5decimal()
        indicator.handle_bar(bar)
    assert indicator.initialized
    assert indicator.value is not None
```

### 3. Integration Test Template
```python
import pytest
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.config import BacktestRunConfig
from strategies.{strategy_module} import {StrategyClass}

@pytest.fixture
def backtest_config():
    """Backtest configuration for integration tests"""
    return BacktestRunConfig(
        engine=BacktestEngineConfig(
            strategies=[{StrategyClass}Config(...)],
        ),
    )

@pytest.mark.integration
@pytest.mark.slow
async def test_strategy_full_backtest(backtest_config):
    """Test complete strategy lifecycle with BacktestNode"""
    node = BacktestNode(configs=[backtest_config])
    results = node.run()

    assert results is not None
    # Verify results metrics
```

### 4. Data Pipeline Test Template
```python
import pytest
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from data.{module} import {DataClass}

@pytest.fixture
def catalog(tmp_path):
    """Fixture for test catalog"""
    return ParquetDataCatalog(path=str(tmp_path / "catalog"))

def test_data_loading(catalog):
    """Test data loads correctly from catalog"""
    bars = catalog.bars()
    assert len(bars) > 0

def test_data_transformation():
    """Test data transformation logic"""
    raw_data = {...}
    transformed = {DataClass}.transform(raw_data)
    assert transformed is not None
```

## Usage Patterns

### Pattern 1: New Strategy
```
User: "Create tests for strategies/mean_reversion.py"

Skill:
1. Detect strategy class and config
2. Generate fixture with config
3. Create 3-5 core tests (RED phase)
4. Add integration test stub
5. Write to tests/test_mean_reversion.py
```

### Pattern 2: Add Test to Existing File
```
User: "Add test for _calculate_position_size method"

Skill:
1. Read existing tests/test_strategy.py
2. Generate new test function
3. Append to file
```

### Pattern 3: Integration Test
```
User: "Create integration test for full backtest"

Skill:
1. Generate integration test in tests/integration/
2. Include BacktestNode setup
3. Create end-to-end flow test
```

## Test Naming Conventions

| Pattern | Example | Use Case |
|---------|---------|----------|
| `test_{strategy}_*` | `test_momentum_on_start` | Strategy test |
| `test_{action}_*` | `test_calculate_signal` | Action-based test |
| `test_{module1}_to_{module2}` | `test_data_to_strategy` | Integration |
| `test_{edge_case}` | `test_empty_bars` | Edge case |

## Fixtures Library

### NautilusTrader Test Kit Fixtures
```python
from nautilus_trader.test_kit.stubs.data import TestDataStubs
from nautilus_trader.test_kit.stubs.identifiers import TestIdStubs
from nautilus_trader.test_kit.stubs.component import TestComponentStubs

@pytest.fixture
def instrument_id():
    """Standard instrument ID for testing"""
    return TestIdStubs.audusd_id()

@pytest.fixture
def bar():
    """Sample bar for testing"""
    return TestDataStubs.bar_5decimal()

@pytest.fixture
def quote_tick():
    """Sample quote tick for testing"""
    return TestDataStubs.quote_tick()
```

### Async Fixtures
```python
@pytest.fixture
async def live_strategy():
    """Strategy with live connection (for integration tests)"""
    strategy = MomentumStrategy(config)
    await strategy.start()
    yield strategy
    await strategy.stop()
```

## Coverage Configuration

Auto-generate `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    asyncio: async test
    integration: integration test
    slow: slow test (deselect with -m 'not slow')
addopts =
    --cov=strategies
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
```

## Output Format

**Generated test file**:
```python
"""
Tests for {module_name}
Coverage target: >80%
"""
import pytest
from nautilus_trader.test_kit.stubs.data import TestDataStubs
from strategies.{module} import {ClassName}

# Fixtures
@pytest.fixture
def {fixture_name}():
    """..."""
    pass

# Unit Tests (RED phase - should fail initially)
def test_{feature_1}():
    """Test {description}"""
    assert False  # RED: Not implemented yet

def test_{feature_2}():
    """Test {description}"""
    assert False  # RED: Not implemented yet

# Integration Tests
@pytest.mark.integration
async def test_integration():
    """Test module integration"""
    pass
```

## Automatic Invocation

**Triggers**:
- "generate tests for [strategy/module]"
- "create test file for [file]"
- "add test for [function]"
- "write integration test for [strategy]"

**Does NOT trigger**:
- Complex test logic design (use subagent)
- Full TDD enforcement (use tdd-guard subagent)
- Test debugging (use general debugging)

## Token Savings

| Task | Without Skill | With Skill | Savings |
|------|--------------|------------|---------|
| Strategy tests (5 tests) | ~1,200 tokens | ~200 tokens | 83% |
| Integration test | ~800 tokens | ~150 tokens | 81% |
| Fixture generation | ~400 tokens | ~100 tokens | 75% |

**Average Savings**: 83% (1,200 -> 200 tokens)
