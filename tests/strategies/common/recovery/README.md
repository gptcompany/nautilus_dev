# Recovery Module Test Suite

**File**: `test_session_recovery.py`  
**Total Tests**: 99  
**Coverage Target**: 90%+

## Overview

Comprehensive test suite for the Position Recovery module (Spec 017), which handles PRODUCTION trading position recovery after crashes. This is CRITICAL infrastructure - all edge cases, failure modes, and race conditions are covered.

## Test Breakdown by Module

### RecoveryStateManager (23 tests)
- State initialization and lifecycle
- File persistence (save/load/delete)
- State transitions (start, complete, fail, timeout, reset)
- Thread safety for concurrent operations
- Atomic write pattern verification
- Corrupted file handling
- Edge cases: missing directories, invalid schemas

**Critical Tests**:
- `test_thread_safety_concurrent_saves` - Concurrent write safety
- `test_atomic_write_pattern` - Data integrity during crashes
- `test_load_state_corrupted_json` - Graceful corruption handling
- `test_sanitize_trader_id_in_filename` - Filesystem safety

### PositionRecoveryProvider (24 tests)
- Position reconciliation (cache vs exchange)
- Discrepancy detection (quantity, side, external, closed)
- Balance reconciliation (FR-003)
- Balance change detection and significance
- O(n+m) algorithm validation
- Duplicate instrument ID handling

**Critical Tests**:
- `test_reconcile_positions_quantity_mismatch` - Detects quantity discrepancies
- `test_reconcile_positions_external_position` - External position handling
- `test_reconcile_balances_total_mismatch` - Balance integrity checks
- `test_large_position_list_reconciliation` - Performance with 1000 positions

### RecoveryEventEmitter (11 tests)
- Event creation for all event types
- Callback invocation
- Timestamp generation
- Event serialization

**Critical Tests**:
- `test_event_callback_invoked` - Callback integration
- `test_emit_recovery_failed` - Error event emission

### EventReplayManager (15 tests)
- Event replay from cache
- Synthetic event generation
- Event gap detection and filling
- Sequence number management
- Timestamp-based filtering

**Critical Tests**:
- `test_detect_event_gaps_sequence_gap` - Gap detection
- `test_generate_position_opened_event` - Synthetic event correctness
- `test_replay_events_sorted_by_timestamp` - Event ordering

### RecoveryConfig (4 tests)
- Parameter validation
- Cross-field validation
- Immutability (frozen config)

**Critical Tests**:
- `test_max_recovery_time_validation` - Safety parameter validation

### RecoveryModels (10 tests)
- RecoveryState validation and properties
- PositionSnapshot validation
- IndicatorState and StrategySnapshot
- Timestamp and side validation
- Duration calculations

**Critical Tests**:
- `test_position_snapshot_timestamp_validation` - Data integrity
- `test_position_snapshot_side_validation` - Enum validation

### RecoverableStrategy (6 tests)
- Strategy initialization
- Recovery config defaults
- Property accessors (is_warming_up, is_ready)
- Position count tracking

**Critical Tests**:
- `test_is_ready_property` - Trading readiness check
- `test_strategy_default_recovery_config` - Fallback behavior

### Edge Cases & Stress Tests (4 tests)
- Concurrent state saves (no data loss)
- Empty reconciliation
- Large position lists (1000 items)
- State file corruption recovery
- Missing parent directories
- Zero positions recovered
- Sequence number overflow

**Critical Tests**:
- `test_concurrent_state_saves_no_data_loss` - Race condition safety
- `test_state_file_corruption_recovery` - Fault tolerance

### Performance Benchmarks (2 tests)
- Reconciliation with 1000 positions (< 1s)
- State save/load cycles (< 0.5s for 10 cycles)

**Critical Tests**:
- `test_reconciliation_performance_1000_positions` - O(n+m) verification

## Test Fixtures

### Core Fixtures
- `temp_state_dir` - Temporary directory for file operations
- `state_manager` - RecoveryStateManager with temp directory
- `state_manager_no_dir` - RecoveryStateManager without persistence
- `mock_cache` - Mock NautilusTrader cache
- `recovery_provider` - PositionRecoveryProvider instance
- `event_emitter` - RecoveryEventEmitter instance
- `event_replay_manager` - EventReplayManager instance
- `recovery_config` - Default RecoveryConfig
- `position_snapshot` - Sample PositionSnapshot
- `mock_position` - Mock Position object
- `mock_balance` - Mock Balance object

## Coverage Focus Areas

### State Persistence (CRITICAL)
- Atomic writes prevent corruption during crashes
- Thread-safe file operations
- Corrupted file recovery
- Missing directory creation

### Position Reconciliation (CRITICAL)
- Exchange is source of truth
- All discrepancy types detected
- O(n+m) performance maintained
- Duplicate handling

### Balance Restoration (FR-003)
- Balance change detection
- Significance thresholds
- New/removed currency handling

### Event Replay (P3 Optional)
- Event ordering correctness
- Synthetic event generation
- Gap detection and filling

## Running Tests

### Full Suite
```bash
uv run pytest tests/strategies/common/recovery/test_session_recovery.py -v
```

### Specific Module
```bash
# RecoveryStateManager only
uv run pytest tests/strategies/common/recovery/test_session_recovery.py::TestRecoveryStateManager -v

# Position reconciliation only
uv run pytest tests/strategies/common/recovery/test_session_recovery.py::TestPositionRecoveryProvider -v
```

### With Coverage
```bash
uv run pytest tests/strategies/common/recovery/test_session_recovery.py \
  --cov=strategies/common/recovery \
  --cov-report=term-missing \
  --cov-report=html \
  -v
```

### Performance Tests Only
```bash
uv run pytest tests/strategies/common/recovery/test_session_recovery.py::TestPerformance -v
```

## Expected Coverage

| Module | Target | Critical Paths |
|--------|--------|----------------|
| state_manager.py | 95%+ | save_state, load_state, thread safety |
| provider.py | 90%+ | reconcile_positions, reconcile_balances |
| recoverable_strategy.py | 85%+ | on_start, _detect_recovered_positions |
| event_replay.py | 80%+ | replay_events, generate_synthetic_events |
| event_emitter.py | 90%+ | All emit_* methods |
| models.py | 95%+ | Validation logic |
| config.py | 95%+ | Cross-field validation |

## Known Limitations

1. **RecoverableStrategy Integration**: Full integration tests with live NautilusTrader cache require BacktestNode setup (tested separately in integration tests)

2. **Exchange API Calls**: `get_exchange_positions()` and `get_exchange_balances()` default implementations use cache. Production implementations that query real exchanges must be tested in live/sandbox environments.

3. **Event Bus Integration**: Event emitter callback integration with NautilusTrader message bus tested in higher-level integration tests.

## Test Maintenance

- Update tests when adding new recovery features
- Maintain 90%+ coverage for all production code paths
- Add stress tests for new edge cases
- Profile performance tests if thresholds change

## Production Readiness Checklist

- [x] All state persistence scenarios tested
- [x] Thread safety verified
- [x] Corruption recovery tested
- [x] Reconciliation logic validated
- [x] Balance restoration tested (FR-003)
- [x] Event replay tested (FR-004)
- [x] Performance benchmarks established
- [x] Edge cases covered
- [x] Mock dependencies isolated
- [x] 99 comprehensive test cases

**Status**: PRODUCTION READY for session recovery testing
