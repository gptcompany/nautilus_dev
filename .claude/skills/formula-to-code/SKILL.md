# Formula to Code Skill

## Metadata

- **Name**: formula-to-code
- **Description**: Convert mathematical formulas (LaTeX, text, or extracted from PDFs) to validated, production-ready Python code
- **Token Savings**: 70% (2000 → 600 tokens)
- **Triggers**: "convert formula", "formula to python", "implement equation", "codify formula"

## Workflow

### Step 1: Parse Formula Input

Accept formula in multiple formats:
- LaTeX: `$f = \frac{bp - q}{b}$`
- Text: `f = (b*p - q) / b`
- Natural language: "Kelly criterion for optimal bet sizing"

### Step 2: Validate with WolframAlpha

```
Use mcp__wolframalpha__ask_llm to:
1. Verify mathematical validity
2. Get simplified form
3. Identify edge cases (division by zero, etc.)
4. Check for convergence properties if iterative
```

### Step 3: Generate Python Code

Output structure:
```python
from typing import Union
import numpy as np

def {function_name}(
    {params_with_types}
) -> {return_type}:
    """
    {formula_description}

    Formula: {latex_formula}

    Args:
        {param_docs}

    Returns:
        {return_doc}

    Raises:
        ValueError: {edge_cases}

    Example:
        >>> {example_usage}
        {example_output}
    """
    # Edge case handling
    {edge_case_checks}

    # Implementation
    {implementation}

    return result
```

### Step 4: Generate Tests

```python
import pytest

def test_{function_name}_basic():
    """Test with known values from WolframAlpha."""
    assert abs({function_name}({test_input}) - {expected_output}) < 1e-9

def test_{function_name}_edge_cases():
    """Test edge cases."""
    with pytest.raises(ValueError):
        {function_name}({invalid_input})
```

## Example Invocation

**Input**: "Convert Kelly Criterion formula to Python"

**Output**:
```python
def kelly_criterion(
    win_probability: float,
    win_loss_ratio: float,
) -> float:
    """
    Calculate optimal bet fraction using Kelly Criterion.

    Formula: f* = (bp - q) / b
    where:
        f* = fraction of bankroll to bet
        b = win/loss ratio (payout odds)
        p = probability of winning
        q = probability of losing (1-p)

    Args:
        win_probability: Probability of winning (0 < p < 1)
        win_loss_ratio: Ratio of win amount to loss amount (b > 0)

    Returns:
        Optimal fraction of bankroll to bet (can be negative = don't bet)

    Raises:
        ValueError: If probability not in (0,1) or ratio <= 0

    Example:
        >>> kelly_criterion(0.6, 1.0)  # 60% win rate, 1:1 odds
        0.2
    """
    if not 0 < win_probability < 1:
        raise ValueError(f"win_probability must be in (0,1), got {win_probability}")
    if win_loss_ratio <= 0:
        raise ValueError(f"win_loss_ratio must be > 0, got {win_loss_ratio}")

    p = win_probability
    q = 1 - p
    b = win_loss_ratio

    return (b * p - q) / b


# Verification (WolframAlpha validated)
if __name__ == "__main__":
    # Test: 60% win rate, 1:1 odds -> f* = (1*0.6 - 0.4)/1 = 0.2
    assert abs(kelly_criterion(0.6, 1.0) - 0.2) < 1e-9
    print("Kelly criterion implementation verified!")
```

## Integration with mathematician agent

This skill can delegate to the `mathematician` agent for complex formulas requiring:
- Symbolic differentiation/integration
- Series expansion
- Numerical method selection (Newton-Raphson, etc.)

## Notes

- Always validate edge cases before implementation
- Use NumPy for vectorized operations when applicable
- Add `@numba.jit` decorator hint for performance-critical formulas
- Reference source paper/book in docstring when available
