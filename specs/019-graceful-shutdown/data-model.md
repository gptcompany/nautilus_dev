# Data Model: Graceful Shutdown

## Entities

### ShutdownConfig

Configuration for graceful shutdown behavior.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| timeout_secs | float | 30.0 | Max time for shutdown sequence |
| cancel_orders | bool | True | Cancel all pending orders |
| verify_stop_losses | bool | True | Check positions have stop-losses |
| flush_cache | bool | True | Ensure cache persisted (native) |
| log_level | str | "INFO" | Logging verbosity during shutdown |

### ShutdownState

Runtime state during shutdown.

| Field | Type | Description |
|-------|------|-------------|
| requested | bool | Shutdown has been requested |
| started_at | datetime | When shutdown began |
| reason | str | Why shutdown was triggered |
| orders_cancelled | int | Count of cancelled orders |
| positions_unprotected | int | Positions without stop-loss |

### ShutdownReason (Enum)

```python
class ShutdownReason(Enum):
    SIGNAL_SIGTERM = "SIGTERM"
    SIGNAL_SIGINT = "SIGINT"
    EXCEPTION = "exception"
    MANUAL = "manual"
    TIMEOUT = "timeout"
```

## State Transitions

```
┌─────────┐     Signal/Exception     ┌──────────┐
│ RUNNING │ ────────────────────────►│ SHUTTING │
└─────────┘                          │   DOWN   │
                                     └────┬─────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
             ┌──────────┐          ┌──────────┐          ┌──────────┐
             │  HALTED  │          │ CANCELLED│          │  FLUSHED │
             │ (trading)│          │ (orders) │          │ (cache)  │
             └──────────┘          └──────────┘          └──────────┘
                    │                     │                     │
                    └─────────────────────┼─────────────────────┘
                                          │
                                          ▼
                                   ┌──────────┐
                                   │   EXIT   │
                                   │ (clean)  │
                                   └──────────┘
```

## Validation Rules

### ShutdownConfig

1. `timeout_secs` >= 5.0 (minimum for order cancellation)
2. `timeout_secs` <= 300.0 (5 min max, don't hang forever)
3. `log_level` in ["DEBUG", "INFO", "WARNING", "ERROR"]

### Shutdown Sequence

1. Trading MUST be halted before order cancellation
2. Orders MUST be cancelled before cache flush
3. Timeout MUST trigger force exit

## Relationships

```
TradingNode
    │
    ├── has one → GracefulShutdownHandler
    │                 │
    │                 ├── uses → ShutdownConfig
    │                 └── tracks → ShutdownState
    │
    ├── has many → Strategy (halted on shutdown)
    │
    ├── has many → Order (cancelled on shutdown)
    │
    └── has many → Position (verified for stop-loss)
```

## Events

| Event | Payload | When |
|-------|---------|------|
| ShutdownRequested | reason, timestamp | Signal received |
| TradingHalted | previous_state | Trading stopped |
| OrdersCancelled | count, failed | Orders processed |
| ShutdownComplete | duration_ms, success | Exit ready |
| ShutdownTimeout | elapsed_secs | Force exit needed |
