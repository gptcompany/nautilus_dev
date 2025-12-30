# Data Model: Walk-Forward Validation

## Entities

### WalkForwardConfig

Configuration for walk-forward validation runs.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| data_start | datetime | Yes | - | Start of data range |
| data_end | datetime | Yes | - | End of data range |
| train_months | int | No | 6 | Training window size in months |
| test_months | int | No | 3 | Test window size in months |
| step_months | int | No | 3 | Rolling step size in months |
| gap_days | int | No | 0 | Purge/embargo period between train/test |
| min_windows | int | No | 4 | Minimum number of windows required |
| min_profitable_windows_pct | float | No | 0.75 | Min % of windows that must be profitable |
| min_test_sharpe | float | No | 0.5 | Minimum Sharpe ratio in test windows |
| max_drawdown_threshold | float | No | 0.30 | Maximum allowed drawdown per window |
| min_robustness_score | float | No | 60.0 | Minimum robustness score to pass |
| seed | int | No | None | Random seed for reproducibility |

**Validation Rules**:
- `data_start < data_end`
- `train_months >= 1`
- `test_months >= 1`
- `step_months >= 1`
- `gap_days >= 0`
- `min_windows >= 2`
- `0 < min_profitable_windows_pct <= 1.0`
- `min_test_sharpe >= 0`
- `0 < max_drawdown_threshold <= 1.0`
- `0 <= min_robustness_score <= 100`

---

### Window

A single train/test window in the walk-forward sequence.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| window_id | int | Yes | Sequential window identifier |
| train_start | datetime | Yes | Training period start |
| train_end | datetime | Yes | Training period end |
| test_start | datetime | Yes | Test period start |
| test_end | datetime | Yes | Test period end |

**Constraints**:
- `train_start < train_end`
- `train_end <= test_start`
- `test_start < test_end`

---

### WindowMetrics

Performance metrics for a single window.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sharpe_ratio | float | Yes | Risk-adjusted return |
| calmar_ratio | float | Yes | Return / Max Drawdown |
| max_drawdown | float | Yes | Maximum peak-to-trough decline |
| total_return | float | Yes | Total percentage return |
| win_rate | float | Yes | Percentage of winning trades |
| trade_count | int | Yes | Number of trades |

---

### WindowResult

Combined result for a window including train and test metrics.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| window | Window | Yes | Window definition |
| train_metrics | WindowMetrics | Yes | Training period metrics |
| test_metrics | WindowMetrics | Yes | Test period metrics (out-of-sample) |
| degradation_ratio | float | Computed | test_sharpe / train_sharpe |

---

### WalkForwardResult

Complete result of walk-forward validation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| config | WalkForwardConfig | Yes | Configuration used |
| windows | list[WindowResult] | Yes | Results for each window |
| robustness_score | float | Computed | Overall robustness (0-100) |
| passed | bool | Computed | Whether validation passed |
| profitable_windows_pct | float | Computed | % of windows with positive return |
| avg_test_sharpe | float | Computed | Average Sharpe across test periods |
| avg_test_return | float | Computed | Average return across test periods |
| worst_drawdown | float | Computed | Worst drawdown across all windows |
| validation_time_seconds | float | Yes | Time taken to run validation |

---

## Relationships

```
WalkForwardConfig
      │
      ▼
WalkForwardValidator.validate()
      │
      ├── generates ──▶ Window (multiple)
      │
      ▼
WalkForwardResult
      │
      └── contains ──▶ WindowResult (multiple)
                            │
                            ├── Window
                            ├── WindowMetrics (train)
                            └── WindowMetrics (test)
```

## State Transitions

```
                          ┌─────────────────┐
                          │   Not Started   │
                          └────────┬────────┘
                                   │
                          validate() called
                                   │
                                   ▼
                          ┌─────────────────┐
                          │   Generating    │
                          │    Windows      │
                          └────────┬────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │    Evaluating Window N of M    │◀──┐
                  └────────────────┬───────────────┘   │
                                   │                    │
                           more windows?               │
                          ┌────────┴────────┐          │
                          │                 │          │
                         Yes                No         │
                          │                 │          │
                          └─────────────────┼──────────┘
                                            │
                                            ▼
                          ┌─────────────────────────────┐
                          │   Calculating Robustness    │
                          └────────────────┬────────────┘
                                           │
                                           ▼
                          ┌─────────────────────────────┐
                          │         Complete            │
                          │   (passed: true/false)      │
                          └─────────────────────────────┘
```

## Computed Fields

### Robustness Score Formula

```python
def calculate_robustness_score(window_results: list[WindowResult]) -> float:
    """
    Robustness Score (0-100):
    - Consistency (30%): Inverse of return volatility across windows
    - Profitability (40%): Percentage of profitable windows
    - Degradation (30%): Test vs Train performance ratio (capped at 1.0)
    """
    returns = [w.test_metrics.total_return for w in window_results]

    # Consistency: lower std dev = higher consistency
    consistency = 1 - min(np.std(returns) / max(np.mean(np.abs(returns)), 0.001), 1)

    # Profitability: % of positive return windows
    profitability = sum(r > 0 for r in returns) / len(returns)

    # Degradation: how well test matches train (higher = less overfitting)
    degradation_ratios = [
        w.test_metrics.sharpe_ratio / max(w.train_metrics.sharpe_ratio, 0.001)
        for w in window_results
    ]
    degradation = np.mean([min(d, 1.0) for d in degradation_ratios])

    return (consistency * 0.3 + profitability * 0.4 + degradation * 0.3) * 100
```

### Pass/Fail Criteria

```python
def check_criteria(result: WalkForwardResult) -> bool:
    """Check if validation passed all criteria."""
    return all([
        result.robustness_score >= result.config.min_robustness_score,
        result.profitable_windows_pct >= result.config.min_profitable_windows_pct,
        result.worst_drawdown <= result.config.max_drawdown_threshold,
        sum(w.test_metrics.sharpe_ratio >= result.config.min_test_sharpe
            for w in result.windows) > len(result.windows) // 2,
    ])
```
